# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import timedelta, datetime
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

class AbatarClientesGral(models.Model):
    _name = "abatar.clientes_gral"
    _description = "Abatar Carteras de Clientes"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name"

    name = fields.Char(string="Alias del Cliente", required=True)
    razon_social = fields.Char(string="Razon social del Cliente", required=True)
    tel = fields.Char(string="Telefono")
    email = fields.Char(string="Email")
    email_vto = fields.Char(string="Email Vto FC", help="Email para consulta de vencimiento de facturas")
    email_vto2 = fields.Char(string="Email Vto2 FC", help="Email para consulta de vencimiento de facturas")
    email_vto3 = fields.Char(string="Email Vto3 FC", help="Email para consulta de vencimiento de facturas")
    email_pagos = fields.Char(string="Email Reclamo Pagos", help="Email para reclamo de Pago de facturas")
    desc = fields.Text(string="Desc")
    dto=fields.Selection([('1', 'No aplica'), ('2', '10%'), ('3', '15%'), ('4', '20%'), ('5', '25%')], default='1', string="Descuento:")
    active=fields.Boolean(string="Activo", default=True)

    vto=fields.Integer(string="Días Vto. desde F.F.", default=15)
    sv_count=fields.Integer(string="Cantidad de usos",store=True, readonly=True, compute='get_sv_count')
    subtotal=fields.Integer(string="$ Total Facturado (s/iva)",store=True, readonly=True, compute='get_sv_count')
    costos=fields.Integer(string="$ Costo Total",store=True, readonly=True, compute='get_sv_count')
    ganancia=fields.Integer(string="$ Ganancia Total (s/iva)",store=True, readonly=True, compute='get_sv_count')
    subtotal_dolar=fields.Integer(string="Total Facturado (s/iva) (Blue)",store=True, readonly=True, compute='get_sv_count')
    costos_dolar=fields.Integer(string="Costo Total (Blue)",store=True, readonly=True, compute='get_sv_count')
    ganancia_dolar=fields.Integer(string="Ganancia Total (s/iva) (Blue)",store=True, readonly=True, compute='get_sv_count')
    subtotal_dolar2 = fields.Integer(string="Total Facturado (s/iva) (Dolar Of)", store=True, readonly=True, compute='get_sv_count')
    costos_dolar2 = fields.Integer(string="Costo Total (Dolar Of)", store=True, readonly=True, compute='get_sv_count')
    ganancia_dolar2 = fields.Integer(string="Ganancia Total (s/iva) (Dolar Of)", store=True, readonly=True, compute='get_sv_count')

    #@api.onchange('desc')
    #def actu(self):
    #    print('hey0')
    #    for rec in self.env['abatar.clientes'].search([]):
    #        print('hey0.1', rec)
    #        rec.get_sv_count()
    #    for rec in self.env['abatar.clientes_gral'].search([]):
    #        print('hey0', rec)
    #        rec.get_sv_count()

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
        res = super(AbatarClientesGral, self).write(vals)
        return res


    @api.model
    def default_get(self, fields):
        rec = super(AbatarClientesGral, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec
    def get_sv_count(self):
        print('hey')
        '''
        for one in self:
            count=0
            costos_pesos=0
            subtotal_pesos=0
            ganancia_pesos=0
            costos_dolar=0
            subtotal_dolar=0
            ganancia_dolar=0
            costos_dolar2=0
            subtotal_dolar2=0
            ganancia_dolar2=0
            for line in self.env['abatar.ordenes'].search([('cliente_gral', '=', one.id), ('active', 'in', (True,False))]):
                print('hey', line)
                count+=1
                costos_dolar+=line.costos_dolar
                subtotal_dolar+=line.subtotal_dolar
                ganancia_dolar+=line.ganancia_dolar
                subtotal_dolar2+=line.subtotal_dolar2
                costos_dolar2+=line.costos_dolar2
                ganancia_dolar2+=line.ganancia_dolar2
                costos_pesos+=line.costos
                subtotal_pesos+=line.subtotal
                ganancia_pesos+=(line.subtotal-line.costos)
            one.sv_count = count
            one.costos = costos_pesos
            one.subtotal = subtotal_pesos
            one.ganancia = ganancia_pesos
            one.subtotal_dolar = subtotal_dolar
            one.costos_dolar = costos_dolar
            one.ganancia_dolar = ganancia_dolar
            one.subtotal_dolar2 = subtotal_dolar2
            one.costos_dolar2 = costos_dolar2
            one.ganancia_dolar2 = ganancia_dolar2
        '''

class AbatarClientes(models.Model):
    _name = "abatar.clientes"
    _description = "Abatar Clientes"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'abataradd.resumenbus']
    _rec_name = "name_gral2"




    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    sector=fields.Char(string='Sector', track_visibility='always')

    clientes_gral_id=fields.Many2one('abatar.clientes_gral', default=False, string="Cartera Clientes")


    name_gral=fields.Char(string='Nombre completo Cliente', store=True, readonly=True,  compute='set_name_gral')
    name_gral2=fields.Char(string='Nombre Cliente', store=True, readonly=True, compute='set_name_gral2')
    cuit=fields.Char(strig="CUIT", track_visibility='always')
    tel = fields.Char(string='Telefono')
    tel2 = fields.Char(string='Telefono 2')
    email = fields.Char(string='Email')
    image = fields.Binary(string='Imagen', attachment=True)
    tarifas = fields.Many2one('abatar.tarifas', string='Tarifa')
    ordenes_r = fields.Integer(string='Ordenes Realizadas',store=True, readonly=True,  compute='cuenta_ordenes')
    ordenes_p2 = fields.Integer(string='Ordenes Pendientes', compute='cuenta_ordenesp2')
    ordenes_p = fields.Integer(string='Ordenes Pendientes')
    direcciones_r = fields.Integer(string='Direcciones Realizadas',store=True, readonly=True, compute='cuenta_direcciones')
    resumenes_r = fields.Integer(string='Resumenes Pendientes',store=True, readonly=True, compute='cuenta_resumenes')
    pagos_r = fields.Integer(string='Pagos Pendientes',store=True, readonly=True, compute='cuenta_pagos')
    clientes_lines = fields.One2many('abatar.clientes.lines', 'clientes_id', string='Responsables')

    res_pendiente=fields.Boolean(compute='set_res_pendiente', store=True, readonly=True, string="Resumenes pendiente?")
    res_pendiente_str=fields.Char(string="Tiene resumen pendiente?", default='No')
    res_pendiente_total=fields.Float(string="Deuda Pendiente")

    sv_count0=fields.Integer(string="Cantidad de usos",readonly=True, compute='get_sv_count0')
    sv_count=fields.Integer(string="Cantidad de usos",store=True, readonly=True, compute='get_sv_count')
    sv_count_fact=fields.Float(string="Facturacion",store=True, readonly=True, compute='get_sv_count')
    sv_count_fact_a=fields.Float(string="Facturacion Ultimo Año",store=True, readonly=True, compute='get_sv_count')
    f_u_c=fields.Float(string="Facturado/Cantidad",store=True, readonly=True, compute='get_sv_count')

    sv_count_fact_dolar=fields.Float(string="Facturacion U$d",store=True, readonly=True, compute='get_sv_count')
    sv_count_fact_a_dolar=fields.Float(string="Facturacion Ultimo Año U$d",store=True, readonly=True, compute='get_sv_count')
    f_u_c_dolar=fields.Float(string="Facturado/Cantidad U$d",store=True, readonly=True, compute='get_sv_count')
    active=fields.Boolean(string="Activo", default=True)

    @api.model
    def cuenta_ordenes_p(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = self.env['abatar.ordenes'].search_count([('cliente', '=', res.id), ('state', '=', 'finalizo'),  ('resumenes', '=', False)])
            res.write({'ordenes_p' : count})

    @api.model
    def cuenta_ordenes(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = self.env['abatar.ordenes'].search_count([('cliente', '=', res.id),  ('active', 'in', (True, False))])
            res.write({'ordenes_r' : count})


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
        res = super(AbatarClientes, self).write(vals)
        return res

    @api.model
    def cuenta_ordenesp2(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = self.env['abatar.ordenes'].search_count([('cliente', '=', res.id),('resumenes', '=', False),('state', '=', 'finalizo')])

            if count>=1:
                res.write({'ordenes_p2' : count})
            else:
                res.write({'ordenes_p2' : 0})


    @api.model
    def cuenta_direcciones(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = res.env['abatar.direcciones'].search_count([('cliente', '=', res.id)])
            res.write({'direcciones_r' : count})


    @api.model
    def cuenta_resumenes(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = self.env['abatar.resumenes'].search_count([('clientes_id', '=', res.id), ('factura', '=', False)])
            if count>=1:
                res.write({'res_pendiente':True})
                res.write({'res_pendiente_str':'Si'})
            else:
                res.write({'res_pendiente':False})
                res.write({'res_pendiente_str':'No'})
            res.write({'resumenes_r' : count})


    @api.model
    def set_res_pendiente(self):
        for res in self:#.env['abatar.clientes'].search([]):
            tot_pend=0
            if self.env['abatar.resumenes'].search([('clientes_id', '=', res.id), ('factura', '=', False)]):
                for res1 in self.env['abatar.resumenes'].search([('clientes_id', '=', res.id), ('factura', '=', False)]):
                    tot_pend+=res1.total
                res.write({'res_pendiente':True})
                res.write({'res_pendiente_str':'Si'})
                res.write({'res_pendiente_total':tot_pend})
            else:
                res.write({'res_pendiente':False})
                res.write({'res_pendiente_str':'No'})
                res.write({'res_pendiente_total':tot_pend})


    @api.model
    def cuenta_pagos(self):
        for res in self:#.env['abatar.clientes'].search([]):
            count = res.env['abatar.pagos'].search_count([('clientes_id.id', '=', res.id), ('caja', '=', False)])
            res.write({'pagos_r' : count})

    @api.model
    def get_sv_count0(self):
        for one in self:
            count=0
            for line in self.env['abatar.ordenes'].search(['|' ,('cliente.id', '=', one.id),'&', ('cliente.sector', '=', one.sector),('cliente_gral', '=', one.clientes_gral_id.id), ('active', 'in', (True,False))]):
                count+=1
            one.sv_count0 = count
            '''
            one.get_sv_count()
            one.cuenta_pagos()
            one.set_res_pendiente()
            one.cuenta_resumenes()
            one.cuenta_direcciones()
            one.cuenta_ordenesp2()
            one.cuenta_ordenes()
            '''

    @api.model
    def get_sv_count(self):
        for one in self:#.env['abatar.clientes'].search([]):
            count=0
            count_f=0
            count_f_a=0
            count_f_dolar=0
            count_f_a_dolar=0
            for line in self.env['abatar.ordenes'].search(['|' ,('cliente.id', '=', one.id),'&', ('cliente.sector', '=', one.sector),('cliente_gral', '=', one.clientes_gral_id.id), ('active', 'in', (True,False))]):
                count+=1
                count_f+=line.subtotal
                count_f_dolar+=line.subtotal_dolar

                if line.fecha_ejecucion:
                    dif_d2=fields.Datetime.from_string(fields.Datetime.now()).strftime('%d')
                    dif_d1=fields.Datetime.from_string(line.fecha_ejecucion).strftime('%d')
                    dif_m2=fields.Datetime.from_string(fields.Datetime.now()).strftime('%m')
                    dif_m1=fields.Datetime.from_string(line.fecha_ejecucion).strftime('%m')
                    dif_y2=fields.Datetime.from_string(fields.Datetime.now()).strftime('%y')
                    dif_y1=fields.Datetime.from_string(line.fecha_ejecucion).strftime('%y')
                    days=(int(dif_y2)-int(dif_y1))*365+(int(dif_m2)-int(dif_m1))*30+(int(dif_d2)-int(dif_d1))
                    if days<=365:
                        count_f_a+=line.subtotal
                        count_f_a_dolar+=line.subtotal_dolar
            one.write({'sv_count' : one.sv_count0 })
            one.write({'sv_count_fact' : count_f })
            one.write({'sv_count_fact_dolar' : count_f_dolar })
            one.write({'sv_count_fact_a' : count_f_a })
            one.write({'sv_count_fact_a_dolar' : count_f_a_dolar })
            if count and count_f:
               one.write({'f_u_c' : count_f/count })
               one.write({'f_u_c_dolar' : count_f_dolar/count })
            else:
               one.write({'f_u_c' : 0 })
               one.write({'f_u_c_dolar' : 0 })



    @api.multi
    def direcciones_cl(self):
        return {
            'name': _('Direcciones'),
            'domain': [('cliente', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.direcciones',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }


    @api.multi
    def resumenes_cl(self):
        return {
            'name': _('Resumenes'),
            'domain': [('clientes_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.resumenes',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


    @api.multi
    def pagos_cl(self):
        return {
            'name': _('Pagos'),
            'domain': [('clientes_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.pagos',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def ordenes_cl(self):
        return {
            'name': _('Ordenes'),
            'domain': [('cliente.sector', '=', self.sector), ('cliente_gral', '=', self.clientes_gral_id.id), ('active', 'in', [False, True])],
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def wsp(self):
        return {'name': 'Go to website',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': 'https://web.whatsapp.com/send?phone=%s' % self.tel,
                }

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.clientes.sequence') or _('New')
        result = super(AbatarClientes, self).create(vals)
        return result



    @api.model
    def default_get(self, fields):
        rec = super(AbatarClientes, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.depends('clientes_gral_id','sector')
    def set_name_gral(self):
        for line in self:
            line.name_gral =''
            if line.name_seq:
                line.name_gral=line.name_seq+' '
            if line.clientes_gral_id:
                line.name_gral += ' - '+str(line.clientes_gral_id.name)
            if line.sector and line.sector!="base":
                line.name_gral += ' - '+str(line.sector)

    @api.depends('clientes_gral_id','sector')
    def set_name_gral2(self):
        for line in self:
            name_gral2=""
            print('occas')
            if line.clientes_gral_id.name:
                name_gral2 += str(line.clientes_gral_id.name)
            if line.sector and line.sector!="base":
                name_gral2 += ' - '+str(line.sector)

            line.name_gral2=name_gral2



#FORMA DE APLICAR REFRESH A TODOS LOS NAME_GRAL2
#    @api.onchange('clientes_gral_id','sector')
#    def set_name_gral3(self):
#        print('hi')
#        for line in self.env['abatar.clientes'].search([]):
#            viejo=line.sector
#            if viejo[0]=="0":
#                if viejo[1]=="0":
#                    nuevo=viejo[2:]
#                else:
#                    nuevo=viejo[1:]
#            else:
#                nuevo=viejo
#            if nuevo==viejo:
#                pass
#            else:
#                print('nuevo')
#                line.write({'sector':nuevo})
#                print("hi3", line.name_gral2)



class AbatarClientesLines(models.Model):
    _name = "abatar.clientes.lines"
    _description = "Abatar clientes lines"
    _rec_name='name'

    name = fields.Char(string='Nombre')
    puesto = fields.Char(string='Puesto')
    tel = fields.Char(string='Telefono')
    tel2 = fields.Char(string='Telefono 2')
    email = fields.Char(string='Email')
    clientes_id = fields.Many2one('abatar.clientes', string='clientes_id')

