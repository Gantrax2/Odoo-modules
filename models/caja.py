from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime,date
import time
import calendar
import logging

from odoo.addons.om_abatartrucks.Analize import Typyze, Analize_model3, BUSQUEDAON
Pagos_active=True
class AbatarCaja(models.Model):
    _name = "abatar.caja"
    _description = "Abatar Caja"
    _inherit=['abataradd.resumenbus']
    _rec_name = "nombre_fecha"
    _order = 'fecha_de_caja desc'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.linea_movimientos:
                for rec2 in rec.linea_movimientos:
                    rec2.unlink()

        res = super(AbatarCaja, self).unlink()
        return res

    fecha_de_caja = fields.Date(string='Fecha de Caja')
    nombre_fecha = fields.Char(string='Nombre Fecha', compute='_get_day_of_date')

    fecha_ant = fields.Many2one('abatar.caja', default=False,string='Caja Anterior')
    name_ant = fields.Char(string='Día Saldo Ant.', compute='set_name_ant')


    obs=fields.Char(string='obs')
    billetes=fields.One2many('abatar.caja.billetes', 'caja_id', string="Billetes")
    monedas = fields.Float(string='Monedas')

    saldo_ant = fields.Float(string='Saldo Ant.')
    saldo_ant2 = fields.Float(string='Saldo Ant.', store=True, readonly=True, compute='set_saldo_ant')
    saldo_bancos_ant = fields.Float(string='Saldo Bancos Ant.')#, store=True, readonly=True, compute='set_billetes')
    total_ingresos = fields.Float(string='Ingresos Totales efectivo', compute='set_total_movimientos')
    total_ingresos_bruto = fields.Float(string='Ingresos Totales bruto', compute='set_total_movimientos')
    total_ingresos_banco = fields.Float(string='Ingresos Totales banco',store=True, readonly=True,  compute='set_total_movimientos')
    total_movimientos_bruto = fields.Float(string='Salidas Totales bruto', compute='set_total_movimientos')
    total_movimientos_banco = fields.Float(string='Salidas Totales banco',store=True, readonly=True,  compute='set_total_movimientos')
    total_movimientos = fields.Float(string='Salidas Totales efectivo', compute='set_total_movimientos')

    dueños_neto=fields.Float(string="Balance de EHRB (Neto)",store=True, readonly=True,  compute='set_total_movimientos')#
    balance_ant=fields.Float(string="Balance acumulado Anterior")#,store=True, readonly=True,  compute='set_acumulado_ant')#,related='fecha_ant.balance_acum',  readonly=True)# store=True, readonly=True,
    balance_acum=fields.Float(string="Balance Acumulado")#,store=True, readonly=True,  compute='set_acumulado')# store=True, readonly=True,
    balance_neto=fields.Float(string="Balance de caja (Neto)",store=True, readonly=True,  compute='set_total_movimientos')# readonly=True,
    balance=fields.Float(string="Balance de caja", store=True, readonly=True,  compute='set_total_movimientos')
    saldo_bancos = fields.Float(string='Saldo Bancos',store=True, readonly=True, compute='set_total_movimientos')
    saldo = fields.Float(string='Saldo',store=True, readonly=True, compute='set_total_movimientos')
    total_bancos=fields.Float(string="Total Bancos",store=True, readonly=True,  compute='set_total_efectivo')
    total_efectivo=fields.Float(string="Total Efectivo",store=True, readonly=True,  compute='set_total_efectivo')
    total_dolar=fields.Float(string="Total Dolares",store=True, readonly=True,  compute='set_total_efectivo')
    total_pesos=fields.Float(string='Total Pesos', store=True, readonly=True, compute='set_total_pesos' )
    difer = fields.Float(string='DIFERENCIA',store=True, readonly=True, compute='set_total_movimientos')
    difer_bancos = fields.Float(string='DIFERENCIA BANCOS',store=True, readonly=True, compute='set_total_movimientos')

    linea_movimientos = fields.One2many('abatar.movimientos.lines', 'caja_id', string='Linea de Mmovimientos')
    linea_ingresos = fields.One2many('abatar.ingresos.lines', 'caja_id', string='Linea de Adicionales')


    movimientos_resumen = fields.Char(string="Resumen Movimientos para busqueda", store=True, compute='set_movimientos_resumen')
    ingresos_resumen = fields.Char(string="Resumen Ingresos para busqueda", store=True, compute='set_ingresos_resumen')

    @api.onchange('fecha_ant')
    def set_acumulado_ant(self):
        for rec in self:
            if rec.fecha_ant:
                rec.balance_ant=rec.fecha_ant.balance_acum
                #rec.write({'balance_ant':rec.fecha_ant.balance_acum})
            else:
                #rec.write({'balance_ant':0})
                rec.balance_ant=0

    @api.depends('total_efectivo', 'total_bancos')
    def set_total_pesos(self):
        for rec in self:
            if rec.total_efectivo and rec.total_bancos:
                rec.total_pesos=rec.total_efectivo+rec.total_bancos
            else:
                #rec.write({'balance_ant':0})
                rec.total_pesos=0

    @api.onchange('balance_neto', 'balance_ant')
    def set_acumulado(self):
        for rec in self:
            if rec.balance_ant:
                #rec.write({'balance_acum':rec.balance_ant+rec.balance_neto})
                rec.balance_acum=rec.balance_ant+rec.balance_neto
            else:
                #rec.write({'balance_acum':rec.balance_neto})
                rec.balance_acum=rec.balance_neto

    def reset_billetes(self):
        for rec in self:
            rec.billetes=[(5,0,0)]
            billetes1= [(0, 0, {'cant':0,'name': 'Veinte Mil' , 'monto': 20000}),
                             (0, 0, {'cant':0,'name': 'Diez Mil' , 'monto': 10000}),
                             (0, 0, {'cant':0,'name': 'Dos Mil' , 'monto': 2000}),
                             (0, 0, {'cant':0,'name': 'Mil' , 'monto': 1000}),
                             (0, 0, {'cant':0,'name': 'Quinientos' , 'monto': 500}),
                             (0, 0, {'cant':0,'name': 'Doscientos' , 'monto': 200}),
                             (0, 0, {'cant':0,'name': 'Cien' , 'monto': 100}),
                             (0, 0, {'cant':0,'name': 'Cincuenta' , 'monto': 50}),
                             (0, 0, {'cant':0,'name': 'Veinte' , 'monto': 20}),
                             (0, 0, {'cant':0,'name': 'Diez' , 'monto': 10})]
            resul = self.env['abatar.bancos'].search([])
            for res in resul:
                billetes1.append((0, 0, {'bancos':res.id,'cant':1,'name': res.name , 'monto': 0}))

            billetes1.append((0, 0, {'cant': 0,'dolar': True, 'name': 'Cien DOLAR (JyG)', 'monto': 100}))
            rec.billetes=billetes1






    @api.depends('saldo_ant')
    def set_saldo_ant(self):
        for rec in self:
            if rec.saldo_ant:
                rec.saldo_ant2=rec.saldo_ant

    @api.model
    def default_get(self, fields):
        rec = super(AbatarCaja, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    @api.model
    def create(self, vals):
        if vals.get('fecha_de_caja'):
            caja_b=self.env['abatar.caja'].search([('fecha_de_caja', '=', vals.get('fecha_de_caja'))], limit=1)
            if caja_b:
                raise UserWarning('Ya Existe una caja con esa FECHA DE CAJA. Elije otra.')
        res = super(AbatarCaja, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('fecha_de_caja'):
            caja_b=self.env['abatar.caja'].search([('fecha_de_caja', '=', vals.get('fecha_de_caja'))], limit=1)
            if caja_b:
                raise UserWarning('Ya Existe una caja con esa FECHA DE CAJA. Elije otra.')

        if BUSQUEDAON==True:
            try:
                if self.ensure_one():
                    if type(self.id)==int:
                        resum=Analize_model3(self, self._name, [('id', '=', self.id), ('active', 'in', (True, False))])
                        if len(resum)>50:
                            vals['resumen_busqueda']=datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarCaja, self).write(vals)
        return res

    @api.onchange('fecha_ant')
    def set_billetes(self):
        for rec in self:
            if rec.fecha_ant:
                rec.saldo_ant=rec.fecha_ant.total_efectivo
                rec.saldo_bancos_ant=rec.fecha_ant.total_bancos


    def set_ant_billetes(self):
        for rec in self:
            if rec.fecha_ant:
                rec.write({'billetes':[(6,0,[])]})
                if rec.fecha_ant.billetes:
                    for rac in rec.fecha_ant.billetes:
                        rec.billetes=[(0,0,{'cant':rac.cant,'name':rac.name , 'monto': rac.monto, 'dolar': rac.dolar, 'bancos': rac.bancos})]
                if rec.fecha_ant.monedas:
                    rec.monedas=rec.fecha_ant.monedas
                else:
                    rec.monedas=0


    @api.depends('billetes', 'monedas')
    def set_total_efectivo(self):
        for rec in self:
            total=0
            total_d=0
            total_bancos=0
            if rec.billetes:
                for prev in rec.billetes:
                    if prev.dolar:
                        if prev.total:
                            total_d+=prev.total
                    elif prev.bancos:
                        if prev.total:
                            total_bancos+=prev.total
                    else:
                        if prev.total:
                            total+=prev.total
                if rec.monedas:
                    total+=rec.monedas
            rec.total_efectivo=total
            rec.total_dolar=total_d
            rec.total_bancos=total_bancos



    @api.depends('linea_ingresos')
    def set_ingresos_resumen(self):
        for r in self:
            r.ingresos_resumen = ' '
            if r.linea_ingresos:
                for ai in r.linea_ingresos:
                    if ai.id:
                        r.ingresos_resumen+='linea '+str(ai.id)+': '+ai.texto+'- '
                    if ai.texto:
                        r.ingresos_resumen+=': '+ai.texto

    @api.depends('linea_movimientos')
    def set_movimientos_resumen(self):
        for r in self:
            r.movimientos_resumen = ' '
            if r.linea_movimientos:
                for ai in r.linea_movimientos:
                    r.movimientos_resumen+='linea '+str(ai.id)+': '
                    if ai.deuda_id.name_gral:
                        r.movimientos_resumen += str(ai.deuda_id.name_gral) + ' - '
                    if ai.materiales_id.name_gral:
                        r.movimientos_resumen += ai.materiales_id.name_gral + ' - '
                    if ai.pagos_id.name_gral:
                        r.movimientos_resumen += ai.pagos_id.name_gral+ ' - '
                    if ai.empleados_id.name:
                        r.movimientos_resumen += str(ai.empleados_id.name) + ' - '
                        if ai.se_pago2:
                            prev= self.env['abatar.pagos.empleados'].search([('id', '=', ai.se_pago2)])
                            r.movimientos_resumen += str(prev.fecha_op) + ', $'+str(prev.monto)+' - '
                    if ai.mensuales_id.name:
                        r.movimientos_resumen += str(ai.mensuales_id.name) + ' - '
                        if ai.se_pago2:
                            prev= self.env['abatar.pagos.mensuales'].search([('id', '=', ai.se_pago2)])
                            r.movimientos_resumen += str(prev.fecha_op) + ', $'+str(prev.monto)+' - '
                    if ai.adjunto:
                        r.movimientos_resumen += str(ai.adjunto)

    @api.depends('linea_movimientos.monto','obs','linea_ingresos.monto', 'linea_movimientos.tipo', 'linea_movimientos.retenciones','total_efectivo', 'total_ingresos', 'saldo_ant', 'saldo_bancos_ant', 'fecha_ant', 'billetes')
    def set_total_movimientos(self):
        for dec in self:
            dec.total_ingresos_bruto = 0
            dec.total_ingresos_banco = 0
            dec.total_ingresos = 0
            dec.total_movimientos_bruto = 0
            dec.total_movimientos_banco = 0
            dec.total_movimientos = 0
            Ingresos_extraer=0
            balance=0
            balance_neto=0
            dueños_neto=0
            for rec in dec.linea_ingresos:
                if rec.monto_salida and rec.monto_entrada:
                    if rec.tipo_salida == 'banco' and rec.tipo_entrada == 'banco':
                        pass
                    elif rec.tipo_salida == 'efectivo' and rec.tipo_entrada == 'efectivo':
                        pass
                    else:

                        if rec.monto_salida:
                            dec.total_movimientos_bruto += rec.monto_salida
                            balance -= rec.monto_salida
                            balance_neto -= rec.monto_salida

                            if rec.tipo_salida == 'banco':
                                dec.total_movimientos_banco += rec.monto_salida

                            elif rec.tipo_salida == 'efectivo':
                                dec.total_movimientos += rec.monto_salida

                        if rec.monto_entrada:
                            dec.total_ingresos_bruto += rec.monto_entrada
                            balance += rec.monto_entrada
                            balance_neto += rec.monto_entrada

                            if rec.tipo_entrada == 'banco':
                                dec.total_ingresos_banco += rec.monto_entrada
                            elif rec.tipo_entrada == 'efectivo':
                                dec.total_ingresos += rec.monto_entrada


            for rec in dec.linea_movimientos:
                if rec.pago_electronico:
                    if rec.tipo_name=='Clientes':
                        if rec.monto>0:
                            dec.total_ingresos_bruto += rec.monto+rec.retenciones
                            dec.total_ingresos_banco += rec.monto+rec.retenciones
                            dec.total_movimientos_banco += rec.retenciones

                        elif rec.monto<0:
                            dec.total_movimientos_bruto += -rec.monto
                            dec.total_movimientos_banco += -rec.monto
                        balance+=rec.monto
                        balance_neto+=rec.monto
                    else:
                        if rec.monto>0:
                            dec.total_movimientos_bruto += rec.monto
                            dec.total_movimientos_banco += rec.monto


                        elif rec.monto<0:
                            dec.total_ingresos_bruto += -rec.monto
                            dec.total_ingresos_banco += -rec.monto

                        balance-=rec.monto
                        if rec.empleados_id:
                            if rec.empleados_id.dueño:
                                dueños_neto-=rec.monto
                            else:
                                balance_neto -= rec.monto
                        elif rec.mensuales_id:
                            if rec.mensuales_id.empleados_id:
                                if rec.mensuales_id.empleados_id.dueño:
                                    dueños_neto-=rec.monto
                                else:
                                    balance_neto -= rec.monto
                            else:
                                balance_neto -= rec.monto
                        else:
                            balance_neto -= rec.monto
                else:
                    if rec.tipo_name=='Clientes':
                        if rec.monto>0:
                            dec.total_ingresos_bruto += rec.monto+rec.retenciones
                            dec.total_ingresos += rec.monto+rec.retenciones
                            dec.total_movimientos_bruto += rec.retenciones
                            dec.total_movimientos += rec.retenciones
                        elif rec.monto<0:
                            dec.total_movimientos_bruto += -rec.monto
                            dec.total_movimientos += -rec.monto
                        balance+=rec.monto
                        balance_neto += rec.monto
                    else:
                        if rec.monto>=0:
                            dec.total_movimientos_bruto += rec.monto
                            dec.total_movimientos += rec.monto

                        elif rec.monto<0:
                            dec.total_ingresos_bruto += -rec.monto
                            dec.total_ingresos += -rec.monto
                        balance-=rec.monto
                        if rec.empleados_id:
                            if rec.empleados_id.dueño:
                                dueños_neto-=rec.monto
                            else:
                                balance_neto -= rec.monto
                        elif rec.mensuales_id:
                            if rec.mensuales_id.empleados_id:
                                if rec.mensuales_id.empleados_id.dueño:
                                    dueños_neto-=rec.monto
                                else:
                                    balance_neto -= rec.monto
                            else:
                                balance_neto -= rec.monto
                        else:
                            balance_neto -= rec.monto
            if dec.saldo_ant:
                dec.saldo = dec.saldo_ant + dec.total_ingresos - dec.total_movimientos
            else:
                dec.saldo = dec.total_ingresos - dec.total_movimientos
            dec.difer=dec.total_efectivo - dec.saldo
            if dec.saldo_bancos_ant:
                dec.saldo_bancos=dec.saldo_bancos_ant+dec.total_ingresos_banco-dec.total_movimientos_banco
            else:
                dec.saldo_bancos=dec.total_ingresos_banco-dec.total_movimientos_banco

            dec.balance=balance
            dec.balance_neto=balance_neto
            dec.dueños_neto=dueños_neto

            if dec.fecha_de_caja:
                if dec.fecha_de_caja <= date(2024, 8, 19):
                    dec.difer_bancos=0
                else:
                    dec.difer_bancos=dec.total_bancos - dec.saldo_bancos



    @api.depends('fecha_de_caja')
    def _get_day_of_date(self):
        for r in self:
            if r.fecha_de_caja != False:

                selected = fields.Datetime.from_string(r.fecha_de_caja)
                texto = calendar.day_name[selected.weekday()]
                r.nombre_fecha = ('%s %s' % (str(texto[0].upper()+texto[1:]), fields.Date.from_string(r.fecha_de_caja).strftime('%d/%m/%Y')))

    @api.depends('fecha_ant')
    def set_name_ant(self):
        for r in self:
            if r.fecha_ant != False:

                selected = fields.Date.from_string(r.fecha_ant.fecha_de_caja)
                if selected:
                    texto = calendar.day_name[selected.weekday()]
                    r.name_ant = ('%s %s' % (texto, fields.Date.from_string(r.fecha_ant.fecha_de_caja).strftime('%d/%m/%Y')))
                

class AbatarMovimientosLines(models.Model):
    _name = "abatar.movimientos.lines"
    _description = "Abatar movimientos lines"
    _rec_name = "texto"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.deuda_id:
                revisad = self.env['abatar.deudas'].search(
                    [('id', '=', rec.deuda_id.id),('active', '=', False)])
                pagado=rec.monto
                adjunto=rec.adjunto
                nuevo_pagado=revisad.pago-pagado
                viejo_adjunto= revisad.adjunto.search([('adjunto', '=', adjunto)])
                if viejo_adjunto:
                    if revisad.adjunto.search([('id', '=',viejo_adjunto.id)]):
                        revisad.write({'adjunto': [(1, viejo_adjunto.id, {'deudas_id':False})]})
                        revisad.write({'adjunto': [(2, viejo_adjunto.id)]})
                revisad.write({'pago':nuevo_pagado,'caja':False,'active':True})
            if rec.pagos_id:
                revisad = self.env['abatar.pagos'].search(
                    [('id', '=', rec.pagos_id.id),('active', '=', Pagos_active)])
                pagado=rec.monto
                if rec.retenciones:
                    retenido=rec.retenciones
                else:
                    retenido = 0
                adjunto=rec.adjunto
                nuevo_pagado=revisad.pago-pagado
                nuevo_retenido=revisad.retenciones-retenido
                viejo_adjunto= revisad.adjunto.search([('adjunto', '=', adjunto)])
                if viejo_adjunto:

                    if revisad.adjunto.search([('id', '=',viejo_adjunto.id)]):
                        revisad.write({'adjunto': [(1, viejo_adjunto.id, {'pagos_id':False})]})
                        revisad.write({'adjunto': [(2, viejo_adjunto.id)]})
                revisad.write({'pago':nuevo_pagado,'retenciones':nuevo_retenido,'caja':False,'active':True})
            if rec.materiales_id:
                revisad = self.env['abatar.materiales'].search(
                    [('id', '=', rec.materiales_id.id),('active', '=', False)])
                pagado=rec.monto
                adjunto=rec.adjunto
                nuevo_pagado=revisad.pago-pagado
                viejo_adjunto= revisad.adjunto.search([('adjunto', '=', adjunto)])
                if viejo_adjunto:

                    if revisad.adjunto.search([('id', '=',viejo_adjunto.id)]):
                        revisad.write({'adjunto': [(1, viejo_adjunto.id, {'materiales_id':False})]})
                        revisad.write({'adjunto': [(2, viejo_adjunto.id)]})
                revisad.write({'pago':nuevo_pagado,'caja':False,'active':True})
            if rec.mensuales_id:
                if rec.se_pago2:
                    revisad2 = self.env['abatar.mensuales'].search(
                        [('id', '=', rec.mensuales_id.id), ('active', 'in', (True, False))])

                    if revisad2.pagos.search([('id', '=',rec.se_pago2)]):
                        revisad2.write({'pagos':[(1, rec.se_pago2, {'caja':False})]})
                        revisad2.write({'pagos':[(2, rec.se_pago2)]})
                if rec.adjunto:
                    revisad2 = self.env['abatar.mensuales'].search(
                        [('id', '=', rec.mensuales_id.id), ('active', 'in', (True, False))])
                    viejo_adjunto=revisad2.adjunto.search([('adjunto', '=', rec.adjunto)])
                    if viejo_adjunto:
                        revisad2.write({'adjunto':[(1, viejo_adjunto.id, {'mensuales_id':False})]})
                        revisad2.write({'adjunto':[(2, viejo_adjunto.id)]})
            if rec.empleados_id:
                if rec.se_pago2:
                    revisad2 = self.env['abatar.empleados'].search(
                        [('id', '=', rec.empleados_id.id)])

                    if revisad2.pagos.search([('id', '=',rec.se_pago2)]):
                        revisad2.write({'pagos':[(1, rec.se_pago2, {'caja':False})]})
                        revisad2.write({'pagos':[(2, rec.se_pago2)]})
                if rec.adjunto:
                    revisad2 = self.env['abatar.empleados'].search(
                        [('id', '=', rec.empleados_id.id)])
                    viejo_adjunto=revisad2.adjunto.search([('adjunto', '=', rec.adjunto)], limit=1)

                    if viejo_adjunto:
                        revisad2.write({'adjunto':[(1, viejo_adjunto.id, {'empleados_id':False})]})
                        revisad2.write({'adjunto':[(2, viejo_adjunto.id)]})

            #else:
            #    if rec.texto.find('- Gasto por OT')>-1:
            #        Name_ot=rec.texto[rec.texto.find(' - Gasto por OT')+len(' - Gasto por '):]
            #        ord=self.env['abatar.ordenes'].search([('name_seq', '=', Name_ot)])
            #        for line in ord.registro_gastos:
            #            if line.desc==rec.texto[:rec.texto.find(' - Gasto por OT')]:
            #                line.unlink()
            #                break
            #    elif rec.texto.find('Adelanto cobrado en fecha por Pedido ')>-1:
            #        Name_crm=rec.texto[rec.texto.find('Adelanto cobrado en fecha por Pedido ')+len('Adelanto cobrado en fecha por Pedido '):]
            #        crm=self.env['abatar.ordenes'].search([('pedide', '=', Name_crm)])
            #        for line in crm.registro_pagos:
            #            if line.monto==rec.monto:
            #                line.unlink()
            #                break

        res = super(AbatarMovimientosLines, rec).unlink()
        return res



    name_gral=fields.Char(string="Name rec", compute='set_name_gral')
    tipo = fields.Many2one('abatar.caja.tipo', string='Tipo de Sujeto')
    tipo_name= fields.Char(string='Tipo de Sujeto', related='tipo.name')

    deuda_id=fields.Many2one('abatar.deudas', string="Deuda asociada")
    empleados_id=fields.Many2one('abatar.empleados', string="Empleado asociado")
    mensuales_id=fields.Many2one('abatar.mensuales', string="Mensual asociado")
    materiales_id=fields.Many2one('abatar.materiales',  string="Ticket de Materiales asociado")
    pagos_id=fields.Many2one('abatar.pagos',  string="Pago asociado")

    proveedor_id=fields.Many2one('abatar.proveedores',string='Proveedor de deuda', related='deuda_id.proveedor')
    monto_contable=fields.Float('Monto contable', store=True, readonly=True, compute='set_monto_contable')

    se_pago2=fields.Integer(string="pago_id")

    texto = fields.Text(string='Descripción')
    retenciones = fields.Float(string='Retenciones')
    monto = fields.Float(string='Monto')
    retenciones_r = fields.Float(string='Retenciones (r)', store=True, readonly=True, compute='set_subt')
    monto_r = fields.Float(string='Monto(r)', store=True, readonly=True, compute='set_subt')
    text_signo = fields.Char(string='', store=True, readonly=True, compute='set_subt')
    caja_id = fields.Many2one('abatar.caja', string='caja ID', readonly=True)
    adjunto= fields.Binary(string='Adjunto')
    pago_electronico= fields.Boolean(string='X Internet?',default=False, help="Marcar si el Pago fue realizado de forma electrónica, sin usar dinero de la caja.")

    @api.depends('monto','deuda_id','empleados_id','mensuales_id','materiales_id','pagos_id')
    def set_monto_contable(self):
        for rec in self:
            if rec.monto:
                if rec.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                    if rec.retenciones:
                        rec.monto_contable=rec.monto-rec.retenciones
                    else:
                        rec.monto_contable=rec.monto
                else:
                    rec.monto_contable=-rec.monto

    @api.depends('monto')
    def set_subt(self):
        for rec in self:
            rec.text_signo=''
            rec.retenciones_r=rec.retenciones
            rec.monto_r=rec.monto
            if rec.monto:
                if rec.tipo.id==self.env['abatar.caja.tipo'].search([('name', '=', 'Clientes')]).id:
                    rec.text_signo='-'
                    rec.retenciones_r=-rec.retenciones
                    rec.monto_r=-rec.monto

    @api.depends('deuda_id', 'empleados_id', 'mensuales_id',
                 'materiales_id', 'pagos_id', 'texto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=''
            if rec.deuda_id.name_gral:
                rec.name_gral+=rec.deuda_id.name_gral+' - '
            elif rec.empleados_id.id:
                rec.name_gral+='Emp.'+str(rec.empleados_id.id)+' - '
            elif rec.mensuales_id:
                if rec.mensuales_id.name_gral:
                    rec.name_gral+=rec.mensuales_id.name_gral+' - '

                elif rec.mensuales_id.id:
                    rec.name_gral+='Mens.'+str(rec.mensuales_id.id)+' - '
            elif rec.materiales_id.name_gral:
                rec.name_gral+=rec.materiales_id.name_gral+' - '
            elif rec.pagos_id.name_gral:
                rec.name_gral+=rec.pagos_id.name_gral+' - '
            if rec.texto:
                rec.name_gral += rec.texto

    @api.multi
    def write(self, vals):
        vals2={}
        change=False
        if vals.get('deuda_id'):change=True
        if vals.get('pagos_id'):change=True
        if vals.get('materiales_id'):change=True
        if vals.get('empleados_id'):change=True
        if vals.get('mensuales_id'):change=True
        if change==True:
            if self.deuda_id:

                if self.env['abatar.deudas'].search([('id', '=', self.deuda_id.id), ('active', '=', False)]):
                    result = self.env['abatar.deudas'].search(
                        [('id', '=', self.deuda_id.id), ('active', '=', False)])
                else:
                    result = self.env['abatar.deudas'].search(
                        [('id', '=', self.deuda_id.id)])

                string = ''
                if self.deuda_id.desc:
                    string=self.deuda_id.desc
                if self.texto:
                    string = ' borrado de info caja'+str(self.caja_id.id)

                tipo =self.tipo
                if vals.get('tipo'):
                    tipo = vals.get('tipo')

                id_safe = ['3', result.proveedor.id, vals.get('monto'), string, tipo,
                           self.caja_id.id]
                retenc=0
                if vals.get('retenciones'):
                    retenc=vals.get('retenciones')
                elif self.retenciones:
                    retenc=self.retenciones

                result.write({
                    'fecha_pago': False,
                    'pago': self.deuda_id.pago - id_safe[2],
                    'desc': id_safe[3],
                    'caja': False,
                    'active': True
                })

                id_viejo_adjunto = -1
                if self.adjunto:
                    for prev in result.adjunto:
                        if prev.adjunto == self.adjunto:
                            id_viejo_adjunto = prev.id

                vals3 = {
                    'adjunto': [(1, id_viejo_adjunto, {'deuda_id': False})]
                }
                if id_viejo_adjunto == -1:
                    pass
                else:
                    result.write(vals3)
                    result.write({'adjunto': [(2, id_viejo_adjunto)]})
            if self.pagos_id:

                if self.env['abatar.pagos'].search([('id', '=',  self.pagos_id.id), ('active', '=',  False)]):
                    result=self.env['abatar.pagos'].search([('id', '=',  self.pagos_id.id), ('active', '=',  False)])
                else:
                    result = self.env['abatar.pagos'].search(
                        [('id', '=', self.pagos_id.id)])

                string=''
                if self.texto:
                    string=self.texto

                id_safe = ['1', self.pagos_id.clientes_id.id, self.monto, string, self.caja_id.id]
                retenc=0
                if self.retenciones:
                    retenc=self.retenciones
                result.write({
                            'fecha_pago': False,
                            'pago': result.pago - id_safe[2],
                            'retenciones': result.retenciones - retenc,
                            'desc': ' borrado de info caja' + str(id_safe[4]) ,
                            'caja': False,
                            'active' : True
                              })

                id_viejo_adjunto = -1
                if self.adjunto:
                    for prev in result.adjunto:
                        if prev.adjunto==self.adjunto:
                            id_viejo_adjunto=prev.id

                vals3 = {
                    'adjunto': [(1, id_viejo_adjunto, {'pagos_id': False})]
                }
                if id_viejo_adjunto== -1:
                    pass
                else:
                    result.write(vals3)
                    result.write({'adjunto':[(2,id_viejo_adjunto)]})
            if self.materiales_id:

                if self.env['abatar.materiales'].search([('id', '=',  self.materiales_id.id), ('active', '=',  False)]):
                    result=self.env['abatar.materiales'].search([('id', '=',  self.materiales_id.id), ('active', '=',  False)])
                else:
                    result = self.env['abatar.materiales'].search(
                        [('id', '=', self.materiales_id.id)])

                string=''
                if self.texto:
                    string=self.texto
                id_safe = ['2', self.materiales_id.id, self.materiales_id.proveedor_id.id,self.monto, string, self.caja_id.id]

                result.write({
                            'fecha_pago': False,
                            'pago': self.materiales_id.pago-id_safe[3],
                            'desc':  self.materiales_id.desc + ' borrado de info caja'+ str(id_safe[5]) ,
                            'caja': False,
                            'active' : True
                              })
                id_viejo_adjunto=-1
                if self.adjunto:
                    for prev in result.adjunto:
                        if prev.adjunto==self.adjunto:
                            id_viejo_adjunto=prev.id

                vals3 = {
                    'adjunto': [(1, id_viejo_adjunto, {'materiales_id': False})]
                }
                if id_viejo_adjunto== -1:
                    pass
                else:
                    result.write(vals3)
                    result.write({'adjunto':[(2,id_viejo_adjunto)]})
            if self.empleados_id:
                if self.se_pago2:
                    result = self.env['abatar.empleados'].search([('id', '=', self.empleados_id.id)])
                    vals3 = {'caja': False, 'mensuales_id': False}
                    result.write({'pagos': [(1, self.se_pago2, vals3)]})
                    result.write({'pagos': [(2, self.se_pago2)]})
                if self.adjunto:
                    result = self.env['abatar.empleados'].search([('id', '=', self.empleados_id.id)])
                    for prev in result.adjunto:
                        if prev.adjunto==self.adjunto:
                            result.write({'adjunto': [(1, prev.id, {'empleados_id': False})]})
                            result.write({'adjunto': [(2, prev.id)]})
                vals2 = {'se_pago2': False}
            if self.mensuales_id:
                if self.se_pago2:
                    result=self.env['abatar.mensuales'].search([('id', '=', self.mensuales_id.id), ('active', 'in', (True, False))])
                    vals3={'caja':False,'mensuales_id':False}
                    result.write({'pagos': [(1, self.se_pago2, vals3)]})
                    result.write({'pagos': [(2, self.se_pago2)]})
                    vals2 = {'se_pago2': False}
                if self.adjunto:
                    result=self.env['abatar.mensuales'].search([('id', '=', self.mensuales_id.id), ('active', 'in', (True, False))])
                    for prev in result.adjunto:
                        if prev.adjunto==self.adjunto:
                            result.write({'adjunto': [(1, prev.id, {'mensuales_id': False})]})
                            result.write({'adjunto': [(2, prev.id)]})

        else:
            if vals.get('monto'):
                if self.deuda_id:
                    if self.env['abatar.deudas'].search([('id', '=', self.deuda_id.id), ('active', '=', False)]):
                        result = self.env['abatar.deudas'].search(
                            [('id', '=', self.deuda_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.deudas'].search(
                            [('id', '=', self.deuda_id.id)])

                    monto_ant=result.pago
                    monto_nuevo=vals.get('monto')
                    monto_difer=monto_nuevo-monto_ant
                    result.write({'pago': self.deuda_id.pago + monto_difer})

                if self.pagos_id:
                    if self.env['abatar.pagos'].search([('id', '=', self.pagos_id.id), ('active', '=', False)]):
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id)])

                    monto_ant=result.pago
                    monto_nuevo=vals.get('monto')
                    monto_difer=monto_nuevo-monto_ant
                    result.write({'pago': self.pagos_id.pago + monto_difer})

                if self.materiales_id:
                    if self.env['abatar.materiales'].search([('id', '=', self.materiales_id.id), ('active', '=', False)]):
                        result = self.env['abatar.materiales'].search(
                            [('id', '=', self.materiales_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.materiales'].search(
                            [('id', '=', self.materiales_id.id)])

                    monto_ant=result.pago
                    monto_nuevo=vals.get('monto')
                    monto_difer=monto_nuevo-monto_ant
                    result.write({'pago': self.materiales_id.pago + monto_difer})

                if self.empleados_id:
                    if self.se_pago2:
                        result = self.env['abatar.empleados'].search([('id', '=', self.empleados_id.id)])

                        monto_nuevo = vals.get('monto')
                        vals3 = {'monto': monto_nuevo}
                        result.write({'pagos': [(1, self.se_pago2, vals3)]})
                    else:
                        result = self.env['abatar.empleados'].search([('id', '=', self.empleados_id.id)])
                        string=''
                        if self.texto:
                            string+=self.texto
                        vals1 = {
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'monto': vals.get('monto'),
                            'mensuales_id': self.empleados_id.id,
                            'desc': 'pago por caja. ' + string,
                            'caja': self.caja_id.id
                        }
                        result.write({'pagos': [(0, 0, vals1)]})
                if self.mensuales_id:
                    result = self.env['abatar.mensuales'].search([('id', '=', self.mensuales_id.id), ('active', 'in', (True, False))])
                    if self.se_pago2:
                        monto_nuevo = vals.get('monto')
                        vals3 = {'monto': monto_nuevo}
                        result.write({'pagos': [(1, self.se_pago2, vals3)]})
                    else:
                        string=''
                        if self.texto:
                            string+=self.texto
                        vals1 = {
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'monto': vals.get('monto'),
                            'mensuales_id': self.mensuales_id.id,
                            'desc': 'pago por caja. ' + string,
                            'caja': self.caja_id.id
                        }
                        result.write({'pagos': [(0, 0, vals1)]})

            if vals.get('adjunto'):
                if self.deuda_id:
                    if self.env['abatar.deudas'].search([('id', '=', self.deuda_id.id), ('active', '=', False)]):
                        result = self.env['abatar.deudas'].search(
                            [('id', '=', self.deuda_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.deudas'].search(
                            [('id', '=', self.deuda_id.id)])

                    id_viejo_adjunto = -1
                    if self.adjunto:
                        for prev in result.adjunto:
                            if prev.adjunto == self.adjunto:
                                id_viejo_adjunto = prev.id

                        vals3 = {
                            'adjunto': [(1, id_viejo_adjunto, {'deudas_id': False})]
                        }
                        if id_viejo_adjunto == -1:
                            pass
                        else:
                            result.write(vals3)
                            result.write({'adjunto': [(2, id_viejo_adjunto)]})

                    nuevo_adjunto = vals.get('adjunto')

                    vals3 = {
                        'adjunto': [(0, 0, {
                            'adjunto': nuevo_adjunto,
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'desc': 'carga por caja. ' + str(self.caja_id.id),
                            'deudas_id': result.id
                        })]}
                    result.write(vals3)
                if self.pagos_id:
                    if self.env['abatar.pagos'].search([('id', '=', self.pagos_id.id), ('active', '=', False)]):
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id)])

                    id_viejo_adjunto = -1
                    if self.adjunto:
                        for prev in result.adjunto:
                            if prev.adjunto == self.adjunto:
                                id_viejo_adjunto = prev.id

                                vals3 = {
                                    'adjunto': [(1, id_viejo_adjunto, {'pagos_id': False})]
                                }

                                result.write(vals3)
                                result.write({'adjunto': [(2, id_viejo_adjunto)]})

                    nuevo_adjunto = vals.get('adjunto')

                    vals3 = {
                        'adjunto': [(0, 0, {
                            'adjunto': nuevo_adjunto,
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'desc': 'carga por caja. ' + str(self.caja_id.id),
                            'pagos_id': result.id
                        })]}
                    result.write(vals3)
                if self.materiales_id:
                    if self.env['abatar.materiales'].search([('id', '=', self.materiales_id.id), ('active', '=', False)]):
                        result = self.env['abatar.materiales'].search(
                            [('id', '=', self.materiales_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.materiales'].search(
                            [('id', '=', self.materiales_id.id)])

                    id_viejo_adjunto = -1
                    if self.adjunto:
                        for prev in result.adjunto:
                            if prev.adjunto == self.adjunto:
                                id_viejo_adjunto = prev.id

                                vals3 = {
                                    'adjunto': [(1, id_viejo_adjunto, {'materiales_id': False})]
                                }

                                result.write(vals3)
                                result.write({'adjunto': [(2, id_viejo_adjunto)]})

                    nuevo_adjunto = vals.get('adjunto')

                    vals3 = {
                        'adjunto': [(0, 0, {
                            'adjunto': nuevo_adjunto,
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'desc': 'carga por caja. ' + str(self.caja_id.id),
                            'materiales_id': result.id
                        })]}
                    result.write(vals3)
                if self.mensuales_id:
                    result = self.env['abatar.mensuales'].search([('id', '=', self.mensuales_id.id), ('active', 'in', (True, False))])
                    if self.adjunto:
                        for prev in result.adjunto:
                            if prev.adjunto == self.adjunto:
                                result.write({'adjunto': [(1, prev.id, {'mensuales_id': False})]})
                                result.write({'adjunto': [(2, prev.id)]})
                    nuevo_adjunto = vals.get('adjunto')
                    vals3 = {
                        'adjunto': [(0, 0, {
                            'adjunto': vals.get('adjunto'),
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'desc': 'carga por caja. ' + str(self.caja_id.id),
                            'mensuales_id': self.mensuales_id.id
                        })]}
                    result.write(vals3)
                if self.empleados_id:
                    result = self.env['abatar.empleados'].search([('id', '=', self.empleados_id.id)])
                    if self.adjunto:
                        for prev in result.adjunto:
                            if prev.adjunto == self.adjunto:
                                result.write({'adjunto': [(1, prev.id, {'empleados_id': False})]})
                                result.write({'adjunto': [(2, prev.id)]})

                    nuevo_adjunto = vals.get('adjunto')
                    vals3 = {
                        'adjunto': [(0, 0, {
                            'adjunto': nuevo_adjunto,
                            'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                            'desc': 'carga por caja. ' + str(self.caja_id.id),
                            'empleados_id': self.empleados_id.id
                        })]}
                    result.write(vals3)
            if vals.get('retenciones'):
                if self.pagos_id:
                    if self.env['abatar.pagos'].search([('id', '=', self.pagos_id.id), ('active', '=', False)]):
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id), ('active', '=', False)])
                    else:
                        result = self.env['abatar.pagos'].search(
                            [('id', '=', self.pagos_id.id)])
                    monto_ant=self.retenciones
                    monto_nuevo=vals.get('retenciones')
                    monto_difer=monto_nuevo-monto_ant
                    result.write({'retenciones': result.retenciones + monto_difer})

        res = super(AbatarMovimientosLines, self).write(vals)

        if vals.get('pagos_id'):
            if type(vals.get('pagos_id'))==int:
                result = self.env['abatar.pagos'].search([('id', '=', vals.get('pagos_id'))])
            else:
                id= self.env['abatar.pagos'].search([('name_gral', '=', vals.get('pagos_id'))])
                result = self.env['abatar.pagos'].search([('id', '=', id)])

            string = ''
            if result.desc:
                string = result.desc
            if self.texto:
                string += ' - pago por caja: '+self.texto
            id_safe=['1', result.clientes_id.id, self.monto, string, self.caja_id.id]

            nuevo_adjunto=False
            if self.adjunto:
                nuevo_adjunto=self.adjunto

            retenc = 0
            if self.retenciones:
                retenc = self.retenciones


            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                'pago': id_safe[2]+result.pago,
                'retenciones': retenc+result.retenciones,
                'desc': id_safe[3],
                'caja': id_safe[4]
            }

            result.write(vals1)
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')

            vals3={
                'adjunto': [(0, 0, {
                    'adjunto': nuevo_adjunto,
                    'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                    'desc': 'carga por caja. ' + str(id_safe[4]),
                    'pagos_id': result.id
                })]}
            if nuevo_adjunto:
                if type(vals.get('pagos_id')) == int:
                    result = self.env['abatar.pagos'].search([('id', '=', vals.get('pagos_id'))])
                else:
                    id = self.env['abatar.pagos'].search([('name_gral', '=', vals.get('pagos_id'))])
                    result = self.env['abatar.pagos'].search([('id', '=', id)])
                result.write(vals3)
            ticket=self.env['abatar.pagos'].search([('id', '=', vals.get('pagos_id'))])
            if round(ticket.saldo, 2)==0:
                ticket.write({'active' : Pagos_active})
        if vals.get('materiales_id'):
            result = self.env['abatar.materiales'].search([('id', '=', vals.get('materiales_id'))])
            string = ''
            if result.desc:
                string = result.desc
            if self.texto:
                string += ' - pago por caja: '+self.texto
            id_safe = ['2', vals.get('materiales_id'), result.proveedor_id.id, self.monto, string, self.caja_id.id]

            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', id_safe[5])]).fecha_de_caja,
                'pago': id_safe[3]+result.pago,
                'desc': id_safe[4],
                'caja': id_safe[5]
            }
            result.write(vals1)
            nuevo_adjunto=False
            if self.adjunto:
                nuevo_adjunto=self.adjunto
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
            vals3={
                'adjunto': [(0, 0, {
                    'adjunto': nuevo_adjunto,
                    'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                    'desc': 'carga por caja. ' + str(id_safe[4]),
                    'materiales_id': vals.get('materiales_id')
                })]}
            if nuevo_adjunto:
                result.write(vals3)
            ticket=self.env['abatar.materiales'].search([('id', '=', vals.get('materiales_id'))])
            if round(ticket.subtotal)==0:
                ticket.write({'active' : False})
        if vals.get('deuda_id'):

            result = self.env['abatar.deudas'].search([('id', '=', vals.get('deuda_id'))])

            string = ''
            if result.desc:
                string = result.desc
            if self.texto:
                string += ' - pago por caja: '+self.texto

            id_safe = ['3', result.proveedor.id, self.monto, string, self.tipo.name,
                       self.caja_id.id]

            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                'pago': id_safe[2] + result.pago,
                'desc': id_safe[4],
                'caja': id_safe[5],
            }


            result.write(vals1)
            nuevo_adjunto=False
            if self.adjunto:
                nuevo_adjunto=self.adjunto
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
            vals3 = {
                'adjunto': [(0, 0, {
                    'adjunto': nuevo_adjunto,
                    'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                    'desc': 'carga por caja. ' + str(id_safe[5]),
                    'deudas_id': vals.get('deuda_id')
                })]}
            if nuevo_adjunto:
                result.write(vals3)
            ticket = self.env['abatar.deudas'].search([('id', '=', vals.get('deuda_id'))])
            if round(ticket.subtotal) == 0:
                ticket.write({'active': False})
        if vals.get('mensuales_id'):
            string=''
            if self.texto:
                string+=self.texto
            id_safe=['2', vals.get('mensuales_id'), self.monto, string, self.caja_id.id]
            vals1 = {
                'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                'monto': id_safe[2],
                'mensuales_id': id_safe[1],
                'desc': 'pago por caja. '+id_safe[3],
                'caja': id_safe[4]
            }
            result = self.env['abatar.mensuales'].search([('id', '=', id_safe[1]), ('active', 'in', (True, False))])
            result.write({'pagos': [(0, 0, vals1)]})


            nuevo_adjunto=False
            if self.adjunto:
                nuevo_adjunto=self.adjunto
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
            vals3 = {
                'adjunto': [(0, 0, {
                    'adjunto': nuevo_adjunto,
                    'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                    'desc': 'carga por caja. ' + str(id_safe[4]),
                    'mensuales_id': vals.get('mensuales_id')
                })]}

            if nuevo_adjunto:
                result.write(vals3)
            ids = []
            for prev in result.pagos:
                ids.append(prev.id)
            max = 0
            for i in range(len(ids)):
                if ids[i] >= max:
                    max = ids[i]
            vals2 = {'se_pago2': max}
        if vals.get('empleados_id'):
            string = ''
            if self.texto:
                string += self.texto
            id_safe = ['2', self.empleados_id.id, self.monto, string, self.caja_id.id]

            vals1 = {
                'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                'monto': id_safe[2],
                'empleados_id': id_safe[1],
                'desc': 'pago por caja. ' + id_safe[3],
                'caja': id_safe[4]
            }
            result = self.env['abatar.empleados'].search([('id', '=', id_safe[1])])
            result.write({'pagos': [(0, 0, vals1)]})
            ids = []
            for prev in result.pagos:
                ids.append(prev.id)
            max = 0
            for i in range(len(ids)):
                if ids[i] >= max:
                    max = ids[i]
            vals2 = {'se_pago2': max}

            nuevo_adjunto=False
            if self.adjunto:
                nuevo_adjunto=self.adjunto
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')

            vals3 = {
                'adjunto': [(0, 0, {
                    'adjunto': nuevo_adjunto,
                    'fecha_op': self.env['abatar.caja'].search([('id', '=', self.caja_id.id)]).fecha_de_caja,
                    'desc': 'carga por caja. ' + str(id_safe[4]),
                    'empleados_id': vals.get('empleados_id')
                })]}
            if nuevo_adjunto:
                result.write(vals3)


        if vals2:
            res = super(AbatarMovimientosLines, self).write(vals2)
        return res


    @api.model
    def create(self, vals):
        vals2={}
        if vals.get('pagos_id'):
            if type(vals.get('pagos_id')) == int:
                result = self.env['abatar.pagos'].search([('id', '=', vals.get('pagos_id'))])
            else:
                id = self.env['abatar.pagos'].search([('name_gral', '=', vals.get('pagos_id'))])
                result = self.env['abatar.pagos'].search([('id', '=', id)])
            string = ''
            if result.desc:
                string = result.desc
            if vals.get('texto'):
                string += ' - pago por caja: '+ vals.get('texto')
            id_safe=['1', result.clientes_id.id,  vals.get('monto'), string, vals.get('caja_id')]

            nuevo_adjunto=False
            if vals.get('adjunto'):
                nuevo_adjunto= vals.get('adjunto')

            retenc = 0
            if vals.get('retenciones'):
                retenc = vals.get('retenciones')


            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                'pago': id_safe[2]+result.pago,
                'retenciones': retenc+result.retenciones,
                'desc': id_safe[3],
                'caja': id_safe[4]
            }

            result.write(vals1)
            if vals.get('adjunto'):

                vals3={
                    'adjunto': [(0, 0, {
                        'adjunto': nuevo_adjunto,
                        'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                        'desc': 'carga por caja. ' + str(id_safe[4]),
                        'pagos_id': result.id
                    })]}
                result.write(vals3)
            if round(result.saldo, 2)==0:
                result.write({'active' : Pagos_active})
        if vals.get('materiales_id'):
            result = self.env['abatar.materiales'].search([('id', '=', vals.get('materiales_id'))])
            string = ''
            if result.desc:
                string = result.desc
            if vals.get('texto'):
                string += ' - pago por caja: '+vals.get('texto')
            id_safe = ['2', vals.get('materiales_id'), result.proveedor_id.id, vals.get('monto'), string, vals.get('caja_id')]

            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                'pago': id_safe[3]+result.pago,
                'desc': id_safe[4],
                'caja': id_safe[5]
            }
            result.write(vals1)
            nuevo_adjunto=False
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
                vals3={
                    'adjunto': [(0, 0, {
                        'adjunto': nuevo_adjunto,
                        'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                        'desc': 'carga por caja. ' + str(id_safe[4]),
                        'materiales_id': vals.get('materiales_id')
                    })]}
                result.write(vals3)
            if round(result.subtotal)==0:
                result.write({'active' : False})
        if vals.get('deuda_id'):

            result = self.env['abatar.deudas'].search([('id', '=', vals.get('deuda_id'))])

            string = ''
            if result.desc:
                string = result.desc
            if vals.get('texto'):
                string += ' - pago por caja: '+vals.get('texto')

            id_safe = ['3', result.proveedor.id, vals.get('monto'), string, vals.get('tipo'),
                       vals.get('caja_id')]

            vals1 = {
                'fecha_pago': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                'pago': id_safe[2] + result.pago,
                'desc': id_safe[4],
                'caja': id_safe[5],
            }


            result.write(vals1)

            nuevo_adjunto=False
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
                vals3 = {
                    'adjunto': [(0, 0, {
                        'adjunto': nuevo_adjunto,
                        'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                        'desc': 'carga por caja. ' + str(id_safe[5]),
                        'deudas_id': vals.get('deuda_id')
                    })]}
                result.write(vals3)
            if round(result.subtotal) == 0:
                result.write({'active': False})
        if vals.get('mensuales_id'):
            string=''
            if vals.get('texto'):
                string+=vals.get('texto')
            id_safe=['2', vals.get('mensuales_id'), vals.get('monto'), string, vals.get('caja_id')]
            vals1 = {
                'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                'monto': id_safe[2],
                'mensuales_id': id_safe[1],
                'desc': 'pago por caja. '+id_safe[3],
                'caja': id_safe[4]
            }
            result = self.env['abatar.mensuales'].search([('id', '=', id_safe[1]), ('active', 'in', (True, False))])
            result.write({'pagos': [(0, 0, vals1)]})


            nuevo_adjunto=False
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')
                vals3 = {
                    'adjunto': [(0, 0, {
                        'adjunto': nuevo_adjunto,
                        'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                        'desc': 'carga por caja. ' + str(id_safe[4]),
                        'mensuales_id': vals.get('mensuales_id')
                    })]}

                result.write(vals3)
            ids = []
            for prev in result.pagos:
                ids.append(prev.id)
            max = 0
            for i in range(len(ids)):
                if ids[i] >= max:
                    max = ids[i]
            vals2 = {'se_pago2': max}
        if vals.get('empleados_id'):
            string = ''
            if vals.get('texto'):
                string += vals.get('texto')
            id_safe = ['2', vals.get('empleados_id'), vals.get('monto'), string, vals.get('caja_id')]

            vals1 = {
                'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                'monto': id_safe[2],
                'empleados_id': id_safe[1],
                'desc': 'pago por caja. ' + id_safe[3],
                'caja': id_safe[4]
            }
            result = self.env['abatar.empleados'].search([('id', '=', id_safe[1])])
            result.write({'pagos': [(0, 0, vals1)]})
            ids = []
            for prev in result.pagos:
                ids.append(prev.id)
            max = 0
            for i in range(len(ids)):
                if ids[i] >= max:
                    max = ids[i]
            vals2 = {'se_pago2': max}

            nuevo_adjunto=False
            if vals.get('adjunto'):
                nuevo_adjunto=vals.get('adjunto')

                vals3 = {
                    'adjunto': [(0, 0, {
                        'adjunto': nuevo_adjunto,
                        'fecha_op': self.env['abatar.caja'].search([('id', '=', vals.get('caja_id'))]).fecha_de_caja,
                        'desc': 'carga por caja. ' + str(id_safe[4]),
                        'empleados_id': vals.get('empleados_id')
                    })]}
                result.write(vals3)

        if vals2:
            vals.update({'se_pago2': vals2.get('se_pago2')})
        res = super(AbatarMovimientosLines, self).create(vals)
        return res

class AbatarCajaTipo(models.Model):
    _name = "abatar.caja.tipo"
    _description = "Abatar caja tipo"
    _rec_name='name'

    name = fields.Char(string="Tabla de sujeto")
    desc = fields.Text(string="Descripcion")



class AbatarMensuales(models.Model):
    _name = "abatar.mensuales"
    _description = "Lista de Servicios Mensuales"
    _inherit=['abataradd.resumenbus']
    _rec_name = 'name_gral'

    active=fields.Boolean('Active', default=True)
    name = fields.Char(string="Servicio", required=True)
    name_gral= fields.Char(string="Nombre rec", store=True, readonly=True, compute='set_name_gral')
    facturas=fields.Binary(string="Facturas")
    es_afip=fields.Boolean(string="Es IMPUESTOS?", default=False)
    monto=fields.Float(string="Monto mensual")
    saldo=fields.Float(string="Saldo a cuenta", store=True, readonly=True, compute='set_saldo')
    fecha_saldo=fields.Date(string="Fecha de ult. actualización:")
    desc = fields.Text(string="Descripcion")
    empleados_id = fields.Many2one('abatar.empleados',string="Empleado Asociado / Responsable")

    pagos = fields.One2many('abatar.pagos.mensuales', 'mensuales_id', string="Pagos y Deudas", help="Pagos en positivo y Deudas en Negativo")
    adjunto= fields.One2many('abatar.mensuales.adjuntos', 'mensuales_id', string='Adjuntos')

    @api.multi
    def write(self, vals):
        if BUSQUEDAON==True:
            try:
                if self.ensure_one():
                    if type(self.id)==int:
                        resum=Analize_model3(self, self._name, [('id', '=', self.id), ('active', 'in', (True, False))])
                        if len(resum)>50:
                            vals['resumen_busqueda']=datetime.strftime(fields.datetime.now(), '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarMensuales, self).write(vals)
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AbatarMensuales, self).default_get(fields)

        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen

        return rec

    #@api.onchange('desc')
    #def pinto(self):
    #    for rec in self.env['abatar.caja'].search([]):
    #        rec.set_total_movimientos()

    @api.depends('pagos')
    def set_saldo(self):
        for rec in self:
            saldo=0
            if rec.pagos:
                for res in rec.pagos:
                    saldo+=res.monto
            rec.saldo=saldo

    def set_mensuales(self):
        today = datetime.today().date()
        day = today.day
        month = today.month
        year = today.year
        for res in self.env['abatar.mensuales'].search([]):
            if res.monto:
                if day == 1:
                    res.write({'pagos': [(0, 0, {
                        'fecha_op': today,
                        'monto': -res.monto,
                        'mensuales_id': res.id,
                        'desc': 'Carga automatica Monto MES %i-%i.' % (month, year)
                    })]})


    @api.depends('name', 'desc')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral=rec.name
            if rec.desc:
                rec.name_gral += ' - ' + rec.desc


class AbatarMensualesAdjuntos(models.Model):
    _name = "abatar.mensuales.adjuntos"
    _description = "Abatar adjuntos de Mensuales"
    _rec_name = 'name_gral'

    name_gral=fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date(string='Fecha de caja')
    adjunto = fields.Binary(string='Adjunto')
    desc = fields.Char(string="Descripcion")

    mensuales_id = fields.Many2one('abatar.mensuales', string='mensuales ID')

    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral='AD'+str(rec.id)+str(rec.adjunto)


class AbatarPagosMensuales(models.Model):
    _name = 'abatar.pagos.mensuales'
    _description = "Pagos de Servicios Mensuales"
    _rec_name='name_gral'
    _order='fecha_op desc, id desc'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.pago_emp_id:
                rec.pago_emp_id.unlink()
                rec.pago_emp_id=False

        res = super(AbatarPagosMensuales, self).unlink()
        return res

    fecha_op = fields.Date(string="Fecha Pago", required=True)
    monto = fields.Float(string="Monto")
    desc = fields.Text(string="Descripción")
    mensuales_id = fields.Many2one('abatar.mensuales', string="mensuales_id")
    mensuales_id2 = fields.Many2one('abatar.mensuales', string="mensuales_id2",store=True,readonly=True, compute='set_mensual')
    mensual_id = fields.Many2one('abatar.mensuales', string="mensual_id")
    empleados_id = fields.Many2one('abatar.empleados',related="mensuales_id.empleados_id", store=True, readonly=True,string="Empleado Asociado / Responsable")
    pago_emp_id=fields.Many2one('abatar.pagos.empleados',string="Id de pago Empleado Asociado")
    caja=fields.Many2one('abatar.caja', string="Caja_id")
    adjunto = fields.Binary(string='Adjunto')

    name_gral=fields.Char(compute='set_name_gral', string="Nombre Rec", store=True, readonly=True)

    es_afip=fields.Boolean(related='mensuales_id2.es_afip', store=True, readonly=True, string='Es Impuesto')
    saldo=fields.Float('Saldo', store=True, readonly=True, compute='set_saldo')


    @api.multi
    def write(self, vals):
        if self.empleados_id and self.pago_emp_id:

            if vals.get('fecha_op'):
                self.pago_emp_id.fecha_op=vals.get('fecha_op')
            if vals.get('monto'):
                self.pago_emp_id.monto=-vals.get('monto')
        res = super(AbatarPagosMensuales, self).write(vals)

        return res



    @api.model
    def create(self, vals):
        result = super(AbatarPagosMensuales, self).create(vals)
        if result.empleados_id:
            if result.monto:
                if result.fecha_op:
                    strin='NO-HALLADO'
                    if result.mensuales_id2:
                        strin=result.mensuales_id2.name_gral
                    elif result.mensuales_id:
                        strin=result.mensuales_id.name_gral
                    result.pago_emp_id=result.empleados_id.pagos.create({
                        'fecha_op':result.fecha_op,
                        'monto':-result.monto,
                        'empleados_id':result.empleados_id.id,
                        'desc': 'Carga de pago a cuenta de empleado por Servicio %s.'%strin,
                    }).id

        return result

    @api.depends('fecha_op','monto','mensuales_id2')
    def set_saldo(self):
        for rec in self:
            ants0=self.env['abatar.pagos.mensuales'].search([('fecha_op','<',rec.fecha_op), ('mensuales_id2', '=',rec.mensuales_id2.id)], order='fecha_op asc,id asc')
            #ants0=rec.mensuales_id.pagos.search([('fecha_op','<',rec.fecha_op)], order='fecha_op asc,id asc')
            integ0=0
            for ant in ants0:
                if ant.monto:
                    integ0+=ant.monto
            #ants1=rec.mensuales_id.pagos.search([('fecha_op','=',rec.fecha_op)], order='id asc')
            ants1=self.env['abatar.pagos.mensuales'].search([('fecha_op','=',rec.fecha_op), ('mensuales_id2', '=',rec.mensuales_id2.id)], order='id asc')
            for ant in ants1:
                if ant.id==rec.id:
                    integ0+=ant.monto
                    break
                elif ant.monto:
                    integ0+=ant.monto
            rec.saldo=integ0



    @api.depends('fecha_op', 'mensuales_id', 'monto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'AD' + str(rec.id)
            if rec.fecha_op:
                rec.name_gral += ' - '+fields.Date.from_string(rec.fecha_op).strftime('%d/%m/%y')
            if rec.mensuales_id:
                rec.name_gral += ' - '+rec.mensuales_id.name

    @api.onchange("desc")
    def set_mensuales_id(self):
        _logger = logging.getLogger(__name__)
        _logger.error('YOGASTONADM: SET_MENSUALES_ID')

        for rec in self.env['abatar.pagos.mensuales'].search([]):
            if rec.mensuales_id:
                pass
            elif rec.mensual_id:
                rec.mensuales_id=rec.mensual_id.id

    @api.depends('mensuales_id', 'mensual_id')
    def set_mensual(self):
        for rec in self:
            if rec.mensuales_id:
                rec.mensuales_id2=rec.mensuales_id.id
            elif rec.mensual_id:
                rec.mensuales_id2=rec.mensual_id.id

    @api.multi
    def action_view_caja(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.caja',
            'res_id': self.caja.id,
        }

class AbatarEmpleados(models.Model):
    _name = "abatar.empleados"
    _description = "Lista de Empleados"
    _inherit=['abataradd.resumenbus']
    _rec_name='name'

    name= fields.Char(string="Nombre y Apellido")
    dni= fields.Char(string="DNI")
    tel= fields.Char(string="Telefono")
    sueldo= fields.Float(string="Sueldo")
    frecuencia_sueldo=fields.Selection([('semanal', 'Semanal'),('quincenal', 'Quincenal'),('mensual', 'Mensual')], string="Frecuencia de cobro")
    saldo=fields.Float(string="Saldo total", store=True, readonly=True, compute='set_saldo')

    desc= fields.Text(string="Descripcion")

    pagos=fields.One2many('abatar.pagos.empleados', 'empleados_id', string="Pagos")
    adjunto= fields.One2many('abatar.empleados.adjuntos', 'empleados_id', string='Adjuntos')

    dueño= fields.Boolean(string="Es Dueño? (EHRB)", help='Indica si forma parte de inversores EHRB y Silvina Rosenthal', default=False)

    @api.depends('pagos')
    def set_saldo(self):
        for rec in self:
            saldo=0
            if rec.pagos:
                for res in rec.pagos:
                    saldo+=res.monto
            rec.saldo=saldo

    @api.multi
    def write(self, vals):
        if BUSQUEDAON == True:
            try:
                if self.ensure_one():
                    if type(self.id) == int:
                        resum = Analize_model3(self, self._name,
                                               [('id', '=', self.id)])
                        if len(resum) > 50:
                            vals['resumen_busqueda'] = datetime.strftime(fields.datetime.now(),
                                                                         '%d/%m/%Y - %H:%M:%S') + resum
            except:
                pass
        res = super(AbatarEmpleados, self).write(vals)
        return res


    @api.model
    def default_get(self, fields):
        rec = super(AbatarEmpleados, self).default_get(fields)
        resumen = ''
        for key in rec:
            resumen += key + ':' + Typyze('str', rec[key]) + '\n'
        rec['resumen_busqueda'] = resumen
        return rec

    #@api.onchange('desc')
    #def refresh(self):
    #    for rec in self.env['abatar.caja'].search([]):
    #        rec.obs='hi'


    def set_sueldos_frecuentes(self):
        today = datetime.today().date()
        day = today.day
        month = today.month
        year = today.year
        ho=0
        for res in self.env['abatar.empleados'].search([]):
            if ho==0:
                res.write({'desc': 'Carga automatica SET SUELDOS FRECUENTES.'})
                ho=1
            if res.frecuencia_sueldo and res.sueldo:
                if res.frecuencia_sueldo == 'semanal' and today.weekday() == 4:
                    res.write({'pagos': [(0, 0, {
                        'fecha_op': today,
                        'monto': -res.sueldo,
                        'empleados_id': res.id,
                        'desc': 'Carga automatica sueldo semanal (viernes).'
                    })]})
                elif res.frecuencia_sueldo == 'quincenal' and day in (1, 15):
                    if day == 1:
                        res.write({'pagos': [(0, 0, {
                            'fecha_op': today,
                            'monto': -res.sueldo,
                            'empleados_id': res.id,
                            'desc': 'Carga automatica sueldo 1ra Quincena %i-%i.' % (month, year)
                        })]})
                    elif day == 15:
                        res.write({'pagos': [(0, 0, {
                            'fecha_op': today,
                            'monto': -res.sueldo,
                            'empleados_id': res.id,
                            'desc': 'Carga automatica sueldo 2da Quincena %i-%i.' % (month, year)
                        })]})
                elif res.frecuencia_sueldo == 'mensual' and day == 1:
                    res.write({'pagos': [(0, 0, {
                        'fecha_op': today,
                        'monto': -res.sueldo,
                        'empleados_id': res.id,
                        'desc': 'Carga automatica sueldo MES %i-%i.' % (month, year)
                    })]})

class AbatarEmpleadosAdjuntos(models.Model):
    _name = "abatar.empleados.adjuntos"
    _description = "Abatar adjuntos de Empleados"
    _rec_name = 'name_gral'

    name_gral=fields.Char(compute='set_name_gral', string="Nombre rec")
    fecha_op = fields.Date(string='Fecha de caja')
    adjunto = fields.Binary(string='Adjunto')
    desc=fields.Char(string="Descripcion")

    empleados_id = fields.Many2one('abatar.empleados', string='empleados ID')

    @api.one
    @api.depends('adjunto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral='AD'+str(rec.id)+str(rec.adjunto)

class AbatarPagosEmpleados(models.Model):
    _name='abatar.pagos.empleados'
    _description = "Pagos de Empleados"
    _rec_name='name_gral'
    _order='fecha_op desc,id desc'

    name_gral = fields.Char(compute='set_name_gral', string="Nombre Rec", store=True, readonly=True)
    fecha_op=fields.Date(string="Fecha Pago", required=True)
    monto=fields.Float(string="Monto")
    desc=fields.Text(string="Descripción")
    empleados_id=fields.Many2one('abatar.empleados', string="Empleados_id")
    caja=fields.Many2one('abatar.caja', string="Caja_id")

    saldo=fields.Float('Saldo', store=True, readonly=True, compute='set_saldo')
    dolar_uso = fields.Float(string='Dolar', store=True, readonly=True, compute='set_dolar')
    dolar2_uso = fields.Float(string='Dolar(Of)', store=True, readonly=True, compute='set_dolar')
    monto_dolar = fields.Float(string='Monto U$D', store=True, readonly=True, compute='set_monto_dolar')

    @api.model
    def set_todos_dolar(self):
        for rec in self.env['abatar.pagos.empleados'].search([]):
            rec.monto += 1
            rec.monto -= 1

    @api.depends('fecha_op', 'monto','dolar_uso')
    def set_monto_dolar(self):
        for rec in self:
            if rec.dolar_uso:
                rec.monto_dolar=rec.monto/rec.dolar_uso

    @api.depends('fecha_op', 'monto')
    def set_dolar(self):
        for rec in self:
            if rec.fecha_op:
                dolar_uso=0
                dolar2_uso=0
                fecha_orden= str(fields.Date.from_string(rec.fecha_op).strftime('%d/%m/%y'))
                dia_ejec=int(fecha_orden[:fecha_orden.find('/')])
                rest=fecha_orden[fecha_orden.find('/')+1:]
                mes_ejec=int(rest[:rest.find('/')])
                rest2=rest[rest.find('/')+1:]
                año_ejec=2000+int(rest2[:])

                actu=self.env['abatar.dolar'].search([('fecha', '=', fields.Date.from_string(rec.fecha_op))], limit=1)
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

                actu=self.env['abatar.dolar2'].search([('fecha', '=', fields.Date.from_string(rec.fecha_op))], limit=1)
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

    @api.depends('fecha_op','monto','empleados_id')
    def set_saldo(self):
        for rec in self:
            ants0=self.env['abatar.pagos.empleados'].search([('fecha_op','<',rec.fecha_op), ('empleados_id', '=',rec.empleados_id.id)], order='fecha_op asc')
            integ0=0
            for ant in ants0:
                if ant.monto:
                    integ0+=ant.monto
            ants1=self.env['abatar.pagos.empleados'].search([('fecha_op','=',rec.fecha_op), ('empleados_id', '=',rec.empleados_id.id)], order='id asc')
            for ant in ants1:
                if ant.id==rec.id:
                    integ0+=ant.monto
                    break
                elif ant.monto:
                    integ0+=ant.monto
            rec.saldo=integ0


    @api.depends('fecha_op', 'empleados_id', 'monto')
    def set_name_gral(self):
        for rec in self:
            rec.name_gral = 'AD' + str(rec.id)
            if rec.fecha_op:
                rec.name_gral += ' - ' + fields.Date.from_string(rec.fecha_op).strftime('%d/%m/%y')
            if rec.empleados_id:
                rec.name_gral += ' - ' + rec.empleados_id.name

    @api.multi
    def action_view_caja(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'abatar.caja',
            'res_id': self.caja.id,
        }
class AbatarIngresosLines(models.Model):
    _name = "abatar.ingresos.lines"
    _description = "Abatar ingresos lines"
    _rec_name='texto'
    _order='caja_id desc'

    texto = fields.Text(string='Texto', required=True)
    monto = fields.Float(string='Monto')
    monto_salida = fields.Float(string='Monto Salida')
    monto_entrada = fields.Float(string='Monto Entrada')
    tipo_salida = fields.Selection([('efectivo','Efectivo ($)'),('banco','Banco'),('dolar','Dolar (U$d)')],string='Tipo Salida')
    selec_salida = fields.Many2one('abatar.bancos',string='Cuenta de Salida', default=False)
    tipo_entrada = fields.Selection([('efectivo','Efectivo ($)'),('banco','Banco'),('dolar','Dolar (U$d)')],string='Tipo Entrada')
    selec_entrada = fields.Many2one('abatar.bancos',string='Cuenta de Entrada', default=False)
    pago_electronico = fields.Boolean(string='xBanco', default=False)
    adjunto = fields.Binary(string='Adjunto')
    caja_id = fields.Many2one('abatar.caja', string='caja ID', readonly=True)

    def aplicar_mov_interno(self):
        if self.monto_salida and self.monto_entrada and self.tipo_salida and self.tipo_entrada:
            if self.tipo_salida not in ('efectivo', 'dolar') and not self.selec_salida:
                raise UserWarning("Debe elegir un tipo de caja de salida si no es efectivo.")
            if self.tipo_entrada not in ('efectivo', 'dolar') and not self.selec_entrada:
                raise UserWarning("Debe elegir un tipo de caja de entrada si no es efectivo.")
            for elem in self.caja_id.billetes:
                if self.tipo_salida=='efectivo':
                    pass
                elif self.tipo_salida=='banco':
                    if elem.bancos:
                        if elem.bancos.id==self.selec_salida.id:
                            elem.monto-=self.monto_salida
                elif self.tipo_salida=='dolar':
                    pass
                if self.tipo_entrada=='efectivo':
                    pass
                elif self.tipo_entrada=='banco':
                    if elem.bancos:
                        if elem.bancos.id==self.selec_entrada.id:
                            elem.monto+=self.monto_entrada
                elif self.tipo_entrada=='dolar':
                    pass
            self.caja_id.write({'obs':'hi'})

class AbatarBanco(models.Model):
    _name = "abatar.bancos"
    _description = "Abatar Cuentas Bancarias"
    _rec_name='name'

    name = fields.Char(string='Nombre de Cuenta')
    active = fields.Boolean(string='Active', default=True)


class AbatarCajaBilletes(models.Model):
    _name = "abatar.caja.billetes"
    _description = "Abatar Caja Billetes"
    _rec_name='name'

    name = fields.Char(string='Nombre (denominacion)')
    monto = fields.Float(string='Monto')
    cant=fields.Integer(string="Cantidad")
    dolar=fields.Boolean(string="Es U$d?", default=False)
    bancos=fields.Many2one('abatar.bancos',string="Es Banco", default=False)
    total=fields.Float(string="Total", compute='set_total')
    caja_id=fields.Many2one('abatar.caja', string="caja id")

    @api.onchange('cant', 'monto')
    def set_total(self):
        for rec in self:
            if rec.monto:
                if rec.cant:
                    rec.total=rec.cant*rec.monto
                else:
                    rec.total=0
