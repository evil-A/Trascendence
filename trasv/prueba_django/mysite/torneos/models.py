# coding=utf-8
from django.db import models
from django.contrib.auth.models import User
import datetime

# Se añaden los modelos de datos -- similar a tablas de base de datos
# por defecto añade id a cada tabla

class Torneo(models.Model):
	nombre = models.CharField(default="", max_length=150)
	comienzo_inscripcion = models.DateTimeField(null=True, blank=True, default=None)
	fin_inscripcion = models.DateTimeField(null=True, blank=True, default=None)
	comienzo_partidos = models.DateTimeField(null=True, blank=True, default=None)
	minutos_duracion_maxima_partidos = models.IntegerField(default=15)
	minutos_entre_partidos = models.IntegerField(default=30)
	fase_actual = models.IntegerField(default=0)
	terminado = models.BooleanField(default=False)
	jugadores = models.ManyToManyField(User, blank=True, default=None)
	def setDateTimes(self):
		t = datetime.datetime.now()
		d1 = datetime.timedelta(days=1)
		d2 = datetime.timedelta(days=2)
		d3 = datetime.timedelta(days=3)
		self.comienzo_inscripcion = t + d1
		self.fin_inscripcion = t + d2
		self.comienzo_partidos = t + d3
	def getFase(self):
		if self.terminado:
			return self.fase_actual
		t = datetime.datetime.now()
		if t < self.fin_inscripcion:
			return 0
		if t < self.comienzo_partidos:
			return 1
		p = 1
		mep = datetime.timedelta(minutes=self.minutos_entre_partidos)
		while True:
			if t < (self.comienzo_partidos + mep * p):
				return p+1
			p += 1
	def esHoraDeEmpezar(self):
		if self.terminado:
			return False
		if self.fase_actual == 0:
			return False
		t = datetime.datetime.now()
		margen = datetime.timedelta(seconds=30)
		mep = datetime.timedelta(minutes=self.minutos_entre_partidos)
		mepPn = (self.fase_actual - 1) * mep
		tOk = self.comienzo_partidos + mepPn
		if tOk - margen < t and t < tOk + margen:
			return True
		return False
	
class FaseTorneo(models.Model):
	torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
	fase = models.IntegerField(default=0)
	#jugadores = models.ManyToManyField(User, blank=True, default=None, related_name = 'ft_users_jugadores')
	lista_jugadores = models.TextField(default="")
	lista_partidos = models.TextField(default="")
	lista_partidos_resultados = models.TextField(default="")
	ganadores = models.ManyToManyField(User, blank=True, default=None, related_name = 'ft_users_ganadores')
	class Meta:
		unique_together = (("torneo", "fase"), )


 