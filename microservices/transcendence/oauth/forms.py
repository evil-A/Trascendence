from django import forms
from .models import User
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
import requests
import os

def unique_username(value, user = None):
    if User.objects.filter(username = value).count() > 0:
        raise forms.ValidationError("This username already exists")
    token = get_intra_token()
    response = get_intra_user(token, 'login', value)
    if response:
        raise ValidationError("This username already exists")
    
def unique_email(value, user = None):
    if User.objects.filter(email = value).count() > 0:
        raise ValidationError("This email already exists")
    token = get_intra_token()
    response = get_intra_user(token, 'email', value)
    if response:
        raise ValidationError("This email already exists")

def same_password(form):
    if form.cleaned_data.get('password') != form.cleaned_data.get('repeat_password'):
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

class UserEditionForm(forms.Form):
    username = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}), required = True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control'}), required = True)
    avatar = forms.ImageField(label = 'Photo', required = False)
    mfa_enabled = forms.BooleanField(label = "2FA", required = False)
    password = forms.CharField(widget=forms.PasswordInput(attrs = {'class': "form-control"}), label="New Password", required = False)
    repeat_password = forms.CharField(widget=forms.PasswordInput(attrs = {'class': "form-control"}), label="Repeat Password", required = False)


    def clean(self, user = None):
        cleaned_data = super().clean()
        if user is not None:
            username_user = User.objects.filter(username = cleaned_data['username']).first()
            email_user = User.objects.filter(email = cleaned_data['email']).first()
            try:
                token = get_intra_token()
                intra_users = get_intra_user(token, 'login', cleaned_data['username']) 
                intra_username_user = int(intra_users[0].get('id')) if intra_users != [] else None
                intra_users = get_intra_user(token, 'email', cleaned_data['email'])
                intra_email_user = int(intra_users[0].get('id')) if intra_users != [] else None
                if (username_user is not None and username_user != user) or (intra_username_user is not None and intra_username_user != user.intra_id):
                    self.add_error('username', "This username already exists")
                    raise ValidationError("This username already exists")
                if (email_user is not None and email_user != user) or (intra_email_user is not None and intra_email_user != user.intra_id):
                    self.add_error('email', "This email already exists")
                    raise ValidationError("This email already exists")
                if cleaned_data['password'] is not None:
                    same_password(self)
            except ConnectionError as e:
                self.non_field_errors = [str(e)]
        return cleaned_data



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
    if not response.ok:
        raise ConnectionError("Unable to verify with 42. Try later")
    return response.json()
