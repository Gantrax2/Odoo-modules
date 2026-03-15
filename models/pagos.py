from odoo import models, fields, tools, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON
from datetime import timedelta, datetime
import time
import calendar


class AbatarPagos(models.Model):
    _name = "abatar.pagos"
    _description = "Abatar Pagos"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _rec_name='name_gral'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.clientes_id:
                for ref in rec.factura_lines:
                    ref.unlink()
                rec.write({'caja':False})
            elif rec.crm_id:
                rec.factura_crm_id.write({'pagos':False,'pagos_id':0, 'active':True})
                rec.factura_crm_id=False
            if rec.caja:
                rec.caja=False

        res = super(AbatarPagos, self).unlink()
        return res


    @api.onchange('clientes_id')
    def cambia_func(self):
        for rec in self:
            if rec.clientes_id:
                for algo in rec.factura_lines:
                    if algo.factura_id:
                        algo.write({'pagos_id' : False})
                rec.factura_lines = [(5,0,0)]


    name_gral=fields.Char(string="Nombre Rec", compute='set_name_gral')
    clientes_id = fields.Many2one('abatar.clientes', string='Cliente')
    crm_id = fields.Many2one('abatar.crm', string='Crm')
    fecha_op=fields.Date(string="Fecha de Operacion", required=True)

    active = fields.Boolean('Active', default=True)
    factura_crm_id=fields.Many2one('abatar.factura' , string="Factura_id")
    factura_lines=fields.One2many('abatar.pagos.factura', 'pagos_id', string="Lista de Facturas en Pago")
    monto=fields.Float(string="Monto",store=True, readonly=True, compute='set_monto')
    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    desc=fields.Text(string="Descripcion")
    pago=fields.Float(string="Pago")
    fecha_pago=fields.Date(String="Fecha de Pago")

    retenciones=fields.Float(string="Retenciones total")
    saldo=fields.Float(string="Saldo de Pago", store=True, readonly=True, compute='set_saldo')
    caja=fields.Many2one('abatar.caja' , string="Caja_id")
    factura_resumen=fields.Char(string="Resumen para busqueda", store=True, readonly=True, compute='set_factura_resumen')
    adjunto= fields.One2many('abatar.pagos.adjuntos', 'pagos_id', string='Adjuntos')

    #@api.onchange('desc')
    #def set_f_crm_id(self):
    #    resul= self.env['abatar.pagos'].search([])
    #    for rec in resul:
    #        if rec.saldo in (0, False):
    #            rec.write({'active':False})

    @api.depends('factura_lines', 'crm_id')
    def set_factura_resumen(self):
        for r in self:
            r.factura_resumen=' '
            if r.clientes_id:
                if r.factura_lines:
                    for ai in r.factura_lines:
                        if ai.factura_id.name_seq:
                            r.factura_resumen+=str(ai.factura_id.name_seq)+ ' - '
            elif r.crm_id:
                if r.factura_crm_id:
                    r.factura_resumen+=str(r.factura_crm_id.name_seq)+ ' - '

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.pagos.sequence') or _('New')
        result = super(AbatarPagos, self).create(vals)
        result.caja=False
        if vals.get('factura_crm_id'):
            fact=self.env['abatar.factura'].search([('id', '=', vals.get('factura_crm_id'))], limit=1)
            fact.write({'pagos': result.id,'pagos_id': result.id, 'active': False})
        return result

    @api.model
    def default_get(self, fields):
        rec = super(AbatarPagos, self).default_get(fields)

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
        result= super(AbatarPagos, self).write(vals)
        if vals.get('factura_crm_id'):
            self.factura_crm_id.write({'pagos':False,'pagos_id':0,'active':True})
            rest=self.env['abatar.factura'].search([('id', '=', vals.get('factura_crm_id'))], limit=1)
            rest.write({'pagos':self.id,'pagos_id':self.id,'active':False})
        return result


    @api.depends('monto', 'name_seq')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = ''
            if rec.name_seq:
                rec.name_gral += 'pago '+str(rec.name_seq)+': '
            if rec.clientes_id:
                rec.name_gral += 'Cl.'+str(rec.clientes_id.clientes_gral_id.name)+': '
            elif rec.crm_id:
                rec.name_gral += 'CRM.'+str(rec.crm_id.name_seq)+': '
            if rec.monto:
                rec.name_gral += 'monto $'+str(rec.monto)

    @api.depends('factura_lines', 'factura_crm_id', 'crm_id')
    def set_monto(self):
        for rec in self:
            monto=0
            if rec.clientes_id:
                if rec.factura_lines:
                    for res in rec.factura_lines:
                        monto+=res.factura_total
            elif rec.crm_id:
                if rec.factura_crm_id.total:
                    monto=rec.factura_crm_id.total
            rec.monto=monto




    @api.depends('factura_lines', 'factura_crm_id','monto','pago','retenciones')
    def set_saldo(self):
        for rec in self:
            rec.saldo=0
            if rec.monto:
                rec.saldo+=rec.monto
            if rec.pago:
                rec.saldo-=rec.pago
            if rec.retenciones:
                rec.saldo-=rec.retenciones

    @api.onchange('saldo','monto','pago','retenciones')
    def set_active(self):
        for rec in self:
            if rec.saldo in (0, False):
                if rec.active:
                    rec.write({'active':False})
            else:
                if not rec.active:
                    rec.write({'active':True})


    @api.multi
    def action_view_caja(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.caja',
            'res_id': self.caja.id,
        }


class AbatarPagosAdjuntos(models.Model):
    _name = "abatar.pagos.adjuntos"
    _description = "Abatar pagos de Deudas"
    _rec_name = 'name_gral'

    name_gral = fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date(string='Fecha de caja')
    adjunto = fields.Binary(string='Adjunto')
    desc = fields.Char(string="Descripcion")

    pagos_id = fields.Many2one('abatar.pagos', string='pagos ID')


    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'AD' + str(rec.id) + str(rec.adjunto)


class AbatarPagosFactura(models.Model):
    _name='abatar.pagos.factura'
    _description="Abatar Pagos Factura"
    _rec_name="factura_id"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.factura_id:
                revisad = self.env['abatar.factura'].search(
                    [('id', '=', rec.factura_id.id),('active', 'in', (True, False))])
                revisad.write({'active': True})
                revisad.write({'pagos':  False})
                revisad.write({'pagos_id':  0})

        res = super(AbatarPagosFactura, self).unlink()
        return res



    #ES COMO EL DEFAULT
    @api.depends('pagos_id.clientes_id')
    def set_clientes_id(self):
        for rec in self:
            if rec.pagos_id.clientes_id:
                rec.clientes_id=rec.pagos_id.clientes_id.id



    clientes_id=fields.Many2one(string="clientes_id", compute='set_clientes_id', store=True, readonly=True) # created 2do_parent or "Related" Many2one
    factura_id=fields.Many2one('abatar.factura', string="Factura", required=True)
    factura_name=fields.Char(string="N° Factura", related='factura_id.name_seq', store=True, readonly=True)
    factura_total=fields.Float(string="Total Factura", related='factura_id.total', store=True, readonly=True)
    pagos_id = fields.Many2one('abatar.pagos', string="pagos_id")


    @api.multi
    def write(self, vals):

        res = super(AbatarPagosFactura, self).write(vals)
        if 'factura_id' in vals:
            if vals.get('factura_id'):
                valor_nuevo = self.env['abatar.factura'].search(
                    [('id', '=', vals.get('factura_id'))])
                valor_nuevo.write({'pagos': res.pagos_id.id})
                valor_nuevo.write({'pagos_id': res.pagos_id.id})
                valor_nuevo.write({'active': False})

                valor_viejo = self.env['abatar.factura'].search(
                    [('id', '=', self.factura_id.id)])
                valor_viejo.write({'active': True})
                valor_viejo.write({'pagos': False})
                valor_viejo.write({'pagos_id': 0})


        return res


    @api.model
    def create(self, vals):

        result = super(AbatarPagosFactura, self).create(vals)
        if vals.get('factura_id'):
            revisac = self.env['abatar.factura'].search([('id', '=', vals.get('factura_id'))])
            revisac.write({'pagos': result.pagos_id.id})
            revisac.write({'pagos_id': result.pagos_id.id})
            revisac.write({'active': False})


        return result

