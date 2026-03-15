from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

from datetime import timedelta, datetime
class AbatarProductos(models.Model):
    _name = "abatar.productos"
    _description = "Abatar productos"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name"

    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    name = fields.Char(string='Producto')
    kgs = fields.Integer(string='Kgs (ud)')
    m3 = fields.Integer(string='M3 (ud)')
    letra = fields.Char(string='Letra (ud)')
    desc = fields.Char(string='Descripcion')
    minimo = fields.Integer(string='Minimo')
    cantidad = fields.Integer(string='Cantidad')
    cant_op_carga = fields.Integer(string='Operarios Carga')
    tiempo_carga = fields.Float(string='Tiempo de carga')
    precio = fields.Float(string='Costo xHr Default', required=True)
    tipo = fields.Many2one('abatar.tipo', string='Tipo', required=True)
    image = fields.Binary(string='Imagen', attachment=True)
    es_flete = fields.Boolean(string='es Ud, Op o Grua?', default=True)
    es_embalaje = fields.Boolean(string='es Mat Emb?',default=False)
    es_gratis = fields.Boolean(string='Es gratis?',help='(X el momento para prods de tabla tipo servicios Ud Op o Grua) xEj el Acompañante, no se cobra y debe admitir tarifa 0',default=False)
    es_mat_consumo_interno = fields.Boolean(string='(Mat) No indicar en la venta',help='Para materiales que se cobran pero no se entregan al cliente en lisa de embalaje',default=False)

    @api.model
    def default_get(self, fields):

        revisa = self.env['abatar.tipo'].search([('name', '=', 'unidad')])
        rec = super(AbatarProductos, self).default_get(fields)
        rec['tipo'] = revisa.id

        return rec


    @api.onchange('tipo')
    def set_tipo(self):
        for rec in self:
            if rec.tipo.name == 'unidad' or rec.tipo.name == 'operario':
                rec.es_flete = True
                rec.es_embalaje = False
            else:
                if rec.tipo.name == 'embalaje':
                    rec.es_embalaje = True
                rec.es_flete = False


    @api.model
    def default_get(self, fields):
        rec = super(AbatarProductos, self).default_get(fields)

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
        res = super(AbatarProductos, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.productos.sequence') or _('New')
        result = super(AbatarProductos, self).create(vals)
        return result

class AbatarCompras(models.Model):
    _name = "abatar.compras"
    _description = "Abatar Facturas de compra"

    fecha_op = fields.Date(string='Fecha', required=True, default=datetime.today().date())
    proveedor = fields.Many2one('abatar.proveedores', string='Proveedor', required=True)
    state = fields.Selection(
        [('pendiente', 'Pendiente'), ('confirmado', 'Confirmado')],
        string='Status', default='pendiente')
    desc = fields.Char(string='Descripcion')
    subtotal = fields.Float(string='Subtotal',store=True, readonly=True, compute='set_subtotal')
    iva = fields.Float(string='IVA',store=True, readonly=True, compute='set_iva')
    total = fields.Float(string='Total', store=True, readonly=True,compute='set_total')
    factura = fields.Binary(string='Imagen', attachmenot=True)
    productos_lines = fields.One2many('abatar.compras.productos', 'compras_id', string='Productos')

    @api.depends('productos_lines.subtotal')
    def set_subtotal(self):
        if self.productos_lines:
            for rec in self.productos_lines:
                self.subtotal += rec.subtotal

    @api.depends('subtotal')
    def set_iva(self):
        if self.subtotal:
            self.iva = round(self.subtotal*0.21,2)

    @api.depends('iva')
    def set_total(self):
        if self.subtotal and self.iva:
            self.total = round(self.subtotal+self.iva,2)

    def ref_confirmacion(self):
        for rec in self:
            rec.state = "confirmado"

            for dec in rec.productos_lines:
                if dec.cantidad > 0:
                    dec.productos_id.cantidad += dec.cantidad



    def ref_cancelar(self):
        for rec in self:
            rec.state = "pendiente"

            for dec in rec.productos_lines:
                if dec.cantidad > 0:
                    dec.productos_id.cantidad -= dec.cantidad

class AbatarComprasProductos(models.Model):
    _name = "abatar.compras.productos"
    _description = "Abatar compras Productos"

    productos_id = fields.Many2one('abatar.productos', string='Producto')
    precio = fields.Float(string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='set_subto')
    cantidad = fields.Integer(string='Cantidad')

    compras_id = fields.Many2one('abatar.compras', string='Compras ID')


    @api.depends('precio', 'cantidad')
    def set_subto(self):
        for rec in self:
            if rec.precio > 0 and rec.cantidad > 0:
                rec.subtotal = rec.precio * rec.cantidad

class AbatarTipo(models.Model):
    _name = "abatar.tipo"
    _description = "Abatar Tipo"
    _rec_name = "name"

    name = fields.Char(string="Tipo", required=True)
    pc_gan = fields.Integer(string="Porcentaje de Ganancia habitual")
    es_consumible = fields.Boolean(string="Es consumible?", default=True)


