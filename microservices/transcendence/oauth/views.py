from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.translation import activate
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .utils import mfaValidator, jwtManager, jwt_login_required
from .forms import LoginForm, RegisterForm, MfaForm
from chat.models import ChatMessage
import requests
import os

auth_url_intra = os.getenv("AUTH_URL_INTRA")
UID = os.getenv("UID")
SECRET = os.getenv("SECRET")
MFA_VALIDATORS = dict()

def render_site(request: HttpRequest) -> HttpResponse:
    activate('en')
    print("Rendering base site")
    manager = jwtManager()
    jwt = request.COOKIES.get('jwt')
    user = manager.validate_token(jwt)
    response = render(request, "base.html", context = {'user': user})
    response['HX-Retarget'] = 'root'
    if user:
        new_jwt = manager.refresh_token(jwt)
        response.set_cookie('jwt', new_jwt)  
    return response

@csrf_exempt
def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        print("Procesing login request")
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Autentificar usuario
            user = authenticate(request, username=username, password=password)
            if user is None:
                form.add_error(None, "Invalid Credentials")
                print("Invalid credentials")
                return render(request, 'login.html', {'form': form})

            # Manejo de MFA
            if user.mfa_enabled:
                print(f"MFA enabled for user {user.username}")
                return mfa_form(None, user)

            # Usuario autentificado
            print(f"User {user.username} authenticated succesfully")
            response = render(request, 'spa_content.html', {'user': user})

            # Generar jWT y configurarlo en cookiees
            jwt = jwtManager()
            token = jwt.generate_token(user)
            response.set_cookie('jwt', token, httponly=True, secure=True) # Added Security flaggs

            # HX-Response para Turbo o similar
            response['HX-Retarget'] = '#root'
            return response

    # si no es POST, mostrar el formulario de login
    form = LoginForm()
    return render(request, 'login.html', {'form': form})

def register_view(request: HttpRequest) -> HttpResponse:
    if request is not None and request.method == 'POST':
        form  = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username =      form.cleaned_data['username'],
                password =      form.cleaned_data['password'],
                email =         form.cleaned_data['email'],
                mfa_enabled =   form.cleaned_data['mfa'])
            response = login_view(None)
            return response
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def intra_login(request: HttpRequest) -> HttpResponse:
    print("Redirigiendo al proveedor OAuth")
    return redirect(auth_url_intra)

def intra_login_redirect(request: HttpRequest) -> HttpResponse:
    code = request.GET.get('code')
    if not code:
        print("No code received")
        return redirect("/")
    print(f"Code received: {code}")

    access_token = exchange_code(code)
    if access_token is None:
        print("Failed to obtain acces token")
        return redirect("/")

    user_info = get_user_info(access_token)
    if not user_info:
        print("No user info received")
        return redirect("/")

    user_id = user_info.get('id')
    user_login = user_info.get('login')
    user_email = user_info.get('email')
    images_user = user_info.get('image', {}).get('versions', {}).get('medium')

    user, created = User.objects.get_or_create(
        intra_id = user_id,
        defaults = {
            'username'  : user_login,
            'avatar'    : images_user,
            'email'     : user_email
        }
    )
    if user.mfa_enabled:
        print(f"MFA enabled for user {user.username}")
        return redirect('/oauth2/mfa?id=' + str(user.id) + '&redirect=True')

    print(f"User {user.username} authenticated via OAuth")
    response = redirect('/')
    jwt = jwtManager()
    response.set_cookie('jwt', jwt.generate_token(user))
    response['HX-Retarget'] = '#root'
    response['HX-Redirect'] = '/'
    return response

#@csrf_exempt
def verify_mfa(request) -> HttpResponse:
    print("Verifying MFA code")
    user_id = request.POST.get('user_id')
    user = User.objects.filter(pk = int(user_id)).first()
    validator = MFA_VALIDATORS.get(user_id)

    if validator is None:
        print("Invalid MFA validator")
        return render(request, 'base.html', {'user': None, 'error': 'Invalid credentials'})

    if (validator.verify_code(request)):
        print(f"Invalid MFA validator")
        del MFA_VALIDATORS[user_id]      
        response = render(request, 'base.html', {'user': user})
        jwt = jwtManager()
        response.set_cookie('jwt', jwt.generate_token(user))
    else:
        print("Invalid MFA code")
        response = render(request, 'base.html', {'user': None, 'error': 'Invalid credentials'})

    return response

def exchange_code(code: str) -> str | None:
    print("Exchanging OAuth code for acces token")
    data = {
        "client_id": UID,
        "client_secret": SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8000/oauth2/login/redirect"
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post("https://api.intra.42.fr/oauth/token", data=data, headers=headers)
    if response.ok:
        response_json = response.json()
        return response_json.get('access_token', '')
    print("Failed to exchange code for acces token")
    return None

def get_user_info(access_token: str) -> dict:
    print("Fetching user info from OAuth provider")
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get("https://api.intra.42.fr/v2/me", headers=headers)
    if response.ok:
        return response.json()
    print("No access token")
    return {}

def mfa_form(request = None, user = None, is_redirect = False) -> HttpResponse:
    if request is not None and request.method == 'POST':
        form = MfaForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user']
            code = form.cleaned_data['code']
            
            # Verificar usuario y codigo
            validator = MFA_VALIDATORS.get(str(user_id))
            if ( validator is not None and validator.verify_code(code)):
                del MFA_VALIDATORS[str(user_id)]
                user = User.objects.get(pk=user_id)

                # Generar respuesta y establecer JWT
                response = render(request, 'spa_content.html')
                jwt_manager = jwtManager()
                response.set_cookie('jwt', jwt.generate_token(user), httponly=True, secure=True)
                response['HX-Retarget'] = '#root'
                response['HX-Redirect'] = '/'
                return response

            # Codigo invalido
            form.add_error(None, "Invalid code. Please, restart login process")
            form.fields['code'].disabled = True

        else:
            form.add_error(None, "Invalid code. Please, restart login process")

        # Mostrar formulario de MFA con error
            response = render(request, '2fa.html', {'form': form, 'extend': 'none.html'})
        return response

    # GET o caso inicial
    if request is not None:
        user_id = request.GET.get('id')
        if not user_id:
            return redirect('/')
        is_redirect = request.GET.get('redirect', False)

    # Generar codigo MFA y enviarlo
    validator = mfaValidator()
    MFA_VALIDATORS[str(user.pk)] = validator
    validator.generate_code()
    validator.send_code(user)

    #Configurar formulario inicial
    form = MfaForm(initial={'user': user.id})
    extend_template = 'base.html' if is_redirect else 'none.html'
    response = render(None, '2fa.html', {'form': form, 'extend': extend_template})
    if not redirect:
        response['HX-Retarget'] = '#simpleForm'
    return response

@csrf_exempt
@jwt_login_required
def game_view(request: HttpRequest) -> HttpResponse:
    print("Game view called")
    response = render(request, 'game.html', {'user': request.user})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@csrf_exempt
@jwt_login_required
def ai_game_view(request: HttpRequest) -> HttpResponse:
    print("Game with AI view called")
    response = render(request, 'game_ai.html', {'user': request.user})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response




@csrf_exempt
@jwt_login_required
def tournaments_view(request: HttpRequest) -> HttpResponse:
    print("Tournaments view called")
    response = render(request, 'tournaments.html', {'user': request.user})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@csrf_exempt
@jwt_login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    print("Profile view called")
    response = render(request, 'profile.html', {'user': request.user})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@csrf_exempt
def logout_view(request: HttpRequest) -> HttpResponse:
    response = redirect('/')
    response.delete_cookie('jwt')
    return response
