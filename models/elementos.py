from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
import base64
from lxml import etree
import json
import simplejson

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime

class AbatarElementos(models.Model):
    _name = "abatar.elementos"
    _description = "Abatar Indumentaria disponible"
    _inherit = ['abataradd.resumenbus']
    _rec_name='name'

    name=fields.Char(string="Elemento")
    cant_total=fields.Integer(string="Cantidad Total", default=0)
    cant_uso=fields.Integer(string="Cantidad en Uso", default=0)
    cant_disp = fields.Integer(string="Cantidad Disponible",store=True, readonly=True, compute='set_cant_disp')

    mov_lines=fields.One2many('abatar.elementos.lines', 'elementos_id', string="Movimientos")
    active = fields.Boolean('Active', default=True)

    @api.model
    def default_get(self, fields):
        rec = super(AbatarElementos, self).default_get(fields)

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
        res = super(AbatarElementos, self).write(vals)
        return res

    @api.depends('cant_total', 'cant_uso')
    def set_cant_disp(self):
        for rec in self:
            if rec.cant_total:
                rec.cant_disp = rec.cant_total
                if rec.cant_uso:
                    rec.cant_disp -= rec.cant_uso



class AbatarElementosLines(models.Model):
    _name = "abatar.elementos.lines"
    _description = "Abatar Elementos Lines disponibles"
    _rec_name='name_gral'

    elementos_id=fields.Many2one('abatar.elementos',string="elementos_id")
    fecha_op=fields.Date(string="Fecha de op", default=fields.Date.today())
    cant=fields.Integer(string="Cantidad")
    desc=fields.Char(string="Desc.")
    ordenes_id=fields.Many2one('abatar.ordenes', string="Orden id")
    name_gral=fields.Char(computed='set_name_gral', string="Name_rec")

    @api.depends('fecha_op', 'cant', 'ordenes_id')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=''
            if rec.fecha_op:
                rec.name_gral+=fields.Date.from_string(rec.fecha_op).strftime('%d/%m/%Y')
            if rec.cant:
                rec.name_gral+=' - cant:'+str(rec.cant)
            if rec.ordenes_id:
                rec.name_gral+=' - '+str(rec.ordenes_id.name_seq)

