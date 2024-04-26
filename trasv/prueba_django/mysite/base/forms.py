# coding=utf-8

from django import forms 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Form de Django
class SignupForm(UserCreationForm):
    class Meta:
        model = User 
        fields = ['username', 'password1', 'password2']

# Form del programa
class LoginForm(forms.Form):
    username = forms.CharField(label=_('User name')) # label='Nombre de usuario'
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput) # label='Contraseña'

