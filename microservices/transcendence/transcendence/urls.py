from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from oauth import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.render_site, name='base'),
    path('oauth2/', include('oauth.urls')),
]
