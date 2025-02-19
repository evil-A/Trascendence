from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    
    intra_id = models.BigIntegerField(blank=True, null=True)
    password = models.CharField(max_length=128 , blank=True, null=True)
    avatar = models.CharField(max_length=200, blank=True, null=True, default = "https://profile.intra.42.fr/images/default.png")
    mfa_enabled = models.BooleanField(default=False)
    first_name = None
    last_name = None

    def get_sort_name(self):
        return self.username
    
