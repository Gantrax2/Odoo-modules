from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime

class AbatarCotizador(models.Model):
    _name = "abatar.cotizador"
    _description = "Abatar cotizador"
    _inherit = ['abataradd.resumenbus']
    _rec_name='name_seq'

    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    tarifa = fields.Many2one('abatar.tarifas', string='Tabla de Tarifas')
    crm = fields.Many2one('abatar.crm', string='Order Reference')
    gastos_extra = fields.Float(string='Gastos Extra',default=False)

    fecha = fields.Datetime(string='Fecha', required=True, default=lambda self: fields.datetime.now())

    subto_personal = fields.Float(string='Traslado',store=True, readonly=True, compute='_subtotal_personal')
    costo_personal = fields.Float(string='Costo Traslado',store=True, readonly=True, compute='costo_set')
    subto_embalaje = fields.Float(string='Embalaje',store=True, readonly=True, compute='_subtotal_embalaje')
    costo_embalaje = fields.Float(string='Costo Embalaje',store=True, readonly=True, compute='costo_set')
    es_masiva = fields.Boolean(string='Es +IVA?', default=False)
    es_ivainc = fields.Boolean(string='Es IVA incluido?', default=False)

    hay_categ=fields.Char(string='Categoria (MDZ)')
    AYD = fields.Integer(string='hs adicionales unidad por prov', default=0)
    aumento = fields.Integer(string='Porcentaje Aumento Sv', default=0)
    kms = fields.Integer(string='Kms total',store=True, readonly=True, compute='_subtotal_')
    subto = fields.Float(string='Subtotal',store=True, readonly=True, compute='_subtotal_')
    subto2 = fields.Float(string='Subtotal Ajustado',store=True, readonly=True, compute='_subtotal2_')
    iva = fields.Float(string='IVA',store=True, readonly=True, compute='_iva_')
    total = fields.Float(string='Total',store=True, readonly=True, compute='_total_')
    costo_total = fields.Float(string='Costo Total',store=True, readonly=True, compute='costo_set')

    linea_personal = fields.One2many('abatar.cotizador.personal', 'cotizador_id', string='Linea de Productos')
    embalaje_lines = fields.One2many('abatar.cotizador.embalaje', 'cotizador_id', string='Linea de Embalaje')


    @api.depends('embalaje_lines', 'linea_personal')
    def costo_set(self):
        for rec in self:
            rec.costo_embalaje = 0
            for new in rec.embalaje_lines:
                rec.costo_embalaje += new.subt_costo
            rec.costo_personal = 0
            for new in rec.linea_personal:
                rec.costo_personal += new.subt_costo
            rec.costo_total = rec.costo_personal + rec.costo_embalaje

    @api.onchange('hay_categ')
    def set_dto(self):
        for rec in self:
            if rec.hay_categ:
                if rec.hay_categ=="A":
                    rec.aumento = 15
                elif rec.hay_categ=="AA":
                    rec.aumento = 25
                elif rec.hay_categ=="B":
                    rec.aumento = 0
                elif rec.hay_categ=="C":
                    rec.aumento = -15


    @api.model
    def default_get(self, fields):

        rec = super(AbatarCotizador, self).default_get(fields)

        busca = self.env['abatar.tarifas'].search(
            [('es_general', '=', True)])

        if busca:
            for ei in busca:
                rec['tarifa'] = ei.id

        if self._context.get('active_model') == 'abatar.crm' and self._context.get('active_ids'):
            revisac = self.env['abatar.crm'].search(
                [('id', '=', self._context.get('active_id', False))])

            if revisac.cliente:
                if revisac.cliente.tarifas:
                    rec['tarifa'] = revisac.cliente.tarifas.id

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen


        return rec

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.cotizador.sequence') or _('New')
        result = super(AbatarCotizador, self).create(vals)
        return result


    def actualiza_precios(self):
        for rec in self:
            if rec.linea_personal:
                for res in rec.linea_personal:
                    if res.producto:
                        for tar in rec.tarifa.productos_lines:
                            if res.producto.id==tar.productos_id.id:
                                res.precio=tar.tarifas_precio
                        for tar in rec.tarifa.kms_lines:
                            if res.producto.id==tar.productos_id.id:
                                res.precio_kms=tar.tarifas_precio
                        res.costo = res.producto.precio
                        if res.precio_kms:
                            res.costo_kms = res.precio_kms * (1 - res.producto.tipo.pc_gan / 100)

    def borra_embalaje(self):
        for rec in self:
            rec.embalaje_lines = [(5, 0, 0)]

    @api.depends('linea_personal.subtotal','linea_personal.kms')
    def _subtotal_personal(self):
        for rec in self:
            rec.subto_personal = 0
            rec.kms = 0
            for new in rec.linea_personal:
                rec.subto_personal += new.subtotal
                if new.kms:
                    rec.kms+=new.kms

    @api.depends('embalaje_lines.subtotal')
    def _subtotal_embalaje(self):
        for rec in self:
            rec.subto_embalaje = 0
            for new in rec.embalaje_lines:
                rec.subto_embalaje += new.subtotal


    @api.depends('subto_personal', 'subto_embalaje')
    def _subtotal_(self):
        for rec in self:
            rec.subto = rec.subto_personal + rec.subto_embalaje

    @api.depends('subto','aumento')
    def _subtotal2_(self):
        for rec in self:
            rec.subto2 = rec.subto*(1+(rec.aumento/100))

    @api.depends('es_masiva', 'es_ivainc', 'subto2')
    def _iva_(self):
        for rec in self:
            if rec.es_masiva == True:
                rec.iva = rec.subto2 * 0.21
            elif rec.es_ivainc == True:
                rec.iva = (rec.subto2 / 1.21)*0.21
            else:
                rec.iva = 0

    @api.depends('subto2','iva')
    def _total_(self):
        for rec in self:
            if rec.es_ivainc==True:
                rec.total = rec.subto2 - rec.iva
            else:
                rec.total = rec.subto2 + rec.iva


    @api.multi
    def write(self, vals):
        if BUSQUEDAON == True:
            try:
                if self.ensure_one():
                    if type(self.id) == int:
                        resum = Analize_model3(self, self._name,
                                               [('id', '=', self.id)])
                        if len(resum) > 50:
                            vals['resumen_busqueda'] = datetime.strftime(fields.datetime.now(),
                                                                         '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarCotizador, self).write(vals)
        return res

    @api.multi
    def action_view_crm(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.crm',
            'res_id': self.crm.id,
        }


class AbatarCotizadorPersonal(models.Model):
    _name = "abatar.cotizador.personal"
    _description = "Abatar cotizador personal"
    _rec_name='name_gral'

    producto = fields.Many2one('abatar.productos', string='Productos')
    horas = fields.Float(string='Horas', default=0)
    precio_forc= fields.Float(string='Cotizado', default=0)
    precio = fields.Float(string='Precio',store=True, readonly=True, compute='set_producto')
    precio_f = fields.Float(string='Precio (F)')
    costo = fields.Float(string='Costo',store=True, readonly=True, compute='set_producto')
    kms = fields.Integer(string='kms')
    cantidad = fields.Integer(string='Cantidad', default=1)
    precio_kms = fields.Float(string='precio kms',store=True, readonly=True, compute='set_producto')
    precio_kms_f = fields.Float(string='precio kms (F)')
    costo_kms = fields.Float(string='costo kms',store=True, readonly=True, compute='set_producto')
    subtotal = fields.Float(string='subtotal',store=True, readonly=True, compute='set_subto')

    subt_costo = fields.Float(string='subtotal costo',store=True, readonly=True, compute='set_subt_costo')
    desc = fields.Char(string='Desc.')

    id_unidad = fields.Integer(string='id unidad')
    id_operario = fields.Integer(string='id operario')

    cotizador_id = fields.Many2one('abatar.cotizador')

    name_gral = fields.Char(compute='set_name_gral', string="Nombre Rec", store=True, readonly=True)
    @api.depends('producto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'CP ' + str(rec.id)
            if rec.producto:
                rec.name_gral += ' - ' + str(rec.producto.name)

    @api.onchange('producto')
    def refresh_f(self):
        for rec in self:
            rec.precio_kms_f=0
            rec.precio_f=0


    @api.depends('producto', 'precio_f', 'precio_kms_f')
    def set_producto(self):
        for rec in self:
            if rec.precio_f:
                rec.precio = rec.precio_f
            else:

                if rec.cotizador_id.tarifa:
                    for ei in rec.cotizador_id.tarifa.productos_lines:
                        if ei.productos_id.id == rec.producto.id:
                            rec.precio = ei.tarifas_precio
                else:
                    tar_gen=self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)
                    for ei in tar_gen.productos_lines:
                        if ei.productos_id.id == rec.producto.id:
                            rec.precio = ei.tarifas_precio

            if rec.precio_kms_f:
                rec.precio_kms = rec.precio_kms_f
            else:
                if rec.cotizador_id.tarifa:
                    tar_gen=self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)

                    for ec in rec.cotizador_id.tarifa.kms_lines:
                        if ec.productos_id.id == rec.producto.id:
                            rec.precio_kms = ec.tarifas_precio

                    for ec in tar_gen.kms_lines:
                        if ec.productos_id.id == rec.producto.id:
                            rec.precio_kms = ec.tarifas_precio
            rec.costo=rec.producto.precio
            if rec.precio_kms:
                rec.costo_kms=rec.precio_kms*(1-rec.producto.tipo.pc_gan/100)



    @api.depends('producto', 'horas', 'precio_forc', 'kms', 'cantidad', 'precio')
    def set_subto(self):
        for rec in self:
            if rec.precio_forc:
                rec.subtotal = rec.precio_forc
            else:
                conud=0
                if rec.producto.name in ('Operario', 'Supervisor'):
                    for lin in rec.cotizador_id.linea_personal:
                        if lin.producto:
                            if lin.producto.name[:6]=='Unidad':
                                conud=2
                min = rec.cotizador_id.tarifa.productos_lines.search([('productos_id', '=', rec.producto.id)], limit=1).tarifas_minimo-conud

                rec.subtotal = rec.cantidad * rec.precio * max([min,(rec.horas+1)]) + (rec.kms * rec.precio_kms)

    @api.depends('producto', 'horas','kms', 'cantidad', 'costo')
    def set_subt_costo(self):
        for rec in self:
            rec.subt_costo = rec.cantidad * rec.costo * (rec.horas) + (rec.kms * rec.costo_kms)


    @api.model
    def default_get(self, fields):

        revisa_a = self.env['abatar.tipo'].search([('name', '=', 'unidad')])
        revisa_b = self.env['abatar.tipo'].search([('name', '=', 'operario')])

        rec = super(AbatarCotizadorPersonal, self).default_get(fields)

        rec['id_unidad'] = revisa_a.id
        rec['id_operario'] = revisa_b.id

        return rec



class AbatarCotizadorEmbalaje(models.Model):
    _name = "abatar.cotizador.embalaje"
    _description = "Abatar cotizador embalaje"
    _rec_name='name_gral'

    embalaje_id = fields.Many2one('abatar.productos', string='Producto')
    cantidad = fields.Integer(string='Cantidad')
    precio = fields.Float(string='Precio', readonly=True, store=True, compute='set_precio')
    costo = fields.Float(string='Costo', readonly=True, store=True, related='embalaje_id.precio')
    subt_costo = fields.Float(string='subtotal costo', compute='set_subt_costo')
    subtotal = fields.Float(string='subtotal', compute='set_subto')
    id_embalaje = fields.Integer(string='id embalaje')

    cotizador_id = fields.Many2one('abatar.cotizador')

    name_gral = fields.Char(compute='set_name_gral', string="Nombre Rec", store=True, readonly=True)

    @api.depends('embalaje_id')
    def set_precio(self):
        for rec in self:
            if rec.cotizador_id:
                if rec.cotizador_id.tarifa:
                    tarifa_act=rec.cotizador_id.tarifa
                else:
                    tarifa_act=self.env['abatar.tarifas'].search([('es_general','=',True)],limit=1)

            if rec.embalaje_id:
                if tarifa_act.productos_lines.search([('productos_id','=',rec.embalaje_id.id)], limit=1):
                    rec.precio=tarifa_act.productos_lines.search([('productos_id','=',rec.embalaje_id.id)], limit=1).tarifas_precio
                elif rec.costo:
                    rec.precio=rec.costo*1.4


    @api.depends('embalaje_id')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'CE ' + str(rec.id)
            if rec.embalaje_id:
                rec.name_gral += ' - ' + str(rec.embalaje_id.name)


    @api.onchange('embalaje_id')
    def set_precio_costo(self):
        for rec in self:
            if rec.embalaje_id:
                if rec.cotizador_id.crm.cliente.tarifas:
                    tar=self.env['abatar.tarifas'].search([('id','=', rec.cotizador_id.crm.cliente.tarifas)],limit=1)
                else:
                    tar = self.env['abatar.tarifas'].search([('es_general', '=', True)],limit=1)
                prec=tar.productos_lines.search([('productos_id','=',rec.embalaje_id.id)],limit=1).tarifas_precio
                cost=rec.embalaje_id.precio
                rec.costo = cost
                rec.precio = prec

    @api.depends('embalaje_id', 'cantidad', 'precio')
    def set_subto(self):
        for rec in self:
            rec.subtotal = rec.precio * rec.cantidad

    @api.depends('embalaje_id', 'cantidad', 'costo')
    def set_subt_costo(self):
        for rec in self:
            rec.subt_costo = rec.costo * rec.cantidad

    @api.model
    def default_get(self, fields):
        revisa_a = self.env['abatar.tipo'].search([('name', '=', 'embalaje')])

        rec = super(AbatarCotizadorEmbalaje, self).default_get(fields)

        rec['id_embalaje'] = revisa_a.id

        return rec
