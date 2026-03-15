from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import time
import calendar
from odoo import api, fields, models, tools, _, modules
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import base64
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, enviar_mensajegral, enviar_mensaje, BUSQUEDAON,POLY_ZONAS

import logging
#####################################################DECLARATION FORMMDZ FUNCTION

import numpy as np
#import os
#os.environ['http_proxy']=''
import requests

COC_PROG=False
IMPRIME_CALCULA_DIST=False
MJSLOG=False
CAMPOS_CAMBIO=['m3_flete','kgs_flete','fdp_flete','cyd_flete','cyd_autoelev','cyd_minop','cyd_forcop','cyd_solo_cod','cyd_emb_grueso','precio','orientacion','mas_iva','codigo','texto_ppal_presup','exced_presup','nota_al_pie_presup','mdz_amb','mdz_pers','mdz_carga','mdz_op_cyd','mdz_hay_mg','mdz_hay_mf','mdz_hay_emb_g','mdz_hay_emb_f','mdz_hay_vacio','mdz_monto_cobro_vacio','mdz_monto_costo_vacio','mdz_esc_ori','mdz_esc_des','mdz_acarreo_ori','mdz_acarreo2_ori','mdz_acarreo_des','mdz_acarreo2_des','mdz_roperitos','mdz_roperitos_cant','mdz_desembalaje','mdz_ascensor_origen','mdz_ascensor_destino','mdz_categ','convenio','fecha_inicial','fecha_ejecucion','fecha_confirmacion','recontactar','desc1','servicio_name','estado','estado_presupuesto','destinos_resumen','active','confirmado_para_resumen','dolar_uso','estado_n8n']

def numtostr(val):
    if val>=1000000:
        a=str(int(val / 1000000)) + '.'
        val2=val-int(val / 1000000)*1000000
        a+= '%03i.%03i' % (int(val2 / 1000), int(val2) - (int(val2 / 1000) * 1000))
        if val - int(val)>0:
            a+= ',' + str(round(val - int(val), 2))[2:]
    else:
        a = '%i.%03i' % (int(val / 1000), int(val) - (int(val / 1000) * 1000))
        if val - int(val)>0:
            a+= ',' + str(round(val - int(val), 2))[2:]
    return a
def norm(x):
    norm=0
    for A in x:
        norm+=A**2
    norm=np.sqrt(norm)
    return norm

def comprostrclean(string):
    if string and type(string)==type('hi'):
        if string[0] == ' ':
            string = string[1:]
        if string[-1] == ' ':
            string = string[:-1]
        if string.find('  ') > -1:
            string = string[:string.find('  ')]+string[string.find('  ')+1:]
    return string

def redond(x):
    if x - int(x) >= 0.25:
        if x - int(x) >= 0.75:
            return int(x) + 1
        else:
            return int(x) + 0.5
    else:
        return int(x)

def CotizMDZ(CATEG, amb, pers, hs_recorr, kms_ori, kms_recorr, piso_ori, piso_dest, asc_ori=0, asc_dest=0,
             nivel_carga0=7, hay_mat_fino=0, hay_mat_grueso=1, hay_emb_fino=0, hay_emb_grueso=1, hay_prov=0, hay_int=0):
    print('hay int?', hay_int)
    DOBLE = 1
    if amb * nivel_carga0 > 45 and amb * nivel_carga0 <= 70:

        nivel_carga = nivel_carga0 / 2
        DOBLE = 2
        print("DOBLE UNIDAD NECESARIA")
    elif amb * nivel_carga0 > 70:
        DOBLE=int(amb * nivel_carga0/24)
        nivel_carga = 24/amb
        if amb * nivel_carga0/24 - int(amb * nivel_carga0/24)>0.1:
            DOBLE+=1
        print("MULTIPLES UNIDADES NECESARIA")
    else:
        nivel_carga = nivel_carga0

    if CATEG == 'C':
        print('Categ C -15%')
        CATEG_dto = 0.85
    elif CATEG == 'B':
        print('Categ B +0%')
        CATEG_dto = 1
    elif CATEG == 'A':
        print('Categ A +15%')
        CATEG_dto = 1.15
    elif CATEG == 'AA':
        print('Categ AA +25%')
        CATEG_dto = 1.25
    else:
        print('Categ desconocida: +25%')
        CATEG_dto = 1.25


    M3 = amb * nivel_carga
    print(' m3/amb:', nivel_carga, 'amb:', amb, 'M3:', M3)

    Lud = [46, 35, 25, 20, 15]
    UD_M3 = 0
    indud = 0
    for i in range(len(Lud)):
        if M3 < Lud[i]:
            UD_M3 = Lud[i]
            UD_M3_2 = Lud[i]
            indud=i

    print('UD_M3:', UD_M3)
    dicc_UD = {}
    diccOP_piso = {}
    diccHS_piso = {}

    dicc_UD['help'] = ['tipo UD (A, B, etc)', "NRO de OP para la previa", 'Nro OP traslado',
                       'Nro Hs de Carga y Descarga', 'Nro Hs Previa (Grueso)',
                       'Previa aparte? 0 si se hace el día del traslado, 1 si se hace el día anterior']
    dicc_UD[Lud[4]]=['C', 1, 2, 3, 2, 0, 2500, 15]
    dicc_UD[Lud[3]]=['D', 2, 2, 4, 2, 1, 4500, 20]
    dicc_UD[Lud[2]]=['E', 2, 4, 5, 3, 1, 7500, 25]
    dicc_UD[Lud[1]]=['F', 3, 5, 6, 3, 1, 15000, 35]  #ELEM NRO OP ERA 4
    dicc_UD[Lud[0]]=['FF', 3, 6, 7, 4, 1, 20000, 60]

    tablares = []
    tablares.append(UD_M3)
    tablares.append(dicc_UD[UD_M3][0])

    Criteriopisos = [1, 5, 10, 15, 20]
    Orig_pisos_crit = 0
    for i in range(len(Criteriopisos)):
        if piso_ori < Criteriopisos[i]:
            Orig_pisos_crit = Criteriopisos[i]
            break
        elif i == len(Criteriopisos) - 1:
            Orig_pisos_crit = Criteriopisos[-1]

    Dest_pisos_crit = 0
    for i in range(len(Criteriopisos)):
        if piso_dest < Criteriopisos[i]:
            Dest_pisos_crit = Criteriopisos[i]
            break
        elif i == len(Criteriopisos) - 1:
            Dest_pisos_crit = Criteriopisos[-1]

    diccOP_piso['help'] = ['Tabla \"cant OP adicionales en CyD\" - fila: cant pisos - columnas: tamaño ascensor',
                           "Col 0. cant OP adicionales en CyD, no hay ascensor", "Col 1. IDEM con ascensor chico",
                           'Col. 2. IDEM ascensor medio', 'Col 3. IDEM Ascensor Grande']
    diccOP_piso[Criteriopisos[0]] = [0, 0, 0, 0]
    diccOP_piso[Criteriopisos[1]] = [0.5, 0, 0, 0]
    diccOP_piso[Criteriopisos[2]] = [1, 0.5, 0, 0]
    diccOP_piso[Criteriopisos[3]] = [2, 1, 0.5, 0]
    diccOP_piso[Criteriopisos[4]] = [2, 1, 0.5, 0]

    diccHS_piso['help'] = ['Tabla \"cant HS adicionales en CyD\" - fila: cant pisos - columnas: tamaño ascensor',
                           'Col 0. Adicional hs: si no hay ascensor', "Col 1.Adicional hs: si hay ascensor chico",
                           'Col. 2 IDEM para ascensor mediano', 'Col. 3. IDEM ascensor grande']
    diccHS_piso[Criteriopisos[0]] = [0, 0, 0, 0]
    diccHS_piso[Criteriopisos[1]] = [1, 0.75, 0.5, 0.25]
    diccHS_piso[Criteriopisos[2]] = [1, 0.75, 0.5, 0.25]
    diccHS_piso[Criteriopisos[3]] = [1.5, 1.25, 0.75, 0.4]
    diccHS_piso[Criteriopisos[4]] = [2, 1.5, 1.25, 0.75]

    dicc_MAT_FINO = {}
    dicc_MAT_FINO['help'] = ['input: ELEMENTO', 'Return: $Costo']
    dicc_MAT_FINO['BOLSONES'] = 162
    dicc_MAT_FINO['PLURIBOL'] = 1900
    dicc_MAT_FINO['STRECHT GDE'] = 1080
    dicc_MAT_FINO['STRECHT CHI'] = 250
    dicc_MAT_FINO['PAPEL'] = 265
    dicc_MAT_FINO['C. EMP'] = 72
    dicc_MAT_FINO['C. FRAGIL'] = 255
    dicc_MAT_FINO['CAJA N1'] = 65
    dicc_MAT_FINO['CAJA N2'] = 140
    dicc_MAT_FINO['CAJA N3'] = 80
    dicc_MAT_FINO['FLETE'] = 80

    NCAJASXCINTA=5
    ccajas = (amb + pers) * 5
    cbolsones = int(ccajas * 0.75)
    if ccajas / NCAJASXCINTA - int(ccajas / NCAJASXCINTA) < 0.3:
        ccintas = int(ccajas / NCAJASXCINTA)
    else:
        ccintas = int(ccajas / NCAJASXCINTA) + 1
    flete = np.max([kms_ori * dicc_MAT_FINO['FLETE'], 450])
    MAT_GRUESO = (dicc_MAT_FINO['PLURIBOL'] + dicc_MAT_FINO['STRECHT GDE'] + dicc_MAT_FINO['STRECHT CHI']) * (
                1 + int(M3 / 30)) * hay_mat_grueso
    MAT_FINO_1 = ccajas / 3 * (
                dicc_MAT_FINO['CAJA N1'] + dicc_MAT_FINO['CAJA N2'] + dicc_MAT_FINO['CAJA N3']) + ccintas * \
                 dicc_MAT_FINO['C. EMP'] + dicc_MAT_FINO['C. FRAGIL']
    MAT_FINO_2 = cbolsones * dicc_MAT_FINO['BOLSONES'] + amb * dicc_MAT_FINO['PAPEL']

    tablares.append(
        [ccajas * hay_mat_fino, cbolsones * hay_mat_fino, ccintas * hay_mat_fino, (1 + int(M3 / 30)) * hay_mat_grueso,
         flete * hay_mat_grueso])
    print('MAT GRUESO: $', MAT_GRUESO * 1.25)
    MAT_FINO = round((MAT_FINO_1 + MAT_FINO_2) * hay_mat_fino, 2)

    print('MAT FINO: $', MAT_FINO * 1.25, ' - Cant cajas:', ccajas * hay_mat_fino)

    MAT_TOTAL = round((MAT_FINO + MAT_GRUESO + flete) * 1.25, 2)

    print('MAT TOTAL: $', MAT_TOTAL)

    m3_fino_xop_xhr = 4 #EMB FINO A LA MITAD DE PRECIO  # constante indica cuantos m3 embala (emb fino) un op por hora (promedio).
    m3_cyd_xop_xhr = 2*dicc_UD[UD_M3_2][7]/(dicc_UD[UD_M3_2][2]*dicc_UD[UD_M3_2][3])#4.5 #EMB FINO A LA MITAD DE PRECIO  # constante indica cuantos m3 embala (emb fino) un op por hora (promedio).
    if indud>0 and COC_PROG==True:
        OP_PV = np.max([(dicc_UD[Lud[indud]][1]+int(M3*((dicc_UD[Lud[indud-1]][1]-dicc_UD[Lud[indud]][1])/(dicc_UD[Lud[indud]][7])))) * hay_emb_grueso, 2 * hay_emb_fino])
    else:
        OP_PV = np.max([dicc_UD[UD_M3_2][1] * hay_emb_grueso, 2 * hay_emb_fino])  # sii hay emb fino minimo 2 op para previa
    if hay_emb_fino == 0:

        if indud>0 and COC_PROG==True:
            HS_PV_grueso = ((dicc_UD[UD_M3_2][4]+M3*((dicc_UD[Lud[indud-1]][4]-dicc_UD[Lud[indud]][4])/(dicc_UD[Lud[indud]][7]))) + dicc_UD[UD_M3_2][5]) * hay_mat_grueso
            HS_PV_EN_TRASLADO = (dicc_UD[UD_M3_2][4]+M3*((dicc_UD[Lud[indud-1]][4]-dicc_UD[Lud[indud]][4])/(dicc_UD[Lud[indud]][7]))) * (1 - dicc_UD[UD_M3_2][5]) * hay_emb_grueso
        else:
            HS_PV_grueso = (dicc_UD[UD_M3_2][4] + dicc_UD[UD_M3_2][5]) * hay_mat_grueso
            HS_PV_EN_TRASLADO = dicc_UD[UD_M3_2][4] * (1 - dicc_UD[UD_M3_2][5]) * hay_emb_grueso
        HS_PV_fino = 0
        HS_PV = (HS_PV_fino + HS_PV_grueso - HS_PV_EN_TRASLADO)
    else:
        if indud>0 and COC_PROG==True:
            HS_PV_grueso = ((dicc_UD[UD_M3_2][4]+M3*((dicc_UD[Lud[indud-1]][4]-dicc_UD[Lud[indud]][4])/(dicc_UD[Lud[indud]][7])))) * hay_mat_grueso
        else:
            HS_PV_grueso = (dicc_UD[UD_M3_2][4]) * hay_mat_grueso
        HS_PV_fino = hay_emb_fino * M3 / (m3_fino_xop_xhr * OP_PV)
        HS_PV_EN_TRASLADO = 0
        HS_PV = (HS_PV_fino + HS_PV_grueso)
    LIST_PISOS_O_D = [[Orig_pisos_crit, asc_ori], [Dest_pisos_crit, asc_dest]]
    LIST_ADOP_O_D = [diccOP_piso[Orig_pisos_crit][asc_ori], diccOP_piso[Dest_pisos_crit][asc_dest]]
    print('Lista pisos, asce. (or y dest):', LIST_PISOS_O_D, 'OP_AD:', np.max(LIST_ADOP_O_D))
    OP_ADIC_TRAS = 0  # np.max(LIST_ADOP_O_D)
    if indud>0 and COC_PROG==True:
        OP_TRAS = dicc_UD[UD_M3_2][2]+int(M3*((dicc_UD[Lud[indud-1]][2]-dicc_UD[Lud[indud]][2])/(dicc_UD[Lud[indud]][7])))  # +OP_ADIC_TRAS
    else:
        OP_TRAS = dicc_UD[UD_M3_2][2]  # +OP_ADIC_TRAS
    if piso_ori + piso_dest > 5:
        HS_OP_AD = 1 + int((piso_ori + piso_dest - 5) / 10)  # diccHS_piso[Orig_pisos_crit][asc_ori]+diccHS_piso[Dest_pisos_crit][asc_dest]
    else:
        HS_OP_AD = 0
    if hay_int == 0:
        if indud>0 and COC_PROG==True:
            UD_HS = (2*M3/(m3_cyd_xop_xhr*OP_TRAS)+M3*((dicc_UD[Lud[indud-1]][3]-dicc_UD[Lud[indud]][3])/(dicc_UD[Lud[indud]][7]))) + hs_recorr
        else:
            UD_HS = 2*M3/(m3_cyd_xop_xhr*OP_TRAS) + hs_recorr
        HS_OP_TRAS = UD_HS + HS_PV_EN_TRASLADO + HS_OP_AD  # HS TRASLADO , SI LA PREVIA_GRUESO SE HACE EN EL MISMO DIA SE AGREGA A ESTE HORARIO
    else:
        print("Hay Interior, según procedimiento de cobros")
        if kms_ori + kms_recorr >= 400:
            UD_HS = 24
            HS_OP_TRAS = 16
        else:
            UD_HS = 12
            HS_OP_TRAS = 8

    tablares.append(OP_PV)
    tablares.append(HS_PV)

    tablares.append(OP_TRAS)
    tablares.append(HS_OP_TRAS)
    tablares.append(UD_HS)

    print('OP_PV: ', OP_PV)
    print('HS_PV: ', HS_PV)

    print('OP_TRAS: ', OP_TRAS)
    print('HS_OP_TRAS: ', UD_HS + HS_PV_EN_TRASLADO, ' + ', HS_OP_AD, '(adicionales por pisos)')
    if HS_PV_EN_TRASLADO>0:
        print('Incluye hs de previa grueso en traslado', HS_PV_EN_TRASLADO)



    print('UD_M3: ', UD_M3)
    print('UD_HS: ', UD_HS)
    print('\n')
    print('\n')
    print('\n')


    if hay_emb_fino == 1:
        LetraB = CATEG
    else:
        LetraB = 'X'
    if np.max([diccOP_piso[Orig_pisos_crit][asc_ori], diccOP_piso[Dest_pisos_crit][asc_dest]]) >= 1:
        LetraC = CATEG
    else:
        LetraC = 'X'


    CATEG_TXT = str(str(round(M3 * DOBLE, 2)) + '(' + str(round(np.max([0, UD_HS - 1]), 2)) + ')' + '/(' + str(
        np.mean([OP_PV, OP_PV * DOBLE])) + '/' + str(round(np.max([0, HS_PV - 1]), 2)) + ')-(' + str(
        np.mean([OP_TRAS, OP_TRAS * DOBLE])) + '/' + str(round(np.max([0, HS_OP_TRAS - 1]), 2)) + ')/' + str(
        CATEG) + str(LetraB) + str(LetraC))

    print('CODIGO:', CATEG_TXT)
    print('\n')
    print('\n')
    print('\n')
    print('resul tabla:', 'm3 Ud', 'Tipo Ud', 'lista:[ccajas, cbolsones, ccintas, set_mat_grueso ,precio_flete]',
          'OP PV', 'HS PV', 'OP TRAS', 'HS OP TRAS', 'UD HS TRAS')
    return DOBLE, tablares, CATEG_TXT,M3/(dicc_UD[Lud[indud]][7])

def calcula_distancia(self, direccion1, direccion2):
    try:
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
    except:
        return 0.2, 2, ' - INVALID REQUEST - CALCULA NO ANDA - RESET PC SERVER'

def calcula_coordenadas(self, direccion):

    api_key = '&units=imperial&key=AIzaSyAvffBICS3JwKVK7xSTj_5sXDQkd5iU6wA'


    print('calc_dist oyd:', direccion)

    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + direccion + api_key

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    anex2='ELEMENTS RESPONSE: '
    for key1 in response.json()["results"][0]["geometry"].keys():
        try:
            for key2 in response.json()["results"][0]["geometry"][key1].keys():
                anex2+='Elem:'+key1+','+key2+':'+str(response.json()["results"][0]["geometry"][key1][key2])+' - '
        except:
            try:
                anex2 += 'Elem:' + key1 + str(response.json()["results"][0]["geometry"][key1]) + ' - '
            except:
                try:
                    anex2 +=str(response.json()["results"][0]["geometry"]["duration"]["value"])
                except:
                    pass
            #if key1=='status' and response.json()["results"][0]["geometry"][key1]=='NOT_FOUND':


    #
    print('oyd:', direccion)
    print('hi1:', response.json())

    try:
        coordenadasx = response.json()["results"][0]["geometry"]["location"]["lat"]
        coordenadasy = response.json()["results"][0]["geometry"]["location"]["lng"]
    except:
        coordenadasx=0
        coordenadasy=0


    if response.json()['status']=='INVALID_REQUEST':
        coordenadasx, coordenadasy = 0, 0
        anex2+=' - INVALID REQUEST'
    return coordenadasx, coordenadasy, anex2

def FormMDZ(self, CATEG, AMB, PERS, NV_CARGA, ORIGEN, DESTINO, PISO_O, ASC_ORI, PISO_D, ASC_DEST, HAYMG, HAYMF,
            HAYEMBFINO, HAYEMBGRUESO, HAYPROV, origen_prov, destino_prov):
    #ORIGEN = 'ESTACION LACROZE, CABA'  # DIRECCION DE CARGA
    #DESTINO = 'CHACARITA BARRIO LOS ANDES '  # DIRECCION DE DESCARGA
    araujo='ARAUJO 1508, caba'

    if self.mdz_tiempo_rec>0 and self.mdz_kms_ori>0 and self.mdz_kms_rec>0:
        anex=str('USO DE KM0, KMOYD, TIEMPOOYD')
        RESLECT = [self.mdz_kms_ori,self.mdz_kms_rec,self.mdz_tiempo_rec]
        self.desc1+='\n'+anex
    else:
        anex=str('USO DE SELENIUM GOOGLE, '+ ORIGEN + DESTINO)
        #anex=str('USO DE KEY API GOOGLE, '+ ORIGEN + DESTINO)

        #raise UserError('Debe llenar los campos -Kms de Araujo a Origen-, -Kms de Origen a Destino- y  -Tiempo de Origen a Destino- ')
        tiempo_myo, distance_myo, anex2 = calcula_distancia(self,araujo, ORIGEN)#calcula_distancia(self, araujo, ORIGEN)
        tiempo_oyd, distance_oyd, anex2 = calcula_distancia(self,ORIGEN, DESTINO)#calcula_distancia(self, ORIGEN, DESTINO)
        anex+=anex2
        RESLECT = [distance_myo, distance_oyd, tiempo_oyd/3600]#LecturaDirec(ORIGEN, DESTINO)#
        act=self.env['abatar.crm'].search([('id', '=', self.id), ('active', 'in', (True, False))], limit=1)
        act.mdz_kms_ori, act.mdz_kms_rec, act.mdz_tiempo_rec, newdesc1=distance_myo, distance_oyd, tiempo_oyd/3600, anex
        act.desc1=act.desc1+'\n'+newdesc1
    print("Result Google:", RESLECT)
    HS_RECORR = RESLECT[2]
    KM_RECORR = RESLECT[1]
    KM_ORI = RESLECT[0]
    if HAYPROV==1:
        if origen_prov:
            kms=KM_ORI+KM_RECORR
        else:
            kms = KM_RECORR
    else:
        kms=0
    HAYINT = 0
    if KM_RECORR + KM_ORI > 300:
        print('hay int!')
        HAYINT = 1  # Hay direccion en el interior (+300km)?  (0=no, 1=si)
        kms=kms*2

    doble, Ej, CATEG_TXT, COC = CotizMDZ(CATEG, AMB, PERS, HS_RECORR, KM_ORI, KM_RECORR, PISO_O, PISO_D, ASC_ORI, ASC_DEST, NV_CARGA, HAYMF,
                  HAYMG, HAYEMBFINO, HAYEMBGRUESO, HAYPROV, HAYINT)
    return doble,kms,KM_ORI, Ej, CATEG_TXT, COC


class AbatarCRM(models.Model):
    _name = "abatar.crm"
    _description = "Abatar CRM"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin','abataradd.resumenbus']
    _rec_name = "pedide"
    _order = 'sin_atender desc, recontactar_days desc'


    @api.multi
    def unlink(self):
        for rec in self:
            rec.write({'recontactar':False})
            if rec.cotizador:
                cotiz=self.env['abatar.cotizador'].search([('id', '=', rec.cotizador.id)], limit=1)
                if cotiz:
                    cotiz.unlink()

            error_calen=self.env['abatar.calendario.crm'].search([('crm', '=', rec.id)])
            if error_calen:
                for rec2 in error_calen:
                    cal_temp=rec2.calendario_id
                    rec2.unlink()
                    if not cal_temp.calendario_lines and not cal_temp.ordenes:
                        cal_temp.unlink()
            if rec.calendario:
                calen=self.env['abatar.calendario'].search([('id', '=', rec.calendario.id)], limit=1)

                for rec2 in calen.calendario_lines:
                    if rec2.crm.id==rec.calendario.id:
                        rec2.unlink()
                if not calen.calendario_lines and not calen.ordenes:
                    calen.unlink()

            if rec.list_restricciones:
                for elem in rec.list_restricciones:
                    elem.unlink()

            if rec.factura:
                rec.factura.unlink()
                rec.factura=False
            ordenes_borr=self.env['abatar.ordenes'].search([('crm', '=', rec.id)])
            if ordenes_borr:
                for rec2 in ordenes_borr:
                    rec2.unlink()
        res = super(AbatarCRM, self).unlink()
        return res


    name_seq = fields.Char(string='CRM Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    pedide = fields.Char(string='Pedido', default=lambda self: _('New'))
    es_conocido = fields.Selection(
        [('si', 'Si'), ('no', 'No')],
        string='Es cliente?', default='no', required=True)


    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_sequence=2,
                              default=lambda self: self.env.user)

    admin = fields.Boolean(string='Es Admin?', compute='set_admin')
    cliente = fields.Many2one('abatar.clientes', string='Cliente')
    contacto = fields.Many2one('abatar.clientes.lines', string='Contacto')
    tel_cliente = fields.Char(string='Telefono')
    email_cliente = fields.Char(string='Email')


    sin_atender=fields.Boolean(string="Hay Que atender Respuesta Boti", default=False)

    generico = fields.Boolean(string='Es presupuesto Generico',help='Los presupuestos hacia personas suelen ser para pautas concretas, pero a veces para empresas se hacen presupuestos que son para tareas genericas que no necesariamente se harán pero se dan para una compulsa de precios', default=False)
    empresa = fields.Char(string='Empresa')
    name = fields.Char(string='Nombre', required=True)
    tel = fields.Char(string='Telefono')
    email = fields.Char(string='Email')
    tel_search=fields.Char(string="Tel search",store=True, readonly=True, compute='set_tel_search')
    key_usuario = fields.Char(string='Key de Usuario')

    m3_flete = fields.Float(string='Flete - M3 de UD')
    kgs_flete = fields.Float(string='Flete - Kgs de UD')
    fdp_flete = fields.Char(string='Forma de Pago:', default="Al Contado en efectivo.")
    cyd_flete = fields.Boolean(string='Hacemos Carga y Descarga', default=False)
    cyd_autoelev = fields.Boolean(string='CyD con Autoelev.', default=False)
    cyd_minop = fields.Integer(string='Min OP CyD', default=0)
    cyd_forcop = fields.Integer(string='Elegir OP CyD', default=0)
    cyd_solo_cod = fields.Char(string='Solo Carga o Desc.?', help='Indicar si trabajamos en "Carga", "Descarga", o "Ambas" escribiendo explicitamente estos valores sin comillas', default='Ambas')
    cyd_emb_grueso = fields.Boolean(string='Hay Emb Grueso?', default=False)

    precio = fields.Float(string='Precio(Sin IVA)')
    precio_mas_iva = fields.Float(string='Precio(Con IVA)', store=True, readonly=True, compute='set_precio_mas_iva')
    orientacion = fields.Boolean(string='Es Orientacion?', default=True, help="Indica si el precio puede oscilar en un 15%.")
    mas_iva = fields.Boolean(string='+ IVA?', default=True, help="Indica si en el presupuesto debe aparecer el \"+ IVA\" luego del precio.")
    codigo = fields.Char(string='Codigo')
    ult_accion=fields.Char(string='Accion venta (ult)',store=True, readonly=True, compute='set_ult_accion')
    ult_fecha=fields.Date(string='Fecha Accion venta (ult)',store=True, readonly=True, compute='set_ult_accion')
    texto_ppal_presup=fields.Boolean(string='Muestra Texto Principal', default=True)
    exced_presup=fields.Float(string='Mostar Excedente por Valor')
    nota_al_pie_presup=fields.Text(string='Nota al Pie Presupuesto')


    ver_flete = fields.Boolean(string='FLETE', default=False)
    ver_mdz = fields.Boolean(string='MUDANZA', default=False)
    ver_direc = fields.Boolean(string='DIRECCIONES', default=False)
    ver_fact = fields.Boolean(string='PRESUPUESTO', default=False)
    ver_cobros = fields.Boolean(string='COBROS', default=False)
    ver_otros = fields.Boolean(string='OTROS', default=False)

    ###########DATOS MDZ
    mdz_amb = fields.Integer(string='Ambientes')
    mdz_pers = fields.Integer(string='Personas')
    mdz_carga = fields.Integer(string='Nivel de Carga (de 6 a 8 en gral)')
    mdz_m3_auto = fields.Integer(string='M3 Estimado',store=True, readonly=True, compute='set_m3_auto')  #def m3_auto=amb*carga
    mdz_op_cyd = fields.Boolean(string='Hacemos Carga y Descarga', default=True)

    mdz_hay_mg=fields.Boolean(string="Hay Mat. emb Grueso", default=True)
    mdz_hay_mf=fields.Boolean(string="Hay Mat. emb Fino", default=True)
    mdz_hay_emb_g=fields.Boolean(string="Hay Emb. Grueso", default=True)
    mdz_hay_emb_f=fields.Boolean(string="Hay Emb. Fino", default=False)

    mdz_hay_vacio=fields.Boolean(string="Hay Vacio", default=False)
    mdz_monto_cobro_vacio=fields.Float(string="Vacio: Monto Cobro con IVA", default=0)
    mdz_monto_costo_vacio=fields.Float(string="Monto Costo con IVA Vacio", default=0)

    mdz_esc_ori = fields.Integer(string='Bultos por Escalera Origen')
    mdz_esc_des = fields.Integer(string='Bultos por Escalera Destino')
    mdz_acarreo_ori = fields.Boolean(string='Acarreo en Origen por Subsuelo', default=False)
    mdz_acarreo2_ori = fields.Boolean(string='Acarreo en Origen más de 20 mts', default=False)
    mdz_acarreo_des = fields.Boolean(string='Acarreo en Destino por Subsuelo', default=False)
    mdz_acarreo2_des = fields.Boolean(string='Acarreo en Destino más de 20 mts', default=False)
    mdz_roperitos = fields.Boolean(string='Hay Roperitos?', default=True)
    mdz_roperitos_cant = fields.Integer(string='Cant Roperitos acordados', default=0)
    mdz_desembalaje = fields.Boolean(string='Hay Desembalaje?', default=True)

    mdz_kms_ori=fields.Float(string='Kms al Origen (desde Of).')
    mdz_kms_rec=fields.Float(string='Kms de Origen a Destino.')
    mdz_tiempo_rec=fields.Float(string='Tiempo de Origen a Destino.')

    mdz_mucho_esc = fields.Boolean(string='Hay Mucha Escalera?', default=False)
    mdz_mucho_emb = fields.Boolean(string='Hay Mucho Embalaje?', default=False)
    mdz_ascensor_origen=fields.Selection([('1', 'No Tiene'), ('2', 'Chico'), ('3', 'Mediano'), ('4', 'Grande')], string="Tamaño del ascensor Origen", default='3')
    mdz_ascensor_destino=fields.Selection([('1', 'No Tiene'), ('2', 'Chico'), ('3', 'Mediano'), ('4', 'Grande')], string="Tamaño del ascensor Destino", default='3')

    mdz_categ=fields.Selection([('C', 'C'), ('B', 'B'), ('A', 'A'), ('AA', 'AA')], string="Categoria Mudanza")
    ###########DATOS MDZ

    bolsones = fields.Integer(string='Bolsones')

    calendario = fields.Many2one('abatar.calendario', string='Calendario')

    ordenes_r = fields.Integer(string='Ordenes Realizadas',  compute='cuenta_ordenes')
    costos_total = fields.Float(string='Costos Totales')
    ganancia_neta = fields.Float(string='Ganancia $ (sin IVA)',  store=True, readonly=True, compute='set_ganancia')
    ganancia_neta_pc = fields.Float(string='% Ganancia $ (sin IVA)',  store=True, readonly=True, compute='set_ganancia')
    ganancia_bruto = fields.Float(string='Ganancia $ (+ IVA)',  store=True, readonly=True, compute='set_ganancia')
    ganancia_bruto_pc = fields.Float(string='% Ganancia $ (+ IVA)',  store=True, readonly=True, compute='set_ganancia')
    estado_mdz = fields.Char(string='Estado',default='VT', store=True, readonly=True, compute='cuenta_ordenes2')

    convenio = fields.Selection(
        [('30', '30 - 30 - 40'), ('40', '40 - 60'), ('25', '25 - 75'), ('20', '20 - 80'), ('contado', 'Al contado'), ('cc', 'Cuenta Corriente')],
        string='Convenio', default='30')
    convenio_dias=fields.Integer('Forz Días para cobro')

    state = fields.Selection(
        [('pendiente', 'Pendiente'), ('presupuesto', 'Presupuesto'), ('confirmado', 'Confirmado'), ('cancelado', 'Cancelado'), ('finalizado', 'Finalizado'), ('rechazado', 'Rechazado')],
        string='Status',store=True, readonly=True, compute='depends_estado', default='pendiente')
    esnuevo = fields.Boolean(default=True)

    tipo_fc = fields.Selection([('s/f', 's/f'),('A', 'A'), ('B', 'B'), ('C', 'C'),('A(myp)', 'A(myp)'), ('B(myp)', 'B(myp)')],default='s/f', string='Tipo Factura')

    fecha_inicial = fields.Datetime(string='Fecha de Ingreso', required=True, default=lambda self: fields.datetime.now())
    fecha_ejecucion = fields.Datetime(string='Fecha de Ejecucion')
    fecha_ejecucion_name = fields.Char(string='Fecha del Servicio')
    fecha_previa_name = fields.Char(string='Fecha de Previa')

    fecha_ejecucion2 = fields.Date(string='Fecha de Ejecucion2', store=True, readonly=True, compute='set_fecha2')
    fecha_confirmacion = fields.Date(string='Fecha de Confirmacion')
    fecha_presupuesto = fields.Date(string='Fecha de Presupuesto')

    recontactar2 = fields.Datetime(string='Fecha de Ejecucion', compute='set_date_edit')
    recontactar = fields.Date(string='Recontactar')
    recontactar_days = fields.Integer(string='Días para Recontactar', compute='set_days_recontactar', store=True, readonly=True)

    fechasv_proximo = fields.Integer(string="fecha_sv_proxima", compute='set_fecha_sv_prox')

    seguro = fields.Char(string='Seguro', default='Seguro de mercadería en tránsito a cargo del Cliente. Sin repetición alguna a Eduardo Hector Roisman Bullrich y/o a quien este contratare.')
    desc1 = fields.Text(string='Descripcion', default='')
    desc_html = fields.Html(string='Descripcion Libre', default='')
    ocultar_cuerpo_pres = fields.Boolean(string='Ocultar Cuerpo direc', default=False)
    ocultar_cuerpo_pres2 = fields.Boolean(string='Ocultar Cuerpo precio', default=False)
    ocultar_cuerpo_pres3 = fields.Boolean(string='Ocultar Cuerpo notas', default=False)
    desc2_html = fields.Html(string='Descripcion Bajo direccion Libre', default='')
    desc_pie_html = fields.Html(string='Descripcion Condiciones Generales Libre', default='')
    desc_state = fields.Text(string='Descripcion Corta', compute='set_state', default='')
    cotizador = fields.Many2one('abatar.cotizador',string='Cotizador')
    cotizador_total=fields.Float(related='cotizador.total',store=True, readonly=True, string="Total Cotización")
    cotizador_total2=fields.Float(related='cotizador.total',string="Total Cotización2")
    servicio = fields.Many2one('abatar.servicios',string='Servicio')
    servicio_name = fields.Char(related='servicio.name', store=True, readonly=True,string='Servicio')
    estado = fields.Many2one('abatar.servicios.estados',string='Estado')
    estado_presupuesto = fields.Many2one('abatar.estados.presupuesto',string='Estado presupuesto')

    bool_desc_html=fields.Boolean('Usar campo Descripcion Libre', default=False)
    bool_desc_pie_html=fields.Boolean('Usar campo Descripcion Condiciones Generales Libre', default=False)
    bool_desc2_pie_html=fields.Boolean('Usar campo Descripcion Bajo direccion Libre', default=False)

    destinos_lines = fields.One2many('abatar.destinos.lines', 'orden_id_x', string='Direcciones de Clientes')
    destinos_lines2 = fields.One2many('abatar.destinos.lines2', 'orden_id_x', string='Direcciones')
    registro_pagos = fields.One2many('abatar.registro.pagos', 'orden_id_x', string='Registro de pagos')
    registro_charla = fields.One2many('abatar.registro.charla', 'orden_id_x', string='Registro de charla')
    registro_presupuestos = fields.One2many('abatar.crm.presupuestos', 'orden_id_x', string='Registro de Presupuestos') #, states={'finalizo': [('readonly', True)]}

    destinos_resumen=fields.Char(string="Resumen para busqueda", store=True, readonly=True, compute='set_destinos_resumen')


    total_pagos = fields.Float(string='Total Cobros',store=True, readonly=True,  compute='set_subtotal_pagos')
    total_saldo = fields.Float(string='Cobros Pendientes',store=True, readonly=True,  compute='set_subtotal_pagos')
    titulo = fields.Char(string='Titulo')
    subtitulo = fields.Text(string='Subtitulo')

    factura_line_ppal=fields.Boolean('Factura Ppal es Line', default=False)
    factura=fields.Many2one('abatar.factura', default=False, string="Factura asociada")
    factura_num=fields.Char(related='factura.name_seq', store=True, readonly=True, string="N° Fact.")

    acciones_venta_lines= fields.One2many('abatar.crm.acciones', 'crm_id', string='Acciones Venta')
    acciones_compra_lines= fields.One2many('abatar.crm.accionesc', 'crm_id', string='Acciones Compra')

    adjuntos= fields.One2many('abatar.crm.adjuntos', 'crm_id', string='Adjuntos')
    facturado=fields.Many2one('abatar.booleana',store=True, readonly=True, string="Tiene Factura", compute='set_facturado')

    rechazado=fields.Many2one('abatar.rechazado.presupuesto', default=False, string="Rechazado")
    rechazado_hizo=fields.Boolean(string="Hizo con otro?", related='rechazado.hizo', store=True, readonly=True)
    rechazado_desc=fields.Char(string="Motivo del Rechazo", default=False)

    hay_int=fields.Boolean(string="hay interior", default=False)
    prov_int_label=fields.Char(string="PROV Interior:", default='', readonly=True, store=True, compute='action_set_int')
    active=fields.Boolean(string="Active", default=True)
    confirmado_para_resumen=fields.Boolean(string="Cerrar para hacer con resumen", default=False)
    pauta_gral= fields.Text(string='Pauta', compute='set_destinos_resumen')
    pauta_gral_pre= fields.Text(string='Pauta', compute='set_destinos_resumen')

    op_pres=fields.Integer(string='Op cotizador', store=True, readonly=True, compute='set_pres')
    ud_pres=fields.Char(string='Ud cotizador', store=True, readonly=True, compute='set_pres')
    kms_pres=fields.Integer(string='Kms cotizador', store=True, readonly=True, compute='set_pres')
    emb_pres=fields.Float(string='$ Emb cotizador', store=True, readonly=True, compute='set_pres')
    hs_pres=fields.Float(string='Horas Sv cotizador', store=True, readonly=True, compute='set_pres')


    precio_dolar_neto=fields.Float(string='Precio Dolar (s/iva)', store=True, readonly=True, compute='set_dolar')
    precio_dolar_bruto=fields.Float(string='Precio Dolar (c/iva)', store=True, readonly=True, compute='set_dolar')
    ganancia_dolar_neto=fields.Float(string='Ganancia Dolar (s/iva)', store=True, readonly=True, compute='set_dolar')
    ganancia_dolar_bruto=fields.Float(string='Ganancia Dolar (c/iva)', store=True, readonly=True, compute='set_dolar')
    ganancia_dolar_neto_pc=fields.Float(string='% Ganancia Dolar (s/iva)', store=True, readonly=True, compute='set_dolar')
    ganancia_dolar_bruto_pc=fields.Float(string='% Ganancia Dolar (c/iva)', store=True, readonly=True, compute='set_dolar')
    costos_dolar=fields.Float(string='Costos Dolar', store=True, readonly=True, compute='set_dolar')
    dolar_uso=fields.Float(string='Dolar', store=True, readonly=True, compute='set_dolar')
    presupuesto=fields.Text(string="Presupuesto", store=True, readonly=True ,compute="read_presupuesto")
    ver_presup=fields.Boolean(string="VER Presupuesto")
    desactivar_n8n=fields.Boolean(string="Desactivar de BOT", default=False)
    vencido=fields.Binary(string="Accion vencida de BOT", default=False)

    estado_str_n8n=fields.Char(string="Estado Str N8N",track_visibility='onchange')

    estado_n8n=fields.Text(string="Estado N8N", help="""BOTI YA RESOLVIO	
1) SI, YA RESOLVÍ--->A QUE RESPONDE LA DECISION?	
--->1) PRECIO--->--->LA DIFERENCIA ES MAS DE UN 15%?	
--->--->--->1) SI--->	CIERRA 
--->--->--->2) NO--->	CIERRA
	
	
--->2) SERVICIO--->--->CIERRA	
--->3) RECOMENDACIÓN--->--->CIERRA	
	
	
2) NO AUN--->EL SERVICIO OFRECIDO ES DE SU INTERES?--->--->TIENE ALGUNA CONSULTA POR EL PTO?	
--->1) SI ESTOY INTERESADO--->--->1) SI TENGO CONSULTAS--->	CIERRA (CONTACTAR URGENTE)
--->--->--->2) NO POR EL MOMENTO--->	CIERRA 
	
--->2) NO ESTOY INTERESADO--->--->MOTIVO?	
--->--->--->1)PRECIO--->	NUESTRO SISTEMA "EASY-PACK" PROPONE VT
--->--->--->--->	1) SI QUIERO VT--->	CIERRA (AVISA OPERADOR)	
--->--->--->--->	2) NO NO QUIERO VT--->	CIERRA	
	
--->--->--->2)SERVICIO--->	CIERRA
--->--->--->3)RECOMENDACIÓN--->	CIERRA
	
	
--->3) AUN ESTAMOS AVERIGUANDO--->--->CIERRA	
	
	
3) SE POSTERGO--->PARA QUE FECHA SERÍA?	
--->DD/MM/AAAA--->--->CIERRA (AVISA AL OPEARDOR)	
	
4) SE CANCELO--->CIERRA""")
    interes=fields.Selection([('0', 'Sin definir'),('1', 'NADA INTERESADO'),('2', 'POCO INTERESADO'),('3', 'ALGO INTERESADO'),('4', 'MUY INTERESADO'),('5', 'DESEA CONTRATAR')],string='Calificación',help="Puntuación segùn el interés del cliente.", track_visibility='onchange')
    firma=fields.Selection([(3, "Grande"),(2, "Mediana"),(1, "Chica")],string='Tamaño de Firma',track_visibility='onchange', default=3)

    revisadas_restricciones = fields.Boolean(string="Restricciones direc.", default=True)
    list_restricciones = fields.One2many('abatar.restricciones.list', 'crm_id', string="Lista de Restricciones")

    def crea_restric(self,vals):
        #self.list_restricciones=[(0, 0, vals)]
        self.write({'list_restricciones': [(0, 0, vals)]})

    def reset_restric(self):
        self.write({'list_restricciones': [(0, 0, 0)]})

    def toggle_revisar(self):
        for rec in self:
            rec.revisadas_restricciones = not rec.revisadas_restricciones

    def set_revisar(self,val):
        self.write({'revisadas_restricciones':val})


    @api.depends('tel')
    def set_tel_search(self):
        for rec in self:
            tel=rec.tel
            if tel==False or tel=='':
                rec['tel_search']=''
            elif tel.find("/")>-1:
                rec['tel_search']=''
            else:
                tel=tel.replace(" ","")
                tel=tel.replace("-","")
                tel=tel.replace("+","")
                if tel[0]=='0':
                    tel=tel[1:]
                rec['tel_search']=tel

    @api.onchange('message_ids','ver_presup')
    def read_presupuesto(self):
        for rec in self:
            haypres2=False
            if rec.acciones_venta_lines:
                haypres1=False
                for elem in rec.acciones_venta_lines:
                    if elem.venta_accion.name=="ENVIÉ PRESUPUESTO":
                        fecha_pres=elem.fecha
                        haypres1=True
                        fields.Glog("envie presup ok")
                        break

                if haypres1:
                    resul=rec.message_ids.search([('date', '>',fields.datetime.now().replace(day=fecha_pres.day, month=fecha_pres.month, year=fecha_pres.year, hour=0, minute=0, second=0)),('date', '>',fields.datetime.now().replace(day=fecha_pres.day, month=fecha_pres.month, year=fecha_pres.year, hour=23, minute=59, second=59))], order='date desc')
                    if resul:
                        for res in resul:
                            if res.body.find("PRECIO DEL SERVICIO:.......")>-1:
                                haypres2=True
                                pres=res.body
                                fields.Glog("hay presup ok")
                                break
                            elif res.body.find("PRECIO ORIENTACION:.......")>-1:
                                haypres2=True
                                pres=res.body
                                fields.Glog("hay presup ori ok")
                                if not rec.orientacion:
                                    try:
                                        pres=pres.replace("ORIENTACION","DEL SERVICIO")
                                        fields.Glog("ori1 ok")
                                    except:
                                        pass
                                    try:
                                        pres=pres.replace("Orientacion","")
                                        fields.Glog("ori2 ok")
                                    except:
                                        pass

                                break
            if haypres2:
                rec.pres=pres
                fields.Glog("pres setted ok")
            else:
                rec.pres=False
                fields.Glog("pres setted null ok")



    def search_proveedores(self):
        for rec in self:
            provincias=[]
            direcciones=[]
            zonas_busqueda=[]
            if rec.destinos_lines:
                for dec in rec.destinos_lines:
                    CABA=False
                    if dec.destino_id:
                        dirac=''
                        if dec.destino_id.name:
                            dirac+=dec.destino_id.name
                            if dec.destino_id.localidad=='CABA':
                               dirac+=', '+dec.destino_id.localidad
                               zonas_busqueda.append('Centro')
                               CABA=True
                            elif dec.destino_id.provincia=='CABA':
                               dirac+=', '+dec.destino_id.provincia
                               zonas_busqueda.append('Centro')
                               CABA=True
                            else:
                               dirac+=', '+dec.destino_id.localidad+', '+dec.destino_id.provincia
                        else:
                            dirac += dec.destino_id.localidad + ', ' + dec.destino_id.provincia
                        if CABA:
                            pass
                        else:
                            CX, CY, rta=calcula_coordenadas(rec,dirac.replace('/',''))
                            if rta.find('INVALID REQUEST')>-1:
                                direcciones.append([rta,rta,dec.provincia])
                            else:
                                direcciones.append([CX,CY,dec.provincia])
            elif rec.destinos_lines2:

                for dec in rec.destinos_lines2:
                    CABA=False
                    dirac=''
                    if dec.destino:
                        dirac+=dec.destino
                        if dec.localidad=='CABA':
                           dirac+=', '+dec.localidad
                           zonas_busqueda.append('Centro')
                           CABA=True
                        elif dec.provincia=='CABA':
                           dirac+=', '+dec.provincia
                           zonas_busqueda.append('Centro')
                           CABA=True
                        else:
                           dirac+=', '+dec.localidad+', '+dec.provincia
                    else:
                        dirac += dec.localidad + ', ' + dec.provincia
                    if CABA:
                        direcciones.append('CABA')
                    else:
                        CX, CY, rta = calcula_coordenadas(rec, dirac.replace('/',''))
                        if rta.find('INVALID REQUEST') > -1:
                            direcciones.append([rta, rta,dec.provincia])
                        else:
                            direcciones.append([CX, CY,dec.provincia])
            try:
                rec.desc1+='\n '+str(direcciones)
            except:
                rec.desc1=str(direcciones)
            fields.Glog('ANALIZANDO COORDENADAS')
            for direc in direcciones:
                if direc=='CABA':
                    pass
                else:
                    FUERA_todo=True
                    for key in POLY_ZONAS.keys():
                        if key=='Centro':
                            pass
                        else:
                            FUERA=False
                            poly=POLY_ZONAS[key]
                            for ind in range(len(poly)):
                                #a=(poly[ind][0]-poly[ind-1][0])/(poly[ind][1]-poly[ind-1][1])
                                #b=poly[ind-1][0]-poly[ind-1][1]*(poly[ind][0]-poly[ind-1][0])/(poly[ind][1]-poly[ind-1][1])
                                A=np.array([poly[ind][1]-poly[ind-1][1],poly[ind][0]-poly[ind-1][0],0])
                                B=np.array([direc[1]-poly[ind-1][1],direc[0]-poly[ind-1][0],0])
                                fields.Glog('poly:'+str(poly[ind])+'direc:'+str(direc)+'- poly-1:'+str(poly[ind-1]))
                                fields.Glog('A:'+str(A)+'B:'+str(B)+'- res:'+str((B[0]*A[1]-B[1]*A[0])))
                                if (B[0]*A[1]-B[1]*A[0])>0: #>
                                    FUERA=True
                            if FUERA:
                                pass
                            else:
                                FUERA_todo=False
                                zonas_busqueda.append(key)
                    if FUERA_todo:
                        pro=direc[2]
                        tildes=[['á','a'],['Á','A'],['é','e'],['É','E'],
                                ['í','i'],['Í','I'],['ó','o'],['Ó','O'],
                                ['ú','u'],['Ú','U']]
                        for elem in tildes:
                            pro=pro.replace(elem[0],elem[1])
                        zonas_busqueda.append(pro)
            if zonas_busqueda:
                rec.desc1 += '\n zonas involucradas:'
                for zon in zonas_busqueda:
                    rec.desc1 += '\n'+zon
            proveedores=[]
            unidades=[]
            operarios=False
            if rec.cotizador:
                if rec.cotizador.linea_personal:
                    for elem in rec.cotizador.linea_personal:
                        namelem=elem.producto.name
                        if namelem in ['Operario','Supervisor']:
                            operarios=True
                        elif namelem.find('Unidad')>-1:
                            unidades.append(namelem[namelem.find('\"')+1:-1])
            resulop={}
            resulud={}
            for zona in zonas_busqueda:
                if operarios:
                    resulop[zona]=self.env['abatar.proveedores'].search([('zona_map','=',zona), ('tipo_str','=','operario')])

                if unidades:
                    resulud[zona]=[]
                    for ud in unidades:
                        resulud[zona].append(ud)
                        resulud[zona].append(self.env['abatar.proveedores'].search([('zona_map','=',zona), ('tiene_ud_tipos','ilike',ud)]))

            rec.desc1 += '\n proveedores posibles:'
            for zona in resulop.keys():
                rec.desc1 += '\n\n' + zona+':'
                rec.desc1 += '\n' +'TIPOS:'
                for elem in resulop[zona]:
                    rec.desc1 += '\n OP'

                for elem in resulud[zona][1]:
                    for ud in elem:
                        rec.desc1 += '\n UD \"%s\"'%resulud[zona][0]

                rec.desc1 += '\n\n' + 'NOMBRES:'
                for elem in resulop[zona]:
                    rec.desc1 += '\n' +elem.name

                for elem in resulud[zona][1]:
                    for ud in elem:
                        rec.desc1 += '\n' + elem.name

                rec.desc1 += '\n\n' + 'TELEFONOS:'
                for elem in resulop[zona]:
                    rec.desc1 += '\n' +elem.tel

                for elem in resulud[zona][1]:
                    for ud in elem:
                        rec.desc1 += '\n'+elem.tel







    def cambio_textos_crm(self, revisap, formato):




        rec={}
        rec['crm_id'] = revisap.id
        rec['precio'] = numtostr(int(revisap.precio))
        rec['mas_iva'] = revisap.mas_iva
        rec['telefono'] = revisap.tel
        if revisap.mdz_esc_ori or revisap.mdz_esc_ori>0:
            rec['escalera_ori'] = True
        if revisap.mdz_esc_des or revisap.mdz_esc_des>0:
            rec['escalera_des'] = True

        revisaB=formato

        rec['formato'] = revisaB.id
        rec['texto'] = revisaB.texto

        nuw_guarda1 = formato.texto


        if formato.name=='Mudanza':
            if revisap.mdz_hay_mg or revisap.mdz_hay_mf:
                if revisap.convenio=='30':
                    convenio = '30% a la Contratación contra Entrega de Materiales. 30% al Cierre del Embalaje. Saldo al Finalizar.'
                elif revisap.convenio=='40':
                    convenio = '40% a la Contratación contra Entrega de Materiales. Saldo al Finalizar.'
                elif revisap.convenio=='20':
                    convenio = '20% a la Contratación contra Entrega de Materiales. Saldo al Finalizar.'
                elif revisap.convenio=='25':
                    convenio = '25% a la Contratación contra Entrega de Materiales. Saldo al Finalizar.'
                elif revisap.convenio=='contado':
                    convenio = 'Al Contado al Finalizar.'
                elif revisap.convenio=='cc':
                    convenio = 'Cuenta Corriente.'
            else:
                if revisap.convenio=='30':
                    convenio = '30% a la Contratación. 30% al Cierre del Embalaje. Saldo al Finalizar.'
                elif revisap.convenio=='40':
                    convenio = '40% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio=='20':
                    convenio = '20% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio=='25':
                    convenio = '25% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio=='contado':
                    convenio = 'Al Contado al Finalizar.'
                elif revisap.convenio=='cc':
                    convenio = 'Cuenta Corriente.'
            name=''
            if revisap.name:
                name=revisap.name[0].upper()+revisap.name[1:].lower()
            nuw_guarda1 = nuw_guarda1.replace("@User", self.env.user.name)
            nuw_guarda1 = nuw_guarda1.replace("@name", name)
            nuw_guarda1 = nuw_guarda1.replace("@pedide", revisap.pedide)

            if revisap.mdz_m3_auto>20:
                tipomdz="Mudanza Clásica"
            elif revisap.mdz_m3_auto>15:
                tipomdz="Mudanza Estándar"
            else:
                tipomdz="Mini Mudanza"

            nuw_guarda1 = nuw_guarda1.replace("@TipoMdz", tipomdz)

            embfino=''
            if revisap.mdz_hay_emb_f:
                embfino="EMBALAJE FINO (El Cliente solo deberá embalar Ropa, Mantelería, Objetos de Valor e Íntimos. La empresa realizará el embalaje del contenido), "
                emb2="NOTA: Si no necesita el servicio de Embalaje Fino puede indicarlo y será bonificado. La Empresa no se responsabiliza por daños o roturas ocasionadas por el incorrecto embalaje de la carga. \n \n Aguardamos su Respuesta."
                nuw_guarda1 = nuw_guarda1.replace("Aguardamos su Respuesta.", emb2)
            acond=''
            if revisap.mdz_hay_emb_g:
                acond="EMBALAJE GRUESO (Protección de los elementos de mayor porte, y desarme y/o desmonte ligero de los elementos que merecen y otros), "

            nuw_guarda1 = nuw_guarda1.replace("@EmbFino", embfino)
            nuw_guarda1 = nuw_guarda1.replace("@AcondMob", acond)

            escalera=''
            if rec['escalera_des'] and rec['escalera_ori']:
                if revisap.mdz_esc_ori and revisap.mdz_esc_des:
                    escalera='Incluye tareas de Escalera en Origen hasta %i elementos y en Destino hasta %i elementos. ' % (revisap.mdz_esc_ori, revisap.mdz_esc_des)
                elif revisap.mdz_esc_ori:
                    escalera='Incluye tareas de Escalera en Origen hasta %i elementos, y en Destino. ' % revisap.mdz_esc_ori
                elif revisap.mdz_esc_des:
                    escalera='Incluye tareas de Escalera en Origen, y en Destino hasta %i elementos. ' % revisap.mdz_esc_des
                else:
                    escalera='Incluye tareas de Escalera en Origen y Destino. '
            elif rec['escalera_ori']:
                if revisap.mdz_esc_ori:
                    escalera='Incluye tareas de Escalera en Origen hasta %i elementos. ' % revisap.mdz_esc_ori
                else:
                    escalera='Incluye tareas de Escalera en Origen. '
            elif rec['escalera_des']:
                if revisap.mdz_esc_des:
                    escalera='Incluye tareas de Escalera en Destino hasta %i elementos. ' % revisap.mdz_esc_des
                else:
                    escalera='Incluye tareas de Escalera en Destino. '
            else:
                escalera='No Incluye tareas de Escalera en Origen ni Destino. '

            nuw_guarda1 = nuw_guarda1.replace("@HayEscalera", escalera)

            acarreo=''
            if revisap.mdz_acarreo_ori and revisap.mdz_acarreo_des:
                acarreo='Incluye tareas de Acarreo por Subsuelo en Origen y Destino. '
            elif revisap.mdz_acarreo_ori:
                acarreo='Incluye tarea de Acarreo por Subsuelo en Origen. '
            elif revisap.mdz_acarreo_des:
                acarreo='Incluye tarea de Acarreo por Subsuelo en Destino. '
            else:
                acarreo='No Incluye tareas de Acarreo por Subsuelo en Origen ni en Destino. '

            nuw_guarda1 = nuw_guarda1.replace("@HayAcarreo", acarreo)

            vacio=''
            if revisap.mdz_hay_vacio:
                if rec['vacio_ori'] and rec['vacio_des']:
                    vacio = 'Incluye tareas de Vacío hasta %i elementos en Origen y hasta %i elementos en Destino. ' % (rec['vacio_ori'],  rec['vacio_des'])
                elif rec['vacio_ori']:
                    vacio = 'Incluye tareas de Vacío hasta %i elementos en Origen. ' % rec['vacio_ori']
                elif rec['vacio_des']:
                    vacio = 'Incluye tareas de Vacío hasta %i elementos en Destino. ' % rec['vacio_des']
                else:
                    vacio = 'Incluye tareas de Vacío en Origen y Destino. '

            nuw_guarda1 = nuw_guarda1.replace("@HayVacio", vacio)

            desemb = ' y Posicionamiento en un solo movimiento en Destino. '
            if revisap.mdz_desembalaje:
                if revisap.mdz_roperitos:
                    if revisap.mdz_roperitos_cant:
                        desemb+='Incluye Asistencia para retiro de rezagos de desembalaje el día posterior, y entrega de %i Roperitos al momento de la carga, para ropa de percha del día (hasta 10 perchas por Roperito) si el cliente solicitare. ' % revisap.mdz_roperitos_cant
                    else:
                        desemb+='Incluye Asistencia para retiro de rezagos de desembalaje el día posterior, y entrega de 2 Roperitos al momento de la carga, para ropa de percha del día (hasta 10 perchas por Roperito) si el cliente solicitare. '
                else:
                    desemb+='Incluye Asistencia para retiro de rezagos de desembalaje el día posterior si el cliente solicitare. '

            else:
                if revisap.mdz_roperitos:
                    if revisap.mdz_roperitos_cant:
                        desemb+='Incluye entrega de %i Roperitos al momento de la carga, para ropa de percha del día (hasta 10 perchas por Roperito) si el cliente solicitare. ' % revisap.mdz_roperitos_cant
                    else:
                        desemb+='Incluye entrega de 2 Roperitos al momento de la carga, para ropa de percha del día (hasta 10 perchas por Roperito) si el cliente solicitare. '
                else:
                    desemb+=''

            nuw_guarda1 = nuw_guarda1.replace("@HayDesembyRoperito", desemb)

            matemb=''
            kms=0
            if revisap.cotizador:
                if revisap.cotizador.kms:
                    kms=revisap.cotizador.kms
            if revisap.mdz_hay_mf:
                if revisap.cotizador.embalaje_lines:
                    cajas=0
                    bolsones=0
                    for elem in revisap.cotizador.embalaje_lines:
                        if elem.embalaje_id.name in ('Cajas N°1','Cajas N°2','Cajas N°3'):
                            cajas+=elem.cantidad
                        elif elem.embalaje_id.name=='Bolsones':
                            bolsones+=elem.cantidad
                    if kms>0:
                        if kms >= 250:
                            matemb='Al contratar se entregará en su domicilio el Set de Materiales de Embalaje "Easy-Pack" con cajas y bolsones hasta agotar la necesidad, entre otros elementos, según se ilustra en 4 pasos en el siguiente link: https://grupoabatar.com.ar/mudanza-easypack/#primero'
                        else:
                            matemb='Al contratar se entregará en su domicilio el Set de Materiales de Embalaje "Easy-Pack" con %i cajas y %i bolsones, entre otros elementos según se ilustra en 4 pasos en el siguiente link: https://grupoabatar.com.ar/mudanza-easypack/#primero' % (cajas, bolsones)
                    else:
                        matemb='Al contratar se entregará en su domicilio el Set de Materiales de Embalaje "Easy-Pack" con %i cajas y %i bolsones, entre otros elementos según se ilustra en 4 pasos en el siguiente link: https://grupoabatar.com.ar/mudanza-easypack/#primero' % (cajas, bolsones)



            nuw_guarda1 = nuw_guarda1.replace("@MatEmb", matemb)

            texto = ''
            cuenta1 = 0
            cuentaei = 0

            if revisap.destinos_lines:
                for ei in revisap.destinos_lines:
                    cuenta1 += 1
                for ei in revisap.destinos_lines:
                    if ei.destino_id.name_gral:
                        if cuentaei==1:
                            texto += 'ORIGEN: ' + ei.destino_id.name_gral.upper() + '\n'
                        else:
                            if cuenta1>2:
                                texto += 'DESTINO %s: ' % str(cuentaei-1)
                                texto += ei.destino_id.name_gral.upper() + '\n'
                            else:
                                texto += 'DESTINO: ' + ei.destino_id.name_gral.upper() + '\n'

            elif revisap.destinos_lines2:
                for ei in revisap.destinos_lines2:
                    cuenta1 += 1
                for ei in revisap.destinos_lines2:
                    cuentaei += 1
                    if cuentaei==1:
                        texto += 'ORIGEN: ' + ei.name_gral.upper() + '\n'
                    else:
                        if cuenta1>2:
                            texto += 'DESTINO %s: ' % str(cuentaei-1)
                            texto += ei.name_gral.upper() + '\n'
                        else:
                            texto += 'DESTINO: ' + ei.name_gral.upper() + '\n'

            nuw_guarda1 = nuw_guarda1.replace("@Direcc", texto)


            orientacion_tel = 'El Precio es Base y de orientación telefónica pasible de ser modificado al momento de la visita, en hasta un 15% si correspondiera. '

            orientacion=''
            orientacion2=''
            if revisap.orientacion:
                    orientacion='ORIENTACION'
                    orientacion2=orientacion_tel
            else:
                    orientacion='DEL SERVICIO'
            nuw_guarda1 = nuw_guarda1.replace("@Orientacion", orientacion)

            if rec['precio']:
                nuw_guarda1 = nuw_guarda1.replace("@Precio", rec['precio'])

            if rec['mas_iva']:
                nuw_guarda1 = nuw_guarda1.replace("@Masiva", ".- + IVA")
            else:
                nuw_guarda1 = nuw_guarda1.replace("@Masiva", ".-")



            if revisap.convenio not in ('contado','cc'):
                convenio='Al Contado. '+convenio
            nuw_guarda1 = nuw_guarda1.replace("@FDP", convenio)
            peajes=''
            if kms>20:
                peajes = 'Peajes: Incluye.\n'
            nuw_guarda1 = nuw_guarda1.replace("@Peajes", peajes)

            nuw_guarda1 = nuw_guarda1.replace("@IVA", 'IVA: 21% Incluir.\n')

            segad=''
            if revisap.seguro=='Seguro de mercadería en tránsito a cargo del Cliente. Sin repetición alguna a Eduardo Hector Roisman Bullrich y/o a quien este contratare.':
                pass
            else:
                if revisap.seguro:
                    segad+=revisap.seguro
            nuw_guarda1 = nuw_guarda1.replace("@Seguros", 'Seguros: Incluye. %s\n'%segad)

            nuw_guarda1 = nuw_guarda1.replace("@Orient2", orientacion2)

        elif formato.name=='Flete':

            if revisap.cyd_emb_grueso:
                if revisap.convenio == '30':
                    convenio = '30% a la Contratación. 30% al Cierre del Embalaje / Despacho de la unidad. Saldo al Finalizar.'
                elif revisap.convenio == '40':
                    convenio = '40% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == '20':
                    convenio = '20% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == '25':
                    convenio = '25% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == 'contado':
                    convenio = 'Al Contado al Finalizar.'
                elif revisap.convenio == 'cc':
                    convenio = 'Cuenta Corriente.'
            else:
                if revisap.convenio == '30':
                    convenio = '30% a la Contratación. 30% al Despacho de la unidad. Saldo al Finalizar.'
                elif revisap.convenio == '40':
                    convenio = '40% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == '20':
                    convenio = '20% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == '25':
                    convenio = '25% a la Contratación. Saldo al Finalizar.'
                elif revisap.convenio == 'contado':
                    convenio = 'Al Contado al Finalizar.'
                elif revisap.convenio == 'cc':
                    convenio = 'Cuenta Corriente.'

            orientacion_tel = 'El Precio es Base y de orientación telefónica pasible de ser modificado al momento de la visita, en hasta un 15% si correspondiera. '

            name=''
            if revisap:
                if revisap.name:
                    name=revisap.name[0].upper()+revisap.name[1:].lower()
            nuw_guarda1 = nuw_guarda1.replace("@User", self.env.user.name)
            nuw_guarda1 = nuw_guarda1.replace("@name", name)
            nuw_guarda1 = nuw_guarda1.replace("@pedide", revisap.pedide)


            UdOp = ''
            UdOp2 = ''
            if revisap.op_pres:
                UdOp = "Unidad Apta, Chofer y Operarios para tareas"
                UdOp2 = "Carga, Traslado, Descarga y Posicionamiento en un solo movimiento en Destino."
            else:
                UdOp = "Unidad Apta y Chofer para tarea"
                UdOp2 = "Traslado. "

            nuw_guarda1 = nuw_guarda1.replace("@UdOp2", UdOp2)
            nuw_guarda1 = nuw_guarda1.replace("@UdOp", UdOp)

            acond = ''
            if revisap.cyd_emb_grueso:
                acond = "Acondicionamiento del Mobiliario, "

            nuw_guarda1 = nuw_guarda1.replace("@AcondMob", acond)

            cargaydesc = ''
            if revisap.cyd_flete:
                if revisap.cyd_solo_cod=='Ambas':
                    cargaydesc = "Carga, Traslado, Descarga y Posicionamiento en un solo movimiento en Destino"
                elif revisap.cyd_solo_cod=='Carga':
                    cargaydesc = "Carga y Traslado"
                elif revisap.cyd_solo_cod=='Descarga':
                    cargaydesc = "Traslado, Descarga y Posicionamiento en un solo movimiento en Destino"

            nuw_guarda1 = nuw_guarda1.replace("@CargayDesc", cargaydesc)

            escalera = ''
            if rec['escalera_des'] and rec['escalera_ori']:
                escalera = 'Incluye tareas de Escalera en Origen y en Destino. '

            elif rec['escalera_ori']:
                escalera = 'Incluye tareas de Escalera en Origen. '

            elif rec['escalera_des']:
                escalera = 'Incluye tareas de Escalera en Destino. '
            else:
                escalera = 'No Incluye tareas de Escalera en Origen ni Destino. '


            nuw_guarda1 = nuw_guarda1.replace("@HayEscalera", escalera)

            acarreo = 'No Incluye tareas de Acarreo por Subsuelo en Origen ni en Destino. '
            nuw_guarda1 = nuw_guarda1.replace("@HayAcarreo", acarreo)

            vacio = ''
            if rec['vacio_ori'] and rec['vacio_des']:
                vacio = 'Incluye tareas de Vacío hasta %i elementos en Origen y hasta %i elementos en Destino. ' % (
                rec['vacio_ori'], rec['vacio_des'])
            elif rec['vacio_ori']:
                vacio = 'Incluye tareas de Vacío hasta %i elementos en Origen. ' % rec['vacio_ori']
            elif rec['vacio_des']:
                vacio = 'Incluye tareas de Vacío hasta %i elementos en Destino. ' % rec['vacio_des']
            else:
                vacio = 'No Incluye tareas de Vacío en Origen ni Destino. '

            nuw_guarda1 = nuw_guarda1.replace("@HayVacio", vacio)

            kms = 0
            if revisap.cotizador:
                if revisap.cotizador.kms:
                    kms = revisap.cotizador.kms

            texto = ''
            cuenta1 = 0
            cuentaei = 0

            if revisap.destinos_lines:
                for ei in revisap.destinos_lines:
                    cuenta1 += 1
                for ei in revisap.destinos_lines:
                    if ei.destino_id.name_gral:
                        if cuentaei == 1:
                            texto += 'ORIGEN: ' + ei.destino_id.name_gral.upper() + '\n'
                        else:
                            if cuenta1 > 2:
                                texto += 'DESTINO %s: ' % str(cuentaei - 1)
                                texto += ei.destino_id.name_gral.upper() + '\n'
                            else:
                                texto += 'DESTINO: ' + ei.destino_id.name_gral.upper() + '\n'

            elif revisap.destinos_lines2:
                for ei in revisap.destinos_lines2:
                    cuenta1 += 1
                for ei in revisap.destinos_lines2:
                    cuentaei += 1
                    if cuentaei == 1:
                        texto += 'ORIGEN: ' + ei.name_gral.upper() + '\n'
                    else:
                        if cuenta1 > 2:
                            texto += 'DESTINO %s: ' % str(cuentaei - 1)
                            texto += ei.name_gral.upper() + '\n'
                        else:
                            texto += 'DESTINO: ' + ei.name_gral.upper() + '\n'

            nuw_guarda1 = nuw_guarda1.replace("@Direcc", texto)

            orientacion = ''
            orientacion2 = ''
            if revisap.orientacion:
                orientacion = 'ORIENTACION'
                orientacion2 = orientacion_tel
            else:
                orientacion = 'DEL SERVICIO'
            nuw_guarda1 = nuw_guarda1.replace("@Orientacion", orientacion)

            if rec['precio']:
                nuw_guarda1 = nuw_guarda1.replace("@Precio", rec['precio'])

            if rec['mas_iva']:
                nuw_guarda1 = nuw_guarda1.replace("@Masiva", ".- + IVA")
            else:
                nuw_guarda1 = nuw_guarda1.replace("@Masiva", ".-")


            if revisap.convenio not in ('contado','cc'):
                convenio='Al Contado. '+convenio
            nuw_guarda1 = nuw_guarda1.replace("@FDP", convenio)

            if kms > 20:
                nuw_guarda1 = nuw_guarda1.replace("@Peajes", 'Peajes: Incluye.\n')
            else:
                nuw_guarda1 = nuw_guarda1.replace("@Peajes", '')

            nuw_guarda1 = nuw_guarda1.replace("@IVA", 'IVA: 21% Incluir.\n')

            nuw_guarda1 = nuw_guarda1.replace("@Seguros", 'Seguros: %s\n'%revisap.seguro)

            nuw_guarda1 = nuw_guarda1.replace("@Orient2", orientacion2)

        else:
            symbols=[' ','@','\n',',','.',';',':','\"','(',')']
            LINIT=10000
            notareemp=''
            if revisap.mdz_amb:
                if revisap.mdz_amb<=2:
                    notareemp='\nNOTA: Si no pudiera realizar la Visita Técnica, es posible en su caso, por ser una mudanza pequeña, realizar un presupuesto estimado de orientación, dejando la Visita Técnica para luego de su aceptación.\n'
            replaced={'@User':self.env.user.name, '@nota':notareemp}
            if nuw_guarda1.count('@')>0:
                for h1 in range(nuw_guarda1.count('@')):
                    objetivo=''
                    long=LINIT
                    h0=0
                    for i in range(len(symbols)):
                        lar=nuw_guarda1.find(symbols[i],nuw_guarda1.find('@')+1)
                        if lar<long and lar!=-1:
                            long=lar
                        h0+=1
                    if long==LINIT:
                        long=-1

                    if long==-1:
                        objetivo=nuw_guarda1[nuw_guarda1.find('@'):]
                    else:
                        objetivo=nuw_guarda1[nuw_guarda1.find('@'):long]


                    vaule=False
                    if objetivo not in replaced.keys():
                        value=revisap[objetivo[1:]]
                        if long == -1:
                            nuw_guarda1 = nuw_guarda1[:nuw_guarda1.find('@')] + str(value)
                        else:
                            nuw_guarda1 = nuw_guarda1[:nuw_guarda1.find('@')] + str(value) + nuw_guarda1[long:]
                    elif objetivo in replaced.keys():
                        if long == -1:
                            nuw_guarda1 = nuw_guarda1[:nuw_guarda1.find('@')] + str(replaced[objetivo])
                        else:
                            nuw_guarda1 = nuw_guarda1[:nuw_guarda1.find('@')] + str(replaced[objetivo]) + nuw_guarda1[long:]

            #NO REMOVER ESTO, ME SIRVE PARA ACTIVARLO SI NECESITO Y ANALIZAR ALGUNA FUNCION
            '''x,y, rta=Analize_model(self,True, 'abatar.ordenes','', 'fecha_ejecucion','subtotal', '', 'vector',[('active', 'in', (False, True)), ('fecha_ejecucion','>', datetime.datetime.strptime('01012022', '%d%m%Y').date()), ('subtotal','>', 1000)], '')

            if rta==True:
                nuw_guarda1 += '\n \n rta: %s \n' % str(rta)
            else:
                h0=0
                nuw_guarda1 += '\n \n '
                for re in rta:
                    nuw_guarda1 += '\n \n rta%i: %s \n' % (h0,str(re))
                    h0+=1

            for i in range(len(x)):
                nuw_guarda1 += '%s : %s \n' % (str(x[i]), str(y[i]))


            nuw_guarda1 += ' END OF CODE.' '''




        rec['texto'] = nuw_guarda1
        return rec['texto']




    def agenda_resolvio_pendientes(self):
        text = ''
        text2 = ''
        h0 = 1
        for rec in self.env['abatar.crm'].search([('es_conocido', '=', 'no'),('servicio', 'in', (self.env['abatar.servicios'].search([('name','=','Mudanza')]).id,self.env['abatar.servicios'].search([('name','=','Flete')]).id)),('desactivar_n8n', '=', False),('recontactar','<=',fields.Date.today()),('estado','=',self.env['abatar.servicios.estados'].search([('name','=','Presupuesto')], limit=1).id)]):

            telfiltred=rec.tel
            if telfiltred.find("/") > -1:
                pass
            else:

                telfiltred=telfiltred.replace(" ","")
                telfiltred=rec.tel.replace("+549","")
                telfiltred=telfiltred.replace("-","")
                if telfiltred[0]=="0":
                    telfiltred=telfiltred[1:]

                if rec.acciones_venta_lines:

                    for id, elem in enumerate(rec.acciones_venta_lines):
                        if id==0:
                            if elem.vencido!=False or elem.rta in (False):

                                text+="Cliente N°%i:\n"%h0
                                text+="Nombre: %s\n"%rec.name
                                text+="telefono: %s\n"%telfiltred

                                text+="\n\n Registra Acciones:\n"
                                if elem.vencido!=False:
                                    text+="Ultima Accion: (estado: VENCIDO)\n"
                                elif elem.rta in (False):
                                    text+="Ultima Accion: (estado: NO RESPONDIDO, Días para vencimiento:%i)\n" %(elem.fecha+relativedelta(days=elem.vto_f)-fields.Date.today()).days()
                                text+="fecha:%s\n"%elem.fecha.strftime('%d/%m/%Y')
                                text+="accion:%s\n"%elem.venta_accion.name

                                if self.env['abatar.textos.wsp'].search([('accion_in','=',elem.venta_accion.id)],limit=1):
                                    datexp=self.env['abatar.textos.wsp'].search([('accion_in','=',elem.venta_accion.id)],limit=1)
                                    datprint=rec.cambio_textos_crm(rec, datexp)
                                    text+="\nMensaje para reenvío:\n%s"%datprint
                                else:
                                    text+="\nMENSAJE PARA OPERADOR:\n"
                                    text += "\n CLIENTE N°%i : TODO OK (servicio chico), NO REQUIERE NINGUN MENSAJE, INIDICAR A UN OPERADOR PARA QUE SE ENCARGUE. \n" % h0
                                text+="___________________________________________\n\n\n"
                                h0+=1
                            else:#elem.rta in ('si','no')

                                #if elem.venta_accion.name=='ENVIÉ PRESUPUESTO':
                                text+="Cliente N°%i:\n"%h0
                                text+="Nombre: %s\n"%rec.name
                                text+="telefono: %s\n"%telfiltred

                                text+="\n\n Registra Acciones:\n"
                                if elem.rta=='si':
                                    text+="Ultima Accion: (estado: Respuesta: SI)\n"
                                else:
                                    text+="Ultima Accion: (estado: Respuesta: NO)\n"
                                text+="fecha:%s\n"%elem.fecha.strftime('%d/%m/%Y')
                                text+="accion:%s\n"%elem.venta_accion.name
                                text+="rta:%s\n"%elem.rta
                                text+="descripcion:%s\n"%elem.desc


                                if elem.venta_accion.name=='ENVIÉ PRESUPUESTO':
                                    if elem.rta=='si':
                                        text+="\nMENSAJE PARA OPERADOR:\n"
                                        text += "\n CLIENTE N°%i : DESEA CONTRATAR. INDICAR A UN OPERADOR PARA QUE SE ENCARGUE. \n" % h0
                                    else:
                                        text+="\nACCION AUTOMATICA:\n"
                                        text += "\n CLIENTE N°%i : PASAR A RECHAZADOS \n" % h0
                                else:
                                    text+="\nMENSAJE PARA OPERADOR:\n"
                                    text += "\n CLIENTE N°%i : TODO OK (servicio chico), NO REQUIERE NINGUN MENSAJE, INIDICAR A UN OPERADOR PARA QUE SE ENCARGUE. \n" % h0
                                text+="___________________________________________\n\n\n"
                                h0+=1
                else:


                    text += "Cliente N°%i:\n" % h0
                    text += "Tipo de Servicio: %s\n" % rec.servicio.name
                    text += "Nombre: %s\n" % rec.name
                    text += "telefono: %s\n" % telfiltred

                    text += "\n NO REGISTRA ACCIONES:\n"
                    largadist=False
                    if rec.mdz_kms_rec<150:
                        text += "Tipo de viaje: Local (OK)\n"

                    else:
                        largadist=True
                        if rec.servicio.name=='Mudanza' :
                            text += "Tipo de viaje: Larga Distancia (REQUIERE VIDEO, VISITA o DETALLE) \n"
                        else:
                            text += "Tipo de viaje: Larga Distancia (REQUIERE DETALLE o IMAGENES) \n"

                    grande=False
                    if rec.servicio.name=='Mudanza':
                        if rec.ambientes<=3:
                            text += "Tamaño: Chica-Mediana (OK)\n"

                        else:
                            grande=True
                            text += "Tamaño: Grande (REQUIERE VIDEO, VISITA o DETALLE) \n"

                    elif rec.servicio.name=='Flete':
                        if rec.m3_flete<=15:
                            text += "Tamaño: Chica-Mediana (OK)\n"

                        else:
                            grande=True
                            text += "Tamaño: Grande (REQUIERE DETALLE o IMAGENES) \n"

                    if grande or largadist:
                        if rec.servicio.name=='Flete':
                            datexp = self.env['abatar.textos.wsp'].search([('name', '=', 'Flete (pedir detalle)')],
                                                                        limit=1)
                            datprint = rec.cambio_textos_crm(rec, datexp)
                            text += "\nMensaje para Envío:\n%s" % datprint
                        else:
                            datexp = self.env['abatar.textos.wsp'].search([('name', '=', 'Mudanza (pedir video)')],
                                                                        limit=1)
                            datprint = rec.cambio_textos_crm(rec, datexp)
                            text += "\nMensaje para Envío:\n%s" % datprint

                    else:

                        text += "\nENVIO PARA OPERADOR:\n"
                        text += "\n CLIENTE N°%i : TODO OK (servicio chico), NO REQUIERE NINGUN MENSAJE, INIDICAR A UN OPERADOR PARA QUE SE ENCARGUE. \n" %h0


                    text += "___________________________________________\n\n\n"
                    h0 += 1
        success, rta=enviar_mensajegral({'data':text})
        fields.Glog('Envio de AGENDA AUTOMATICA a N8N :')
        fields.Glog(text)
        fields.Glog('rta:'+str(success)+' - msj:'+str(rta))


    def agenda_resolvio_presupuestos(self):
        text = ''
        text2 = '''Estimado/a

 Buenos días, me comunico para consultarle si el presupuesto enviado le resultó favorable y desearía avanzar, o si ya pudo resolver su necesidad?. Muchas gracias.

Aguardamos su Respuesta.
Saludos cordiales'''
        h0 = 1

        fields.Glog('for loop:' + str(self.env['abatar.crm'].search([('es_conocido', '=', 'no'),('servicio', 'in', (self.env['abatar.servicios'].search([('name','=','Mudanza')]).id,self.env['abatar.servicios'].search([('name','=','Flete')]).id)),('desactivar_n8n', '=', False),('recontactar','<=',fields.Date.today()),('estado','=',self.env['abatar.servicios.estados'].search([('name','=','Presupuesto')], limit=1).id)])))
        for rec in self.env['abatar.crm'].search([('es_conocido', '=', 'no'),('servicio', 'in', (self.env['abatar.servicios'].search([('name','=','Mudanza')]).id,self.env['abatar.servicios'].search([('name','=','Flete')]).id)),('desactivar_n8n', '=', False),('recontactar','<=',fields.Date.today()),('estado','=',self.env['abatar.servicios.estados'].search([('name','=','Presupuesto')], limit=1).id)]):

            telfiltred=rec.tel
            if telfiltred.find("/") > -1:
                pass
            else:
                telfiltred=telfiltred.replace(" ","")
                telfiltred=rec.tel.replace("+549","")
                telfiltred=telfiltred.replace("-","")
                if telfiltred[0]=="0":
                    telfiltred=telfiltred[1:]

                if rec.acciones_venta_lines:

                    for id, elem in enumerate(rec.acciones_venta_lines):
                        if id==0:



                            text+="Cliente N°%i:\n"%h0
                            text+="ID: %s\n"%rec.id
                            text+="Nombre: %s\n"%rec.name
                            text+="telefono: %s\n"%telfiltred


                            text+="\n___________________________________________\n\n\n"
                            h0+=1
                else:

                    text += "Cliente N°%i:\n" % h0
                    text += "ID: %s\n" % rec.id
                    text += "Nombre: %s\n" % rec.name
                    text += "telefono: %s\n" % telfiltred

                    text += "___________________________________________\n\n\n"
                    h0 += 1


        #datexp = self.env['abatar.textos.wsp'].search([('name', '=', 'Mudanza (resolvió?)')], limit=1)
        #datprint = rec.cambio_textos_crm(rec, datexp)
        text += "\nMensaje para Envío:\n%s" % text2  # datprint

        success, rta=enviar_mensajegral({'data':text})
        fields.Glog('Envio de AGENDA AUTOMATICA a N8N :')
        fields.Glog(text)
        fields.Glog('rta:'+str(success)+' - msj:'+str(rta))



    @api.onchange('fecha_ejecucion')
    def set_previa_name(self):
        for rec in self:
            text=''
            text2=''
            if rec.fecha_ejecucion:
                prevday=rec.fecha_ejecucion-timedelta(hours=3)-timedelta(days=1)
                text2=(rec.fecha_ejecucion-timedelta(hours=3)-timedelta(days=1)).strftime('%d/%m/%Y')
                text=(rec.fecha_ejecucion-timedelta(hours=3)).strftime('%d/%m/%Y - %H:%M')

                dias={
                    calendar.weekday(2023, 4,3):'Lun',
                    calendar.weekday(2023, 4,4):'Mar',
                    calendar.weekday(2023, 4,5):'Mie',
                    calendar.weekday(2023, 4,6):'Jue',
                    calendar.weekday(2023, 4,7):'Vie',
                    calendar.weekday(2023, 4,8):'Sab',
                    calendar.weekday(2023, 4,9):'Dom',
                }
                if prevday.weekday():
                    text2=dias[prevday.weekday()]+' '+text2
                rec.fecha_previa_name=text2
                if rec.fecha_ejecucion.weekday():
                    text = dias[rec.fecha_ejecucion.weekday()] + ' ' + text
                rec.fecha_ejecucion_name = text



    def set_admin(self):
        for rec in self:
            if rec.env.user.id==2:
                rec.admin=True
            else:
                rec.admin=False


    @api.depends('recontactar')
    def set_days_recontactar(self, todos=False):
        #if todos:
        #    reco=self.env['abatar.crm'].search([])
        #else:
        #    reco=self
        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
        _logger.error('YOGASTONADM: set_days_recontactar')
        #if MJSLOG:
        for rec in self:
            ult=rec.acciones_venta_lines.search([('crm_id', '=', rec.id)], order='id desc', limit=1)

            if rec.recontactar:
                if ult:
                    ult.write({'vto_f': (rec.recontactar-ult.fecha).days})
                rec.recontactar_days = abs((rec.recontactar - fields.Date.today()).days)
            else:
                rec.recontactar_days = -2


    @api.onchange('active')
    def quit_calend(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: quit_calend')
        for rec in self:
            if rec.active:
                pass
            else:
                if rec.calendario:
                    cal=self.env['abatar.calendario'].search([('id', '=', rec.calendario.id)])
                    h=0
                    for res in cal.calendario_lines:
                       h+=1
                    for res in cal.calendario_lines:
                        if res.crm.id==rec.id:
                            res.unlink()
                            if h==1:
                                cal.unlink()
                    rec.calendario=False

    @api.depends('mas_iva','precio')
    def set_precio_mas_iva(self):
        for rec in self:
            if rec.mas_iva:
                if rec.precio:
                    rec.precio_mas_iva=rec.precio*1.21
            else:
                rec.precio_mas_iva=rec.precio


    @api.depends('costos_total','precio')
    def set_ganancia(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_ganancia')
        for rec in self:
            if rec.costos_total:
                if rec.precio:
                    rec.ganancia_neta=rec.precio - rec.costos_total
                    rec.ganancia_neta_pc=round((rec.precio - rec.costos_total)/rec.precio, 2)
                    rec.ganancia_bruto=rec.precio_mas_iva - rec.costos_total
                    rec.ganancia_bruto_pc=round((rec.precio_mas_iva - rec.costos_total)/rec.precio_mas_iva, 2)



    @api.depends('precio', 'costos_total', 'fecha_ejecucion')
    def set_dolar(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_dolar')
        for rec in self:
            if rec.fecha_ejecucion:
                subtotal_neto=0
                subtotal_bruto=0
                costos=0
                subtotal_dolar_neto=0
                subtotal_dolar_bruto=0
                costos_dolar=0
                if rec.precio:
                    subtotal_neto=rec.precio
                if rec.precio_mas_iva:
                    subtotal_bruto=rec.precio_mas_iva
                if rec.costos_total:
                    costos=rec.costos_total
                fecha_orden= str(fields.Date.from_string(rec.fecha_ejecucion).strftime('%d/%m/%y'))
                dia_ejec=int(fecha_orden[:fecha_orden.find('/')])
                rest=fecha_orden[fecha_orden.find('/')+1:]
                mes_ejec=int(rest[:rest.find('/')])
                rest2=rest[rest.find('/')+1:]
                año_ejec=2000+int(rest2[:])

                actu=self.env['abatar.dolar'].search([('fecha', '=', fields.Date.from_string(rec.fecha_ejecucion))], limit=1)
                if actu.pesos:
                    subtotal_dolar_neto=subtotal_neto/actu.pesos
                    subtotal_dolar_bruto=subtotal_bruto/actu.pesos
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
                            subtotal_dolar_neto=subtotal_neto/actu.pesos
                            subtotal_dolar_bruto=subtotal_bruto/actu.pesos
                            costos_dolar = costos / actu.pesos
                            rec.dolar_uso=actu.pesos

                    if subtotal_dolar_neto==0 and subtotal_neto:
                        actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                        if actu.pesos:
                            subtotal_dolar_neto = subtotal_neto / actu.pesos
                    if subtotal_dolar_bruto==0 and subtotal_bruto:
                        actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                        if actu.pesos:
                            subtotal_dolar_bruto = subtotal_bruto / actu.pesos
                            costos_dolar = costos / actu.pesos
                            rec.dolar_uso=actu.pesos

                if subtotal_dolar_neto and subtotal_dolar_bruto:
                    rec.precio_dolar_neto=subtotal_dolar_neto
                    rec.precio_dolar_bruto=subtotal_dolar_bruto
                    rec.costos_dolar=costos_dolar
                    rec.ganancia_dolar_neto=subtotal_dolar_neto-costos_dolar
                    rec.ganancia_dolar_neto_pc=round((subtotal_dolar_neto-costos_dolar)/subtotal_dolar_neto, 2)
                    rec.ganancia_dolar_bruto=subtotal_dolar_bruto-costos_dolar
                    rec.ganancia_dolar_bruto_pc=round((subtotal_dolar_bruto-costos_dolar)/subtotal_dolar_bruto, 2)




    @api.depends('acciones_venta_lines')
    def set_ult_accion(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_ult_accion')
        for rec in self:
            if rec.acciones_venta_lines:
                ult=rec.acciones_venta_lines.search([('crm_id', '=', rec.id)], order='fecha desc, id desc', limit=1)

                if ult.desc:
                    rec.ult_accion=ult.venta_accion.name +'('+ ult.desc+')'
                else:
                    rec.ult_accion = ult.venta_accion.name
                rec.ult_fecha=ult.fecha

    def set_ult_accion_vencida(self):
        for rec in self:
            if rec.acciones_venta_lines:
                ult=rec.acciones_venta_lines.search([('crm_id', '=', rec.id)], order='fecha desc, id desc', limit=1)

                if ult.fecha+relativedelta(days=ult.vto_f)>=fields.Date.today():
                    if ult.rta not in ('si','no'):
                        image_path = modules.get_module_resource('om_abatartrucks', 'static/src/img', 'cruzno.png')
                        rec.vencido= tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))
                    else:
                        rec.vencido=False
                else:
                    rec.vencido=False
            else:
                rec.vencido=False


    @api.depends('cotizador')
    def set_pres(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_pres')
        print('SE llamo!')
        for rec in self:
            if rec.cotizador:
                op_pres=0
                ud_pres=''
                kms_pres=0
                emb_pres=0
                hs_pres=0
                for res in rec.cotizador.linea_personal:
                    if res.producto.tipo.name=='operario':
                        op_pres+=res.cantidad
                        hs_pres=res.horas
                    elif res.producto.tipo.name=='unidad':
                        ud_pres=res.producto.name
                        if res.kms:
                            kms_pres=res.kms

                if rec.cotizador.subto_embalaje:
                    emb_pres=rec.cotizador.subto_embalaje

            else:
                op_pres=0
                ud_pres=''
                kms_pres=0
                emb_pres=0
                hs_pres=0
            rec.op_pres=op_pres
            rec.ud_pres=ud_pres
            rec.kms_pres=kms_pres
            rec.emb_pres=emb_pres
            rec.hs_pres=hs_pres

    @api.onchange('es_conocido')
    def set_fdp(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_fdp')
        for rec in self:
            if rec.es_conocido=='si':
                rec.fdp_flete='Cuenta Corriente'
            else:
                rec.fdp_flete='Al Contado en efectivo.'

    @api.depends('destinos_lines','destinos_lines2')
    def set_destinos_resumen(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_destinos_resumen')
        print('he11')
        for r in self:

            r.destinos_resumen=' '
            r.pauta_gral=''
            if r.destinos_lines:
                for ai in r.destinos_lines:
                    if ai.destino_id.name_gral:
                        r.destinos_resumen+=str(ai.destino_id.name_gral)+ ' - '
                    if ai.pauta:
                        r.pauta_gral+=str(ai.pauta)+ ' - '
            if r.destinos_lines2:
                for ai in r.destinos_lines2:
                    if ai.destino:
                        r.destinos_resumen+=str(ai.destino)+ ' - '
                    if ai.pauta:
                        r.pauta_gral+=str(ai.pauta)+ ' - '
            if r.pauta_gral[-3:]==' - ':
                r.pauta_gral=r.pauta_gral[:-3]
            r.pauta_gral_pre = 'Servicio'
            if r.cotizador:
                aux_ud = False
                aux_op = False
                for res1 in r.cotizador.linea_personal:
                    if res1.producto.tipo.name == 'unidad':
                        aux_ud = True
                    elif res1.producto.tipo.name == 'operario':
                        aux_op = True
                if aux_ud == True:
                    if aux_op == True:
                        r.pauta_gral_pre += ' con Unidad Apta, Chofer y Operario/s para tareas de Carga, Traslado y Descarga.'
                    else:
                        r.pauta_gral_pre += ' con Unidad Apta y Chofer para tarea de Traslado.'
                else:
                    if aux_op == True:
                        if r.servicio.name in ('Mudanza', 'Operarios') and r.mdz_op_cyd:
                            r.pauta_gral_pre += ' con Operario/s para tareas de Carga y Descarga.'
                        elif r.servicio.name in ('Flete', 'Reparto') and r.cyd_flete:
                            r.pauta_gral_pre += ' con Operario/s para tareas de Carga y Descarga.'
                        else:
                            r.pauta_gral_pre += ' con Operario/s.'
            elif r.servicio.name == 'Mudanza':
                r.pauta_gral_pre += ' con Unidad Apta, Chofer y Operario/s para tareas de Carga, Traslado y Descarga.'

            elif r.servicio.name == 'Flete' or r.servicio.name == 'Reparto':
                if r.cyd_flete == True and r.cyd_autoelev == False:
                    r.pauta_gral_pre += ' con Unidad Apta, Chofer y Operario/s para tareas de Carga, Traslado y Descarga.'
                else:
                    r.pauta_gral_pre += ' con Unidad Apta y Chofer, para tarea de Traslado.'
            elif r.servicio.name == 'Operarios':
                r.pauta_gral_pre += ' con Operario/s.'
            else:
                r.pauta_gral_pre += '.'

            if r.servicio.name == 'Mudanza':
                if r.mdz_hay_emb_g or r.mdz_hay_emb_f:
                    r.pauta_gral_pre += ' Incluye'
                    if r.mdz_hay_emb_g:
                        r.pauta_gral_pre += ' tareas de Acondicionamiento del Mobiliario'
                        if r.mdz_hay_emb_f:
                            r.pauta_gral_pre += ' y el Guardado y Envasado del Contenido: Adornos, Vajilla y Libros (No incluye Ropa, blanco y mantelería. Obetos de valor no se responsabiliza la empresa por su robo o extravío)'

                        r.pauta_gral_pre += '.'
                    else:
                        if r.mdz_hay_emb_f:
                            r.pauta_gral_pre += ' tareas de Guardado y Envasado del Contenido: Adornos, Vajilla y Libros (No incluye Ropa, blanco y mantelería. Obetos de valor no se responsabiliza la empresa por su robo o extravío)'

                        r.pauta_gral_pre += '.'

                if r.mdz_hay_mg or r.mdz_hay_mf:
                    if r.mdz_hay_mg or r.mdz_hay_mf:
                        r.pauta_gral_pre += ' Incluye Materiales de Embalaje'
                        if r.mdz_hay_mg:
                            r.pauta_gral_pre += ' Grueso'
                            if r.mdz_hay_mf:
                                r.pauta_gral_pre += ' y Fino'
                        else:
                            if r.mdz_hay_mf:
                                r.pauta_gral_pre += ' Fino'

                        r.pauta_gral_pre += '.'
                if r.pauta_gral:
                    r.pauta_gral_pre += ' '+r.pauta_gral



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



    @api.depends('fecha_ejecucion')
    def set_fecha2(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_fecha2')
        print('he12')
        for rec in self:
            if rec.fecha_ejecucion:
                rec.fecha_ejecucion2=datetime.strptime(rec.fecha_ejecucion.strftime('%d-%m-%Y'), '%d-%m-%Y').date()


    @api.one
    @api.depends('factura')
    def set_facturado(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_facturado')
        print('he13')
        if self.factura:
            self.facturado=self.env['abatar.booleana'].search([('name', '=', 'Facturado')]).id
        else:
            self.facturado=self.env['abatar.booleana'].search([('name', '=', 'No Facturado')]).id



    @api.depends('mdz_amb','mdz_carga','m3_flete')
    def set_m3_auto(self):
        print('he14')

        for rec in self:
            if rec.mdz_amb:
                if rec.mdz_carga:
                    rec.mdz_m3_auto=round(rec.mdz_amb*rec.mdz_carga, 2)
            elif rec.servicio.name=="Flete" or rec.servicio.name=="Reparto":
                if rec.m3_flete:
                    rec.mdz_m3_auto=rec.m3_flete

    def set_sin_atender(self):
        for rec in self:
            rec.sin_atender = not rec.sin_atender

    def state_pendiente(self):
        print('he19')
        valor_pausado = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Pausado')])
        valor_pendiente = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Pendiente')])

        for rec in self:
            rec.estado = valor_pendiente.id
            rec.estado_presupuesto = valor_pausado.id

            rec.message_post(body=_("La orden volvio a estado: Pendiente"))

    def state_confirmado(self):
        print('he20')


        valor_confirmado = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Confirmado')])
        valor_vigente = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Confirmado')])

        for rec in self:
            rec.fecha_confirmacion = fields.datetime.now().date()
            if rec.estado:
                rec.estado = valor_confirmado.id
            if rec.estado_presupuesto != valor_vigente.id:
                rec.estado_presupuesto = valor_vigente.id

        self.message_post(body=_("La orden pasó a estado: Confirmado"))
    def state_finalizado(self):
        print('he21')


        valor_pendiente = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Finalizado')])

        for rec in self:
            if not rec.confirmado_para_resumen:
                ordenes=self.env['abatar.ordenes'].search([('crm', '=', rec.id)])
                notin=''
                for orden in ordenes:
                    if orden.state=='finalizado':
                        pass
                    else:
                        notin+=orden.name_gral+', '
                if notin != '':
                    raise UserError(_('Debe Finalizar Todas las Ordenes que tiene este CRM para poder finalizar el pedido. Faltan las ordenes %s' % notin))
                else:
                    pass
                if rec.estado:
                    rec.estado = valor_pendiente.id
            else:
                if rec.estado:
                    rec.estado = valor_pendiente.id
                rec.active=False
        self.message_post(body=_("La orden ha pasado a estado: Finalizado"))
    '''def state_rechazado(self):
        print('he22')

        valor_rechazado = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Rechazado')])
        valor_vigente = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Cancelado')])

        for rec in self:
            if rec.estado:
                rec.estado = valor_rechazado.id
            if rec.estado_presupuesto != valor_vigente.id:
                rec.estado_presupuesto = valor_vigente.id

        self.message_post(body=_("La orden pasó a estado: Rechazado"))'''
    def state_pendiente(self):

        valor_pendiente = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Pendiente')])
        valor_pausado = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Pausado')])

        if self.env['abatar.ordenes'].search([('crm', '=', self.id)]):
            for ordenes in self.env['abatar.ordenes'].search([('crm', '=', self.id), ('active', 'in', (True, False))]):
                if ordenes.servicio.name!='Visita Tecnica':
                    if ordenes.state=='finalizo':
                        raise UserWarning('No puedes volver a Pendiente un pedido que ya tiene ordenes finalizadas')
                    ordenes.unlink()

        self.estado = valor_pendiente.id
        self.active=True

        if self.estado_presupuesto != valor_pausado.id:
            self.estado_presupuesto = valor_pausado.id

        self.message_post(body=_("La orden volvió a estado: Pendiente"))

    def state_cancelado_f(self):
        print('he24')

        valor_pendiente = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Confirmado')])

        for rec in self:
            rec.estado = valor_pendiente.id
            rec.state = 'confirmado'
            rec.factura.unlink()
            rec.factura=False

            rec.message_post(body=_("La orden volvió a estado: Confirmado"))

    def state_reactivar(self):
        print('he24')

        valor_pendiente = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Pendiente')])

        ordenes=''
        try:
            if self.ensure_one():
                ordenes=self.pedide
                self.estado = valor_pendiente.id
                self.state = "pendiente"
                self.message_post(body=_("La orden %s volvió a estado: Pendiente" % ordenes))
            else:
                for rec in self:
                    ordenes += rec.pedide + ', '
                    rec.estado = valor_pendiente.id
                    rec.state = "pendiente"
                self.message_post(body=_("Las ordenes %s volvieron a estado: Pendiente" % ordenes))
        except:
            for rec in self:
                ordenes+=rec.pedide+', '
                rec.estado = valor_pendiente.id
            self.message_post(body=_("Las ordenes %s volvieron a estado: Pendiente" % ordenes))

    def state_cancelado_p(self):


        valor_cancelado = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Cancelado')])

        for rec in self:
            if rec.estado:
                rec.estado = valor_cancelado.id
            if rec.state:
                rec.state = 'cancelado'


        self.message_post(body=_("La/s orden/es pasaron a estado: Cancelado"))


    def state_presupuesto(self):


        guarda = self.search([
            ('recontactar', '<=', fields.Date.to_string(date.today() - relativedelta(days=7)))
        ])
        valor_pausado = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Pausado')])
        valor_vigente = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Vigente')])

        for rec in self:
            if rec.precio == 0:
                if not rec.cotizador:
                    raise UserError(_("Para pasar a estado PRESUPUESTO debes haber enviado un precio al cliente,"
                                      "El Precio Orientación (sin IVA) que se le halla enviado al cliente debe ser colocado"
                                      "en el campo llamado PRECIO."
                                      "Si no sabes el precio puedes presionar el Boton ubicado arriba a la derecha"
                                      "para CREAR COTIZACION, y obtendrás un número que puedes estimar como PRECIO ORIENTACION."))
                else:
                    raise UserError(_("Completa el Campo PRECIO para definir el Precio Orientacion (Sin IVA)."))
            elif rec.recontactar == False :
                raise UserError(_("Tiene que poner una fecha de Recontacto."))
            else:
                valor_presupuesto = self.env['abatar.servicios.estados'].search(
                    [('name', '=', 'Presupuesto')])
                if rec.estado:
                    rec.estado = valor_presupuesto.id
                if rec.state:
                    rec.state = 'presupuesto'
                rec.fecha_presupuesto = date.today()

                if rec.recontactar > date.today() + relativedelta(days=7):
                    rec.estado_presupuesto = valor_pausado
                else:
                    rec.estado_presupuesto = valor_vigente

                self.message_post(body=_("La orden paso a estado: Presupuesto"))


    def cuenta_ordenes(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: cuenta_ordenes')
        print('he26')
        for rec in self:
            count = rec.env['abatar.ordenes'].search_count([('crm', '=', rec.id),('active', 'in', (True, False))])
            rec.ordenes_r = count
            resul=rec.env['abatar.ordenes'].search([('crm', '=', rec.id),('active', 'in', (True, False))])
            costo=0
            if resul:
                for res in resul:
                    costo += res.costos

            rec.write({'costos_total':costo})


    @api.depends('name', 'state', 'cliente', 'precio')
    def cuenta_ordenes2(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: cuenta_ordenes2')
        print('he17')
        for rec in self:
            if rec.factura:
                rec.estado_mdz='FIN'
            elif rec.facturado.name=='Facturado':
                rec.estado_mdz='COBRAR'
            elif self.env['abatar.ordenes'].search([('crm', '=', rec.id), ('servicio', '=', self.env['abatar.servicios.calendario'].search([('name', '=', 'Mudanza')], limit=1).id)], limit=1):
                rec.estado_mdz='FACT'
            elif self.env['abatar.ordenes'].search([('crm', '=', rec.id), ('servicio', '=', self.env['abatar.servicios.calendario'].search([('name', '=', 'Previa')], limit=1).id)], limit=1):
                rec.estado_mdz='MDZ'
            elif self.env['abatar.ordenes'].search([('crm', '=', rec.id), ('servicio', '=', self.env['abatar.servicios.calendario'].search([('name', '=', 'Entrega de Materiales')], limit=1).id)], limit=1):
                rec.estado_mdz='PV'
            elif rec.state=='confirmado':
                if rec.mdz_hay_mg!=False or rec.mdz_hay_mg!=False:
                    if self.env['abatar.ordenes'].search([('crm', '=', rec.id), ('servicio', '=', self.env['abatar.servicios.calendario'].search([('name', '=', 'Visita Tecnica')], limit=1).id)], limit=1):
                        rec.estado_mdz='EM'
                    else:
                        rec.estado_mdz = 'PV/TRAS/MDZ'
            elif rec.state=='pendiente':
                if rec.mdz_carga and rec.mdz_categ:
                    rec.estado_mdz='PRESUP.'
                else:
                    rec.estado_mdz='FALTAN DATOS'

    @api.multi
    def action_view_cotizador(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.cotizador',
            'res_id': self.cotizador.id,
        }
    @api.one
    def action_view_cotizador_unlink(self):
        self.cotizador.unlink()
    @api.one
    def action_view_factura_unlink(self):
        self.factura.unlink()
    @api.multi
    def ordenes_cl(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: ordenes_cl')
        print('he16')
        return {
            'name': _('Ordenes'),
            'domain': [('crm', '=', self.id),('active', 'in', (True, False))],
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
    @api.depends('fecha_ejecucion')
    def set_fecha_sv_prox(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_fecha_sv_prox')
        for rec in self:
            if rec.fecha_ejecucion:
                guarda = self.search([
                    ('fecha_ejecucion', '<=', fields.Date.to_string(date.today() + relativedelta(days=4))),
                    ('fecha_ejecucion', '>', fields.Date.to_string(date.today()))
                ])

                cuenta = 0

                for dec in guarda:
                    if dec.id == rec.id:
                        cuenta += 1

                rec.fechasv_proximo = cuenta
    @api.depends('recontactar')
    def set_date_edit(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_date_edit')
        for rec in self:
            if rec.recontactar:
                rec.recontactar2 = fields.Datetime.to_string(rec.recontactar)
                rec.recontactar2 = fields.Datetime.to_string(rec.recontactar2 + timedelta(hours=10))

    @api.depends('precio','codigo','cotizador','adjuntos')
    def set_state(self):
        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: set_state')
        for rec in self:

            if not rec.desc_state:
                rec.desc_state = ''

            if not rec.precio > 0 and rec.state == 'pendiente':
                rec.desc_state = rec.desc_state + '- Falta precio \n'

            if not rec.codigo and rec.state == 'pendiente':
                rec.desc_state = rec.desc_state + '- Falta codigo \n'

            if not rec.cotizador and rec.state == 'pendiente':
                rec.desc_state = rec.desc_state + '- Falta cotizador \n'

            if not rec.adjuntos and rec.state == 'pendiente':
                rec.desc_state = rec.desc_state + '- Faltan Imagenes \n'

    @api.depends('registro_pagos','precio')
    def set_subtotal_pagos(self):
        for rec in self:
            for dec in rec.registro_pagos:
                rec.total_pagos += dec.monto
            rec.total_saldo=rec.precio_mas_iva-rec.total_pagos

    @api.onchange('email_cliente')
    def _check_email(self):
        for rec in self:
            rec.email = rec.email_cliente

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

    @api.onchange('cliente')
    def set_tel_cliente(self):
        for rec in self:
            rec.contacto = False

    @api.onchange('contacto')
    def set_tel_cliente(self):
        for rec in self:
            if rec.contacto:
                if rec.contacto.tel:
                    rec.tel_cliente = rec.contacto.tel
                    rec.tel = rec.tel_cliente
                if rec.contacto.email:
                    rec.email_cliente = rec.contacto.email
                if rec.cliente:
                    rec.name = rec.cliente.name_gral+' - '+rec.contacto.name
            else:
                if rec.cliente:
                    rec.name = rec.cliente.name_gral

    @api.multi
    def action_crea_orden(self):
        fecha_sv=fields.Datetime()
        if self.fecha_ejecucion:
            fecha_sv=self.fecha_ejecucion
        else:
            fecha_sv=fields.Datetime.now()
        if self.fecha_inicial:
            fecha_p=self.fecha_inicial
        else:
            fecha_p=fields.Datetime.now()
        vals2 = {
            'user_id': self.env.user.id,
            'fecha_pedido': fecha_p,
            'crm': self.id,
            'pedide': self.pedide,
            'fecha_ejecucion' : fecha_sv
        }

        if self.state in ('pendiente', 'presupuesto'):
            vals2.update(
                {
                    'servicio': 1,
                }
            )
        elif self.state == 'confirmado':
            try:
                sv0=self.env['abatar.servicios.calendario'].search([('name', '=', self.servicio.name)]).id
            except:
                h=0
                for bb in self.env['abatar.servicios.calendario'].search([('name', '=', self.servicio.name)]):
                   if h==0:
                       sv0 = bb.id

            vals2.update(
                {
                    'servicio': sv0,
                }
            )

        if self.es_conocido == 'si':
            vals2.update(
                {
                    'es_conocido': 'si',
                    'cliente': self.cliente.id,
                    'contacto': self.contacto.id,
                    'name' : self.cliente.clientes_gral_id.name,
                    'tel_cliente': self.tel_cliente,
                    'email_cliente': self.email_cliente,
                }
            )
        else:
            vals2.update(
                {
                    'es_conocido': 'no',
                    'empresa': self.empresa,
                    'name': self.name,
                    'tel': self.tel,
                    'email': self.email,
                }
            )

        resu = self.env['abatar.ordenes'].create(vals2)



        if self.destinos_lines:
            for ei in self.destinos_lines:
                vals1 = {
                    'destino_id': ei.destino_id.id,
                    'pauta': ei.pauta,
                    'destino_contacto': ei.destino_contacto,
                    'destino_tipo': ei.destino_tipo
                }

                resu.write({'destinos_lines': [(0, 0, vals1)]})

        if self.destinos_lines2:
            for ei in self.destinos_lines2:

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

                resu.write({'destinos_lines2': [(0, 0, vals1)]})

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.ordenes',
            'res_id': resu.id,
        }

    @api.multi
    def action_crea_calculadora(self):
        fields.Glog("aca1")
        #SECCION COMPROBACIONES----------##################################################

        #######################SECCION MUDANZAS----------##################################
        if self.servicio.name=='Mudanza':
            requerid=[self.mdz_ascensor_destino, self.mdz_ascensor_origen, self.mdz_amb,
                      self.mdz_categ, self.mdz_carga, self.mdz_pers]
            req_name=['mdz_ascensor_destino', 'mdz_ascensor_origen', 'mdz_amb',
                      'mdz_categ', 'mdz_carga', 'mdz_pers']
            h=0
            for req in requerid:
                if req:
                    pass
                else:
                    raise UserError('Para iniciar un cotizador necesitas llenar los datos del formulario, falta %s -  valor: %s' % (str(req_name[h]),str(req)))
                h+=1
        if self.servicio.name=='Flete' or self.servicio.name=='Reparto':
            requerid=[[self.m3_flete,self.kgs_flete], [self.destinos_lines,self.destinos_lines2]]
            req_name=[['m3_flete', 'kgs_flete'], ['destinos_lines','destinos_lines2']]
            h=0
            for req in requerid:
                if type(req)!=list:
                    if req:
                        pass
                    else:
                        raise UserError('Para iniciar un cotizador necesitas llenar los datos del formulario, falta %s - valor: %s' % (str(req_name[h]),str(req)))
                else:
                    salta=False
                    strerror=[]
                    j=0
                    for req2 in req:
                        if req2:
                            salta=True
                        else:
                            strerror.append(req2)
                            pass
                        j+=1
                    if salta==True:
                        pass
                    else:
                        raise UserError('Para iniciar un cotizador necesitas llenar los datos basicos, falta %s - valor: %s' % (str(req_name[h][j]), str(strerror)))
                h+=1
        fields.Glog("aca2")
        ####################### CREA COTIZADOR----------##################################
        ivainc=self.env['abatar.constantes'].search([('name','=','COTIZ_ESIVAINC')]).booleano
        fields.Glog("aca3")
        if self.es_conocido=='si':
            ivainc=False
        vals2 = {
            'crm': self.id,
            'es_ivainc': ivainc,
        }
        fields.Glog("aca4")
        resu = self.env['abatar.cotizador'].create(vals2)
        fields.Glog("aca5")
        self.cotizador = resu.id
        BSAS_list=['BS AS', 'BS. AS.', 'BSAS', 'BUENOS AIRES']
        CABA_list=['CABA','C.A.B.A.','CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTONOMA DE BS AS','CIUDAD AUTONOMA DE BS. AS.', 'CIUDAD AUTÓNOMA DE BUENOS AIRES', 'CAPITAL']
        #SECCION MUDANZA----------##################################################
        if self.servicio.name=='Mudanza':

            CATEG = self.mdz_categ#'C'= -15% - 'B'= 0% - 'A'= +15% - 'AA'= +25%
            AMB = self.mdz_amb# 3
            PERS =  self.mdz_pers#4

            NV_CARGA =  self.mdz_carga#6  # Nivel de carga cant de m3 por amb,  6 = poca, 7 = media u 8 = ocho

            h = 0
            ORIGEN = ''
            DESTINO = ''
            PISO_O=0
            PISO_D=0
            HAYPROV=0
            origen_prov=0
            destino_prov=0
            if self.es_conocido=='no':
                for rec in self.destinos_lines2:
                    rec.provincia=comprostrclean(rec.provincia)
                    rec.localidad=comprostrclean(rec.localidad)
                    if h==0:
                        if rec.destino:
                            ORIGEN = rec.destino+', '+rec.localidad
                        else:
                            ORIGEN =rec.localidad

                        if rec.provincia.upper() not in  CABA_list+BSAS_list:
                            ORIGEN+=', '+rec.provincia
                            origen_prov=1

                        if rec.localidad.upper() not in CABA_list:
                            origen_prov=1

                        if rec.piso:
                            PISO_O = rec.piso
                    elif h==len(self.destinos_lines2)-1:

                        if rec.destino:
                            DESTINO = rec.destino+', '+rec.localidad
                        else:
                            DESTINO =rec.localidad
                        if rec.provincia.upper() not in CABA_list+BSAS_list:
                            DESTINO+=', '+rec.provincia
                            destino_prov=1

                        if rec.localidad.upper() not in CABA_list:
                            destino_prov=1
                        if rec.piso:
                            PISO_D = rec.piso
                    h+=1
            else:

                for rec in self.destinos_lines:

                    rec.provincia=comprostrclean(rec.provincia)
                    rec.localidad=comprostrclean(rec.localidad)
                    if rec.destino_id:
                        if h == 0:
                            if rec.destino_id.name:
                                ORIGEN = rec.destino_id.name+', '+rec.destino_id.localidad
                            else:
                                ORIGEN =rec.destino_id.localidad
                            if rec.destino_id.provincia.upper() not in BSAS_list+CABA_list:
                                ORIGEN+=', '+rec.destino_id.provincia

                            if rec.destino_id.provincia.upper() in CABA_list:
                                pass
                            else:
                                if rec.destino_id.localidad.upper() not in CABA_list:
                                    origen_prov=1
                                if rec.destino_id.provincia.upper() not in BSAS_list:
                                    origen_prov=1
                            if rec.destino_id.piso:
                                PISO_O = rec.destino_id.piso
                        elif h == len(self.destinos_lines2) - 1:
                            if rec.destino_id.name:
                                DESTINO = rec.destino_id.name+', '+rec.destino_id.localidad
                            else:
                                DESTINO =rec.destino_id.localidad
                            if rec.destino_id.provincia.upper() in CABA_list or rec.localidad.upper() in CABA_list:
                                pass
                            else:
                                if rec.destino_id.localidad.upper() not in CABA_list:
                                    destino_prov = 1
                                if rec.destino_id.provincia.upper() not in BSAS_list:
                                    destino_prov = 1
                            if rec.destino_id.piso:
                                PISO_D = rec.destino_id.piso
                    h += 1
            fields.Glog("aca6")
            ASC_ORI=2
            if self.mdz_ascensor_origen:
                if self.mdz_ascensor_origen == '1':
                    ASC_ORI = 0
                elif self.mdz_ascensor_origen == '2':
                    ASC_ORI = 1
                elif self.mdz_ascensor_origen == '3':
                    ASC_ORI = 2
                elif self.mdz_ascensor_origen == '4':
                    ASC_ORI = 3

            ASC_DEST=2
            if self.mdz_ascensor_destino:
                if self.mdz_ascensor_destino=='1':
                    ASC_DEST=0
                elif self.mdz_ascensor_destino=='2':
                    ASC_DEST=1
                elif self.mdz_ascensor_destino=='3':
                    ASC_DEST=2
                elif self.mdz_ascensor_destino=='4':
                    ASC_DEST=3

            HAYMG = self.mdz_hay_mg
            HAYMF = self.mdz_hay_mf

            HAYEMBFINO = self.mdz_hay_emb_f
            HAYEMBGRUESO = self.mdz_hay_emb_g

            if destino_prov==1 or origen_prov==1:
                HAYPROV=1


            fields.Glog("aca7")
            doble,kms,KM_ORI, Ej, CATEG_TXT, COC=FormMDZ(self, CATEG, AMB, PERS, NV_CARGA, ORIGEN, DESTINO, PISO_O, ASC_ORI, PISO_D, ASC_DEST, HAYMG, HAYMF,
                HAYEMBFINO, HAYEMBGRUESO, HAYPROV, origen_prov, destino_prov)
            fields.Glog("aca8")
            self.codigo=CATEG_TXT
            if doble>1:
                cant_ud_op=doble
            else:
                cant_ud_op=1
            fields.Glog("aca9")
            prod_op=self.env['abatar.productos'].search([('name', '=', 'Operario')], limit=1)
            if Ej[1]=='C':
                prod_ud=self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
                prod_ud_COC=self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
            elif Ej[1]=='D':
                prod_ud=self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
                prod_ud_COC=self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
            elif Ej[1]=='E':
                prod_ud=self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
                prod_ud_COC=self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
            elif Ej[1]=='F':
                prod_ud=self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
                prod_ud_COC=self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)
            elif Ej[1]=='FF':
                prod_ud=self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)

            fields.Glog("aca10")
            tarifa_gener=self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)
            tar_ud=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
            if Ej[1]!='FF' and COC_PROG == True:
                tar_ud_COC = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud_COC.id)], limit=1)
                precio_ud = (tar_ud.tarifas_precio + COC * (tar_ud_COC.tarifas_precio - tar_ud.tarifas_precio))
                costo_ud = tar_ud.tarifas_costo(tar_ud) + COC * (tar_ud_COC.tarifas_costo(tar_ud_COC) - tar_ud.tarifas_costo(tar_ud))
            else:
                precio_ud = tar_ud.tarifas_precio
                costo_ud = tar_ud.tarifas_costo(tar_ud)

            tar_op = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_op.id)], limit=1)
            precio_op = tar_op.tarifas_precio
            costo_op = tar_op.tarifas_costo(tar_op)


            tar_ud_kms = tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
            if  Ej[1]!='FF' and COC_PROG == True:
                tar_ud_kms_COC = tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud_COC.id)], limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio + COC * (tar_ud_kms_COC.tarifas_precio - tar_ud_kms.tarifas_precio)
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms) + COC * (tar_ud_kms_COC.tarifas_costo(tar_ud_kms_COC) - tar_ud_kms.tarifas_costo(tar_ud_kms))
            else:
                tar_ud_kms = tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)

            fields.Glog("aca11")

            op_pv=Ej[3]
            hs_op_pv=redond(Ej[4])
            op_tras=Ej[5]
            hs_op_tras = redond(Ej[6])
            hs_ud_tras = redond(Ej[7])

            if self.mdz_acarreo2_des:
                hs_op_tras += 0.5
                hs_ud_tras += 0.5
            if self.mdz_acarreo2_ori:
                hs_op_tras += 0.5
                hs_ud_tras += 0.5
            if self.mdz_acarreo_des:
                hs_op_tras += 1
                hs_ud_tras += 1
            if self.mdz_acarreo_ori:
                hs_op_tras += 1
                hs_ud_tras += 1

            dtring=str(doble)
            fields.Glog("aca12")
            resu.write({'linea_personal':[(0, 0, {'producto':prod_ud.id,
                                                  'desc':'UD TRASLADOS x %s' % dtring,
                                                  'horas':hs_ud_tras,
                                                  'kms':kms,
                                                  'cantidad':doble,
                                                  'precio_f':precio_ud,
                                                  'precio_kms_f':precio_ud_kms,
                                                  'cotizador_id':self.cotizador.id,
                                                  })]})
            fields.Glog("aca13")
            resu.write({'linea_personal':[(0, 0, {'producto':prod_op.id,
                                                  'desc':'OP TRASLADOS x %s' % dtring,
                                                  'horas':hs_op_tras,
                                                  'cantidad':op_tras*doble,
                                                  'cotizador_id':self.cotizador.id,
                                                  })]})
            if op_pv==0 or hs_op_pv==0:
                pass
            else:
                resu.write({'linea_personal':[(0, 0, {'producto':prod_op.id,
                                                  'desc':'OP PREVIA x %s' % dtring,
                                                  'horas':hs_op_pv,
                                                  'cantidad':op_pv*doble,
                                                  'cotizador_id':self.cotizador.id,
                                                  })]})
            fields.Glog("aca14")
            prod_caja1=self.env['abatar.productos'].search([('name', '=', 'Cajas N°1')], limit=1)
            prod_caja2=self.env['abatar.productos'].search([('name', '=', 'Cajas N°2')], limit=1)
            prod_caja3=self.env['abatar.productos'].search([('name', '=', 'Cajas N°3')], limit=1)
            prod_pluribol=self.env['abatar.productos'].search([('name', '=', 'Pluriboll')], limit=1)
            prod_st_gde=self.env['abatar.productos'].search([('name', '=', 'Streech Grande')], limit=1)
            prod_st_chi=self.env['abatar.productos'].search([('name', '=', 'Streech Chico')], limit=1)
            prod_bolsones=self.env['abatar.productos'].search([('name', '=', 'Bolsones')], limit=1)
            prod_c_emp=self.env['abatar.productos'].search([('name', 'ilike', 'Cintas de Embalar%')], limit=1)
            prod_c_fragil=self.env['abatar.productos'].search([('name', '=', 'Fragil')], limit=1)
            prod_flete=self.env['abatar.productos'].search([('name', '=', 'Flete Entrega')], limit=1)
            prod_papel=self.env['abatar.productos'].search([('name', '=', 'Papel Blanco')], limit=1)
            prod_bolsa=self.env['abatar.productos'].search([('name', '=', 'Bolsa Camiseta')], limit=1)
            prod_cajaP=self.env['abatar.productos'].search([('name', '=', 'Cajas de Proteccion')], limit=1)
            fields.Glog("aca15")
            precio_caja1=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja1.id)], limit=1).tarifas_precio
            precio_caja2=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja2.id)], limit=1).tarifas_precio
            precio_caja3=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja3.id)], limit=1).tarifas_precio
            precio_pluribol=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)], limit=1).tarifas_precio
            precio_st_gde=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)], limit=1).tarifas_precio
            precio_st_chi=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)], limit=1).tarifas_precio
            precio_bolsones=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_bolsones.id)], limit=1).tarifas_precio
            precio_c_emp=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)], limit=1).tarifas_precio
            precio_c_fragil=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_fragil.id)], limit=1).tarifas_precio
            precio_flete=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)], limit=1).tarifas_precio
            precio_papel=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_papel.id)], limit=1).tarifas_precio
            precio_bolsa=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_bolsa.id)], limit=1).tarifas_precio
            precio_cajaP=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_cajaP.id)], limit=1).tarifas_precio

            costo_caja1=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja1.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja1.id)], limit=1))
            costo_caja2=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja2.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja2.id)], limit=1))
            costo_caja3=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja3.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_caja3.id)], limit=1))
            costo_pluribol=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)], limit=1))
            costo_st_gde=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)], limit=1))
            costo_st_chi=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)], limit=1))
            costo_bolsones=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_bolsones.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_bolsones.id)], limit=1))
            costo_c_emp=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)], limit=1))
            costo_c_fragil=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_fragil.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_fragil.id)], limit=1))
            costo_flete=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)], limit=1))
            costo_papel=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_papel.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_papel.id)], limit=1))
            costo_bolsa=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_bolsa.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_papel.id)], limit=1))
            costo_cajaP=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_cajaP.id)], limit=1).tarifas_costo2#(tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_papel.id)], limit=1))

            prods_emb=[prod_caja1, prod_caja2, prod_caja3, prod_pluribol, prod_st_gde,
                       prod_st_chi, prod_bolsones, prod_c_emp, prod_c_fragil, prod_flete, prod_papel, prod_bolsa, prod_cajaP]
            precios_emb = [precio_caja1, precio_caja2, precio_caja3, precio_pluribol, precio_st_gde,
                         precio_st_chi, precio_bolsones, precio_c_emp, precio_c_fragil, precio_flete, precio_papel, precio_bolsa, precio_cajaP]
            costos_emb = [costo_caja1, costo_caja2, costo_caja3, costo_pluribol, costo_st_gde,
                         costo_st_chi, costo_bolsones, costo_c_emp, costo_c_fragil, costo_flete, costo_papel, costo_bolsa, costo_cajaP]
            cant_emb=[int(Ej[2][0]/3), int(Ej[2][0]/3), int(Ej[2][0]/3),
                      Ej[2][3],Ej[2][3],Ej[2][3],int(Ej[2][0]/4),Ej[2][2],1,max(5, KM_ORI),min(max(2,AMB), 7), 1, int(Ej[2][0]/3)]
            fields.Glog("aca16")
            for i in range(len(prods_emb)):

                resu.write({'embalaje_lines':[(0, 0, {'embalaje_id':prods_emb[i].id,
                                                      'cantidad':cant_emb[i],
                                                      'precio':precios_emb[i],
                                                      'costo':costos_emb[i],
                                                      'cotizador_id':self.cotizador.id,
                                                      })]})
                fields.Glog("aca17: %i"%i)
            aum=0
            if CATEG=="C":
                aum=-15
            elif CATEG=="B":
                aum=0
            elif CATEG=="A":
                aum=15
            elif CATEG=="AA":
                aum=25
            resu.aumento=aum
            resu.hay_categ=CATEG
        #SECCION MUDANZA----------##################################################
        #SECCION FLETE----------##################################################
        if self.servicio.name == 'Flete' or self.servicio.name == 'Reparto':
            opudc=1
            if self.servicio.name == 'Flete':
                opudc = 2
            AYD=0
            listud_m3=[5, 10,15, 20, 25, 35, 45]
            listud_kgs=[500, 1500,2500, 4500, 7500, 15000, 20000]
            listud_xdirec=[0.2,0.25, 0.3, 0.35, 0.4, 0.45, 0.45]
            listud_tipo=['A','B', 'C','D', 'E', 'F', 'FF']
            solocod=1
            adopec_l=[0  , 0  , 0  , 0  , 0 , 0  , 0]
            if self.cyd_flete==True:
                if self.cyd_forcop>0:
                    listud_cyd_op=[self.cyd_forcop  , self.cyd_forcop  , self.cyd_forcop, self.cyd_forcop, self.cyd_forcop, self.cyd_forcop, self.cyd_forcop  ]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 1, 1.5, 2, 2.5]
                elif self.cyd_minop>0:
                    listud_cyd_op=[ max([1,self.cyd_minop]), max([1,self.cyd_minop]) ,  max([opudc,self.cyd_minop])  , max([2,self.cyd_minop])  , max([3,self.cyd_minop]), max([4,self.cyd_minop]), max([6,self.cyd_minop])  ]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 1, 1.5, 2, 2.5]
                elif self.cyd_emb_grueso==True:
                    listud_cyd_op=[2  , 2  , 2  , 2  , 3, 4, 6  ]
                    listud_cyd_hs=[0.75, 1, 1.25, 2.25, 3, 3, 4]

                    adopec_l=[0.45, 0.5, 0.25, 0.75, 1,1, 1.5]
                elif self.cyd_autoelev==True:
                    listud_cyd_op=[0  , 0  , 0  , 0  , 0 , 0  , 0]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 0.75, 1, 1.5, 2]
                else:
                    listud_cyd_op=[1  ,1  ,opudc, 2  , 3, 4, 6  ]
                    listud_cyd_hs=[0.3,0.5,1, 1.5, 2, 2, 2.5]
                if self.cyd_solo_cod=='Carga' or self.cyd_solo_cod=='Descarga':
                    solocod=2
            else:
                listud_cyd_op=[0, 0, 0, 0, 0, 0, 0 ]
                listud_cyd_hs=[0.3,0.5,1, 1.5, 2, 2, 2.5]
            if not self.m3_flete:
                self.m3_flete=1
            if not self.kgs_flete:
                self.kgs_flete=1
            idef1=0
            for i in range(len(listud_m3)):
                if self.m3_flete<=listud_m3[i] or i==len(listud_m3)-1:
                    idef1=i
                    break
            idef2=0
            for i in range(len(listud_kgs)):
                if self.kgs_flete<=listud_kgs[i] or i==len(listud_kgs)-1:
                    idef2=i
                    break
            idef = max([idef1, idef2])
            COC=max([self.m3_flete/listud_m3[idef], self.kgs_flete/listud_kgs[idef]])
            ud_sv = listud_tipo[idef]
            if idef<len(listud_m3)-1 and COC_PROG==True:
                op_sv = (listud_cyd_op[idef]+int(COC*(listud_cyd_op[idef+1]-listud_cyd_op[idef])))
            else:
                op_sv = listud_cyd_op[idef]
            if idef<len(listud_m3)-1 and COC_PROG==True:
                hs_sv=((listud_cyd_hs[idef]+COC*(listud_cyd_hs[idef+1]-listud_cyd_hs[idef]))-(adopec_l[idef]+COC*(adopec_l[idef+1]-adopec_l[idef])))*2
                hs_sv_op=(adopec_l[idef]+COC*(adopec_l[idef+1]-adopec_l[idef]))*2
            else:
                hs_sv=(listud_cyd_hs[idef]-adopec_l[idef])*2
                hs_sv_op=adopec_l[idef]*2
            PISOS=[]
            B_PISOS=[]
            S_PISOS=[]
            HAYPROV=0
            TIEMPO_REC=0
            KMS=0
            KMS00=0
            if self.mdz_tiempo_rec:
                hs_sv+=self.mdz_tiempo_rec
                if self.mdz_kms_rec:
                    HAYPROV=1
                    KMS=self.mdz_kms_rec

                if self.es_conocido=='si':
                    for dest in self.destinos_lines:
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                else:
                    for dest in self.destinos_lines2:
                        if dest:
                            hs_sv+=listud_xdirec[idef]
            else:
                if self.es_conocido=='si':
                    print('Si!')
                    h=0
                    hmax=len(self.destinos_lines)
                    for dest in self.destinos_lines:
                        print('dest', dest)
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'

                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name+', '+dest.destino_id.localidad
                                    else:
                                        DESTINO =dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in  ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO+=', '+dest.destino_id.provincia
                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            destino_prov=1
                                            HAYPROV=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            destino_prov=1
                                            HAYPROV=1

                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)
                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        destino_prov = 1
                                        HAYPROV=1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd
                                if IMPRIME_CALCULA_DIST==True:
                                    self.write({'desc1':self.desc1+'\n'+des})
                                if destino_prov==1 and self.convenio=='cc':
                                    KMS+=KMS00
                                    self.write({'desc1':self.desc1+'\n'+'%.1f kms al origen incluidos en kms total.' % KMS00})

                                #Desactivo que si empieza en provincia cobra kms hasta el origen
                                #if destino_prov==1:
                                #    tiempo_oyd, distance_oyd, des = calcula_distancia(self, ORIGEN, DESTINO)
                                #    KMS+=distance_oyd
                                if dest.destino_id.piso and not dest.autoelev:
                                    PISOS.append(dest.destino_id.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                            if h>0 :
                                if hant:

                                    if hant.destino_id.forc_direc:
                                        ORIGEN = hant.destino_id.forc_direc
                                    else:
                                        if hant.destino_id.name:
                                            ORIGEN = hant.destino_id.name + ', ' + hant.destino_id.localidad
                                        else:
                                            ORIGEN = hant.destino_id.localidad
                                        if hant.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            ORIGEN += ', ' + hant.destino_id.provincia



                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name + ', ' + dest.destino_id.localidad
                                    else:
                                        DESTINO = dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO += ', ' + dest.destino_id.provincia


                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1


                                if dest.destino_id.piso and not dest.autoelev:
                                    PISOS.append(dest.destino_id.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                                print('o y d', ORIGEN, DESTINO)
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO) ACA 24-2
                                time.sleep(1)
                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    self.write({'desc1':self.desc1+'\n'+des})
                            h += 1
                            hant =dest



                else:
                    print('else')
                    h=0
                    hmax=len(self.destinos_lines2)
                    for dest in self.destinos_lines2:
                        print('dest', dest)
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'
                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia


                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1
                                #    destino_prov=1
                                #    HAYPROV=1
                                #if dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                #    destino_prov=1
                                #    HAYPROV=1

                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                if IMPRIME_CALCULA_DIST==True:
                                    self.write({'desc1':self.desc1+'\n'+des})
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd


                                if dest.piso and not dest.autoelev:
                                    PISOS.append(dest.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                            if h>0 :
                                if hant:

                                    if hant.forc_direc:
                                        ORIGEN = hant.forc_direc
                                    else:
                                        if hant.destino:
                                            ORIGEN = hant.destino+', '+hant.localidad
                                        else:
                                            ORIGEN =hant.localidad
                                        if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            ORIGEN+=', '+hant.provincia

                                        if hant.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and hant.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                                HAYPROV = 1
                                            elif hant.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                                HAYPROV = 1




                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia

                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV = 1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV = 1



                                if dest.piso and not dest.autoelev:
                                    PISOS.append(dest.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    self.write({'desc1':self.desc1+'\n'+des})
                            h += 1
                            hant =dest

                self.mdz_kms_ori, self.mdz_kms_rec, self.mdz_tiempo_rec = KMS00, KMS, TIEMPO_REC

            pistot=0
            hs_ad=0
            for j in range(len(PISOS)):
                pistot+=PISOS[j]

            if pistot>5:
                hs_ad=1+int((pistot-5)/10)


            #for j in range(len(PISOS)):
            #    hs_ad+=round((PISOS[j]*2)/60, 2)
            #    if S_PISOS[j]:
            #        hs_ad+=round((15/60)*S_PISOS[j], 2)+round((PISOS[j]*S_PISOS[j]*3)/60, 2)
            #    if B_PISOS[j]:
            #        hs_ad+=round((15/60)*B_PISOS[j], 2)+round((PISOS[j]*B_PISOS[j]*2)/60, 2)
            #    if (S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/(op_sv+op_ad)>7.5:
            #        if ((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)-int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)>0:
            #            op_ad+=int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)+1-(op_sv+op_ad)
            #        else:
            #            op_ad+=int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)-(op_sv+op_ad)
            #print('cotiz. flete, hs ad', hs_ad, 'op ad', op_ad)

            hs_sv+= hs_ad
            hs_sv_op+=hs_sv
            if solocod==2:
                if idef<len(listud_m3)-1 and COC_PROG==True:
                    hs_sv_op=(listud_cyd_hs[idef]+COC*(listud_cyd_hs[idef+1]-listud_cyd_hs[idef]))+ hs_ad
                else:
                    hs_sv_op=listud_cyd_hs[idef]+ hs_ad


            HAYINT = 0
            if HAYPROV==1 and KMS > 150:
                HAYINT = 1
                KMS = KMS * 2
                if KMS <=365:
                    hs_sv=12+hs_ad
                    hs_sv_op=8+hs_ad
                else:
                    hs_sv=24+hs_ad
                    hs_sv_op=6+hs_ad

            if self.key_usuario:
                if HAYINT==0:
                    if KMS >= 50:
                        AYD += int(KMS/50)
                        HAYPROV = 0
                        self.write({'desc1':self.desc1+'\n'+'sin prov, key_usuario AYD: %i' % AYD})
                    elif KMS >= 20:
                        HAYPROV = 1
                    else:
                        pass



            hs_sv=redond(hs_sv)
            hs_sv_op=redond(hs_sv_op)

            print('hs sv:', hs_sv,'hs sv op:', hs_sv_op, 'c_op:', op_sv, 'ud:', ud_sv, 'kms:', KMS, 'HAY PROV:', HAYPROV)

            prod_sup = self.env['abatar.productos'].search([('name', '=', 'Supervisor')], limit=1)
            prod_op = self.env['abatar.productos'].search([('name', '=', 'Operario')], limit=1)
            if ud_sv == 'A':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"A\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"B\"')], limit=1)
            elif ud_sv == 'B':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"B\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
            elif ud_sv == 'C':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
            elif ud_sv == 'D':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
            elif ud_sv == 'E':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
            elif ud_sv == 'F':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)
            elif ud_sv == 'FF':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)

            tarifa_gener = self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)

            tar_ud=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)

            if idef < len(listud_m3) - 1 and COC_PROG==True:
                tar_ud_COC=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud_COC.id)], limit=1)
                precio_ud = (tar_ud.tarifas_precio+COC*(tar_ud_COC.tarifas_precio-tar_ud.tarifas_precio))
                costo_ud = tar_ud.tarifas_costo(tar_ud)+COC*(tar_ud_COC.tarifas_costo(tar_ud_COC)-tar_ud.tarifas_costo(tar_ud))
            else:
                precio_ud = tar_ud.tarifas_precio
                costo_ud = tar_ud.tarifas_costo(tar_ud)
            print('tar_ud', tar_ud, precio_ud, costo_ud)

            tar_op=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_op.id)],limit=1)
            precio_op = tar_op.tarifas_precio
            costo_op = tar_op.tarifas_costo(tar_op)
            print('tar_op', tar_op, precio_op, costo_op)

            tar_sup=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_sup.id)], limit=1)
            precio_sup = tar_sup.tarifas_precio
            costo_sup = tar_sup.tarifas_costo(tar_sup)


            tar_ud_kms = tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
            if idef < len(listud_m3) - 1 and COC_PROG==True:
                tar_ud_kms_COC=tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud_COC.id)],limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio+COC*(tar_ud_kms_COC.tarifas_precio-tar_ud_kms.tarifas_precio)
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)+COC*(tar_ud_kms_COC.tarifas_costo(tar_ud_kms_COC)-tar_ud_kms.tarifas_costo(tar_ud_kms))
            else:
                tar_ud_kms=tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)],limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)
            print('cotiz cost:', costo_op, costo_sup, costo_ud, costo_ud_kms)
            self.codigo=str(self.m3_flete)+'('+str(hs_sv+1+AYD)

            if HAYPROV*KMS:
                if self.key_usuario:
                    self.codigo +='+kms'+str(KMS*HAYPROV)
                    #HAYPROV=0
                else:
                    self.codigo +='+kms'+str(KMS*HAYPROV)
            self.codigo +=')/'+str(op_sv)+'('+str(hs_sv_op+1)+')/BXX'

            #if op_sv>0:
            #    resu.write({'linea_personal':[(0, 0, {'producto':prod_sup.id,
            #                                          'desc':'SUPERVISOR',
            #                                          'horas':hs_sv_op+AYD,
            #                                          'precio':precio_sup,
            #                                          'costo':costo_sup,
            #                                          'cantidad':1,
            #                                          'cotizador_id':self.cotizador.id,
            #                                          })]})

            resu.write({'linea_personal':[(0, 0, {'producto':prod_ud.id,
                                                  'desc':'UNIDAD',
                                                  'horas':hs_sv+AYD,
                                                  'precio_f':precio_ud,
                                                  'costo':costo_ud,
                                                  'kms':KMS*HAYPROV,
                                                  'precio_kms_f':precio_ud_kms,
                                                  'costo_kms':costo_ud_kms,
                                                  'cantidad':1,
                                                  'cotizador_id':self.cotizador.id,
                                                  })]})
            if op_sv>0:
                resu.write({'linea_personal':[(0, 0, {'producto':prod_op.id,
                                                      'desc':'OPERARIOS',
                                                      'horas':hs_sv_op,
                                                      'precio':precio_op,
                                                      'costo':costo_op,
                                                      'cantidad':op_sv,
                                                      'cotizador_id':self.cotizador.id,
                                                      })]})
            if self.cyd_emb_grueso == True:

                prod_pluribol = self.env['abatar.productos'].search([('name', '=', 'Pluriboll')], limit=1)
                prod_st_gde = self.env['abatar.productos'].search([('name', '=', 'Streech Grande')], limit=1)
                prod_st_chi = self.env['abatar.productos'].search([('name', '=', 'Streech Chico')], limit=1)
                prod_c_emp = self.env['abatar.productos'].search([('name', '=', 'Cintas de Embalar')], limit=1)
                prod_flete = self.env['abatar.productos'].search([('name', '=', 'Flete Entrega')], limit=1)


                precio_pluribol = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)],
                                                                      limit=1).tarifas_precio
                precio_st_gde = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)],
                                                                    limit=1).tarifas_precio
                precio_st_chi = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)],
                                                                    limit=1).tarifas_precio
                precio_c_emp = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)],
                                                                   limit=1).tarifas_precio
                precio_flete = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)],
                                                                   limit=1).tarifas_precio

                costo_pluribol = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)],limit=1).tarifas_costo2
                costo_st_gde = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)],limit=1).tarifas_costo2
                costo_st_chi = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)],limit=1).tarifas_costo2
                costo_c_emp = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)],limit=1).tarifas_costo2
                costo_flete = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)],limit=1).tarifas_costo2

                prods_emb = [prod_pluribol, prod_st_gde,prod_st_chi,prod_c_emp,prod_flete]
                precios_emb = [precio_pluribol, precio_st_gde,precio_st_chi,precio_c_emp,precio_flete]
                costos_emb = [costo_pluribol, costo_st_gde,costo_st_chi, costo_c_emp, costo_flete]
                cant_emb = [1, 1, 1, 1, max([10,KMS00])]

                for i in range(len(prods_emb)):
                    resu.write({'embalaje_lines': [(0, 0, {'embalaje_id': prods_emb[i].id,
                                                           'cantidad': cant_emb[i],
                                                           'precio': precios_emb[i],
                                                           'costo': costos_emb[i],
                                                           'cotizador_id': self.cotizador.id,
                                                           })]})

            resu.AYD=AYD
            resu.aumento=0
            resu.hay_categ="B"
        #SECCION FLETE----------##################################################
        fields.Glog("aca18 fin")
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.cotizador',
            'res_id': resu.id,
        }

    @api.depends('destinos_lines','destinos_lines2', 'desc1')
    def action_set_int(self):
        for RECA in self:

            AYD=0
            PISOS=[]
            B_PISOS=[]
            S_PISOS=[]
            HAYPROV=0
            HAYINT = 0
            TIEMPO_REC=0
            KMS=0
            KMS00=0
            if RECA.mdz_tiempo_rec:
                pass
            else:
                if RECA.es_conocido=='si':
                    print('Si!')
                    h=0
                    hmax=len(RECA.destinos_lines)
                    for dest in RECA.destinos_lines:
                        print('dest', dest)
                        if dest and dest.destino_id:
                            if h==0 :
                                ORIGEN = 'ARAUJO 1508, CABA'

                                if dest.destino_id.forc_direc:
                                    pass
                                else:
                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):

                                            HAYINT=1
                                            RECA.hay_int=True
                                            if RECA.prov_int_label:
                                                RECA.prov_int_label+=', '+dest.destino_id.provincia.upper()
                                            else:
                                                RECA.prov_int_label=dest.destino_id.provincia.upper()
                            if h>0 :

                                if dest.destino_id.forc_direc:
                                    pass
                                else:
                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYINT=1
                                            RECA.hay_int=True
                                            if RECA.prov_int_label:
                                                RECA.prov_int_label+=', '+dest.destino_id.provincia.upper()
                                            else:
                                                RECA.prov_int_label=dest.destino_id.provincia.upper()
                            h += 1
                            hant =dest



                else:
                    print('else')
                    h=0
                    hmax=len(RECA.destinos_lines2)
                    for dest in RECA.destinos_lines2:
                        print('dest', dest)
                        if dest:

                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'
                                if dest.forc_direc:
                                    pass
                                else:

                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYINT=1
                                            RECA.hay_int=True
                                            if RECA.prov_int_label:
                                                RECA.prov_int_label+=', '+dest.provincia.upper()
                                            else:
                                                RECA.prov_int_label=dest.provincia.upper()
                            if h>0 :
                                if hant:

                                    if hant.forc_direc:
                                        pass
                                    else:
                                        if hant.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and hant.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):

                                                HAYINT=1
                                                RECA.hay_int=True
                                                if RECA.prov_int_label:
                                                    RECA.prov_int_label+=', '+hant.provincia.upper()
                                                else:
                                                    RECA.prov_int_label=hant.provincia.upper()



                                if dest.forc_direc:
                                    pass
                                else:
                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYINT=1
                                            RECA.hay_int=True
                                            if RECA.prov_int_label:
                                                RECA.prov_int_label+=dest.provincia.upper()
                                            else:
                                                RECA.prov_int_label=dest.provincia.upper()

                            h += 1
                            hant =dest
            RECA.hay_int=False
            RECA.prov_int_label=''
    @api.multi
    def action_crea_calculadora2(self):
        for RECA in self:
            #SECCION COMPROBACIONES----------##################################################

            requerid=[RECA.m3_flete, [RECA.destinos_lines,RECA.destinos_lines2]]
            req_name=['m3_flete', ['destinos_lines','destinos_lines2']]
            h=0
            for req in requerid:
                if type(req)!=list:
                    if req:
                        pass
                    else:
                        raise UserError('Para iniciar un cotizador necesitas llenar los datos del formulario, falta %s - valor: %s' % (str(req_name[h]),str(req)))
                else:
                    salta=False
                    strerror=[]
                    j=0
                    for req2 in req:
                        if req2:
                            salta=True
                        else:
                            strerror.append(req2)
                            pass
                        j+=1
                    if salta==True:
                        pass
                    else:
                        raise UserError('Para iniciar un cotizador necesitas llenar los datos basicos, falta %s - valor: %s' % (str(req_name[h][j]), str(strerror)))
                h+=1
            ####################### CREA COTIZADOR----------##################################
            ivainc=True
            if RECA.es_conocido=='si':
                ivainc=False
            vals2 = {
                'crm': RECA.id,
                'es_ivainc': ivainc,
            }

            resu = self.env['abatar.cotizador'].create(vals2)
            RECA.cotizador = resu.id
            BSAS_list=['BS AS', 'BS. AS.', 'BSAS', 'BUENOS AIRES']
            CABA_list=['CABA','C.A.B.A.','CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTONOMA DE BS AS','CIUDAD AUTONOMA DE BS. AS.', 'CIUDAD AUTÓNOMA DE BUENOS AIRES', 'CAPITAL']
            #SECCION MUDANZA----------##################################################

            opudc=1
            if RECA.servicio.name == 'Flete':
                opudc = 2
            AYD=0
            listud_m3=[5, 10,15, 20, 25, 35, 45]
            listud_kgs=[500, 1500,2500, 4500, 7500, 15000, 20000]
            listud_xdirec=[0,0,0,0,0,0,0]#[0.2,0.25, 0.3, 0.35, 0.4, 0.45, 0.45]
            listud_tipo=['A','B', 'C','D', 'E', 'F', 'FF']
            solocod=1
            adopec_l=[0  , 0  , 0  , 0  , 0 , 0  , 0]
            if RECA.cyd_flete==True:
                if RECA.cyd_forcop>0:
                    listud_cyd_op=[RECA.cyd_forcop  , RECA.cyd_forcop  , RECA.cyd_forcop, RECA.cyd_forcop, RECA.cyd_forcop, RECA.cyd_forcop, RECA.cyd_forcop  ]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 1, 1.5, 2, 2.5]
                elif RECA.cyd_minop>0:
                    listud_cyd_op=[ max([1,RECA.cyd_minop]), max([1,RECA.cyd_minop]) ,  max([opudc,RECA.cyd_minop])  , max([2,RECA.cyd_minop])  , max([3,RECA.cyd_minop]), max([4,RECA.cyd_minop]), max([6,RECA.cyd_minop])  ]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 1, 1.5, 2, 2.5]
                elif RECA.cyd_emb_grueso==True:
                    listud_cyd_op=[2  , 2  , 2  , 2  , 3, 4, 6  ]
                    listud_cyd_hs=[0.75, 1, 1.25, 2.25, 3, 3, 4]

                    adopec_l=[0.45, 0.5, 0.25, 0.75, 1,1, 1.5]
                elif RECA.cyd_autoelev==True:
                    listud_cyd_op=[0  , 0  , 0  , 0  , 0 , 0  , 0]
                    listud_cyd_hs=[0.5, 0.5, 0.5, 0.75, 1, 1.5, 2]
                else:
                    listud_cyd_op=[1  ,1  ,opudc, 2  , 3, 4, 6  ]
                    listud_cyd_hs=[0.3,0.5,1, 1.5, 2, 2, 2.5]
                if RECA.cyd_solo_cod=='Carga' or RECA.cyd_solo_cod=='Descarga':
                    solocod=2
            else:
                listud_cyd_op=[0, 0, 0, 0, 0, 0, 0 ]
                listud_cyd_hs=[0.3,0.5,1, 1.5, 2, 2, 2.5]
            idef1=0
            for i in range(len(listud_m3)):
                if RECA.m3_flete<=listud_m3[i] or i==len(listud_m3)-1:
                    idef1=i
                    break
            idef2=0
            for i in range(len(listud_kgs)):
                if RECA.kgs_flete<=listud_kgs[i] or i==len(listud_kgs)-1:
                    idef2=i
                    break
            idef = max([idef1, idef2])
            COC=max([RECA.m3_flete/listud_m3[idef], RECA.kgs_flete/listud_kgs[idef]])
            ud_sv = listud_tipo[idef]
            if idef<len(listud_m3)-1 and COC_PROG==True:
                op_sv = (listud_cyd_op[idef]+int(COC*(listud_cyd_op[idef+1]-listud_cyd_op[idef])))
            else:
                op_sv = listud_cyd_op[idef]
            if idef<len(listud_m3)-1 and COC_PROG==True:
                hs_sv=((listud_cyd_hs[idef]+COC*(listud_cyd_hs[idef+1]-listud_cyd_hs[idef]))-(adopec_l[idef]+COC*(adopec_l[idef+1]-adopec_l[idef])))*2
                hs_sv_op=(adopec_l[idef]+COC*(adopec_l[idef+1]-adopec_l[idef]))*2
            else:
                hs_sv=(listud_cyd_hs[idef]-adopec_l[idef])*2
                hs_sv_op=adopec_l[idef]*2
            PISOS=[]
            B_PISOS=[]
            S_PISOS=[]
            HAYPROV=0
            HAYINT = 0
            TIEMPO_REC=0
            KMS=0
            KMS00=0
            if RECA.mdz_tiempo_rec:
                hs_sv+=RECA.mdz_tiempo_rec
                if RECA.mdz_kms_rec:
                    HAYPROV=1
                    KMS=RECA.mdz_kms_rec

                if RECA.es_conocido == 'si':
                    for dest in RECA.destinos_lines:
                        if dest:
                            hs_sv += listud_xdirec[idef]
                else:
                    for dest in RECA.destinos_lines2:
                        if dest:
                            hs_sv += listud_xdirec[idef]
            else:
                if RECA.es_conocido=='si':
                    print('Si!')
                    h=0
                    hmax=len(RECA.destinos_lines)
                    for dest in RECA.destinos_lines:
                        print('dest', dest)
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'

                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name+', '+dest.destino_id.localidad
                                    else:
                                        DESTINO =dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in  ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO+=', '+dest.destino_id.provincia

                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            destino_prov=1
                                            HAYPROV=1
                                            HAYINT=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            destino_prov=1
                                            HAYPROV=1

                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)
                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        destino_prov = 1
                                        HAYPROV=1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd
                                if IMPRIME_CALCULA_DIST==True:
                                    RECA.write({'desc1':RECA.desc1+'\n'+des})
                                if destino_prov==1 and RECA.convenio=='cc':
                                    KMS+=KMS00
                                    RECA.write({'desc1':RECA.desc1+'\n'+'%.1f kms al origen incluidos en kms total.' % KMS00})

                                #Desactivo que si empieza en provincia cobra kms hasta el origen
                                #if destino_prov==1:
                                #    tiempo_oyd, distance_oyd, des = calcula_distancia(self, ORIGEN, DESTINO)
                                #    KMS+=distance_oyd
                                if dest.destino_id.piso and not dest.autoelev:
                                    PISOS.append(dest.destino_id.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                            if h>0 :
                                if hant:

                                    if hant.destino_id.forc_direc:
                                        ORIGEN = hant.destino_id.forc_direc
                                    else:
                                        if hant.destino_id.name:
                                            ORIGEN = hant.destino_id.name + ', ' + hant.destino_id.localidad
                                        else:
                                            ORIGEN = hant.destino_id.localidad
                                        if hant.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            ORIGEN += ', ' + hant.destino_id.provincia



                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name + ', ' + dest.destino_id.localidad
                                    else:
                                        DESTINO = dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO += ', ' + dest.destino_id.provincia


                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                            HAYINT=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1


                                if dest.destino_id.piso and not dest.autoelev:
                                    PISOS.append(dest.destino_id.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                                print('o y d', ORIGEN, DESTINO)
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO) ACA 24-2
                                time.sleep(1)
                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    RECA.write({'desc1':RECA.desc1+'\n'+des})
                            h += 1
                            hant =dest



                else:
                    print('else')
                    h=0
                    hmax=len(RECA.destinos_lines2)
                    for dest in RECA.destinos_lines2:
                        print('dest', dest)
                        if dest:

                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'
                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia


                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                            HAYINT=1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1
                                #    destino_prov=1
                                #    HAYPROV=1
                                #if dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                #    destino_prov=1
                                #    HAYPROV=1

                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                if IMPRIME_CALCULA_DIST==True:
                                    RECA.write({'desc1':RECA.desc1+'\n'+des})
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd


                                if dest.piso and not dest.autoelev:
                                    PISOS.append(dest.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                            if h>0 :
                                if hant:

                                    if hant.forc_direc:
                                        ORIGEN = hant.forc_direc
                                    else:
                                        if hant.destino:
                                            ORIGEN = hant.destino+', '+hant.localidad
                                        else:
                                            ORIGEN =hant.localidad
                                        if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            ORIGEN+=', '+hant.provincia

                                        if hant.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and hant.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                                HAYPROV = 1
                                                HAYINT=1
                                            elif hant.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                                HAYPROV = 1




                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia

                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV = 1
                                            HAYINT=1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV = 1



                                if dest.piso and not dest.autoelev:
                                    PISOS.append(dest.piso)
                                    if dest.m3_escalera_c:
                                        B_PISOS.append(dest.m3_escalera_c)
                                    else:
                                        B_PISOS.append(0)
                                    if dest.m3_escalera_d:
                                        S_PISOS.append(dest.m3_escalera_d)
                                    else:
                                        S_PISOS.append(0)
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    RECA.write({'desc1':RECA.desc1+'\n'+des})
                            h += 1
                            hant =dest

                RECA.mdz_kms_ori, RECA.mdz_kms_rec, RECA.mdz_tiempo_rec = KMS00, KMS, TIEMPO_REC


            pistot=0
            hs_ad=0
            for j in range(len(PISOS)):
                pistot+=PISOS[j]

            if pistot>5:
                hs_ad=1+int((pistot-5)/10)


            #for j in range(len(PISOS)):
            #    hs_ad+=round((PISOS[j]*2)/60, 2)
            #    if S_PISOS[j]:
            #        hs_ad+=round((15/60)*S_PISOS[j], 2)+round((PISOS[j]*S_PISOS[j]*3)/60, 2)
            #    if B_PISOS[j]:
            #        hs_ad+=round((15/60)*B_PISOS[j], 2)+round((PISOS[j]*B_PISOS[j]*2)/60, 2)
            #    if (S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/(op_sv+op_ad)>7.5:
            #        if ((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)-int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)>0:
            #            op_ad+=int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)+1-(op_sv+op_ad)
            #        else:
            #            op_ad+=int((S_PISOS[j]+B_PISOS[j]/2)*PISOS[j]/7.5)-(op_sv+op_ad)
            #print('cotiz. flete, hs ad', hs_ad, 'op ad', op_ad)

            hs_sv+= hs_ad
            hs_sv_op+=hs_sv
            if solocod==2:
                if idef<len(listud_m3)-1 and COC_PROG==True:
                    hs_sv_op=(listud_cyd_hs[idef]+COC*(listud_cyd_hs[idef+1]-listud_cyd_hs[idef]))+ hs_ad
                else:
                    hs_sv_op=listud_cyd_hs[idef]+ hs_ad


            if HAYPROV==1 and KMS > 100:
                HAYINT = 1
                RECA.hay_int=True
                KMS = KMS * 2
                if KMS <=365*2:
                    hs_sv=12+hs_ad
                    hs_sv_op=8+hs_ad
                else:
                    hs_sv=24+hs_ad
                    hs_sv_op=6+hs_ad
            else:
                KMS = KMS * 2
            #if RECA.key_usuario:
            #    if HAYINT==0:
            #        if KMS >= 50:
            #            AYD += int(KMS/50)
            #            HAYPROV = 0
            #            RECA.write({'desc1':RECA.desc1+'sin prov, key_usuario AYD: %i' % AYD})
            #        elif KMS >= 20:
            #            HAYPROV = 1
            #        else:
            #            pass



            hs_sv=redond(hs_sv)
            hs_sv_op=redond(hs_sv_op)

            print('hs sv:', hs_sv,'hs sv op:', hs_sv_op, 'c_op:', op_sv, 'ud:', ud_sv, 'kms:', KMS, 'HAY PROV:', HAYPROV)

            prod_sup = self.env['abatar.productos'].search([('name', '=', 'Supervisor')], limit=1)
            prod_op = self.env['abatar.productos'].search([('name', '=', 'Operario')], limit=1)
            if ud_sv == 'A':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"A\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"B\"')], limit=1)
            elif ud_sv == 'B':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"B\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
            elif ud_sv == 'C':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
            elif ud_sv == 'D':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
            elif ud_sv == 'E':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
            elif ud_sv == 'F':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
                prod_ud_COC = self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)
            elif ud_sv == 'FF':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)

            tarifa_gener = self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)

            tar_ud=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)

            if idef < len(listud_m3) - 1 and COC_PROG==True:
                tar_ud_COC=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud_COC.id)], limit=1)
                precio_ud = (tar_ud.tarifas_precio+COC*(tar_ud_COC.tarifas_precio-tar_ud.tarifas_precio))
                costo_ud = tar_ud.tarifas_costo(tar_ud)+COC*(tar_ud_COC.tarifas_costo(tar_ud_COC)-tar_ud.tarifas_costo(tar_ud))
            else:
                precio_ud = tar_ud.tarifas_precio
                costo_ud = tar_ud.tarifas_costo(tar_ud)
            print('tar_ud', tar_ud, precio_ud, costo_ud)

            tar_op=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_op.id)],limit=1)
            precio_op = tar_op.tarifas_precio
            costo_op = tar_op.tarifas_costo(tar_op)
            print('tar_op', tar_op, precio_op, costo_op)

            tar_sup=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_sup.id)], limit=1)
            precio_sup = tar_sup.tarifas_precio
            costo_sup = tar_sup.tarifas_costo(tar_sup)


            tar_ud_kms = tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
            if idef < len(listud_m3) - 1 and COC_PROG==True:
                tar_ud_kms_COC=tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud_COC.id)],limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio+COC*(tar_ud_kms_COC.tarifas_precio-tar_ud_kms.tarifas_precio)
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)+COC*(tar_ud_kms_COC.tarifas_costo(tar_ud_kms_COC)-tar_ud_kms.tarifas_costo(tar_ud_kms))
            else:
                tar_ud_kms=tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)],limit=1)
                precio_ud_kms = tar_ud_kms.tarifas_precio
                costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)
            print('cotiz cost:', costo_op, costo_sup, costo_ud, costo_ud_kms)
            RECA.codigo=str(RECA.m3_flete)+'('+str(hs_sv+1+AYD)

            if HAYPROV*KMS:
                if RECA.key_usuario:
                    RECA.codigo +='+kms'+str(KMS*HAYPROV)
                    #HAYPROV=0
                else:
                    RECA.codigo +='+kms'+str(KMS*HAYPROV)
            RECA.codigo +=')/'+str(op_sv)+'('+str(hs_sv_op+1)+')/BXX'

            #if op_sv>0:
            #    resu.write({'linea_personal':[(0, 0, {'producto':prod_sup.id,
            #                                          'desc':'SUPERVISOR',
            #                                          'horas':hs_sv_op+AYD,
            #                                          'precio':precio_sup,
            #                                          'costo':costo_sup,
            #                                          'cantidad':1,
            #                                          'cotizador_id':RECA.cotizador.id,
            #                                          })]})

            resu.write({'linea_personal':[(0, 0, {'producto':prod_ud.id,
                                                  'desc':'UNIDAD cyd %.1f' % hs_sv,
                                                  'horas':hs_sv+AYD,
                                                  'precio_f':precio_ud,
                                                  'costo':costo_ud,
                                                  'kms':KMS*HAYPROV,
                                                  'precio_kms_f':precio_ud_kms,
                                                  'costo_kms':costo_ud_kms,
                                                  'cantidad':1,
                                                  'cotizador_id':RECA.cotizador.id,
                                                  })]})
            if op_sv>0:
                resu.write({'linea_personal':[(0, 0, {'producto':prod_op.id,
                                                      'desc':'OPERARIOS',
                                                      'horas':hs_sv_op,
                                                      'precio':precio_op,
                                                      'costo':costo_op,
                                                      'cantidad':op_sv,
                                                      'cotizador_id':RECA.cotizador.id,
                                                      })]})
            if RECA.cyd_emb_grueso == True:

                prod_pluribol = self.env['abatar.productos'].search([('name', '=', 'Pluriboll')], limit=1)
                prod_st_gde = self.env['abatar.productos'].search([('name', '=', 'Streech Grande')], limit=1)
                prod_st_chi = self.env['abatar.productos'].search([('name', '=', 'Streech Chico')], limit=1)
                prod_c_emp = self.env['abatar.productos'].search([('name', '=', 'Cintas de Embalar')], limit=1)
                prod_flete = self.env['abatar.productos'].search([('name', '=', 'Flete Entrega')], limit=1)


                precio_pluribol = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)],
                                                                      limit=1).tarifas_precio
                precio_st_gde = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)],
                                                                    limit=1).tarifas_precio
                precio_st_chi = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)],
                                                                    limit=1).tarifas_precio
                precio_c_emp = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)],
                                                                   limit=1).tarifas_precio
                precio_flete = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)],
                                                                   limit=1).tarifas_precio

                costo_pluribol = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_pluribol.id)],limit=1).tarifas_costo2
                costo_st_gde = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_gde.id)],limit=1).tarifas_costo2
                costo_st_chi = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_st_chi.id)],limit=1).tarifas_costo2
                costo_c_emp = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_c_emp.id)],limit=1).tarifas_costo2
                costo_flete = tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_flete.id)],limit=1).tarifas_costo2

                prods_emb = [prod_pluribol, prod_st_gde,prod_st_chi,prod_c_emp,prod_flete]
                precios_emb = [precio_pluribol, precio_st_gde,precio_st_chi,precio_c_emp,precio_flete]
                costos_emb = [costo_pluribol, costo_st_gde,costo_st_chi, costo_c_emp, costo_flete]
                cant_emb = [1, 1, 1, 1, max([10,KMS00])]

                for i in range(len(prods_emb)):
                    resu.write({'embalaje_lines': [(0, 0, {'embalaje_id': prods_emb[i].id,
                                                           'cantidad': cant_emb[i],
                                                           'precio': precios_emb[i],
                                                           'costo': costos_emb[i],
                                                           'cotizador_id': resu.id,
                                                           })]})

            resu.AYD=AYD
            resu.aumento=0
            resu.hay_categ="B"
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'abatar.cotizador',
                'res_id': resu.id,
            }

    @api.multi
    def action_crea_boti(self):

        requerid=[self.m3_flete, [self.destinos_lines,self.destinos_lines2]]
        req_name=['m3_flete', ['destinos_lines','destinos_lines2']]
        h=0
        for req in requerid:
            if type(req)!=list:
                if req:
                    pass
                else:
                    raise UserError('Para iniciar un cotizador necesitas llenar los datos del formulario, falta %s - valor: %s' % (str(req_name[h]),str(req.name)))
            else:
                salta=False
                strerror=[]
                j=0
                for req2 in req:
                    if req2:
                        salta=True
                    else:
                        strerror.append(req2)
                        pass
                    j+=1
                if salta==True:
                    pass
                else:
                    raise UserError('Para iniciar un cotizador necesitas llenar los datos basicos, falta %s - valor: %s' % (str(req_name[h][j]), str(strerror)))
            h+=1
        ####################### CREA COTIZADOR----------##################################
        ivainc=True
        if self.es_conocido=='si':
            ivainc=False
        vals2 = {
            'crm': self.id,
            'es_ivainc': ivainc,
        }

        resu = self.env['abatar.cotizador'].create(vals2)
        self.cotizador = resu.id
        BSAS_list=['BS AS', 'BS. AS.', 'BSAS', 'BUENOS AIRES']
        CABA_list=['CABA','C.A.B.A.','CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTONOMA DE BS AS','CIUDAD AUTONOMA DE BS. AS.', 'CIUDAD AUTÓNOMA DE BUENOS AIRES', 'CAPITAL']
        #SECCION MUDANZA----------##################################################
        #SECCION FLETE----------##################################################
        if self.servicio.name == 'Flete':
            opudc = 2
            AYD=0
            listud_m3=[5, 10,15, 20, 25, 35, 45]
            listud_kgs=[500, 1500,2500, 4500, 7500, 15000, 20000]
            listud_xdirec=[0.2,0.25, 0.3, 0.35, 0.4, 0.45, 0.45]
            listud_tipo=['A','B', 'C','D', 'E', 'F', 'FF']

            idef=0
            for i in range(len(listud_m3)):
                if self.m3_flete<=listud_m3[i] or i==len(listud_m3)-1:
                    idef=i
                    break

            ud_sv = listud_tipo[idef]

            TIEMPO_REC=0
            hs_sv=0
            HAYPROV=0
            KMS=0
            KMS00=0
            if self.mdz_tiempo_rec:
                hs_sv+=self.mdz_tiempo_rec
                if self.mdz_kms_rec:
                    HAYPROV=1
                    KMS=self.mdz_kms_rec

                if self.es_conocido == 'si':
                    for dest in self.destinos_lines:
                        if dest:
                            hs_sv += listud_xdirec[idef]
                else:
                    for dest in self.destinos_lines2:
                        if dest:
                            hs_sv += listud_xdirec[idef]
            else:
                if self.es_conocido=='si':
                    print('Si!')
                    h=0
                    hmax=len(self.destinos_lines)
                    for dest in self.destinos_lines:
                        print('dest', dest)
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'


                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name+', '+dest.destino_id.localidad
                                    else:
                                        DESTINO =dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in  ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO+=', '+dest.destino_id.provincia
                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            destino_prov=1
                                            HAYPROV=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            destino_prov=1
                                            HAYPROV=1

                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)

                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        destino_prov = 1
                                        HAYPROV=1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd
                                if destino_prov==1 and self.convenio=='cc':
                                    KMS+=KMS00
                                    if IMPRIME_CALCULA_DIST==True:
                                        self.desc1=self.desc1+'\n'+'%.1f kms al origen incluidos en kms total.' % KMS00



                            elif h>0 :
                                if hant:
                                    if hant.destino_id.forc_direc:
                                        ORIGEN=hant.destino_id.forc_direc
                                    else:
                                        if hant.destino_id.name:
                                            ORIGEN = hant.destino_id.name + ', ' + hant.destino_id.localidad
                                        else:
                                            ORIGEN = hant.destino_id.localidad
                                        if hant.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            ORIGEN += ', ' + hant.destino_id.provincia



                                if dest.destino_id.forc_direc:
                                    DESTINO=dest.destino_id.forc_direc
                                else:
                                    if dest.destino_id.name:
                                        DESTINO = dest.destino_id.name + ', ' + dest.destino_id.localidad
                                    else:
                                        DESTINO = dest.destino_id.localidad
                                    if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.', 'CABA','CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        DESTINO += ', ' + dest.destino_id.provincia


                                    if dest.destino_id.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.destino_id.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.destino_id.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                        elif dest.destino_id.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1



                                print('o y d', ORIGEN, DESTINO)
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO) ACA 24-2
                                time.sleep(1)
                                if dest.destino_id.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV=1

                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    self.desc1=self.desc1+'\n'+des
                            h += 1
                            hant =dest



                else:
                    print('else')
                    h=0
                    hmax=len(self.destinos_lines2)
                    for dest in self.destinos_lines2:
                        print('dest', dest)
                        if dest:
                            hs_sv+=listud_xdirec[idef]
                            if h==0 :
                                destino_prov=0
                                ORIGEN = 'ARAUJO 1508, CABA'

                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia


                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV=1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV=1
                                #    destino_prov=1
                                #    HAYPROV=1
                                #if dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                #    destino_prov=1
                                #    HAYPROV=1


                                #if destino_prov==1:
                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV = 1
                                print('dest', dest,'tiempo', tiempo_oyd/3600)
                                KMS00=distance_oyd
                                if IMPRIME_CALCULA_DIST==True:
                                    self.desc1=self.desc1+'\n'+des



                            elif h>0 :
                                if hant:
                                    if hant.forc_direc:
                                        ORIGEN = hant.forc_direc
                                    else:
                                        if hant.destino:
                                            ORIGEN = hant.destino+', '+hant.localidad
                                        else:
                                            ORIGEN =hant.localidad
                                        if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            ORIGEN+=', '+hant.provincia

                                        if hant.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and hant.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            if hant.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                                HAYPROV = 1
                                            elif hant.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                                HAYPROV = 1

                                if dest.forc_direc:
                                    DESTINO = dest.forc_direc
                                else:
                                    if dest.destino:
                                        DESTINO = dest.destino+', '+dest.localidad
                                    else:
                                        DESTINO =dest.localidad
                                    if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                        DESTINO+=', '+dest.provincia

                                    if dest.provincia.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES') and dest.localidad.upper() not in ('CABA', 'CIUDAD AUTONOMA DE BUENOS AIRES', 'CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                        if dest.provincia.upper() not in ('BUENOS AIRES', 'BS AS', 'BS. AS.'):
                                            HAYPROV = 1
                                        elif dest.localidad.upper() not in ('CABA', 'C.A.B.A.', 'CIUDAD AUTONOMA DE BUENOS AIRES','CIUDAD AUTÓNOMA DE BUENOS AIRES'):
                                            HAYPROV = 1

                                tiempo_oyd, distance_oyd, des = calcula_distancia(self,ORIGEN, DESTINO) #calcula_distancia(self, ORIGEN, DESTINO)  ACA 24-2

                                if dest.forc_direc:
                                    if distance_oyd>20:
                                        HAYPROV = 1
                                KMS+=distance_oyd
                                hs_sv+=tiempo_oyd/3600
                                TIEMPO_REC+=tiempo_oyd/3600
                                if IMPRIME_CALCULA_DIST==True:
                                    self.desc1=self.desc1+'\n'+des
                            h += 1
                            hant =dest
                self.mdz_kms_ori, self.mdz_kms_rec, self.mdz_tiempo_rec = KMS00, KMS, TIEMPO_REC

            HAYINT = 0
            if HAYPROV==1 and KMS > 150:
                HAYINT = 1
                KMS = KMS * 2
                if KMS <=365:
                    hs_sv=12
                else:
                    hs_sv=24

            '''if self.key_usuario:
                if HAYINT==0:
                    if KMS >= 50:
                        AYD += int(KMS/50)
                        HAYPROV = 0
                    elif KMS >= 20:
                        HAYPROV = 1
                    else:
                        pass'''


            hs_sv=redond(hs_sv)

            print('hs sv:', hs_sv, 'ud:', ud_sv, 'kms:', KMS, 'HAY PROV:', HAYPROV)

            prod_op = self.env['abatar.productos'].search([('name', '=', 'Operario')], limit=1)
            if ud_sv == 'A':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"A\"')], limit=1)
            elif ud_sv == 'B':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"B\"')], limit=1)
            elif ud_sv == 'C':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"C\"')], limit=1)
            elif ud_sv == 'D':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"D\"')], limit=1)
            elif ud_sv == 'E':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"E\"')], limit=1)
            elif ud_sv == 'F':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"F\"')], limit=1)
            elif ud_sv == 'FF':
                prod_ud = self.env['abatar.productos'].search([('name', '=', 'Unidad \"FF\"')], limit=1)

            tarifa_gener = self.env['abatar.tarifas'].search([('es_general', '=', True)], limit=1)

            tar_ud=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_ud.id)], limit=1)
            precio_ud = tar_ud.tarifas_precio
            costo_ud = tar_ud.tarifas_costo(tar_ud)
            print('tar_ud', tar_ud, precio_ud, costo_ud)

            tar_op=tarifa_gener.productos_lines.search([('productos_id.id', '=', prod_op.id)],limit=1)
            precio_op = tar_op.tarifas_precio
            costo_op = tar_op.tarifas_costo(tar_op)
            print('tar_op', tar_op, precio_op, costo_op)

            tar_ud_kms=tarifa_gener.kms_lines.search([('productos_id.id', '=', prod_ud.id)],limit=1)
            precio_ud_kms = tar_ud_kms.tarifas_precio
            costo_ud_kms = tar_ud_kms.tarifas_costo(tar_ud_kms)
            print('cotiz cost:', costo_op, costo_ud, costo_ud_kms)
            self.codigo=str(self.m3_flete)+'('+str(hs_sv+1+AYD)

            if HAYPROV*KMS:
                if self.key_usuario:
                    self.codigo +='+kms'+str(KMS*HAYPROV)
                    #HAYPROV=0
                else:
                    self.codigo +='+kms'+str(KMS*HAYPROV)
            self.codigo +=')'

            resu.write({'linea_personal':[(0, 0, {'producto':prod_ud.id,
                                                  'desc':'UNIDAD',
                                                  'horas':hs_sv+AYD,
                                                  'precio_f':precio_ud,
                                                  'costo':costo_ud,
                                                  'kms':KMS*HAYPROV,
                                                  'precio_kms_f':precio_ud_kms,
                                                  'costo_kms':costo_ud_kms,
                                                  'cantidad':1,
                                                  'cotizador_id':self.cotizador.id,
                                                  })]})

            resu.AYD=AYD
            resu.aumento=0
            resu.hay_categ="B"
        #SECCION FLETE----------##################################################
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.cotizador',
            'res_id': resu.id,
        }

    @api.model
    def default_get(self, fields):

        revisa = self.env['abatar.servicios'].search(
            [('name', '=', 'Mudanza')])
        revisb = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Pendiente')])
        revisc = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Vigente')])

        rec = super(AbatarCRM, self).default_get(fields)

        rec['servicio'] = revisa.id
        rec['estado'] = revisb.id
        rec['estado_presupuesto'] = revisc.id

        rec['factura']=False
        rec['facturado']=self.env['abatar.booleana'].search([('name', '=', 'No Facturado')], limit=1).id

        resumen=''
        for key in rec:
            resumen+=key+':'+Typyze('str', rec[key])+'\n'
        rec['resumen_busqueda'] = resumen


        return rec

    @api.model
    def vencimiento_state(self):

        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: vencimiento_state')
        guarda = self.search([
            ('recontactar', '<=', fields.Date.to_string(date.today() + relativedelta(days=4)))
        ])

        valor_pausado = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Pausado')])
        valor_vigente = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Vigente')])

        for rec in guarda:

            if rec.recontactar < date.today():
                rec.recontactar = date.today()

            if rec.estado_presupuesto.id == valor_pausado.id:
                rec.estado_presupuesto = valor_vigente.id

        #COLORES EN FECHA DE SV
        guarda2 = self.search([
            ('fecha_ejecucion', '<=', fields.Date.to_string(date.today() + relativedelta(days=4))),
            ('fecha_ejecucion', '>', fields.Date.to_string(date.today())),
            ('fechasv_proximo', '=', 0)
        ])
        for dec in guarda2:
            dec.fechasv_proximo = 1

        guarda3 = self.search([
            ('fecha_ejecucion', '<', fields.Date.to_string(date.today())),
            ('fechasv_proximo', '=', 1)
        ])
        for dec in guarda3:
            dec.fechasv_proximo = 0


    @api.depends('estado','tel')
    def depends_estado(self):
        for rec in self:
            if rec.estado.name == 'Pendiente':
                rec.state = 'pendiente'
            elif rec.estado.name == 'Presupuesto':
                rec.state = 'presupuesto'
            elif rec.estado.name == 'Confirmado':
                rec.state = 'confirmado'
            elif rec.estado.name == 'Finalizado':
                rec.state = 'finalizado'
            elif rec.estado.name == 'Rechazado':
                rec.state = 'rechazado'
            elif rec.estado.name == 'Cancelado':
                rec.state = 'cancelado'
                rec.write({'active':False})

    def close_solapas(self):
        self.write({'ver_flete' : False})
        self.write({'ver_direc' : False})
        self.write({'ver_fact' : False})
        self.write({'ver_cobros' : False})
        self.write({'ver_otros' : False})

    def open_solapas(self):
        self.write({'ver_flete' : True})
        self.write({'ver_direc' : True})
        self.write({'ver_fact' : True})
        self.write({'ver_cobros' : True})
        self.write({'ver_otros' : True})

    @api.multi
    def write(self, vals,resumen_load=True):

        if MJSLOG:
            _logger = logging.getLogger(__name__)
            _logger.error('YOGASTONADM: %s' % datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
            _logger.error('YOGASTONADM: write')
        for rec in self:
            vale = ''

            hhoo=0
            for elem in CAMPOS_CAMBIO:
                if elem in vals:
                    if hhoo==0:
                        vale = ('<li> '+elem+str(' Viejo: %s - '% str(rec[elem])) +elem+' Nuevo: %s</li>'%str(vals.get(elem)))
                    else:
                        vale += ('<li> '+elem+str(' Viejo: %s - '% str(rec[elem])) +elem+' Nuevo: %s</li>'%str(vals.get(elem)))
                    hhoo+=1

            if vals.get('ver_flete'):
                vals['ver_flete']=False
            if vals.get('ver_direc'):
                vals['ver_direc']=False
            if vals.get('ver_fact'):
                vals['ver_fact']=False
            if vals.get('ver_cobros'):
                vals['ver_cobros']=False
            if vals.get('ver_otros'):
                vals['ver_otros']=False

            if vale != '':
                try:
                    rec.message_post(body=_(vale))
                except:
                    pass
        if BUSQUEDAON==True and resumen_load:
            try:
                if self.ensure_one():
                    if type(self.id)==int:
                        resum=Analize_model3(self, self._name, [('id', '=', self.id), ('active', 'in', (True, False))])
                        if len(resum)>50:
                            vals['resumen_busqueda']=datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarCRM, self).write(vals)

        h0=0
        self2=[]
        for rec in self:
            h0+=1
            self2.append(rec)
        if h0>1:
            vals2={}
            vals2=vals
            h=0
            for vals in vals2:
                rec=self2[h]
                h+=1
                if 'recontactar' in vals:
                    if vals.get('recontactar'):

                        valor_pausado = rec.env['abatar.estados.presupuesto'].search(
                            [('name', '=', 'Pausado')])
                        valor_vigente = rec.env['abatar.estados.presupuesto'].search(
                            [('name', '=', 'Vigente')])
                        # ANALIZA ESTADO VIGENTE/PAUSADO
                        guarda = rec.search([
                            ('recontactar', '<=', fields.Date.to_string(date.today() + relativedelta(days=4))),
                            ('id', '=', rec.id)
                        ])
                        if guarda.id == rec.id:
                            rec.estado_presupuesto = valor_vigente
                            if rec.recontactar < date.today():
                                rec.recontactar = date.today()

                        guarda = rec.search([
                            ('recontactar', '>', fields.Date.to_string(date.today() + relativedelta(days=4))),
                            ('id', '=', rec.id)
                        ])
                        if guarda.id == rec.id:
                            rec.estado_presupuesto = valor_pausado

                        # ANALIZA CALENDARIO
                        rec.calendario = rec._analiza_calendario(1)
        else:
            if 'recontactar' in vals:
                if vals.get('recontactar'):

                    valor_pausado = rec.env['abatar.estados.presupuesto'].search(
                        [('name', '=', 'Pausado')])
                    valor_vigente = self.env['abatar.estados.presupuesto'].search(
                        [('name', '=', 'Vigente')])
                    # ANALIZA ESTADO VIGENTE/PAUSADO
                    guarda = self.search([
                        ('recontactar', '<=', fields.Date.to_string(date.today() + relativedelta(days=4))),
                        ('id', '=', self.id)
                    ])
                    if guarda.id == self.id:
                        self.estado_presupuesto = valor_vigente
                        if self.recontactar < date.today():
                            self.recontactar = date.today()

                    guarda = self.search([
                        ('recontactar', '>', fields.Date.to_string(date.today() + relativedelta(days=4))),
                        ('id', '=', self.id)
                    ])
                    if guarda.id == self.id:
                        self.estado_presupuesto = valor_pausado

                    # ANALIZA CALENDARIO
                    self.calendario = self._analiza_calendario(1)




        return res

    def _analiza_calendario(self, tipo):

        # LO PRIMERO ES BORRAR LA ANTERIOR CRM.
        cuenta = 0
        if self.calendario:
            for ej in self.calendario.calendario_lines:
                cuenta += 1
            for ex in self.calendario.calendario_lines:
                if ex.crm.id == self.id:
                    ex.unlink()
                    if cuenta == 1:
                        revisac = self.env['abatar.calendario'].search(
                            [('id', '=', self.calendario.id)])
                        if revisac:
                            revisac.unlink()

        revisa_uno = self.env['abatar.servicios.calendario'].search(
            [('name', '=', 'Presupuesto')])

        revisac = self.env['abatar.calendario'].search(
            [('accion', '=', revisa_uno.id), ('recontactar', '=', self.recontactar)])

        if revisac:
            vals1 = {
                'crm': self.id,
                'calendario_id': revisac.id,
            }
            revisac.write({'calendario_lines': [(0, 0, vals1)]})
            return revisac.id

        else:
            calen_id=self.env['abatar.calendario'].search([], order='id desc', limit=1).id+1

            vals1 = {
                'crm': self.id,
                'calendario_id': calen_id,
            }
            vals2 = {
                'name': 'CRM',
                'name_oculto': 'CRM',
                'accion': revisa_uno.id,
                'fecha_ejecucion': self.recontactar2,
                'recontactar': self.recontactar,
                'calendario_lines': [(0, 0, vals1)],
            }
            return self.env['abatar.calendario'].create(vals2)

    @api.one
    def action_crea_factura(self):
        factuso=False
        mont_fact=0
        id_ult_fact=0
        if self.registro_pagos:
            for elem in self.registro_pagos:
                if elem.factura_id:
                    id_ult_fact=elem.factura_id.id
                    mont_fact+=elem.monto
                    factuso=True
        if factuso and mont_fact==self.precio_mas_iva:
            self.active = False
            self.factura = id_ult_fact
            self.factura.crm= self.id
            self.factura_line_ppal=True
        else:


            self.active=False
            dni = ""
            if self.cliente:
                sujeto=self.cliente.name_gral2
                clien=self.cliente.id
                if self.cliente.cuit:
                    id_client=self.cliente.cuit
                    dni=self.cliente.cuit
                else:
                    id_client=0

            else:

                sujeto= self.name
                clien=False
                id_client=0
            vals2 = {
                'crm': self.id,
                'sujeto': sujeto,
                'resumenes': False,
                'cliente': clien,
                'cuit': id_client,
                'sujeto': sujeto,
                'dni': dni,
                'tipo_fc': self.tipo_fc,
                'monto': self.precio,
            }

            resu = self.env['abatar.factura'].create(vals2)
            self.factura = resu.id

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.factura',
            'res_id': self.factura.id,
        }

    @api.onchange('factura')
    def action_no_crea_factura(self):
        if self.factura:
            self.active = False
            self.factura_line_ppal=True

    @api.multi
    def action_view_factura(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.factura',
            'res_id': self.factura.id,
        }

    def copy(self, default=None, context=None):


        revisb = self.env['abatar.servicios.estados'].search(
            [('name', '=', 'Pendiente')])

        revisa = self.env['abatar.estados.presupuesto'].search(
            [('name', '=', 'Pendiente')])

        if default is None:
            default = {}
        # Todo code (You can pass your value of any field in default)
        default.update({'factura': False,
                        'calendario': False,
                        'cotizador': False,
                        'user_id': self.env.user.id,
                        'pedide': self.env['ir.sequence'].next_by_code('abatar.pedido.sequence') or _('New'),
                        'state': 'pendiente',
                        'estado': revisb.id,
                        'estado_presupuesto': revisa.id,
                        'fecha_confirmacion': False,
                        'registro_pagos': [(5,0,0)],
                        'acciones_venta_lines': [(5,0,0)],
                        'adjuntos': [(5,0,0)],
                        'rechazado': False,
                        'active': True,
                        'registro_charla': [(5,0,0)],
                        })
        res= super(AbatarCRM, self).copy(default)
        for direc in self.destinos_lines:
            vals={}
            for field in direc.fields_get():
                if field=='orden_id_x':
                    vals['orden_id_x']=res.id
                elif field=='destino_id':
                    vals[field]=direc[field].id
                elif field=='orden_id':
                    vals['orden_id']=False
                else:
                    vals[field]=direc[field]
            res.destinos_lines.create(vals)
        for direc in self.destinos_lines2:
            vals={}
            for field in direc.fields_get():
                if field=='orden_id_x':
                    vals['orden_id_x']=res.id
                elif field=='orden_id':
                    vals['orden_id']=False
                else:
                    vals[field]=direc[field]
            fields.Glog('DESTINO_LINES2 ERROR vals:%s'%str(vals))
            res.destinos_lines2.create(vals)
        return res

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            print('HOla, aca se cita el new_sequence de CRM ')
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('abatar.crm.sequence') or _('New')
            vals['esnuevo'] = False
        if vals.get('pedide', _('New')) == _('New'):
            vals['pedide'] = self.env['ir.sequence'].next_by_code('abatar.pedido.sequence') or _('New')

        text = ''
        text2 = ''
        if vals['fecha_ejecucion']:
            if type(vals['fecha_ejecucion'])==str:
                datetime_ejecucion=datetime.strptime(vals['fecha_ejecucion'], '%Y-%m-%d %H:%M:%S')
            else:
                datetime_ejecucion=vals['fecha_ejecucion']

            prevday=datetime_ejecucion-timedelta(hours=3)-timedelta(days=1)
            text2=(datetime_ejecucion-timedelta(hours=3)-timedelta(days=1)).strftime('%d/%m/%Y')
            text=(datetime_ejecucion-timedelta(hours=3)).strftime('%d/%m/%Y - %H:%M')

            dias={
                calendar.weekday(2023, 4,3):'Lun',
                calendar.weekday(2023, 4,4):'Mar',
                calendar.weekday(2023, 4,5):'Mie',
                calendar.weekday(2023, 4,6):'Jue',
                calendar.weekday(2023, 4,7):'Vie',
                calendar.weekday(2023, 4,8):'Sab',
                calendar.weekday(2023, 4,9):'Dom',
            }
            if prevday.weekday():
                text2=dias[prevday.weekday()]+' '+text2
            vals['fecha_previa_name']=text2
            if datetime_ejecucion.weekday():
                text = dias[datetime_ejecucion.weekday()] + ' ' + text
            vals['fecha_ejecucion_name']= text
        result = super(AbatarCRM, self).create(vals)
        return result

class AbatarRestriccionesList(models.Model):
    _name = "abatar.restricciones.list"
    _description = "Abatar lista de Restricciones"
    _rec_name = 'desc_restricciones'

    fecha_op = fields.Date("Fecha", default=fields.Date.today)
    desc_restricciones=fields.Text(string="Descripcion")
    bool_restricciones=fields.Boolean(string="cumplida?", default=False)

    crm_id = fields.Many2one('abatar.crm', string='crm ID')
    orden_id = fields.Many2one('abatar.ordenes', string='orden ID')

    @api.multi
    def write(self,vals):
        res = super(AbatarRestriccionesList, self).write(vals)
        fields.Glog("DEBUG RESTRICCIONES:")
        fields.Glog("vals:"+str(vals))
        if 'bool_restricciones' in vals.keys():
            if vals['bool_restricciones']==False:
                fields.Glog("BOOL FALSE!"+str(vals))
                if self.crm_id:
                    self.crm_id.set_revisar(False)
                elif self.orden_id:
                    self.orden_id.set_revisar(False)
            else:
                if self.crm_id:
                    incumplida = False
                    for elem in self.crm_id.list_restricciones:
                        if not elem.bool_restricciones:
                            fields.Glog("Loop restricc lines OK (inclumplido)")
                            self.crm_id.set_revisar(False)
                            incumplida=True
                            break
                    if not incumplida:
                        fields.Glog("Loop restricc lines OK (Todo OK")
                        self.crm_id.set_revisar(True)
                elif self.orden_id:
                    incumplida = False
                    for elem in self.orden_id.list_restricciones:
                        if not elem.bool_restricciones:
                            fields.Glog("Loop restricc lines OK (inclumplido)")
                            self.orden_id.set_revisar(False)
                            incumplida=True
                            break
                    if not incumplida:
                        fields.Glog("Loop restricc lines OK (Todo OK")
                        self.orden_id.set_revisar(True)


        return res


class AbatarCrmAdjuntos(models.Model):
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

class AbatarCrmAcciones(models.Model):
    _name = "abatar.crm.acciones"
    _description = "Abatar Acciones de crm"
    _rec_name = 'venta_accion'
    _order = 'fecha desc, id desc'

    venta_accion=fields.Many2one('abatar.acciones.presupuesto',string='Acciones venta', required=True)
    fecha = fields.Date("Fecha", default=fields.Date.today, required=True)
    desc=fields.Char(string="Respuesta")
    vto=fields.Integer(string="Días Vto. sugerido", related="venta_accion.vto", store=True, readonly=True)
    vto_f=fields.Integer(string="Días Vto.")
    rta=fields.Selection([("si", "Si"),("no", "No")],string="Se resolvió?")
    vencido=fields.Binary(string="Vencido", compute='set_vencido')

    crm_id = fields.Many2one('abatar.crm', string='crm ID')

    @api.onchange('vto')
    def set_vto_f(self):
        for rec in self:
            if rec.vto:
                rec.vto_f=rec.vto



    @api.depends("fecha","vto_f","rta")
    def set_vencido(self):
        for rec in self:
            if rec.fecha and rec.vto_f:
                if fields.Date.today()>rec.fecha+relativedelta(days=rec.vto_f):
                    if not rec.rta:
                        image_path = modules.get_module_resource('om_abatartrucks', 'static/src/img', 'cruzno.png')
                        rec.vencido= tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))
                    else:

                        rec.vencido= False
                else:

                    rec.vencido= False
            else:

                rec.vencido= False


class AbatarCrmAccionesC(models.Model):
    _name = "abatar.crm.accionesc"
    _description = "Abatar Acciones Compra de crm"
    _rec_name = 'compra_accion'
    _order = 'fecha desc, id desc'

    compra_accion=fields.Many2one('abatar.accionesc.presupuesto',string='Acciones compra', required=True)
    fecha = fields.Date("Fecha", default=fields.Date.today, required=True)
    vto=fields.Integer(string="Días Vto.", related="compra_accion.vto", store=True, readonly=True)
    desc=fields.Char(string="Respuesta")
    rta=fields.Selection([("si", "Si"),("no", "No")],string="Se resolvió?")
    vencido=fields.Binary(string="Vencido")

    crm_id = fields.Many2one('abatar.crm', string='crm ID')

    @api.onchange("fecha","vto","rta")
    def set_vencido(self):
        for rec in self:
            if rec.fecha and rec.vto:
                if fields.Date.today()>rec.fecha+relativedelta(days=rec.vto):
                    if not rec.rta:
                        image_path = modules.get_module_resource('om_abatartrucks', 'static/src/img', 'cruzno.png')
                        rec.vencido= tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))
                    else:

                        rec.vencido= False
                else:

                    rec.vencido= False
            else:

                rec.vencido= False

class AbatarOrdenesCharla(models.Model):
    _name = "abatar.registro.charla"
    _description = "Abatar registro charla"
    _order = 'fecha desc'

    texto = fields.Text(string='texto', required=True)
    fecha = fields.Datetime(string='Fecha', required=True)
    orden_id_x = fields.Many2one('abatar.crm', string='Orden ID')



class AbatarOrdenesPagos(models.Model):
    _name = "abatar.registro.pagos"
    _description = "Abatar registro pagos"
    _rec_name='monto'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.fecha:
                caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', rec.fecha)])

                crm = self.orden_id_x
                if caja_act.linea_movimientos:
                    for elem in caja_act.linea_movimientos:
                        if elem.tipo.id == self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                            if elem.texto.find('Adelanto cobrado en fecha por Pedido %s' % crm.pedide)>-1:
                                if elem.monto == rec.monto:
                                    elem.unlink()
                                    break
                                elif rec.monto:
                                    elem.monto -= rec.monto
                                    break
            if rec.factura_id:
                rec.factura_id.unlink()

        res = super(AbatarOrdenesPagos, self).unlink()
        return res


    monto = fields.Float(string='Monto', required=True)
    pago_electronico = fields.Boolean(string='Pago electrónico?', default=False)
    fecha = fields.Date(string='Fecha', required=True)
    factura_id=fields.Many2one('abatar.factura', string='Factura ID', default=False)
    orden_id = fields.Many2one('abatar.ordenes', string='Orden ID')
    orden_id_x = fields.Many2one('abatar.crm', string='Orden ID')

    @api.model
    def create(self, vals):
        if vals.get('orden_id_x'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', vals.get('fecha'))])

            if not caja_act:
                id_caja = self.env['abatar.caja'].search([], order='id desc', limit=1).id + 1
            else:
                id_caja = caja_act.id
            crm=self.env['abatar.crm'].search([('id', '=', vals.get('orden_id_x'))])
            if vals.get('pago_electronico'):
                pago_elec=vals.get('pago_electronico')
            else:
                pago_elec=False
            fact=False
            str_ad=''
            if vals.get('factura_id'):
                fact=vals.get('factura_id')
                fact_id=self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
                fact_id.write({'active':False})
                str_ad+='. Factura %s Nª %s'%(fact_id.tipo_fc, fact_id.name_seq)

            pagos_list={
                'tipo': self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id,
                'texto': 'Adelanto cobrado en fecha por Pedido %s %s' % (crm.pedide, str_ad),
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
        result = super(AbatarOrdenesPagos, self).create(vals)

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

            fact_ant = self.factura_id
            if fact_ant:
                str_ad = '. Factura %s Nº %s' % (fact_ant.tipo_fc, fact_ant.name_seq)

            else:
                str_ad=''

            if self.factura_id:
                fact_an=self.factura_id
                fact_ant = self.env['abatar.factura'].search([('id', '=', fact_an)], limit=1)
            if vals.get('factura_id'):
                fact = vals.get('factura_id')
                fact_id = self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
            elif self.factura_id:
                fact=self.factura_id
                fact_id = self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
            else:
                fact_id=False
            if vals.get('factura_id'):
                if fact_ant:
                    fact_ant.write({'active': True})
                fact_id.write({'active': False})
                str_ad += '. Factura %s Nº %s' % (fact_id.tipo_fc, fact_id.name_seq)

            crm=self.orden_id_x
            if caja_ant.linea_movimientos:
                for elem in caja_ant.linea_movimientos:
                    if elem.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                        if elem.texto.find('Adelanto cobrado en fecha por Pedido %s' % crm.pedide)>-1:
                            if elem.monto==self.monto:
                                elem.unlink()
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

            pagos_list={
                'tipo': self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id,
                'texto': 'Adelanto cobrado en fecha por Pedido %s %s' % (crm.pedide, str_ad),
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

            fact_ant = self.factura_id
            if fact_ant:
                str_ad = '. Factura %s Nº %s' % (fact_ant.tipo_fc, fact_ant.name_seq)
            else:
                str_ad=''
            if vals.get('factura_id'):
                fact = vals.get('factura_id')
                fact_id = self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
                str_ad += '. Factura %s Nº %s' % (fact_id.tipo_fc, fact_id.name_seq)

                if fact_ant:
                    fact_ant.write({'active': True})
                fact_id.write({'active': False})

            crm=self.orden_id_x
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                        if elem.texto.find('Adelanto cobrado en fecha por Pedido %s' % crm.pedide)>-1:
                            elem.write({'monto':vals.get('monto')})
                            elem.write({'pago_electronico':pago_elec})
                            elem.write({'texto': 'Adelanto cobrado en fecha por Pedido %s %s' % (crm.pedide, str_ad)})
                            break
        elif vals.get('pago_electronico'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', self.fecha)])

            id_caja = caja_act.id

            pago_elec = vals.get('pago_electronico')

            fact_ant = self.factura_id
            if fact_ant:
                str_ad = '. Factura %s Nº %s' % (fact_ant.tipo_fc, fact_ant.name_seq)
            else:
                str_ad=''
            if vals.get('factura_id'):
                fact = vals.get('factura_id')
                fact_id = self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
                str_ad += '. Factura %s Nº %s' % (fact_id.tipo_fc, fact_id.name_seq)

                if fact_ant:
                    fact_ant.write({'active': True})
                fact_id.write({'active': False})

            crm = self.orden_id_x
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id == self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                        if elem.texto.find('Adelanto cobrado en fecha por Pedido %s' % crm.pedide)>-1:
                            elem.write({'pago_electronico': pago_elec})
                            if fact_ant:
                                if fact_ant==fact_id:
                                    pass
                                else:
                                    elem.write({'texto': 'Adelanto cobrado en fecha por Pedido %s %s' % (crm.pedide, str_ad)})
                            break
        elif vals.get('factura_id'):
            caja_act = self.env['abatar.caja'].search([('fecha_de_caja', '=', self.fecha)])

            id_caja = caja_act.id

            pago_elec = self.pago_electronico

            fact_ant=self.factura_id
            str_ad=''
            if vals.get('factura_id'):
                fact = vals.get('factura_id')
                fact_id = self.env['abatar.factura'].search([('id', '=', fact)], limit=1)
                str_ad += '. Factura %s Nº %s' % (fact_id.tipo_fc, fact_id.name_seq)

                if fact_ant:
                    fact_ant.write({'active': True})
                fact_id.write({'active': False})

            crm = self.orden_id_x
            if caja_act.linea_movimientos:
                for elem in caja_act.linea_movimientos:
                    if elem.tipo.id == self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                        if elem.texto.find('Adelanto cobrado en fecha por Pedido %s' % crm.pedide)>-1:

                            elem.write({'texto': 'Adelanto cobrado en fecha por Pedido %s %s' % (crm.pedide, str_ad)})
                            break

        res = super(AbatarOrdenesPagos, self).write(vals)

        return res


class AbatarCrmPresupuestos(models.Model):
    _name = "abatar.crm.presupuestos"
    _description = "Abatar registro Presupuestos"
    _rec_name='monto'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.proveedor_id:
                rec.proveedor_id=False

        res = super(AbatarCrmPresupuestos, self).unlink()
        return res


    monto = fields.Float(string='Monto', required=True)
    pago_electronico = fields.Boolean(string='Pago electrónico?', default=False)
    requisitos = fields.Boolean(string='Ya Cumple Requisitos?', default=False)
    forma_de_pago = fields.Char(string='Forma de pago', default=False)
    m3_incluye = fields.Float(string='m3 que Incluye', default=0)
    hs_incluye = fields.Float(string='Hs que Incluye', default=0)
    kms_incluye = fields.Float(string='Kms que Incluye', default=0)
    fecha = fields.Date(string='Fecha', required=True)
    desc = fields.Char(string='Descripcion', default='')
    proveedor_id=fields.Many2one('abatar.proveedores', string='Proveedor ID', default=False)
    productos=fields.Many2one('abatar.productos', string='Producto', default=False)
    orden_id_x = fields.Many2one('abatar.crm', string='Orden ID')
    mas_iva = fields.Boolean(string='+ IVA', default=False)
    dolar_uso = fields.Float(string='Dolar',store=True, readonly=True, compute='set_dolar')
    dolar2_uso = fields.Float(string='Dolar(Of)',store=True, readonly=True, compute='set_dolar')
    monto_dolar = fields.Float(string='Monto U$D',store=True, readonly=True, compute='set_monto_dolar')

    #@api.onchange('desc')
    def set_todos_dolar(self):
        for rec in self.env['abatar.crm.presupuestos'].search([]):
            rec.monto+=1
            rec.monto-=1
            

    @api.depends('fecha', 'monto','dolar_uso')
    def set_monto_dolar(self):
        for rec in self:
            if rec.dolar_uso:
                rec.monto_dolar=rec.monto/rec.dolar_uso

    @api.depends('fecha', 'monto')
    def set_dolar(self):
        for rec in self:
            if rec.fecha:
                dolar_uso=0
                dolar2_uso=0
                fecha_orden= str(fields.Date.from_string(rec.fecha).strftime('%d/%m/%y'))
                dia_ejec=int(fecha_orden[:fecha_orden.find('/')])
                rest=fecha_orden[fecha_orden.find('/')+1:]
                mes_ejec=int(rest[:rest.find('/')])
                rest2=rest[rest.find('/')+1:]
                año_ejec=2000+int(rest2[:])

                actu=self.env['abatar.dolar'].search([('fecha', '=', fields.Date.from_string(rec.fecha))], limit=1)
                if actu:
                    if actu.pesos:
                        dolar_uso=actu.pesos


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

                        if actu:
                            if actu.pesos:
                                dolar_uso=actu.pesos
                                break

                    if dolar_uso==0:
                        actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                        if actu:
                            if actu.pesos:
                                rec.dolar_uso=actu.pesos

                rec.dolar_uso=dolar_uso

                actu=self.env['abatar.dolar2'].search([('fecha', '=', fields.Date.from_string(rec.fecha))], limit=1)
                if actu:
                    if actu.pesos:
                        dolar2_uso=actu.pesos

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

                        if actu:
                            if actu.pesos:
                                dolar2_uso=actu.pesos
                                break

                        if dolar2_uso==0:
                            actu = self.env['abatar.dolar2'].search([], order='fecha desc', limit=1)
                            if actu:
                                if actu.pesos:
                                    rec.dolar2_uso=actu.pesos
                rec.dolar2_uso=actu.pesos


class AbatarServicios(models.Model):
    _name = "abatar.servicios"
    _description = "Abatar servicios"
    _rec_name = "name_gral"

    name_gral=fields.Char(string='Servicio', compute='set_name_gral')
    name = fields.Char(string='Servicio')

    @api.depends('name')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=''
            if rec.name:
                if rec.id:
                    rec.name_gral+=str(rec.id)+' - '+rec.name
                else:
                    rec.name_gral+=rec.name


class AbatarPresupuestoEstado(models.Model):
    _name = "abatar.estados.presupuesto"
    _description = "Abatar estado presupuesto"
    _rec_name = "name"

    name = fields.Char(string='Estado Presupuesto')

class AbatarPresupuestoAccion(models.Model):
    _name = "abatar.acciones.presupuesto"
    _description = "Abatar Acciones presupuesto"
    _rec_name = "name"

    name = fields.Char(string='Accion Presupuesto')
    vto = fields.Integer(string='Duración de la Acción (días)')

class AbatarPresupuestoAccionC(models.Model):
    _name = "abatar.accionesc.presupuesto"
    _description = "Abatar Acciones Compra presupuesto"
    _rec_name = "name"

    name = fields.Char(string='Accion Compra Presupuesto')
    vto = fields.Integer(string='Duración de la Acción (días)')

class AbatarPresupuestoRechazo(models.Model):
    _name = "abatar.rechazado.presupuesto"
    _description = "Abatar Rechazos de presupuesto"
    _rec_name = "name"

    name = fields.Char(string='Motivo de Rechazo')
    hizo = fields.Boolean(string='Implica que Realizó con otro?')

class AbatarServiciosEstados(models.Model):
    _name = "abatar.servicios.estados"
    _description = "Abatar servicios"
    _rec_name = "name"
    _order="orden_name asc"

    name = fields.Char(string='Estado')
    orden_name = fields.Char(string='Estado')

class AbatarServiciosTipo(models.Model):
    _name = "abatar.servicios.tipo"
    _description = "Abatar servicios tipo"
    _rec_name = "name"

    name = fields.Char(string='Estado')

class AbatarServiciosCalendario(models.Model):
    _name = "abatar.servicios.calendario"
    _description = "Abatar servicios calendario"
    _rec_name = "name"

    name = fields.Char(string='Estado')
    accion = fields.Many2one('abatar.servicios.tipo', string='tipo', required=True)


class AbatarWsp(models.Model):
    _name = "abatar.textos.wsp"
    _description = "Abatar textos wsp"
    _rec_name = "name"

    name = fields.Char(string='Nombre')
    accion_in = fields.Many2one('abatar.acciones.presupuesto',help='Acción que se aplicará en el CRM al presionar ENVIAR. Si se desea omitir: borrar el contenido del campo.',string='Accion asociada para CRM')
    texto = fields.Text(string='Texto')

class AbatarChatAutomatico(models.Model):
    _name = "abatar.chat.auto"
    _description = "Abatar chat auto"
    _rec_name = "nombre"

    channel_ids = fields.Many2one('mail.channel', string='channel')
    crm_ids = fields.Many2one('abatar.crm', string='channel')
    nombre = fields.Char(string='Nombre')
    telefono = fields.Char(string='telefono')
    ambientes = fields.Char(string='ambientes')
    habitantes = fields.Char(string='habitantes')
    origen = fields.Char(string='calle_origen')
    tipo_origen = fields.Char(string='Telefono')
    piso_origen = fields.Char(string='Telefono')
    ascensor_origen = fields.Char(string='Telefono')
    destino = fields.Char(string='Telefono')
    tipo_destino = fields.Char(string='Telefono')
    piso_destino = fields.Char(string='Telefono')
    ascensor_destino = fields.Char(string='Telefono')
    embalaje_fino = fields.Char(string='Telefono')
    categoria = fields.Char(string='Telefono')
    precio_total = fields.Char(string='Telefono')
    kms_recorrido = fields.Float(string='Telefono')
    tiempo_viaje = fields.Float(string='Telefono')