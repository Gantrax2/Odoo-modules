from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

class AbatarMails(models.Model):
    _name = "abatar.mails"
    _description = "Abatar mails"
    _rec_name = "mail_from"
    _order = "fecha desc"


    mail_from = fields.Char(string="Desde")
    mail_to = fields.Char(string="Para")
    asunto = fields.Char(string="Asunto")
    fecha = fields.Datetime(string="Fecha del Mail")
    texto = fields.Text(string="Cuerpo del mensaje")
    adjuntos= fields.One2many('abatar.mails.adjuntos', 'mails_id', string='Adjuntos')


class AbatarMailsAdjuntos(models.Model):
    _name = "abatar.mails.adjuntos"
    _description = "Abatar adjuntos de mail"
    _rec_name = 'name'

    name = fields.Char(string='Nombre')
    adjunto = fields.Binary(string='Adjunto')

    mails_id = fields.Many2one('abatar.mails', string='mail ID')



class AbatarInstitucional(models.Model):
    _name = "abatar.institucional"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _description = "Abatar institucional"
    _rec_name = "numero"
    _order = 'numero desc'

    numero = fields.Char(string='Numero', related='relacion.numero')
    relacion = fields.Many2one('abatar.relacion.institu',string='Relacion')
    desc = fields.Text(string='Descripcion')
    adjunto1 = fields.Binary(string='Adjunta Word')
    adjunto2 = fields.Binary(string='Adjunto PDF')
    fecha_creacion = fields.Date(string='Fecha de Creacion', default=datetime.now().strftime('%Y-%m-%d'))
    fecha_vencimiento = fields.Date(string='Fecha del Vencimiento')
    active = fields.Boolean('Active', default=True)
    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)

    @api.model
    def default_get(self, fields):
        rec = super(AbatarInstitucional, self).default_get(fields)

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
        res = super(AbatarInstitucional, self).write(vals)
        return res

    @api.constrains('relacion')
    @api.one
    def _check_your_field(self):
        if self.relacion.id < 1:
            raise UserError(_("No puede estar vacio el campo Relacion"))


class AbatarInstituRelacion(models.Model):
    _name = "abatar.relacion.institu"
    _description = "Abatar relacion"

    name = fields.Char(string='Nombre')
    numero = fields.Char(string='Numero Institucional')


class AbatarConstantes(models.Model):
    _name = "abatar.constantes"
    _description = "Abatar Constantes"

    name = fields.Char(string='Nombre')
    flotante = fields.Float(string='valor Decimal')
    entero = fields.Integer(string='valor Entero')
    char=fields.Char(string='valor Frase')
    booleano=fields.Boolean(string='valor Booleano')
    fecha=fields.Char(string='valor Fecha')
    fechatime=fields.Char(string='valor Fecha y Tiempo')
    date_time=fields.Datetime(string='valor especial Fecha y Tiempo')
    binario=fields.Char(string='valor Adjunto')