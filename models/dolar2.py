from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
#from abatar.ventana_caja import Analize_model3, Typyze

class AbatarDolar2(models.Model):
    _name = "abatar.dolar2"
    _description = "Abatar Dolar Oficial"
    _rec_name = "pesos"
    _order ="fecha desc"

    fecha = fields.Date(string='Fecha')
    pesos = fields.Float(string='Cotizacion', help="Pesos COMPRA")

    #@api.onchange('pesos')
    #def set_all(self):
    #    for rec in self.env['abatar.dolar2'].search([]):
    #        if rec.pesos > 10000:
    #            rec.write({'pesos':rec.pesos/100})
    #        elif rec.pesos > 1000:
    #            rec.write({'pesos':rec.pesos/10})

class AbatarPedidosreg(models.Model):
    _name = "abatar.pedidosreg"
    _description = "Abatar Pedidos"
    _order ="fecha asc"

    fecha = fields.Date(string='Fecha', default=fields.Date.today())
    tipo = fields.Selection([('flete', 'Flete'),('mudanza', 'Mudanza')], string='Tipo de servicio')


class AbatarDolar3(models.Model):
    _name = "abatar.dolar3"
    _description = "Abatar Modelo Base"
    _rec_name = "NOMBRE_IMPOSIBLE"

    NOMBRE_IMPOSIBLE = fields.Char(string='name')


class FuncionesVisor(models.Model):
    _name = "abatar.funcionesvisor"
    _description = "Abatar Funciones Visor"
    _rec_name = "name"

    name = fields.Char(string='Nombre')

    grupot=fields.Selection([('year', 'Año'),('month', 'Mes'),('day', 'Dia')],string="Tipo grupo1 elemA", default='month')
    grupoN=fields.Selection([('NOMBRE_IMPOSIBLE', 'Nombre'),('name1', 'Nombre1'),('name2', 'Nombre2')],string="Tipo grupo", default='name1')
    valorA=fields.Char(string="Nombre grupo elemA")
    valorB = fields.Char(string="Nombre grupo elemB")
    valorC = fields.Char(string="Nombre grupo elemC")
    valorD = fields.Char(string="Nombre grupo elemD")
    valorE = fields.Char(string="Nombre grupo elemE")
    valorF = fields.Char(string="Nombre grupo elemF")
    valorG = fields.Char(string="Nombre grupo elemG")


    forc_name=fields.Char(string="Elejir Nombre")

    texto = fields.Text(string="Codigo",default='newelem.y_num= valorA+valorB +valorC +valorD +valorE+valorF+valorG ', help='newelem es el elemento de visor que se va a crear, su valorA (y B,C,D,E,F,G) los valores en comun a operar.')

'''
class AbatarResumenbusqueda(models.Model):
    _name = "abatar.resumenbusqueda"
    _description = "Abatar Resumen Busqueda"
    _rec_name = "resumen_busqueda"

    resumen_busqueda = fields.Text(string='Resumen Busqueda', store=True, readonly=True, compute='set_resumen')

    def Typyze(Type, elem, nottime=False):
        if nottime == False:
            if type(elem) == type(fields.datetime.now()):
                elem = elem.date()
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

    def Analize_model3(self, mod_name, dominio):

        a = ''
        mod = self.env[mod_name].search(dominio, limit=1)
        for rec in mod:
            for Field in rec.fields_get():
                a += Field + ': ' + Typyze('str', rec[Field], True) + '\n'
        return a

    @api.onchange(*[attr for attr in dir() if not callable(attr) and not attr.startswith("__")])
    def set_resumen(self):
        for rec in self:
            if type(rec.id) == int:
                rec.resumen_busqueda = Analize_model3(self, rec._name, [('id', '=', rec.id)])

'''
class AbatarVisor(models.Model):
    _name = "abatar.visor"
    _description = "Abatar Modelo Visor"
    _rec_name = "NOMBRE_IMPOSIBLE"

    NOMBRE_IMPOSIBLE = fields.Char(string='name')
    name1 = fields.Char(string='name1')
    name2 = fields.Char(string='name2')
    x_num=fields.Float('x f')
    x_str=fields.Char('x s')
    x_date=fields.Date('x d')
    x_bool=fields.Boolean('x b')
    y_num=fields.Float('y f')
    y_dolar=fields.Float('y f (u$d)', store=True, readonly=True, compute='set_monto_dolar')
    y_func=fields.Float('y F(f)')
    y_func_dolar=fields.Float('y F(f(u$d))')
    y_integral0=fields.Float('y integral0', store=True, readonly=True, compute='set_integral')
    y_integral1=fields.Float('y integral1', store=True, readonly=True, compute='set_integral')
    y_integral2=fields.Float('y integral2', store=True, readonly=True, compute='set_integral')
    y_str=fields.Char('y s')
    y_date=fields.Date('y d')
    y_bool=fields.Boolean('y b')
    dolar_uso = fields.Float(string='Dolar', store=True, readonly=True, compute='set_dolar')
    dolar2_uso = fields.Float(string='Dolar(Of)')#, store=True, readonly=True, compute='set_dolar')

    @api.depends('x_date', 'y_num', 'dolar_uso')
    def set_monto_dolar(self):
        for rec in self:
            if rec.dolar_uso:
                rec.y_dolar = rec.y_num / rec.dolar_uso

    @api.depends('x_date', 'y_num')
    def set_dolar(self):
        for rec in self:
            if rec.x_date:
                dolar_uso = 0
                dolar2_uso = 0
                fecha_orden = str(fields.Date.from_string(rec.x_date).strftime('%d/%m/%y'))
                dia_ejec = int(fecha_orden[:fecha_orden.find('/')])
                rest = fecha_orden[fecha_orden.find('/') + 1:]
                mes_ejec = int(rest[:rest.find('/')])
                rest2 = rest[rest.find('/') + 1:]
                año_ejec = 2000 + int(rest2[:])

                actu = self.env['abatar.dolar'].search([('fecha', '=', fields.Date.from_string(rec.x_date))], limit=1)
                if actu:
                    if actu.pesos:
                        dolar_uso = actu.pesos


                else:
                    for h0 in [0]:
                        day2 = dia_ejec - (h0 + 1) * 5
                        mes2 = mes_ejec
                        año2 = año_ejec
                        day3 = dia_ejec + (h0 + 1) * 5
                        mes3 = mes_ejec
                        año3 = año_ejec
                        if day2 < 1:
                            day2 = 28
                            mes2 -= 1
                        elif day2 > 28:
                            day2 = 1
                            mes2 += 1
                        if mes2 > 12:
                            mes2 = 1
                            año2 += 1
                        elif mes2 < 1:
                            mes2 = 12
                            año2 -= 1

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
                        actu = self.env['abatar.dolar'].search(
                            [('fecha', '>', fields.Date.from_string(str(año2) + '-' + str(mes2) + '-' + str(day2))),
                             ('fecha', '<=', fields.Date.from_string(str(año3) + '-' + str(mes3) + '-' + str(day3)))],
                            limit=1)

                        if actu:
                            if actu.pesos:
                                dolar_uso = actu.pesos
                                break

                    if dolar_uso == 0:
                        actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                        if actu:
                            if actu.pesos:
                                rec.dolar_uso = actu.pesos

                rec.dolar_uso = dolar_uso
                ''' DESACTIVO DOLAR OF
                actu = self.env['abatar.dolar2'].search([('fecha', '=', fields.Date.from_string(rec.x_date))], limit=1)
                if actu:
                    if actu.pesos:
                        dolar2_uso = actu.pesos

                else:
                    for h0 in [0]:
                        day2 = dia_ejec - (h0 + 1) * 5
                        mes2 = mes_ejec
                        año2 = año_ejec
                        day3 = dia_ejec + (h0 + 1) * 5
                        mes3 = mes_ejec
                        año3 = año_ejec
                        if day2 < 1:
                            day2 = 28
                            mes2 -= 1
                        elif day2 > 28:
                            day2 = 1
                            mes2 += 1
                        if mes2 > 12:
                            mes2 = 1
                            año2 += 1
                        elif mes2 < 1:
                            mes2 = 12
                            año2 -= 1

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
                        actu = self.env['abatar.dolar2'].search(
                            [('fecha', '>', fields.Date.from_string(str(año2) + '-' + str(mes2) + '-' + str(day2))),
                             ('fecha', '<=', fields.Date.from_string(str(año3) + '-' + str(mes3) + '-' + str(day3)))],
                            limit=1)

                        if actu:
                            if actu.pesos:
                                dolar2_uso = actu.pesos
                                break

                        if dolar2_uso == 0:
                            actu = self.env['abatar.dolar2'].search([], order='fecha desc', limit=1)
                            if actu:
                                if actu.pesos:
                                    rec.dolar2_uso = actu.pesos
                rec.dolar2_uso = actu.pesos
                '''

    def set_dolarmanual(self, fecha, monto):

        monto_dolar = 0
        fecha_orden = str(fields.Date.from_string(fecha).strftime('%d/%m/%y'))
        dia_ejec = int(fecha_orden[:fecha_orden.find('/')])
        rest = fecha_orden[fecha_orden.find('/') + 1:]
        mes_ejec = int(rest[:rest.find('/')])
        rest2 = rest[rest.find('/') + 1:]
        año_ejec = 2000 + int(rest2[:])

        actu = self.env['abatar.dolar'].search([('fecha', '=', fecha)],
                                               limit=1)
        if actu.pesos:
            monto_dolar = monto / actu.pesos


        else:
            for h0 in [0]:
                day2 = dia_ejec - (h0 + 1) * 5
                mes2 = mes_ejec
                año2 = año_ejec
                day3 = dia_ejec + (h0 + 1) * 5
                mes3 = mes_ejec
                año3 = año_ejec
                if day2 < 1:
                    day2 = 28
                    mes2 -= 1
                elif day2 > 28:
                    day2 = 1
                    mes2 += 1
                if mes2 > 12:
                    mes2 = 1
                    año2 += 1
                elif mes2 < 1:
                    mes2 = 12
                    año2 -= 1

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
                actu = self.env['abatar.dolar'].search(
                    [('fecha', '>', fields.Date.from_string(str(año2) + '-' + str(mes2) + '-' + str(day2))),
                     ('fecha', '<=', fields.Date.from_string(str(año3) + '-' + str(mes3) + '-' + str(day3)))],
                    limit=1)

                if actu.pesos:
                    monto_dolar = monto / actu.pesos

            if monto_dolar == 0:
                actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                if actu.pesos:
                    monto_dolar = monto / actu.pesos

        return monto_dolar

    @api.multi
    def export_data(self, fields_to_export, raw_data=False):
        """ Override Export Function -> Exportar siempre total de filas """

        records = self.env['abatar.visor'].search([])#self.browse(set(get_real_ids(self.ids)))
        return super(AbatarVisor, records).export_data(fields_to_export, raw_data)

    @api.depends('y_num','x_date','NOMBRE_IMPOSIBLE','name1','name2')
    def set_integral(self):
        for rec in self:
            ants0=self.env['abatar.visor'].search([('x_date','<=',rec.x_date), ('name1', '=',rec.NOMBRE_IMPOSIBLE)])
            ants1=self.env['abatar.visor'].search([('x_date','<=',rec.x_date), ('name1', '=',rec.name1)])
            ants2=self.env['abatar.visor'].search([('x_date','<=',rec.x_date), ('name2', '=',rec.name2)])
            integ0=0
            integ1=0
            integ2=0
            for ant in ants0:
                if ant.y_num:
                    integ0+=ant.y_num
            for ant in ants1:
                if ant.y_num:
                    integ1+=ant.y_num
            for ant in ants2:
                if ant.y_num:
                    integ2+=ant.y_num
            rec.y_integral0=integ0
            rec.y_integral1=integ1
            rec.y_integral2=integ2



class AbatarVisor2(models.Model):
    _name = "abatar.visor2"
    _inherit = 'abatar.visor'
    _description = "Abatar Modelo Visor 2"
    _rec_name = "NOMBRE_IMPOSIBLE"

class AbatarVisor3(models.Model):
    _name = "abatar.visor3"
    _inherit = 'abatar.visor'
    _description = "Abatar Modelo Visor 3"
    _rec_name = "NOMBRE_IMPOSIBLE"

class AbatarVisor4(models.Model):
    _name = "abatar.visor4"
    _inherit = 'abatar.visor'
    _description = "Abatar Modelo Visor 4"
    _rec_name = "NOMBRE_IMPOSIBLE"

class SaveVisor(models.Model):
    """Wizard to update a manual goal"""
    _name = 'abatar.savevisor'
    _description = 'Guardados de Visor'

    carpeta2=fields.Char(string='Grupo Macro')
    carpeta=fields.Char(string='Carpeta')
    name=fields.Char(string='Nombre de busqueda')
    name2=fields.Char(string='Nombre 2')
    modelo = fields.Char(string="modelo")
    campo_x = fields.Char(string="campo_x")
    campo_y = fields.Char(string="campo_y")
    dolarizar = fields.Boolean(string="Pasar a Dolar?")
    ids_list = fields.Char(string="ids", help="ej:1,2,3,4,5,6 .Indicar numeros de id separados por comas")
    dominio = fields.Char(string="dominio", help="ej:[('fecha_ejecucion','>=', fields.datetime.now())] Indicar un dominio como se busca en la funcion search")
    orden = fields.Char(string="Orden", help="ej:*fecha desc* (sin asteriscos) para parametro order de funcion search")
    comparacion = fields.Char(string="comparacion", help="ej:['<', 5000] Indicar una lista con 2 elementos: elem logico, y valor de referencia.")
    salida = fields.Char(string="salida", help="ej: vector  . Indicar la forma de salida, puede ser: vector, inversor, suma, promedio, o indicar una funcion existente que trabaje con (self, x, y)", default='vector')
    tipo = fields.Selection([('1', 'Por Defecto'),('str', 'Texto'),('float', 'Num. decimal'),('int', 'Entero'),('list', 'Lista'),('bool', 'Booleano')],string="tipo", help="valores: float/str/int/list/bool Indicar si se desea elejir un Type para el campo_y", default='1')



class AbatarProveedoresVisor(models.Model):
    _name = "abatar.proveedoresvisor"
    _description = "Abatar Proveedores precios Visor"
    _rec_name = "name_gral"

    name_gral=fields.Char('Nombre', store=True, readonly=True, compute='set_namegral')
    fecha=fields.Date('Fecha', default=fields.Date.today)
    proveedor_id = fields.Many2one('abatar.proveedores',string='Proveedores')
    proveedor_producto = fields.Many2one('abatar.productos', string='Productos')
    horas=fields.Float('Horas que incluye')
    kms=fields.Float('Kms que incluye')
    precio=fields.Float('Precio $ (sin IVA)')
    preciousd=fields.Float('Precio u$d (sin IVA)')
    dolaruso=fields.Float('U$d usado')

    @api.onchange('precio', 'fecha','proveedor_id','proveedor_producto','horas','kms')
    def set_namegral(self):
        for rec in self:
            string=''
            if rec.fecha:
                string+=str(fields.Date.from_string(rec.fecha).strftime('%d/%m/%y'))+' '
            if rec.proveedor_id:
                string+=rec.proveedor_id.name+' '
            if rec.proveedor_producto:
                string+='('+rec.proveedor_producto.name+')'
            if rec.preciousd:
                string+=' u$d '+str(rec.preciousd)
            elif rec.precio:
                string+=' $ '+str(rec.precio)
            rec.name_gral=string


    #@api.onchange('precio', 'fecha')
    def set_preciousd(self):
        for rec in self:
            dolaruso=0
            preciousd=0
            if rec.precio:
                if rec.fecha:
                    fecha = str(fields.Date.from_string(rec.fecha).strftime('%d/%m/%y'))
                    precio = rec.precio

                    dia_ejec = int(fecha[:fecha.find('/')])
                    rest = fecha[fecha.find('/') + 1:]
                    mes_ejec = int(rest[:rest.find('/')])
                    rest2 = rest[rest.find('/') + 1:]
                    año_ejec = 2000 + int(rest2[:])

                    actu = self.env['abatar.dolar'].search(
                        [('fecha', '=', fields.Date.from_string(rec.fecha))], limit=1)
                    if actu.pesos:
                        preciousd = precio / actu.pesos
                        dolaruso = actu.pesos


                    else:
                        for h0 in [0,1]:
                            day2 = dia_ejec - (h0 + 1) * 2
                            mes2 = mes_ejec
                            año2 = año_ejec
                            day3 = dia_ejec + (h0 + 1) * 2
                            mes3 = mes_ejec
                            año3 = año_ejec
                            if day2 < 1:
                                day2 = 28
                                mes2 -= 1
                            elif day2 > 28:
                                day2 = 1
                                mes2 += 1
                            if mes2 > 12:
                                mes2 = 1
                                año2 += 1
                            elif mes2 < 1:
                                mes2 = 12
                                año2 -= 1

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
                            actu = self.env['abatar.dolar'].search(
                                [('fecha', '>', fields.Date.from_string(str(año2) + '-' + str(mes2) + '-' + str(day2))),
                                 ('fecha', '<=',
                                  fields.Date.from_string(str(año3) + '-' + str(mes3) + '-' + str(day3)))], limit=1)

                            if actu.pesos:
                                preciousd = precio / actu.pesos
                                dolaruso = actu.pesos

                        if preciousd == 0 and precio:
                            actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                            if actu.pesos:
                                preciousd = precio / actu.pesos

            rec.preciousd=preciousd
            rec.dolaruso=dolaruso


    @api.model
    def create(self, vals):

        fecha0=vals.get('fecha')
        precio = vals.get('precio')

        fecha = str(fields.Date.from_string(fecha0).strftime('%d/%m/%y'))

        dolaruso = 0
        preciousd = 0

        dia_ejec = int(fecha[:fecha.find('/')])
        rest = fecha[fecha.find('/') + 1:]
        mes_ejec = int(rest[:rest.find('/')])
        rest2 = rest[rest.find('/') + 1:]
        año_ejec = 2000 + int(rest2[:])

        actu = self.env['abatar.dolar'].search(
            [('fecha', '=', fecha0)], limit=1)
        if actu.pesos:
            preciousd = precio / actu.pesos
            dolaruso = actu.pesos


        else:
            for h0 in [0, 1]:
                day2 = dia_ejec - (h0 + 1) * 2
                mes2 = mes_ejec
                año2 = año_ejec
                day3 = dia_ejec + (h0 + 1) * 2
                mes3 = mes_ejec
                año3 = año_ejec
                if day2 < 1:
                    day2 = 28
                    mes2 -= 1
                elif day2 > 28:
                    day2 = 1
                    mes2 += 1
                if mes2 > 12:
                    mes2 = 1
                    año2 += 1
                elif mes2 < 1:
                    mes2 = 12
                    año2 -= 1

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
                actu = self.env['abatar.dolar'].search(
                    [('fecha', '>', fields.Date.from_string(str(año2) + '-' + str(mes2) + '-' + str(day2))),
                     ('fecha', '<=',
                      fields.Date.from_string(str(año3) + '-' + str(mes3) + '-' + str(day3)))], limit=1)

                if actu.pesos:
                    preciousd = precio / actu.pesos
                    dolaruso = actu.pesos

            if preciousd == 0 and precio:
                actu = self.env['abatar.dolar'].search([], order='fecha desc', limit=1)
                if actu.pesos:
                    preciousd = precio / actu.pesos
                    dolaruso = actu.pesos

        vals['preciousd']=preciousd
        vals['dolaruso']=dolaruso

        result = super(AbatarProveedoresVisor, self).create(vals)
        return result


class AbatarTrends(models.Model):
    _name = 'abatar.trends'
    _description="Trends de Palabras"
    _rec_name="palabra"

    palabra=fields.Char(string="Palabra")
    busquedas_lines=fields.One2many('abatar.trends.lines','trends_id',string='Lista de Valores')
    ultimo_valor=fields.Float(string="Ultimo valor", store=True, readonly=True, compute="_compute_ultimo_valor")

    @api.depends('busquedas_lines.valor', 'busquedas_lines.fecha')
    def _compute_ultimo_valor(self):
        for record in self:
            # buscamos el registro con fecha más reciente
            if record.busquedas_lines:
                ultimo = record.busquedas_lines.sorted(key=lambda r: r.fecha, reverse=True)[0]
                record.ultimo_valor = ultimo.valor
            else:
                record.ultimo_valor = 0.0


class AbatarTrendsLines(models.Model):
    _name = 'abatar.trends.lines'

    fecha=fields.Date(string='Fecha')
    valor=fields.Float(string='Porcentaje de Búsqueda')
    trends_id=fields.Many2one('abatar.trends',string="trend_id")