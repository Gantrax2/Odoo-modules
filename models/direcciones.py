from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON, PROVINCIAS

from datetime import timedelta, datetime

CABA_list = ['CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTONOMA DE BS AS',
             'CIUDAD AUTONOMA DE BS. AS.', 'CIUDAD AUTÓNOMA DE BUENOS AIRES', 'CAPITAL']


class AbatarDirecciones(models.Model):
    _name = "abatar.direcciones"
    _description = "Abatar direcciones"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'abataradd.resumenbus']
    _rec_name = "name_gral"

    name_gral = fields.Char(string='Direccion',store=True, readonly=True, compute='set_name_gral' ,track_visibility='always')
    name = fields.Char(string='Calle y altura', required=True, track_visibility='always')
    cliente = fields.Many2one('abatar.clientes', string='Cliente')
    cliente_gral = fields.Many2one('abatar.clientes_gral', string='C.Cliente',store=True, readonly=True, related='cliente.clientes_gral_id')
    piso = fields.Integer(string='Piso', track_visibility='always')
    dto = fields.Char(string='Dto / Lote ', track_visibility='always')
    localidad = fields.Char(string='Localidad', default='CABA', required=True, track_visibility='always')
    provincia = fields.Selection(PROVINCIAS, string='Provincia', default='Buenos Aires',
                                 required=True, track_visibility='always')
    alias = fields.Char(string="Nombre fantasía")
    contacto = fields.Char(string='Contacto de direccion')
    obs = fields.Char(string="Datos adicionales")
    forc_direc = fields.Char(string="Direccion")
    sv_count=fields.Integer(string="Cantidad de usos", compute='get_sv_count')
    active=fields.Boolean('Active', default=True)
    admin = fields.Boolean(string='Es Admin?', compute='set_admin')
    restricciones = fields.Text(string='Restricciones')

    def set_admin(self):
        for rec in self:
            if rec.env.user.id == 2:
                rec.admin = True
            else:
                rec.admin = False

    def get_sv_count(self):
        for one in self:
            count=0
            axi=one.id
            for line in self.env['abatar.ordenes'].search([]):
                for rec in line.destinos_lines:
                    if rec.destino_id.id== axi:
                        count+=  1
                    elif rec.destino_id.name_gral == one.name_gral:
                        count+=  1
            one.sv_count = count


    @api.model
    def default_get(self, fields):
        rec = super(AbatarDirecciones, self).default_get(fields)

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
        res = super(AbatarDirecciones, self).write(vals)
        return res

    @api.depends('alias','name','localidad','provincia','dto','piso','obs','forc_direc')
    def set_name_gral(self):
        for line in self:
            line.name_gral=''
            if line.forc_direc:
                line.name_gral=line.forc_direc.upper()
            else:
                if line.alias:
                    if str(line.alias)[0]=="\"":
                        line.name_gral += line.alias.upper() + ' - '
                    else:
                        line.name_gral+='\"'+line.alias.upper()+'\" - '
                if line.name:
                    line.name_gral+=line.name.upper()+', '
                if line.piso:
                    line.name_gral+='PISO '+ str(line.piso)+', '
                else:
                    line.name_gral+='P.B., '
                if line.dto:
                    line.name_gral+='DTO '+ line.dto.upper()+', '
                if line.localidad:
                    line.name_gral+=line.localidad.upper()
                    if line.provincia.upper() not in ['BUENOS AIRES', 'BS AS', 'BS. AS.', 'BA', 'B.A.']+CABA_list:
                        line.name_gral += ', ' + line.provincia.upper()
                if line.provincia and not line.name:
                    line.name_gral+=line.provincia.upper()
                elif line.provincia and not line.localidad:
                    line.name_gral+=line.provincia.upper()

