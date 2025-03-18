from django.urls import path
from oauth import views

urlpatterns = [
    path('', views.intra_login, name='oauth_login'),
    path('login/', views.login_view, name='login'),
    path('login/redirect/', views.intra_login_redirect, name='intra_login_redirect'),
    path('register/', views.register_view, name='register'),
    path('mfa/', views.mfa_form, name='2fa'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='profile_edit'),
    path('logout/', views.logout_view, name='logout'),
]