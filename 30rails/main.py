#!/usr/bin/env python
""" a 30 RAILS clone by Joshua Wong """

from pygame.locals import *
import copy
import pygame
import random
import sys
import time


WIN_WIDTH = 800
WIN_HEIGHT = 600

BLACK = (0, 0, 0)
GRAY = (64, 64, 64)
WHITE = (255, 255, 255)
RED = (255, 0, 0)


class Board(object):
    """ board class """
    __slots__ = ('xy', 'h', 'w')

    def __init__(self, xy, hw):
        self.xy = xy
        (self.h, self.w) = hw


class Text(pygame.Rect):
    """ text class """
    __slots__ = ('font', 'fg', 'bg', 'surface')
    
    def __init__(self, text, size, xy, fg, bg=None):
        self.font = pygame.font.Font(FONT, size)
        (self.fg, self.bg) = (fg, bg)  # foreground and background colours
        self.surface = self.font.render(text, False, fg, bg)
        super().__init__(self.surface.get_rect())
        self.center = xy  # position of the centre of the text

    def update(self, text):
        center = self.center
        self.surface = self.font.render(text, False, self.fg, self.bg)
        self.width = self.surface.get_rect().width
        self.center = center


class Gui(object):
    """ gui class """
    __slots__ = ('mousexy', 'mousebutton', 'texts', 'r')
    
    def __init__(self):
        self.mousexy = (0, 0)
        self.mousebutton = 0
        self.texts = []
        self.r = 5

    def update(self, events):
        self.mousexy = events.mousexy
        self.mousebutton = events.mousebutton

        if self.mousebutton == 4:
            self.r = min(self.r + 1, 50)
        if self.mousebutton == 5:
            self.r = max(self.r - 1, 1)

    def render(self, console):
        pygame.draw.circle(console, WHITE, self.mousexy, self.r)

        for text in self.texts:
            console.blit(text.surface, text)


class EventHandler():
    """ event handling class """
    __slots__ = ('mousexy', 'mousebutton')
    
    def __init__(self):
        self.mousexy = (0, 0)
        self.mousebutton = 0

    def get_events(self):
        self.reset_events()
        event = pygame.event.wait()

        if event.type == QUIT or \
                (event.type == KEYUP and event.key == K_ESCAPE):
            pygame.quit()
            sys.exit()

        elif event.type == MOUSEBUTTONUP:
            self.mousexy = event.pos
            self.mousebutton = event.button

        elif event.type == MOUSEMOTION:
            self.mousexy = event.pos

    def reset_events(self):
        self.mousebutton = 0


class Engine(object):
    """ game engine class """
    __slots__ = ('console', 'event_handler', 'gui', 'state', 'board')
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('30 Rails')
        self.console = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.event_handler = EventHandler()
        self.gui = Gui()
        
    def init(self):
        """ initialises a new game """
        pass
        
    def update(self):
        self.event_handler.get_events()
        self.gui.update(self.event_handler)
        
    def render(self):
        self.console.fill(BLACK)
        self.gui.render(self.console)
        pygame.display.update()


if __name__ == '__main__':
    engine = Engine()

    while True:
        engine.update()
        engine.render()

