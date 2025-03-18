from django.urls import path
from tournament import views

urlpatterns = [
    path("", views.tournament_home, name = 'standard'),
    path("leave/", views.leave, name = 'leave'),
    path("join/", views.join, name = 'join'),
    path("wait/", views.wait, name = 'wait'),
]