from django.urls import re_path
from .consumers import *
from tournament.consumers import *

websocket_urlpatterns = [
    re_path('ws/waiting-room/', WaitingRoom.as_asgi()),
    re_path(r'ws/game/(?P<game_id>[0-9-]+)/$', GameConsumer.as_asgi()),
    re_path('ws/tournament-room/(?P<tournament_id>\w+)', TournamentRoom.as_asgi()),
]