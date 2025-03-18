from .models import Standing

def update_tournament_games(tournament, force = False):
    if force: #Finishes the round avoids double absent games stucked.
        standings = tournament.get_standings()
        for standing in standings:
            if standing.played_matches < tournament.current_round:
                standing.played_matches = tournament.current_round
                standing.save()
    finished_players = Standing.objects.filter(tournament = tournament, played_matches = tournament.current_round).count()
    print(finished_players)
    if finished_players == tournament.players:
        tournament.current_round += 1
        tournament.pair_players()
    if tournament.current_round > tournament.rounds:
        tournament.status = 'F'
    tournament.save()