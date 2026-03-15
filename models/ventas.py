from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

from datetime import timedelta, datetime
import calendar

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON
def redond(x):
    if x - int(x) >= 0.25:
        if x - int(x) >= 0.75:
            return int(x) + 1
        else:
            return int(x) + 0.5
    else:
        return int(x)


class AbatarVentas(models.Model):
    _name = "abatar.ventas"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _description = "Abatar Ventas"
    _rec_name = "name_gral"
    _order = "fecha_ejecucion asc"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.calendario:
                rec.calendario.unlink()
                rec.calendario=False
            

        res = super(AbatarVentas, self).unlink()
        return res

    name_gral=fields.Char(string="Nombre de rec", store=True, readonly=True, compute='set_name_gral')
    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    empresa = fields.Char(string='Empresa')
    contacto = fields.Char(string='Responsable')
    tel = fields.Char(string='Telefono')
    email = fields.Char(string='Email')

    desc = fields.Text(string='Descripcion')

    crm = fields.Many2one('abatar.crm', string='CRM')#, states={'finalizo': [('readonly', True)]})
    accion_n = fields.Integer(string='Accion', store=True, readonly=True, compute='set_accion')

    orden_lines = fields.One2many('abatar.ordenes.lines', 'orden_id', string='Linea de Personal') #, states={'finalizo': [('readonly', True)]}

    state = fields.Selection(
        [('nuevo', 'Nuevo'), ('interesado', 'Interesado'), ('presupuestado', 'Presupuestado'),  ('ingresado', 'Ingresado'), ('cancelo', 'Cancelado')],
        string='Status', default='orden')

    destinos_resumen=fields.Char(string="Resumen para busqueda", store=True, readonly=True, compute='set_destinos_resumen')

    fecha_ingreso = fields.Datetime(string='Fecha de Ingreso', default=fields.Datetime.now())
    fecha_ultimo = fields.Datetime(string='Fecha de Ultimo contacto')
    fecha_ejecucion = fields.Datetime(string='Contacto Programado', required=True) #, states={'finalizo': [('readonly', True)]}
    fecha_ejecucion_name = fields.Char(string='Fecha del Servicio',compute='set_fecha_name')  # , states={'finalizo': [('readonly', True)]}
    fecha_ejecucion_name2 = fields.Char(string='Fecha del Servicio',
                                        compute='set_fecha_name')  # , states={'finalizo': [('readonly', True)]}
    fecha_ejecucion2 = fields.Char(string='Fecha de Ejecucion2', store=True,
                                   readonly=True, compute='set_fecha2')

    ejecucion_days = fields.Integer(string='Días para Recontactar')  # , compute='set_days_recontactar'
    fecha_mes_año = fields.Char(string="Mes y Año", store=True, readonly=True, compute='set_fecha_mes_año')

    active = fields.Boolean('Active', default=True)
    acciones_venta_lines = fields.One2many('abatar.ventas.acciones', 'crm_id', string='Acciones')
    adjuntos = fields.One2many('abatar.ventas.adjuntos', 'crm_id', string='Adjuntos')

    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user, states={'finalizo': [('readonly', True)]})

    calendario = fields.Many2one('abatar.calendario', string='Calendario')

    servicio = fields.Many2one('abatar.servicios.calendario', string='Servicio', required=True) #, states={'finalizo': [('readonly', True)]}
    servicio_name=fields.Char(related='servicio.name', store=True, readonly=True, string="Servicio Name")






    @api.model
    @api.onchange('fecha_ejecucion')
    def set_days_recontactar(self):
        if self:
            reco=self
        else:
            reco=self.env['abatar.crm'].search([])
        for rec in reco:
            if rec.fecha_ejecucion:
                fecha=datetime.strptime(rec.fecha_ejecucion.strftime('%d-%m-%Y'), '%d-%m-%Y').date()
                rec.ejecucion_days = abs((fecha - fields.Date.today()).days)
            else:
                rec.ejecucion_days = -2


    def set_fecha_name(self):
        for rec in self:
            text=''
            text2=''
            if rec.fecha_ejecucion:
                text=(rec.fecha_ejecucion-datetime.timedelta(hours=3)).strftime('%d/%m/%Y - %H:%M')
                text2=(rec.fecha_ejecucion-datetime.timedelta(hours=3)).strftime('%d/%m/%Y')
                dias={
                    calendar.weekday(2023, 4,3):'Lun',
                    calendar.weekday(2023, 4,4):'Mar',
                    calendar.weekday(2023, 4,5):'Mie',
                    calendar.weekday(2023, 4,6):'Jue',
                    calendar.weekday(2023, 4,7):'Vie',
                    calendar.weekday(2023, 4,8):'Sab',
                    calendar.weekday(2023, 4,9):'Dom',
                }
                if rec.fecha_ejecucion.weekday():
                    text=dias[rec.fecha_ejecucion.weekday()]+' '+text
                    text2=dias[rec.fecha_ejecucion.weekday()]+' '+text2
            rec.fecha_ejecucion_name=text
            rec.fecha_ejecucion_name2=text2


    @api.onchange('active')
    def quit_calend(self):
        for rec in self:
            if rec.active:
                pass
            else:
                if rec.calendario:
                    cal=self.env['abatar.calendario'].search([('id', '=', rec.calendario.id)])
                    cal.unlink()
                    rec.calendario=False



    @api.depends('crm')
    def set_accion(self):
        for rec in self:
            if rec.crm:
                if rec.crm.state in ('pendiente','presupuesto'):
                    rec.accion_n=2
                else:
                    rec.accion_n=1
            else:
                rec.accion_n=1

            if rec.fecha_ejecucion:
                rec.fecha_ejecucion2=rec.fecha_ejecucion.strftime('%Y-%m-%d')


    @api.depends('fecha_ejecucion')
    def set_fecha2(self):
        for rec in self:
            if rec.fecha_ejecucion:
                rec.fecha_ejecucion2=rec.fecha_ejecucion.strftime('%Y-%m-%d')


    @api.depends('name_seq','cliente')
    def set_name_gral(self):
        for line in self:
            if line.name_seq:
                line.name_gral=str(line.name_seq)
            if line.cliente:
                line.name_gral+=' '+ str(line.cliente)


    @api.depends('fecha_ejecucion')
    def set_fecha_mes_año(self):
        for r in self:
            if r.fecha_ejecucion:
                r.fecha_mes_año =  str(fields.Date.from_string(r.fecha_ejecucion).strftime('%m/%y'))


    def state_cancelo(self):
        for rec in self:
            if rec.state == 'ingresado':
                rec.state = "nuevo"
                self.message_post(body=_("Canceló la venta, volvio a estado Nuevo."))
                for dec in rec.orden_lines:
                    dec.state = rec.state


            return {
                'name': _('Ventas'),
                'view_type': 'form',
                'res_model': 'abatar.ventas',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }


    @api.onchange('name_seq','desc','crm','orden_lines','empresa','contacto','tel','email')
    def name_calendar(self):
        for many in self.env['abatar.ventas'].search([]):

            string = ''

            if many.pedide:
                string +=str(many.pedide)

            if many.crm:
                if many.crm.name_seq:
                    string += ' (' + str(many.crm.name_seq) + ')'

            if many.empresa:
                string += '\n' + many.empresa

            if many.contacto:
                string += '\n' + many.contacto.name
            if many.tel:
                string += '\n' + many.tel
            elif many.email:
                string += '\n' + many.email




    @api.depends('orden_lines.subtotal','precio_convenido')
    def set_subtotal(self):
        for rec in self:
            if rec.precio_convenido > 0:
                rec.subtotal = rec.precio_convenido
            else:
                for dec in rec.orden_lines:

                    rec.subtotal += dec.subtotal
                    if rec.state != 'orden':
                        dec.state = rec.state
                    if dec.proveedor_producto.subtipo.tipo.name == 'unidad':
                        rec.tarifas_precio = dec.proveedor_producto.subtipo.id
                for dec in rec.embalaje_lines:
                    if dec.embalaje_id and dec.cantidad:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        precio=tar.productos_lines.search([('productos_id', '=', dec.embalaje_id.id)], limit=1).tarifas_precio
                        rec.subtotal_teo+=precio*dec.cantidad

    @api.depends('crm')
    def set_tiene_precio(self):
        for rec in self:
            if rec.crm:
                rec.tiene_precio = True
            else:
                rec.tiene_precio = False


    @api.depends('fecha_ejecucion')
    def datetime_to_float(self):
        for rec in self:
            if rec.fecha_ejecucion:

                secs = rec.fecha_ejecucion.time()
                new_time = str(secs)
                time = new_time.replace(":", ",")
                nue_valor1 = ""
                nue_valor2 = ""

                for dec in range(2):
                    nue_valor1 = nue_valor1 + time[dec]

                for dec in range(2):
                    nue_valor2 = nue_valor2 + time[dec + 3]

                nue_valor3 = float(nue_valor2) / 60
                valor_final = (float(nue_valor1) - 3) + nue_valor3

                rec.hora_inicio = valor_final



    @api.onchange('destinos_lines','destinos_lines2')
    def _es_par_wey(self):
        for rec in self:

            numero = 0
            for cu in rec.destinos_lines:
                numero += 1
                resto = numero % 2
                if resto == 0:
                    cu.es_par = True
                else:
                    cu.es_par = False

            numero = 0
            for cu in rec.destinos_lines2:
                numero += 1
                resto = numero % 2
                if resto == 0:
                    cu.es_par = True
                else:
                    cu.es_par = False

    @api.multi
    def action_view_crm(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.crm',
            'res_id': self.crm.id,
        }

    @api.multi
    def action_crea_relacionado(self):

        vemos = self.copy(
            {
                'pedide': self.pedide,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'res_id': vemos.id,
        }

    @api.multi
    def action_view_deudas(self):
        return {
            'name': _('Deudas'),
            'domain': [('orden', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.deudas',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


    @api.multi
    def action_view_resumenes(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.resumenes',
            'res_id': self.resumenes.id,
        }


    @api.multi
    def write(self, vals):
        for many in self:

            if vals.get('ver_horas'):
                vals['ver_horas']=False
            if vals.get('ver_direc'):
                vals['ver_direc']=False
            if vals.get('ver_prov'):
                vals['ver_prov']=False
            if vals.get('ver_cobros'):
                vals['ver_cobros']=False

            if 'fecha_ejecucion' in vals:
                revisac = self.env['abatar.calendario'].search(
                    [('ordenes', '=', many.id)])
                if revisac:
                    for ei in revisac:
                        string=''
                        if str(ei.fecha_ejecucion) != vals.get('fecha_ejecucion'):
                            if vals.get('servicio'):
                                ei.write({'accion': vals.get('servicio')})
                            else:
                                ei.write({'accion': many.servicio.id})
                            ei.write({'fecha_ejecucion': vals.get('fecha_ejecucion')})

                            string = ''
                            if vals.get('name_seq'):
                                string += str(vals.get('name_seq'))
                            elif many.name_seq:
                                string+=str(many.name_seq)

                            if vals.get('pedide'):
                                string += str(vals.get('pedide'))
                            elif many.pedide:
                                string+=str(many.pedide)

                            if vals.get('crm'):
                                crm= self.env['abatar.crm'].search([('id', '=', vals.get('crm'))], limit=1)
                                if crm.m3_flete:
                                    string+=' ('+str(crm.m3_flete)+')'
                                elif crm.mdz_m3_auto:
                                    string+=' ('+str(crm.mdz_m3_auto)+')'
                            elif many.crm:
                                if many.crm.m3_flete:
                                    string+=' ('+str(many.crm.m3_flete)+')'
                                elif many.crm.mdz_m3_auto:
                                    string+=' ('+str(many.crm.mdz_m3_auto)+')'

                            if vals.get('ud_ppal'):
                                string+='-'+vals.get('ud_ppal')
                            elif many.ud_ppal:
                                string+='-'+many.ud_ppal
                            if vals.get('op_sv'):
                                string+='-'+str(vals.get('op_sv'))
                            elif many.op_sv:
                                string+='-'+str(many.op_sv)

                            if vals.get('cliente'):
                                CLI=vals.get('cliente')
                                CLI2=self.env['abatar.clientes'].search([('id', '=', CLI)], limit=1)

                                string+=' '+CLI2.name_gral2
                            elif many.cliente:
                                CLI2=many.cliente
                                string+=' '+CLI2.name_gral2
                            elif vals.get('empresa'):
                                string+=' '+vals.get('empresa')
                            elif many.empresa:
                                string+=' '+many.empresa


                            if vals.get('contacto'):
                                string+=' '+self.env['abatar.clientes.lines'].search(('id', '=',vals.get('contacto')), limit=1).name
                            elif many.contacto:
                                string+=' '+ many.contacto.name
                            elif vals.get('name'):
                                string+=' '+ vals.get('name')
                            elif many.name:
                                string+=' '+ many.name


                            ei.write({'name': string})

            elif vals.get('servicio'):
                revisac = self.env['abatar.calendario'].search(
                    [('ordenes', '=', many.id)])
                if revisac:
                    for ei in revisac:
                        ei.write({'accion': vals.get('servicio')})

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
        res = super(AbatarVentas, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        revisa = self.env['abatar.tipo'].search([('name', '=', 'unidad')])

        rec = super(AbatarVentas, self).default_get(fields)

        rec['servicio'] = 3
        rec['id_unidad'] = revisa.id
        print('DEFAULT ORDENES', self, self.crm, self.crm.fecha_inicial)
        if self.crm:
            rec['fecha_pedido'] = self.crm.fecha_inicial

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.model
    def create(self, vals):
        if vals.get('forc_name_seq'):
            if vals.get('name_seq', _('New')) == _('New'):
                vals.update({'name_seq': str(vals.get('forc_name_seq'))})
        else:
            if vals.get('name_seq', _('New')) == _('New'):
                vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.ordenes.sequence') or _('New')


        if vals.get('forc_pedide'):
            if vals.get('pedide', _('New')) == _('New'):
                vals.update({'pedide': vals.get('forc_pedide')})
        else:
            if vals.get('pedide', _('New')) == _('New'):
                vals['pedide'] = self.env['ir.sequence'].next_by_code('abatar.pedido.sequence') or _('New')

        result = super(AbatarVentas, self).create(vals)
        if vals.get('name_seq'):
            string = vals.get('name_seq')
        else:
            string=""
        if vals.get('ud_ppal'):
            string+=' - '+str(vals.get('ud_ppal'))
            if vals.get('op_sv'):
                string+='/'+str(vals.get('op_sv'))
            else:
                string+='/0'
        elif vals.get('op_sv'):
            string+=' - XXX/'+str(vals.get('op_sv'))
        else:
            string+=' - XXX/0'

        if vals.get('clientes'):
            if vals.get('contacto'):
                cont=self.env['abatar.clientes.lines'].search([('id', '=', vals.get('contacto'))], limit=1)
                string+=' - '+str(cont.name)
                if vals.get('tel_cliente'):
                    string+=' - ' +str(vals.get('tel_cliente'))
                elif vals.get('email_cliente'):
                    string+=' - ' +str(vals.get('email_cliente'))
        elif vals.get('name'):
            if vals.get('empresa'):
                string+= ' - '+ str(vals.get('empresa'))
            string += ' - ' + str(vals.get('name'))
            if vals.get('tel'):
                string += ' - ' + str(vals.get('tel'))
            elif vals.get('email'):
                string += ' - ' + str(vals.get('email'))

        calen_id=self.env['abatar.calendario'].search([], order='id desc', limit=1).id+1
        vals2 = {
            'name': string,
            'accion': vals.get('servicio'),
            'ordenes': result.id,
            'calendario_lines': [(0,0, {'orden':result.id,'calendario_id':calen_id})],
            'deudas': False,
            'materiales': False,
            'fecha_ejecucion': vals.get('fecha_ejecucion')
        }

        vals['calendario'] = self.env['abatar.calendario'].create(vals2).id


        return result


class AbatarVentasAdjuntos(models.Model):
    _name = "abatar.crm.adjuntos"
    _description = "Abatar adjuntos de crm"
    _rec_name = 'name_gral'

    name_gral=fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date("Fecha subida", default=fields.Date.today)
    adjunto = fields.Binary(string='Adjunto')
    name_adjunto = fields.Char(string='Nombre Adjunto')
    desc=fields.Char(string="Descripcion")

    crm_id = fields.Many2one('abatar.crm', string='crm ID')

    @api.one
    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral='AD'+str(rec.id)+str(rec.adjunto)

class AbatarVentasAcciones(models.Model):
    _name = "abatar.crm.acciones"
    _description = "Abatar Acciones de crm"
    _rec_name = 'venta_accion'
    _order = 'fecha desc'

    venta_accion=fields.Many2one('abatar.acciones.presupuesto',string='Acciones venta', required=True)
    fecha = fields.Date("Fecha", default=fields.Date.today)
    desc=fields.Char(string="Descripcion")

    crm_id = fields.Many2one('abatar.crm', string='crm ID')



class AbatarVentasLines(models.Model):
    _name = "abatar.ventas.lines"
    _description = "Abatar ventas lines"
    _rec_name = "fecha"




    fecha=fields.Datetime('fecha de contacto', default=fields.datetime.today())
    desc=fields.Text('Conversacion')
    orden_id = fields.Many2one('abatar.ventas', string='Orden ID', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('adelanto'):
            if vals.get('orden_id') and vals.get('proveedor_id') and vals.get('precio_pactado'):
                vals1={
                    'fecha':fields.datetime.now(),
                    'proveedor':vals.get('proveedor_id'),
                    'deuda':vals.get('adelanto'),
                    'orden':vals.get('orden_id')
                }
                res=self.env['abatar.deudas'].create(vals1)
                vals['adelanto_id']=res.id
        result = super(AbatarVentasLines, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if vals.get('adelanto'):
            if self.adelanto and self.adelanto_id:
                resul=self.env['abatar.deudas'].search([('id', '=', self.adelanto_id.id)], limit=1)
                resul.deuda=vals.get('adelanto')
            else:
                if vals.get('proveedor_id'):
                    prov=vals.get('proveedor_id')
                elif self.proveedor_id:
                    prov=self.proveedor_id.id
                vals1 = {
                    'fecha': fields.datetime.now(),
                    'proveedor': prov,
                    'deuda': vals.get('adelanto'),
                    'orden': self.orden_id.id
                }
                res = self.env['abatar.deudas'].create(vals1)
                vals['adelanto_id'] = res.id
        elif vals.get('adelanto') in (0, False):
            if self.adelanto_id:
                resul=self.env['abatar.deudas'].search([('id', '=', self.adelanto_id.id)], limit=1)
                resul.unlink()
                vals['adelanto_id']=False

        res = super(AbatarVentasLines, self).write(vals)
        return res


    @api.model
    def default_get(self, fields):

        revisap = self.env['abatar.ordenes'].search(
            [('id', '=', self.env.context.get('id_activo'))])

        rec = super(AbatarVentasLines, self).default_get(fields)

        rec['hora_inicio'] = revisap.hora_inicio

        return rec
class AbatarDestinosLines(models.Model):
    _name = "abatar.destinos.lines"
    _description = "Abatar destinos lines"
    _rec_name='destino_id'

    @api.onchange('destino_id')
    def domain_onchange(self):
        for rec in self:
            if rec.orden_id:
                rec.cliente = rec.orden_id.cliente
            if rec.orden_id_x:
                rec.cliente = rec.orden_id_x.cliente

    destino_id = fields.Many2one('abatar.direcciones', string='Direccion')
    cliente = fields.Many2one('abatar.clientes', store=True, readonly=True, compute='set_cliente', string='clientes')
    destino_contacto = fields.Char(string='Contactos')
    destino_tipo = fields.Selection([
            ('origen', 'Origen'),
            ('destino', 'Destino')], string='Tipo')


    pauta = fields.Text(string='Pauta')
    autoelev=fields.Boolean(string='C/Autoelev.')
    m3_escalera_c=fields.Integer(string='N Bultos Bajan esc.')
    m3_escalera_d=fields.Integer(string='N Bultos Suben esc.')

    es_par = fields.Boolean(string='Es par')
    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='CRM ID')
    orden_id_x_sv=fields.Char(related='orden_id_x.servicio_name', store=True, readonly=True, string="Servicio")



    @api.onchange('destino_id')
    def set_contacto(self):
        for rec in self:
            if rec.destino_id:
                if rec.destino_id.contacto:
                    rec.destino_contacto=rec.destino_id.contacto

    def set_cliente(self):
        for rec in self:
            if rec.orden_id:
                rec.cliente=rec.orden_id.cliente.id
            elif rec.orden_id_x:
                rec.cliente=rec.orden_id_x.cliente.id
