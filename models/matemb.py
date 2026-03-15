from odoo import models, fields, tools, api, _

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime

class AbatarMatemb(models.Model):
    _name = "abatar.matemb"
    _description = "Abatar Materiales de Emb"
    _inherit = ['abataradd.resumenbus']
    _rec_name='name'
    
    productos_id=fields.Many2one('abatar.productos',domain=[('tipo', '=', 'embalaje')], string="Producto")
    name=fields.Char(related='productos_id.name', store=True, readonly=True, string="Elemento")


    cant_total=fields.Integer(string="Cantidad Total", default=0)
    cant_disp = fields.Integer(string="Cantidad Disponible", store=True, readonly=True, compute='set_cant_disp')
    cant_uso=fields.Integer(string="Cantidad en Uso", default=0)

    mov_lines=fields.One2many('abatar.matemb.lines', 'matemb_id', string="Movimientos")


    @api.model
    def default_get(self, fields):
        rec = super(AbatarMatemb, self).default_get(fields)

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
        res = super(AbatarMatemb, self).write(vals)
        return res

    @api.depends('cant_total', 'cant_uso')
    def set_cant_disp(self):
        print('hi_insu')
        for rec in self:
            if rec.cant_total:
                rec.cant_disp = rec.cant_total
                if rec.cant_uso:
                    if rec.cant_uso>0:
                        print('cant uso', rec.cant_uso)
                        rec.cant_disp -= rec.cant_uso


class AbatarMatembLines(models.Model):
    _name = "abatar.matemb.lines"
    _description = "Abatar Matemb Lines disponibles"
    _rec_name='name_gral'

    matemb_id=fields.Many2one('abatar.matemb',string="matemb_id")
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

