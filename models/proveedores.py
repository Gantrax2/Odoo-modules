from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import time
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON, PROVINCIAS
from .crm import MJSLOG
import logging
import requests

def calcula_distancia(self, direccion1, direccion2):

    api_key = '&units=imperial&key=AIzaSyAvffBICS3JwKVK7xSTj_5sXDQkd5iU6wA'



    print('calc_dist oyd:', direccion1, direccion2)
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + direccion1 + "&destinations=" + direccion2 + api_key

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    print('oyd:', direccion1, direccion2)
    print('hi1:', response.json())

    try:
        tiempo_value = 2*response.json()["rows"][0]["elements"][0]["duration"]["value"]
    except:
        tiempo_value = 0
    try:
        distance_value = response.json()["rows"][0]["elements"][0]["distance"]["value"]
    except:
        distance_value = 0

    kms = distance_value / 1000

    if response.json()['status']=='INVALID_REQUEST':
        tiempo_value, kms = 0.2, 2
    return tiempo_value, kms
class AbatarProveedores(models.Model):
    _name = "abatar.proveedores"
    _description = "Abatar proveedores"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'abataradd.resumenbus']
    _rec_name = "name"
    _order='deudas2_r desc'


    def cuenta_presup(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: cuenta_ordenes')
        print('he26')
        for rec in self:
            count = rec.env['abatar.crm.presupuestos'].search_count([('proveedor_id', '=', rec.id)])
            rec.presup_r = count


    def cuenta_deudas(self):
        for rec in self:
            count = self.env['abatar.deudas'].search_count([('proveedor', '=', rec.id),('active', 'in', (True))])
            rec.deudas_r = count
            count2 = self.env['abatar.deudas'].search_count([('proveedor', '=', rec.id),('active', 'in', (True, False))])
            rec.deudas2_r = count2


    @api.depends('deudas_r')
    def cuenta_deudas_total(self):
        for nec in self:
            count = self.env['abatar.deudas'].search([('proveedor', '=', nec.id)])
            deudas = 0
            pagos = 0
            for rec in count:
                if rec.deuda:
                    deudas += rec.deuda
                if rec.pago:
                    pagos += rec.pago
            total = deudas - pagos
            nec.deudas_t = '%s - $ %s' % (nec.deudas_r, total)
            nec.write({'deudas_total': total})

    fecha_ingreso = fields.Datetime(string='Fecha de Ingreso', default=fields.Datetime.now(), track_visibility='onchange')
    name_gral=fields.Char(string="NAme Rec",store=True, readonly=True, compute='set_name_gral')
    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    forc_name_seq = fields.Char(string='F Order Reference')
    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)

    name = fields.Char(string='Nombre', track_visibility='onchange')
    tel = fields.Char(string='Telefono', track_visibility='onchange')
    dni = fields.Char(string='DNI', track_visibility='onchange')
    zona = fields.Char(string='Direccion', track_visibility='onchange')
    zona_map = fields.Selection([('Centro','Centro'),('Norte', 'Norte'),('Oeste', 'Oeste'),('SurOeste', 'SurOeste'),('Sur', 'Sur')]+PROVINCIAS,string='Zona', track_visibility='onchange', help='Seleccione a que zona corresponde la dirección: 1) Norte desde el Rio hasta la mitad entre Panamericana y Acceso Oeste. 2) Oeste desde donde termina Z.Norte hasta Linea que une Liniers con Laferrere. 3) SurOeste Ruta hacia Ezeiza y alrededores. 4) Sur hacia La Plata')
    active = fields.Boolean('Active', default=True)
    empleado = fields.Many2one('abatar.empleados', default=False, string="Es Empleado?")
    image = fields.Binary(string='Imagen', attachment=True)
    productos_lines = fields.One2many('abatar.proveedores.productos', 'proveedor_id', string='Productos', track_visibility='onchange')
    personal_lines = fields.One2many('abatar.proveedores.personal', 'proveedor_id', string='Personal', track_visibility='onchange')
    deudas_lines = fields.One2many('abatar.deudas', 'proveedor',domain=[('active','in', (True, False))], string='Deudas')

    tipo_str2 = fields.Char(string='proces tipostr', default='',readonly=True, store=True, compute='set_tipostr2')
    tipo_str = fields.Char(string='Tipos')
    tiene_emb = fields.Boolean(string='Tiene Embalaje?', default=False,  store=True, readonly=True, compute='set_tieneunop')
    tiene_un = fields.Boolean(string='Tiene Unidad?', default=False,  store=True, readonly=True, compute='set_tieneunop')
    tiene_gr = fields.Boolean(string='Tiene Grua?', default=False,  store=True, readonly=True, compute='set_tieneunop')
    tiene_op = fields.Boolean(string='Tiene Operarios?', default=False, store=True, readonly=True,  compute='set_tieneunop')

    tiene_ud_tipos = fields.Char(string='Tipos UD', store=True, readonly=True, compute='set_tieneunop')
    presup_r = fields.Integer(string='Presupuestos Realizados',  compute='cuenta_presup')

    deudas_r = fields.Integer(string='Cantidad Deudas', store=True, readonly=True,  compute='cuenta_deudas')
    deudas2_r = fields.Integer(string='Cantidad Pagos totales', store=True, readonly=True,  compute='cuenta_deudas')
    deudas_t = fields.Char(string='Deudas Rec', store=True, readonly=True,   compute='cuenta_deudas_total')
    deudas_total = fields.Float(string='Deudas T.')
    usos_total_prod=fields.Integer(string="Usos Total", store=True, readonly=True,  compute='set_usos_total_prod')
    usos_total_pers=fields.Integer(string="C.Usos Total Personal", store=True, readonly=True,  compute='set_usos_total_pers')
    prueba=fields.Boolean(string='Estado de Prueba', default=False, track_visibility='onchange')
    desc = fields.Text(string='Descripcion', track_visibility='onchange')
    calificacion = fields.Selection([('0', ''),('1', 'NO LLAMAR'),('2', 'Malo'),('3', 'Aceptable'),('4', 'Apto para probar'),('5', 'Excelente')],string='Calificación',help="Puntuación segùn tipo de mensaje que requiere:\n 5) Los fijos, Comunicarles 1ro \n 4) A probarlos si no hay 5) disponibles. Comunicarles 2do \n 3 y 2) Los probados que no cumplen para hablarles siempre ya caen en esta puntuación de 2 a 3 (2 malo, 3 aceptable). \n 1) BANEADOS. NO LLAMAR.", track_visibility='onchange')

    adjuntos_lines= fields.One2many('abatar.proveedores.adjuntos', 'proveedores_id', string='Adjuntos', track_visibility='onchange')

    uso_elem=fields.One2many('abatar.proveedores.elementos', 'proveedor_id', string="Elementos adeudados", track_visibility='onchange')

    @api.onchange('zona')
    def set_zona_map(self):
        for rec in self:
            if rec.zona_map==False and rec.zona:
                if rec.zona.upper().find('CABA')>=0 or rec.zona.upper().find('CIUDAD AUTONOMA DE BUENOS AIRES')>=0 or rec.zona.upper().find('CIUDAD AUTÓNOMA DE BUENOS AIRES')>=0:
                    rec.zona_map='Centro'
                else:
                    print('Working...', rec.zona)
                    N='El Talar'
                    O='Moreno'
                    SO='Barrio Uno'
                    S='Florencio Varela'
                    timeN, kmsN=calcula_distancia(self,rec.zona, N)
                    timeO, kmsO=calcula_distancia(self,rec.zona, O)
                    timeSO, kmsSO=calcula_distancia(self,rec.zona, SO)
                    timeS, kmsS=calcula_distancia(self,rec.zona, S)
                    kms=[kmsN, kmsO, kmsSO, kmsS]
                    zonas=['Norte','Oeste','SurOeste','Sur']
                    kmZ=1000
                    zona=''
                    for i in range(len(kms)):
                        if kms[i]<kmZ:
                            kmZ=kms[i]
                            zona=zonas[i]
                    if kmZ==1000:

                        print('Work NOT FOUND', zona)

                    else:
                        print('Work DONE!', zona)

                        rec.zona_map=zona


    def set_usos_total_prod(self):
        for rec in self:
            usos=0
            for prev in rec.productos_lines:
                if prev.sv_count:
                    usos+=prev.sv_count
            rec.usos_total_prod=usos

    def set_usos_total_pers(self):
        for rec in self:
            usos=0
            for prev in rec.personal_lines:
                if prev.sv_count:
                    usos+=prev.sv_count
            rec.usos_total_pers=usos


    def personal_quick(self):
        for rec in self:
            vals={}
            if rec.name:
                vals['name']=rec.name
                if rec.tel:
                    vals['tel']=rec.tel
                if rec.dni:
                    vals['dni']=rec.dni
                vals['proveedor_id']=rec.id
                rec.personal_lines = [(0,0,vals)]


    @api.depends('name_seq', 'name', 'deudas_t')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=str(rec.name_seq)
            if rec.name:
                rec.name_gral+= ' '+str(rec.name)
            if rec.deudas_t:
                rec.name_gral+=' - $'+str(rec.deudas_t)


    #@api.onchange('dni')
    def refresh(self):
        for rec in self.env['abatar.proveedores'].search([]):
            if rec.desc:
                rec.write({'desc':rec.desc+'.'})
            else:
                rec.write({'desc':'.'})


    @api.multi
    def deudas_cl(self):
        return {
            'name': _('Deudas'),
            'domain': [('proveedor.id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.deudas',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def deudas2_cl(self):
        return {
            'name': _('Deudas'),
            'domain': [('proveedor.id', '=', self.id), ('active', 'in', (True, False))],
            'view_type': 'form',
            'res_model': 'abatar.deudas',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def presup_cl(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: presup_cl')
        print('he16')
        return {
            'name': _('Presupuestos'),
            'domain': [('proveedor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'abatar.crm.presupuestos',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.depends('productos_lines', 'productos_lines.tipo', 'productos_lines.name_gral', 'desc')
    def set_tieneunop(self):
        for rec in self:
            rec.tiene_un = False
            rec.tiene_op = False
            rec.tiene_gr = False
            rec.tiene_emb = False
            tiene_ud_tipos = ' '
            for vec in rec.productos_lines:
                if vec.tipo.name == 'unidad':
                    rec.tiene_un = True
                    if vec.subtipo.letra:
                        if tiene_ud_tipos.find(' ' + str(vec.subtipo.letra) + ' ') > -1:
                            pass
                        else:
                            tiene_ud_tipos += str(vec.subtipo.letra) + ' '
                    elif vec.subtipo.name:
                        if tiene_ud_tipos.find(' ' + str(vec.subtipo.name[-2]) + ' ') > -1:
                            pass
                        else:
                            tiene_ud_tipos += vec.subtipo.name[-2] + ' '
                    else:
                        tiene_ud_tipos += 'ND '

                elif vec.tipo.name == 'operario':
                    rec.tiene_op = True
                elif vec.tipo.name == 'embalaje':
                    rec.tiene_emb = True
                elif vec.tipo.name == 'grua':
                    rec.tiene_gr = True
                    if vec.subtipo.letra:
                        if tiene_ud_tipos.find(' ' + str(vec.subtipo.letra) + ' ') > -1:
                            pass
                        else:
                            tiene_ud_tipos += str(vec.subtipo.letra) + ' '
                    elif vec.subtipo.name:
                        if tiene_ud_tipos.find(' ' + str(vec.subtipo.name[-2]) + ' ') > -1:
                            pass
                        else:
                            tiene_ud_tipos += vec.subtipo.name[-2] + ' '
                    else:
                        tiene_ud_tipos += 'ND '

            tiene_ud_tipos2 = ' '
            if tiene_ud_tipos != ' ':
                if tiene_ud_tipos.find(' OP ') > -1:
                    tiene_ud_tipos2 += 'OP '
                if tiene_ud_tipos.find(' A ') > -1:
                    tiene_ud_tipos2 += 'A '
                if tiene_ud_tipos.find(' B ') > -1:
                    tiene_ud_tipos2 += 'B '
                if tiene_ud_tipos.find(' C ') > -1:
                    tiene_ud_tipos2 += 'C '
                if tiene_ud_tipos.find(' D ') > -1:
                    tiene_ud_tipos2 += 'D '
                if tiene_ud_tipos.find(' E ') > -1:
                    tiene_ud_tipos2 += 'E '
                if tiene_ud_tipos.find(' F ') > -1:
                    tiene_ud_tipos2 += 'F '
                if tiene_ud_tipos.find(' FF ') > -1:
                    tiene_ud_tipos2 += 'FF '
                if tiene_ud_tipos.find(' G ') > -1:
                    tiene_ud_tipos2 += 'G '
            rec.tiene_ud_tipos = tiene_ud_tipos2
            '''
            if emb == True :
                if rec.tiene_op == True or rec.tiene_un == True:
                    rec.write({'tipo_str': 'varios'})
                else:
                    rec.write({'tipo_str': 'embalaje'})
            elif rec.tiene_op == True and rec.tiene_un == True:
                rec.write({'tipo_str': 'unidad y operario'})
            elif rec.tiene_op == True and rec.tiene_un == False:
                rec.write({'tipo_str': 'operario'})
            elif rec.tiene_op == False and rec.tiene_un == True:
                rec.write({'tipo_str': 'unidad'})
            '''
    @api.depends('tiene_un', 'tiene_op','tiene_gr','tiene_emb', 'desc')
    def set_tipostr2(self):
        for rec in self:
            if rec.tiene_gr:
                string='grua con unidad y operario'
                if rec.tiene_op or rec.tiene_un or rec.tiene_emb:
                    if rec.tiene_emb:
                        string='grua con varios'
                    elif rec.tiene_op and rec.tiene_un:
                        string='grua con unidad y operario'
                    elif rec.tiene_op:
                        string='grua con operario'
                    elif rec.tiene_un:
                        string='grua con unidad'
                    elif rec.tiene_emb:
                        string='grua con emb'
                    else:
                        string='grua'
                else:
                    string='grua'
            else:
                string='unidad y operario'

                if rec.tiene_emb and (rec.tiene_op or rec.tiene_un):
                    string='varios'
                elif rec.tiene_emb:
                    string='embalaje'
                elif rec.tiene_op and rec.tiene_un:
                    string='unidad y operario'
                elif rec.tiene_op:
                    string='operario'
                elif rec.tiene_un:
                    string='unidad'
            rec.tipo_str2=string
    @api.onchange('tipo_str2')
    def set_tipostr(self):
        for rec in self:
            if rec.tipo_str2:
                rec.tipo_str=rec.tipo_str2


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

        if 'active' in vals:
            if vals['active']:
                for record in self:
                    hijos = record.with_context(active_test=False).productos_lines
                    recset = hijos.filtered(lambda h: h.unactived_by_father and not h.active)
                    if recset:
                        recset.write({'active': True,'unactived_by_father':False})
            else:
                for record in self:
                    hijos = record.productos_lines  # aquí solo necesito los activos
                    recset = hijos.filtered(lambda h: h.active)
                    if recset:
                        recset.write({'active': False,'unactived_by_father':True})
        res = super(AbatarProveedores, self).write(vals)
        return res


    #@api.multi
    #def ordenes_cl(self):
    #    return {
    #        'name': _('Deudas'),
    #        'domain': [('proveedor.id', '=', self.sector), ('cliente_gral', '=', self.clientes_gral_id.id), ('active', 'in', [False, True])],
    #        'view_type': 'form',
    #        'res_model': 'abatar.deudas',
    #        'view_id': False,
    #        'view_mode': 'tree,form',
    #        'type': 'ir.actions.act_window',
    #    }


    @api.model
    def create(self, vals):
        if vals.get('forc_name_seq'):
            if vals.get('name_seq', _('New')) == _('New'):
                vals['name_seq'] = 'P'+vals.get('forc_name_seq')
        else:
            if vals.get('name_seq', _('New')) == _('New'):
                vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.proveedores.sequence') or _('New')

        result = super(AbatarProveedores, self).create(vals)
        return result


class AbatarProveedoresAdjuntos(models.Model):
    _name = "abatar.proveedores.adjuntos"
    _description = "Abatar adjuntos de Proveedores"
    _rec_name = 'name'
    _order='fecha_op desc'

    name=fields.Char(string="Nombre de Archivo")
    fecha_op = fields.Date(string='Fecha de carga', default=fields.Date.today)
    adjunto = fields.Binary(string='Adjunto', required=True)
    desc=fields.Char(string="Descripcion")

    proveedores_id = fields.Many2one('abatar.proveedores', string='proveedores ID')


class AbatarProveedoresProductos(models.Model):
    _name = "abatar.proveedores.productos"
    _description = "Abatar Proveedores Productos"
    _rec_name = "name_gral"

    active=fields.Boolean(string='Active', default=True)
    unactived_by_father=fields.Boolean(string='Unlink_by_parent', default=False)
    name_gral=fields.Char(string='REc name', store=True, readonly=True, compute='set_name_gral')
    desc = fields.Char(string='Descripcion')
    tarifa = fields.Float(string='Tarifa', required=True)
    subtipo = fields.Many2one('abatar.productos', string='Producto', required=True)
    tipo = fields.Many2one('abatar.tipo', string='Tipo', required=True)
    tipo_name=fields.Char(string="Tipo", related='tipo.name', store=True, readonly=True)
    minimo = fields.Float(string='Minimo')
    adjunto = fields.Binary(string='Fotos adjunta')

    patente = fields.Char(string='Patente')
    modelo = fields.Char(string='Modelo')
    largo = fields.Float(string='Largo')
    alto = fields.Float(string='Alto')
    ancho = fields.Float(string='Ancho')
    kgs = fields.Integer(string='KGS')
    m3=fields.Float(string='M3', compute='set_m3')
    c_pala=fields.Boolean(string='Pala')
    c_rastreo=fields.Boolean(string='Rastro satelital')
    c_hidrogrua=fields.Boolean(string='Hidrogrua')
    tipo_caja_new=fields.Many2one('abatar.tiposcaja',string='Tipo de caja')
    tipo_caja=fields.Selection([('1', 'furgon'),('2', 't/puertas'),('3', 'furgon c/arco y lona'),('4', 'sider'),('5', 'frio'),
                                ('6', 'paquetero'),('7', 'playo'),('8', 'Balancin'),('9', 'Semi')],
                               string='Tipo de caja VIEJO no usar')

    tiene_ud=fields.Boolean(string='Tiene Unidad', compute='set_tiene_ud')

    proveedor_id = fields.Many2one('abatar.proveedores', string='Proveedor ID')
    prov_zona = fields.Selection(related='proveedor_id.zona_map', store=True,readonly=True,string='Proveedor Zona')
    prov_id_num = fields.Integer(related='proveedor_id.id', string='Proveedor ID num')
    sv_counts=fields.Integer(string="Cantidad de usos", compute='get_sv_count', store=True, readonly=True)
    sv_ultimo=fields.Datetime(string="Ultimo uso", compute='get_sv_ult', store=True, readonly=True)
    sv_ultimos_30d=fields.Integer(string="Ultimos usos 30 días", compute='get_sv_ult', store=True, readonly=True)

    sv_ultimos_1a=fields.Integer(string="Ultimos usos 1 año", compute='get_sv_ult', store=True, readonly=True)


    def get_sv_ult(self):
        for one in self:
            result= self.env['abatar.ordenes.lines'].search([('proveedor_producto','=',one.id),('orden_id','!=',False)])
            ids=[]
            for res in result:
                if res.orden_id:
                    ids.append(res.orden_id.id)

            hoy = datetime.today()
            hace_30_dias = hoy - timedelta(days=30)
            hace_365_dias = hoy - timedelta(days=365)
            fecha= self.env['abatar.ordenes'].search([('id','in',ids),('fecha_ejecucion','!=',False), ('active','in',[True,False])],order='fecha_ejecucion desc', limit=1).fecha_ejecucion
            cant_menos_30_dias= self.env['abatar.ordenes'].search_count([('id','in',ids),('fecha_ejecucion','!=',False),('fecha_ejecucion', '>=', hace_30_dias),('fecha_ejecucion', '<=', hoy), ('active','in',[True,False])])
            cant_menos_365_dias= self.env['abatar.ordenes'].search_count([('id','in',ids),('fecha_ejecucion','!=',False),('fecha_ejecucion', '>=', hace_365_dias),('fecha_ejecucion', '<=', hoy), ('active','in',[True,False])])
            #fecha= self.env['abatar.ordenes.lines'].search([('proveedor_producto','=',one.id),('uso_orden','!=',False)],order='uso_orden desc', limit=1).uso_orden

            one.sv_ultimos_30d = cant_menos_30_dias
            one.sv_ultimos_1a = cant_menos_365_dias
            one.sv_ultimo = fecha

    def get_sv_count(self):
        for one in self:
            count= self.env['abatar.ordenes.lines'].search_count([('proveedor_producto','=',one.id),('orden_id','!=',False)])

            one.sv_counts = count

    @api.one
    @api.depends('patente', 'modelo')
    def set_tiene_ud(self):
        for rec in self:
            bool=False
            if rec.patente:
                bool=True
            if rec.modelo:
                bool=True
            rec.tiene_ud=bool

    @api.one
    @api.depends('ancho', 'ancho', 'largo')
    def set_m3(self):
        for rec in self:
            rec.m3=rec.largo*rec.alto*rec.ancho


    @api.one
    @api.depends('subtipo', 'desc', 'patente', 'modelo')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=str(rec.subtipo.name)
            if rec.patente:
                rec.name_gral+=' - '+str(rec.patente)
            if rec.modelo:
                rec.name_gral+=' '+str(rec.modelo)
            if rec.desc:
                rec.name_gral+=' - '+str(rec.desc)


class AbatarProveedoresPersonal(models.Model):
    _name = "abatar.proveedores.personal"
    _description = "Abatar Proveedores personal"
    _rec_name = "name"

    active=fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Nombre')
    tel = fields.Char(string='Telefono')
    dni = fields.Char(string='DNI')
    fecha_nac = fields.Char(string='Fecha de Nacimiento')

    proveedor_id = fields.Many2one('abatar.proveedores', string='Personal ID')
    sv_count=fields.Integer(string="Cantidad de usos", compute='get_sv_count2')

    def get_sv_count2(self):
        for one in self:
            count=0
            axi=one.proveedor_id.id
            result=self.env['abatar.ordenes'].search([])
            if result:
                for line in self.env['abatar.ordenes'].search([]):
                    if line.orden_lines:
                        for rec in line.orden_lines:
                            if rec.proveedor_id.id== axi:
                                #if rec.proveedor_personal.name==one.name:
                                count+=  1
            one.sv_count = count

class AbatarDeudas(models.Model):
    _name = "abatar.deudas"
    _description = "Abatar Deudas"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name_gral"
    _order = 'id desc'

    @api.one
    @api.depends('proveedor')
    def _ref(self):
        for rec in self:
            rec.seq = rec.proveedor.name_seq

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.calendario:
                rec.calendario.unlink()
                rec.calendario=False
            if rec.orden:

                rec.deuda=0
                if rec.orden.desc1:
                    rec.orden.write({'desc1':rec.orden.desc1+"a"})
                else:
                    rec.orden.write({'desc1':"a"})
        res = super(AbatarDeudas, self).unlink()
        return res

    name_seq = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    name_gral=fields.Char(string="Nombre rec", store=True, readonly=True, compute='set_name_gral')
    fecha = fields.Datetime(string='Fecha de Deuda', required=True, default = fields.datetime.now())
    proveedor = fields.Many2one('abatar.proveedores', string='Proveedor')
    clientes = fields.Many2one('abatar.clientes', string='Clientes')
    seq = fields.Char(string='Referencia de Proveedor', compute='_ref')
    tipo = fields.Char(string='Descripcion')
    deuda = fields.Float(string='Deuda')
    pago = fields.Float(string='Pago')
    saldo = fields.Float(string='Saldo', compute='set_saldo')

    subtotal= fields.Float(string="Monto Total", store=True, readonly=True, compute='set_subtotal')
    active = fields.Boolean('Active', default=True)
    caja = fields.Many2one('abatar.caja', string='caja')
    orden = fields.Many2one('abatar.ordenes', string='Orden')
    fecha_calen = fields.Datetime(string='Fecha de Pago programada')
    calendario = fields.Many2one('abatar.calendario', string='calendario', default=False)
    fecha_pago = fields.Date(string='Fecha de pago')
    desc=fields.Text(string="Descripcion")
    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    adjunto= fields.One2many('abatar.deudas.adjuntos', 'deudas_id', string='Adjuntos')

    def set_saldo(self):
        for rec in self:
            if rec.pago and rec.deuda:
                rec.saldo=rec.deuda-rec.pago
            elif rec.deuda:
                rec.saldo=rec.deuda

    @api.multi
    def write(self, vals):
        if 'fecha_calen' in vals:
            if self.calendario:
                revisac = self.env['abatar.calendario'].search(
                    [('id', '=', self.calendario.id)])
                if revisac:
                    if str(revisac.fecha_ejecucion) != vals.get('fecha_calen'):
                        revisac.write({'fecha_ejecucion': vals.get('fecha_calen')})

            else:
                pago=self.env['abatar.servicios.calendario'].search([('name', '=', 'Pagos')], limit=1).id
                calen_id = self.env['abatar.calendario'].search([], order='id desc',
                                                                limit=1).id + 1

                vals1 = {
                    'deuda': self.id,
                    'calendario_id': calen_id,
                }
                vals2 = {
                    'name': self.name_seq,
                    'accion': pago,
                    'deudas': self.id,
                    'ordenes': False,
                    'materiales': False,
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
        res = super(AbatarDeudas, self).write(vals)
        if vals.get('orden'):
            orden=self.env['abatar.ordenes'].search([('id', '=', vals.get('orden')), ('active', 'in', (True, False))], limit=1)
            if orden.desc1:
                orden.desc1 += "a"
            else:
                orden.desc1 = "a"
        elif self.orden:
            if self.orden.desc1:
                self.orden.desc1 += "a"
            else:
                self.orden.desc1 = "a"
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AbatarDeudas, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec


    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.deudas.sequence') or _('New')
        res_id = self.env['abatar.deudas'].search([('active', 'in', (True, False))], order='id desc',limit=1).id + 1
        res = super(AbatarDeudas, self).create(vals)
        if vals.get('fecha_calen'):
            pago=self.env['abatar.servicios.calendario'].search([('name', '=', 'Pagos')], limit=1).id
            calen_id = self.env['abatar.calendario'].search([], order='id desc',limit=1).id + 1

            vals1 = {
                'deuda': res_id,
                'calendario_id': calen_id,
            }
            vals2 = {
                'name': vals.get('name_seq'),
                'accion': pago,
                'deudas': res_id,
                'ordenes': False,
                'materiales': False,
                'fecha_ejecucion': vals.get('fecha_calen'),
                'calendario_lines': [(0, 0, vals1)],
            }

            vals['calendario'] = self.env['abatar.calendario'].create(vals2).id
        if vals.get('orden'):
            orden=self.env['abatar.ordenes'].search([('id', '=', vals.get('orden')), ('active', 'in', (True, False))], limit=1)
            if orden:
                if orden.desc1:
                    orden.desc1 += "a"
                else:
                    orden.desc1 = "a"


        return res


    @api.depends('proveedor', 'clientes', 'orden', 'deuda', 'pago')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral =''
            if rec.proveedor:
                if rec.proveedor.name:
                    rec.name_gral=str(rec.proveedor.name)
                elif rec.proveedor.id:
                    rec.name_gral='prov.'+str(rec.proveedor.name)
            if rec.orden:
                rec.name_gral+='- '+str(rec.orden.name_seq)
            if rec.clientes:
                rec.name_gral+=' - '+str(rec.clientes.name_gral)
            if rec.deuda:
                deuda=rec.deuda
                if rec.pago:
                    pago=rec.pago
                    if round(deuda-pago, 2)==0:
                        rec.name_gral+='-PAGADO- $' + str(deuda)
                    else:
                        rec.name_gral+=' - saldo: $'+str(deuda-pago)+ '/$' + str(deuda)
                else:
                    rec.name_gral += ' - $' + str(deuda)

    @api.one
    @api.depends('deuda', 'pago')
    def set_subtotal(self):
        for rec in self:
            monto=0
            if rec.deuda:
                monto += rec.deuda
            if rec.pago:
                monto-=rec.pago
            rec.subtotal=round(monto, 2)


    def pagar_action(self, fecha_pago):

        caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', fecha_pago)], limit=1)

        if caja_act:
            pass
        else:
            vals1={
                'fecha_de_caja':fecha_pago
            }
            caja_act = self.env['abatar.caja'].create()
            caja_act.write(vals1)
        for deuda_act in self:
            if deuda_act.deuda:
                vals2={
                    'tipo': self.env['abatar.caja.tipo'].search([('name', '=', 'Proveedores')]).id,
                    'deuda_id' : deuda_act.id,
                    'texto' : 'Pagado por acción en fecha %s' % str(fields.Date.context_today),
                    'monto' : deuda_act.deuda,
                    'caja_id' : caja_act.id,
                    'adjunto' : self.adjunto,
                }
                caja_act.write({'linea_movimientos':[(0,0,vals2)]})




class AbatarDeudasAdjuntos(models.Model):
    _name = "abatar.deudas.adjuntos"
    _description = "Abatar adjuntos de Deudas"
    _rec_name = 'name_gral'

    name_gral = fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date(string='Fecha de caja')
    adjunto = fields.Binary(string='Adjunto')
    desc = fields.Char(string="Descripcion")

    deudas_id = fields.Many2one('abatar.deudas', string='deudas ID')


    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'AD' + str(rec.id) + str(rec.adjunto)



class AbatarProveedoresElem(models.Model):
    _name = "abatar.proveedores.elementos"
    _description = "Abatar Proveedores elementos prestados"



    elem_id=fields.Many2one('abatar.elementos', string="Elemento")
    cant=fields.Integer(string="Cantidad", default=1)
    proveedor_id=fields.Many2one('abatar.proveedores', string="Proveedor")
    ordenes_id=fields.Many2one('abatar.ordenes', string="Orden_id")
    elem_slot=fields.Many2one('abatar.ordenes.elem', string="Adeudado elem")


class AbatarCadena(models.Model):
    _name = "abatar.cadena"
    _description = "Abatar Cadena"

    op_ud=fields.Selection([('op', 'op'), ('ud', 'ud')], string="Op o Ud?", required=True)
    tipo=fields.Char(string="tipo de Sv (Flete, Mudanza, Reparto, Previa, etc.)")
    fecha=fields.Char(string="fecha")
    hora_inicio=fields.Char(string="hora_inicio")
    origen=fields.Char(string="origen", required=True)
    contacto=fields.Char(string="contacto")
    destino=fields.Char(string="destino")
    precio=fields.Char(string="precio")
    texto=fields.Char(string="texto")

class AbatarTiposcaja(models.Model):
    _name = "abatar.tiposcaja"
    _description = "Abatar Tipos de Caja"

    name=fields.Char(string="tipo de Caja")
    '''
    tipo_caja=fields.Selection([('1', 'furgon'),('2', 't/puertas'),('3', 'furgon c/arco y lona'),('4', 'sider'),('5', 'frio'),
                                ('6', 'paquetero'),('7', 'playo'),('8', 'Balancin'),('9', 'Semi')],
                               string='Tipo de caja')
                               '''

