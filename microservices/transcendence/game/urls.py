from django.urls import path
from game import views

urlpatterns = [
    path('ai', views.ai_game, name='ai'),
    path('local/', views.local_game, name='local'),
    path('local/save', views.local_save, name='ai_save'),
    path('wait/', views.wait, name='wait'),
    path('history/', views.game_history, name='game_history'),
    path('jwt/', views.keep_token, name='token'),
]