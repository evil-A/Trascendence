# Import necessary modules
from datetime import datetime, timedelta, timezone  # For handling date and time operations
from apscheduler.schedulers.background import BackgroundScheduler  # For scheduling background tasks
from oauth.models import User  # User model for authentication
from tournament.models import Tournament  # Tournament model
from tournament.utils import *  # Utility functions for tournament operations

def offline_status_check():
    """
    Check and update user online status based on their last activity.
    - Users active -> inactive after 5 minutes of inactivity
    - Users inactive -> offline after 25 minutes of inactivity
    """
    # Find users who are active but haven't had activity in the last 5 minutes
    to_inactive = User.objects.filter(online = 'A', last_activity__lte = datetime.now(timezone.utc) - timedelta(minutes=5))
    
    # Find users who are inactive but haven't had activity in the last 25 minutes
    to_offline = User.objects.filter(online = 'I', last_activity__lte = datetime.now(timezone.utc) - timedelta(minutes=25))
    
    # Update status of users from active to inactive
    for user in to_inactive:
        print(user, "declared inactive")
        user.online = 'I'
        user.save()
    
    # Update status of users from inactive to offline
    for user in to_offline:
        print(user, "declared offline")
        user.online = 'O'
        user.save()

def tournament_start():
    """
    Start pending tournaments if conditions are met:
    - Tournament status is Pending
    - Start time has passed (by at least 1 minute)
    - Even number of players
    """
    # Find the first pending tournament whose scheduled start time has passed
    tournament = Tournament.objects.filter(status = 'P', date__lte = datetime.now(timezone.utc) - timedelta(minutes=1)).first()
    
    # Only start tournament if there's an even number of players
    # Note: There's a commented condition that also required more than 2 players
    if tournament and not tournament.players % 2:# and tournament.players > 2:
        ##Send message to participants through chat.
        # Set the number of rounds (minimum 4)
        tournament.rounds = max(tournament.players / 2, 4)
        tournament.current_round = 1
        tournament.status = 'A'  # Set status to Active
        tournament.pair_players()  # Match players for the tournament
        tournament.save()

def tournament_advance():
    """
    Advance active tournaments to the next round if they've been active for at least 30 minutes.
    """
    # Find active tournaments that started at least 30 minutes ago
    tournaments = Tournament.objects.filter(status = 'A', date__lte = datetime.now(timezone.utc) - timedelta(minutes = 30))
    
    # Update each tournament's games and possibly advance to next round
    for tournament in tournaments:
        update_tournament_games(tournament, True)  # True flag likely forces updates

def start():
    """
    Initialize and start the background scheduler with all required periodic tasks.
    """
    # Create a background scheduler
    scheduler = BackgroundScheduler()
    
    # Add periodic jobs:
    # 1. Check user online status every minute
    scheduler.add_job(offline_status_check, 'interval', minutes=1)
    
    # 2. Check for tournaments to start every minute
    scheduler.add_job(tournament_start, 'interval', minutes = 1)
    
    # 3. Check for tournaments to advance every 10 minutes
    scheduler.add_job(tournament_advance, 'interval', minutes=10)
    
    # Start the scheduler
    scheduler.start()