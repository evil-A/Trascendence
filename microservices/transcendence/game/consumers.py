import json  # Standard library for JSON operations
from oauth.utils import jwtManager  # JWT token handling
from channels.generic.websocket import AsyncWebsocketConsumer  # Base class for WebSocket consumers
from social.models import Ban  # Ban model to check for banned users
from asgiref.sync import sync_to_async, async_to_sync  # Utilities for sync/async compatibility
from datetime import datetime  # Date and time utilities
from .models import *  # Import all models from current app
from .views import remote_game  # View function for rendering remote game pages
import numpy as np  # Numerical processing library
import time  # Time-related functions
import asyncio  # Asynchronous I/O library
import threading  # Threading library for concurrent operations
from .utils import GameState  # Game state management class
from tournament.utils import *  # Tournament utilities

# Global variables
waiting_list = []  # List of users waiting for a match
game_states = {}  # Dictionary to store active game states

class WaitingRoom(AsyncWebsocketConsumer):
   async def connect(self):
       # Validate the user via JWT token from cookie
       try:
           headers = dict(self.scope['headers'])
           jwt_code = headers[b'cookie'].decode('utf-8').split('jwt=')[1]
           manager = jwtManager()
           self.user = await sync_to_async(manager.validate_token)(jwt_code)
           if self.user is None:
               raise ValueError
       except Exception as e:
           # Close connection if authentication fails
           await self.close(code=4000)
           return
       # Accept the connection and try to find a match
       await self.accept()
       await self.match_maker()
       
   async def disconnect(self, close_code=1000):
       # Remove user from waiting list when they disconnect
       global waiting_list
       try:
           waiting_list.remove(self)
       except:
           pass
   
   def valid_oponents(self, oponent):
       # Check if users are banned from each other or if it's the same user
       banned = Ban.objects.filter(user_from = self.user, user_to = oponent).count()
       banned += Ban.objects.filter(user_from = oponent, user_to = self.user).count()
       return (not banned) and (self.user != oponent)
   
   def get_user(self):
       # Getter for the user object
       return self.user
   
   async def match_maker(self):
       # Try to find a valid opponent from waiting list
       for oponent in waiting_list:
           oponent_user = oponent.get_user()
           if (await sync_to_async(self.valid_oponents)(oponent_user)):
               await self.start_match(oponent)
               return
       # If no match found, add self to waiting list
       waiting_list.append(self)
   
   async def start_match(self, oponent):
       # Create a new game record in the database
       game = await sync_to_async(Game.objects.create)(user1 = self.user, user2 = oponent.get_user())
       # Generate HTML for both players
       response1 = (await sync_to_async(remote_game)(None, game, self.user)).content.decode('utf-8')
       response2 = (await sync_to_async(remote_game)(None, game, oponent.get_user())).content.decode('utf-8')
       # Send game HTML to first player
       data = {
           'type': 'load',
           'html': response1,
       }
       await self.send(text_data = json.dumps(data))
       # Send game HTML to second player
       data['html'] = response2
       await oponent.send(text_data = json.dumps(data))
       # Close both connections and remove opponent from waiting list
       await self.close()
       await oponent.close()
       waiting_list.remove(oponent)
   
   async def send_message(self, event):
       # Forward channel layer messages to the WebSocket
       await self.send(text_data=json.dumps(event["message"]))    

class GameConsumer(AsyncWebsocketConsumer):
   async def connect(self):
       # Validate the user via JWT token
       try:
           headers = dict(self.scope['headers'])
           jwt_code = headers[b'cookie'].decode('utf-8').split('jwt=')[1]
           manager = jwtManager()
           self.user = await sync_to_async(manager.validate_token)(jwt_code)
           if self.user is None:
               raise ValueError
       except Exception as e:
           await self.close(code=4000)
           
       # Get game ID from URL route and retrieve game object
       game_id = self.scope["url_route"]["kwargs"]["game_id"]
       self.game = await sync_to_async(Game.objects.get)(id = game_id)
       self.tournament = await sync_to_async(lambda: self.game.tournament)()
       
       # Initialize state variables
       self.end = False  # Flag to indicate if game has ended
       self.primary = False  # Flag to indicate if this instance manages game state
       
       # Verify user is a participant in the game
       user1 = await sync_to_async(lambda: self.user == self.game.user1)()
       user2 = await sync_to_async(lambda: self.user == self.game.user2)()
       if not (user1 or user2):
           await self.close(code=4000)
           return
           
       # Set up channel group for this game
       self.group_name = f"game_{game_id}"
       await self.channel_layer.group_add(self.group_name, self.channel_name)
       await self.accept()
       await self.register_player()
   
   async def receive(self, text_data):
       # Handle paddle movement messages from client
       data = json.loads(text_data)
       if data['action'] == 'paddle' and not self.end:
           game_states.get(self.group_name)[0].move_paddle(self.right, data['direction'])
   
   async def disconnect(self, close_code):
       # Handle player disconnection
       try:
           if (game_states.get(self.group_name)) and (not self.end):
               # Send disconnection notification
               self.send(text_data = {'type': 'disconnected'})
               # End the game with a forfeit (other player wins)
               data = {'type': 'game_status'}
               data.update(game_states.get(self.group_name)[0].get_game_state())
               data['end'] = 1
               data['disconnection'] = 1
               data['scores'][int(not self.right)] = 10  # Award max score to opponent
               await self.broadcast_message(data)
           # Remove from channel group
           await self.channel_layer.group_discard(self.group_name, self.channel_name)
       except Exception as e:
           pass
       # Clean up game state if this was the last connection
       if self.end:
           game_states.pop(self.group_name, None)
           
   async def start_game(self, event):
       # Handle game start event
       await self.send(text_data=json.dumps(event))
       # Start game loop if this is the primary instance
       if self.primary: 
           asyncio.ensure_future(self.game_loop())
   
   async def game_status(self, event):
       # Handle game status updates
       if event['end']:
           # If game has ended, update database
           self.end = True
           self.game.score1 = event['scores'][1]
           self.game.score2 = event['scores'][0]
           await sync_to_async(self.game.save)()
           # Update tournament if applicable
           if self.tournament and (self.primary or event.get('disconnection')):
               await sync_to_async(self.update_tournment)()
           event['type'] = 'end_game'
       # Forward status to client
       await self.send(text_data=json.dumps(event))
   
   async def broadcast_message(self, message):
       # Send a message to all connections in the group
       try:
           await self.channel_layer.group_send(self.group_name, message)
       except Exception as e:
           print("Broadcast message error:", message, e)
           
   async def register_player(self):
       # Determine which paddle this player controls and set up game state
       self.right = await sync_to_async(lambda: self.user == self.game.user1)()
       # Initialize game state if this is the first player
       if not game_states.get(self.group_name):
           game_states[self.group_name] = [GameState(), 0]
           self.primary = True
       # Increment player count
       game_states.get(self.group_name)[1] += 1
       # Start game when both players are connected
       if game_states.get(self.group_name)[1] == 2:
           data = {'type': 'start_game'}
           await self.broadcast_message(data)
   
   async def game_loop(self):
       # Main loop for game state updates
       game_state = game_states.get(self.group_name)
       while self.primary and not self.end and game_state:
           start_time = time.monotonic()
           state_object = game_state[0]
           # Update game state and broadcast to players
           data = {'type': 'game_status'}
           data.update(state_object.update_game())
           await self.broadcast_message(data)
           await asyncio.sleep(0)  # Yield to event loop
           game_state = game_states.get(self.group_name)
           
   def update_tournment(self):
       # Update tournament statistics after a game ends
       player1 = self.tournament.is_participant(self.game.user1)
       player2 = self.tournament.is_participant(self.game.user2)
       dif = self.game.score1 - self.game.score2
       
       # Award points based on win/loss
       if dif > 0:
           player1.score += 3
       else: 
           player2.score += 3
           
       # Update player statistics
       player1.point_difference += dif
       player2.point_difference -= dif
       player1.played_matches += 1
       player2.played_matches += 1
       player1.save()
       player2.save()
       
       # Update tournament state
       update_tournament_games(self.tournament)