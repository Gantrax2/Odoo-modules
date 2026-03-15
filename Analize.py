from odoo import models, fields, api, _
import datetime
import numpy as np
import ast, subprocess, logging
import requests

BUSQUEDAON=True
PROVINCIAS=[('Buenos Aires', 'Buenos Aires'), ('La Pampa', 'La Pampa'), ('Jujuy', 'Jujuy'),
                                  ('Salta', 'Salta'), ('Formosa', 'Formosa'), ('Chaco', 'Chaco'),
                                  ('Catamarca', 'Catamarca'), ('Tucuman', 'Tucuman'),
                                  ('Santiago del Estero', 'Santiago del Estero'), ('La Rioja', 'La Rioja'),
                                  ('Cordoba', 'Cordoba'), ('Santa Fe', 'Santa Fe'), ('Corrientes', 'Corrientes'),
                                  ('Misiones', 'Misiones'), ('San Juan', 'San Juan'), ('Entre Rios', 'Entre Rios'),
                                  ('San Luis', 'San Luis'), ('Mendoza', 'Mendoza'), ('Neuquen', 'Neuquen'),
                                  ('Rio Negro', 'Rio Negro'), ('Chubut', 'Chubut'), ('Santa Cruz', 'Santa Cruz'),
                                  ('Tierra del Fuego', 'Tierra del Fuego')]
BSAS_ZONAS=[('Centro','Centro'),('Norte', 'Norte'),('Oeste', 'Oeste'),('SurOeste', 'SurOeste'),('Sur', 'Sur')]
TOTAL_ZONAS=BSAS_ZONAS+PROVINCIAS

POLY_ZONAS= {'Norte':[[-34.531195, -58.458125],[-34.072982, -59.037599],[-34.370383, -59.124632], [-34.587660, -58.531580]],
             'Oeste':[[-34.587660, -58.531580],[-34.370383, -59.124632],[-34.617260, -59.185154],[-35.113459, -58.837157],[-34.816349, -58.640187],[-34.687581, -58.492369]],
             'SurOeste':[[-34.687581, -58.492369],[-34.816349, -58.640187],[-35.113459, -58.837157],[-35.186190, -58.235672],[-34.783624, -58.383925],[-34.703570, -58.460170]],
             'Sur':[[-34.703570, -58.460170],[-34.783624, -58.383925],[-35.186190, -58.235672],[-34.976478, -57.623598],[-34.623439, -58.292855]],
             'Centro':[[-34.567888, -58.344067],[-34.531195, -58.458125],[-34.587660, -58.531580],[-34.687581, -58.492369],[-34.703570, -58.460170],[-34.623439, -58.292855]]}

import requests


def enviar_mensajegral(mensaje):
    # URL del Webhook de n8n
    api_url = "https://n8n-n8n-pruebas.juo2x0.easypanel.host/webhook-test/odoo-mensaje"

    # Datos que se van a enviar en la solicitud
    data = {
        'message': mensaje['data']
    }

    # Realizando la solicitud POST
    response = requests.post(api_url, json=data)


    # Verificar el estado de la respuesta
    if response.status_code == 200:
        # Si la solicitud es exitosa, imprimir la respuesta en formato JSON
        return True, response.json()  # Exito
    else:
        # Si la solicitud falla, imprimir el mensaje de error
        return False, response.text  # Fracaso


def enviar_mensaje(mensaje):
    # URL del Webhook de n8n
    api_url = "" #"https://n8n-n8n-pruebas.kznq6m.easypanel.host/webhook-test/odoo-mensaje"

    # Datos que se van a enviar en la solicitud
    data = {
        'phone': '+54'+mensaje['tel'],  # Número de teléfono con código de país
        'message': mensaje['data']
    }

    # Realizando la solicitud POST
    response = requests.post(api_url, json=data)


    # Verificar el estado de la respuesta
    if response.status_code == 200:
        # Si la solicitud es exitosa, imprimir la respuesta en formato JSON
        return True, response.json()  # Exito
    else:
        # Si la solicitud falla, imprimir el mensaje de error
        return False, response.text  # Fracaso


def string_comma_to_list(a):
    filtro0 = a
    if filtro0:
        provs0 = []
        while filtro0.find(',') > -1:
            provs0.append(filtro0[:filtro0.find(',')])
            filtro0 = filtro0[filtro0.find(',') + 1:]
        provs0.append(filtro0)
        return provs0
    else:
        return []



def execVariable(a):
    result = subprocess.run(["python", "-c", "a=%s;print(a)" % a], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    _logger = logging.getLogger(__name__)
    if result.stderr:
        _logger.error('YOGASTONADM: Cargavisor res.dominio')
        _logger.error("there was an error :\n")
        _logger.error(result.stderr.decode("utf-8"))
        raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))
    return ast.literal_eval(result.stdout.decode("ascii"))

def execCode(a):
    result = subprocess.run(["python", a], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    _logger = logging.getLogger(__name__)
    if result.stderr:
        _logger.error('YOGASTONADM: Cargavisor res.dominio')
        _logger.error("there was an error :\n")
        _logger.error(result.stderr.decode("utf-8"))
        raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))
    return ast.literal_eval(result.stdout.decode("ascii"))

def Analize_DATETF(elem):
    str0 = elem[len('DATETF:'):]
    dayL = int(str0[:str0.find('/')])
    str0 = str0[str0.find('/') + 1:]
    monthL = int(str0[:str0.find('/')])
    yearL = int(str0[str0.find('/') + 1:])
    return fields.datetime.now().replace(day=dayL, month=monthL, year=yearL, hour=0, minute=0, second=0)

def Analize_DATEF(elem):
    str0 = elem[len('DATEF:'):]
    dayL = int(str0[:str0.find('/')])
    str0 = str0[str0.find('/') + 1:]
    monthL = int(str0[:str0.find('/')])
    yearL = int(str0[str0.find('/') + 1:])
    return fields.datetime.now().replace(day=dayL, month=monthL, year=yearL, hour=0, minute=0, second=0).date()

def Analize_DATETL(elem):
    str0 = elem[len('DATETL:'):]
    Indicador = int(str0[:str0.find('/')])
    str0 = str0[str0.find('/') + 1:]
    cantL = int(str0)
    if Indicador in ('D','d'):
        dia=int(fields.datetime.now().day/cantL)
        return fields.datetime.now().replace(day=dia)
    elif Indicador in ('M','m'):
        mes=int(fields.datetime.now().month/cantL)
        return fields.datetime.now().replace(month=mes)
    elif Indicador in ('Y','y'):
        año=int(fields.datetime.now().year/cantL)
        return fields.datetime.now().replace(year=año)

def Analize_DATEL(elem):
    str0 = elem[len('DATEL:'):]
    Indicador = int(str0[:str0.find('/')])
    str0 = str0[str0.find('/') + 1:]
    cantL = int(str0)
    if Indicador in ('D','d'):
        dia=int(fields.datetime.now().day/cantL)
        return fields.datetime.now().replace(day=dia).date()
    elif Indicador in ('M','m'):
        mes=int(fields.datetime.now().month/cantL)
        return fields.datetime.now().replace(month=mes).date()
    elif Indicador in ('Y','y'):
        año=int(fields.datetime.now().year/cantL)
        return fields.datetime.now().replace(year=año).date()

def Analize_DATEBACK(elem):
    str0 = elem[len('DATEBACK:'):]
    dayL = int(str0)
    #str0 = str0[str0.find('/') + 1:]
    #monthL = int(str0[:str0.find('/')])
    #yearL = int(str0[str0.find('/') + 1:])
    return fields.datetime.now().date() - datetime.timedelta(days=dayL)

def Analize_DATEFORW(elem):
    str0 = elem[len('DATEFORW:'):]
    dayL = int(str0)
    #str0 = str0[str0.find('/') + 1:]
    #monthL = int(str0[:str0.find('/')])
    #yearL = int(str0[str0.find('/') + 1:])
    return fields.datetime.now().date() + datetime.timedelta(days=dayL)

def Analize_DATETBACK(elem):
    str0 = elem[len('DATETBACK:'):]
    dayL = int(str0)
    #str0 = str0[str0.find('/') + 1:]
    #monthL = int(str0[:str0.find('/')])
    #yearL = int(str0[str0.find('/') + 1:])
    fecha_pre=fields.datetime.now().date() - datetime.timedelta(days=dayL)
    return fields.datetime.now().replace(day=fecha_pre.day,month=fecha_pre.month, year=fecha_pre.year)

def Analize_DATETFORW(elem):
    str0 = elem[len('DATETFORW:'):]
    dayL = int(str0)
    #str0 = str0[str0.find('/') + 1:]
    #monthL = int(str0[:str0.find('/')])
    #yearL = int(str0[str0.find('/') + 1:])
    fecha_pre=fields.datetime.now().date() + datetime.timedelta(days=dayL)
    return fields.datetime.now().replace(day=fecha_pre.day,month=fecha_pre.month, year=fecha_pre.year)

def Analize_EMPLF(self,elem):
    str0 = elem[len('EMPLF:'):]
    return self.env['abatar.empleados'].search([('name', '=', str0)], limit=1).id

def COMPARESTRFUNC(res, elem):
    if type(elem) == str:
        if elem[:len('DATEBACK:')] == 'DATEBACK:':
            return Analize_DATEBACK(elem)
        elif elem[:len('DATETBACK:')] == 'DATETBACK:':
            return Analize_DATETBACK(elem)
        elif elem[:len('DATEFORW:')] == 'DATEFORW:':
            return Analize_DATEFORW(elem)
        elif elem[:len('DATETFORW:')] == 'DATETFORW:':
            return Analize_DATETFORW(elem)
        elif elem[:len('DATEF:')] == 'DATEF:':
            return Analize_DATEF(elem)
        elif elem[:len('DATETF:')] == 'DATETF:':
            return Analize_DATETF(elem)
        elif elem[:len('DATEL:')] == 'DATEL:':
            return Analize_DATEL(elem)
        elif elem[:len('DATETL:')] == 'DATETL:':
            return Analize_DATETL(elem)
        elif elem[:len('EMPLF:')] == 'EMPLF:':
            return Analize_EMPLF(res, elem)
        else:
            return elem
    else:
        return elem

def CALCULA_INDICADOR(rec):
    resultf = False
    if rec:
        if rec.modelo:
            dominio = []
            if rec.dominio:
                result = subprocess.run(["python", "-c", "import datetime\na=%s;print(a)" % rec.dominio],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                _logger = logging.getLogger(__name__)
                if result.stderr:
                    raise UserWarning("AUTO REFRESH : there was an error :\n" + result.stderr.decode("utf-8"))
                list_dom0 = ast.literal_eval(result.stdout.decode("ascii"))
                list2 = []
                for conds in list_dom0:
                    list2elem = []
                    for elem in conds:
                        list2elem.append(COMPARESTRFUNC(rec, elem))
                    list2.append((list2elem[0], list2elem[1], list2elem[2]))
                dominio = list2.copy()
            fields.Glog('GASTON94 dominio:%s' % str(dominio))
            if rec.salida:
                if rec.salida == 'cuenta':
                    resultf = rec.env[rec.modelo].search_count(dominio)


                elif rec.salida == 'suma':
                    results = rec.env[rec.modelo].search(dominio)
                    suma = 0
                    for res in results:
                        if rec.campo_x in res:
                            suma += res[rec.campo_x]
                    resultf = suma
                elif rec.salida == 'promedio':
                    count = 0
                    results = rec.env[rec.modelo].search(dominio)
                    suma = 0
                    for res in results:
                        if rec.campo_x in res:
                            suma += res[rec.campo_x]
                            count += 1
                    # rec.write({'campo_y':suma/count})
                    if count > 0:
                        resultf = suma / count

                elif rec.salida[:len('promedio_')] == 'promedio_':
                    #fields.Glog('GASTON94 promedio_ :%s' % (str(rec.name0) + ' ' + str(rec.name)))
                    str0 = rec.salida[len('promedio_'):]
                    Indicador = str0[0]

                    cantP = int(str0[2:])
                    count = 0
                    results = rec.env[rec.modelo].search(dominio, order='%s desc' % rec.fecha_indicador)
                    resultsB = rec.env[rec.modelo].search(dominio, order='%s desc' % rec.fecha_indicador, limit=1)
                    resultsA = rec.env[rec.modelo].search(dominio, order='%s asc' % rec.fecha_indicador, limit=1)
                    delday = resultsB[rec.fecha_indicador] - resultsA[rec.fecha_indicador]
                    if Indicador in ('D', 'd'):
                        sumaL = np.full(1 + int(delday.days / cantP), 0)
                    elif Indicador in ('M', 'm'):
                        sumaL = np.full(1 + int(delday.months / cantP), 0)
                    elif Indicador in ('Y', 'y'):
                        sumaL = np.full(1 + int(delday.years / cantP), 0)
                    for res in results:

                        #fields.Glog('GASTON94 promedio_ Itering...%s' % str(res[rec.fecha_indicador]))
                        if rec.campo_x:
                            delday1 = res[rec.fecha_indicador] - resultsA[rec.fecha_indicador]
                            if Indicador in ('D', 'd'):
                                sumaL[int(delday1.days / cantP)] += res[rec.campo_x]
                            if Indicador in ('M', 'm'):
                                sumaL[int(delday1.months / cantP)] += res[rec.campo_x]
                            if Indicador in ('Y', 'y'):
                                sumaL[int(delday1.years / cantP)] += res[rec.campo_x]

                        else:
                            delday1 = res[rec.fecha_indicador] - resultsA[rec.fecha_indicador]
                            if Indicador in ('D', 'd'):
                                sumaL[int(delday1.days / cantP)] += 1
                            if Indicador in ('M', 'm'):
                                sumaL[int(delday1.months / cantP)] += 1
                            if Indicador in ('Y', 'y'):
                                sumaL[int(delday1.years / cantP)] += 1

                    i0 = 0
                    while i0 < len(sumaL):
                        if sumaL[i0] == 0:
                            sumaL = np.array(list(sumaL)[:i0] + list(sumaL)[i0 + 1:])
                        else:
                            i0 += 1
                    resultf = sum(sumaL) / len(sumaL)
                elif rec.salida[:len('Promedio_')] == 'Promedio_':
                    #fields.Glog('GASTON94 Promedio_ :%s' % (str(rec.name0) + ' ' + str(rec.name)))
                    str0 = rec.salida[len('Promedio_'):]
                    Indicador = str0[0]

                    cantP = int(str0[2:])
                    count = 0
                    results = rec.env[rec.modelo].search(dominio, order='%s desc' % rec.fecha_indicador)
                    resultsB = rec.env[rec.modelo].search(dominio, order='%s desc' % rec.fecha_indicador, limit=1)
                    resultsA = rec.env[rec.modelo].search(dominio, order='%s asc' % rec.fecha_indicador, limit=1)
                    delday = resultsB[rec.fecha_indicador] - resultsA[rec.fecha_indicador]

                    year0 = resultsA[rec.fecha_indicador].year
                    maxdiv = resultsB[rec.fecha_indicador].year - year0
                    # if maxdiv>0:
                    #    sumaL = np.full(maxdiv,0)
                    #    cantL = np.full(maxdiv,0)
                    # else:
                    sumaL = np.full(15, 0)
                    cantL = np.full(15, 0)
                    try:
                        if resultsB[rec.fecha_indicador].hour >= 0:
                            today = datetime.datetime.now()
                    except:
                        today = datetime.datetime.now().date()

                    delday2 = today - today.replace(day=1, month=1)
                    if Indicador in ('D', 'd'):
                        ndiv = int(delday2.days / cantP)
                    elif Indicador in ('M', 'm'):
                        ndiv = int(delday2.months / cantP)
                    for res in results:
                        if res[rec.fecha_indicador].year < today.year:
                            #fields.Glog('GASTON94 Promedio_ Itering...%s' % str(res[rec.fecha_indicador]))
                            delday1 = res[rec.fecha_indicador] - res[rec.fecha_indicador].replace(day=1, month=1)

                            if rec.campo_x:
                                if Indicador in ('D', 'd'):
                                    if int(delday1.days / cantP) == ndiv:
                                        sumaL[res[rec.fecha_indicador].year - year0] += res[rec.campo_x]
                                        cantL[res[rec.fecha_indicador].year - year0] += 1
                                elif Indicador in ('M', 'm'):
                                    if int(delday1.months / cantP) == ndiv:
                                        sumaL[res[rec.fecha_indicador].year - year0] += res[rec.campo_x]
                                        cantL[res[rec.fecha_indicador].year - year0] += 1

                            else:
                                if Indicador in ('D', 'd'):
                                    if int(delday1.days / cantP) == ndiv:
                                        sumaL[res[rec.fecha_indicador].year - year0] += 1
                                        cantL[res[rec.fecha_indicador].year - year0] = 1
                                elif Indicador in ('M', 'm'):
                                    if int(delday1.months / cantP) == ndiv:
                                        sumaL[res[rec.fecha_indicador].year - year0] += 1
                                        cantL[res[rec.fecha_indicador].year - year0] = 1

                    i0 = 0
                    while i0 < len(cantL):
                        if cantL[i0] == 0:
                            sumaL = np.array(list(sumaL)[:i0] + list(sumaL)[i0 + 1:])
                            cantL = np.array(list(cantL)[:i0] + list(cantL)[i0 + 1:])
                        else:
                            i0 += 1

                    listprom = sumaL / cantL
                    if len(listprom)>0:
                        resultf = sum(listprom) / len(listprom)
                    else:
                        resultf =0

                elif rec.salida == 'max':
                    results = rec.env[rec.modelo].search(dominio)
                    max0 = -999999
                    max = max0
                    for res in results:
                        if rec.campo_x in res:
                            if res[rec.campo_x] > max:
                                max = res[rec.campo_x]
                    if max > max0:
                        resultf = max
                elif rec.salida == 'min':
                    results = rec.env[rec.modelo].search(dominio)
                    min0 = 999999
                    min = min0
                    for res in results:
                        if rec.campo_x in res:
                            if res[rec.campo_x] < min:
                                min = res[rec.campo_x]
                    if min < min0:
                        resultf = min
            else:
                resultf = rec.env[rec.modelo].search_count(dominio)
            # rec.write({'x_c': fields.datetime.now().date().strftime('%d/%m/%y')})
            # rec.write({'x_d': fields.datetime.now().date()})
            if rec.multiplicador:
                resultf *= rec.multiplicador
    return resultf


def execCode3(a,b=False):
    if b==False:

        result = subprocess.run(["python3", a], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _logger = logging.getLogger(__name__)
        if result.stderr:
            _logger.error('YOGASTONADM: Cargavisor res.dominio')
            _logger.error("there was an error :\n")
            _logger.error(result.stderr.decode("utf-8"))
            raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))
        return ast.literal_eval(result.stdout.decode("ascii"))
    else:
        result = subprocess.run(["python3", a,b], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _logger = logging.getLogger(__name__)
        if result.stderr:
            _logger.error('YOGASTONADM: Cargavisor res.dominio')
            _logger.error("there was an error :\n")
            _logger.error(result.stderr.decode("utf-8"))
            raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))
        return ast.literal_eval(result.stdout.decode("ascii"))


def execCode3_ret(a,b):
    _logger = logging.getLogger(__name__)
    _logger.error('YOGASTONADM: Cargadolar0')
    echo = subprocess.Popen(["echo", "45437154"], stdout=subprocess.PIPE)
    #_logger.error(echo.stdout.read().decode())
    #process = subprocess.run(["sudo","-S","python3", a,b], stdout=subprocess.PIPE, input=echo.stdout.read().decode(), encoding="utf-8",stderr=subprocess.PIPE) #
    process = subprocess.Popen(["su","-", "julian","-S","python", a,b], stdout=subprocess.PIPE, stdin=echo.stdout,stderr=subprocess.PIPE) #
    result, stderr=process.communicate()#echo.stdout.read())
    #result, stderr=process.communicate()
    #result, stderr=process.stdout.read().decode(),process.stderr.read().decode()
    _logger.error('YOGASTONADM: Cargadolar1')
    _logger.error(result.decode("utf-8"))
    _logger.error(stderr.decode("utf-8"))

    if stderr:
        _logger.error('YOGASTONADM: Cargadolar')
        _logger.error("there was an error :\n")
        _logger.error(stderr.decode("utf-8"))
        raise UserWarning("there was an error :\n" + stderr.decode("utf-8"))
        '''
        if 'contraseña' in result.stderr.decode("utf-8"):
            result.stdin='45437154'

            if result.stderr:
                _logger.error('YOGASTONADM: Cargadolar')
                _logger.error("there was an error :\n")
                _logger.error(result.stderr.decode("utf-8"))
                raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))

            else:
                montos = ast.literal_eval(result.stdout.decode("ascii"))
                _logger.error('YOGASTONADM: Carga dolar: %s ' % str(montos))
                return montos
        else:
            raise UserWarning("there was an error :\n" + result.stderr.decode("utf-8"))'''
    else:
        montos= ast.literal_eval(result.decode("ascii"))

        _logger.error('YOGASTONADM: Carga dolar: %s ' % str(montos))
        return montos


def Typyze(Type, elem, nottime=False):
    if nottime == False:
        if type(elem) == type(fields.datetime.now()):
            elem = elem.date()
            if Type == 'str':
                return fields.datetime.strftime(elem, '%d/%m/%Y')
        elif type(elem) == type(fields.datetime.now().date()):
            if Type == 'str':
                return fields.datetime.strftime(elem, '%d/%m/%Y')
    if Type in ('', '1', False):
        return elem
    elif Type == 'str':
        return str(elem)
    elif Type == 'int':
        return int(elem)
    elif Type == 'float':
        return float(elem)
    elif Type == 'list':
        return list(elem)
    elif Type == 'bool':
        return bool(elem)


def Typyze2(Type, elem): # funcion que recibe values para campos siempre en string y debe convertirlos al type correcto
    if type(Type) == type(fields.datetime.now()):
        return fields.datetime.strptime(elem, '%d/%m/%Y-%H:%M:%S')
    elif type(Type) == type(fields.datetime.now().date()):
        return fields.datetime.strptime(elem, '%d/%m/%Y')
    elif type(Type) == type(1) or Type==int:
        return int(elem)
    elif type(Type) == type(1.) or Type==float:
        return float(elem)
    elif type(Type) == type(False) or Type==bool:
        return bool(int(elem)) #aplicación especial, para n8n , recibe string con "0" o "1" segun bool False o True
    elif type(Type) == type('hola') or Type==str:
        return str(elem)




def Analize_model3(self, mod_name, dominio):
    a = ''
    clock=self.env['abatar.constantes'].search([('name','=','Resumen_clock')],limit=1)
    if clock.date_time < datetime.datetime.now():
        TYPELIST=(float, int, str, bool, type(fields.datetime.now()),type(fields.datetime.now().date()), type(fields.datetime), type(fields.Binary(attachment=True)), type(fields.Html()))
        MAXINTERC=20
        MAXINTERF=15
        REJECTLIST=['resumen_busqueda', 'create_date',  'write_date', '__last_update','user_id','user_ids','image','image_medium', 'image_small', 'message_ids','message_follower_ids', 'message_partner_ids', 'commercial_partner_id', 'create_uid', 'write_uid' ,'calendario' ,'calendario_id','cotizador' ,'cotizador_id','orden_id','orden_id_x','crm_id','crm_id_x']

        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: %s' % fields.datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
        _logger.error('YOGASTONADM: MODELO : %s' % mod_name)
        mod = self.env[mod_name].search(dominio, limit=1)
        for rec in mod:
            for Field in rec.fields_get():
                if Field not in REJECTLIST:
                    if rec[Field] not in (False,0,0.0) and type(rec[Field]) in TYPELIST:
                        a += str(Typyze('str', rec[Field])) + '\n'#Field + ' : ' +
                    else:
                        #_logger.error('YOGASTONADM: %s' % str(Field+' ; '+str(rec[Field])+' ; '+str(type(rec[Field]))))
                        #_logger.error('YOGASTONADM: %s' % rec[Field].ttype)
                        if rec._fields[Field].type=='one2many':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':

                            hu=0
                            for ei in rec[Field]:
                                hu2 = 0
                                for Field2 in ei.fields_get():
                                    if Field2 not in REJECTLIST:
                                        if ei[Field2] not in (False,0,0.0) and type(ei[Field2]) in TYPELIST:
                                            a += str(Typyze('str', ei[Field2])) + '\n'#Field + ' (' +  str(hu) + '): '  + Field2 + ' : ' +
                                        elif ei._fields[Field2].type=='many2one':
                                            hu22=0
                                            for Field3 in ei[Field2].fields_get():
                                                if Field3 not in REJECTLIST:
                                                    if ei[Field2][Field3] not in (False,0,0.0) and type(ei[Field2][Field3]) in TYPELIST:
                                                        a += str(Typyze('str', ei[Field2][Field3])) + '\n'#Field + '(' + str(hu) + '): ' + Field2 + ' -> ' + Field3 + ' : ' +

                                                    hu22 += 1

                                                    if hu22 > MAXINTERC:
                                                        break
                                        hu2 += 1

                                        if hu2 > MAXINTERC:
                                            break

                                hu += 1

                                if hu > MAXINTERF:
                                    break
                        elif rec._fields[Field].type=='many2one':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                            hu3=0
                            for Field2 in rec[Field].fields_get():
                                if Field2 not in REJECTLIST:
                                    if rec[Field][Field2] not in (False,0,0.0) and type(rec[Field][Field2]) in TYPELIST:
                                        a += str(Typyze('str', rec[Field][Field2])) + '\n'#Field + ' : '  + Field2 + ' : ' +
                                    elif rec[Field]._fields[Field2].type=='many2one':
                                        hu4=0
                                        for Field3 in rec[Field][Field2].fields_get():
                                            if Field3 not in REJECTLIST:
                                                if rec[Field][Field2][Field3] not in (False,0,0.0) and type(rec[Field][Field2][Field3]) in TYPELIST:
                                                    a+= str(Typyze('str', rec[Field][Field2][Field3])) + '\n'#Field + ' : ' +Field2 + ' : ' +Field3+' : '+

                                                hu4 += 1
                                                if hu4 > MAXINTERC:
                                                    break
                                    hu3 += 1
                                    if hu3 > MAXINTERC:
                                        break
        clock.date_time=datetime.datetime.now()+datetime.timedelta(seconds=2)
    else:

        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: (CLOCK_RESUMEN NO LISTO) NO ANALIZADO MODELO : %s' % mod_name)
    return a

def Analize_model3_viejo24_11_25(self, mod_name, dominio):
    a = ''
    clock=self.env['abatar.constantes'].search([('name','=','Resumen_clock')],limit=1)
    if clock.date_time < datetime.datetime.now():
        TYPELIST=(float, int, str, bool, type(fields.datetime.now()),type(fields.datetime.now().date()), type(fields.datetime), type(fields.Binary(attachment=True)), type(fields.Html()))
        MAXINTERC=100
        MAXINTERF=10
        REJECTLIST=['resumen_busqueda', 'create_date',  'write_date', '__last_update','user_id','user_ids','image','image_medium', 'image_small', 'message_ids','message_follower_ids', 'message_partner_ids', 'commercial_partner_id', 'create_uid', 'write_uid' ,'calendario' ,'calendario_id','cotizador' ,'cotizador_id','orden_id','orden_id_x','crm_id','crm_id_x']

        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: %s' % fields.datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
        _logger.error('YOGASTONADM: MODELO : %s' % mod_name)
        mod = self.env[mod_name].search(dominio, limit=1)
        for rec in mod:
            for Field in rec.fields_get():
                if Field not in REJECTLIST:
                    if rec[Field] not in (False,0,0.0) and type(rec[Field]) in TYPELIST:
                        a += str(Typyze('str', rec[Field])) + '\n'#Field + ' : ' +
                    else:
                        #_logger.error('YOGASTONADM: %s' % str(Field+' ; '+str(rec[Field])+' ; '+str(type(rec[Field]))))
                        #_logger.error('YOGASTONADM: %s' % rec[Field].ttype)
                        if rec._fields[Field].type=='one2many':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':

                            hu=0
                            for ei in rec[Field]:
                                hu2 = 0
                                for Field2 in ei.fields_get():
                                    if Field2 not in REJECTLIST:
                                        if ei[Field2] not in (False,0,0.0) and type(ei[Field2]) in TYPELIST:
                                            a += str(Typyze('str', ei[Field2])) + '\n'#Field + ' (' +  str(hu) + '): '  + Field2 + ' : ' +
                                        elif ei._fields[Field2].type=='many2one':
                                            hu22=0
                                            for Field3 in ei[Field2].fields_get():
                                                if Field3 not in REJECTLIST:
                                                    if ei[Field2][Field3] not in (False,0,0.0) and type(ei[Field2][Field3]) in TYPELIST:
                                                        a += str(Typyze('str', ei[Field2][Field3])) + '\n'#Field + '(' + str(hu) + '): ' + Field2 + ' -> ' + Field3 + ' : ' +

                                                    hu22 += 1

                                                    if hu22 > MAXINTERC:
                                                        break
                                        hu2 += 1

                                        if hu2 > MAXINTERC:
                                            break

                                hu += 1

                                if hu > MAXINTERF:
                                    break
                        elif rec._fields[Field].type=='many2one':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                            hu3=0
                            for Field2 in rec[Field].fields_get():
                                if Field2 not in REJECTLIST:
                                    if rec[Field][Field2] not in (False,0,0.0) and type(rec[Field][Field2]) in TYPELIST:
                                        a += str(Typyze('str', rec[Field][Field2])) + '\n'#Field + ' : '  + Field2 + ' : ' +
                                    elif rec[Field]._fields[Field2].type=='many2one':
                                        hu4=0
                                        for Field3 in rec[Field][Field2].fields_get():
                                            if Field3 not in REJECTLIST:
                                                if rec[Field][Field2][Field3] not in (False,0,0.0) and type(rec[Field][Field2][Field3]) in TYPELIST:
                                                    a+= str(Typyze('str', rec[Field][Field2][Field3])) + '\n'#Field + ' : ' +Field2 + ' : ' +Field3+' : '+

                                                hu4 += 1
                                                if hu4 > MAXINTERC:
                                                    break
                                    hu3 += 1
                                    if hu3 > MAXINTERC:
                                        break
        clock.date_time=datetime.datetime.now()+datetime.timedelta(seconds=5)
    else:

        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: (CLOCK_RESUMEN NO LISTO) NO ANALIZADO MODELO : %s' % mod_name)
    return a

def Analize_model3VIEJO_21_9_24(self, mod_name, dominio):
    TYPELIST=(float, int, str, bool, type(fields.datetime.now()),type(fields.datetime.now().date()), type(fields.datetime), type(fields.Binary(attachment=True)), type(fields.Html()))
    MAXINTERC=25
    MAXINTERF=10
    REJECTLIST=['resumen_busqueda', 'create_date',  'write_date', '__last_update','user_id','user_ids','image','image_medium', 'image_small', 'message_ids','message_follower_ids', 'message_partner_ids', 'commercial_partner_id', 'create_uid', 'write_uid' ,'calendario' ,'calendario_id','cotizador' ,'cotizador_id','orden_id','orden_id_x','crm_id','crm_id_x']
    a = ''
    _logger = logging.getLogger(__name__)
    _logger.error('YOGASTONADM: %s' % fields.datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S'))
    _logger.error('YOGASTONADM: MODELO : %s' % mod_name)
    mod = self.env[mod_name].search(dominio, limit=1)
    for rec in mod:
        for Field in rec.fields_get():
            if Field not in REJECTLIST:
                if type(rec[Field]) in TYPELIST:
                    a += Field + ' : ' + str(Typyze('str', rec[Field])) + '\n'
                else:
                    #_logger.error('YOGASTONADM: %s' % str(Field+' ; '+str(rec[Field])+' ; '+str(type(rec[Field]))))
                    #_logger.error('YOGASTONADM: %s' % rec[Field].ttype)
                    if rec._fields[Field].type=='one2many':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':

                        hu=0
                        for ei in rec[Field]:
                            hu2 = 0
                            for Field2 in ei.fields_get():
                                if Field2 not in REJECTLIST:
                                    if type(ei[Field2]) in TYPELIST:
                                        a += Field + ' (' +  str(hu) + '): '  + Field2 + ' : ' + str(Typyze('str', ei[Field2])) + '\n'
                                    elif ei._fields[Field2].type=='many2one':
                                        hu22=0
                                        for Field3 in ei[Field2].fields_get():
                                            if Field3 not in REJECTLIST:
                                                if type(ei[Field2][Field3]) in TYPELIST:
                                                    a += Field + '(' + str(hu) + '): ' + Field2 + ' -> ' + Field3 + ' : ' + str(Typyze('str', ei[Field2][Field3])) + '\n'

                                                hu22 += 1

                                                if hu22 > MAXINTERC:
                                                    break
                                    hu2 += 1

                                    if hu2 > MAXINTERC:
                                        break

                            hu += 1

                            if hu > MAXINTERF:
                                break
                    elif rec._fields[Field].type=='many2one':#if str(type(rec[Field]))[:len('<class \'odoo.api.')] == '<class \'odoo.api.':
                        hu3=0
                        for Field2 in rec[Field].fields_get():
                            if Field2 not in REJECTLIST:
                                if type(rec[Field][Field2]) in TYPELIST:
                                    a += Field + ' : '  + Field2 + ' : ' + str(Typyze('str', rec[Field][Field2])) + '\n'
                                elif rec[Field]._fields[Field2].type=='many2one':
                                    hu4=0
                                    for Field3 in rec[Field][Field2].fields_get():
                                        if Field3 not in REJECTLIST:
                                            if type(rec[Field][Field2][Field3]) in TYPELIST:
                                                a+=Field + ' : ' +Field2 + ' : ' +Field3+' : '+  str(Typyze('str', rec[Field][Field2][Field3])) + '\n'

                                            hu4 += 1
                                            if hu4 > MAXINTERC:
                                                break
                                hu3 += 1
                                if hu3 > MAXINTERC:
                                    break


    return a
