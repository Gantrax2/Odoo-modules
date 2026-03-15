from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
#import datetime
import calendar
from odoo.http import request

from datetime import timedelta, datetime
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON

NOT_NORMAL_TYPES=[type(fields.Many2one('abatar.clientes')),type(fields.One2many('abatar.ordenes.lines', 'orden_id'))]
COMPUTAR_TODO=True
def redond(x):
    if x - int(x) >= 0.25:
        if x - int(x) >= 0.75:
            return int(x) + 1
        else:
            return int(x) + 0.5
    else:
        return int(x)


class AbatarOrdenes(models.Model):
    _name = "abatar.ordenes"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _description = "Abatar ordenes"
    _rec_name = "name_gral"
    _order = "fecha_ejecucion asc"

    @api.multi
    def unlink(self):
        for rec in self:

            if rec.calendario:
                rec.calendario.unlink()
                rec.calendario=False

            if rec.list_restricciones:
                for elem in rec.list_restricciones:
                    elem.unlink()

            if rec.resumenes:
                elim=rec.resumenes.producto_lines2.search([('ordenes_id', '=', rec.id)])
                if elim:
                    for ref in elim:
                        ref.unlink()
                rec.resumenes=False
            deudas_borr=self.env['abatar.deudas'].search([('orden', '=', rec.id)])
            if deudas_borr:
                for rec2 in deudas_borr:
                    rec2.unlink()
            if rec.uso_elem:
                for rec2 in rec.uso_elem:
                    rec2.unlink()

        res = super(AbatarOrdenes, self).unlink()
        return res

    def _set_orden_enviada(self):
        creation_var_time=datetime.strptime("8/9/2025 - 09:22:00", "%d/%m/%Y - %H:%M:%S") #fecha de creaciòn de sta variable

        for rec in self:
            if rec.fecha_pedido:
                if rec.fecha_pedido>creation_var_time:
                    return False
                else:
                    return True
            else:
                return True





    name_gral=fields.Char(string="Nombre de rec", store=True, readonly=True, compute='set_name_gral')
    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    pedide = fields.Char(string='Pedido', default=lambda self: _('New'))
    es_conocido = fields.Selection([('si', 'Si'), ('no', 'No')],
        string='Es cliente?', default='no', required=True, states={'finalizo': [('readonly', True)]})

    orden_enviada=fields.Boolean(string="Orden Enviada?", default=lambda self:self._set_orden_enviada())

    hay_carreta = fields.Selection([('si', 'Si'), ('no', 'No')],
        string='Llevar Carretilla?', default='si')
    lleva_carreta = fields.Selection([('chofer', 'CHOFER'), ('abatar', 'ABATAR'), ('sin definir', 'Sin Definir')],
        string='Quien Lleva Carretilla?', default='sin definir')



    ver_horas = fields.Boolean(string='HORARIOS', default=False)
    ver_prov = fields.Boolean(string='PROVEEDORES+', default=False)
    ver_direc = fields.Boolean(string='DIRECCIONES', default=False)
    ver_cobros = fields.Boolean(string='COBROS', default=False)

    cliente = fields.Many2one('abatar.clientes', string='Cliente', states={'finalizo': [('readonly', True)]})
    cliente_gral = fields.Many2one('abatar.clientes_gral', string='C.Cliente',store=True, readonly=True, related='cliente.clientes_gral_id')

    contacto = fields.Many2one('abatar.clientes.lines', string='Contacto')
    tel_cliente = fields.Char(string='Telefono')
    email_cliente = fields.Char(string='Email')

    empresa = fields.Char(string='Empresa', states={'finalizo': [('readonly', True)]})
    name = fields.Char(string='Nombre', required=True, states={'finalizo': [('readonly', True)]})
    tel = fields.Char(string='Telefono', states={'finalizo': [('readonly', True)]})
    email = fields.Char(string='Email', states={'finalizo': [('readonly', True)]})

    orden_vieja = fields.Char(string='orden_vieja')
    pedido_viejo = fields.Char(string='pedido_viejo')

    resumenes = fields.Many2one('abatar.resumenes', default=False, string='resumenes')
    resumenes_id=fields.Integer(string="Resumen id")

    id_unidad = fields.Integer(string='id unidad')
    horas_total = fields.Float(string="Horas Trabajadas",store=True, readonly=True, compute='set_horas', states={'finalizo': [('readonly', True)]})

    oculta_desc = fields.Boolean(string='Mostrar LINEAS PAUTA', default=True)
    desc = fields.Text(string='Descripcion')
    desc1 = fields.Text(string='Descripcion2')
    reg_cotiz = fields.Many2one('abatar.cotizaciones', default=False, string='Cotizaciones')
    reg_cotiz_precio_ad = fields.Float(related='reg_cotiz.precio_adicional', store=True, readonly=True,string='Precio de Adicional')
    reg_cotiz_cant_ad = fields.Integer(string='Cantidad Adicionales',default=0)
    reg_cotiz_text_ad = fields.Char(related='reg_cotiz.texto_adicional', store=True, readonly=True,string='Texto Adicionales')


    cont_pauta = fields.Integer(string='contador pautas', compute='set_pauta')
    cont_tipos = fields.Integer(string='contador tipos', compute='set_pauta')
    pauta = fields.Text(string='Pauta', compute='set_pauta')
    comentario = fields.Text(string='Comentario Interno')

    crm = fields.Many2one('abatar.crm', string='CRM')#, states={'finalizo': [('readonly', True)]})
    factura = fields.Many2one('abatar.factura', string='Factura CRM', store=True, readonly=True, compute='set_factura')
    accion_n = fields.Integer(string='Accion', store=True, readonly=True, compute='set_accion')
    unidades = fields.Integer(string="unidades")
    ud_sv = fields.Char(string="Tipo Ud", store=True, readonly=True, compute='set_ud_op')
    kms_sv = fields.Integer(string="kms Ud", store=True, readonly=True, compute='set_ud_op')
    ud_ppal = fields.Char(string="Tipo Ud", store=True, readonly=True, compute='set_ud_op')
    op_sv = fields.Integer(string="Cant Op", store=True, readonly=True, compute='set_ud_op')
    forc_ud_ppal = fields.Char(string="f Tipo Ud", default='')
    forc_ud_ppal2 = fields.Many2one('abatar.productos', default=False, store=True, readonly=True, compute='set_forc_ud_ppal2',string="f Tipo Ud")
    forc_op_sv = fields.Integer(string="f Cant Op")
    forc_kms_sv = fields.Integer(string="f Kms")
    forc_name_seq = fields.Integer(string="f N OT")
    forc_pedide = fields.Integer(string="f N Pedido")

    operarios = fields.Integer(string="operarios")

    tiene_precio = fields.Boolean(string='Tiene Precio', compute='set_tiene_precio')
    solo_efectivo = fields.Boolean(string='Solo Efectivo?', default=False)
    solo_efectivo2 = fields.Boolean(string='Solo Efectivo?', default=False)
    solo_efectivo3 = fields.Boolean(string='Solo Efectivo?', default=False)
    cobro_convenido = fields.Float(string="Cobrar al finalizar") #, states={'finalizo': [('readonly', True)]}
    cobro_convenido2 = fields.Float(string="Cobrar 2do adel")
    cobro_convenido3 = fields.Float(string="Cobrar 3er adel")
    cobro1_pago=fields.Boolean(string='Ya se Cobró?', default=False)
    cobro2_pago=fields.Boolean(string='Ya se Cobró?', default=False)
    cobro3_pago=fields.Boolean(string='Ya se Cobró?', default=False)
    precio_convenido = fields.Float(string="Precio Convenido",help='Valor que indica cuanto sumará esta orden en una facturación posterior')

    total_gastos = fields.Float(string="Gastos Ad.",store=True, readonly=True,  compute='set_ad')
    subtotal = fields.Float(string='Subtotal',store=True, readonly=True,  compute='set_subtotal')
    forc_costos = fields.Float(string='Costos')
    costos = fields.Float(string='Costos',store=True, readonly=True,  compute='set_costos')
    costos_mat = fields.Float(string='Costos',store=True, readonly=True,  compute='set_costos')
    costos_teo = fields.Float(string='Costos Teo',store=True, readonly=True,  compute='set_costos_teo')
    subtotal_teo = fields.Float(string='Subtotal Teo', store=True, readonly=True, compute='set_subtotal_teo')
    subtotal_dolar = fields.Float(string='Subtotal U$d', store=True, readonly=True, compute='set_dolar')
    costos_dolar = fields.Float(string='Costos U$d',store=True, readonly=True,  compute='set_dolar')
    ganancia_pesos = fields.Float(string='Ganancia $', store=True, readonly=True, compute='set_ganancia_pesos')
    ganancia_dolar = fields.Float(string='Ganancia U$d', store=True, readonly=True, compute='set_ganancia_dolar')
    costos_dolar2 = fields.Float(string='Costos U$d Of',store=True, readonly=True,  compute='set_dolar')
    subtotal_dolar2 = fields.Float(string='Subtotal U$d Of', store=True, readonly=True, compute='set_dolar')
    ganancia_dolar2 = fields.Float(string='Ganancia U$d Of', store=True, readonly=True, compute='set_ganancia_dolar')

    m3_ppal = fields.Float(string='M3 PPal', store=True, readonly=True, compute='set_m3_ppal')

    deudas_r = fields.Integer(string='Deudas Total', compute='cuenta_deudas')

    proveedor_modelo = fields.Char(string='Modelo', default='')
    proveedor_patente = fields.Char(string='Patente', default='')
    hora_inicio = fields.Float(string='Hora nueva', compute='datetime_to_float')
    hora_final = fields.Float(string='Hora final')
    dolar_uso = fields.Float(string='Dolar conv.', store=True, readonly=True, compute='set_dolar')
    dolar2_uso = fields.Float(string='Dolar Of conv.', store=True, readonly=True, compute='set_dolar')

    orden_lines = fields.One2many('abatar.ordenes.lines', 'orden_id', string='Linea de Personal') #, states={'finalizo': [('readonly', True)]}
    embalaje_lines = fields.One2many('abatar.embalaje.lines', 'orden_id', string='Productos de Embalaje') #, states={'finalizo': [('readonly', True)]}
    registro_gastos = fields.One2many('abatar.registro.gastos', 'orden_id', string='Registro de gastos') #, states={'finalizo': [('readonly', True)]}
    uso_elem=fields.One2many('abatar.ordenes.elem', 'ordenes_id', string="Uso de Elementos")

    state = fields.Selection(
        [('orden', 'Orden DT'), ('finalizo', 'Finalizo'), ('cancelo', 'Cancelado')],
        string='Status', default='orden')

    destinos_lines = fields.One2many('abatar.destinos.lines', 'orden_id', string='Linea de Direcciones')
    destinos_lines2 = fields.One2many('abatar.destinos.lines2', 'orden_id', string='-Linea de Direcciones')
    destinos_resumen=fields.Char(string="Resumen para busqueda", store=True, readonly=True, compute='set_destinos_resumen')

    fecha_pedido = fields.Datetime(string='Fecha de Pedido', default=fields.Datetime.now())
    fecha_confirmacion = fields.Datetime(string='Fecha de Confirmacion', readonly=True, default=fields.Datetime.now())
    fecha_ejecucion = fields.Datetime(string='Fecha del Servicio', required=True) #, states={'finalizo': [('readonly', True)]}
    fecha_ejecucion_name = fields.Char(string='Fecha del Servicio',store=True, readonly=True,  compute='set_fecha_name') #, states={'finalizo': [('readonly', True)]}

    fecha_ejecucion_name2 = fields.Char(string='Fecha del Servicio', store=True, readonly=True, compute='set_fecha_name') #, states={'finalizo': [('readonly', True)]}
    active = fields.Boolean('Active', default=True)
    desc_imprimir = fields.Boolean('Mostrar en Orden?', default=False)
    fecha_mes_año=fields.Char(string="Mes y Año", store=True, readonly=True, compute='set_fecha_mes_año')


    atajos = fields.Boolean('atajos', default=False, states={'finalizo': [('readonly', True)]})
    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user, states={'finalizo': [('readonly', True)]})

    calendario = fields.Many2one('abatar.calendario', string='Calendario')

    cadena_pedidos_r = fields.Integer(string='Pedidos Realizadas', compute='cuenta_cadena')
    servicio = fields.Many2one('abatar.servicios.calendario', string='Servicio', required=True) #, states={'finalizo': [('readonly', True)]}
    servicio_name=fields.Char(related='servicio.name', store=True, readonly=True, string="Servicio Name")

    largo_de_cadena = fields.Integer(string='Largo de cadena', default=0, compute='set_largodecadena')


    fecha_ejecucion2 = fields.Char(string='Fecha de Ejecucion2', store=True, readonly=True, compute='set_fecha2')
    debe_elementos = fields.Boolean('Elem. Pendientes', compute='set_debe_elem')
    para_enviar = fields.Boolean(
        compute='_compute_para_enviar',
        store=True, readonly=True
    )

    revisadas_restricciones = fields.Boolean(string="Restricciones direc.", default=True)
    list_restricciones = fields.One2many('abatar.restricciones.list', 'orden_id', string="Lista de Restricciones")


    def toggle_revisar(self):
        for rec in self:
            rec.revisadas_restricciones = not rec.revisadas_restricciones

    def set_revisar(self,val):
        fields.Glog("SET RESTRICCIONES REVISAR OK:"+str(val))
        self.write({'revisadas_restricciones':val})

    @api.depends('fecha_ejecucion', 'orden_enviada')
    def _compute_para_enviar(self):
        for rec in self:
            if rec.fecha_ejecucion:
                hoy=datetime.today()
                if rec.fecha_ejecucion.date()>hoy.date():

                    dias = {
                        calendar.weekday(2023, 4, 3): 'Lun',
                        calendar.weekday(2023, 4, 4): 'Mar',
                        calendar.weekday(2023, 4, 5): 'Mie',
                        calendar.weekday(2023, 4, 6): 'Jue',
                        calendar.weekday(2023, 4, 7): 'Vie',
                        calendar.weekday(2023, 4, 8): 'Sab',
                        calendar.weekday(2023, 4, 9): 'Dom',
                    }
                    if dias[hoy.weekday()]=='Vie':
                        if rec.fecha_ejecucion.date()-hoy.date()<=timedelta(days=3): #sab dom o lun
                            rec.para_enviar=True

                        else:
                            rec.para_enviar=False
                    elif dias[hoy.weekday()] =='Sab':
                        if rec.fecha_ejecucion.date()-hoy.date()<=timedelta(days=2): #dom o lun
                            rec.para_enviar=True

                        else:
                            rec.para_enviar=False
                    else:
                        if rec.fecha_ejecucion.date()-hoy.date()<=timedelta(days=1): #dom o lun
                            rec.para_enviar=True

                        else:
                            rec.para_enviar=False
                else:
                    rec.para_enviar = False
            else:
                rec.para_enviar = False

    def toggle_orden_enviada(self):
        self.orden_enviada= not self.orden_enviada


    def state_cancelo2(self):
        self.state='cancelo'
        if self.calendario:
            if self.calendario.active:
                self.calendario.active=False


        self.message_post(body=_("La orden volvió a estado: Cancelada"))
    def state_orden(self):
        self.state='orden'
        if self.calendario:
            if not self.calendario.active:
                self.calendario.active=True
        self.message_post(body=_("La orden volvió a estado: Orden (Activa)"))

    @api.onchange('servicio')
    def carga_crm_datos(self):
        for rec in self:
            fields.Glog('inicia carga_crm_datos')
            if rec.servicio_name=='Entrega de Materiales':
                if rec.crm:
                    if rec.crm.cotizador:
                        emb_lines=[]
                        if rec.crm.cotizador.embalaje_lines:
                            rec.embalaje_lines=[(5,0,0)]

                            for elem in rec.crm.cotizador.embalaje_lines:
                                if elem.embalaje_id and elem.cantidad:
                                    if not elem.embalaje_id.es_mat_consumo_interno:
                                        emb_lines.append((0,0,{'embalaje_id':elem.embalaje_id.id, 'cantidad':elem.cantidad, 'orden_id':rec.id}))
                            rec.embalaje_lines=emb_lines
                    fields.Glog('carga_crm_datos embalaje listo')
                    if rec.crm.convenio:
                        precio=rec.crm.precio_mas_iva
                        if not rec.crm.mas_iva:
                            rec.solo_efectivo=True
                            rec.solo_efectivo2=True
                            rec.solo_efectivo3=True
                        if rec.crm.convenio in ['20','25', '40']:
                            rec.cobro_convenido=round(precio*(float(rec.crm.convenio)/100),2)
                            rec.cobro_convenido2=0
                            rec.cobro_convenido3=round(precio*(1-float(rec.crm.convenio)/100),2)

                        elif rec.crm.convenio == '30':
                            rec.cobro_convenido=round(precio*0.3,2)
                            rec.cobro_convenido2=round(precio*0.3,2)
                            rec.cobro_convenido3=round(precio*0.4,2)
                        else:
                            rec.cobro_convenido=round(precio,2)
                            rec.cobro_convenido2=0
                            rec.cobro_convenido3=0
                    fields.Glog('carga_crm_datos convenio listo')


   #api.onchange('fecha_ejecucion')
    #def rest(self):
    #    for rec in self.env['abatar.ordenes'].search([('active','in', [True, False])]):
    #        if rec.desc:
    #            rec.write({'desc':rec.desc+'.'})
    #        else:
    #            rec.write({'desc':'.'})



    @api.depends('fecha_ejecucion')
    def set_fecha_name(self):
        for rec in self:
            text=''
            text2=''
            if rec.fecha_ejecucion:
                fields.Glog("hay fecha_ejec")
                text=(rec.fecha_ejecucion-timedelta(hours=3)).strftime('%d/%m/%Y - %H:%M')
                text2=(rec.fecha_ejecucion-timedelta(hours=3)).strftime('%d/%m/%Y')
                dias={
                    calendar.weekday(2023, 4,3):'Lun',
                    calendar.weekday(2023, 4,4):'Mar',
                    calendar.weekday(2023, 4,5):'Mie',
                    calendar.weekday(2023, 4,6):'Jue',
                    calendar.weekday(2023, 4,7):'Vie',
                    calendar.weekday(2023, 4,8):'Sab',
                    calendar.weekday(2023, 4,9):'Dom',
                }
                if rec.fecha_ejecucion.weekday() in list(dias.keys()):
                    fields.Glog("hay weekday")

                    text=dias[rec.fecha_ejecucion.weekday()]+' '+text
                    text2=dias[rec.fecha_ejecucion.weekday()]+' '+text2
            rec.fecha_ejecucion_name=text
            rec.fecha_ejecucion_name2=text2


    def set_debe_elem(self):
        for rec in self:
            rec.debe_elementos=False
            if rec.uso_elem:
                for res in rec.uso_elem:
                    if res.elem_id:
                        rec.debe_elementos=True
                        break



    #@api.onchange('tel')
    #def set_factura2(self):
    #    for rec in self.env['abatar.ordenes'].search([('active', 'in', (True, False))]):
    #        if rec.crm:
    #            if rec.crm.factura:
    #                rec.write({'factura':rec.crm.factura.id })


    '''@api.onchange('servicio')
    def set_entrega_montos(self):
        for rec in self:
            if rec.servicio_name=="Entrega de Materiales":
                if rec.crm:
                    if rec.crm.convenio=="30":
                        rec.write({'cobro_convenido':rec.crm.precio_mas_iva*0.3 })
                        rec.write({'cobro_convenido2':rec.crm.precio_mas_iva*0.3 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva*0.4 })
                    elif rec.crm.convenio=="40":
                        rec.write({'cobro_convenido':rec.crm.precio_mas_iva*0.4 })
                        rec.write({'cobro_convenido2':0 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva*0.6 })
                    elif rec.crm.convenio=="20":
                        rec.write({'cobro_convenido':rec.crm.precio_mas_iva*0.2 })
                        rec.write({'cobro_convenido2':0 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva*0.8 })
                    elif rec.crm.convenio=="25":
                        rec.write({'cobro_convenido':rec.crm.precio_mas_iva*0.25 })
                        rec.write({'cobro_convenido2':0 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva*0.75 })
                    elif rec.crm.convenio=="contado":
                        rec.write({'cobro_convenido':0 })
                        rec.write({'cobro_convenido2':0 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva })
                    elif rec.crm.convenio=="cc":
                        rec.write({'cobro_convenido':0 })
                        rec.write({'cobro_convenido2':0 })
                        rec.write({'cobro_convenido3':rec.crm.precio_mas_iva })
    '''
    def crea_restric(self,vals):
        #self.list_restricciones=[(0, 0, vals)]
        self.write({'list_restricciones': [(0, 0, vals)]})

    def reset_restric(self):
        self.write({'list_restricciones': [(0, 0, 0)]})
    @api.depends('subtotal','costos')
    def set_ganancia_pesos(self):
        for rec in self:
            if rec.subtotal:
                if rec.costos:
                    rec.ganancia_pesos= rec.subtotal - rec.costos


    @api.depends('state')
    def set_factura(self):
        for rec in self:
            if rec.crm:
                if rec.crm.factura:
                    rec.factura= rec.crm.factura.id



    @api.depends('costos_dolar','costos_dolar2', 'subtotal_dolar', 'subtotal_dolar2')
    def set_ganancia_dolar(self):
        for rec in self:
            if rec.subtotal_dolar>0:
                if rec.costos_dolar>0:
                    rec.ganancia_dolar= rec.subtotal_dolar - rec.costos_dolar
            if rec.subtotal_dolar2>0:
                if rec.costos_dolar2>0:
                    rec.ganancia_dolar2= rec.subtotal_dolar2 - rec.costos_dolar2



    #@api.onchange('desc')
    @api.model
    def set_todos(self):
        print('hi todos')
        for rec in self.env['abatar.ordenes'].search([('active', 'in', (True, False))]):
            print('vie', rec)
            viejo=rec.precio_convenido
            rec.write({'precio_convenido':1})
            rec.write({'precio_convenido':viejo})
    
    @api.depends('forc_ud_ppal2')
    def set_m3_ppal(self):
        for rec in self:
            if rec.forc_ud_ppal2:
                rec.m3_ppal= rec.forc_ud_ppal2.m3
            elif rec.ud_ppal:
                m3_ud=self.env['abatar.productos'].search([('name', '=', str('Unidad \"'+rec.ud_ppal+'\"'))], limit=1).m3
                rec.m3_ppal= m3_ud
            else:
                rec.m3_ppal = 0


    @api.depends('forc_ud_ppal')
    def set_forc_ud_ppal2(self):

        for rem in self:
            if rem.forc_ud_ppal:
                prod=self.env['abatar.productos'].search([('name', '=', str('Unidad \"'+str(rem.forc_ud_ppal)+'\"'))], limit=1).id
                rem.forc_ud_ppal2=prod
            else:
                rem.forc_ud_ppal2= False

    @api.onchange('reg_cotiz','reg_cotiz_precio_ad','reg_cotiz_cant_ad','reg_cotiz_text_ad')
    def set_cotiz(self):
        for rec in self:
            if rec.reg_cotiz and rec.reg_cotiz_precio_ad and rec.reg_cotiz_cant_ad:
                rec.desc+=' - Adicionales: %i por $ %.2f' % (rec.reg_cotiz_cant_ad,rec.reg_cotiz_precio_ad)
                rec.precio_convenido=round(rec.reg_cotiz.precio+rec.reg_cotiz_precio_ad*rec.reg_cotiz_cant_ad,2)

            elif rec.reg_cotiz:
                rec.desc=rec.reg_cotiz.name
                rec.precio_convenido=rec.reg_cotiz.precio


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



    @api.depends('subtotal', 'costos')
    def set_dolar(self):
        for rec in self:
            if rec.crm:
                rec.crm.cuenta_ordenes()
            if rec.fecha_ejecucion:
                subtotal=0
                costos=0
                subtotal_dolar=0
                costos_dolar=0
                subtotal_dolar2=0
                costos_dolar2=0
                if rec.subtotal:
                    subtotal=rec.subtotal
                if rec.costos:
                    costos=rec.costos
                fecha_orden= str(fields.Date.from_string(rec.fecha_ejecucion).strftime('%d/%m/%y'))
                dia_ejec=int(fecha_orden[:fecha_orden.find('/')])
                rest=fecha_orden[fecha_orden.find('/')+1:]
                mes_ejec=int(rest[:rest.find('/')])
                rest2=rest[rest.find('/')+1:]
                año_ejec=2000+int(rest2[:])

                actu=self.env['abatar.dolar'].search([('fecha', '=', fields.Date.from_string(rec.fecha_ejecucion))], limit=1)
                if actu.pesos:
                    subtotal_dolar=subtotal/actu.pesos
                    costos_dolar=costos/actu.pesos
                    rec.dolar_uso=actu.pesos


                else:
                    for h0 in [0]:
                        day2=dia_ejec-(h0+1)*5
                        mes2=mes_ejec
                        año2=año_ejec
                        day3=dia_ejec+(h0+1)*5
                        mes3=mes_ejec
                        año3=año_ejec
                        if day2<1:
                            day2=28
                            mes2-=1
                        elif day2>28:
                            day2=1
                            mes2+=1
                        if mes2>12:
                            mes2=1
                            año2+=1
                        elif mes2<1:
                            mes2=12
                            año2-=1

                        if day3 < 1:
                            day3 = 28
                            mes3 -= 1
                        elif day3 > 28:
                            day3 = 1
                            mes3 += 1
                        if mes3 > 12:
                            mes3 = 1
                            año3 += 1
                        elif mes3 < 1:
                            mes3 = 12
                            año3 -= 1
                        actu = self.env['abatar.dolar'].search([('fecha', '>', fields.Date.from_string(str(año2)+'-'+str(mes2)+'-'+str(day2))),('fecha', '<=', fields.Date.from_string(str(año3)+'-'+str(mes3)+'-'+str(day3)))],limit=1)

                        if actu.pesos:
                            subtotal_dolar = subtotal / actu.pesos
                            costos_dolar = costos / actu.pesos
                            rec.dolar_uso=actu.pesos

                    if subtotal_dolar==0:
                        actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                        if actu.pesos:
                            subtotal_dolar = subtotal / actu.pesos
                            costos_dolar = costos / actu.pesos
                            rec.dolar_uso=actu.pesos

                rec.subtotal_dolar=subtotal_dolar
                rec.costos_dolar=costos_dolar

                actu=self.env['abatar.dolar2'].search([('fecha', '=', fields.Date.from_string(rec.fecha_ejecucion))], limit=1)
                if actu.pesos:
                    subtotal_dolar2=subtotal/actu.pesos
                    costos_dolar2=costos/actu.pesos
                    rec.dolar2_uso=actu.pesos

                else:
                    for h0 in [0]:
                        day2=dia_ejec-(h0+1)*5
                        mes2=mes_ejec
                        año2=año_ejec
                        day3=dia_ejec+(h0+1)*5
                        mes3=mes_ejec
                        año3=año_ejec
                        if day2<1:
                            day2=28
                            mes2-=1
                        elif day2>28:
                            day2=1
                            mes2+=1
                        if mes2>12:
                            mes2=1
                            año2+=1
                        elif mes2<1:
                            mes2=12
                            año2-=1

                        if day3 < 1:
                            day3 = 28
                            mes3 -= 1
                        elif day3 > 28:
                            day3 = 1
                            mes3 += 1
                        if mes3 > 12:
                            mes3 = 1
                            año3 += 1
                        elif mes3 < 1:
                            mes3 = 12
                            año3 -= 1
                        actu = self.env['abatar.dolar2'].search([('fecha', '>', fields.Date.from_string(str(año2)+'-'+str(mes2)+'-'+str(day2))),('fecha', '<=', fields.Date.from_string(str(año3)+'-'+str(mes3)+'-'+str(day3)))],limit=1)

                        if actu.pesos:
                            subtotal_dolar2 = subtotal / actu.pesos
                            costos_dolar2 = costos / actu.pesos
                            rec.dolar2_uso=actu.pesos

                            break
                    if subtotal_dolar2==0:
                        actu = self.env['abatar.dolar2'].search([], order='fecha desc', limit=1)
                        if actu.pesos:
                            subtotal_dolar2 = subtotal / actu.pesos
                            costos_dolar2 = costos / actu.pesos
                            rec.dolar2_uso=actu.pesos

                rec.subtotal_dolar2=subtotal_dolar2
                rec.costos_dolar2=costos_dolar2




    def copy(self, default=None, context=None):

        if default is None:
            default = {}
        # Todo code (You can pass your value of any field in default)
        default.update({'resumenes': False,
                        'resumenes_id': False,
                        'user_id': self.env.user.id,
                        'pedide': self.env['ir.sequence'].next_by_code('abatar.pedido.sequence') or _('New'),
                        'state': 'orden',
                        'orden_lines': [(5,0,0)],
                        'embalaje_lines': [(5,0,0)],
                        'registro_gastos': [(5,0,0)],
                        'uso_elem': [(5,0,0)],
                        'destinos_lines': [(5,0,0)],
                        'destinos_lines2': [(5,0,0)],
                        'hora_final': False,
                        'debe_elementos': False,
                        'active': True,
                        })
        res= super(AbatarOrdenes, self).copy(default)
        for direc in self.orden_lines:
            vals={'orden_id':res.id}
            for field in direc.fields_get():
                #fields.Glog(str('ORDEN COPY: '+field+str(type(direc[field]))+ str(NOT_NORMAL_TYPES)))
                if field=='orden_id_x':
                    vals['orden_id_x']=res.crm.id
                elif field=='orden_id':
                    pass
                elif field=='adelanto':
                    vals['adelanto']=0
                elif str(type(direc[field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                    vuel=0
                    for he in direc[field]:
                        if vuel>1:
                            break
                        vuel+=1
                    if vuel>1:
                        pass
                    else:
                        vals[field]=direc[field].id

                else:
                    vals[field]=direc[field]

            res.orden_lines.create(vals)
        for direc in self.embalaje_lines:
            vals={'orden_id':res.id}
            for field in direc.fields_get():
                if field=='orden_id_x':
                    vals['orden_id_x']=res.crm.id
                elif field=='orden_id':
                    pass
                elif str(type(direc[field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                    vuel=0
                    for he in direc[field]:
                        if vuel>1:
                            break
                        vuel+=1
                    if vuel>1:
                        pass
                    else:
                        vals[field]=direc[field].id

                else:
                    vals[field]=direc[field]
            res.embalaje_lines.create(vals)
        for direc in self.destinos_lines:
            vals={'orden_id':res.id}
            for field in direc.fields_get():
                if field=='orden_id_x':
                    vals['orden_id_x']=res.crm.id
                elif field=='destino_id':
                    vals[field]=direc[field].id
                elif field=='orden_id':
                    pass
                elif str(type(direc[field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                    vuel=0
                    for he in direc[field]:
                        if vuel>1:
                            break
                        vuel+=1
                    if vuel>1:
                        pass
                    else:
                        vals[field]=direc[field].id

                else:
                    vals[field]=direc[field]
            res.destinos_lines.create(vals)
        for direc in self.destinos_lines2:
            vals={'orden_id':res.id}
            for field in direc.fields_get():
                if field=='orden_id_x':
                    vals['orden_id_x']=res.crm.id
                elif field=='orden_id':
                    pass
                elif str(type(direc[field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                    vuel=0
                    for he in direc[field]:
                        if vuel>1:
                            break
                        vuel+=1
                    if vuel>1:
                        pass
                    else:
                        vals[field]=direc[field].id

                else:
                    vals[field]=direc[field]
            res.destinos_lines2.create(vals)
        return res



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
            if line.forc_name_seq:
                line.name_gral=str(line.forc_name_seq)
            elif line.name_seq:
                line.name_gral=str(line.name_seq)
            if line.cliente.name_gral:
                line.name_gral+=' '+ str(line.cliente.name_gral)
            elif line.cliente.clientes_gral_id.name:
                line.name_gral+=' '+ str(line.cliente.clientes_gral_id.name)
            elif line.cliente.id:
                line.name_gral+=' CL'+ str(line.cliente.id)



    @api.depends('registro_gastos')
    def set_ad(self):
        for r in self:
            total_gastos=0
            for rec in r.registro_gastos:
                if rec.monto:
                    total_gastos+=rec.monto
            r.total_gastos=total_gastos


    @api.depends('orden_lines','forc_ud_ppal','forc_op_sv')
    def set_ud_op(self):
        uds_list=['A', 'B', 'C', 'D', 'E', 'F', 'FF']
        for r in self:
            count=0
            h0=0
            ud_sv=''
            op_sv=0
            kms_sv=0
            for line in r.orden_lines:
                if line.proveedor_producto:
                    count+=1
                    if line.tipo in (False, ''):
                        pass
                    elif line.tipo=='operario':
                        if line.proveedor_producto:
                            if not line.proveedor_producto.subtipo.es_gratis:
                                op_sv += 1
                    elif line.tipo=='unidad':
                        if not line.tipo_ud.es_gratis:
                            h=1
                            for lett in uds_list:
                                if str(line.tipo_ud.name)[str(line.tipo_ud.name).find("\"")+1:-1]==lett:
                                    ud_sv += lett + ' '
                                    if h>h0:
                                        h0=h
                                        if line.kms:
                                            kms_sv = line.kms
                                h+=1

            r.ud_sv=ud_sv
            if r.forc_ud_ppal:
                r.ud_ppal = str(r.forc_ud_ppal)
                r.ud_sv += str(r.forc_ud_ppal)
            elif h0>0:
                r.ud_ppal=uds_list[h0-1]


            if r.forc_op_sv:
                r.op_sv=int(r.forc_op_sv)
            else:
                r.op_sv = op_sv
            if r.forc_kms_sv:
                r.kms_sv=int(r.forc_kms_sv)
            else:
                r.kms_sv = kms_sv

    @api.depends('embalaje_lines', 'orden_lines', 'forc_costos', 'registro_gastos', 'state', 'desc1')
    def set_costos(self):
        for r in self:
            if r.forc_costos:
                r.costos=r.forc_costos
            else:
                costo=0
                for rec in r.embalaje_lines:
                    if rec.embalaje_id and rec.cantidad:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        costo_ud=tar.productos_lines.search([('productos_id', '=', rec.embalaje_id.id )]).tarifas_costo2
                        costo+=rec.cantidad*costo_ud
                if r.state=='finalizo':
                    resul_deud = r.env['abatar.deudas'].search(
                        [('orden', '=', r.id), ('active', 'in', (True, False))])
                    fields.Glog("aca entro0")
                    if resul_deud:
                        for res2 in resul_deud:
                            costo += res2.deuda

                            fields.Glog("aca entro1 $ %f"%res2.deuda)

                        for rec in r.orden_lines:
                            if rec.proveedor_id.empleado:
                                if rec.precio_pactado:
                                    costo += rec.precio_pactado
                    else:
                        for rec in r.orden_lines:
                            if rec.proveedor_id:
                                if rec.precio_pactado:
                                    costo += rec.precio_pactado
                else:
                    for rec in r.orden_lines:
                        if rec.proveedor_id:
                            if rec.precio_pactado:
                                costo+=rec.precio_pactado
                for rec in r.registro_gastos:
                    if rec.monto:
                        costo+=rec.monto
                r.costos=costo




    @api.depends('embalaje_lines', 'orden_lines')
    def set_costos_teo(self):
        for r in self:
            if r.state=='finalizo':
                for rec in r.embalaje_lines:
                    if rec.embalaje_id and rec.cantidad:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        precio=tar.productos_lines.search([('productos_id', '=', rec.embalaje_id.id )], limit=1).tarifas_precio
                        r.costos_teo+=precio*rec.cantidad*(1-rec.embalaje_id.tipo.pc_gan/100)
                for rec in r.orden_lines:
                    if rec.proveedor_id:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        precio=tar.productos_lines.search([('productos_id', '=', rec.proveedor_producto.subtipo.id )], limit=1).tarifas_precio
                        r.costos_teo += (precio*rec.productos_horas + rec.kms_precio*rec.kms)*(1-rec.proveedor_producto.tipo.pc_gan/100)


    @api.depends('embalaje_lines', 'orden_lines')
    def set_subtotal_teo(self):
        for r in self:
            if r.state=='finalizo':
                for rec in r.embalaje_lines:
                    if rec.embalaje_id and rec.cantidad:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        precio=tar.productos_lines.search([('productos_id', '=', rec.embalaje_id.id)], limit=1).tarifas_precio
                        r.subtotal_teo+=precio*rec.cantidad
                for rec in r.orden_lines:
                    if rec.proveedor_id:
                        tar=self.env['abatar.tarifas'].search([('es_general', '=', True )], limit=1)
                        precio=tar.productos_lines.search([('productos_id', '=', rec.proveedor_producto.subtipo.id )], limit=1).tarifas_precio
                        r.subtotal_teo += (precio*rec.productos_horas + rec.kms_precio*rec.kms)


    @api.depends('destinos_lines','destinos_lines2')
    def set_destinos_resumen(self):
        for r in self:
            r.destinos_resumen=' '
            if r.destinos_lines:
                for ai in r.destinos_lines:
                    if ai.destino_id.name_gral:
                        r.destinos_resumen+=str(ai.destino_id.name_gral)+ ' - '
            if r.destinos_lines2:
                for ai in r.destinos_lines2:
                    if ai.destino:
                        r.destinos_resumen+=str(ai.destino)+ ' - '


    @api.depends('fecha_ejecucion')
    def set_fecha_mes_año(self):
        for r in self:
            if r.fecha_ejecucion:
                r.fecha_mes_año =  str(fields.Date.from_string(r.fecha_ejecucion).strftime('%m/%y'))


    @api.one
    @api.depends('destinos_lines2.pauta','destinos_lines.pauta','destinos_lines2.destino_tipo','destinos_lines.destino_tipo')
    def set_pauta(self):
        string=''
        cp=0
        ct=0
        h=0
        if self.destinos_lines:
            for line in self.destinos_lines:
                if h==0:
                    if line.pauta:
                        string+=str(line.pauta)
                        cp+=1
                    if line.destino_tipo:
                        ct+=1
                else:
                    if line.pauta:
                        string+=' - '+str(line.pauta)
                        cp+=1
                    if line.destino_tipo:
                        ct+=1
                h+=1


        if self.destinos_lines2:
            h=0
            for line in self.destinos_lines2:
                if h==0:
                    if line.pauta:
                        string+=str(line.pauta)
                        cp+=1
                    if line.destino_tipo:
                        ct+=1
                else:
                    if line.pauta:
                        string+=' - '+str(line.pauta)
                        cp+=1
                    if line.destino_tipo:
                        ct+=1
                h+=1
        self.pauta=string
        self.cont_pauta=cp
        self.cont_tipos=ct

    @api.depends('hora_inicio', 'hora_final', 'servicio_name')
    def set_horas(self):
        for rec in self:
            if rec.servicio_name not in  ("Visita Tecnica","Entrega de Materiales"):
                if rec.hora_final > 0 or rec.hora_inicio > 0:
                    if rec.hora_final - rec.hora_inicio>0:
                        rec.horas_total = redond(rec.hora_final - rec.hora_inicio)
                    else:
                        rec.horas_total = 0
                    line = []
                    for line in rec.orden_lines:
                        line.hora_final = rec.hora_final
                        line.hora_inicio = rec.hora_inicio
                        line.productos_horas = rec.horas_total
            else:
                rec.horas_total = 1

    def state_cancelo(self):
        for rec in self:
            if rec.state == 'finalizo':
                rec.state = "orden"

                if self.calendario:
                    if not self.calendario.active:
                        self.calendario.active = True
                self.message_post(body=_("Canceló la orden, volvio a estado Orden."))
                for dec in rec.orden_lines:
                    dec.state = rec.state
                if rec.crm and rec.cobro_convenido:
                    pago_reg=rec.crm.registro_pagos.search([('orden_id', '=', rec.id)])
                    pago_reg.unlink()

                if not rec.active:
                    rec.active = True


            for dec in rec.orden_lines:
                if dec.proveedor_id.empleado:
                    testeo = self.env['abatar.pagos.empleados'].sudo().search(
                        [('empleados_id', '=', dec.proveedor_id.empleado.id), ('desc', '=', 'Carga autom. Deuda por '+rec.name_seq)], limit=1, order='id desc')

                    if testeo:
                        for de in testeo:
                            de.unlink()
                else:
                    testeo = self.env['abatar.deudas'].sudo().search(
                        [('proveedor', '=', dec.proveedor_id.id), ('orden', '=', self.id)])

                    if testeo:
                        for de in testeo:
                            de.unlink()
                    #AL CANCELAR EL PEDIDO ELIMINA DE DEUDAS

            return {
                'name': _('Ordenes'),
                'view_type': 'form',
                'res_model': 'abatar.ordenes',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window',
            }

    def borra_personal(self):
        for rec in self:
            if rec.state:
                rec.orden_lines = [(5, 0, 0)]

    def borra_destino(self):
        for rec in self:
            if rec.state:
                rec.destinos_lines = [(5, 0, 0)]
                rec.destinos_lines2 = [(5, 0, 0)]

    def com_direc_from_crm(self):

        for rec in self:
            if rec.crm:
                if rec.crm.destinos_lines:
                    rec.write({'destinos_lines':  [(5, 0, 0)]},resumen_load=False)
                    for ei in rec.crm.destinos_lines:
                        vals1 = {
                            'destino_id': ei.destino_id.id,
                            'pauta': ei.pauta,
                            'destino_contacto': ei.destino_contacto,
                            'destino_tipo': ei.destino_tipo
                        }

                        rec.write({'destinos_lines': [(0, 0, vals1)]},resumen_load=False)
                    if rec.desc:
                        rec.write({'desc': rec.desc+". Loaded direc from CRM"})
                    else:
                        rec.write({'desc': ". Loaded direc from CRM"})

                if rec.crm.destinos_lines2:
                    rec.write({'destinos_lines2':  [(5, 0, 0)]},resumen_load=False)

                    for ei in rec.crm.destinos_lines2:

                        vals1 = {
                            'destino': ei.destino,
                            'alias': ei.alias,
                            'piso': ei.piso,
                            'dto': ei.dto,
                            'localidad': ei.localidad,
                            'provincia': ei.provincia,
                            'obs': ei.obs,
                            'autoelev': ei.autoelev,
                            'm3_escalera_c': ei.m3_escalera_c,
                            'm3_escalera_d': ei.m3_escalera_d,
                            'autoelev': ei.autoelev,
                            'pauta' : ei.pauta, #'orden_id' : resu.id,
                            'destino_contacto': ei.destino_contacto,
                            'destino_tipo': ei.destino_tipo
                        }

                        rec.write({'destinos_lines2': [(0, 0, vals1)]},resumen_load=False)
                    if rec.desc:
                        rec.write({'desc': rec.desc+". Loaded direc from CRM"})
                    else:
                        rec.write({'desc':"Loaded direc from CRM"})

    def com_direc_to_crm(self):

        for rec in self:
            if rec.crm:
                if rec.crm.destinos_lines:
                    rec.crm.write({'destinos_lines':  [(5, 0, 0)]},resumen_load=False)
                    for ei in rec.destinos_lines:
                        vals1 = {
                            'destino_id': ei.destino_id.id,
                            'pauta': ei.pauta,
                            'destino_contacto': ei.destino_contacto,
                            'destino_tipo': ei.destino_tipo
                        }

                        rec.crm.write({'destinos_lines': [(0, 0, vals1)]},resumen_load=False)
                    if rec.crm.desc1:
                        rec.crm.write({'desc1': rec.crm.desc1+". Loaded direc from orden %s"%rec.name_seq})
                    else:
                        rec.crm.write({'desc1':". Loaded direc from orden %s"%rec.name_seq})

                if rec.crm.destinos_lines2:
                    rec.crm.write({'destinos_lines2':  [(5, 0, 0)]},resumen_load=False)

                    for ei in rec.destinos_lines2:

                        vals1 = {
                            'destino': ei.destino,
                            'alias': ei.alias,
                            'piso': ei.piso,
                            'dto': ei.dto,
                            'localidad': ei.localidad,
                            'provincia': ei.provincia,
                            'obs': ei.obs,
                            'autoelev': ei.autoelev,
                            'm3_escalera_c': ei.m3_escalera_c,
                            'm3_escalera_d': ei.m3_escalera_d,
                            'autoelev': ei.autoelev,
                            'pauta' : ei.pauta, #'orden_id' : resu.id,
                            'destino_contacto': ei.destino_contacto,
                            'destino_tipo': ei.destino_tipo
                        }

                        rec.crm.write({'destinos_lines2': [(0, 0, vals1)]},resumen_load=False)
                    if rec.crm.desc1:
                        rec.crm.write({'desc1': rec.crm.desc1 + ". Loaded direc from orden %s" % rec.name_seq})
                    else:
                        rec.crm.write({'desc1': ". Loaded direc from orden %s" % rec.name_seq})

    def maps_direcciones(self):
        for rec in self:
            basedir="https://www.google.com.ar/maps/dir/"
            if rec.destinos_lines:
                for dir in rec.destinos_lines:

                    if dir.destino_id:
                        if dir.destino_id.forc_direc:
                            basedir+=dir.destino_id.name.replace(' ','+')
                        else:
                            if dir.destino_id.name:
                                basedir+=dir.destino_id.name.replace(' ','+')
                                fields.Glog("name, base_dir")
                                fields.Glog(dir.destino_id.name)
                                fields.Glog(basedir)
                                if dir.destino_id.localidad:
                                    basedir+=',+'+dir.destino_id.localidad.replace(' ','+')
                                if dir.destino_id.provincia:
                                    basedir+=',+'+dir.destino_id.provincia.replace(' ','+')
                            elif dir.destino_id.localidad:
                                basedir+=dir.destino_id.localidad.replace(' ','+')
                                if dir.destino_id.provincia:
                                    basedir+=',+'+dir.destino_id.provincia.replace(' ','+')
                            else:
                                basedir+=dir.destino_id.provincia.replace(' ','+')
                            basedir+='/'

            elif rec.destinos_lines2:
                for dir in rec.destinos_lines2:
                    if dir.forc_direc:
                        basedir+=dir.forc_direc.replace(' ','+')
                        basedir+='/'

                    else:
                        if dir.destino:
                            basedir+=dir.destino.replace(' ','+')
                            fields.Glog("destino, base_dir")
                            fields.Glog(dir.destino)
                            fields.Glog(basedir)
                            if dir.localidad:
                                basedir+=',+'+dir.localidad.replace(' ','+')
                            if dir.provincia:
                                basedir+=',+'+dir.provincia.replace(' ','+')
                        elif dir.localidad:
                            basedir+=dir.localidad.replace(' ','+')
                            if dir.provincia:
                                basedir+=',+'+dir.provincia.replace(' ','+')
                        else:
                            basedir+=dir.provincia.replace(' ','+')
                        basedir+='/'
            return {
                'type': 'ir.actions.act_url',
                'url': basedir[:-1],
                'target': 'new',
            }

    def borra_embalaje(self):
        for rec in self:
            if rec.state:
                rec.embalaje_lines = [(5, 0, 0)]

    def set_oculta_desc(self):
        for rec in self:
            if rec.oculta_desc == True:
                rec.update({'oculta_desc': False})
            else:
                rec.update({'oculta_desc': True})


    @api.onchange('cliente')
    def set_tel_cliente2(self):
        for rec in self:
            rec.contacto = False


    @api.onchange('contacto')
    def set_tel_cliente(self):
        for rec in self:
            rec.empresa = rec.cliente.name_gral
            rec.tel = rec.contacto.tel
            rec.tel_cliente = rec.contacto.tel
            rec.email_cliente = rec.contacto.email
            if rec.es_conocido=='si':
                rec.name = rec.contacto.name
            rec.tel = rec.tel_cliente


    @api.depends('unidades', 'operarios', 'pauta', 'destinos_lines.destino_id', 'destinos_lines2.destino')
    def set_largodecadena(self):
        for rec in self:

            if rec.pauta:
                if len(rec.pauta) > 200:
                    rec.largo_de_cadena = 1

            contador = rec.operarios

            if rec.es_conocido == 'si':
                for i in rec.destinos_lines:
                    contador += 1
            else:
                for i in rec.destinos_lines2:
                    contador += 1

            if contador > 9:
                rec.largo_de_cadena = 1

    def cuenta_deudas(self):
        for rec in self:
            count = self.env['abatar.deudas'].search_count([('orden', '=', rec.id)])
            rec.deudas_r = count



    def cuenta_cadena(self):
        for rec in self:
            count = self.env['abatar.ordenes'].search_count([('pedide', '=', rec.pedide)])
            rec.cadena_pedidos_r = count


    @api.multi
    def cadena_pedidos(self):
        return {
            'name': _('Pedidos'),
            'domain': [('pedide', '=', self.pedide)],
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def cadena_deudas(self):
        return {
            'name': _('Deudas'),
            'domain': [('orden', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.deudas',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


    @api.one
    @api.constrains('servicio')
    def _check_your_field(self):
        if self.crm.state == 'pendiente':
            if self.servicio.name != 'Visita Tecnica' and self.servicio.name != 'Entrega de Materiales':
                raise ValidationError('El CRM esta en Estado Pendiente, solo podes seleccionar el servicio en V.T. o E.M.')

    @api.onchange('es_conocido')
    def remove_all_(self):
        for rec in self:
            rec.empresa = ""
            rec.name = ""
            rec.tel = ""
            rec.email = ""
            rec.cliente = False
            rec.contacto = False
            rec.email_cliente = ""
            rec.tel_cliente = ""


    @api.onchange('es_conocido','name_seq','pedide','desc','crm','orden_lines','ud_ppal','op_sv','cliente','empresa','contacto','name')
    def name_calendar(self):
        for many in self:#.env['abatar.ordenes'].search([]):

            string = ''

            if many.pedide:
                string +=str(many.pedide)

            if many.crm:
                if many.crm.m3_flete:
                    string += ' (' + str(many.crm.m3_flete) + ')'
                elif many.crm.mdz_m3_auto:
                    string += ' (' + str(many.crm.mdz_m3_auto) + ')'

            if many.cliente:
                CLI2 = many.cliente
                string += '\n' + CLI2.name_gral2
            elif many.empresa:
                string += '\n' + many.empresa

            if many.contacto:
                string += '\n' + many.contacto.name
            elif many.name:
                string += '\n' + many.name


            if many.orden_lines:
                h0 = 0
                h1 = 0
                string2 = []
                for elem in many.orden_lines:
                    if elem.tipo == 'unidad':
                        h0 += 1
                        if elem.tipo and not elem.proveedor_id:
                            string2.append('\n UD %i:' % h0)
                        elif elem.tipo and elem.proveedor_id:
                            string2.append('\n UD %i: %s' % (h0, elem.proveedor_id.name))

                    elif elem.tipo == 'operario':
                        h1 += 1
                        if elem.tipo and not elem.proveedor_id:
                            string2.append('\n OP %i:' % h1)
                        elif elem.tipo and elem.proveedor_id:
                            string2.append('\n OP %i: %s' % (h1, elem.proveedor_id.name))

                ei = many.calendario
                if ei:
                    ei.write({'name': string})
                    for ind1 in range(len(string2)):
                        if ind1<6:
                            ei.write({'name%i'%(ind1+2): string2[ind1]})
                        else:
                            ei.write({'name%i'%(ind1+1): '...'})
                            break
                elif self.env['abatar.calendario.crm'].search([('orden', '=', many.id)]):
                    for ai in self.env['abatar.calendario.crm'].search([('orden', '=', many.id)]):
                        ei2=self.env['abatar.calendario'].search([('id', '=', ai.calendario_id.id)])
                        ei2.write({'name': string})
                        for ind1 in range(len(string2)):
                            if ind1<6:
                                ei2.write({'name%i'%(ind1+2): string2[ind1]})


    @api.depends('orden_lines','precio_convenido')
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
    def action_toggle_envio_orden_OK(self):
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
    def write(self, vals,resumen_load=True):
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

        if BUSQUEDAON == True and resumen_load:
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
        res = super(AbatarOrdenes, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        revisa = self.env['abatar.tipo'].search([('name', '=', 'unidad')])

        rec = super(AbatarOrdenes, self).default_get(fields)

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

        result = super(AbatarOrdenes, self).create(vals)
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

        result.calendario = self.env['abatar.calendario'].create(vals2).id


        return result

class AbatarOrdenesElem(models.Model):
    _name = "abatar.ordenes.elem"
    _description = "Abatar ordenes elementos"
    _rec_name='elem_id'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.elem_id:
                result = rec.elem_id
                uso = result.cant_uso-rec.cant
                result.cant_uso=uso
                result.write({'mov_lines':[(1, rec.elem_lines_id.id,
                                            {'ordenes_id':False,
                                           'elementos_id' : False
                                           })]})
                result.write({'mov_lines':[(2, rec.elem_lines_id.id)]})
                result.elem_lines_id=False

            if rec.proveedor_id:
                prev=self.env['abatar.proveedores'].search([('id', '=', rec.proveedor_id.id)])
                prev2 = prev.uso_elem.search([('elem_slot.id', '=', rec.id)], limit=1)
                cant_nuevo=prev2.cant-rec.cant
                if cant_nuevo==0 or cant_nuevo==False :
                    prev2.unlink()
                else:
                    prev2.write({'cant':cant_nuevo})

        res = super(AbatarOrdenesElem, self).unlink()
        return res


    elem_id=fields.Many2one('abatar.elementos', string="Elemento", required=True)
    cant=fields.Integer(string="Cantidad", default=1, required=True)
    proveedor_id=fields.Many2one('abatar.proveedores', string="Proveedor", required=True)
    ordenes_id=fields.Many2one('abatar.ordenes', string="Orden_id")
    elem_lines_id=fields.Many2one('abatar.elementos.lines', string="elem lines_id", default=False)

    @api.constrains('cant')
    def aviso_constrains(self):
        for rec in self:
            if rec.cant == 0 or rec.cant==False:
                raise UserError('No se puede adjudicar deuda de cantidad 0, elimine la fila para cancelar la deuda.')

    @api.model
    def create(self, vals):
        result = super(AbatarOrdenesElem, self).create(vals)
        result2 = self.env['abatar.elementos'].search([('id', '=', vals.get('elem_id'))])
        result2.cant_uso+=vals.get('cant')
        result2.write({'mov_lines': [(0, 0, {'desc': 'Uso por Orden %s.' % vals.get('ordenes_id'),
                                            'fecha_op': fields.Datetime.now(),
                                            'cant': -vals.get('cant'),
                                            'ordenes_id': vals.get('ordenes_id'),
                                            'elementos_id': vals.get('elem_id')
                                            })]})
        result.elem_lines_id=result2.mov_lines.search([], order='id desc', limit=1).id


        result3 = self.env['abatar.proveedores'].search([('id', '=', vals.get('proveedor_id'))])
        vals1={ 'elem_id' : vals.get('elem_id'),
                'proveedor_id': vals.get('proveedor_id'),
                'ordenes_id': vals.get('ordenes_id'),
                'cant': vals.get('cant'),
                'elem_slot': result.id
                }
        result3.uso_elem.create(vals1)

        return result
    @api.multi
    def write(self, vals):
        if vals.get('elem_id'):
            if self.elem_id:
                result=self.env['abatar.elementos'].search([('id', '=', self.elem_id)])
                if result:
                    if self.cant:
                        result.cant_uso-=self.cant
                        result.write({'mov_lines':[(1, self.elem_lines_id.id,
                                                    {'ordenes_id':False,
                                                   'elementos_id' : False
                                                   })]})
                        result.write({'mov_lines':[(2, self.elem_lines_id.id)]})
                        result.elem_lines_id=False
            result2=self.env['abatar.elementos'].search([('id', '=', vals.get('elem_id'))])
            if vals.get('cant'):
                result2.cant_uso+=vals.get('cant')
                result2.write({'mov_lines': [(0, 0, {'desc': 'Uso por Orden.',
                                                    'fecha_op': fields.Datetime.now(),
                                                    'cant': -vals.get('cant'),
                                                    'ordenes_id': self.ordenes_id.id,
                                                    'elementos_id': result2.id
                                                    })]})
            elif self.cant:
                result2.cant_uso+=self.cant
                result2.write({'mov_lines': [(0, 0, {'desc': 'Uso por Orden.',
                                                    'fecha_op': fields.Datetime.now(),
                                                    'cant': -self.cant,
                                                    'ordenes_id': self.ordenes_id.id,
                                                    'elementos_id': result2.id
                                                    })]})
            self.elem_lines_id=result2.mov_lines.search([], order='id desc', limit=1).id

        if vals.get('proveedor_id'):
            if self.proveedor_id:
                result=self.env['abatar.proveedores'].search([('id', '=', self.proveedor_id.id)], limit=1)
                result2 =result.uso_elem.search([('elem_slot', '=', self.id)])
                result2.unlink()
            result = self.env['abatar.proveedores'].search([('id', '=', vals.get('proveedor_id'))], limit=1)
            if vals.get('elem_id'):
                elem_nuevo= vals.get('elem_id')
            else:
                elem_nuevo = self.elem_id.id
            if vals.get('cant'):
                cant_nuevo= vals.get('cant')
            else:
                cant_nuevo = self.cant
            if vals.get('proveedor_id'):
                proveedor_nuevo= vals.get('proveedor_id')
            else:
                proveedor_nuevo = self.proveedor_id.id
            if vals.get('ordenes_id'):
                ordenes_nuevo= vals.get('ordenes_id')
            else:
                ordenes_nuevo = self.ordenes_id.id
            elem_slot_nuevo=self.id
            vals1={
                'elem_id':elem_nuevo,
                'cant':cant_nuevo,
                'proveedor_id':proveedor_nuevo,
                'ordenes_id':ordenes_nuevo,
                'elem_uso':elem_slot_nuevo
            }
            result.write({'uso_elem':[(0,0, vals1)]})

        if not vals.get('proveedor_id'):
            if not vals.get('elem_id'):
                if vals.get('cant'):

                    result=self.env['abatar.proveedores'].search([('id', '=', self.proveedor_id.id)], limit=1)
                    result2 =result.uso_elem.search([('elem_slot.id', '=', self.id)], limit=1)
                    result2.cant=vals.get('cant')


                    result3=self.env['abatar.elementos'].search([('id', '=', self.elem_id.id)], limit=1)
                    cant_nuevo=(vals.get('cant')-self.cant)
                    result3.cant_uso+=cant_nuevo
                    result3.write({'mov_lines': [(1, self.elem_lines_id.id,
                                                 {'cant':-vals.get('cant')})]})

        result = super(AbatarOrdenesElem, self).write(vals)
        return result

class AbatarOrdenesLines(models.Model):
    _name = "abatar.ordenes.lines"
    _description = "Abatar ordenes lines"
    _rec_name = "proveedor_id"

    @api.onchange('proveedor_producto', 'tipo_ud')
    def set_tipo(self):
        hay_ud=False
        tipo_ud=0
        for line in self:
            for elem in line.orden_id.orden_lines:
                if elem.tipo=='unidad':
                    hay_ud=True
                    tipo_ud=elem.tipo_ud
                    break
            break

        for line in self:

            if line.proveedor_producto:
                if line.tipo_ud:
                    #if line.proveedor_producto.minimo:
                    line.productos_minimo = line.proveedor_producto.minimo
                    if line.orden_id.cliente:
                        if line.orden_id.cliente.tarifas:
                            tar_uso=line.orden_id.cliente.tarifas
                        else:
                            tar_uso = self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)

                    else:
                        tar_uso=self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)
                    line.productos_minimo_subt=tar_uso.productos_lines.search([('productos_id', '=',line.tipo_ud.id)], limit=1).tarifas_minimo

                else:
                    line.productos_minimo = line.proveedor_producto.minimo
                    if line.orden_id.cliente:
                        if line.orden_id.cliente.tarifas:
                            tar_uso=line.orden_id.cliente.tarifas
                        else:
                            tar_uso = self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)
                    else:
                        tar_uso=self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)
                    if hay_ud==False:
                        line.productos_minimo_subt=  tar_uso.productos_lines.search([('productos_id', '=',line.proveedor_producto.subtipo.id)], limit=1).tarifas_minimo#line.proveedor_producto.subtipo.minimo+2
                    else:
                        #xud=tar_uso.productos_lines.search([('productos_id', '=',tipo_ud.id)], limit=1).tarifas_minimo
                        #xop=tar_uso.productos_lines.search([('productos_id', '=',line.proveedor_producto.subtipo.id)], limit=1).tarifas_minimo
                        #line.productos_minimo_subt = tar_uso.productos_lines.search([('productos_id', '=',tipo_ud.id)], limit=1).tarifas_minimo#line.proveedor_producto.subtipo.minimo
                        line.productos_minimo_subt = tar_uso.productos_lines.search([('productos_id', '=',line.proveedor_producto.subtipo.id)], limit=1).tarifas_minimo-2#line.proveedor_producto.subtipo.minimo

                if line.orden_id.es_conocido == 'si' and line.orden_id.cliente.tarifas:
                    busca = line.orden_id.cliente.tarifas
                else:
                    busca = self.env['abatar.tarifas'].search(
                        [('es_general', '=', True)])

                    if not busca:
                        raise UserError(_("No existe la Tarifa General."))

                if line.tipo_ud:
                    for rec in busca.productos_lines:
                        if rec.productos_id.id == line.tipo_ud.id:
                            line.productos_precio = rec.tarifas_precio
                    #if not line.productos_precio > 0:
                    #    raise UserError(_("No existe %s en la Tarifa %s.") % (line.proveedor_producto.subtipo.name, line.orden_id.cliente.tarifas.name_seq))

                    for rec in busca.kms_lines:
                        if rec.productos_id.id == line.tipo_ud.id:
                            line.kms_precio = rec.tarifas_precio
                    #if not line.kms_precio > 0:
                    #    raise UserError(_("No existe precio por km de %s en la Tarifa %s.") % (line.proveedor_producto.subtipo.name, line.orden_id.cliente.tarifas.name_seq))
                else:
                    for rec in busca.productos_lines:
                        if rec.productos_id.id == line.proveedor_producto.subtipo.id:
                            line.productos_precio = rec.tarifas_precio
                    #if not line.productos_precio > 0:
                    #    raise UserError(_("No existe %s en la Tarifa %s.") % (line.proveedor_producto.subtipo.name, line.orden_id.cliente.tarifas.name_seq))

    @api.onchange('proveedor_id')
    def set_tipo2(self):
        for rec in self:
            if rec.proveedor_id != False:
                return {'domain': {'proveedor_producto': [('proveedor_id', '=', rec.proveedor_id.id)]}}


    @api.onchange('tipo')
    def set_tipo5(self):
        for rec in self:
            if rec.tipo:
                rec.proveedor_id=False


    @api.onchange('proveedor_personal')
    def set_tipo3(self):
        for rec in self:
            if rec.proveedor_personal:
                rec.proveedor_tel = rec.proveedor_personal.tel
                rec.proveedor_dni = rec.proveedor_personal.dni



    @api.depends('productos_precio', 'productos_horas','productos_minimo_subt','productos_minimo')
    def set_subtotal(self):
        last=False
        for line in self:

            if line.productos_horas+1 < line.productos_minimo_subt:
                line.productos_horas_invisible = line.productos_minimo_subt
            else:
                line.productos_horas_invisible = line.productos_horas+1

            if line.productos_horas < line.productos_minimo:
                line.productos_horas_invisible_compra = line.productos_minimo
            else:
                line.productos_horas_invisible_compra = line.productos_horas

            if line.productos_precio and line.productos_horas_invisible:
                line.subtotal = line.productos_precio * line.productos_horas_invisible
            else:
                line.subtotal = 0

            if line.kms > 0 and line.kms_precio > 0:
                line.subtotal += line.kms * line.kms_precio
            last=line
        if last.orden_id.resumenes:
            fields.Glog("cambio de resumen_cambio_prod2:"+str(last.orden_id.resumenes.cambio_prod2))
            last.orden_id.resumenes.write({'cambio_prod2': not last.orden_id.resumenes.cambio_prod2})
            fields.Glog("FIN cambio de resumen_cambio_prod2:"+str(last.orden_id.resumenes.cambio_prod2))



    @api.depends('hora_final', 'hora_inicio')
    def set_subtota2l(self):
        for line in self:
            if line.orden_id.servicio_name not in ("Visita Tecnica","Entrega de Materiales"):
                line.productos_horas = line.hora_final - line.hora_inicio
            else:
                line.productos_horas = 1



    @api.onchange('proveedor_id')
    def cambia_func(self):
        for rec in self:
            if rec.proveedor_id:
                rec.proveedor_personal = False
                rec.proveedor_producto = False


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.adelanto_id:
                rec.adelanto_id.unlink()
                rec.adelanto_id=False
            if rec.adelanto_emp:
                rec.adelanto_emp.unlink()
                rec.adelanto_emp=False
            for ei in self.env['abatar.deudas'].search([('orden','=',rec.id),('active','in',(True,False))]):
                ei.unlink()
        res = super(AbatarOrdenesLines, self).unlink()
        return res


    tipo = fields.Selection([('unidad', 'Unidad'), ('operario', 'Operario'), ('grua', 'Grua')], string='Tipo Proveedor')
    productos_horas = fields.Float(string='Horas Trabajadas', compute='set_subtota2l')
    productos_horas_invisible = fields.Float(string='Horas Trabajadas')
    productos_horas_invisible_compra = fields.Float(string='Horas Trabajadas (compra)')
    productos_precio = fields.Float(string='Precio', track_visibility='onchange')
    precio_pactado = fields.Float(string='Conv. Compra')
    dias_precio_pactado = fields.Float(string='Días para Saldo')
    adelanto = fields.Float(string='Adelanto')
    adelanto_emp = fields.Many2one('abatar.pagos.empleados', default=False, string='Adelanto emp id')
    adelanto_id = fields.Many2one('abatar.deudas', default=False, string='Adelanto id')
    productos_minimo = fields.Float(string='Minimo (compra)')
    productos_minimo_subt = fields.Float(string='Minimo (venta)')
    hora_inicio = fields.Float(string='Hora inicio')
    hora_final = fields.Float(string='Hora final')
    kms_precio = fields.Float(string='Precio kms')
    kms = fields.Float(string='kms')
    state = fields.Selection([('orden', 'Orden DT'), ('finalizo', 'Finalizo'), ('cancelo', 'Cancelado')],
        string='Status', default='orden')
    proveedor_id = fields.Many2one('abatar.proveedores', string='Proveedor')
    proveedor_producto = fields.Many2one('abatar.proveedores.productos', string='Productos')
    proveedor_personal = fields.Many2one('abatar.proveedores.personal', string='Personal')
    tipo_ud = fields.Many2one('abatar.productos', default=False, string='Tarifa Ud')

    proveedor_tel = fields.Char(string='Telefono', default='')
    proveedor_dni = fields.Char(string='DNI', default='')
    obs = fields.Char(string='Obs.', default='')
    es_par = fields.Boolean(string='Es par')

    proveedor_mensaje_aviso = fields.Char(string='MSJ AUTO AVISO', default='')
    subtotal = fields.Float(string='Subtotal', compute='set_subtotal')

    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID', readonly=True)
    uso_orden=fields.Datetime(string='fecha uso',related='orden_id.fecha_ejecucion',store=True,readonly=True)
    prov_id_num = fields.Integer(related='proveedor_id.id', string='Proveedor ID num')

    #@api.onchange
    #def set_lastdate(self):
    #    for rec in self:
    #        fecha_act=rec.orden_id.fecha_ejecucion
    #        if rec.proveedor_id:
    #            if rec

    @api.model
    def create(self, vals):
        if vals.get('proveedor_producto'):
            obj=self.env['abatar.proveedores.productos'].search([('id','=',vals.get('proveedor_producto'))])
            obj.get_sv_count()
            obj.get_sv_ult()
        if vals.get('adelanto'):
            if vals.get('orden_id') and vals.get('proveedor_id') and vals.get('precio_pactado'):
                proov=self.env['abatar.proveedores'].search([('id', '=', vals.get('proveedor_id'))], limit=1)
                empleado=False
                if proov.empleado:
                    empleado=True
                if empleado:

                    vals2 = {
                        'fecha_op': fields.datetime.now(),
                        'monto': 0 - vals.get('adelanto'),
                        'desc': 'Carga autom. Adelanto por ' + self.orden_id.name_gral,
                        'empleados_id': proov.empleado.id
                    }

                    res=proov.empleado.pagos.create(vals2)
                    vals['adelanto_emp'] = res.id
                else:
                    vals1={
                        'fecha':fields.datetime.now(),
                        'proveedor':vals.get('proveedor_id'),
                        'deuda':vals.get('adelanto'),
                        'orden':vals.get('orden_id')
                    }
                    res=self.env['abatar.deudas'].create(vals1)
                    vals['adelanto_id']=res.id
        result = super(AbatarOrdenesLines, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        obj0=False
        obj1=False
        if vals.get('proveedor_producto'):
            obj0=self.env['abatar.proveedores.productos'].search([('id','=',vals.get('proveedor_producto'))])

            if self.proveedor_producto:
                obj1=self.proveedor_producto

        if vals.get('adelanto'):
            if self.adelanto and self.adelanto_id:
                resul=self.env['abatar.deudas'].search([('id', '=', self.adelanto_id.id),('active', 'in', (True,False))], limit=1)
                resul.deuda=vals.get('adelanto')
                if resul.deuda!=resul.pago:
                    resul.active=True
                if self.orden_id.state=='finalizo':
                    resul2 = self.env['abatar.deudas'].search(
                        [('proveedor', '=', self.proveedor_id.id),('orden', '=', self.orden_id.id),('deuda', '=', self.precio_pactado-self.adelanto ), ('active', 'in', (True, False))], limit=1)
                    if resul2:
                        resul2.deuda=self.precio_pactado-vals.get('adelanto')
                        if resul2.deuda!=resul2.pago:
                            resul2.active=True
            elif self.adelanto and self.adelanto_emp:
                resul=self.env['abatar.pagos.empleados'].search([('id', '=', self.adelanto_emp.id)], limit=1)
                resul.monto=vals.get('adelanto')

                if self.orden_id.state=='finalizo':
                    resul2 = self.env['abatar.pagos.empleados'].search(
                        [('empleados_id', '=', self.proveedor_id.empleado.id),('fecha_op', '=', self.orden_id.fecha_ejecucion.date()),('monto', '!=', self.precio_pactado-self.adelanto)], limit=1)
                    if resul2:
                        resul2.monto=self.precio_pactado-vals.get('adelanto')
            else:
                if vals.get('proveedor_id'):
                    prov=vals.get('proveedor_id')
                    proov = self.env['abatar.proveedores'].search([('id', '=', prov)], limit=1)
                    empleado = False
                    if proov.empleado:
                        empleado = True
                    if empleado:

                        vals2 = {
                            'fecha_op': fields.datetime.now(),
                            'monto': 0 - vals.get('adelanto'),
                            'desc': 'Carga autom. Adelanto por ' + self.orden_id.name_gral,
                            'empleados_id': proov.empleado.id
                        }

                        res = proov.empleado.pagos.create(vals2)
                        vals['adelanto_emp'] = res.id
                    else:
                        vals1 = {
                            'fecha': fields.datetime.now(),
                            'proveedor': prov,
                            'deuda': vals.get('adelanto'),
                            'orden': self.orden_id.id
                        }
                        res = self.env['abatar.deudas'].create(vals1)
                        vals['adelanto_id'] = res.id
                elif self.proveedor_id:
                    prov=self.proveedor_id.id
                    proov = self.env['abatar.proveedores'].search([('id', '=', prov)], limit=1)
                    empleado = False
                    if proov.empleado:
                        empleado = True
                    if empleado:

                        vals2 = {
                            'fecha_op': fields.datetime.now(),
                            'monto': 0 - vals.get('adelanto'),
                            'desc': 'Carga autom. Adelanto por ' + self.orden_id.name_gral,
                            'empleados_id': proov.empleado.id
                        }

                        res = proov.empleado.pagos.create(vals2)
                        vals['adelanto_emp'] = res.id
                    else:

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
                resul=self.env['abatar.deudas'].search([('id', '=', self.adelanto_id.id),('active', 'in', (True,False))], limit=1)
                resul.unlink()
                vals['adelanto_id']=False

                if self.orden_id.state=='finalizo':
                    resul2 = self.env['abatar.deudas'].search(
                        [('proveedor', '=', self.proveedor_id.id),('orden', '=', self.orden_id.id),('deuda', '=', self.precio_pactado-self.adelanto ), ('active', 'in', (True, False))], limit=1)
                    if resul2:
                        resul2.deuda=self.precio_pactado
                        if resul2.deuda!=resul2.pago:
                            resul2.active=True

            elif self.adelanto_emp:
                resul=self.env['abatar.pagos.empleados'].search([('id', '=', self.adelanto_emp.id)], limit=1)
                resul.unlink()
                vals['adelanto_emp']=False

                if self.orden_id.state=='finalizo':
                    resul2 = self.env['abatar.pagos.empleados'].search(
                        [('empleados_id', '=', self.proveedor_id.empleado.id),('fecha_op', '=', self.orden_id.fecha_ejecucion.date()),('monto', '!=', self.precio_pactado-self.adelanto)], limit=1)
                    if resul2:
                        resul2.monto=self.precio_pactado

        res = super(AbatarOrdenesLines, self).write(vals)
        if obj0:
            obj0.get_sv_count()
            obj0.get_sv_ult()
            if obj1:
                obj1.get_sv_count()
                obj1.get_sv_ult()
        return res


    @api.model
    def default_get(self, fields):

        revisap = self.env['abatar.ordenes'].search(
            [('id', '=', self.env.context.get('id_activo'))])

        rec = super(AbatarOrdenesLines, self).default_get(fields)

        rec['hora_inicio'] = revisap.hora_inicio

        return rec
class AbatarDestinosLines(models.Model):
    _name = "abatar.destinos.lines"
    _description = "Abatar destinos lines"
    _rec_name='destino_id'
    _order='zorden_id asc, id asc'

    #@api.onchange('destino_id')
    #def domain_onchange(self):
    #    for rec in self:
    #        if rec.orden_id:
    #            rec.cliente = rec.orden_id.cliente
    #        if rec.orden_id_x:
    #            rec.cliente = rec.orden_id_x.cliente

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.restricciones_direc_id:

                if rec.orden_id_x:
                    rec.orden_id_x.list_restricciones = [(2, rec.restricciones_direc_id, 0)]
                    incumplida = False
                    for elem in rec.orden_id_x.list_restricciones:
                        if not elem.bool_restricciones:
                            rec.orden_id_x.revisadas_restricciones = False
                            incumplida=True
                            break
                    if not incumplida:
                        rec.orden_id_x.revisadas_restricciones = True
                elif rec.orden_id:
                    rec.orden_id.list_restricciones = [(2, rec.restricciones_direc_id, 0)]
                    incumplida = False
                    for elem in rec.orden_id.list_restricciones:
                        if not elem.bool_restricciones:
                            rec.orden_id.revisadas_restricciones = False
                            incumplida=True
                            break
                    if not incumplida:
                        rec.orden_id.revisadas_restricciones = True

            res = super(AbatarDestinosLines, self).unlink()
            return res

    zorden_id=fields.Integer('Nª')
    destino_id = fields.Many2one('abatar.direcciones', string='Direccion')
    cliente = fields.Many2one('abatar.clientes', store=True, readonly=True, compute='set_cliente', string='clientes')
    destino_contacto = fields.Char(string='Contactos')
    destino_tipo = fields.Selection([
            ('origen', 'Origen'),
            ('destino', 'Destino')], string='Tipo')


    restricciones_direc_id = fields.Integer(string='Restricciones direc id')
    pauta = fields.Text(string='Pauta')
    autoelev=fields.Boolean(string='C/Autoelev.')
    m3_escalera_c=fields.Integer(string='N Bultos Bajan esc.')
    m3_escalera_d=fields.Integer(string='N Bultos Suben esc.')

    es_par = fields.Boolean(string='Es par')
    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='CRM ID')
    orden_id_x_sv=fields.Char(related='orden_id_x.servicio_name', store=True, readonly=True, string="Servicio")



    #@api.onchange('destino_id')
    def set_restricc(self):
        for rec in self:
            if rec.destino_id:
                if rec.destino_id.restricciones:
                    if rec.orden_id_x:

                        val={'desc_restricciones': rec.destino_id.name + ":\n" + rec.destino_id.restricciones, 'crm_id':rec.orden_id_x.id}

                        #rec.orden_id_x.write({'list_restricciones': [(0, 0, val)]})
                        rec.orden_id_x.crea_restric(val)
                        rec.restricciones_direc_id = rec.orden_id_x.list_restricciones.search(([]), order="id desc",limit=1).id

                        incumplida = False
                        for elem in rec.orden_id_x.list_restricciones:
                            if not elem.bool_restricciones:
                                rec.orden_id_x.revisadas_restricciones = False
                                incumplida = True
                                break
                        if not incumplida:
                            rec.orden_id_x.revisadas_restricciones = True
                    elif rec.orden_id:

                        val={'desc_restricciones': rec.destino_id.name + ":\n" + rec.destino_id.restricciones, 'orden_id':rec.orden_id.id}

                        #rec.orden_id.list_restricciones = [(0, 0, val)]

                        rec.orden_id.crea_restric(val)
                        rec.restricciones_direc_id = rec.orden_id.list_restricciones.search(([]), order="id desc",limit=1).id

                        incumplida = False
                        for elem in rec.orden_id.list_restricciones:
                            if not elem.bool_restricciones:
                                rec.orden_id.revisadas_restricciones = False
                                incumplida = True
                                break
                        if not incumplida:
                            rec.orden_id.revisadas_restricciones = True


    @api.onchange('destino_id')
    def set_contacto(self):
        for rec in self:
            if rec.destino_id:
                if rec.destino_id.contacto:
                    rec.destino_contacto=rec.destino_id.contacto

    @api.depends('destino_id')
    def set_cliente(self):
        for rec in self:
            if rec.orden_id:
                rec.cliente=rec.orden_id.cliente.id
            elif rec.orden_id_x:
                rec.cliente=rec.orden_id_x.cliente.id

    @api.multi
    def write(self,vals):
        no=False
        if vals.get('destino_id'):
            if self.restricciones_direc_id:

                if self.orden_id_x:
                    self.orden_id_x.list_restricciones = [(2, self.restricciones_direc_id, 0)]
                    incumplida = False
                    for elem in self.orden_id_x.list_restricciones:
                        if not elem.bool_restricciones:
                            self.orden_id_x.revisadas_restricciones = False
                            incumplida=True
                            break
                    if not incumplida:
                        self.orden_id_x.revisadas_restricciones = True
                elif self.orden_id:
                    self.orden_id.list_restricciones = [(2, self.restricciones_direc_id, 0)]
                    incumplida = False
                    for elem in self.orden_id.list_restricciones:
                        if not elem.bool_restricciones:
                            self.orden_id.revisadas_restricciones = False
                            incumplida=True
                            break
                    if not incumplida:
                        self.orden_id.revisadas_restricciones = True
                self.restricciones_direc_id=False

            no=True

        res = super(AbatarDestinosLines, self).write(vals)
        if no:
            self.set_restricc()

        return res

    @api.model
    def create(self,vals):
        result = super(AbatarDestinosLines, self).create(vals)

        result.set_restricc()

        return result


class AbatarDestinosLines2(models.Model):
    _name = "abatar.destinos.lines2"
    _description = "Abatar destinos lines"
    _rec_name='name_gral'
    _order='zorden_id asc, id asc'

    zorden_id=fields.Integer('Nª')
    name_gral= fields.Char(string='Direccion', compute='set_name_gral')
    destino = fields.Char(string='Calle y Altura')
    alias = fields.Char(string='Alias')
    piso = fields.Integer(string='Piso')
    dto = fields.Char(string='Dto')
    localidad = fields.Char(string='Localidad', default='CABA', required=True)
    provincia = fields.Char(string='Provincia', default='Buenos Aires',required=True)
    obs = fields.Text(string="Obs Adicional")
    destino_contacto = fields.Char(string='Contactos')
    autoelev=fields.Boolean(string='C/Autoelev.')
    m3_escalera_c=fields.Integer(string='N Bultos Bajan esc.')
    m3_escalera_d=fields.Integer(string='N Bultos Suben esc.')

    destino_tipo = fields.Selection([
            ('origen', 'Origen'),
            ('destino', 'Destino')
            ], string='Tipo')

    pauta = fields.Text(string='Pauta')
    es_par = fields.Boolean(string='Es par')
    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='CRM ID')
    forc_direc = fields.Char(string="Direccion")
    orden_id_x_sv=fields.Char(related='orden_id_x.servicio_name', store=True, readonly=True, string="Servicio")


    @api.depends('alias','destino','localidad','provincia','dto','piso','obs')
    def set_name_gral(self):
        for line in self:
            line.name_gral=''
            if line.forc_direc:
                line.name_gral=line.forc_direc
            else:
                if line.alias:
                    line.name_gral+='\"'+line.alias+'\" - '
                if line.destino:
                    line.name_gral+=line.destino+', '
                if line.piso:
                    line.name_gral+='PISO '+ str(line.piso)+', '
                else:
                    line.name_gral+='P.B., '
                if line.dto:
                    line.name_gral+='DTO '+ line.dto+', '
                if line.localidad:
                    line.name_gral+=line.localidad
                if line.provincia:
                    if line.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                        line.name_gral+= ', ' + line.provincia
                if line.obs:
                    line.name_gral+=' - '+ line.obs

class AbatarOrdenesGastos(models.Model):
    _name = "abatar.registro.gastos"
    _description = "Abatar registro gastos"


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.fecha:
                caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', rec.fecha)])

                crm = self.orden_id_x
                if caja_act.linea_movimientos:
                    for elem in caja_act.linea_movimientos:
                        if elem.tipo.id == self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id:
                            if elem.texto.find('%s - Gasto por %s' % (rec.desc,rec.orden_id.name_seq))>-1:
                                if elem.monto == rec.monto:
                                    elem.unlink()
                                    break
                                elif rec.monto:
                                    elem.monto -= rec.monto
                                    break

        res = super(AbatarOrdenesGastos, self).unlink()
        return res


    monto = fields.Float(string='Monto', required=True)
    desc = fields.Char(string='Descripcion', required=True)
    pago_electronico = fields.Boolean(string='Pago electrónico?', default=False)
    fecha = fields.Date(string='Fecha', required=True)
    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='CRM ID')

    @api.model
    def create(self, vals):
        if vals.get('orden_id'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', vals.get('fecha'))])

            if not caja_act:
                id_caja = self.env['abatar.caja'].search([], order='id desc', limit=1).id + 1
            else:
                id_caja = caja_act.id
            orden=self.env['abatar.ordenes'].search([('id', '=', vals.get('orden_id'))])
            if vals.get('pago_electronico'):
                pago_elec=vals.get('pago_electronico')
            else:
                pago_elec=False
            pagos_list={
                'tipo': self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id,
                'texto': '%s - Gasto por %s' % (vals.get('desc'),self.env['abatar.ordenes'].search([('id','=',vals.get('orden_id'))]).name_seq),
                'monto': vals.get('monto'),
                'pago_electronico': pago_elec,
                'caja_id': id_caja}

            if not caja_act:
                valst = []
                valst.append((0, 0, {
                    'tipo': pagos_list['tipo'],
                    'texto': pagos_list['texto'],
                    'monto': pagos_list['monto'],
                    'pago_electronico': pagos_list['pago_electronico'],
                    'caja_id': pagos_list['caja_id'],
                }))
                vals1 = {
                    'fecha_de_caja': vals.get('fecha'),
                    'linea_movimientos': valst
                }
                resul2 = self.env['abatar.caja'].create(vals1)
            else:
                caja_act.linea_movimientos.create({
                    'tipo': pagos_list['tipo'],
                    'texto': pagos_list['texto'],
                    'monto': pagos_list['monto'],
                    'pago_electronico': pagos_list['pago_electronico'],
                    'caja_id': pagos_list['caja_id'],
                })
        result = super(AbatarOrdenesGastos, self).create(vals)

        return result


    @api.multi
    def write(self, vals):
        if vals.get('fecha'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', vals.get('fecha'))])
            caja_ant = self.env['abatar.caja'].search([('fecha_de_caja', '=', self.fecha)])

            if not caja_act:
                id_caja = self.env['abatar.caja'].search([], order='id desc', limit=1).id + 1
            else:
                id_caja = caja_act.id
            orden=self.orden_id
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id:
                        if elem.texto.find('%s - Gasto por %s' % (self.desc,orden.name_seq))>-1:
                            if elem.monto==self.monto:
                                elem.unlink()
                                break
                            elif self.monto:
                                elem.monto-=self.monto
                                break
            act_monto=0
            if vals.get('monto'):
                act_monto=vals.get('monto')
            else:
                act_monto=self.monto

            if vals.get('pago_electronico'):
                pago_elec=vals.get('pago_electronico')
            elif self.pago_electronico:
                pago_elec=self.pago_electronico
            else:
                pago_elec=False

            if vals.get('desc'):
                text=vals.get('desc')
            else:
                text=self.desc

            pagos_list={
                'tipo': self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id,
                'texto': '%s - Gasto por %s' % (text,orden.name_seq),
                'monto': act_monto,
                'pago_electronico': pago_elec,
                'caja_id': id_caja}

            if not caja_act:
                valst = []
                valst.append((0, 0, {
                    'tipo': pagos_list['tipo'],
                    'texto': pagos_list['texto'],
                    'monto': pagos_list['monto'],
                    'pago_electronico': pagos_list['pago_electronico'],
                    'caja_id': pagos_list['caja_id'],
                }))
                vals1 = {
                    'fecha_de_caja': vals.get('fecha'),
                    'linea_movimientos': valst
                }
                resul2 = self.env['abatar.caja'].create(vals1)
            else:
                caja_act.linea_movimientos.create({
                    'tipo': pagos_list['tipo'],
                    'texto': pagos_list['texto'],
                    'monto': pagos_list['monto'],
                    'pago_electronico': pagos_list['pago_electronico'],
                    'caja_id': pagos_list['caja_id'],
                })
        elif vals.get('monto'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', self.fecha)])

            id_caja = caja_act.id

            if vals.get('pago_electronico'):
                pago_elec = vals.get('pago_electronico')
            else:
                pago_elec = self.pago_electronico

            orden=self.orden_id
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id:
                        if elem.texto=='%s - Gasto por %s' % (self.desc,orden.name_seq):
                            elem.write({'monto':vals.get('monto')})
                            elem.write({'pago_electronico':pago_elec})
                            break
        elif vals.get('pago_electronico'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', self.fecha)])

            id_caja = caja_act.id

            pago_elec = vals.get('pago_electronico')

            orden = self.orden_id
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id == self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id:
                        if elem.texto == '%s - Gasto por %s' % (self.desc,orden.name_seq):
                            elem.write({'pago_electronico': pago_elec})
                            break

        res = super(AbatarOrdenesGastos, self).write(vals)

        return res



class AbatarEmbalajeLines(models.Model):
    _name = "abatar.embalaje.lines"
    _description = "Abatar embalaje lines"
    _rec_name="embalaje_id"

    @api.model
    def default_get(self, fields):

        revisa = self.env['abatar.tipo'].search(
            [("name", '=', "embalaje")])

        for inte in revisa:
            guardemos = inte.id

        rec = super(AbatarEmbalajeLines, self).default_get(fields)

        rec['embalaje_oculto'] = guardemos

        return rec

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.embalaje_id:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', rec.embalaje_id.id)])
                if result:
                    result.cant_total+=rec.cantidad

                    result.write({'mov_lines':[(1, rec.matemb_lines_id.id,
                                                {'ordenes_id':False,
                                               'matemb_id' : False
                                               })]})
                    result.write({'mov_lines':[(2, rec.matemb_lines_id.id)]})
                    rec.matemb_lines_id=False
                    #if result.cant_total==0 or result.cant_total==False:
                    #    result.unlink()
                    #    print('unlink por cant 0')

        res = super(AbatarEmbalajeLines, self).unlink()
        return res



    embalaje_id = fields.Many2one('abatar.productos', string='Producto', required=True)
    cantidad = fields.Integer(string='Cantidad', required=True)
    embalaje_oculto = fields.Char(string='embalaje oculto')

    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='Crm ID')
    matemb_lines_id=fields.Many2one('abatar.matemb.lines', string="Linea de Mat Emb", default=False)





    @api.model
    def create(self, vals):
        result = super(AbatarEmbalajeLines, self).create(vals)
        result2 = self.env['abatar.matemb'].search([('productos_id.id','=', vals.get('embalaje_id'))], limit=1)
        if result2:
            result2.cant_total-=vals.get('cantidad')
            result2.write({'mov_lines':[(0,0,{'desc':'Uso por Orden.',
                                               'fecha_op':result.orden_id.fecha_ejecucion,
                                               'cant':-vals.get('cantidad'),
                                               'ordenes_id':result.orden_id.id,
                                               'matemb_id' : result2.id
                                               })]})
            result.matemb_lines_id=result2.mov_lines.search([], order='id desc', limit=1).id

        else:
            result2=self.env['abatar.matemb']
            idmat=self.env['abatar.matemb'].search([],order='id desc',  limit=1).id+1
            result3=result2.create({'productos_id':vals.get('embalaje_id'),
                            'cant_total':-vals.get('cantidad'),
                            'mov_lines':[(0,0,{'desc':'(Producto Creado por Orden) Uso por Orden.',
                                               'fecha_op':result.orden_id.fecha_ejecucion,
                                               'cant':-vals.get('cantidad'),
                                               'ordenes_id':result.orden_id.id,
                                               'matemb_id' : idmat
                                               })]
                            })


            result.matemb_lines_id=result3.mov_lines.search([], order='id desc', limit=1).id


        return result


    @api.multi
    def write(self, vals):
        if vals.get('embalaje_id'):
            if self.embalaje_id:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', self.embalaje_id.id)])
                if result:
                    if self.cantidad and result.cant_total:
                        result.cant_total+=self.cantidad
                        result.write({'mov_lines': [(1, self.matemb_lines_id.id,
                                                     {'ordenes_id': False,
                                                      'matemb_id': False
                                                      })]})
                        result.write({'mov_lines': [(2, self.matemb_lines_id.id)]})
                        self.matemb_lines_id = False

            result2=self.env['abatar.matemb'].search([('id', '=', vals.get('embalaje_id'))])
            if vals.get('cantidad'):
                cat=-vals.get('cantidad')
                result2.cant_total-=vals.get('cantidad')
                result2.write({'mov_lines':[(0,0,{'desc':'Uso por Orden.',
                                                   'fecha_op':self.orden_id.fecha_ejecucion,
                                                   'cant':-vals.get('cantidad'),
                                                   'ordenes_id':self.orden_id.id,
                                                   'matemb_id' : result2.id
                                                   })]})

            elif self.cantidad:
                cat=-self.cantidad
                result2.cant_total-=self.cantidad
                result2.write({'mov_lines':[(0,0,{'desc':'Uso por Orden.',
                                                   'fecha_op':self.orden_id.fecha_ejecucion,
                                                   'cant':-self.cantidad,
                                                   'ordenes_id':self.orden_id.id,
                                                   'matemb_id' : result2.id
                                                   })]})
            for rec in result2.mov_lines:
                if [rec.fecha_op, rec.cant, rec.ordenes_id, rec.desc] == [self.orden_id.fecha_ejecucion,
                                                                          cat, self.orden_id.id,
                                                                          'Uso por Orden.']:
                    self.materiales_lines_id = rec.id
                    break
        elif vals.get('cantidad'):
            if self.embalaje_id:
                result=self.env['abatar.matemb'].search([('productos_id.id', '=', self.embalaje_id.id)])
                if result:
                    result.cant_total-=(vals.get('cantidad')-self.cantidad)
                    result.write({'mov_lines': [(1, self.matemb_lines_id.id,
                                                 {'cant':-vals.get('cantidad')})]})

        result = super(AbatarEmbalajeLines, self).write(vals)
        return result
