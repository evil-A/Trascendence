from django.shortcuts import render, redirect  # Django functions for rendering templates and redirecting
from django.http import HttpRequest, HttpResponse, JsonResponse  # Django HTTP response classes
from .utils import *  # Import all utilities from the current app
from oauth.utils import jwtManager, jwt_login_required, jwt_refresh  # JWT authentication utilities
from oauth.views import profile_view  # Import the profile view function
from social import utils as social_utils  # Social utilities imported with alias
from django.db.models import Q, F  # Django query expressions
from .models import Game  # Game model from current app
from tournament.models import Tournament  # Tournament model
import json  # JSON handling library

# Create your views here.
@jwt_refresh  # Refreshes JWT token
@jwt_login_required  # Requires valid JWT authentication
def ai_game(request):
    # Renders the game template for AI opponent mode
    response = render(request, "game.html", context = {'user1': request.user})
    # Set cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    # HTMX trigger for client-side events after page swap
    response['HX-Trigger-After-Swap'] = 'game-event'
    return response

@jwt_refresh  # Refreshes JWT token
@jwt_login_required  # Requires valid JWT authentication
def local_game(request):
    # Renders the game template for local multiplayer mode
    response = render(request, "game.html", context = {'user1': request.user, 'local': True})
    # Set cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    # HTMX trigger for client-side events after page swap
    response['HX-Trigger-After-Swap'] = 'game-event'
    return response

def remote_game(request, game, user):
    # Renders the game template for remote multiplayer mode
    context = {
        "room_id": game.id,
        "user1": game.user1,
        "user2": game.user2,
        "user": user,
        "game": game
    }
    return render(request, 'game.html', context)

@jwt_login_required  # Requires valid JWT authentication
def local_save(request):
    # Saves the results of a local game
    data = json.loads(request.body)
    # Create a new game record with swapped scores (player vs AI)
    Game.objects.create(user1 = request.user, score1 = data.get('score2'), score2 = data.get('score1'))
    # Return to the main content page
    response = render(request, "spa_content.html", context = {'user1': request.user})
    # Prevent URL change in browser history
    response['HX-Push-Url'] = 'false'
    return response

@jwt_refresh  # Refreshes JWT token
@jwt_login_required  # Requires valid JWT authentication
def wait(request):
    # Renders the waiting room template for matchmaking
    return(render(request, 'waiting_room.html'))

@jwt_refresh  # Refreshes JWT token
@jwt_login_required  # Requires valid JWT authentication
def game_history(request):
    # Get user ID from query parameters or use the current user's ID
    user_id = request.GET.get('user', request.user.id)
    # Check if the current user is banned by the requested user
    if social_utils.is_banned(user_id, request.user.id):
        return HttpResponse(status = 401, content="Unauthorized")
    # Query for games where the specified user participated (as user1 or user2)
    game_list = Game.objects.filter(Q(user1__pk = user_id) | Q(user2__pk = user_id)).order_by('-date')
    # Render the game history template
    response =  render(request, 'game_history.html', {'data': game_list})
    # If not an HTMX request, wrap the content in the profile view
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return profile_view(request, content)
    return(response)

@jwt_login_required  # Requires valid JWT authentication
def keep_token(request):
    # Update the tournament's last modified timestamp
    id = request.GET.get('id')
    if id: #The tournament game is active
        Tournament.objects.get(id = id).save()
    # Refresh the JWT token
    manager = jwtManager()
    new_token = manager.refresh_token(request.COOKIES.get('jwt'))
    # Return empty response with new token in cookie
    response = HttpResponse(status = 204)
    response.set_cookie('jwt', new_token)
    return(response)