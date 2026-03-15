from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError

class AbatarBooleana(models.Model):
    _name = "abatar.booleana"
    _description = "Abatar Booleana"

    name=fields.Char(string="si o no")