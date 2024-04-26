"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt #nuevo

from base import views as ba_views
from torneos import views as to_views
from partidos import views as pa_views
from django.conf.urls.static import static

urlpatterns = [
    #path('admin/', admin.site.urls), # ya estaba
    path('', ba_views.home, name='home'),
    path('login', ba_views.user_login, name='login'),
    path('signup', ba_views.user_signup, name='signup'),
    path('logout', ba_views.user_logout, name='logout'),
    path('change_es', ba_views.change_es, name='es'),
    path('change_en', ba_views.change_en, name='en'),
    path('change_fr', ba_views.change_fr, name='fr'),
    path('torneos_inscripcion_list', to_views.torneos_inscripcion_list, name='torneos_inscripcion_list'), 
    path('torneos_inscripcion', to_views.torneos_inscripcion, name='torneos_inscripcion'), 
    path('torneos_admin', to_views.torneos_admin, name='torneos_admin'), 
    path('torneos_delete', to_views.torneos_delete, name='torneos_delete'), 
    path('torneos_edit', to_views.torneos_edit, name='torneos_edit'), 
    path('torneos_mantenimiento', to_views.torneos_mantenimiento, name='torneos_mantenimiento'), # quitar y pasar a home
    path('torneos_info_list', to_views.torneos_info_list, name='torneos_info_list'),
    path("arranque_rapido", pa_views.fun_arranque_rapido, name='arranque_rapido'), 
    path("arranque_torneo", pa_views.fun_arranque_torneo, name='arranque_torneo'), 
    path("aj_keys", csrf_exempt(pa_views.fun_keys)),
    path('aj_status', csrf_exempt(pa_views.fun_status)),
    path('partidos_mlist', pa_views.partidos_mlist, name='partidos_mlist'),
    path('partidos_list', pa_views.partidos_list, name='partidos_list'),
    path('oauth2/login', ba_views.intra_login, name='oauth_login'), 
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# partidos
# views.fun_arranque es la funcion fun_arranque del modulo view
# arranque = url que arranca el partido
# key     = url para comunicacion ajax entre el javascript del navegador y el servidor.
#                el navegador envia las teclas que pulsa el usuario para mover su jugador
# status = url para comunicacion ajax entre el javascript del navegador y el servidor.
#               el navegador pide al servidor el estado del partido (posicion de pelota, jugadores, marcador, etc.).