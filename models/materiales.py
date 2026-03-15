from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
import time
import calendar

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON


class AbatarMateriales(models.Model):
    _name = "abatar.materiales"
    _description = "Ticket de Materiales"
    _inherit = ['abataradd.resumenbus']
    _rec_name='name_gral'

    @api.multi
    def unlink(self):
        for rec in self:

            if rec.calendario:
                rec.calendario.unlink()
                rec.calendario=False
            for ref in rec.producto_lines2:
                ref.unlink()
            for ref in rec.producto_lines3:
                ref.unlink()
            rec.write({'caja':False})
        res = super(AbatarMateriales, self).unlink()
        return res
    name_gral= fields.Char(string="Sujeto", compute='set_name_gral')
    proveedor_id=fields.Many2one('abatar.proveedores', string="Proveedor")
    fecha_op=fields.Date(String="Fecha de Compra")
    fecha_calen = fields.Datetime(string='Fecha de Pago programada')
    calendario = fields.Many2one('abatar.calendario', string='calendario', default=False)

    pago=fields.Float(string="Pago")
    fecha_pago=fields.Date(String="Fecha de Pago")

    active = fields.Boolean('Active', default=True)
    subtotal= fields.Float(string="Monto Total", compute='set_subtotal')
    mas_iva= fields.Boolean(string="+ IVA", default=False)
    percepciones= fields.Float(string="Percepciones" )
    monto= fields.Float(string="Monto Total", compute='set_monto')
    producto_lines2 = fields.One2many('abatar.materiales.productos', 'materiales_id', string="Listado de Materiales")
    producto_lines3 = fields.One2many('abatar.elementos.productos', 'materiales_id', string="Listado de Elementos")
    name_seq = fields.Char(string='Orden Reference', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    desc= fields.Text(string="Descripcion")
    caja=fields.Many2one('abatar.caja' , string="Caja_id")

    day_month=fields.Date(string="Fecha op", compute='set_day_month')
    adjunto= fields.One2many('abatar.materiales.adjuntos', 'materiales_id', string='Adjuntos')
    productos_resumen=fields.Char(string="Resumen productos", compute='set_productos_resumen')

    @api.depends('fecha_op')
    def set_day_month(self):
        for r in self:
            if r.fecha_op:
                r.nombre_fecha =  fields.Date.from_string(r.fecha_op).strftime('%d/%m')


    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.materiales.sequence') or _('New')
        res_id=self.env['abatar.materiales'].search([('active', 'in', (True, False))], order='id desc', limit=1).id+1
        result = super(AbatarMateriales, self).create(vals)

        if vals.get('fecha_calen'):
            pago=self.env['abatar.servicios.calendario'].search([('name', '=', 'Pagos')], limit=1).id
            calen_id=self.env['abatar.calendario'].search([], order='id desc', limit=1).id+1

            vals1 = {
                'material': res_id,
                'calendario_id': calen_id,
            }
            vals2 = {
                'name': vals.get('name_seq'),
                'accion': pago,
                'materiales': res_id,
                'deudas': False,
                'ordenes': False,
                'fecha_ejecucion': vals.get('fecha_calen'),
                'calendario_lines': [(0, 0, vals1)],

            }

            vals['calendario'] = self.env['abatar.calendario'].create(vals2).id
        return result

    @api.model
    def default_get(self, fields):
        rec = super(AbatarMateriales, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.multi
    def write(self, vals):

        if 'fecha_calen' in vals:
            if self.calendario:
                revisac = self.env['abatar.calendario'].search(
                    [('deudas', '=', self.id)])
                if revisac:
                    for ei in revisac:
                        if str(ei.fecha_ejecucion) != vals.get('fecha_calen'):
                            ei.write({'fecha_ejecucion': vals.get('fecha_calen')})

            else:
                calen_id = self.env['abatar.calendario'].search([], order='id desc',limit=1).id + 1
                pago=self.env['abatar.servicios.calendario'].search([('name', '=', 'Pagos')], limit=1).id

                vals1 = {
                    'material': self.id,
                    'calendario_id': calen_id,
                }

                vals2 = {
                    'name': self.name_seq,
                    'accion': pago,
                    'materiales': self.id,
                    'deudas': False,
                    'ordenes': False,
                    'fecha_ejecucion': vals.get('fecha_calen'),
                    'calendario_lines': [(0, 0, vals1)],
                }

                vals['calendario'] = self.env['abatar.calendario'].create(vals2).id

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
        res = super(AbatarMateriales, self).write(vals)
        return res
    @api.one
    @api.depends('producto_lines2','producto_lines3', 'mas_iva','percepciones')
    def set_monto(self):
        monto=0
        for rec in self.producto_lines2:
            monto+=rec.precio
        for rec in self.producto_lines3:
            monto+=rec.precio
        if self.mas_iva:
            monto=monto*1.21
        if self.percepciones:
            monto+=self.percepciones
        self.monto=round(monto, 2)

    @api.one
    @api.depends('producto_lines2', 'producto_lines3', 'pago')
    def set_subtotal(self):
        for rec in self:
            monto=0
            if rec.pago:
                monto+=rec.pago
            if rec.monto:
                monto -= rec.monto
            rec.subtotal=round(monto, 2)

    @api.one
    @api.depends('proveedor_id', 'desc', 'day_month', 'monto', 'name_seq')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=rec.proveedor_id.name
            if rec.monto:
                rec.name_gral += ' - $'+str(rec.monto)
            if rec.name_seq:
                rec.name_gral += ' - '+rec.name_seq
            if rec.day_month:
                rec.name_gral += ' - '+rec.day_month
            if rec.desc:
                rec.name_gral += ' - '+rec.desc


    @api.depends('producto_lines3','producto_lines2')
    def set_productos_resumen(self):
        for rec in self:
            rec.productos_resumen=''
            for prev in rec.producto_lines2:
                if prev.subtipo:
                    rec.productos_resumen += prev.subtipo.name
                if prev.desc:
                    rec.productos_resumen += ' - '+prev.desc+ ' - '

            for prev in rec.producto_lines3:
                if prev.elemento:
                    rec.productos_resumen += prev.elemento.name
                if prev.desc:
                    rec.productos_resumen += ' - '+prev.desc+ ' - '

    @api.multi
    def action_view_caja(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.caja',
            'res_id': self.caja.id,
        }

class AbatarMaterialesAdjuntos(models.Model):
    _name = "abatar.materiales.adjuntos"
    _description = "Abatar adjuntos de Materiales"
    _rec_name = 'name_gral'

    name_gral=fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date(string='Fecha de caja')
    adjunto = fields.Binary(string='Adjunto')
    desc=fields.Char(string="Descripcion")

    materiales_id = fields.Many2one('abatar.materiales', string='materiales ID')

    @api.one
    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral='AD'+str(rec.id)+str(rec.adjunto)

class AbatarMaterialesProductos(models.Model):
    _name='abatar.materiales.productos'
    _description = "Abatar Materiales Productos"
    _rec_name = "name_gral"



    @api.multi
    def unlink(self):
        for rec in self:
            if rec.subtipo:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', rec.subtipo.id)])
                if result:
                    result.cant_total-=rec.cantidad
                    result.write({'mov_lines': [(1, rec.materiales_lines_id.id,
                                                 {'ordenes_id': False,
                                                  'matemb_id': False
                                                  })]})
                    result.write({'mov_lines': [(2, rec.materiales_lines_id.id)]})
                    if result.cant_total==0 or result.cant_total==False:
                        result.unlink()

        res = super(AbatarMaterialesProductos, self).unlink()
        return res



    name_gral=fields.Char(string='REc name', compute='set_name_gral')
    subtipo = fields.Many2one('abatar.productos',domain="[('tipo', '=', 'embalaje')]", string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad', required=True)
    tarifa = fields.Float(string='Tarifa UD', required=True)

    precio= fields.Float(string='Precio', compute='set_precio')
    desc = fields.Char(string='Descripcion')
    materiales_id = fields.Many2one('abatar.materiales', string='materiales_id')
    materiales_lines_id = fields.Many2one('abatar.matemb.lines', string='materiales_lines_id')
    active = fields.Boolean('Active', default=True)
    @api.depends('subtipo')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=rec.subtipo.name

    @api.one
    @api.depends('cantidad', 'tarifa')
    def set_precio(self):
        self.precio=self.tarifa*self.cantidad




    @api.model
    def create(self, vals):
        result = super(AbatarMaterialesProductos, self).create(vals)
        print('create_mat:', result.id, vals)
        result2 = self.env['abatar.matemb'].search([('productos_id.id','=', vals.get('subtipo'))], limit=1)
        if result2:
            result2.cant_total+=vals.get('cantidad')
            result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % result.materiales_id.name_seq,
                                               'fecha_op':result.materiales_id.fecha_op,
                                               'cant':vals.get('cantidad'),
                                               'ordenes_id':False,
                                               'matemb_id' : result2.id
                                               })]})
        else:
            result2=self.env['abatar.matemb']
            result2.create({'productos_id':vals.get('subtipo'),
                            'cant_total':vals.get('cantidad')
                            })
            result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % result.materiales_id.name_seq,
                                               'fecha_op':result.materiales_id.fecha_op,
                                               'cant':vals.get('cantidad'),
                                               'ordenes_id':False,
                                               'matemb_id' : result2.id
                                               })]})

        result.materiales_lines_id = result2.mov_lines.search([], order='id desc', limit=1).id
        #for rec in result2.mov_lines:
        #    if [rec.fecha_op, rec.cant, rec.ordenes_id, rec.desc] == [result.materiales_id.fecha_op,vals.get('cantidad'),False,'Compra por Ticket %s.' % result.materiales_id.name_seq]:
        #        result.materiales_lines_id=rec.id
        #        break

        return result


    @api.multi
    def write(self, vals):
        if vals.get('subtipo'):
            if self.subtipo:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', self.subtipo.id)])
                if result:
                    if self.cantidad and result.cant_total:
                        result.cant_total-=self.cantidad
                        if self.materiales_lines_id.id:
                            result.write({'mov_lines': [(1, self.materiales_lines_id.id,
                                                         {'ordenes_id': False,
                                                          'matemb_id': False
                                                          })]})
                            result.write({'mov_lines': [(2, self.materiales_lines_id.id)]})
                            self.materiales_lines_id = False
            result2=self.env['abatar.matemb'].search([('productos_id.id', '=', vals.get('subtipo'))], limit=1)
            if vals.get('cantidad'):
                cat=vals.get('cantidad')
                result2.cant_total+=vals.get('cantidad')
                result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % self.materiales_id.name_seq,
                                                   'fecha_op':self.materiales_id.fecha_op,
                                                   'cant':vals.get('cantidad'),
                                                   'ordenes_id':False,
                                                   'matemb_id' : result2.id
                                                   })]})
            elif self.cantidad:
                cat=self.cantidad
                result2.cant_total+=self.cantidad
                result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % self.materiales_id.name_seq,
                                                   'fecha_op':self.materiales_id.fecha_op,
                                                   'cant':self.cantidad,
                                                   'ordenes_id':False,
                                                   'matemb_id' : result2.id
                                                   })]})
            self.materiales_lines_id = result2.mov_lines.search([], order='id desc', limit=1).id
            #for rec in result2.mov_lines:
            #    if [rec.fecha_op, rec.cant, rec.ordenes_id, rec.desc] == [self.materiales_id.fecha_op,
            #                                                              cat, False,
            #                                                              'Compra por Ticket %s.' % self.materiales_id.name_seq]:
            #        self.materiales_lines_id = rec.id
            #        break
        elif vals.get('cantidad'):
            if self.subtipo:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', self.subtipo.id)], limit=1)
                if result:
                    result.cant_total+=(vals.get('cantidad')-self.cantidad)
                    result.write({'mov_lines': [(1, self.materiales_lines_id.id,
                                                 {'cant':-vals.get('cantidad')})]})

        resultad = super(AbatarMaterialesProductos, self).write(vals)
        return resultad

class AbatarElementosProductos(models.Model):
    _name='abatar.elementos.productos'
    _description = "Abatar Elementos Productos"
    _rec_name = "name_gral"



    @api.multi
    def unlink(self):
        for rec in self:
            if rec.elemento:
                result=self.env['abatar.elementos'].search([('id', '=', rec.elemento.id)])
                if result:
                    result.cant_total-=rec.cantidad
                    result.write({'mov_lines': [(1, rec.elementos_lines_id.id,
                                                 {'ordenes_id': False,
                                                  'materiales_id': False
                                                  })]})
                    result.write({'mov_lines': [(2, rec.elementos_lines_id.id)]})
                    if result.cant_total==0 or result.cant_total==False:
                        result.unlink()

        res = super(AbatarElementosProductos, self).unlink()
        return res



    name_gral=fields.Char(string='REc name', compute='set_name_gral')
    elemento = fields.Many2one('abatar.elementos', string='Elemento', required=True)
    cantidad = fields.Float(string='Cantidad', required=True)
    tarifa = fields.Float(string='Tarifa UD', required=True)

    precio= fields.Float(string='Precio', compute='set_precio')
    desc = fields.Char(string='Descripcion')
    materiales_id = fields.Many2one('abatar.materiales', string='materiales_id')
    elementos_lines_id = fields.Many2one('abatar.elementos.lines', string='Elem line id')
    active = fields.Boolean('Active', default=True)

    @api.depends('elemento')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=rec.elemento.name

    @api.one
    @api.depends('cantidad', 'tarifa')
    def set_precio(self):
        self.precio=self.tarifa*self.cantidad




    @api.model
    def create(self, vals):
        result = super(AbatarElementosProductos, self).create(vals)
        print('create_mat:', result.id, vals)
        result2 = self.env['abatar.elementos'].search([('id','=', vals.get('elemento'))], limit=1)
        if result2:
            result2.cant_total+=vals.get('cantidad')
            result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % result.materiales_id.name_seq,
                                               'fecha_op':result.materiales_id.fecha_op,
                                               'cant':vals.get('cantidad'),
                                               'ordenes_id':False,
                                               'elementos_id' : result2.id
                                               })]})


            result.elementos_lines_id = result2.mov_lines.search([], order='id desc', limit=1).id


        return result


    @api.multi
    def write(self, vals):
        if vals.get('elemento'):
            if self.elemento:
                result=self.env['abatar.elementos'].search([('id', '=', self.elemento.id)])
                if result:
                    if self.cantidad and result.cant_total:
                        result.cant_total-=self.cantidad
                        if self.elementos_lines_id.id:
                            result.write({'mov_lines': [(1, self.elementos_lines_id.id,
                                                         {'ordenes_id': False,
                                                          'elementos_id': False
                                                          })]})
                            result.write({'mov_lines': [(2, self.elementos_lines_id.id)]})
                            self.elementos_lines_id = False
            result2=self.env['abatar.elementos'].search([('id', '=', vals.get('elemento'))], limit=1)
            if vals.get('cantidad'):
                cat=vals.get('cantidad')
                result2.cant_total+=vals.get('cantidad')
                result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % self.materiales_id.name_seq,
                                                   'fecha_op':self.materiales_id.fecha_op,
                                                   'cant':vals.get('cantidad'),
                                                   'ordenes_id':False,
                                                   'elementos_id' : result2.id
                                                   })]})
            elif self.cantidad:
                cat=self.cantidad
                result2.cant_total+=self.cantidad
                result2.write({'mov_lines':[(0,0,{'desc':'Compra por Ticket %s.' % self.materiales_id.name_seq,
                                                   'fecha_op':self.materiales_id.fecha_op,
                                                   'cant':self.cantidad,
                                                   'ordenes_id':False,
                                                   'elementos_id' : result2.id
                                                   })]})
            self.elementos_lines_id = result2.mov_lines.search([], order='id desc', limit=1).id
            #for rec in result2.mov_lines:
            #    if [rec.fecha_op, rec.cant, rec.ordenes_id, rec.desc] == [self.materiales_id.fecha_op,
            #                                                              cat, False,
            #                                                              'Compra por Ticket %s.' % self.materiales_id.name_seq]:
            #        self.materiales_lines_id = rec.id
            #        break
        elif vals.get('cantidad'):
            if self.elemento:
                result=self.env['abatar.elementos'].search([('id', '=', self.elemento.id)], limit=1)
                if result:
                    result.cant_total+=(vals.get('cantidad')-self.cantidad)
                    result.write({'mov_lines': [(1, self.elementos_lines_id.id,
                                                 {'cant':-vals.get('cantidad')})]})

        resultad = super(AbatarElementosProductos, self).write(vals)
        return resultad
