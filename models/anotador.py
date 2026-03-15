from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

class AbatarAnotador(models.Model):
    _name = "abatar.anotador"
    _description = "Abatar Anotador"

    name=fields.Char(string="Nombre")
    anotador=fields.Text(string="Anotador")