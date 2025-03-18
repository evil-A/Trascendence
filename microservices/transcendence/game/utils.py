from datetime import datetime as dt  # Import datetime with alias dt
import numpy as np  # Import NumPy for numerical operations
import random  # Import random module for generating random numbers
import json  # Import JSON module for data serialization

# Game constants
BALL_RADIUS = .02  # Defines the ball's radius as a fraction of the game area
PADDLE_HEIGHT = .2  # Defines the paddle height as a fraction of the game area
PADDLE_WIDTH = .02  # Defines the paddle width as a fraction of the game area
PADDLE_SPEED = .02  # Defines how fast paddles can move
BALL_SPEED =.005  # Defines the base ball speed
ASPECT_RATIO = 16/9  # Screen aspect ratio (widescreen)

class GameState:
   def __init__(self):
       # Initialize player paddles at left and right sides of screen
       self.players = [
           {'x': 0,                'y': .5 - PADDLE_HEIGHT/2},  # Left paddle starting position
           {'x': 1 - PADDLE_WIDTH, 'y': .5 - PADDLE_HEIGHT/2}   # Right paddle starting position
       ]
       # Initialize ball in center with velocity set in reset_ball()
       self.ball = {'x': .5, 'y': .5, 'vx': None, 'vy': None}
       self.reset_ball()  # Set initial ball velocity
       self.scores = [0, 0]  # Initial scores for both players
       self.max_score = 10  # Points needed to win the game
       self.directions = [0, 0]  # Paddle movement directions (0=stationary, -1=up, 1=down)
   
   def get_ball(self):
       # Return the ball's current position
       return([self.ball['x'], self.ball['y']])
   
   def get_paddles(self):
       # Return the Y-positions of both paddles
       return([self.players[0]['y'], self.players[1]['y']])
   
   def get_scores(self):
       # Return the current scores
       return(self.scores)
   
   def get_game_state(self):
       # Check if game has ended (someone reached max_score)
       end = int(np.max(self.scores) == self.max_score)
       # Compile all game state data
       data = {
           'end': end,  # 1 if game ended, 0 if still in progress
           'ball': self.get_ball(),  # Ball position
           'paddles': self.get_paddles(),  # Paddle positions
           'scores': self.get_scores()  # Current scores
       }
       return(data)
       
   def reset_ball(self):
       # Reset ball to center of screen
       self.ball['x'] = .5
       self.ball['y'] = .5
       # Random horizontal direction (left or right)
       self.ball['vx'] = np.random.choice([-BALL_SPEED, BALL_SPEED])
       # Random vertical direction (normalized to BALL_SPEED)
       self.ball['vy'] = BALL_SPEED * np.random.uniform(-1,1)
       
   def update_ball(self):
       # Move ball according to its velocity
       self.ball['x'] += self.ball['vx']
       self.ball['y'] += self.ball['vy']
       # Check for collisions
       self.vertical_collisions()  # With top/bottom walls
       self.paddle_collisions()  # With paddles or scoring
   
   def vertical_collisions(self):
       # If ball hits top or bottom wall, reverse its vertical direction
       if not (BALL_RADIUS*ASPECT_RATIO < self.ball['y'] < 1 - BALL_RADIUS*ASPECT_RATIO):
           self.ball['vy'] *= -1
   
   def paddle_collisions(self):
       # Check for collision with left paddle
       if (self.ball['vx'] < 0) & (self.ball['x'] <= BALL_RADIUS + PADDLE_WIDTH):
           if self.players[0]['y'] - BALL_RADIUS <= self.ball['y'] <= self.players[0]['y'] + PADDLE_HEIGHT + BALL_RADIUS:
               # Ball hit the paddle, reverse direction with slight speed increase
               self.ball['vx'] = -self.ball['vx'] + 0.0001
           elif self.ball['x'] < 0:
               # Ball missed the paddle, right player scores
               self.reset_ball()
               self.scores[1] += 1
               
       # Check for collision with right paddle
       if (self.ball['vx'] > 0) & (self.ball['x'] >= 1 - BALL_RADIUS - PADDLE_WIDTH):
           if self.players[1]['y'] - BALL_RADIUS <= self.ball['y'] <= self.players[1]['y'] + PADDLE_HEIGHT + BALL_RADIUS:
               # Ball hit the paddle, reverse direction with slight speed increase
               self.ball['vx'] = -self.ball['vx'] - 0.0001
           elif self.ball['x'] > 1:
               # Ball missed the paddle, left player scores
               self.reset_ball()
               self.scores[0] += 1
   
   def move_paddle(self, paddle, direction):
       # Set the movement direction for a paddle (0=left paddle, 1=right paddle)
       self.directions[paddle] = direction
   
   def update_paddle(self):
       # Update positions of both paddles based on their directions
       for paddle, direction in zip(self.players, self.directions):
           # Calculate new y position
           y = paddle['y'] + PADDLE_SPEED * direction
           # Constrain paddle to remain within game boundaries
           y = min(1- PADDLE_HEIGHT, max(0, y))
           paddle['y'] = y
       # Reset directions to stop paddles after movement
       self.directions = [0,0]
       
   def update_game(self):
       # Update paddles first, then ball position, and return current game state
       self.update_paddle()
       self.update_ball()
       return(self.get_game_state())