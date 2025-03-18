from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Q, F
from .models import User
from game.models import Game
from social.models import Friendship
from social import utils as social_utils
from .utils import mfaValidator, jwtManager, jwt_login_required, jwt_refresh
from .forms import LoginForm, RegisterForm, MfaForm, UserEditionForm
from django.core.files.storage import FileSystemStorage
import requests
import os

# OAuth configuration settings from environment variables
auth_url_intra = os.getenv("AUTH_URL_INTRA").replace('localhost', os.getenv('HOST'))
UID = os.getenv("UID")
SECRET = os.getenv("SECRET")
# Dictionary to store MFA validators by user ID
MFA_VALIDATORS = dict()

def render_site(request: HttpRequest) -> HttpResponse:
    """
    Renders the base site template with user context if authenticated.
    Refreshes JWT token if user is authenticated.
    """
    print("Rendering base site")
    manager = jwtManager()
    jwt = request.COOKIES.get('jwt')
    user = manager.validate_token(jwt)
    response = render(request, "base.html", context = {'user': user})
    response['HX-Retarget'] = 'root'
    if user:
        # Refresh JWT token and set in cookie
        new_jwt = manager.refresh_token(jwt)
        response.set_cookie('jwt', new_jwt)  
    return response

@csrf_exempt
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user login authentication.
    If MFA is enabled, redirects to the MFA form.
    Sets JWT token upon successful authentication.
    """
    if request is not None and request.method == 'POST':
        print("Procesing login request")
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = authenticate(request, username=username, password=password)
            except TypeError:
                user = None
        
        if user is None:
            form.add_error(None, "Invalid Credentials")
            print("Invalid credentials")
            return render(request, 'login.html', {'form': form})
        
        # If MFA is enabled, redirect to MFA form
        if user.mfa_enabled:
            print(f"MFA enabled for user {user.username}")
            return mfa_form(None, user)
            
        print(f"User {user.username} authenticated succesfully")
        response = render(request, 'spa_content.html', {'user': user})
        # Generate JWT token and set in cookie
        jwt = jwtManager()
        response.set_cookie('jwt', jwt.generate_token(user))
        response['HX-Retarget'] = '#root'
        return response
    else:
        form = LoginForm()
    
    response = render(request, 'login.html', {'form': form})
    # If not an HTMX request, wrap in base template
    if request is not None and not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return(render(request, 'base.html', {'user': None, 'root_content': content}))
    return response

def register_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user registration.
    Creates a new user and redirects to login on success.
    """
    if request is not None and request.method == 'POST':
        form  = RegisterForm(request.POST)
        if form.is_valid():
            # Create new user with form data
            user = User.objects.create_user(
                username =      form.cleaned_data['username'],
                password =      form.cleaned_data['password'],
                email =         form.cleaned_data['email'],
                mfa_enabled =   form.cleaned_data['mfa'])
            response = login_view(None)
            print(response)
            return response
    else:
        form = RegisterForm()
    
    response = render(request, 'register.html', {'form': form})
    # If not an HTMX request, wrap in base template
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return(render(request, 'base.html', {'user': None, 'root_content': content}))
    return response

def intra_login(request: HttpRequest) -> HttpResponse:
    """
    Redirects to OAuth provider for authentication.
    """
    print("Redirigiendo al proveedor OAuth")
    return redirect(auth_url_intra)

def intra_login_redirect(request: HttpRequest) -> HttpResponse:
    """
    Handles OAuth callback after authorization.
    Exchanges code for access token, fetches user info, and creates/authenticates user.
    """
    code = request.GET.get('code')
    if not code:
        print("No code received")
        return redirect("/")
    print(f"Code received: {code}")
    
    # Exchange code for access token
    access_token = exchange_code(code)
    if access_token is None:
        print("Failed to obtain acces token")
        return redirect("/")
    
    # Get user information from API
    user_info = get_user_info(access_token)
    if not user_info:
        print("No user info received")
        return redirect("/")
    
    # Extract relevant user data
    user_id = user_info.get('id')
    user_login = user_info.get('login')
    user_email = user_info.get('email')
    images_user = user_info.get('image', {}).get('versions', {}).get('medium')
    
    # Get or create user based on intra_id
    user, created = User.objects.get_or_create(
        intra_id = user_id,
        defaults = {
            'username'  : user_login,
            'avatar'    : images_user,
            'email'     : user_email
        }
    )
    
    # If MFA enabled, redirect to MFA verification
    if user.mfa_enabled:
        print(f"MFA enabled for user {user.username}")
        response = mfa_form(request, user, True)
        response['HX-Push-Url'] = '/'
        return response
    
    print(f"User {user.username} authenticated via OAuth")
    response = redirect('/')
    # Generate JWT token and set in cookie
    jwt = jwtManager()
    response.set_cookie('jwt', jwt.generate_token(user))
    response['HX-Retarget'] = '#root'
    response['HX-Redirect'] = '/'
    return response

#@csrf_exempt
def verify_mfa(request) -> HttpResponse:
    """
    Verifies MFA code entered by user.
    Authenticates user if code is valid.
    """
    print("Verifying MFA code")
    user_id = request.POST.get('user_id')
    user = User.objects.filter(pk = int(user_id)).first()
    validator = MFA_VALIDATORS.get(user_id)
    
    if validator is None:
        print("Invalid MFA validator")
        return render(request, 'base.html', {'user': None, 'error': 'Invalid credentials'})
    
    if (validator.verify_code(request)):
        print(f"Invalid MFA validator")
        # Remove validator after successful verification
        del MFA_VALIDATORS[user_id]      
        response = render(request, 'base.html', {'user': user})
        # Generate JWT token and set in cookie
        jwt = jwtManager()
        response.set_cookie('jwt', jwt.generate_token(user))
    else:
        print("Invalid MFA code")
        response = render(request, 'base.html', {'user': None, 'error': 'Invalid credentials'})
    return response

def exchange_code(code: str) -> str | None:
    """
    Exchanges OAuth authorization code for access token.
    Returns access token on success, None on failure.
    """
    print("Exchanging OAuth code for acces token")
    data = {
        "client_id": UID,
        "client_secret": SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://" + os.getenv("HOST") + ":8000/oauth2/login/redirect"
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Make POST request to OAuth token endpoint
    response = requests.post("https://api.intra.42.fr/oauth/token", data=data, headers=headers)
    if response.ok:
        response_json = response.json()
        return response_json.get('access_token', '')
    print("Failed to exchange code for acces token")
    return None

def get_user_info(access_token: str) -> dict:
    """
    Fetches user information from OAuth provider using access token.
    Returns user data on success, empty dict on failure.
    """
    print("Fetching user info from OAuth provider")
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Make GET request to user info endpoint
    response = requests.get("https://api.intra.42.fr/v2/me", headers=headers)
    if response.ok:
        return response.json()
    print("No access token")
    return {}

def mfa_form(request = None, user = None, redirect = False) -> HttpResponse:
    """
    Handles MFA form rendering and verification.
    Generates and sends MFA code for verification.
    Authenticates user if code is valid.
    """
    if request is not None and request.method == 'POST':
        form = MfaForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            code = form.cleaned_data['code']
            validator = MFA_VALIDATORS.get(str(user))
            
            # Verify MFA code
            if ( validator is not None and validator.verify_code(code)):
                # Remove validator after successful verification
                del MFA_VALIDATORS[str(user)]
                response = render(request, 'spa_content.html')
                # Generate JWT token and set in cookie
                jwt = jwtManager()
                response.set_cookie('jwt', jwt.generate_token(User.objects.get(pk = user)))
                response['HX-Retarget'] = '#root'
                response['HX-Redirect'] = '/'
            else:
                # Invalid code handling
                form.add_error(None, "Invalid code. Please, restart login process")
                form.fields['code'].disabled = True
                response = render(request, '2fa.html', {'form': form, 'extend': 'none.html'})
        else:
            form.add_error(None, "Invalid code. Please, restart login process")
            response = render(request, '2fa.html', {'form': form, 'extend': 'none.html'})
        return response
    else:
        # Initial MFA form rendering
        if request is not None:
            if not user:
                user = User.objects.get(pk = int(request.GET.get('id')))
            if not redirect:
                redirect = request.GET.get('redirect')
        
        # Generate and send MFA code
        validator = mfaValidator()
        MFA_VALIDATORS[str(user.pk)] = validator
        validator.generate_code()
        validator.send_code(user)
        
        # Prepare MFA form
        form = MfaForm()
        form.initial['user'] = user.id
        extend = 'base.html' if redirect else 'none.html'
        response = render(None, '2fa.html', {'form': form, 'extend': extend})
        
        # Set HTMX headers for proper rendering
        if not redirect: 
            response['HX-Retarget'] = '#simpleForm'
        response['HX-Push-Url'] = '/'
        return response

@csrf_exempt
@jwt_refresh
@jwt_login_required
def home_view(request: HttpRequest) -> HttpResponse:
    """
    Renders the home page for authenticated users.
    Sets cache control headers to prevent caching.
    """
    response = render(request, 'home.html', {'user': request.user})
    # Prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    # If not an HTMX request, wrap in base template
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return(render(request, 'base.html', {'user': request.user}))
    return response

@jwt_refresh
@jwt_login_required
def profile_view(request: HttpRequest, content = None) -> HttpResponse:
    """
    Renders the user profile page with related statistics.
    Includes game stats, friendship status, and ban status.
    """
    # Get user profile to view (default to current user)
    user = User.objects.get(id = request.GET.get('user', request.user.id))
    
    # Check if current user is banned by profile owner
    if social_utils.is_banned(user.id, request.user.id):
        return HttpResponse(status = 401, content="Unautorized")
    
    # Get game statistics
    games = Game.objects.filter(Q(user1_id = user.id) | Q(user2_id = user.id))
    victory = games.filter(Q(user1_id = user.id) & Q(score1 = 10)).count() + games.filter(Q(user2_id = user.id) & Q(score2 = 10)).count()
    
    # Get friendship count
    friends = Friendship.objects.filter(status = 'A').filter(Q(user_from = user) | Q(user_to = user)).count()
    
    # Prepare context with all relevant data
    context = {
        'user': user,
        'edit': user == request.user,
        'friend': social_utils.is_friend(request.user.id, user.id) | social_utils.is_friend(user.id, request.user.id),
        'canApply': social_utils.can_apply(request.user.id, user.id),
        'banned': social_utils.is_banned(request.user.id, user.id) | social_utils.is_banned(user.id, request.user.id),
        'games': games.count(),
        'victory': victory,
        'defeat': games.count() - victory, 
        'friends': friends,
        'profile_content': content
    }
    
    response = render(request, 'profile.html', context)
    # If not an HTMX request, wrap in base template
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return(render(request, 'base.html', {'main_content': content}))
    return response

@jwt_refresh
@jwt_login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    """
    Handles profile editing form for authenticated users.
    Updates user profile data including avatar upload.
    """
    if request.method == 'POST':
        form = UserEditionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Clean form data and prepare for update
                cleaned_data = form.clean(user = request.user)
                cleaned_data.pop('repeat_password')
                new_password = cleaned_data.pop('password')
                # Remove None values
                cleaned_data = {k: v for k, v in cleaned_data.items() if v is not None}
                
                # Update password if provided
                if new_password != '':
                    request.user.set_password(new_password)
                    request.user.save()
                
                # Handle avatar upload
                if cleaned_data.get('avatar') is not None:
                    # Save avatar file with user ID as filename
                    path = '/app/media/profile_avatar/' + str(request.user.id) + '.' + cleaned_data['avatar'].name.split('.')[-1]
                    with open(path, "wb+") as dest:
                        for chunk in request.FILES['avatar'].chunks():
                            dest.write(chunk)
                        dest.close()
                    # Update avatar path in database
                    cleaned_data['avatar'] = "/media/profile_avatar/" + str(request.user.id) + '.' + cleaned_data['avatar'].name.split('.')[-1]
                
                # Update user data
                User.objects.filter(pk = request.user.id).update(**cleaned_data)
                response = profile_view(request)
                response['HX-ReTarget'] = '#main-content'
                
                # Trigger avatar update if changed
                if cleaned_data.get('avatar') is not None:
                    response['HX-Trigger-After-Swap'] = 'change-photo' 
                print(response.headers)
                return response
            except Exception as e:
                print(e)
                return render(request, 'profile_edit.html', {'form': form})
    else:
        # Prepare initial form data for GET request
        data = {
            'username': request.user.username,
            'email': request.user.email, 
            'mfa_enabled': request.user.mfa_enabled
        }
        form = UserEditionForm(data)
        response = render(request, 'profile_edit.html', {'form': form})
        
        # If not an HTMX request, wrap in profile template
        if not request.headers.get('Hx-Request'):
            content = response.content.decode("utf-8")
            return profile_view(request, content)
        return response

@csrf_exempt
@jwt_login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user logout.
    Updates user online status and removes JWT token.
    """
    response = redirect('/')
    # Update user status to Offline
    request.user.online = 'O'
    request.user.save()
    # Remove JWT token
    response.delete_cookie('jwt')
    return response

@jwt_login_required
def refresh_jwt(request: HttpRequest) -> HttpResponse:
    """
    Refreshes the JWT token for authenticated users.
    Returns empty response with new JWT token in cookie.
    """
    manager = jwtManager()
    new_token = manager.refresh_token(request.COOKIES.get('jwt'))
    response = HttpResponse(status = 204)
    response.set_cookie('jwt', new_token)
    return response