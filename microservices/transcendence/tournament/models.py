from django.db import models
from django.contrib.postgres.fields import ArrayField
from oauth.models import User
import random

# Create your models here.

class Tournament(models.Model):
    STATUS_PENDING = 'P'
    STATUS_ACTIVE = 'A'
    STATUS_FINISHED = 'F'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'pending'),
        (STATUS_ACTIVE, 'started'),
        (STATUS_FINISHED, 'finished'),
    ]
    
    date = models.DateTimeField(auto_now = True)
    players = models.IntegerField(default = 1)
    rounds = models.IntegerField(default = 0)
    pairings = ArrayField(models.IntegerField(default = 0), blank=True, null = True)
    current_round = models.IntegerField(default = 0)
    games = models.IntegerField(default = 0)
    status = models.CharField(choices = STATUS_CHOICES, default=STATUS_PENDING)

    def pair_players(self):
        self.pairings = list(range(self.players))
        random.shuffle(self.pairings)
        self.save()
    
    def get_standings(self):
        standings = Standing.objects.filter(tournament_id = self.id).order_by('-score', '-point_difference', 'played_matches')
        return(standings)

    def next_match(self, participant):
        if self.pairings != []:
            
            standings = Standing.objects.filter(tournament_id = self.id).order_by('id')
            print(standings, self.pairings)
             # Indice de participant
            for idx, standing in enumerate(standings):
                if standing == participant:
                    break
            # Posición del Indice en Pairings
            pair_idx = self.pairings.index(idx)
            if pair_idx % 2:
                match = [standings[self.pairings[pair_idx - 1]], standings[idx]]
            else:
                match = [standings[idx], standings[self.pairings[pair_idx + 1]]]
            return match
        return None
    
    def is_participant(self, participant):
        return self.get_standings().filter(user = participant).first()

class Standing(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, blank=False, related_name='standing')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name='user')
    score = models.IntegerField(default = 0, blank = False, null = False)
    point_difference = models.IntegerField(default = 0, blank = False, null = False)
    played_matches = models.IntegerField(default = 0, blank = False, null = False)
