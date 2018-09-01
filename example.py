#!/usr/bin/env python
""" pygame template """

from pygame.locals import *
import pygame


WIN_WIDTH = 800
WIN_HEIGHT = 600

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)


class EventHandler():
    """ event handling class """

    def __init__(self):
        """ initialise event variables """
        self.eventtype = None
        self.keypress = None
        self.mousexy = (0, 0)
        self.mousebutton = 0

    def get_events(self):
        """ get mouse and key events """
        self.reset_events()
        event = pygame.event.wait()

        if event.type == QUIT or \
                (event.type == KEYUP and event.key == K_ESCAPE):
            pygame.quit()
            exit()

        elif event.type in {KEYDOWN, KEYUP}:
            self.keypress = event.key

        elif event.type in {MOUSEBUTTONDOWN, MOUSEBUTTONUP}:
            self.mousexy = event.pos
            self.mousebutton = event.button

        elif event.type == MOUSEMOTION:
            self.mousexy = event.pos

        self.eventtype = event.type

    def reset_events(self):
        """ reset any events if necessary """
        self.eventtype = None
        self.keypress = None
        self.mousebutton = 0


class Game():
    """ game class """

    def __init__(self):
        """ initialise the game components """
        pass

    def update(self, events):
        """ update the game components """
        pass

    def render(self, console):
        """ render the game components """
        pass


class Gui():
    """ gui class """

    def __init__(self):
        """ initialise the gui """
        pass

    def update(self, events, game):
        """ update the gui based on events and the game state """
        pass

    def render(self, console):
        """ render the gui """
        pass

    
class Engine():
    """ game engine class """

    def __init__(self):
        """ initialise the game state """
        pygame.init()
        pygame.display.set_caption('Pygame')
        self.console = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.event_handler = EventHandler()
        self.game = Game()
        self.gui = Gui()

    def update(self):
        """ update the game state """
        self.event_handler.get_events()
        self.game.update(self.event_handler)
        self.gui.update(self.event_handler, self.game)

    def render(self):
        """ render the game state """
        self.console.fill(BLACK)
        self.game.render(self.console)
        self.gui.render(self.console)
        pygame.display.update()


if __name__ == '__main__':
    engine = Engine()

    while True:
        engine.update()
        engine.render()
        
