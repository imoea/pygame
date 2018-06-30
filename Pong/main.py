#!/usr/bin/env python
""" a PONG clone by Joshua Wong """

from init import *
from pygame.locals import *
import pygame
import random
import sys
import time


class Ball(pygame.Rect):
	""" ball object """
	def __init__(self, round_num):
		""" initialise starting position """
		self.left = HALFWINWIDTH - BALLSIZE/2  # Rect left
		self.top = random.randint(0, WINHEIGHT - BALLSIZE)  # Rect top
		self.width = BALLSIZE
		self.height = BALLSIZE

		self.vy = random.choice([-1, 1]) * random.randint(MINBALLVELY, MAXBALLVELY)
		if round_num % 2 == 0:  # starts towards P2
			self.vx = MINBALLVELX**2 / abs(self.vy)
		else:  # starts towards P1
			self.vx = -MINBALLVELX**2 / abs(self.vy)

	def update(self, P1, P2):
		""" resolve collisions and move the ball """
		if self.top <= 0 or self.bottom >= WINHEIGHT:
			self.vy = -self.vy  # change vertical velocity
		elif self.colliderect(P1):
			self.vy += P1.vy  # adjust horizontal and vertical velocity
			self.vx = MINBALLVELX**2 / abs(self.vy) if self.vy != 0 else MAXBALLVELX
			self.left = P1.right  # prevent overlap
		elif self.colliderect(P2):
			self.vy += P2.vy  # adjust horizontal and vertical velocity
			self.vx = -MINBALLVELX**2 / abs(self.vy) if self.vy != 0 else MAXBALLVELX
			self.right = P2.left  # prevent overlap

		if abs(self.vx) < MINBALLVELX:  # make sure the game doesn't slow down
			self.vx = self.vx / abs(self.vx) * MINBALLVELX
		if abs(self.vx) > MAXBALLVELX:  # make sure the ball's x velocity doesn't go crazy
			self.vx = self.vx / abs(self.vx) * MAXBALLVELX
		if abs(self.vy) > MAXBALLVELY:  # make sure the ball's y velocity doesn't go crazy
			self.vy = self.vy / abs(self.vy) * MAXBALLVELY

		self.move_ip(self.vx, self.vy)  # move the ball


class Player(pygame.Rect):
	""" player object """
	def __init__(self, player):
		""" initialise starting position """
		self.player = player
		if player == 1:
			self.left = XMARGIN  # left side
		elif player == 2:
			self.left = WINWIDTH - XMARGIN - PLAYERWIDTH  # right side
		self.top = HALFWINHEIGHT - PLAYERHEIGHT/2  # centre
		self.width = PLAYERWIDTH
		self.height = PLAYERHEIGHT
		self.vy = 0  # not moving
		self.score = 0

	def update(self, move_up, move_down):
		""" move the player given inputs """
		if (move_up and move_down) or not (move_up or move_down):  # gridlock or no movement
			self.vy = 0
		else:
			if move_up:
				self.vy -= PLAYERACCELY
				if self.vy < -MAXPLAYERVELY:  # maximum velocity
					self.vy = -MAXPLAYERVELY
			elif move_down:
				self.vy += PLAYERACCELY
				if self.vy > MAXPLAYERVELY:  # maximum velocity
					self.vy = MAXPLAYERVELY

		self.move_ip(0, self.vy)  # move the player

		if self.top <= 0:  # hit the top
			self.top = 0  # keep the player in the window
		elif self.bottom >= WINHEIGHT:  # hit the bottom
			self.bottom = WINHEIGHT  # keep the player in the window

	def lose(self, ball):
		""" check if the player loses the round """
		if ball.right <= 0:
			if self.player == 1:
				return True
			elif self.player == 2:
				self.score += 1
		elif ball.left >= WINWIDTH:
			if self.player == 1:
				self.score += 1
			elif self.player == 2:
				return True
		return False


class Text(pygame.Rect):
	""" text object """
	def __init__(self, text, size, color, bg=None):
		""" initialise text variables """
		self.font = pygame.font.Font(FONT, size)
		self.Surf = self.font.render(text, True, color, bg)
		super().__init__(self.Surf.get_rect())


class EventHandler(object):
	""" event handler object """
	def __init__(self):
		""" initialise input variables """
		self.P1MOVEUP = False
		self.P1MOVEDOWN = False
		self.P2MOVEUP = False
		self.P2MOVEDOWN = False

	def terminate(self):
		""" quit """
		pygame.quit()
		sys.exit()

	def checkForQuit(self):
		""" check for QUIT events """
		for __ in pygame.event.get(QUIT):
			self.terminate()
		for event in pygame.event.get(KEYUP):
			if event.key == K_ESCAPE:
				self.terminate()
			pygame.event.post(event)

	def getEvent(self, event_type, key=None):
		""" check for specific event """
		for event in pygame.event.get(event_type):
			if key is not None and event.key == key:
				return True
			elif key == None:
				pygame.event.clear()
				return True
			pygame.event.post(event)
		return False

	def getEvents(self):
		""" event handling """
		for event in pygame.event.get():
			if event.type == KEYDOWN:
				if event.key == K_w:  # P1 move
					self.P1MOVEUP = True
				if event.key == K_s:
					self.P1MOVEDOWN = True

				if event.key == K_UP:  # P2 move
					self.P2MOVEUP = True
				if event.key == K_DOWN:
					self.P2MOVEDOWN = True

			elif event.type == KEYUP:
				if event.key == K_w:  # P1 stop moving
					self.P1MOVEUP = False
				if event.key == K_s:
					self.P1MOVEDOWN = False

				if event.key == K_UP:  # P2 stop moving
					self.P2MOVEUP = False
				if event.key == K_DOWN:
					self.P2MOVEDOWN = False


class Display(object):
	""" display object """
	def __init__(self, input):
		""" initialise display environment """
		self.FPSClock = pygame.time.Clock()
		self.Surf = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
		self.Input = input
		
	def displayScores(self, P1_score, P2_score):
		""" display scores """
		P1_score = Text(str(P1_score).zfill(2), BIGFONTSIZE, FGCOLOR)
		P1_score.center = (HALFWINWIDTH/2, YMARGIN)
		P2_score = Text(str(P2_score).zfill(2), BIGFONTSIZE, FGCOLOR)
		P2_score.center = (HALFWINWIDTH/2*3, YMARGIN)

		self.Surf.blit(P1_score.Surf, P1_score)
		self.Surf.blit(P2_score.Surf, P2_score)

	def titleScreen(self):
		""" display title screen """
		self.Surf.fill(BGCOLOR)

		title = Text("PONG", HUGEFONTSIZE, FGCOLOR)
		title.center = (HALFWINWIDTH, HALFWINHEIGHT - YMARGIN)
		start = Text("Hit 'Enter' to start.", SMALLFONTSIZE, FGCOLOR)
		start.center = (HALFWINWIDTH, HALFWINHEIGHT + YMARGIN)

		self.Surf.blit(title.Surf, title)
		self.Surf.blit(start.Surf, start)
		pygame.display.update()

		while True:
			self.Input.checkForQuit()
			if self.Input.getEvent(KEYUP, K_RETURN):
				pygame.event.clear()
				return
			self.FPSClock.tick(FPS)
			
	def currentGameState(self, P1, P2, ball):
		""" display current game state """
		self.Surf.fill(BGCOLOR)  # draw the background
		for i in range(int(WINHEIGHT/20)):  # draw dotted line in the middle
			pygame.draw.line(self.Surf, FGCOLOR, (HALFWINWIDTH, i*20+5), (HALFWINWIDTH, i*20+15), 2)
		self.Surf.fill(FGCOLOR, P1)  # draw P1
		self.Surf.fill(FGCOLOR, P2)  # draw P2
		self.Surf.fill(FGCOLOR, ball)  # draw the ball
		self.displayScores(P1.score, P2.score)
		pygame.display.update()

	def gameOverScreen(self, P1_score, P2_score):
		""" display game over screen """
		pygame.event.clear()
		self.Surf.fill(BGCOLOR)

		for i in range(int(WINHEIGHT/20)):  # draw dotted line in the middle
			pygame.draw.line(self.Surf, FGCOLOR, (HALFWINWIDTH, i*20+5), (HALFWINWIDTH, i*20+15), 2)

		self.displayScores(P1_score, P2_score)

		win = Text("WIN", HUGEFONTSIZE, FGCOLOR)
		lose = Text("LOSE", HUGEFONTSIZE, FGCOLOR)
		cont = Text("Hit 'Enter' to continue.", SMALLFONTSIZE, FGCOLOR, BGCOLOR)
		cont.center = (HALFWINWIDTH, HALFWINHEIGHT + YMARGIN)

		if P1_score > P2_score:
			win.center = (HALFWINWIDTH/2, HALFWINHEIGHT - YMARGIN)
			lose.center = (HALFWINWIDTH/2*3, HALFWINHEIGHT - YMARGIN)
		else:
			win.center = (HALFWINWIDTH/2*3, HALFWINHEIGHT - YMARGIN)
			lose.center = (HALFWINWIDTH/2, HALFWINHEIGHT - YMARGIN)

		self.Surf.blit(win.Surf, win)
		self.Surf.blit(lose.Surf, lose)
		self.Surf.blit(cont.Surf, cont)

		pygame.display.update()

		while True:
			self.Input.checkForQuit()
			if self.Input.getEvent(KEYUP, K_RETURN):
				pygame.event.clear()
				return
			self.FPSClock.tick(FPS)


class Game(object):
	""" game object """
	def __init__(self):
		""" initialise game variables """
		self.max_points = MAXPOINTS
		self.shame_limit = SHAMELIMIT
		self.P1 = Player(1)
		self.P2 = Player(2)
		self.Input = EventHandler()
		self.Display = Display(self.Input)

	def startRound(self, i):
		""" start a round of pong """
		self.Ball = Ball(i)
		self.start_time = time.time()

		while True:  # round loop
			self.Input.checkForQuit()
			self.Input.getEvents()

			self.P1.update(self.Input.P1MOVEUP, self.Input.P1MOVEDOWN)  # move P1
			self.P2.update(self.Input.P2MOVEUP, self.Input.P2MOVEDOWN)  # move P2
			if time.time() - self.start_time > 2:
				self.Ball.update(self.P1, self.P2)  # move the ball

			self.Display.currentGameState(self.P1, self.P2, self.Ball)

			P1_lost = self.P1.lose(self.Ball)
			P2_lost = self.P2.lose(self.Ball)
			if P1_lost or P2_lost:  # end the round if someone loses
				return

			self.Display.FPSClock.tick(FPS)

	def run(self):
		""" run this game instance """
		self.Display.titleScreen()

		for i in range(self.max_points * 2):  # play a max of (MAXPOINTS * 2 - 1) rounds
			self.startRound(i)
			if abs(self.P1.score - self.P2.score) >= self.shame_limit or \
			   self.max_points in (self.P1.score, self.P2.score):  # max score or shame limit reached
				break  # end game

		self.Display.gameOverScreen(self.P1.score, self.P2.score)


def main():
	pygame.init()
	pygame.display.set_caption('PONG')

	while True:  # main game loop
		game = Game()
		game.run()


if __name__ == '__main__':
	main()
