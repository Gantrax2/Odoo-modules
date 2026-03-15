from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

from datetime import timedelta, datetime
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON
class AbatarTarifas(models.Model):
    _name = "abatar.tarifas"
    _description = "Abatar Tarifas"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name_seq"

    def ref_general(self):
        for rec in self:
            if rec.es_general == True:
                rec.es_general = False
            else:
                busca = self.env['abatar.tarifas'].search(
                    [('es_general', '=', True), ('name_seq', '!=', rec.name_seq)])
                if busca:
                    raise UserError(_("Existe otra tarifa General"))
                else:
                    rec.es_general = True

    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    es_general = fields.Boolean(string='Es la general?',default=False)

    productos_lines = fields.One2many('abatar.tarifas.lines', 'tarifas_id', string='Linea de Productos')

    kms_lines = fields.One2many('abatar.tarifas.kms', 'tarifas_id', string='Linea de Kms')

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
        res = super(AbatarTarifas, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AbatarTarifas, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec


    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.tarifas.sequence') or _('New')
        result = super(AbatarTarifas, self).create(vals)
        return result



class AbatarTarifasLines(models.Model):
    _name = "abatar.tarifas.lines"
    _description = "Abatar tarifas lines"
    _order='numero_orden asc, id asc'

    numero_orden= fields.Integer('NºOrd.', help="Número para orden, de menor a mayor")
    productos_id = fields.Many2one('abatar.productos', string='Productos')
    tarifas_precio = fields.Float(string='Precio')
    tarifas_costo2 = fields.Float(string='Costo estimado')
    tarifas_minimo = fields.Float(string='Minimo')
    tarifas_id = fields.Many2one('abatar.tarifas', string='Tarifas ID')
    tarifas_precio_base = fields.Float(string='$ Precio mìnimo', store=True, readonly=True,compute='set_precio_min' )

    def tarifas_costo(self, algo):
        if algo.tarifas_precio:
            if algo.productos_id.tipo.pc_gan:
                por_costo=1+(algo.productos_id.tipo.pc_gan/100)
            else:
                por_costo=1.5
            return algo.tarifas_precio/por_costo
        else:
            try:
                return algo / 1.5
            except:
                return 0

    @api.depends('tarifas_minimo','tarifas_precio')
    def set_precio_min(self):
        for rec in self:
            if rec.tarifas_minimo and rec.tarifas_precio:
                rec.tarifas_precio_base= rec.tarifas_minimo*rec.tarifas_precio




class AbatarTarifasKms(models.Model):
    _name = "abatar.tarifas.kms"
    _description = "Abatar tarifas kms"
    _order='numero_orden asc, id asc'

    numero_orden= fields.Integer('NºOrd.', help="Número para orden, de menor a mayor")
    productos_id = fields.Many2one('abatar.productos', string='Productos')
    tarifas_precio = fields.Float(string='Precio')
    tarifas_id = fields.Many2one('abatar.tarifas', string='Tarifas ID')



    def tarifas_costo(self, algo):
        if algo.tarifas_precio:
            if algo.productos_id.tipo.pc_gan:
                por_costo=1+(algo.productos_id.tipo.pc_gan/100)
            else:
                por_costo=1.5
            return algo.tarifas_precio/por_costo
        else:
            try:
                return algo / 1.5
            except:
                return 0

class AbatarAumentos(models.Model):
    _name = "abatar.aumentos"
    _description = "Abatar aumentos"


    fecha = fields.Date(string='Fecha')
    aumento = fields.Float(string='Aumento masivo de Tarifas')


