from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

from datetime import timedelta, datetime

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

class AbatarResumenes(models.Model):
    _name = "abatar.resumenes"
    _description = "FACTURAS"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _rec_name='name_gral'
    _order="id desc"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.producto_lines2:
                for ref in rec.producto_lines2:
                    ref.unlink()

            rec.producto_lines2 = [(5, 0, 0)]
            if rec.factura:
                rec.factura.resumenes=False
                rec.factura.unlink()
                rec.factura=False


        res = super(AbatarResumenes, self).unlink()
        return res

    @api.onchange('clientes_id')
    def cambia_func(self):
        for rec in self:
            if rec.clientes_id:
                rec.factura = False
                for algo in rec.producto_lines2:
                    if algo.ordenes_id:
                        algo.write({'resumenes' : False})
                rec.producto_lines2 = [(5,0,0)]

    name_gral= fields.Char(string="FACTURA",store=True, readonly=True, compute='set_name_gral')
    clientes_id=fields.Many2one('abatar.clientes', string="cliente")

    cliente_vto=fields.Integer('Días Vencimiento de FF',related='clientes_id.clientes_gral_id.vto', store=True, readonly=True)
    fecha_op=fields.Date(String="Fecha de Emisión", default=lambda self: fields.Date.today())

    active = fields.Boolean('Active', default=True)
    cambio_prod2= fields.Boolean('Cambio, uso interno')
    producto_lines2 = fields.One2many('abatar.resumenes.ordenes', 'resumenes_id', string="Listado de Ordenes", required=True)
    monto= fields.Float(string="Monto Total sin IVA",store=True, readonly=True, compute='set_monto')
    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    desc= fields.Text(string="Descripcion")

    day_month=fields.Date(string="Fecha op", store=True, readonly=True,compute='set_day_month')
    dto=fields.Selection([('1', 'No aplica'), ('2', '10%'), ('3', '15%'), ('4', '20%'), ('5', '25%')], default='1', string="Descuento:")
    dto_forc=fields.Integer(string='Descuento Especial', default=0)
    monto_dto=fields.Float(compute='set_monto_dto',store=True, readonly=True, string="Subtotal con Dto:")
    monto_IVA=fields.Float(compute='set_monto_IVA',store=True, readonly=True, string="Monto IVA 21%:")
    total=fields.Float(string="Monto Total",store=True, readonly=True, compute='set_total')
    ordenes_resumen=fields.Char(string="Resumen para busqueda", store=True, readonly=True,compute='set_ordenes_resumen')

    tipo_fc = fields.Selection([('A', 'A'), ('B', 'B'), ('C', 'C'),('A(myp)', 'A(myp)'), ('B(myp)', 'B(myp)'), ('s/f', 's/f')],string='Tipo Factura')
    factura=fields.Many2one('abatar.factura', default=False, string="Factura asociada")
    factura_num=fields.Char(related='factura.name_seq',store=True, readonly=True, string="N° Fact.")
    pagado=fields.Boolean(string="Pagado", default=False)

    facturado=fields.Boolean(compute='set_facturado',store=True, readonly=True, string="Tiene Factura")


    @api.onchange('desc')
    def set_pagado(self):
        for rec in self:
            if rec.factura:
                if rec.factura.pagos:
                    if rec.factura.pagos.saldo in (0, False):
                        rec.pagado=True

    @api.onchange('pagado')
    def set_active(self):
        for rec in self:
            if rec.pagado:
                rec.active=False

    @api.multi
    @api.depends('factura')
    def set_facturado(self):
        for rec in self:
            if rec.factura:
                rec.facturado=True
            else:
                rec.facturado=False
    @api.one
    def action_crea_factura(self):

        if self.clientes_id and self.tipo_fc and self.monto :
            pass
        else:
            raise UserError('Primero elije el CLiente, Tipo de Factura y el Monto ')

        dto=1
        if self.dto:
            if self.dto=='2':
                dto=0.9
            elif self.dto=='3':
                dto=0.85
            elif self.dto=='4':
                dto=0.8
            elif self.dto=='5':
                dto=0.75

        vals2 = {
            'resumenes': self.id,
            'cliente': self.clientes_id.id,
            'crm': False,
            'cuit': self.clientes_id.cuit,
            'tipo_fc': self.tipo_fc,
            'monto': self.monto*dto,
        }

        resu = self.env['abatar.factura'].create(vals2)
        self.factura = resu.id
        self.factura_num = resu.name_seq

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.factura',
            'res_id': resu.id,
        }

    @api.multi
    def action_view_factura(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.factura',
            'res_id': self.factura.id,
        }

    @api.one
    def action_view_factura_unlink(self):
        self.factura.unlink()
    @api.depends('producto_lines2','cambio_prod2')
    def set_ordenes_resumen(self):
        for r in self:
            r.ordenes_resumen=' '
            if r.producto_lines2:
                for ai in r.producto_lines2:
                    if ai.ordenes_id.name_gral:
                        r.ordenes_resumen+=str(ai.ordenes_id.name_gral)+ ' - '
    @api.depends('factura')
    def set_res_pendiente(self):
        for rec in self.env['abatar.resumenes']:
            if rec.factura==False:
                res = self.env['abatar.clientes'].search([('id', '=', rec.id)])
                res.write({'res_pendiente' : True})
    @api.one
    @api.depends('monto','dto','dto_forc')
    def set_monto_dto(self):
        for rec in self:
            monto=0
            if rec.monto:
                if rec.dto_forc:
                        Desc=1-(rec.dto_forc/100)
                elif rec.dto:
                    if rec.dto=='1':
                        Desc=1
                    elif rec.dto=='2':
                        Desc=0.9
                    elif rec.dto=='3':
                        Desc=0.85
                    elif rec.dto=='4':
                        Desc=0.8
                    elif rec.dto=='5':
                        Desc=0.75
                else:
                    Desc=1
                IVA=1.21
                if rec.tipo_fc:
                    if rec.tipo_fc=='s/f':
                        IVA=1
                monto=rec.monto*IVA*(1-Desc)
            rec.monto_dto=round(monto, 2)
    @api.one
    @api.depends( 'monto')
    def set_monto_IVA(self):
        for rec in self:
            monto=0
            IVA=0.21
            if rec.tipo_fc:
                if rec.tipo_fc=='s/f':
                    IVA=0
            if rec.monto:
                monto=rec.monto*IVA
            rec.monto_IVA=round(monto, 2)

    @api.one
    @api.depends('monto_dto','monto_IVA','monto')
    def set_total(self):
        for rec in self:
            monto=0
            if rec.monto_dto:
                if rec.monto_IVA:
                    monto=rec.monto+rec.monto_IVA-rec.monto_dto
                else:
                    monto=rec.monto-rec.monto_dto
            else:
                if rec.monto_IVA:
                    monto=rec.monto+rec.monto_IVA
                else:
                    monto=rec.monto
            rec.total=round(monto, 2)
    @api.depends('fecha_op')
    def set_day_month(self):
        for r in self:
            if r.fecha_op:
                r.nombre_fecha =  fields.Date.from_string(r.fecha_op).strftime('%d/%m')


    @api.model
    def default_get(self, fields):
        rec = super(AbatarResumenes, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

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
        res = super(AbatarResumenes, self).write(vals)
        return res
    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.resumenes.sequence') or _('New')
        vals['factura']=False
        result = super(AbatarResumenes, self).create(vals)
        return result
    @api.one
    @api.depends('producto_lines2','cambio_prod2')
    def set_monto(self):
        for res in self:
            monto=0
            for rec in res.producto_lines2:
                monto+=rec.precio
            res.monto=round(monto, 2)

    @api.multi
    def ref_proforma(self):

        return {'name': 'Go to website',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': 'http://localhost:8069/report/pdf/om_abatartrucks.report_resumenes/%s' % (self.id)
                }
    @api.one
    @api.depends('clientes_id', 'desc', 'day_month', 'total', 'name_seq')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=''
            if rec.clientes_id:
                rec.name_gral+=rec.clientes_id.name_gral
            if rec.total:
                rec.name_gral += ' - $'+str(rec.total)
            if rec.name_seq and type(rec.name_seq)==str:
                rec.name_gral += ' - '+rec.name_seq
            if rec.day_month:
                rec.name_gral += ' - '+rec.day_month
            if rec.factura:
                rec.name_gral += ' - PAGADO:'+ str(rec.factura.name_seq)
            if rec.desc:
                rec.name_gral += ' - '+rec.desc

    @api.onchange('clientes_id')
    def set_dto(self):
        for rec in self:
            if rec.clientes_id:
                if rec.clientes_id.clientes_gral_id.dto:
                    rec.dto=rec.clientes_id.clientes_gral_id.dto


class AbatarResumenesOrdenes(models.Model):
    _name='abatar.resumenes.ordenes'
    _description = "Abatar Resumenes Ordenes"
    _rec_name = "ordenes_id"


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.ordenes_id:
                revisad = self.env['abatar.ordenes'].search(
                    [('id', '=', rec.ordenes_id.id),('active', '=', False)])
                revisad.write({'active':  True,
                               'factura':  False,
                               'resumenes':  False,
                               'resumenes_id':  0})

                cliente=revisad.cliente

        ordenes_p = self.env['abatar.ordenes'].search_count(
            [('cliente', '=', cliente.id), ('state', '=', 'finalizo'), ('resumenes', '=', False)])
        cliente.write({'ordenes_p': ordenes_p})
        res = super(AbatarResumenesOrdenes, self).unlink()
        return res


    #ES COMO EL DEFAULT
    @api.depends('resumenes_id.clientes_id')
    def set_clientes_id(self):
        for rec in self:
            if rec.resumenes_id.clientes_id:
                rec.clientes_id=rec.resumenes_id.clientes_id.id


    resumenes_id=fields.Many2one('abatar.resumenes', string="Resumenes id")
    clientes_id=fields.Many2one(string="clientes id", compute='set_clientes_id')

    ordenes_id = fields.Many2one('abatar.ordenes', string='Ordenes', required=True)
    precio= fields.Float(string='Precio s/IVA', compute='set_precio')
    desc = fields.Char(string='Descripcion')

    @api.one
    @api.depends('ordenes_id')
    def set_precio(self):

        for res in self:
            for rec in res.ordenes_id:
                if rec.precio_convenido:
                    self.precio += rec.precio_convenido
                else:
                    self.precio += rec.subtotal
                self.resumenes_id.cambio_prod2=not self.resumenes_id.cambio_prod2

    @api.model
    def create(self, vals):

        result = super(AbatarResumenesOrdenes, self).create(vals)
        if vals.get('ordenes_id'):
            revisac = self.env['abatar.ordenes'].search([('id', '=', vals.get('ordenes_id'))])
            revisac.write({'resumenes': result.resumenes_id.id})
            revisac.write({'resumenes_id': result.resumenes_id.id})
            revisac.write({'active': False})
            actres=self.env['abatar.resumenes'].search([('id', '=', vals.get('resumenes_id'))], limit=1)
            if actres.factura:
                revisac.write({'factura': actres.factura.id})
            cliente=revisac.cliente
            ordenes_p = self.env['abatar.ordenes'].search_count(
                [('cliente', '=', cliente.id), ('state', '=', 'finalizo'), ('resumenes', '=', False)])
            cliente.write({'ordenes_p': ordenes_p})

        return result

    @api.multi
    def write(self, vals):

        res = super(AbatarResumenesOrdenes, self).write(vals)
        if 'ordenes_id' in vals:
            if vals.get('ordenes_id'):
                valor_nuevo = self.env['abatar.ordenes'].search(
                    [('id', '=', vals.get('ordenes_id'))])
                valor_nuevo.write({'resumenes': res.resumenes_id.id})
                valor_nuevo.write({'resumenes_id': res.resumenes_id.id})
                resact=self.env['abatar.ordenes'].search([('id', '=', vals.get('resumenes_id'))], limit=1)
                if resact.factura:
                    valor_nuevo.write({'factura': resact.factura.id})
                valor_nuevo.write({'active': False})

                valor_viejo = self.env['abatar.ordenes'].search(
                    [('id', '=', self.ordenes_id.id)])
                valor_viejo.write({'active': True})
                valor_viejo.write({'resumenes': False})
                valor_viejo.write({'factura': False})
                valor_viejo.write({'resumenes_id': 0})

                cliente = valor_nuevo.cliente
                ordenes_p = self.env['abatar.ordenes'].search_count(
                    [('cliente', '=', cliente.id), ('state', '=', 'finalizo'), ('resumenes', '=', False)])
                cliente.write({'ordenes_p': ordenes_p})

        return res