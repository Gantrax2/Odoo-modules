from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import numpy as np

class AbatarKeyusuario(models.Model):
    _name = "abatar.keyusuario"
    _description = "Abatar Key usuarios"
    _rec_name = "keynum"
    _order ="keynum desc"

    fecha = fields.Date(string='Fecha de ingreso', default=fields.Date.today)
    keynum = fields.Integer(string='Key', required=True)
    fdp = fields.Selection([('efectivo', 'Efectivo'),('transferencia', 'Transferencia'),('cta cte','Cuenta Corriente')],string='Forma de pago')
    name = fields.Char(string='Nombre')
    tel = fields.Char(string='Telefono')
    empresa = fields.Char(string='Empresa')
    cliente = fields.Many2one('abatar.clientes', string='Cliente')

    @api.model
    def default_get(self, fields):
        rec = super(AbatarKeyusuario, self).default_get(fields)

        Searching=True
        while Searching:
            probenum=int(np.random.random()*99999.9)
            if self.env['abatar.keyusuario'].search_count([('keynum','=',probenum)])>0:
                pass
            else:
                Searching=False

        rec['keynum'] = probenum

        return rec