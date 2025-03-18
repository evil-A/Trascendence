from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from oauth import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.render_site, name='base'),
    path('oauth2/', include('oauth.urls')),
    path('game/', include('game.urls')),
    path('home/', views.home_view, name='home'),
    path('social/', include('social.urls')),
    path('tournament/', include('tournament.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
