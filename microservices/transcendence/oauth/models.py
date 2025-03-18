from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta, timezone

# Create your models here.
class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    Adds additional fields for 42 Intra authentication, MFA, and user status tracking.
    """
    
    # User status constants
    STATUS_ACTIVE = 'A'    # User is currently active/online
    STATUS_INACTIVE = 'I'  # User is logged in but inactive
    STATUS_OFFLINE = 'O'   # User is offline
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'active'),
        (STATUS_INACTIVE, 'inactive'),
        (STATUS_OFFLINE, 'offline')
    ]
    
    # 42 Intra integration field
    intra_id = models.BigIntegerField(blank=True, null=True)
    
    # Override password field to make it optional (for OAuth users)
    password = models.CharField(max_length=128, blank=True, null=True)
    
    # User profile avatar with default image
    avatar = models.CharField(max_length=200, blank=True, null=True, default="/media/profile_avatar/default.png")
    
    # Multi-Factor Authentication toggle
    mfa_enabled = models.BooleanField(default=False)
    
    # Disable first and last name fields from AbstractUser
    first_name = None
    last_name = None
    
    # User status tracking
    online = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_OFFLINE)
    last_activity = models.DateTimeField(auto_now=True)
    
    def get_sort_name(self):
        """
        Returns the username for sorting purposes.
        Could be extended to support more complex name sorting.
        
        Returns:
            str: The user's username
        """
        return self.username