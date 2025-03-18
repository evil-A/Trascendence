from django.db import models
from oauth.models import User

# Create your models here.

class Friendship(models.Model):
    STATUS_PENDING = 'P'
    STATUS_ACCEPTED = 'A'
    STATUS_REJECTED = 'R'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'pending'),
        (STATUS_ACCEPTED, 'accepted'),
    ]
    
    user_from = models.ForeignKey(User, on_delete = models.CASCADE, blank = False, related_name = '+')
    user_to = models.ForeignKey(User, on_delete = models.CASCADE, blank = False, related_name = '+')
    status = models.CharField(max_length = 1, choices = STATUS_CHOICES, default=STATUS_PENDING)

class Ban(models.Model):
    user_from = models.ForeignKey(User, on_delete = models.CASCADE, blank = False, related_name = '+')
    user_to = models.ForeignKey(User, on_delete = models.CASCADE, blank = False, related_name = '+')
