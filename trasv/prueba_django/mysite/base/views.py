# coding=utf-8

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import UserCreationForm, LoginForm
from general.views import activate_language
from torneos.views import torneo_jugar, proximos_torneos
from django.http import HttpRequest, HttpResponse, JsonResponse

auth_url_intra = "https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-edf92ca8bb6141ed1f1dcffb34c70e77a1a1444edcb36a123784be32e42555e7&redirect_uri=http%3A%2F%2Flocalhost&response_type=code"

def change_en(request):
    request.session['myLanguage'] = 'en'
    return redirect('home')

def change_es(request):
    request.session['myLanguage'] = 'es'
    return redirect('home')

def change_fr(request):
    request.session['myLanguage'] = 'fr'
    return redirect('home')
    
# Create your views here.
# Home page
def home(request):
    activate_language(request)
    jugar = False
    hayProximosTorneos = False
    proximosTorneos = []
    if request.user.is_authenticated:
        res = torneo_jugar(request.user.id)
        jugar = res['ok']
        proximosTorneos = proximos_torneos(request.user.id)
        hayProximosTorneos = (len(proximosTorneos) > 0)
        #print(proximosTorneos)
        #print(jugar)
    context = { 'jugar': jugar, 
                      'proximosTorneos': proximosTorneos, 
                      'hayProximosTorneos': hayProximosTorneos }
    return render(request, 'base/home_t.html', context)

# signup page
def user_signup(request):
    activate_language(request)
    if request.method == 'POST': 
        # fin edición
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        # crear el html para editar (comienzo de edición)
        form = UserCreationForm()
    # crear el html para editar o error en form
    return render(request, 'base/signup_t.html', {'form': form})

# login page
def user_login(request):
    activate_language(request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)    
                return redirect('home')
    else:
        form = LoginForm()
    # crear el html para editar o error en form
    return render(request, 'base/login_t.html', {'form': form})

def intra_login(request: HttpRequest):
    return redirect(auth_url_intra)


# logout page
def user_logout(request):
    activate_language(request)
    logout(request)
    return redirect('home')

