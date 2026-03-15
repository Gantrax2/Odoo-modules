from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from datetime import datetime
import logging
import numpy as np
from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON,Analize_DATETF, Analize_DATEF, Analize_DATETL, Analize_DATEL,Analize_DATEBACK,Analize_DATEFORW,Analize_DATETBACK,Analize_DATETFORW,Analize_EMPLF,COMPARESTRFUNC, CALCULA_INDICADOR,execVariable



class AbatarIndicadores(models.Model):
    _name = "abatar.indicadores"
    _description = "Abatar Indicadores"
    _inherit = ['abataradd.resumenbus']
    _rec_name = "name0"
    _order= "capa_orden asc"

    name0 = fields.Char(string="Nombre grupo")
    name = fields.Char(string="Nombre")
    ult_act=fields.Datetime(string="Ultima Actualizacion")
    modelo = fields.Char(string="Modelo", help='ej:abatar.crm  . Nombre del módulo a operar')
    campo_x = fields.Char(string="Campo_y", help='Nombre del campo sobre el que se operará según -salida-. Se observan los nombres en modo debug (solo admnistrador)')
    dominio = fields.Char(string="Dominio", help="ej:[('fecha_ejecucion','>=', fields.datetime.now()-fields.datetime.timedelta(days=7)] Indicar un dominio como se busca en la funcion search. Para fechas u empleados se puede usar: \n 'DATEBACK:N' hoy-N \n 'DATEFORW:N' hoy+N \n 'DATEF:d/m/yyyy' \n 'DATEL:d-m-y/cantDiv' fecha en div actual \n 'EMPLF:NAME'")
    fecha_indicador = fields.Char(string="Campo_X: Variable tipo fecha para promedio_N", help="nombre de la variable de fecha para el promediado")
    salida = fields.Char(string="Salida", help="ej: cuenta  . Indicar la forma de salida, puede ser: cuenta, suma, promedio, promedio_d-m-y/N (N=entero para prom cada N elementos. A lo largo del tiempo), Promedio_d-m-y/N (igual al ant. pero compara contra el mismo período del año que el actual), max, min", default='cuenta')
    multiplicador=fields.Float(string='Multiplicador', help='Indica un valor por el cual multiplicar el resultado de salida.')

    final_tablero=fields.Boolean(string="Es Indicador final para tablero",help="si es un indicador parcial, que es usado por otro indicador, se debe dejar en FALSE para que no aparezca" , default=True)
    formula=fields.Char(sting="Formula",help="Indicar Fórmula en lugar de extraer datos. Se debe indicar entre [] corchetes los nombres de grupo de indicador que se desea usar. \n Ej: ([nombre de grupo a]+[nombre de grupo b]*[nombre de grupo c])/([nombre de grupo d]+[nombre de grupo e])")
    capa_orden=fields.Integer(sting="Orden de Formula",help="para indicadores con formula, se indica el orden de procesamiento>0. El 0 es el primero, luego el 1, y así en orden ascendente. (Permite usar en una formula otros indicadores formulas que deben estar en orden inferior. (Si un indicador formula -A- quiere usar otro -B- tendrá que tener orden A mayor a B)")

    x_f=fields.Float(string="X_float")
    x_i=fields.Integer(string="X_int")
    x_c=fields.Char(string="X_char")
    x_d=fields.Date(string="X_date")
    value_f=fields.Float(string="Valor_float")
    value_i=fields.Integer(string="Valor_int")
    value_c=fields.Char(string="Valor_char")
    active=fields.Boolean(string="Active" , default=True)

    @api.model
    def refresh_indicadores(self):

        dict_indic={}

        for rec in self.env['abatar.indicadores'].search([('formula','in',[False,''])]):

            fields.Glog('GASTON94 AUTOREFRESH REC:%s - %s'%(str(rec.name0),rec.name))
            if rec:

                resultf=CALCULA_INDICADOR(rec)
                rec.x_c= fields.datetime.now().date().strftime('%d/%m/%y')
                rec.x_d= fields.datetime.now().date()
                rec.ult_act= fields.datetime.now()
                rec.value_f = resultf

                if rec.final_tablero:
                    if rec.name0 in dict_indic:
                        if rec.name=='ACTUAL':
                            dict_indic[rec.name0][0]=rec.value_f
                            dict_indic[rec.name0][3]=rec.ult_act
                        elif rec.name=='PROM ESPERADO':
                            dict_indic[rec.name0][1]=rec.value_f
                        elif rec.name=='PROM SEMANAL':
                            dict_indic[rec.name0][2]=rec.value_f
                    else:
                        dict_indic[rec.name0]=[0,0,0,0]
                        if rec.name=='ACTUAL':
                            dict_indic[rec.name0][0]=rec.value_f
                            dict_indic[rec.name0][3]=rec.ult_act
                        elif rec.name=='PROM ESPERADO':
                            dict_indic[rec.name0][1]=rec.value_f
                        elif rec.name=='PROM SEMANAL':
                            dict_indic[rec.name0][2]=rec.value_f
        #prev=self.env['abatar.indicadores'].search([('formula','not in',[False,''])],order='capa_orden asc')
        #fields.Glog('FORMULA RECs FOUND:%s' % str(prev))

        for rec in self.env['abatar.indicadores'].search([('formula','not in',[False,''])],order='capa_orden asc'):

            fields.Glog('GASTON94 AUTOREFRESH FORMULA REC:%s - %s'%(str(rec.name0),rec.name))
            if rec:
                formul=rec.formula
                while formul.find("[")>-1:
                    val=self.env['abatar.indicadores'].search([('name0','=',formul[formul.find("[")+1:formul.find("]")]),('name','=',rec.name)]).value_f
                    formul=formul[:formul.find("[")]+str(val)+formul[formul.find("]")+1:]

                fields.Glog('PREPARANDO VALOR DE resultf:'+formul)
                fields.Glog('formul value:'+str(execVariable(formul)))
                resultf=execVariable(formul)
                fields.Glog('aca el valor de resultf:')
                fields.Glog(str(resultf))
                rec.x_c= fields.datetime.now().date().strftime('%d/%m/%y')
                rec.x_d= fields.datetime.now().date()
                rec.ult_act= fields.datetime.now()
                rec.value_f = float(resultf)
                if rec.final_tablero:
                    if rec.name0 in dict_indic:
                        if rec.name=='ACTUAL':
                            dict_indic[rec.name0][0]=rec.value_f
                            dict_indic[rec.name0][3]=rec.ult_act
                        elif rec.name=='PROM ESPERADO':
                            dict_indic[rec.name0][1]=rec.value_f
                        elif rec.name=='PROM SEMANAL':
                            dict_indic[rec.name0][2]=rec.value_f
                    else:
                        dict_indic[rec.name0]=[0,0,0,0]
                        if rec.name=='ACTUAL':
                            dict_indic[rec.name0][0]=rec.value_f
                            dict_indic[rec.name0][3]=rec.ult_act
                        elif rec.name=='PROM ESPERADO':
                            dict_indic[rec.name0][1]=rec.value_f
                        elif rec.name=='PROM SEMANAL':
                            dict_indic[rec.name0][2]=rec.value_f
        if dict_indic:
            self.env['abatar.tableros'].search([]).unlink()
            for key in dict_indic:
                fields.Glog("pelon dict:")
                fields.Glog(key+':'+str(dict_indic[key][0]))
                self.env['abatar.tableros'].create({

                    'name': key,
                    'ult_act': dict_indic[key][3],
                    'act_value': dict_indic[key][0],
                    'esp_value': dict_indic[key][1],
                    'prom_value': dict_indic[key][2],
                    })


    def state_confirmado(self):

        for rec in self:
            if rec.state=='borrador':
                rec.state = 'confirmado'
        self.message_post(body=_("La orden pasó a estado: Confirmado"))

    def state_borrador(self):
        for rec in self:
            if rec.state=='confirmado':
                rec.state = 'borrador'
        self.message_post(body=_("La orden pasó a estado: Borrador"))
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
        res = super(AbatarIndicadores, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AbatarIndicadores, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.depends('name', 'x_f', 'x_i', 'x_c', 'value_f', 'value_i', 'value_c')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=''
            if rec.name:
                rec.name_gral+=rec.name
            if rec.x_f:
                rec.name_gral+='- x:'+str(rec.x_f)
            if rec.x_i:
                rec.name_gral+='- x:'+str(rec.x_i)
            if rec.x_c:
                rec.name_gral+='- x:'+str(rec.x_c)
            if rec.value_f:
                rec.name_gral+='- y:'+str(rec.value_f)
            if rec.value_i:
                rec.name_gral+='- y:'+str(rec.value_i)
            if rec.value_c:
                rec.name_gral+='- y:'+str(rec.value_c)

    def set_value(self):
        for REC in self:
            res_ud=['A','B','C','D','E','F','FF']
            for UD_T in res_ud:
                if REC.name=='PAGO X UD ('+UD_T+')':
                    suma=0
                    monto=0
                    cant=0
                    for rec in REC.env['abatar.ordenes'].search([('active', 'in', (True,False))]):
                        if rec.orden_lines:
                            for rec1 in rec.orden_lines:
                                if rec1.proveedor_producto.subtipo.name=="Unidad \""+UD_T+"\"":
                                    if rec1.precio_pactado!=False:
                                        cant+=1
                                        suma+=rec1.precio_pactado

                    if suma:
                        if cant:
                            monto=suma/cant

                    REC.value_f=monto
                    REC.x_c=UD_T
            res = ['PAGO X OP', ['Operario', '=', ['abatar.ordenes', 'orden_lines', 'proveedor_producto', 'name']], '']
            if REC.name=='PAGO X OP':
                suma=0
                monto=0
                cant=0
                for rec in REC.env['abatar.ordenes'].search([('active', '=', False)]):
                    if rec.orden_lines:
                        for rec1 in rec.orden_lines:
                            if rec1.proveedor_producto.subtipo.name=="Operario" or rec1.proveedor_producto.subtipo.name=="Supervisor":
                                if rec1.precio_pactado!=False:
                                    cant+=1
                                    suma+=rec1.precio_pactado

                if suma:
                    if cant:
                        monto=suma/cant
                REC.value_f=monto

            res = ['COBRO POR MDZ (H/M3) con m3 de 15 a 120', ['Operario', '=', ['abatar.ordenes', 'orden_lines', 'proveedor_producto', 'name']], '']
            res_m3_0=15
            res_m3_paso=5
            res_m3_pasos=21
            for i in range(res_m3_pasos):
                if REC.name=='COBRO POR MDZ (H/'+str(int(res_m3_0+i*res_m3_paso))+')':

                    suma=0
                    monto=0
                    cant=0
                    m3=0
                    for rec in REC.env['abatar.factura'].search([('crm', '!=', False)]):
                        for aux in range(res_m3_pasos):
                            if rec.crm.mdz_m3_auto>=res_m3_0+aux*res_m3_paso:
                                pass
                            else:
                                m3=res_m3_0+aux*res_m3_paso
                                break

                        if m3!=0 and m3==res_m3_0+res_m3_paso*i:
                            cant+=1
                            suma+=rec.total

                    if suma:
                        if cant:
                            monto=suma/cant

                    REC.value_f=monto
                    REC.x_i=int(res_m3_0+i*res_m3_paso)
                    REC.ult_act=fields.datetime.now()


class AbatarTableros(models.Model):
    _name = "abatar.tableros"
    _description = "Abatar Tableros Indicadores"

    name = fields.Char(string="Nombre")
    ult_act = fields.Datetime(string="Ultima Actualizacion")

    act_value=fields.Float(string="Valor Actual")
    prom_value=fields.Float(string="Valor Promedio")
    esp_value=fields.Float(string="Valor Esperado")
    color=fields.Char(string="Color", store=True, readonly=True, compute="set_color")

    @api.depends('act_value', 'prom_value','esp_value')
    def set_color(self):
        for rec in self:
            if rec.act_value >= rec.prom_value and rec.act_value >= rec.esp_value :
                rec.color='Verde'
            elif rec.act_value < rec.prom_value and rec.act_value < rec.esp_value :
                rec.color='Rojo'
            else:
                rec.color='Amarillo'

