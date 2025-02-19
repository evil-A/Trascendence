from .models import User
import string
import random
from datetime import datetime, timedelta
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpRequest
import jwt
import os
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

class mfaValidator:
    time = None
    code = None

    def __init__(self):
        self.time = None
        self.code = None

    def generate_code(self) -> str:
        self.code = "".join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=6))
        self.time = datetime.now()
    
    def send_code(self, user):
        subject = "Login attempt"
        body = "An attempt to login in transcendence has taken place.\nEnter this code to confirm: " + self.code
        user.email_user(subject, body)
    
    def verify_code(self, code) -> bool:
        if datetime.now() - self.time < timedelta(minutes=3):
            return(self.code == code)
        return(False)

class jwtManager:
    secret = os.getenv('JWT_SECRET')
    algorithm = os.getenv('JWT_ALGORITHM')

    def __init__(self):
        pass

    def generate_token(self, user) -> str | None:
        payload = {
            'user_id' : user.id,
            'exp' : datetime.timestamp(datetime.now() + timedelta(minutes=30))
        }
        token = jwt.encode(payload, self.secret, algorithm =self.algorithm)
        return token
    
    def validate_token(self, token) -> User | None:
        try:
            token_decoded = jwt.decode(token, self.secret, algorithms = [self.algorithm])
            return User.objects.filter(pk = token_decoded.get('user_id')).first()
        except ExpiredSignatureError:
            print("Token expirado.")
            return None
        except InvalidTokenError:
            print("Token invalido.")
            return None
        except Exception as e:
            print(f"Error desconocido: {e}")
            return None
    
    def refresh_token(self, token) -> str | None:
        try:
            token_decoded = jwt.decode(token, self.secret, algorithms = [self.algorithm])
            if datetime.fromtimestamp(token_decoded.get('exp')) - datetime.now() < timedelta(minutes=5):
                return(self.generate_token(User.objects.get(pk = token_decoded.get('user_id'))))
            return token
        except:
            return None

def jwt_login_required(view_func):
    @wraps(view_func)  # Corregir typo: "view_func"
    def wrapper(request: HttpRequest, *args, **kwargs):
        # Obtener el JWT de las cookies
        jwt = request.COOKIES.get('jwt')
        if jwt is None:
            print("JWT no encontrado en las cookies.")
            return redirect('/login')  # Redirigir si no hay JWT

        # Validar el JWT
        manager = jwtManager()
        user = manager.validate_token(jwt)

        if user is None:
            print("JWT inválido o expirado.")
            return redirect('/login')  # Redirigir si el JWT no es válido

        # Asignar el usuario al request
        request.user = user
        print(f"Usuario autenticado con JWT: {user.username}")

        # Llamar a la vista original
        return view_func(request, *args, **kwargs)

    return wrapper

