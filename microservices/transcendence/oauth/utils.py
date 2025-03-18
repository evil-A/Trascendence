from .models import User
import string
import random
from datetime import datetime, timedelta
from functools import wraps
from django.shortcuts import render
from django.http import HttpRequest
import jwt
import os

class mfaValidator:
    """
    Handles multi-factor authentication (MFA) validation process.
    Generates, sends, and verifies MFA codes.
    """
    time = None
    code = None
    
    def __init__(self):
        """Initialize MFA validator with empty time and code."""
        self.time = None
        self.code = None
        
    def generate_code(self) -> str:
        """
        Generates a random 6-character code for MFA verification.
        Sets the generation timestamp.
        """
        self.code = "".join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=6))
        self.time = datetime.now()
    
    def send_code(self, user):
        """
        Sends the MFA code to the user's email.
        
        Args:
            user: User model instance to send the code to
        """
        subject = "Login attempt"
        body = "An attempt to login in transcendence has taken place.\nEnter this code to confirm: " + self.code
        user.email_user(subject, body)
    
    def verify_code(self, code) -> bool:
        """
        Verifies the MFA code submitted by the user.
        Checks if the code matches and is still valid (within 3 minutes).
        
        Args:
            code: The code submitted by the user
            
        Returns:
            bool: True if code is valid, False otherwise
        """
        if datetime.now() - self.time < timedelta(minutes=3):
            return(self.code == code)
        return(False)


class jwtManager:
    """
    Manages JWT token operations - generation, validation, and refreshing.
    Uses environment variables for secret key and algorithm.
    """
    secret = os.getenv('JWT_SECRET')
    algorithm = os.getenv('JWT_ALGORITHM')
    
    def __init__(self):
        """Initialize JWT manager."""
        pass
    
    def generate_token(self, user) -> str | None:
        """
        Generates a new JWT token for the user.
        Sets expiration to 30 minutes in the future.
        Updates user's online status.
        
        Args:
            user: User model instance for token generation
            
        Returns:
            str: JWT token string or None if generation fails
        """
        payload = {
            'user_id' : user.id,
            'exp' : datetime.timestamp(datetime.now() + timedelta(minutes=30))
        }
        # Set user status to Active
        user.online = 'A'
        user.save()
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token
    
    def validate_token(self, token) -> User | None:
        """
        Validates a JWT token and returns the associated user.
        
        Args:
            token: JWT token string to validate
            
        Returns:
            User: User object if token is valid
            None: If token is invalid or expired
        """
        try:
            token_decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return User.objects.filter(pk=token_decoded.get('user_id')).first()
        except:
            return None
    
    def refresh_token(self, token) -> str | None:
        """
        Refreshes an existing JWT token.
        Decodes existing token, retrieves user, and generates a new token.
        
        Args:
            token: Existing JWT token string
            
        Returns:
            str: New JWT token string
            None: If original token is invalid or refresh fails
        """
        try:
            token_decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return(self.generate_token(User.objects.get(pk=token_decoded.get('user_id'))))
        except:
            return None


def jwt_login_required(view_func):
    """
    Decorator to restrict view access to authenticated users only.
    Validates JWT token from cookies and attaches user to request.
    Redirects to base page if authentication fails.
    
    Args:
        view_func: The view function to be protected
        
    Returns:
        function: Wrapped view function with authentication check
    """
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        # Get JWT from cookies
        jwt_token = request.COOKIES.get('jwt')
        if jwt_token is None:
            # No JWT token found
            response = render(request, "base.html", {'user': None})
            response['HX-Retarget'] = 'body'
            response.delete_cookie('jwt')
            return response
        
        # Validate the JWT token
        manager = jwtManager()
        user = manager.validate_token(jwt_token)
        if user is None:
            print("JWT inválido o expirado.")
            response = render(request, "base.html", {'user': None})  # Redirect if JWT is invalid
            response['HX-Retarget'] = 'body'
            response.delete_cookie('jwt')
            return response
        
        # Attach authenticated user to request
        request.user = user
        print(f"Usuario autenticado con JWT: {user.username}")
        
        # Call the original view function
        return view_func(request, *args, **kwargs)
    return wrapper


def jwt_refresh(view_func):
    """
    Decorator to refresh JWT token on each request.
    Updates user's online status.
    
    Args:
        view_func: The view function to wrap
        
    Returns:
        function: Wrapped view function with token refresh logic
    """
    @wraps(view_func)
    def wrapper(request, *args, **kargs):
        # Get current token from cookies
        token = request.COOKIES.get('jwt')
        manager = jwtManager()
        
        # Execute the view function
        response = view_func(request, *args, **kargs)
        
        # Refresh token and update user status if authenticated
        if (request.user is not None) & (not request.user.is_anonymous):
            response.set_cookie('jwt', manager.refresh_token(token))
            request.user.online = 'A'
            request.user.save()
        return response
    
    return wrapper