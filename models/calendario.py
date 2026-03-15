from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
class AbatarCalendario(models.Model):
    _name = "abatar.calendario"
    _description = "Abatar calendario"
    _rec_name = "name"

    @api.multi
    def unlink(self):
        for rec in self:
            rec.ordenes=False
            rec.deudas=False
            rec.materiales=False
            rec.calendario_lines= [(5,0,0)]
        res = super(AbatarCalendario, self).unlink()

        return res

    active = fields.Boolean('Active', default=True)

    name = fields.Text(string="name")#, compute='set_nombre_com', default='')
    name2 = fields.Char(string="name2")
    name3 = fields.Char(string="name3")
    name4 = fields.Char(string="name4")
    name5 = fields.Char(string="name5")
    name6 = fields.Char(string="name6")
    name7 = fields.Char(string="name7")
    name_oculto = fields.Char(string="name_oculto")
    ordenes = fields.Many2one('abatar.ordenes', string='Ordenes')
    deudas = fields.Many2one('abatar.deudas', string='Deuda')
    materiales = fields.Many2one('abatar.materiales', string='Boleta Mat.')
    accion = fields.Many2one('abatar.servicios.calendario', string='Accion')
    precio = fields.Float(string="Precio")
    minimo = fields.Float(string="Cantidad")
    duration = fields.Float(string="Duracion", default=2.5)
    total = fields.Float(string="Total")
    desc = fields.Text(string="Descripción")
    fecha_ejecucion = fields.Datetime(string='Fecha del Servicio')
    calendario_lines = fields.One2many('abatar.calendario.crm', 'calendario_id', string='Registro de gastos')


    recontactar = fields.Date(string='Recontactar')
    name_seq = fields.Char(string="name_seq")

    #@api.depends('calendario_lines.crm', 'ordenes', 'deudas')
    #def set_nombre_com(self):
    #    for rec in self:
    #        rec.name = ''
    #        for ei in rec.calendario_lines:
    #            if ei:
    #                rec.name = '%s-%s' % (rec.name, ei.crm.name_seq)

    #        if rec.ordenes:
    #            rec.name = '%s' % (rec.ordenes.name_seq)
    #        if rec.deudas:
    #            rec.name = rec.deudas.name_gral
    #        if rec.materiales:
    #            rec.name = rec.materiales.name_gral

    @api.multi
    def action_view_ordenes(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'res_id': self.ordenes.id,
        }

    @api.multi
    def write(self, vals):

        res = super(AbatarCalendario, self).write(vals)
        if 'fecha_ejecucion' in vals:
            if self.ordenes:
                revisac = self.env['abatar.ordenes'].search(
                    [('id', '=', self.ordenes.id)])
                if revisac:
                    for ei in revisac:
                        if str(ei.fecha_ejecucion) != vals.get('fecha_ejecucion'):
                            ei.write({'fecha_ejecucion': vals.get('fecha_ejecucion')})

        return res

class AbatarCalendarioCrm(models.Model):
    _name = "abatar.calendario.crm"
    _description = "Abatar calendario"

    crm = fields.Many2one('abatar.crm', string='CRM')
    orden = fields.Many2one('abatar.ordenes', string='ORDEN')
    pago = fields.Many2one('abatar.pagos', string='PAGOS')
    deuda = fields.Many2one('abatar.deudas', string='DEUDAS')
    material = fields.Many2one('abatar.materiales', string='BOLETA MATERIALES')
    calendario_id = fields.Many2one('abatar.calendario', string='CRM')