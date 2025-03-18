from django.shortcuts import render
from oauth.utils import *
from game.models import Game
from .models import *
from django.db.models import Q, F

# Create your views here.

@jwt_login_required
def tournament_home(request):
    tournament = Tournament.objects.filter(standing__user=request.user, status__in = ['A', 'P']).first() #Playing/Joined tournament
    next_game = None
    participant = None
    if tournament is not None:
        participant = tournament.get_standings().filter(user = request.user).first() #The player is in the tournament
        if participant is not None and participant.played_matches < tournament.current_round:
            next_game= tournament.next_match(participant)
    else:
        tournament = Tournament.objects.filter(standing__user=request.user).order_by('-date').first()
    context = {
        'tournament': tournament,
        'participant': participant,
        'next': next_game
    }
    response = render(request, 'tournaments.html', context)
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return(render(request, 'base.html', {'main_content': content}))
    return response

@jwt_refresh
@jwt_login_required
def leave(request):
    tournament = Tournament.objects.filter(standing__user=request.user, status__in = ['P']).first()
    standings = tournament.get_standings().filter(user = request.user)
    tournament.players -= standings.count()
    if tournament.players:
        tournament.save()
    else:
        tournament.delete()
    standings.delete()
    return(tournament_home(request))

@jwt_refresh
@jwt_login_required
def join(request):
    tournament = Tournament.objects.filter(status__in = ['P']).first()
    if tournament is None:
        tournament = Tournament.objects.create()
    else:
        tournament.players += 1
        tournament.save()
    Standing.objects.create(user = request.user, tournament = tournament)
    return(tournament_home(request))

@jwt_refresh
@jwt_login_required
def wait(request):
    try:
        tournament = Tournament.objects.get(pk = request.GET.get('id'))
        participant = tournament.is_participant(request.user)
        if participant and participant.played_matches < tournament.current_round: #Prevents joining a timed out game.
            return render(request, 'tournament_wait.html',{'tournament': tournament})
        raise ValueError
    except:
        return(tournament_home(request))

