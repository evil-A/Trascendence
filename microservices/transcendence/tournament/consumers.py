import json
from asgiref.sync import sync_to_async, async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from oauth.utils import jwtManager
from .models import Tournament, Standing
from game.models import Game
from game.views import remote_game
from .utils import *


waitlists = {} #  tournamient_id: [connected_staindings, ]
class TournamentRoom(AsyncWebsocketConsumer):
    async def connect(self):
        self.tournament_id = self.scope["url_route"]["kwargs"]["tournament_id"]
        self.tournament = await sync_to_async(Tournament.objects.get)(id = self.tournament_id)
        try:
            headers = dict(self.scope['headers'])
            jwt_code = headers[b'cookie'].decode('utf-8').split('jwt=')[1]
            manager = jwtManager()
            self.user = await sync_to_async(manager.validate_token)(jwt_code)
            if self.user is None:
                raise ValueError
        except Exception as e:
            await self.close(code=4000)
            return
        self.participant = await sync_to_async(self.tournament.is_participant)(self.user)
        if not self.participant or self.participant.played_matches == self.tournament.current_round: #If not a player // oponent timed out
            await self.send(json.dumps({'type': 'timeout'}))
            await self.disconnect(code=4000)
            return
        await self.accept()
        await self.match_maker()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data == 'timeout':
            await sync_to_async(self.absent_player)()
            await self.send(json.dumps({'type': 'timeout'}))
            await self.disconnect(4000)


    async def disconnect(self, close_code = 1000):
        try:
            waitlists[self.tournament_id].remove(self)
        except Exception as e:
            pass
    
    async def start_match(self, oponent):
        game = await sync_to_async(Game.objects.create)(
            user1= self.user, 
            user2= oponent.get_user(),
            tournament = self.tournament)
        response1 = (await sync_to_async(remote_game)(None, game, self.user)).content.decode('utf-8')
        response2 = (await sync_to_async(remote_game)(None, game, oponent.get_user())).content.decode('utf-8')
        data = {
            'type': 'load',
            'html': response1
        }
        await self.send(text_data = json.dumps(data)) 
        data['html'] = response2
        await oponent.send(text_data = json.dumps(data))
        await self.close()
        await oponent.close()
        waitlists[self.tournament_id].remove(oponent)
    
    async def match_maker(self):
        match = await sync_to_async(self.tournament.next_match)(self.participant)
        against = [i for i in match if i != self.participant][0]
        wait = waitlists.get(self.tournament_id, [])
        for oponent in wait:
            if oponent.get_participant() == against:
                await self.start_match(oponent)
                return
        wait.append(self)
        waitlists[self.tournament_id] = wait
    
    def absent_player(self):
        match = self.tournament.next_match(self.participant)
        oponent = [i for i in match if i != self.participant][0]
        
        print(oponent)
        self.participant.played_matches += 1
        self.participant.score += 1
        self.participant.save()
        oponent.played_matches += 1
        oponent.save()
        update_tournament_games(self.tournament)

    def get_participant(self):
        return self.participant

    def get_user(self):
        return self.user


