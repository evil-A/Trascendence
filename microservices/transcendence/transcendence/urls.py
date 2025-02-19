from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from oauth import views
from chat.routing import websocket_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.render_site, name='base'),
    path('oauth2/', include('oauth.urls')),
    path('chat/', include('chat.urls')),
] + websocket_urlpatterns
