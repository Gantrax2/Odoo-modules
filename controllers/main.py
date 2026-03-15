from odoo import http, _, fields as Fields
from odoo.http import request
import requests
import datetime
import time
from odoo.addons.om_abatartrucks.Analize import Typyze,Typyze2, Analize_model3, BUSQUEDAON

CUENTA_API_KEY=True
BUSQUEDA_MAIN=False

def sinobool(a):
    if a.upper()=="SI":
        return True
    else:
        return False
def Tomas(a):
    for i in range(len(a)):
        if a[i] == " ":
            a = a[:i] + "+" + a[i + 1:]
    return a
def Topc(a):
    for i in range(len(a)):
        if a[i] == " ":
            a = a[:i] + "%20" + a[i + 1:]
    return a


def redond(x):
    if x - int(x) >= 0.25:
        if x - int(x) >= 0.75:
            return int(x) + 1
        else:
            return int(x) + 0.5
    else:
        return int(x)

def inv_Tomas(a):
    for i in range(len(a)):
        if a[i] == "+":
            a = a[:i] + " " + a[i + 1:]
    return a

def numtostr(val):
    if val>=1000000:
        a=str(int(val / 1000000)) + '.'
        val2=val-int(val / 1000000)*1000000
        a+= '%03i.%03i' % (int(val2 / 1000), int(val2) - (int(val2 / 1000) * 1000))
        a+= ',' + str(round(val - int(val), 2))[2:]
    else:
        a = '%i.%03i' % (int(val / 1000), int(val) - (int(val / 1000) * 1000))
        a+= ',' + str(round(val - int(val), 2))[2:]
    return a
def calcula_distancia(direccion1, direccion2):

    api_key = '&units=imperial&key=AIzaSyAvffBICS3JwKVK7xSTj_5sXDQkd5iU6wA'



    print('calc_dist oyd:', direccion1, direccion2)
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + direccion1 + "&destinations=" + direccion2 + api_key

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    anex2='ELEMENTS RESPONSE: '
    for key1 in response.json()["rows"][0]["elements"][0].keys():
        try:
            for key2 in response.json()["rows"][0]["elements"][0][key1].keys():
                anex2+='Elem:'+key1+','+key2+':'+str(response.json()["rows"][0]["elements"][0][key1][key2])+' - '
        except:
            try:
                anex2 += 'Elem:' + key1 + str(response.json()["rows"][0]["elements"][0][key1]) + ' - '
            except:
                try:
                    anex2 +=str(response.json()["rows"][0]["elements"][0]["duration"]["value"])
                except:
                    pass
            #if key1=='status' and response.json()["rows"][0]["elements"][0][key1]=='NOT_FOUND':


    #
    print('oyd:', direccion1, direccion2)
    print('hi1:', response.json())

    try:
        tiempo_value = 2*response.json()["rows"][0]["elements"][0]["duration"]["value"]
    except:
        tiempo_value = 0.2
    try:
        distance_value = response.json()["rows"][0]["elements"][0]["distance"]["value"]
    except:
        distance_value = 2000

    kms = distance_value / 1000

    if response.json()['status']=='INVALID_REQUEST':
        tiempo_value, kms = 0.2, 2
        anex2+=' - INVALID REQUEST'
    return tiempo_value, kms, anex2

class Crmpage(http.Controller):

    @http.route('/telansw', type="http", auth="public", website=True)
    def abatar_cons_prov(self, **kw):
        # return "hello World"
        # Requiere como input "tipo=(unidad/operario) & tipoud= & zona=(N, O, SO, S) & amb=(Numero) & pers=(Numero) & origen=(Direccion) & p_origen=(Numero) & asc_origen=(No Hay, Chico, Mediano, Grande) & acarr_origen=(1=si, 0=no) & destino=(Direccion) & p_destino=(Numero) & asc_destino=(No Hay, Chico, Mediano, Grande) &  acarr_destino=(1=si, 0=no) & hay_emb_fino= (Si o No)"

        tipoud=''
        tipo = inv_Tomas(kw.get('tipo'))
        if tipo=='unidad':
            tipoud=inv_Tomas(kw.get('tipoud'))

        zona = inv_Tomas(kw.get('zona'))

        if tipoud:
            resul = http.request.env['abatar.proveedores'].search(['|',('tipo_str', '=', tipo),('tipo_str', '=', 'unidad y operario'),('tiene_ud_tipos', 'like', tipoud), '|',('zona_map', '=', zona),('zona_map', '=', False)])
        else:
            resul = http.request.env['abatar.proveedores'].search(
                ['|', ('tipo_str', '=', tipo), ('tipo_str', '=', 'unidad y operario'),
                 '|', ('zona_map', '=', zona), ('zona_map', '=', False), ('empleado', '=', False)])

        name=[]
        tel=[]
        asd=''
        for rec in resul:
            asd+=rec.name+' , '+ rec.tel + '<br/>'
            name.append(rec.name)
            tel.append(rec.tel)


        #web = 'https://grupoabatar.com.ar/index.php/' + datos2
        return asd#request.redirect(web)


    @http.route('/crm21', type="http", auth="public", website=True, csrf=False, methods=['POST'])
    def abatar_crmonline(self, **kw):

        return "No se proporcionó el nombre"

    @http.route('/crm22', type="http", auth="public", website=True, csrf=False, methods=['GET'])
    def abatar_crmonline2(self, **kw):
        res = {}

        res['servicio'] = request.env['abatar.servicios'].search([('name', '=', 'Mudanza')]).id
        res['name'] = inv_Tomas(kw.get('name'))
        res['tel'] = inv_Tomas(kw.get('tel'))
        try:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/') + ' 11:00:00'),
                                            '%d/%m/%Y %H:%M:%S')
        except:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/') + ' 11:00:00'),
                                            '%d/%m/%y %H:%M:%S')

        res['fecha_ejecucion'] = AA
        res['es_conocido'] = 'no'
        res['es_ivainc'] = True

        def una_cif(elem):
            try:
                a = int(elem)
            except:
                a = 0
                nums = ['UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS',
                        'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE']
                for i in range(len(nums)):
                    if elem.upper() == nums[i]:
                        a = i + 1
                        break
            return a

        res['mdz_amb'] = una_cif(kw.get('amb'))
        res['mdz_pers'] = una_cif(kw.get('pers'))
        try:
            ori_cya = inv_Tomas(kw.get('cya_origen')).upper()
        except:
            ori_cya = ''
        ori_loc = inv_Tomas(kw.get('loc_origen')).upper()
        ori_prov = inv_Tomas(kw.get('prov_origen')).upper()
        if ori_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            ori_prov = "BS AS"

        try:
            piso_origen = int(kw.get('p_origen'))
        except:
            piso_origen = 0

        PROVS = ['BS AS', 'BUENOS AIRES', 'JUJUY', 'SALTA', 'TUCUMAN', 'FORMOSA',
                 'CHACO', 'SANTIAGO DEL ESTERO', 'STGO. DEL ESTERO', 'LA RIOJA', 'SAN JUAN',
                 'CATAMARCA', 'MENDOZA', 'SAN LUIS', 'CORDOBA', 'SANTA FE', 'ENTRE RIOS', 'MISIONES',
                 'CORRIENTES', 'NEUQUEN', 'RIO NEGRO', 'CHUBUT', 'SANTA CRUZ', 'STA. CRUZ', 'TIERRA DEL FUEGO']
        coinc = ['PROVINCIA DE BUENOS AIRES']
        for prov in PROVS:
            coinc.append(prov)
            coinc.append('PROVINCIA DE %s' % prov)

        try:
            des_cya = inv_Tomas(kw.get('cya_destino')).upper()
        except:
            des_cya = ''

        des_loc = inv_Tomas(kw.get('loc_destino')).upper()  # destino[len(destino) - des_inv.find(' '):]
        des_prov = inv_Tomas(kw.get('prov_destino')).upper()  # destino[len(destino) - des_inv.find(' '):]
        if des_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            des_prov = "BS AS"

        try:
            piso_destino = int(kw.get('p_destino'))
        except:
            piso_destino = 0
        id_crm_nuevo = http.request.env['abatar.crm'].search([], order='id desc', limit=1).id + 1

        res['destinos_lines2'] = [[0, 0, {'destino': ori_cya, 'piso': piso_origen, 'localidad': ori_loc,
                                          'provincia': ori_prov, 'orden_id_x': id_crm_nuevo}],
                                  [0, 0, {'destino': des_cya, 'piso': piso_destino, 'localidad': des_loc,
                                          'provincia': des_prov, 'orden_id_x': id_crm_nuevo}]]

        asc_ori0 = inv_Tomas(kw.get('asc_origen'))
        asc_des0 = inv_Tomas(kw.get('asc_destino'))
        if asc_ori0 == "No hay":
            asc_ori = '1'
        elif asc_ori0 == "Chico":
            asc_ori = '2'
        elif asc_ori0 == "Mediano":
            asc_ori = '3'
        elif asc_ori0 == "Grande":
            asc_ori = '4'
        else:
            asc_ori = '1'

        if asc_des0 == "No hay":
            asc_des = '1'
        elif asc_des0 == "Chico":
            asc_des = '2'
        elif asc_des0 == "Mediano":
            asc_des = '3'
        elif asc_des0 == "Grande":
            asc_des = '4'
        else:
            asc_des = '1'

        res['mdz_ascensor_origen'] = asc_ori
        acarr_origen = kw.get('acarr_origen')
        acarr_destino = kw.get('acarr_destino')
        acarr2_origen = kw.get('acarr2_origen')
        acarr2_destino = kw.get('acarr2_destino')
        if acarr2_origen:
            acarr2_origen = inv_Tomas(acarr2_origen)
            if acarr2_origen == 'Es mayor a 20m':
                res['mdz_acarreo2_ori'] = True
        if acarr2_destino:
            acarr2_destino = inv_Tomas(acarr2_destino)
            if acarr2_destino == 'Es mayor a 20m':
                res['mdz_acarreo2_des'] = True

        if kw.get('esc_origen'):
            elem_esc_origen = int(kw.get('esc_origen'))
        else:
            elem_esc_origen = 0

        if kw.get('esc_destino'):
            elem_esc_destino = int(kw.get('esc_destino'))
        else:
            elem_esc_destino = 0

        if acarr_origen == "Subsuelo":
            res['mdz_acarreo_ori'] = True
        if acarr_destino == "Subsuelo":
            res['mdz_acarreo_des'] = True
        if elem_esc_origen:
            res['mdz_esc_ori'] = elem_esc_origen
        if elem_esc_destino:
            res['mdz_esc_des'] = elem_esc_destino

        res['mdz_ascensor_destino'] = asc_des
        res['mdz_ascensor_destino'] = asc_des

        res['mdz_ascensor_destino'] = asc_des
        hay_emb_fino = kw.get('hay_emb_fino')
        res['mdz_categ'] = 'B'
        if res['mdz_amb'] == 1:
            res['mdz_carga'] = 10
        elif res['mdz_amb'] == 2:
            res['mdz_carga'] = 8
        else:
            res['mdz_carga'] = 7

        if hay_emb_fino == 'Si':
            res['mdz_hay_emb_f'] = True
        else:
            res['mdz_hay_emb_f'] = False
        todo = True
        res_no = []
        for key in res.keys():
            if key == 'acarr_destino' or key == 'acarr_origen' or key == 'mdz_hay_emb_f' or key == 'mdz_ascensor_origen' or key == 'mdz_ascensor_destino':
                pass
            elif res[key]:
                pass
            else:
                res_no.append(key)
                todo = False

        asd = ''
        datos2 = ''
        if todo == False:
            asd += ' Error - Carga de Pedido Interrumpida. Faltan Datos: </br>'
            datos2 += 'errloadmdz/'
            print('Falta algun dato:', res_no)
            for exc in res_no:
                asd += exc
                # if datos2[-1]=='?':
                #    datos2 += exc
                # else:
                #    datos2 += '&'+exc
            asd += '  -  '

            return asd
        else:
            http.request.env['abatar.crm'].create(res)
            crm = http.request.env['abatar.crm'].search([], order='id desc', limit=1)
            PEDIDO = crm.pedide
            crm.action_crea_calculadora()

            pres = crm.cotizador

            total = round(crm.cotizador_total, 0)
            crm.write({'precio': total})
            if BUSQUEDAON == True and BUSQUEDA_MAIN == True:
                crm.resumen_busqueda = Analize_model3(crm, crm._name,
                                                      [('id', '=', crm.id), ('active', 'in', (True, False))])

            datos2 += 'loadmdz/?'
            datos2 += 'pedido=' + str(PEDIDO)
            datos2 += '&origen=' + str(ori_cya) + ', ' + str(ori_loc) + ', ' + str(ori_prov)
            datos2 += '&destino=' + str(des_cya) + ', ' + str(des_loc) + ', ' + str(des_prov)
            datos2 += '&precio=' + str(total)

            web = 'https://grupoabatar.com.ar/index.php/' + datos2
            return request.redirect(web)



    @http.route('/crm3', type="http", auth="public", website=True, csrf=False, methods=['GET'])
    def abatar_crmonline3(self, **kw):
        res = {}
        try:
            res['type'] = int(kw.get('type'))

        except:

            return "AYUDA ! :   Bienvenido al GET Method para consultar datos de Grupo-Abatar." \
                   "         debes enviar los datos:" \
                   "         'type'=int entre 1 (obtener fields),2 (obtener ids),3 (obtener (str(value),str(type))),4 (escribir value ['d/m/Y H:M:S' para datetime , 'd/m/Y' para date, 0/1 para booleano])." \
                   "          'model'=string. Un modelo existente de odoo (obligatorio, tanto para type 1, 2, 3 y 4)" \
                   "         " \
                   "          SI ELIJES 'type'=3 debes además enviar :" \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para obtener su valor convertido a string mediante str(). " \
                   "         SI ELIJES 'type'=4 debes enviar " \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para elejir su valor. " \
                   "             'value' Valor de campo a escribir" \
                   "         " \
                   "         " \
                   "          Buena suerte!."

        res['model'] = kw.get('model')

        if not res['type']:

            return "AYUDA ! :   Bienvenido al GET Method para consultar datos de Grupo-Abatar." \
                   "         debes enviar los datos:" \
                   "         'type'=int entre 1 (obtener fields),2 (obtener ids),3 (obtener (str(value),str(type))),4 (escribir value ['d/m/Y H:M:S' para datetime , 'd/m/Y' para date, 0/1 para booleano])." \
                   "          'model'=string. Un modelo existente de odoo (obligatorio, tanto para type 1, 2, 3 y 4)" \
                   "         " \
                   "          SI ELIJES 'type'=3 debes además enviar :" \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para obtener su valor convertido a string mediante str(). " \
                   "         SI ELIJES 'type'=4 debes enviar " \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para elejir su valor. " \
                   "             'value' Valor de campo a escribir" \
                   "         " \
                    "         " \
                   "          Buena suerte!."
        if res['type']==1:
            try:
                a=''
                Fields.Glog('Except:'+res['model'])
                Fields.Glog(http.request.env[res['model']].search([('active','in',(True, False))], limit=1).fields_get())
                for field in http.request.env[res['model']].search([('active','in',(True, False))], limit=1).fields_get():
                    a+=field+"<\\br>"
                    Fields.Glog(field+"<\\br>")
                return a
            except:

                a=''
                Fields.Glog('Except:'+res['model'])
                Fields.Glog(http.request.env[res['model']].search([], limit=1).fields_get())
                for field in http.request.env[res['model']].search([], limit=1).fields_get():
                    a+=field+"<\\br>"
                    Fields.Glog(field+"<\\br>")
                return a
        elif res['type']==2:

            try:
                a = ''
                for rec in http.request.env[res['model']].search([('active', 'in', (True, False))]):
                    a += str(rec.id) + "<\\br>"
                return a
            except:
                a = ''
                for rec in http.request.env[res['model']].search([]):
                    a += str(rec.id) + "<\\br>"
                return a

        elif res['type']==3:

            res['id'] = int(kw.get('id'))
            res['field'] = kw.get('field')
            try:
                return (str(http.request.env[res['model']].search([('id','=',res['id']),('active', 'in', (True, False))], limit=1)[res['field']]),str(type(http.request.env[res['model']].search([('id','=',res['id']),('active', 'in', (True, False))], limit=1)[res['field']])))
            except:
                return (str(http.request.env[res['model']].search([('id','=',res['id'])], limit=1)[res['field']]),str(type(http.request.env[res['model']].search([('id','=',res['id']),('active', 'in', (True, False))], limit=1)[res['field']])))

        elif res['type']==4:
            res['id'] = int(kw.get('id'))
            res['field'] = kw.get('field')
            try:
                resul =http.request.env[res['model']].search([('id','=',res['id']),('active', 'in', (True, False))], limit=1)
            except:
                resul= http.request.env[res['model']].search([('id','=',res['id'])], limit=1)

            res['value'] = Typyze2(resul[res['field']],inv_Tomas(kw.get('value')))

            try:
                resul.write({res['field']:res['value']})
                return 'True'
            except:
                return 'False'

        else:
            return "Bienvenido al GET Method para consultar datos de Grupo-Abatar." \
                   "         debes enviar los datos:" \
                   "         'type'=int entre 1 (obtener fields),2 (obtener ids),3 (obtener (str(value),str(type))),4 (escribir value ['d/m/Y H:M:S' para datetime , 'd/m/Y' para date, 0/1 para booleano])." \
                   "          'model'=string. Un modelo existente de odoo (obligatorio, tanto para type 1, 2, 3 y 4)" \
                   "         " \
                   "          SI ELIJES 'type'=3 debes además enviar :" \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para obtener su valor convertido a string mediante str(). " \
                   "         SI ELIJES 'type'=4 debes enviar " \
                   "             'id'=numero " \
                   "             'field'=string. Nombre de campo para elejir su valor. " \
                   "             'value' Valor de campo a escribir" \
                   "         " \
                    "         " \
                   "          Buena suerte!."





    @http.route('/crm4', type="http", auth="public", website=True, csrf=False, methods=['GET'])
    def abatar_crmonline4(self, **kw):
        res = {}
        try:
            res['crm_id'] = int(kw.get('crm_id'))

        except:

            return "AYUDA ! :   Bienvenido al 'WRITE ACCION CRM Method' para escribir respuestas de whatsapp de Grupo-Abatar. ;" \
                   "         debes enviar los datos:;" \
                   "         'crm_id'=int ;" \
                   "         'write_id'=int 0 si no hay id, para crear uno nuevo. o un id != 0 para editar uno existente (solo rta y desc).;" \
                   "          'accion'= string. Un nombre ya existente de odoo (obligatorio);" \
                   "          'rta'=string  entre 'si' o 'no' ;" \
                   "          'desc'=string. Descripcion de la respuesta mas detallada;" \
                   "         ;" \
                   "         ;" \
                   "          Buena suerte!.;"
        res['write_id']=int(kw.get('write_id'))
        if res['write_id']==0:
            res['accion'] = inv_Tomas(kw.get('accion'))
        res['rta'] = kw.get('rta')
        res['desc'] = kw.get('desc')
        if res['rta']==False:
            res['rta']=''
        if res['desc']==False:
            res['desc']=''

        crm=http.request.env['abatar.crm'].search([('id', '=', res['crm_id']), ('active', 'in', (True, False))], limit=1)

        if res['write_id']==0:
            accion = http.request.env['abatar.acciones.presupuesto'].search([('name', '=', res['accion'])])
            if accion:
                crm.acciones_venta_lines=[(0,0,{'fecha':Fields.Date.today(),'crm_id':res['crm_id'],'venta_accion':accion.id,'rta':res['rta'],'desc':res['desc']})]
                return "Carga Exitosa!. ID de accion=%i"%int(crm.acciones_venta_lines.search([],order='id desc',limit=1).id)
            else:
                return "ERROR, Acción incorrecta..."
        else:
            crm.acciones_venta_lines=[(1,res['write_id'],{'rta':res['rta'],'desc':res['desc']})]
            return "Carga Exitosa!"


    @http.route('/crm5', type="http", auth="public", website=True, csrf=False, methods=['GET'])
    def abatar_crmonline5(self, **kw):
        res = {}
        try:
            res['crm_id'] = int(kw.get('crm_id'))

        except:

            return "AYUDA ! :   Bienvenido al 'WRITE CRM Method' para escribir respuestas de whatsapp de Grupo-Abatar. ;" \
                   "         debes enviar los datos:;" \
                   "         'crm_id'=int ;" \
                   "         'recontactar'=str dia/mes/año ;" \
                   "         o;" \
                   "         'fecha_ej'=str dia/mes/año-hora:min:seg ;" \
                   "         o;" \
                   "         'estado_n8n'=str de estado_n8n ;" \
                   "         ;" \
                   "         ;" \
                   "          Buena suerte!.;"
        res['recontactar']=kw.get('recontactar')
        res['fecha_ej']=kw.get('fecha_ej')
        res['estado_n8n']=kw.get('estado_n8n')
        res['estado_str_n8n']=kw.get('estado_str_n8n')

        crm=http.request.env['abatar.crm'].sudo().search([('id', '=', res['crm_id']), ('active', 'in', (True, False))], limit=1)

        if res['recontactar']:
            crm.recontactar=datetime.datetime.strptime(res['recontactar'],'%d/%m/%Y').date()
            return "Carga Exitosa!. fecha recontactar=%s"%crm.recontactar.strftime('%d/%m/%Y')

        elif res['fecha_ej']:
            crm.fecha_ejecucion=datetime.datetime.strptime(res['fecha_ej'],'%d/%m/%Y-%H:%M:%S')
            return "Carga Eejecucion=%s"%crm.recontactar.strftime('%d/%m/%Y-%H:%M:%S')

        elif res['estado_n8n']:

            crm.estado_n8n=res['estado_n8n']
            if res['estado_str_n8n']:
                crm.estado_str_n8n=res['estado_str_n8n']
            if res['estado_n8n'][-2:]=="/1":
                pass
            else:
                crm.sin_atender=True
                try:
                    if res['estado_str_n8n']:

                        #group = request.env.ref('om_abatartrucks.group_abatar_user')
                        #group2 = request.env.ref('om_abatartrucks.group_abatar_manager')
                        #users=request.env['res.users'].sudo().search(['|',('groups_id', 'in', group.id),('groups_id', 'in', group2.id)])
                        #partners = users.mapped('partner_id')
                        BOTI_PARTNER_ID = 2#request.env['res.users'].sudo().browse(11).partner_id.id
                        bot = request.env['res.partner'].sudo().browse(BOTI_PARTNER_ID)
                        user_ids = [9, 2, 7, 8]

                        partners = request.env['res.users'].sudo().browse(user_ids).mapped('partner_id')

                        for partner in partners:

                            Channel = request.env['mail.channel'].sudo()

                            channel = Channel.search([
                                ('channel_type', '=', 'chat'),
                                ('public', '=', 'private'),
                                ('channel_partner_ids', 'in', [bot.id]),
                                ('channel_partner_ids', 'in', [partner.id]),
                            ], limit=1)

                            if not channel:
                                channel = Channel.create({
                                    'name': 'Boti',
                                    'channel_type': 'chat',
                                    'public': 'private',
                                    'channel_partner_ids': [(6, 0, [bot.id, partner.id])],
                                })

                            channel.message_post(
                                author_id=bot.id,
                                body=f"""
                                        <p>🤖 <b>Boti</b></p>
                                        <p>CRM {crm.pedide} respondió: {res['estado_str_n8n']}</p>
                                    """,
                                message_type='comment',
                                subtype='mail.mt_comment',
                            )

                except:
                    #group = request.env.ref('om_abatartrucks.group_abatar_user')
                    #group2 = request.env.ref('om_abatartrucks.group_abatar_manager')
                    #users = request.env['res.users'].sudo().search(
                    #    ['|', ('groups_id', 'in', group.id), ('groups_id', 'in', group2.id)])
                    #partners = users.mapped('partner_id')
                    partners = [9,2,7,3]
                    request.env['ir.logging'].sudo().create({
                        'name': 'N8N NOTIFY FAILED 22',
                        'type': 'server',
                        'level': 'INFO',
                        'dbname': request.env.cr.dbname,
                        'message': f'Message created para pedido %s,  Respondió boti %s.  Partners:%s'%(crm.pedide,res['estado_n8n'],str(partners)),
                        'path': 'n8n',
                        'func': 'notify',
                        'line': '1',
                    })
            return "Carga Exitosa!. estado_n8n=%s"%crm.estado_n8n
        else:
            return "Error, ningun dato indicado"





    @http.route('/crma2', type="http", auth="public", website=True)
    def abatar_crm_2(self, **kw):
        # return "hello World"
        # Requiere como input "nombre= & tel= & fecha_sv=(Fecha dia/mes/año) & amb=(Numero) & pers=(Numero) & origen=(Direccion) & p_origen=(Numero) & asc_origen=(No Hay, Chico, Mediano, Grande) & acarr_origen=(1=si, 0=no) & destino=(Direccion) & p_destino=(Numero) & asc_destino=(No Hay, Chico, Mediano, Grande) &  acarr_destino=(1=si, 0=no) & hay_emb_fino= (Si o No)"

        res = {}

        res['servicio'] = request.env['abatar.servicios'].search([('name', '=', 'Mudanza')]).id
        res['name'] = inv_Tomas(kw.get('name'))
        res['tel'] = inv_Tomas(kw.get('tel'))
        try:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/')+' 11:00:00'), '%d/%m/%Y %H:%M:%S')
        except:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/') + ' 11:00:00'), '%d/%m/%y %H:%M:%S')

        res['fecha_ejecucion'] = AA
        res['es_conocido'] = 'no'
        res['es_ivainc'] = True

        def una_cif(elem):
            try:
                a = int(elem)
            except:
                a = 0
                nums = ['UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS',
                        'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE']
                for i in range(len(nums)):
                    if elem.upper() == nums[i]:
                        a = i + 1
                        break
            return a

        res['mdz_amb'] = una_cif(kw.get('amb'))
        res['mdz_pers'] = una_cif(kw.get('pers'))
        try:
            ori_cya = inv_Tomas(kw.get('cya_origen')).upper()
        except:
            ori_cya = ''
        ori_loc = inv_Tomas(kw.get('loc_origen')).upper()
        ori_prov = inv_Tomas(kw.get('prov_origen')).upper()
        if ori_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            ori_prov = "BS AS"

        try:
            piso_origen = int(kw.get('p_origen'))
        except:
            piso_origen = 0

        PROVS=['BS AS', 'BUENOS AIRES', 'JUJUY', 'SALTA', 'TUCUMAN', 'FORMOSA',
               'CHACO', 'SANTIAGO DEL ESTERO', 'STGO. DEL ESTERO', 'LA RIOJA', 'SAN JUAN',
               'CATAMARCA', 'MENDOZA', 'SAN LUIS', 'CORDOBA', 'SANTA FE', 'ENTRE RIOS', 'MISIONES',
               'CORRIENTES', 'NEUQUEN', 'RIO NEGRO', 'CHUBUT', 'SANTA CRUZ', 'STA. CRUZ', 'TIERRA DEL FUEGO']
        coinc=['PROVINCIA DE BUENOS AIRES']
        for prov in PROVS:
            coinc.append(prov)
            coinc.append('PROVINCIA DE %s' % prov)




        try:
            des_cya = inv_Tomas(kw.get('cya_destino')).upper()
        except:
            des_cya = ''

        des_loc = inv_Tomas(kw.get('loc_destino')).upper() #destino[len(destino) - des_inv.find(' '):]
        des_prov = inv_Tomas(kw.get('prov_destino')).upper() #destino[len(destino) - des_inv.find(' '):]
        if des_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            des_prov = "BS AS"

        try:
            piso_destino = int(kw.get('p_destino'))
        except:
            piso_destino = 0
        id_crm_nuevo = http.request.env['abatar.crm'].search([], order='id desc', limit=1).id + 1

        res['destinos_lines2'] = [[0,0, {'destino': ori_cya, 'piso': piso_origen, 'localidad': ori_loc, 'provincia': ori_prov, 'orden_id_x': id_crm_nuevo}],
            [0, 0, {'destino': des_cya, 'piso': piso_destino, 'localidad': des_loc, 'provincia': des_prov, 'orden_id_x': id_crm_nuevo}]]

        asc_ori0 = inv_Tomas(kw.get('asc_origen'))
        asc_des0 = inv_Tomas(kw.get('asc_destino'))
        if asc_ori0 == "No hay":
            asc_ori = '1'
        elif asc_ori0 == "Chico":
            asc_ori = '2'
        elif asc_ori0 == "Mediano":
            asc_ori = '3'
        elif asc_ori0 == "Grande":
            asc_ori = '4'
        else:
            asc_ori = '1'

        if asc_des0 == "No hay":
            asc_des = '1'
        elif asc_des0 == "Chico":
            asc_des = '2'
        elif asc_des0 == "Mediano":
            asc_des = '3'
        elif asc_des0 == "Grande":
            asc_des = '4'
        else:
            asc_des = '1'

        res['mdz_ascensor_origen'] = asc_ori
        acarr_origen = kw.get('acarr_origen')
        acarr_destino = kw.get('acarr_destino')
        acarr2_origen = kw.get('acarr2_origen')
        acarr2_destino = kw.get('acarr2_destino')
        if acarr2_origen:
            acarr2_origen=inv_Tomas(acarr2_origen)
            if acarr2_origen=='Es mayor a 20m':
                res['mdz_acarreo2_ori'] = True
        if acarr2_destino:
            acarr2_destino=inv_Tomas(acarr2_destino)
            if acarr2_destino=='Es mayor a 20m':
                res['mdz_acarreo2_des'] = True

        if kw.get('esc_origen'):
            elem_esc_origen = int(kw.get('esc_origen'))
        else:
            elem_esc_origen = 0

        if kw.get('esc_destino'):
            elem_esc_destino = int(kw.get('esc_destino'))
        else:
            elem_esc_destino = 0

        if acarr_origen=="Subsuelo":
            res['mdz_acarreo_ori'] = True
        if acarr_destino=="Subsuelo":
            res['mdz_acarreo_des'] = True
        if elem_esc_origen:
            res['mdz_esc_ori'] = elem_esc_origen
        if elem_esc_destino:
            res['mdz_esc_des'] = elem_esc_destino

        res['mdz_ascensor_destino'] = asc_des
        res['mdz_ascensor_destino'] = asc_des

        res['mdz_ascensor_destino'] = asc_des
        hay_emb_fino = kw.get('hay_emb_fino')
        res['mdz_categ'] = 'B'
        if res['mdz_amb']==1:
            res['mdz_carga'] = 10
        elif res['mdz_amb']==2:
            res['mdz_carga'] = 8
        else:
            res['mdz_carga'] = 7

        if hay_emb_fino == 'Si':
            res['mdz_hay_emb_f'] = True
        else:
            res['mdz_hay_emb_f'] = False
        todo = True
        res_no = []
        for key in res.keys():
            if key == 'acarr_destino' or key == 'acarr_origen'  or key == 'mdz_hay_emb_f' or key == 'mdz_ascensor_origen' or key == 'mdz_ascensor_destino':
                pass
            elif res[key]:
                pass
            else:
                res_no.append(key)
                todo = False

        asd = ''
        datos2=''
        if todo == False:
            asd+= ' Error - Carga de Pedido Interrumpida. Faltan Datos: </br>'
            datos2 += 'errloadmdz/'
            print('Falta algun dato:', res_no)
            for exc in res_no:
                asd+= exc
                #if datos2[-1]=='?':
                #    datos2 += exc
                #else:
                #    datos2 += '&'+exc
            asd+= '  -  '


            return asd
        else:
            http.request.env['abatar.crm'].sudo().create(res)
            crm = http.request.env['abatar.crm'].search([], order='id desc', limit=1)
            PEDIDO = crm.pedide
            crm.action_crea_calculadora()

            pres = crm.cotizador

            total = round(crm.cotizador_total, 0)
            crm.write({'precio': total})
            if BUSQUEDAON == True and BUSQUEDA_MAIN==True:
                crm.resumen_busqueda = Analize_model3(crm, crm._name,
                                                        [('id', '=', crm.id), ('active', 'in', (True, False))])

            datos2 += 'loadmdz/?'
            datos2+='pedido='+str(PEDIDO)
            datos2 += '&origen=' + str(ori_cya) + ', ' + str(ori_loc) + ', ' + str(ori_prov)
            datos2 += '&destino=' + str(des_cya) + ', ' + str(des_loc) + ', ' + str(des_prov)
            datos2 += '&precio=' + str(total)
            try:

                # group = request.env.ref('om_abatartrucks.group_abatar_user')
                # group2 = request.env.ref('om_abatartrucks.group_abatar_manager')
                # users=request.env['res.users'].sudo().search(['|',('groups_id', 'in', group.id),('groups_id', 'in', group2.id)])
                # partners = users.mapped('partner_id')
                BOTI_PARTNER_ID = 2  # request.env['res.users'].sudo().browse(11).partner_id.id
                bot = request.env['res.partner'].sudo().browse(BOTI_PARTNER_ID)
                user_ids = [9, 2, 7, 8]

                partners = request.env['res.users'].sudo().browse(user_ids).mapped('partner_id')

                for partner in partners:

                    Channel = request.env['mail.channel'].sudo()

                    channel = Channel.search([
                        ('channel_type', '=', 'chat'),
                        ('public', '=', 'private'),
                        ('channel_partner_ids', 'in', [bot.id]),
                        ('channel_partner_ids', 'in', [partner.id]),
                    ], limit=1)

                    if not channel:
                        channel = Channel.create({
                            'name': 'Boti',
                            'channel_type': 'chat',
                            'public': 'private',
                            'channel_partner_ids': [(6, 0, [bot.id, partner.id])],
                        })

                    channel.message_post(
                        author_id=bot.id,
                        body=f"""
                                <p>🤖 <b>Boti</b></p>
                                <p>{res['name']} Llenó el Boti con PEDIDO {PEDIDO}</p>
                            """,
                        message_type='comment',
                        subtype='mail.mt_comment',
                    )
            except:
                pass

            web = 'https://grupoabatar.com.ar/index.php/' + datos2
            return request.redirect(web)



    @http.route('/crma3', type="http", auth="public", website=True)
    def abatar_crm_3(self, **kw):
        # return "hello World"
        # Requiere como input "nombre= & tel= & fecha_sv=(Fecha dia/mes/año) & amb=(Numero) & pers=(Numero) & origen=(Direccion) & p_origen=(Numero) & asc_origen=(No Hay, Chico, Mediano, Grande) & acarr_origen=(1=si, 0=no) & destino=(Direccion) & p_destino=(Numero) & asc_destino=(No Hay, Chico, Mediano, Grande) &  acarr_destino=(1=si, 0=no) & hay_emb_fino= (Si o No)"

        res = {}

        res['servicio'] = request.env['abatar.servicios'].search([('name', '=', 'Flete')]).id
        res['name'] = inv_Tomas(kw.get('name'))
        res['tel'] = inv_Tomas(kw.get('tel'))
        res['empresa'] = inv_Tomas(kw.get('cuit'))
        try:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/')+' 11:00:00'), '%d/%m/%Y %H:%M:%S')
        except:
            AA = datetime.datetime.strptime(str(kw.get('fecha_sv').replace('-', '/') + ' 11:00:00'), '%d/%m/%y %H:%M:%S')

        res['fecha_ejecucion'] = AA
        res['es_conocido'] = 'no'
        res['es_ivainc'] = False

        def una_cif(elem):
            try:
                a = int(elem)
            except:
                a = 0
                nums = ['UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS',
                        'SIETE', 'OCHO', 'NUEVE', 'DIEZ', 'ONCE', 'DOCE']
                for i in range(len(nums)):
                    if elem.upper() == nums[i]:
                        a = i + 1
                        break
            return a

        res['m3_flete'] = una_cif(kw.get('m3'))
        res['kgs_flete'] = una_cif(kw.get('kgs'))
        cydo=kw.get('cydo')
        cydd=kw.get('cydd')
        if cydo=="Si" and cydd=="Si":
            res['cyd_flete'] = True
            res['cyd_solo_cod'] = "Ambas"
        else:
            if cydo == "Si" or cydd == "Si":
                if cydo=="Si":
                    res['cyd_flete'] = True
                    res['cyd_solo_cod'] = "Carga"
                elif cydd=="Si":
                    res['cyd_flete'] = True
                    res['cyd_solo_cod'] = "Descarga"
            else:
                res['cyd_flete'] = False


        try:
            ori_cya = inv_Tomas(kw.get('cya_origen')).upper()
        except:
            ori_cya = ''
        ori_loc = inv_Tomas(kw.get('loc_origen')).upper()
        ori_prov = inv_Tomas(kw.get('prov_origen')).upper()
        if ori_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            ori_prov = "BS AS"

        try:
            piso_origen = int(kw.get('p_origen'))
        except:
            piso_origen = 0

        PROVS=['BS AS', 'BUENOS AIRES', 'JUJUY', 'SALTA', 'TUCUMAN', 'FORMOSA',
               'CHACO', 'SANTIAGO DEL ESTERO', 'STGO. DEL ESTERO', 'LA RIOJA', 'SAN JUAN',
               'CATAMARCA', 'MENDOZA', 'SAN LUIS', 'CORDOBA', 'SANTA FE', 'ENTRE RIOS', 'MISIONES',
               'CORRIENTES', 'NEUQUEN', 'RIO NEGRO', 'CHUBUT', 'SANTA CRUZ', 'STA. CRUZ', 'TIERRA DEL FUEGO']
        coinc=['PROVINCIA DE BUENOS AIRES']
        for prov in PROVS:
            coinc.append(prov)
            coinc.append('PROVINCIA DE %s' % prov)




        try:
            des_cya = inv_Tomas(kw.get('cya_destino')).upper()
        except:
            des_cya = ''

        des_loc = inv_Tomas(kw.get('loc_destino')).upper() #destino[len(destino) - des_inv.find(' '):]
        des_prov = inv_Tomas(kw.get('prov_destino')).upper() #destino[len(destino) - des_inv.find(' '):]
        if des_loc in ["CABA", "CUIDAD AUTONOMA DE BUENOS AIRES", "C.A.B.A."]:
            des_prov="BS AS"

        try:
            piso_destino = int(kw.get('p_destino'))
        except:
            piso_destino = 0



        if kw.get('esc_origen'):
            elem_esc_origen = int(kw.get('esc_origen'))
        else:
            elem_esc_origen = 0

        if kw.get('esc_destino'):
            elem_esc_destino = int(kw.get('esc_destino'))
        else:
            elem_esc_destino = 0




        id_crm_nuevo = http.request.env['abatar.crm'].search([], order='id desc', limit=1).id + 1

        res['destinos_lines2'] = [[0,0, {'destino': ori_cya, 'piso': piso_origen, 'localidad': ori_loc, 'provincia': ori_prov, 'm3_escalera_c': elem_esc_origen, 'orden_id_x': id_crm_nuevo}],
            [0, 0, {'destino': des_cya, 'piso': piso_destino, 'localidad': des_loc, 'provincia': des_prov, 'm3_escalera_d': elem_esc_destino,  'orden_id_x': id_crm_nuevo}]]



        no_emb_grueso = kw.get('no_emb_grueso')



        if no_emb_grueso == 'Si':
            res['cyd_emb_grueso'] = False
        else:
            res['cyd_emb_grueso'] = True

        todo = True
        res_no = []
        for key in res.keys():
            if key == 'cyd_flete' or key == 'cyd_emb_grueso' or key == 'es_ivainc':
                pass
            elif res[key]:
                pass
            else:
                res_no.append(key)
                todo = False

        asd = ''
        datos2=''
        if todo == False:
            asd+= ' Error - Carga de Pedido Interrumpida. Faltan Datos: </br>'
            datos2 += 'errloadmdz/'
            print('Falta algun dato:', res_no)
            for exc in res_no:
                asd+= exc
                #if datos2[-1]=='?':
                #    datos2 += exc
                #else:
                #    datos2 += '&'+exc
            asd+= '  -  '


            return asd
        else:
            http.request.env['abatar.crm'].create(res)
            crm = http.request.env['abatar.crm'].search([], order='id desc', limit=1)
            PEDIDO = crm.pedide
            crm.action_crea_calculadora()

            pres = crm.cotizador

            total = round(crm.cotizador_total, 0)
            crm.write({'precio': total})
            if BUSQUEDAON == True and BUSQUEDA_MAIN==True:
                crm.resumen_busqueda = Analize_model3(crm, crm._name,
                                                        [('id', '=', crm.id), ('active', 'in', (True, False))])

            datos2 += 'loadmdz/?'
            datos2+='pedido='+str(PEDIDO)
            datos2 += '&origen=' + str(ori_cya) + ', ' + str(ori_loc) + ', ' + str(ori_prov)
            datos2 += '&destino=' + str(des_cya) + ', ' + str(des_loc) + ', ' + str(des_prov)
            datos2 += '&precio=' + str(total)


            web = 'https://grupoabatar.com.ar/index.php/' + datos2
            return request.redirect(web)




    @http.route('/promos', type="http", auth="public", website=True)
    def abatar_promos(self, **kw):

        res = {}

        res['servicio'] = request.env['abatar.servicios'].search([('name', '=', 'Flete')]).id
        res['name'] = inv_Tomas(kw.get('nombre'))
        res['tel'] = inv_Tomas(kw.get('tel'))
        obs=kw.get('obs')
        if obs:
            res['desc1'] = obs
        else:
            res['desc1'] = ''


        AA = datetime.datetime.strptime(str(kw.get('fecha_sv')+' 11:00:00'), '%d/%m/%Y %H:%M:%S')
        res['fecha_ejecucion'] = AA
        res['es_conocido'] = 'no'

        UD0=int(kw.get('m3_flete'))
        M3=0
        l_ud=[5, 10, 15, 20, 25, 35, 45]
        l2_ud=['A', 'B','C','D','E','F','FF']
        UD=l2_ud[UD0-1]
        M3=l_ud[UD0-1]


        res['m3_flete'] = M3

        res['key_usuario'] = kw.get('key')
        usuariokey=self.env['abatar.keyusuario'].search([('keynum','=',res['key_usuario'])])
        convenio=usuariokey.fdp
        if convenio == 'efectivo':
            res['convenio'] = 'contado'
            res['mas_iva']=False
        elif convenio == 'transferencia':
            res['convenio'] = 'contado'
            res['mas_iva']=True
        elif convenio=='cta cte':
            res['convenio'] = 'cc'
            res['mas_iva']=True

        cyd_flete_str= kw.get('cyd_flete')
        if cyd_flete_str=='Si':
            res['cyd_flete'] = True
        else:
            res['cyd_flete'] = False


        cyd_autoelev_str= kw.get('cyd_autoelev')
        if cyd_autoelev_str=='Si':
            res['cyd_autoelev'] = True
        else:
            res['cyd_autoelev'] = False


        cyd_emb_grueso_str= kw.get('cyd_emb_grueso')
        if cyd_emb_grueso_str=='Si':
            res['cyd_emb_grueso'] = True
        else:
            res['cyd_emb_grueso'] = False


        cyd_minop_str= kw.get('cyd_minop')
        if cyd_minop_str=='Si':
            res['cyd_minop'] = True
        else:
            res['cyd_minop'] = False

        cyd_solo_cod= kw.get('cyd_final')
        if cyd_solo_cod=='Ambas' or not cyd_solo_cod:
            pass
        elif cyd_solo_cod=='Origen':
            res['cyd_solo_cod'] = 'Carga'
        elif cyd_solo_cod=='Destino':
            res['cyd_solo_cod'] = 'Descarga'



        PROVS = ['BS AS', 'BUENOS AIRES', 'JUJUY', 'SALTA', 'TUCUMAN', 'FORMOSA',
                 'CHACO', 'SANTIAGO DEL ESTERO', 'STGO. DEL ESTERO', 'LA RIOJA', 'SAN JUAN',
                 'CATAMARCA', 'MENDOZA', 'SAN LUIS', 'CORDOBA', 'SANTA FE', 'ENTRE RIOS', 'MISIONES',
                 'CORRIENTES', 'NEUQUEN', 'RIO NEGRO', 'CHUBUT', 'SANTA CRUZ', 'STA. CRUZ', 'TIERRA DEL FUEGO']
        coinc = ['PROVINCIA DE BUENOS AIRES']
        for prov in PROVS:
            coinc.append(prov)
            coinc.append('PROVINCIA DE %s' % prov)

        piso_origen = 0  # int(kw.get('p_origen'))
        ori_elem_escalera_c = 0  # int(kw.get('bajan_origen_esc'))
        ori_elem_escalera_d = 0  # int(kw.get('suben_origen_esc'))
        piso_destino = 0#int(kw.get('p_destino'))
        des_elem_escalera_c = 0#int(kw.get('bajan_destino_esc'))
        des_elem_escalera_d = 0#int(kw.get('suben_destino_esc'))
        id_crm_nuevo = http.request.env['abatar.crm'].search([], order='id desc', limit=1).id + 1

        if CUENTA_API_KEY==False:
            ori_cya = inv_Tomas(kw.get('cyaorigen'))
            ori_cya2 = kw.get('cyaorigen')
            ori_loc = inv_Tomas(kw.get('localidadorigen'))
            ori_loc2 = kw.get('localidadorigen')
            ori_prov = inv_Tomas(kw.get('provinciaorigen'))
            ori_prov2 = kw.get('provinciaorigen')

            des_cya = inv_Tomas(kw.get('cyadestino'))
            des_cya2 = kw.get('cyadestino')
            des_loc = inv_Tomas(kw.get('localidaddestino'))
            des_loc2 = kw.get('localidaddestino')
            des_prov = inv_Tomas(kw.get('provinciadestino'))
            des_prov2 = kw.get('provinciadestino')

            res['destinos_lines2'] = [[0,0, {'destino': ori_cya, 'piso': piso_origen, 'localidad': ori_loc,
                                             'provincia': ori_prov,'m3_escalera_c':ori_elem_escalera_c,'m3_escalera_d':ori_elem_escalera_d,
                                             'orden_id_x': id_crm_nuevo}],
                [0, 0, {'destino': des_cya, 'piso': piso_destino, 'localidad': des_loc, 'provincia': des_prov,
                        'm3_escalera_c':des_elem_escalera_c,'m3_escalera_d':des_elem_escalera_d,'orden_id_x': id_crm_nuevo}]]

            origen = ori_cya
            origen2 = ori_cya2
            if piso_origen:
                origen2 += ', PISO ' + str(piso_origen)
            if ori_loc:
                origen += ', ' + ori_loc
                origen2 += ', ' + ori_loc2
            if ori_prov:
                origen += ', ' + ori_prov
                origen2 += ', ' + ori_prov2

            destino = des_cya
            destino2 = des_cya2
            if piso_destino:
                destino2 += ', PISO ' + str(piso_destino)
            if des_loc:
                destino += ', ' + des_loc
                destino2 += ', ' + des_loc2
            if des_prov:
                destino += ', ' + des_prov
                destino2 += ', ' + des_prov2

        else:
            ori_cya = inv_Tomas(kw.get('direccion_org'))
            ori_cya2 = kw.get('direccion_org')

            des_cya = inv_Tomas(kw.get('direccion_dest'))
            des_cya2 = kw.get('direccion_dest')

            res['destinos_lines2'] = [[0, 0, {'destino': ori_cya[:ori_cya.find(',')], 'piso': piso_origen, 'localidad': ori_cya[ori_cya.find(',')+1:ori_cya.find(',', ori_cya.find(',')+1)],
                                              'provincia': ori_cya[ori_cya.find(',', ori_cya.find(',')+1)+1:], 'forc_direc':ori_cya, 'm3_escalera_c': ori_elem_escalera_c,
                                              'm3_escalera_d': ori_elem_escalera_d,
                                              'orden_id_x': id_crm_nuevo}],
                                      [0, 0, {'destino': des_cya[:des_cya.find(',')], 'piso': piso_destino, 'localidad': des_cya[des_cya.find(',')+1:des_cya.find(',', des_cya.find(',')+1)],
                                              'provincia': des_cya[des_cya.find(',', des_cya.find(',')+1)+1:], 'forc_direc':des_cya,
                                              'm3_escalera_c': des_elem_escalera_c,
                                              'm3_escalera_d': des_elem_escalera_d, 'orden_id_x': id_crm_nuevo}]]

            origen = ori_cya
            origen2 = ori_cya
            origen = ori_cya
            origen2 = ori_cya
            if piso_origen:
                origen2 = origen2[:ori_cya.find(',')] +', PISO ' + str(piso_origen)+origen2[ori_cya.find(','):]


            destino = des_cya
            destino2 = des_cya
            if piso_destino:
                destino2 = destino2[:ori_cya.find(',')] +', PISO ' + str(piso_destino)+destino2[ori_cya.find(','):]


        time_rec, kms_rec, des=calcula_distancia(origen, destino)
        time_rec00, kms_rec00, des=calcula_distancia('CABA', origen)
        time_rec01, kms_rec01, des=calcula_distancia('CABA', destino)
        res['desc1']+='datos rec: %s' % des
        todo = True
        res_no = []
        for key in res.keys():
            if res[key]:
                pass
            elif key in ('cyd_flete', 'cyd_autoelev', 'cyd_emb_grueso', 'cyd_minop', 'cyd_minop'):
                pass
            else:
                res_no.append(key)
                todo = False

        asd = ''
        if todo == False:
            asd+= ' Error - Carga de Pedido Interrumpida. Faltan Datos: </br> </br>'
            print('Falta algun dato:', res_no)
            for exc in res_no:
                asd+= exc
            asd+= '  -  '
            for key in kw.keys():
                asd += '</br>'
                asd += key + ':' + kw[key] + ' </br>'
            return ('<h2>ERROR Carga de Pedidos: </br> %s </h2>' % asd)

        else:
            resul= http.request.env['abatar.crm'].create(res)
            resul.action_crea_calculadora2()
            if kms_rec00>75 and kms_rec01>75:
                #web='https://grupoabatar.com.ar/index.php/loadmdz'+datos2+'&#primero'
                return ('<h2> ERROR </br> </br>Ambas direcciones Fuera de Radio de Acción 75kms. </br> Realize su consulta por vía Telefónica, Email o WhatsApp </h2>')
            elif kms_rec00>75:
                #web='https://grupoabatar.com.ar/index.php/loadmdz'+datos2+'&#primero'
                return ('<h2> ERROR </br> </br>Direccion de Origen Fuera de Radio de Acción 75kms. </br> Realize su consulta por vía Telefónica, Email o WhatsApp </h2>')
            elif kms_rec01>75:
                #web='https://grupoabatar.com.ar/index.php/loadmdz'+datos2+'&#primero'
                return ('<h2> ERROR </br> </br>Direccion de Destino Fuera de Radio de Acción 75kms. </br> Realize su consulta por vía Telefónica, Email o WhatsApp </h2>')



            if res['key_usuario']:
                keyid= http.request.env['abatar.keyusuario'].search([('keynum', '=', res['key_usuario'])], limit=1).fdp
                dto_Base=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_DTO_BASE_PORMIL')],limit=1).flotante
                dto_Transf=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_DTO_TRANSF_PORMIL')],limit=1).flotante
                dto_CtaCte=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_DTO_CTACTE_PORMIL')],limit=1).flotante
                dto_Efect=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_DTO_EFECT_PORMIL')],limit=1).flotante
                dto_Base=dto_Base/1000
                dto_Transf=dto_Transf/1000
                dto_CtaCte=dto_CtaCte/1000
                dto_Efect=dto_Efect/1000

                ivainc_Transf=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_IVA-INC_TRANSF')],limit=1).booleano
                ivainc_CtaCte=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_IVA-INC_CTACTE')],limit=1).booleano
                ivainc_Efect=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_IVA-INC_EFECT')],limit=1).booleano

                categ_Transf=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_TRANSF')],limit=1).char
                categ_CtaCte=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_CTACTE')],limit=1).char
                categ_Efect=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_EFECT')],limit=1).char

                masiva_Transf=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_TRANSF')],limit=1).booleano
                masiva_CtaCte=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_CTACTE')],limit=1).booleano
                masiva_Efect=self.env['abatar.constantes'].search([('name','=','FLETE_BOTI_COTIZVARIOS_EFECT')],limit=1).booleano
                if keyid=='cta cte':
                    resul.cotizador.es_ivainc=ivainc_CtaCte
                    resul.cotizador.hay_categ=categ_CtaCte
                    Dto=dto_CtaCte*dto_Base
                    Keyid = 'Cuenta Corriente'
                    hayiva=masiva_CtaCte
                elif keyid=='transferencia':
                    resul.cotizador.es_ivainc=ivainc_Transf
                    resul.cotizador.hay_categ=categ_Transf
                    Dto=dto_Transf*dto_Base
                    Keyid = 'Transferencia'
                    hayiva=masiva_Transf
                elif keyid=='efectivo':
                    resul.cotizador.es_ivainc=ivainc_Efect
                    resul.cotizador.hay_categ=categ_Efect
                    Dto=dto_Efect*dto_Base
                    Keyid = 'Efectivo'
                    hayiva=masiva_Efect

            n_seq=http.request.env['abatar.crm'].search([], order='id desc', limit=1).pedide
            pres=resul.cotizador
            lin_ud2 = pres.linea_personal
            quite=[]
            for udie in lin_ud2:
                if udie.producto:
                    if udie.producto.letra:
                        if udie.producto.letra==UD:
                            kms_sv=int(udie.kms)
                            hs_sv=redond(udie.horas)
                    else:
                        quite.append(udie)
            if quite:
                for i in range(len(quite)):
                    quite[len(quite)-1-i].unlink()

            total=round(10*int(pres.total*Dto/10), 0)
            resul.write({'precio':total})
            if hayiva==True:
                resul.write({'mas_iva':True})
                total=round(total*1.21, 0)
            if BUSQUEDAON==True and BUSQUEDA_MAIN==True:
                resul.resumen_busqueda=Analize_model3(resul, resul._name, [('id', '=', resul.id), ('active', 'in', (True, False))])

            #lin_ud = lin_ud2.search([('producto.letra', '=', UD)], limit=1)
            #tar_ud=lin_ud.precio/1.21
            tiempo_rec = redond(time_rec / 3600)
            tar_gral=http.request.env['abatar.tarifas'].search([('es_general','=', True)], limit=1).productos_lines
            min = tar_gral.search([('productos_id.letra', '=', UD)],limit=1).tarifas_minimo
            tar_ud = int(tar_gral.search([('productos_id.letra', '=', UD)],limit=1).tarifas_precio*Dto)
            hs_sv=max([hs_sv, min-1])#min-1#

            prod_op = http.request.env['abatar.productos'].search([('name', '=', 'Operario')], limit=1).id
            tar_op=int(tar_gral.search([('productos_id', '=', prod_op)],limit=1).tarifas_precio*Dto)
            #advertencia=''
            #if hs_sv!=tiempo_rec:
            #    advertencia='La pauta cotizada en %.1f hs difiere a lo expuesto en el mapa mostrado por %.1f' % (hs_sv, tiempo_rec)
            #AYD=pres.AYD
            #kms_sv=0
            #hs_sv=0
            #for res in pres.linea_personal:
            #    if res.producto.tipo.name=='unidad':
            #        if res.kms:
            #            kms_sv=res.kms
            #        hs_sv=max([hs_sv,res.horas-1-AYD])



            datos=''
            datos+='M3: %s </br>' % str(M3)
            datos+='Origen: %s  </br>' % origen2
            datos+='Destino: %s  </br> </br>' % destino2
            datos+='Incluye:  </br>'
            datos+='Tipo de Unidad: %s  </br>' % UD


            datos2='?'
            datos2+='pedido=%s' % str(n_seq)
            datos2+='&origen=%s' % Tomas(origen2)
            datos2+='&destino=%s' % Tomas(destino2)
            datos2+='&keyid=%s' % Tomas(Keyid)
            datos2+='&tipoud=%s' % UD
            datos2+='&tiempo_rec=%s' % str(tiempo_rec)
            datos2+='&kms_rec=%s' % str(int(kms_rec))
            datos2+='&excedentes=%s' % numtostr(tar_ud)
            #datos2+='&advertencia=%s' % advertencia
            if len(str(int(total)))>6:
                pre=str(int(total))
                total_str=pre[:-6]+'.'+pre[-6:-3]+'.'+pre[-3:]#+','+dec[2:]
            elif len(str(int(total)))>3:
                pre=str(int(total))
                total_str=pre[:-3]+'.'+pre[-3:]#+','+dec[2:]
            else:
                pre=str(int(total))
                total_str=pre#+','+dec[2:]
                
            if kms_sv:
                datos+='Kilometros Provincia: %s  </br>' % str(kms_sv)
                datos2+='&kms=%s' % str(int(kms_sv/2))
            else:
                datos2+='&kms=%s' % '0'

            datos+='Horas de Servicio: %s  </br>' % str(hs_sv)

            datos2+='&precio=%s' % total_str
            datos2+='&hs=%s' % str(hs_sv)
            datos2 += '&tarop=%s' % numtostr(tar_op)

            datos+='IVA INCLUYE  </br>'
            #datos2+='&IVA=Si'

            web='https://grupoabatar.com.ar/index.php/loadmdz'+datos2+'&#primero'

            #('<h2> Presupuesto Automático ABATAR-TRUCKS - PEDIDO N° %s </h2> </br> %s </br> <h2>  Total: $ %s </h2>' % (n_seq, datos, str(total)))
            return request.redirect(web)


        #return request.redirect('http://grupoabatar.com.ar/')


    @http.route('/consulta', type="http", auth="public", website=True)
    def abatar_consulta(self, **kw):
        # return "hello World"
        # Requiere como input "nombre= & tel= & fecha_sv=(Fecha dia-mes-año) & m3_flete=(Numero) & cyd_flete="Si/No" &
        #  & cyd_autoelev="Si/No"  & cyd_emb_grueso="Si/No" & cyd_minop="Si/No"
        #  & cya_origen=(Calle y altura) & p_origen=(Numero)
        #  & loc_origen=(localidad)  & prov_origen=(localidad)  & bajan_origen_esc=Numero & suben_origen_esc=Numero
        #  & cya_destino=(Calle y altura) & p_destino=(Numero)
        #  & loc_destino=(localidad)  & prov_destino=(localidad)  & bajan_destino_esc=Numero & suben_destino_esc=Numero
        key_usuario=inv_Tomas(kw.get('clave'))
        crm=inv_Tomas(kw.get('pedido'))
        if crm[:2]=='CR':
            pass
        else:
            crm='CR'+crm


        resul = request.env['abatar.crm'].search([('name_seq', '=', crm),('key_usuario', '=', key_usuario)], limit=1)
        if resul:
            nombre=Tomas(resul.name)
            tel=Tomas(resul.tel)
            M3=resul.m3_flete
            UD=resul.ud_pres
            OP=resul.op_pres
            HS=resul.hs_pres
            h=0
            for rec in resul.destinos_lines2:
                if h==0:
                    origen=Tomas(rec.name_gral)
                else:
                    destino=Tomas(rec.name_gral)
                h+=1

            obs=resul.desc1
            fecha=resul.fecha_ejecucion


            cyd_flete_str= resul.cyd_flete
            if cyd_flete_str==True:
                time_cyd = [0.3,0.5,1, 1.5, 2, 2, 2.5]
            else:
                time_cyd = [0.3,0.5,1, 1.5, 2, 2, 2.5]


            cyd_autoelev_str= resul.cyd_autoelev
            if cyd_autoelev_str==True:
                time_cyd = [0.5, 0.5, 0.5, 0.75, 1, 1.5, 2]
            else:
                pass


            cyd_emb_grueso_str= resul.cyd_emb_grueso
            if cyd_emb_grueso_str==True:
                time_cyd=[0.75, 1, 1.25, 2.25, 3, 3, 4]
            else:
                pass

            m3l=[5, 10, 15, 20, 25, 35, 45]
            udi=0
            tcyd=0
            for m in range(len(m3l)):
                if M3==m3l[m]:
                  tcyd=time_cyd[m]


            cyd_solo_cod= resul.cyd_solo_cod
            total=resul.precio


            datos2='?'
            datos2+='nombre=%s' % nombre
            datos2+='&tel=%s' % tel
            datos2+='&pedido=%s' % str(crm)
            #datos2+='M3=%s' % str(M3)
            datos2+='&origen=%s' % origen
            datos2+='&destino=%s' % destino
            datos2+='&tipoud=%s' % UD
            datos2+='&tiempocyd=%s' % tcyd
            if obs:
                datos2 += '&obs=%s' % obs
            if len(str(int(total)))>3:
                pre=str(int(total))
                total_str=pre[:-3]+'.'+pre[-3:]
            else:
                pre=str(int(total))
                total_str=pre

            datos2+='&precio=%s' % total_str

            datos2+='&operarios=%s' % str(OP)
            if OP==0:
                datos2 += '&cydod=%s' % 'Ninguna'
            else:
                datos2+='&cydod=%s' % cyd_solo_cod



            web='https://grupoabatar.com.ar/index.php/consul'+datos2+'&#primero'

            return request.redirect(web)
        else:

            web = 'https://grupoabatar.com.ar/index.php/errconsul'

            return request.redirect(web)

    @http.route('/functions', type="http", auth="public", website=True)
    def abatar_functions(self, **kw):
        """
        Endpoint multipropósito para consultas públicas.
        Parámetros esperados:
            func = tipo de función ('lect_dolar', 'lect_cliente_nuevo', etc.)
        """

        func = inv_Tomas(kw.get('func'))

        # === LECTURA DE DÓLAR ===
        if func == 'lect_dolar':
            try:
                resul = request.env['abatar.dolar'].sudo().search([], order='fecha desc', limit=1)
                if resul:
                    fecha = resul.fecha.strftime('%d/%m/%Y')
                    return 'fecha=%s' % fecha
            except:
                pass

            return request.redirect('https://grupoabatar.com.ar/index.php/errconsul')

        # === VERIFICACIÓN DE CLIENTE NUEVO ===
        elif func == 'lect_cliente_nuevo':
            tel = inv_Tomas(kw.get('tel', '')).replace("-", "").replace(" ", "")
            datos2 = 'escliente=no'

            try:
                tel = tel[-8:]  # usa los últimos 8 dígitos
                resul = request.env['abatar.crm'].sudo().search([
                    ('tel', 'ilike', tel),
                    ('active', 'in', (True, False))
                ], order='fecha_inicial desc', limit=1)

                if resul:
                    datos2 = 'escliente=si'
            except:
                pass
            #except Exception as e:
            #    _logger.warning("Error en lect_cliente_nuevo: %s", e)

            return datos2

        # === DEFAULT: FUNCIÓN DESCONOCIDA ===
        else:
            return request.redirect('https://grupoabatar.com.ar/index.php/errconsul')

    @http.route('/cargaprov', type="http", auth="public", website=True)
    def abatar_cargaprov(self, **kw):

        vals2 = {}
        vals3 = {}
        vals4 = {}
        key_usuario = '76543210'  # inv_Tomas(kw.get('clave'))
        if key_usuario == '76543210':
            vals2['name'] = inv_Tomas(kw.get('nombre'))
            vals2['tel'] = kw.get('tel')
            if kw.get('dni'):
                vals2['dni'] = kw.get('dni')
            else:
                vals2['dni'] = ''
            if kw.get('direc'):
                vals2['zona'] = inv_Tomas(kw.get('direc'))
            else:
                vals2['zona'] = ''
            vals2['zona_map'] = kw.get('zona_map')

            tipo = kw.get('tipo')
            if tipo.upper() == "UD":
                vals3['tipo'] = request.env['abatar.tipo'].sudo().search([('name', '=', 'unidad')]).id
                tipo_ud = kw.get('tipo_ud')
                prod0 = 'Unidad ' + '\"' + tipo_ud + '\"'
                prod = request.env['abatar.productos'].sudo().search([('name', '=', prod0)])
                prod_id = prod.id
                vals3['subtipo'] = prod_id

                prod_pcgan = prod.tipo.pc_gan
                tar_gen = request.env['abatar.tarifas'].sudo().search([('es_general', '=', True)], limit=1)
                prod_precio = tar_gen.productos_lines.sudo().search([('productos_id', '=', prod_id)],
                                                                    limit=1).tarifas_precio * (1 - prod_pcgan / 100)
                vals3['tarifa'] = prod_precio
                vals3['minimo'] = tar_gen.productos_lines.sudo().search([('productos_id', '=', prod_id)],
                                                                        limit=1).tarifas_minimo
                if kw.get('modelo'):
                    vals3['modelo'] = kw.get('modelo')
                if kw.get('patente'):
                    vals3['patente'] = inv_Tomas(kw.get('patente'))
                if kw.get('caja'):
                    vals3['caja'] = kw.get('caja')
                if kw.get('largo'):
                    vals3['largo'] = kw.get('largo')
                if kw.get('ancho'):
                    vals3['ancho'] = kw.get('ancho')
                if kw.get('alto'):
                    vals3['alto'] = kw.get('alto')
                if kw.get('kgs'):
                    vals3['kgs'] = kw.get('kgs')
                if kw.get('c_pala'):
                    vals3['c_pala'] = sinobool(kw.get('c_pala'))
                if kw.get('c_rastreo'):
                    vals3['c_rastreo'] = sinobool(kw.get('c_rastreo'))
                if kw.get('c_hidrogrua'):
                    vals3['c_hidrogrua'] = sinobool(kw.get('c_hidrogrua'))

            elif tipo.upper() == "OP":
                vals3['tipo'] = request.env['abatar.tipo'].sudo().search([('name', '=', 'operario')]).id
                tipo_op = 'operario'

                prod0 = 'Operario'
                prod = request.env['abatar.productos'].sudo().search([('name', '=', prod0)])
                prod_id = prod.id
                vals3['subtipo'] = prod_id

                prod_pcgan = prod.tipo.pc_gan
                tar_gen = request.env['abatar.tarifas'].sudo().search([('es_general', '=', True)], limit=1)
                prod_precio = tar_gen.productos_lines.sudo().search([('productos_id', '=', prod_id)],
                                                                    limit=1).tarifas_precio * (1 - prod_pcgan / 100)
                vals3['tarifa'] = prod_precio
                vals3['minimo'] = tar_gen.productos_lines.sudo().search([('productos_id', '=', prod_id)],
                                                                        limit=1).tarifas_minimo

            vals4['name'] = inv_Tomas(kw.get('nombre'))
            vals4['tel'] = kw.get('tel')
            if kw.get('dni'):
                vals4['dni'] = kw.get('dni')
            if kw.get('fecha_nac'):
                vals4['fecha_nac'] = inv_Tomas(kw.get('fecha_nac'))

            vals2['desc'] = 'Proveedor cargado por WEB'
            if request.env['abatar.proveedores'].sudo().search(
                    [('name', '=', vals2['name']), ('tel', '=', vals2['tel']), ('dni', '=', vals2['dni'])]):
                resu = request.env['abatar.proveedores'].sudo().search(
                    [('name', '=', vals2['name']), ('tel', '=', vals2['tel']), ('dni', '=', vals2['dni'])])
            else:
                resu = request.env['abatar.proveedores'].sudo().create(vals2)

            # Las líneas también se escriben con permisos elevados
            resu.sudo().write({'productos_lines': [(0, 0, vals3)]})
            resu.sudo().write({'personal_lines': [(0, 0, vals4)]})

            datos = ' <strong>CARGA AUTOMATICA PROVEEDOR:</strong> <br/><br/>'
            datos += ' PROVEEDOR: <br/>'
            for key in vals2.keys():
                datos += key + ' : ' + str(vals2[key]) + ' <br/>'
            datos += ' PRODUCTO: <br/>'
            for key in vals3.keys():
                datos += key + ' : ' + str(vals3[key]) + ' <br/>'
            datos += ' PERSONAL: <br/>'
            for key in vals4.keys():
                datos += key + ' : ' + str(vals4[key]) + ' <br/>'

            return datos
        else:
            web = 'https://grupoabatar.com.ar/index.php/errconsul'
            return request.redirect(web)

    @http.route('/cargadolar', type="http", auth="public", website=True)
    def abatar_cargadolar(self, **kw):

        vals2={}
        vals2['fecha']=inv_Tomas(kw.get('fecha')).replace('-','/')
        vals2['pesos']=kw.get('monto')
        resu = request.env['abatar.dolar'].sudo().create(vals2)

        datos=' <strong>CARGA AUTOMATICA FECHA REALIZADA</strong> <br/><br/>'

        return datos

    @http.route('/cargatrend', type="http", auth="public", website=True)
    def abatar_cargatrend(self, **kw):

        vals2={}
        vals2['palabra']=kw.get('palabra')
        vals2['fecha']=inv_Tomas(kw.get('fecha')).replace('-','/')
        vals2['valor']=kw.get('valor')
        resu = request.env['abatar.trends'].sudo().search([('palabra','=',vals2['palabra'])],limit=1)
        resu2=request.env['abatar.trends.lines'].sudo().create({'fecha':datetime.datetime.strptime(vals2['fecha'], "%d/%m/%Y").date(),'valor':float(vals2['valor']),'trends_id':resu.id})

        if resu2:
            datos=' <strong>CARGA AUTOMATICA TREND REALIZADA</strong> <br/><br/>PALABRA:%s<br/>FECHA:%s<br/>VALOR:%.2f'%(resu.palabra,vals2['fecha'],resu2.valor)
        else:
            datos=' <strong>CARGA AUTOMATICA TREND FALLIDA...</strong> <br/><br/>'

        return datos

    def _calcula_tarifa(self, unidad_nombre, kms, tiempo_viaje, operarios):

        busca = request.env['abatar.tarifas'].sudo().search(
            [('es_general', '=', True)])

        precio_final = 0
        precio_hora = 0
        precio_hora_op = 0
        cant_op = 0
        precio_kms = 0
        minimo = 0
        tiempo_carga = 0

        if busca:
            for ei in busca.productos_lines:
                if ei.productos_id.name == unidad_nombre:
                    minimo = ei.productos_id.minimo
                    tiempo_carga = ei.productos_id.tiempo_carga
                    precio_hora = ei.tarifas_precio
                    if operarios == True:
                        cant_op = ei.productos_id.cant_op_carga

            for ed in busca.productos_lines:
                if ed.productos_id.name == 'Operarios':
                    precio_hora_op = ed.tarifas_precio

            for ec in busca.kms_lines:
                if ec.productos_id.name == unidad_nombre:
                    precio_kms = ec.tarifas_precio

            tiempo_final = (tiempo_carga*2) + (tiempo_viaje*2)

            if tiempo_final < minimo-0.5:
                tiempo_final = minimo
            else:
                tiempo_final += 1

            precio = (precio_hora * tiempo_final) + (precio_kms * kms) + (precio_hora_op * tiempo_final * cant_op)

        return precio

    def _es_capital(self, direccion):

        primer = 0
        cadena_new = ""
        for ie in direccion[::-1]:
            if primer == 1:
                cadena_new = ie + cadena_new
            if ie == ",":
                primer += 1

        return cadena_new


    def _calcula_distancia(self, direccion1, direccion2):

        api_key = '&units=imperial&key=AIzaSyAvffBICS3JwKVK7xSTj_5sXDQkd5iU6wA'

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + direccion1 + "&destinations=" + direccion2 + api_key

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        tiempo_value = response.json()["rows"][0]["elements"][0]["duration"]["value"]
        distance_value = response.json()["rows"][0]["elements"][0]["distance"]["value"]

        kms = distance_value / 1000

        return tiempo_value, kms


    def _action_crea_crm(self,id):

        resultado = request.env['abatar.chat.auto'].sudo().search([('channel_ids', '=', id)]
                                                           )
        for j in resultado:
            vals2 = {
                'fecha_pedido': datetime.datetime.now(),
                'es_conocido': 'no',
                'name': j.nombre,
                'tel': j.telefono,
            }

            resu = self.env['abatar.crm'].create(vals2)

            vals1 = {
                'destino': j.origen,
                'destino_tipo': 'origen'
            }
            resu.write({'destinos_lines2': [(0, 0, vals1)]})

            vals1 = {
                'destino': j.destino,
                'destino_tipo': 'destino'
            }
            resu.write({'destinos_lines2': [(0, 0, vals1)]})