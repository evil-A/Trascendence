# coding=utf-8

from django.db import models
from django.contrib.auth.models import User
import datetime

# Se añaden los modelos de datos -- similar a tablas de base de datos
# por defecto anade id a cada tabla

# jugador1 a la izquierda -- jugador2 a la derecha
# coordenadas: 0, 0 centro del campo, x hacia derecha, y hacia abajo

class Partido_enJuego(models.Model):
	TIPO = (
		("R", "Rápido"),
		("T", "Torneo"),
	)
	tipo = models.CharField(max_length=1, choices=TIPO, default="R")
	# Solo para torneos:
	idTorneo = models.IntegerField(default=0)
	nFaseTorneo = models.IntegerField(default=0)
	# Si se pasa este tiempo el partido acaba >>
	limiteTiempoTorneo = models.DateTimeField(null=True, blank=True, default=None)
	# Si se pasa este tiempo con un solo jugador, el otro pierde el partido >>
	limiteTiempoConUnJugador = models.DateTimeField(null=True, blank=True, default=None)
	ESTADO_TORNEO = (
		("0", "Sin jugadores"),
		("1", "Jugador 1 dentro"),
		("2", "Jugador 2 dentro"),
		("A", "Ambos jugadores dentro"),
	)
	estadoTorneo = models.CharField(max_length=1, choices=ESTADO_TORNEO, default="0")
	# si el partido de torneo acaba por tiempo y hay empate a puntos gana el jugador1
	# el orden de jugadores se calcula cada fase del tornoe y es aleatorio
	#
	jugador1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'pj_user_jugador1')
	jugador2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'pj_user_jugador2')
	empezado = models.BooleanField(default=False) # si true partido empezado
	terminado = models.BooleanField(default=False) # si true partido terminado
	comienzo = models.DateTimeField(null=True, blank=True, default=None) # comienzo del partido
	rearranque =  models.DateTimeField(null=True, blank=True, default=None) 
	fin = models.DateTimeField(null=True, blank=True, default=None) # final del partido
	desconectado = models.BooleanField(default=False) # si los clientes dejan de pedir el estado durante un tiempo se desconecta
	jugador1_marcador = models.IntegerField(default=0)	# marcador de puntos
	jugador2_marcador = models.IntegerField(default=0) 
	pausa = models.BooleanField(default=False) # si true partido en pausa # si se marca un punto se espera 1 s antes de seguir (saque)
	finDePausa = models.DateTimeField(null=True, blank=True, default=None) # si esta en pausa este es el momento que se quitara la pausa
	pelota_actualizacion = models.DateTimeField(null=True, blank=True, default=None)
	pelota_x = models.FloatField(default=0)
	pelota_y = models.FloatField(default=0)
	pelota_velocidad_x = models.FloatField(default=0)
	pelota_velocidad_y = models.FloatField(default=0)	
	jugador1_actualizacion = models.DateTimeField(null=True, blank=True, default=None)
	jugador1_y = models.FloatField(default=0)
	jugador1_velocidad_y = models.FloatField(default=0)	
	jugador2_actualizacion = models.DateTimeField(null=True, blank=True, default=None)
	jugador2_y = models.FloatField(default=0)
	jugador2_velocidad_y = models.FloatField(default=0)
	def setDateTimes(self):
		t = datetime.datetime.now()
		self.pelota_actualizacion = t
		self.jugador1_actualizacion = t
		self.jugador2_actualizacion = t

class Partido_historia(models.Model):
	partido_enJuego_id = models.IntegerField(default=0, unique=True) # para que las conexiones de los dos jugadores no cree dos registros
	jugador1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'ph_user_jugador1')
	jugador2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'ph_user_jugador2')
	jugador1_marcador = models.IntegerField(default=0)	# marcador de puntos
	jugador2_marcador = models.IntegerField(default=0) 
	comienzo = models.DateTimeField(null=True, blank=True, default=None) # comienzo del partido
	fin = models.DateTimeField(null=True, blank=True, default=None) # final del partido


