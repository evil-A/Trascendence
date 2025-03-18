from django.db import models  # Import Django's model framework
from oauth.models import User  # Import User model from oauth app
from tournament.models import Tournament  # Import Tournament model

# Create your models here.
class Game(models.Model):
   # User who created/initiated the game (required)
   user1 = models.ForeignKey(User,             on_delete = models.CASCADE, blank = False,              related_name = '+')
   
   # Second user/opponent (optional - could be null for AI games)
   user2 = models.ForeignKey(User,             on_delete = models.CASCADE, blank = True, null=True,    related_name = '+')
   
   # Optional tournament this game belongs to
   tournament = models.ForeignKey(Tournament,  on_delete = models.CASCADE, blank = True, null = True,  related_name = '+')
   
   # Score for user1 (defaults to 0)
   score1 = models.IntegerField(default = 0, blank = False)
   
   # Score for user2 (defaults to 0)
   score2 = models.IntegerField(default = 0, blank = False)
   
   # Timestamp when the game was created
   date = models.DateTimeField(auto_now_add = True)