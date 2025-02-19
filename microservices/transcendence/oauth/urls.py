from django.urls import path
from oauth import views

urlpatterns = [
    path('', views.intra_login, name='oauth_login'),
    path('login/', views.login_view, name='login'),
    path('login/redirect/', views.intra_login_redirect, name='intra_login_redirect'),
    path('register/', views.register_view, name='register'),
    path('mfa/', views.mfa_form, name='2fa'),
#####
    path('game/player', views.game_view, name='player_game_view'),
    path('game/ai/', views.ai_game_view, name='ai_game_view'),
#    path('chat/', views.chat_view, name='chat'),
    path('tournaments/', views.tournaments_view, name='tournaments'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]