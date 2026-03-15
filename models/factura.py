from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime

BASEA=-38
BASEAmyp=5
BASEB=135
BASEBmyp=2
BASEC=25


class AbatarFactura(models.Model):
    _name = "abatar.factura"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _description = "Abatar factura"
    _rec_name = "name_seq"
    _order = 'name_seq desc'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.crm:
                rec.crm.factura=False
                rec.crm.active=True
            if rec.resumenes:
                rec.resumenes.factura=False
                rec.resumenes.active=True
            if rec.pagos:
                rec.pagos=False


        res = super(AbatarFactura, self).unlink()
        return res


    camb_tipo = fields.Char(string='Tipo a cambiar')
    camb_nro = fields.Char(string='Nuevo Próximo Número')

    name_seq = fields.Char(string='F Nro')
    name_seq2 = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    crm = fields.Many2one('abatar.crm',string='CRM')
    responsable=fields.Char('Responsable', store=True, readonly=True, compute='set_resp')
    es_crm_pago_line = fields.Boolean(string='Es CRM Pago Line', default=False)
    cliente = fields.Many2one('abatar.clientes',string='Cliente (Cta.Cte.)' )
    cliente_gral=fields.Char('Cartera Cliente',related='cliente.clientes_gral_id.name', store=True, readonly=True)
    resumenes = fields.Many2one('abatar.resumenes',string='Resumen')
    email_vto = fields.Char(string='Email aviso VTO')
    email_vto2 = fields.Char(string='Email aviso VTO2')
    email_vto3 = fields.Char(string='Email aviso VTO3')
    email_pagos = fields.Char(string='Email reclamo Pago')
    cuit = fields.Char(string='CUIT')
    dni = fields.Char(string='CUIT/DNI')
    sujeto = fields.Char(string='Cliente')

    tipo_fc = fields.Selection([('s/f', 's/f'),('A', 'A'), ('B', 'B'), ('C', 'C'),('A(myp)', 'A(myp)'), ('B(myp)', 'B(myp)')],required=True,string='Tipo Factura')

    monto = fields.Float(string='Subtotal')
    mas_iva_sf=fields.Boolean('+ IVA?', default=False)
    iva_excento=fields.Boolean('IVA EXCENTO?', default=False)
    iva=fields.Float(string='IVA', store=True, readonly=True, compute='set_iva')
    total = fields.Float(string='Total', store=True, readonly=True, compute='set_total')
    desc = fields.Text(string='Descripcion')

    vto = fields.Date(string='Vencimiento')
    adjunto = fields.Binary(string='Factura adjunta')
    fecha_op = fields.Datetime(string='Fecha de Emision', default=fields.Datetime.now())
    active = fields.Boolean('Active', default=True)
    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)

    hay_cheque_recibido = fields.Boolean('Hay Cheque Recibido', default=False)
    pagos = fields.Many2one('abatar.pagos',string='Pago')
    fecha_pago=fields.Date("Fecha de pago",related="pagos.fecha_pago", store=True, readonly=True)
    dias_pago=fields.Integer("Días al pago", store=True, readonly=True,compute="set_dias_pago")
    es_pagado=fields.Boolean('Es Pagado?', store=True, readonly=True,compute='set_es_pagado')
    pagos_id = fields.Integer(string='Pago_id')

    vencida = fields.Boolean(string='Vencida',store=True, readonly=True,compute='set_vencida')


    @api.depends("pagos", "vto")
    def set_vencida(self):
        for rec in self:
            if rec.name_seq:
                if rec.pagos or rec.name_seq[:2]=="NC":
                    rec.vencida= False
                else:
                    if rec.vto:
                        if datetime.today().date()>=rec.vto:
                            rec.vencida= True
                        else:
                            rec.vencida= False
                    else:
                        rec.vencida= True
            else:
                rec.vencida= True





    @api.depends("pagos", "fecha_pago")
    def set_dias_pago(self):
        for rec in self:
            if rec.pagos:
                if rec.fecha_pago:
                    if rec.fecha_op:
                        rec.dias_pago= abs((rec.fecha_op.date() - rec.fecha_pago).days)


    @api.onchange('iva_excento')
    def refresh(self):
        for rec in self.env['abatar.factura'].search([('active','in',(True,False))]):
            if rec.desc:
                rec.desc=rec.desc+'.'
            else:
                rec.desc='.'
    @api.depends('pagos','desc')
    def set_es_pagado(self):
        for rec in self:
            if rec.pagos:
                rec.es_pagado=True
            else:
                rec.es_pagado=False

    @api.depends('resumenes','crm')
    def set_resp(self):
        for rec in self:
            if rec.crm:
                rec.responsable=rec.crm.contacto.name
            elif rec.resumenes:
                for res in rec.resumenes.producto_lines2:
                    if res.ordenes_id:
                        if res.ordenes_id.contacto:
                            if res.ordenes_id.contacto.name:
                                rec.responsable=res.ordenes_id.contacto.name
                                break


    @api.onchange('pagos','active')
    def set_pago_resumen(self):
        for rec in self:
            if rec.resumenes and rec.cliente:
                if rec.pagos:
                    if rec.pagos.saldo in (0, False):
                        rec.resumenes.write({'pagado':True})

    @api.onchange('cliente','sujeto')
    def set_cuit(self):
        for rec in self:
            if rec.cliente:
                if rec.cliente.cuit:
                    rec.cuit=rec.cliente.cuit
            else:
                rec.cuit=''

    @api.onchange('cliente','sujeto')
    def set_vto(self):
        for rec in self:
            if rec.cliente:
                if rec.vto==False:
                    if rec.cliente.clientes_gral_id.vto:
                        rec.vto=(rec.fecha_op+timedelta(days=rec.cliente.clientes_gral_id.vto)).date()
                if rec.cliente.clientes_gral_id.email_vto:
                    rec.email_vto = rec.cliente.clientes_gral_id.email_vto
                if rec.cliente.clientes_gral_id.email_vto2:
                    rec.email_vto2 = rec.cliente.clientes_gral_id.email_vto2
                if rec.cliente.clientes_gral_id.email_vto3:
                    rec.email_vto3 = rec.cliente.clientes_gral_id.email_vto3
                if rec.cliente.clientes_gral_id.email_pagos:
                    rec.email_pagos = rec.cliente.clientes_gral_id.email_pagos
            else:
                rec.vto=rec.fecha_op.date()


    @api.depends('monto', 'tipo_fc', 'iva_excento', 'mas_iva_sf')
    def set_iva(self):
        for rec in self:
            monto=0
            if rec.monto:
                if rec.tipo_fc:
                    if rec.tipo_fc in ('A','B','A(myp)','B(myp)'):
                        if rec.iva_excento:
                            iva=0
                        else:
                            iva=0.21
                    else:
                        if rec.tipo_fc=='s/f':
                            if rec.mas_iva_sf:
                                iva=0.21
                            else:
                                iva=0
                        else:
                            iva=0
                else:
                    iva=0
            else:
                iva=0

            monto=rec.monto*iva
            rec.iva=round(monto, 2)

    @api.multi
    def action_view_pagos(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.pagos',
            'res_id': self.pagos.id,
        }

    @api.depends('monto','iva','iva_excento', 'mas_iva_sf')
    def set_total(self):
        for rec in self:
            monto=0
            if rec.monto:
                monto=rec.monto+rec.iva
            rec.total=round(monto, 2)


    @api.model
    def default_get(self, fields):
        rec = super(AbatarFactura, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen
        #if 'crm' in rec.keys():
        #    ped=self.env['abatar.crm'].search([('id','=',rec['crm'])])
        #    if ped.mas_iva:
        #        rec['mas_iva_sf']=True
        #elif self.crm:
        #    ped=self.env['abatar.crm'].search([('id','=',self.crm)])
        #    if ped.mas_iva:
        #        rec['mas_iva_sf']=True


        return rec

    @api.multi
    def write(self, vals):
        if BUSQUEDAON == True:
            try:
                if self.ensure_one():
                    if type(self.id) == int:
                        resum = Analize_model3(self, self._name,
                                               [('id', '=', self.id), ('active', 'in', (True, False))])
                        if len(resum) > 50:
                            vals['resumen_busqueda'] = datetime.strftime(fields.datetime.now(),
                                                                         '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarFactura, self).write(vals)

        return res

    @api.model
    def create(self, vals):

        base=0
        if vals.get('tipo_fc')=='A':
            b0 = self.env['abatar.constantes'].search([('name', '=', 'BASEA')], limit=1)
            if b0:
                base = b0.entero
            else:
                base = BASEA
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaA.sequence') or _('New')
        elif vals.get('tipo_fc')=='B':
            b0 = self.env['abatar.constantes'].search([('name', '=', 'BASEB')], limit=1)
            if b0:
                base = b0.entero
            else:
                base = BASEB
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaB.sequence') or _('New')
        elif vals.get('tipo_fc')=='A(myp)':
            b0 = self.env['abatar.constantes'].search([('name', '=', 'BASEAmyp')], limit=1)
            if b0:
                base = b0.entero
            else:
                base = BASEAmyp
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaAmyp.sequence') or _('New')
        elif vals.get('tipo_fc')=='B(myp)':
            b0 = self.env['abatar.constantes'].search([('name', '=', 'BASEBmyp')], limit=1)
            if b0:
                base = b0.entero
            else:
                base = BASEBmyp
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaBmyp.sequence') or _('New')
        elif vals.get('tipo_fc')=='C':
            b0 = self.env['abatar.constantes'].search([('name', '=', 'BASEC')], limit=1)
            if b0:
                base = b0.entero
            else:
                base = BASEC
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaC.sequence') or _('New')
        elif vals.get('tipo_fc')=='s/f':
            base = 0
            if vals.get('name_seq2', _('New')) == _('New'):
                vals['name_seq2'] = self.env['ir.sequence'].next_by_code('abatar.facturaSF.sequence') or _('New')
        result = super(AbatarFactura, self).create(vals)
        n2 = self.env['abatar.factura'].search_count([('tipo_fc', '=', vals.get('tipo_fc')), ('active', 'in', (True,False))])

        if result.crm:
            if result.crm.mas_iva:
                result.mas_iva_sf=True
        string= 'F'+vals.get('tipo_fc')
        for i in range(5-len(str(n2+base))):
            string+='0'
        string+=str(int(n2)+base)
        result.name_seq=string
        return result
