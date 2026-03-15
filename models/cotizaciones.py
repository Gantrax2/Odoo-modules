from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime

class AbatarCotizaciones(models.Model):
    _name = "abatar.cotizaciones"
    _description = "Abatar Cotizaciones"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name_gral"

    fecha=fields.Date(string='Fecha ult. actualiz')
    name_gral = fields.Char(string='Cotizacion', store=True, readonly=True, compute='set_name_gral')
    name = fields.Char(string='Cotizacion', required=True)
    crm = fields.Many2one('abatar.crm', default=False, string='Presupuesto CRM')
    cliente = fields.Many2one('abatar.clientes', default=False, string='Cliente', required=True)
    precio = fields.Float(string='Precio Sin IVA', required=True)
    texto_adicional = fields.Char(string='Texto adicionales', default='')
    precio_adicional = fields.Float(string='Precio adicionales', default=0)
    active = fields.Boolean(string='Activo', default=True)


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
        res = super(AbatarCotizaciones, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AbatarCotizaciones, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.depends('name','cliente','precio')
    def set_name_gral(self):
        for line in self:
            line.name_gral=''
            if line.cliente:
                if line.cliente.name_gral2:
                    line.name_gral+= line.cliente.name_gral2
                elif line.cliente.clientes_gral_id and line.cliente.sector:
                    line.name_gral+= line.cliente.clientes_gral_id.name + ' ' + line.cliente.sector
            if line.name:
                line.name_gral+=' '+line.name
            if line.precio:
                line.name_gral+=' '+str(line.precio)

    def set_actualiz(self, aumento):
        for rec in self:
            rec.precio=rec.precio*aumento