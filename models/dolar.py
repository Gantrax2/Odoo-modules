from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime
from datetime import date

from odoo.addons.om_abatartrucks.Analize import execCode3_ret


def Compdat(b):
	DATE=True
	if type(b)==str:
		for i_i in range(len(b)):
			if i_i in (0,1,3,4,6,7,8,9):
				if b[i_i] in ('0','1','2','3','4','5','6','7','8','9'):
					pass
				else:
					DATE=False
			else:
				if b[i_i] == "/":
					pass
				else:
					DATE=False
	else:
		DATE=False

	return DATE

def Prevdat(b):

	start_date = date(int(b[6:]),int(b[3:5]),int(b[:2]))
	Previous_Date = start_date - datetime.timedelta(days=1)
	a=Previous_Date.strftime('%d/%m/%Y')
	return a
def DateG(b):

	return date(int(b[6:]),int(b[3:5]),int(b[:2]))
def daysdates(a,b):

	date1 = date(int(a[6:]),int(a[3:5]),int(a[:2]))
	date2 = date(int(b[6:]),int(b[3:5]),int(b[:2]))
	Difer_date = date2-date1
	#Lprint('diferdate:',Difer_date.days)
	return Difer_date.days


class AbatarDolar(models.Model):
    _name = "abatar.dolar"
    _description = "Abatar Dolar Blue"
    _rec_name = "pesos"
    _order ="fecha desc"

    fecha = fields.Date(string='Fecha')
    pesos = fields.Float(string='Cotizacion', help="Pesos COMPRA")

    def cargadolar(self):
        actrec=self.env['abatar.dolar'].search([], order='fecha desc', limit=1).fecha
        fields.Glog('CARGA DOLAR EJECUTANDO...')
        fields.Glog('Ultima fehca cargada: %s' % actrec.strftime('%d/%m/%Y'))
        deltadate=datetime.datetime.today().date()-actrec

        fields.Glog('Dias hasta hoy: %s' % str(deltadate.days))
        if deltadate.days>4:
            A = actrec.strftime('%d/%m/%Y')

            lis_dates = []
            ind_dates = []
            act_date = datetime.datetime.today().date().strftime('%d/%m/%Y')
            Lenlist = daysdates(A, act_date)
            for i in range(Lenlist):
                lis_dates.append(act_date)
                ind_dates.append(-i)
                act_date = Prevdat(act_date)
            b = list(zip(ind_dates, lis_dates))
            b.sort()
            ind_dates, fechas = zip(*b)

            montos=execCode3_ret('/home/julian/Descargas/chromedriver19/chromedriver-linux64/lecturaDolarblue2_odoo.py',actrec.strftime('%d/%m/%Y'))#,'home/julian/Descargas/chromedriver19/chromedriver-linux64/','blue_salida.txt')

            fields.Glog('Dias mayores a 4...')
            fields.Glog('fechas' % str(fechas))
            fields.Glog('montos' % str(montos))
            #for i in range(len(fechas)):
            #    self.env['abatar.dolar'].create({'fecha':fechas[i],'monto':montos[i]})
