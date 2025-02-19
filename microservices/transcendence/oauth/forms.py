from django import forms
from .models import User
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
import requests
import os

def unique_username(value):
    if User.objects.filter(username = value).count() > 0:
        raise forms.ValidationError("This username already exists")
    token = get_intra_token()
    response = get_intra_user(token, 'login', value)
    if not response.ok:
        raise ValidationError("Unable to verify with 42. Try later")
    if response.ok and response.json():
        raise ValidationError("This username already exists")
    
def unique_email(value):
    if User.objects.filter(email = value).count() > 0:
        raise ValidationError("This email already exists")
    token = get_intra_token()
    response = get_intra_user(token, 'email', value)
    if not response.ok:
        raise ValidationError("Unable to verify with 42. Try later")
    if response.ok and response.json():
        raise ValidationError("This email already exists")

def same_password(form):
    if form.cleaned_data['password'] != form.cleaned_data['repeat_password']:
        form.add_error('password', "Passwords do not coincide")
        form.add_error('repeat_password', "Passwords do not coincide")
        raise ValidationError("Passwords do not coincide")

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs = {'class': "form-control"}),       required = True)
    password = forms.CharField(widget=forms.PasswordInput(attrs = {'class': "form-control"}),   required = True)

class RegisterForm(forms.Form):
    
    username =          forms.CharField(widget=forms.TextInput(attrs = {'class': "form-control"}),      required = True,    validators = [unique_username])
    email =             forms.EmailField(widget=forms.TextInput(attrs = {'class': "form-control"}),     required = True,    validators = [unique_email])
    password =          forms.CharField(widget=forms.PasswordInput(attrs = {'class': "form-control"}),  required = True)
    repeat_password =   forms.CharField(widget=forms.PasswordInput(attrs = {'class': "form-control"}),  required = True,    label="Repeat Password")
    mfa =               forms.BooleanField(                                                             required = False,   label = "2FA")

    def clean(self):
        cleaned_data = super().clean()
        try:
            same_password(self)
        except:
            self.non_field_errors = []
        return cleaned_data

class MfaForm(forms.Form):
    code    = forms.CharField(required = True)
    user    = forms.IntegerField(widget=forms.HiddenInput(), label = "")

def get_intra_token():
    data = {
        "client_id": os.getenv('UID'),
        "client_secret": os.getenv('SECRET'),
        "grant_type": "client_credentials",
    }
    response = requests.post("https://api.intra.42.fr/oauth/token", data = data).json()
    return response.get('access_token', '')

def get_intra_user(token, field, value) -> dict:
    headers = {
        'Authorization': f'Bearer {token}'
    }
    url = "https://api.intra.42.fr/v2/users" + "?filter[" + field + "]=" + value
    response = requests.get(url, headers=headers)
    return response
