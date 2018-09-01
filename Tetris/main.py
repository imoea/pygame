#!/usr/bin/env python
""" a TETRIS clone by Joshua Wong """

from argparse import ArgumentParser
from pygame.locals import *
import copy
import pygame
import random
import sys
import time

FONT = 'PressStart2P.ttf'
SCALE = 2
WIN_WIDTH = 176
WIN_HEIGHT = 176

BLACK = (0, 0, 0)
GRAY = (64, 64, 64)
WHITE = (255, 255, 255)

MULTIPLIER = {1: 40, 2: 100, 3: 300, 4: 1200}

SHAPES = {'I': [['....', '####', '....', '....'],
                ['..#.', '..#.', '..#.', '..#.']],
          'J': [['...', '###', '..#'],
                ['.#.', '.#.', '##.'],
                ['#..', '###', '...'],
                ['.##', '.#.', '.#.']],
          'L': [['...', '###', '#..'],
                ['##.', '.#.', '.#.'],
                ['..#', '###', '...'],
                ['.#.', '.#.', '.##']],
          'O': [['....', '.##.', '.##.', '....']],
          'S': [['...', '.##', '##.'],
                ['.#.', '.##', '..#']],
          'T': [['...', '###', '.#.'],
                ['.#.', '##.', '.#.'],
                ['.#.', '###', '...'],
                ['.#.', '.##', '.#.']],
          'Z': [['...', '##.', '.##'],
                ['..#', '.##', '.#.']]}


class Piece(object):
    """ tetromino class """
    __slots__ = ('x', 'y', 'shape', 'rotation', 'color')
    
    def __init__(self):
        self.x, self.y = 14, 10  # top left position in blocks
        self.shape = random.choice(list(SHAPES))  # returns a random shape
        self.rotation = 0  # current rotation
        self.color = WHITE  # color

    def get_template(self):
        """ returns the template to render """
        template = SHAPES[self.shape][self.rotation]
        size = list(range(len(template)))
        yield from [(self.x + x, self.y + y)
                    for y in size for x in size if template[y][x] == '#']

    def move(self, x, y):
        self.x += x
        self.y += y

    def rotate(self, rotation):
        self.rotation = (self.rotation + rotation) % len(SHAPES[self.shape])

    def hold(self):
        """ puts the piece in the holding area """
        self.x, self.y = 14, 16
        self.rotation = 0

    def reset(self):
        """ sets the piece to enter by the top """
        self.x, self.y = 3, -3
        self.rotation = 0

    def render(self, console):
        for (x, y) in self.get_template():
            if y >= 0:
                pygame.draw.rect(console, self.color, (scale(8 + shift(x)),
                                                       scale(8 + shift(y)),
                                                       scale(6),
                                                       scale(6)))


class Board(object):
    """ board class """
    __slots__ = ('x', 'y', 'w', 'h', 'grid', 'pieces',
                 'hold', 'level', 'score', 'fall_speed',
                 'last_fall_time', 'last_move_time', 'last_update')
    
    def __init__(self, x, y, w, h):
        self.x, self.y = x, y  # top left position in pixels
        self.w, self.h = w, h  # height and width in blocks

        # make an empty board
        self.grid = [[None for _ in range(w)] for _ in range(h)]
        # [current piece, next piece, held piece, ghost piece]
        self.pieces = [None, Piece(), None, None]
        self.get_next_piece()
        self.get_ghost()
        self.hold = True  # allow holding

        self.level, self.score = 0, 0
        self.fall_speed = 0.5
        self.last_fall_time = time.time()
        self.last_move_time = time.time()
        self.last_update = time.time()

    def drop_piece(self):
        """ drops the piece to it's ghost's position """
        self.last_update = time.time()
        self.pieces[0].x, self.pieces[0].y = self.pieces[3].x, self.pieces[3].y
        
    def hold_piece(self):
        """ assigns the piece to holding area """
        if self.pieces[2]:
            self.pieces[0], self.pieces[2] = self.pieces[2], self.pieces[0]
        else:
            self.pieces[:3] = [self.pieces[1], Piece(), self.pieces[0]]

        self.pieces[0].reset()
        self.pieces[2].hold()
        self.hold = False

    def get_ghost(self):
        """ shows where the piece will fall """
        self.pieces[3] = copy.deepcopy(self.pieces[0])
        self.pieces[3].color = GRAY
        
        while self.is_valid_position(self.pieces[3]):
            self.pieces[3].y += 1
        self.pieces[3].y -= 1

    def get_next_piece(self):
        self.pieces[0], self.pieces[1] = self.pieces[1], Piece()
        self.pieces[0].reset()  # starting position of the current piece

    def set_piece(self):
        """ sets the piece inplace on the board """
        for (x, y) in self.pieces[0].get_template():
            self.grid[y][x] = self.pieces[0].color

        self.score += 10
        self.get_next_piece()

    def is_valid_position(self, piece):
        """ checks if the piece is in a valid position on the board """
        for (x, y) in piece.get_template():
            if x < 0 or x > 9 or y > 19 or \
                    (0 <= x <= 9 and 0 <= y <= 19 and self.grid[y][x]):
                return False
        return True

    def move_piece(self, x, y):
        self.pieces[0].move(x, y)
        if self.is_valid_position(self.pieces[0]):
            self.last_move_time = self.last_update = time.time()
        else:
            self.pieces[0].move(-x, -y)
                
    def rotate_piece(self, rotation):
        self.pieces[0].rotate(rotation)
        if not self.is_valid_position(self.pieces[0]):
            self.pieces[0].rotate(-rotation)

    def update(self, inputs):
        """ updates the board """
        if inputs.move_left and time.time() - self.last_move_time > 0.075:
            self.move_piece(-1, 0)
        elif inputs.move_right and time.time() - self.last_move_time > 0.075:
            self.move_piece(1, 0)
        elif inputs.move_down and time.time() - self.last_move_time > 0.075:
            self.move_piece(0, 1)
        elif inputs.drop:
            self.drop_piece()
            inputs.drop = False

        if inputs.rotate_left:
            self.rotate_piece(-1)
            inputs.rotate_left = False
        elif inputs.rotate_right:
            self.rotate_piece(1)
            inputs.rotate_right = False
            
        if inputs.hold and self.hold:
            self.hold_piece()
            inputs.hold = False

        if time.time() - self.last_fall_time > self.fall_speed:
            self.last_fall_time = time.time()
            self.move_piece(0, 1)

        if time.time() - self.last_update > 0.08:
            self.last_update = time.time()
            if (self.pieces[0].x, self.pieces[0].y) == \
                    (self.pieces[3].x, self.pieces[3].y):
                self.set_piece()
                inputs.reset()
                self.hold = True
                
        lines_cleared = 0
        for row in reversed(range(self.h)):
            while None not in self.grid[row]:
                self.grid[1:row + 1] = self.grid[:row]
                self.grid[0] = [None] * self.w
                lines_cleared += 1

        if lines_cleared:
            # update the score
            self.score += MULTIPLIER[lines_cleared] * (self.level + 1)

        if self.level < 30:
            self.level = self.score // 1000  # update the level
            # update the falling speed of the pieces
            self.fall_speed = 0.5 - self.level * 0.015

        self.get_ghost()

    def render(self, console):
        # render the border
        pygame.draw.rect(console, WHITE, (scale(self.x - 2),
                                          scale(self.y - 2),
                                          scale(8 * self.w + 4),
                                          scale(8 * self.h + 4)),
                         scale(1))

        # render the board
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x]:
                    pygame.draw.rect(console, self.grid[y][x],
                                     (scale(self.x + shift(x)),
                                      scale(self.y + shift(y)),
                                      scale(6),
                                      scale(6)))
                    
        # render the pieces
        for piece in reversed(self.pieces):
            if piece:
                piece.render(console)


class Text(pygame.Rect):
    """ text class """
    __slots__ = ('font', 'fg', 'bg', 'surface')
    
    def __init__(self, text, size, x, y, fg, bg=None):
        self.font = pygame.font.Font(FONT, size)
        self.fg, self.bg = fg, bg  # foreground and background colours
        self.surface = self.font.render(text, False, fg, bg)
        super().__init__(self.surface.get_rect())
        self.center = (x, y)  # position of the centre of the text

    def update(self, text):
        center = self.center
        self.surface = self.font.render(text, False, self.fg, self.bg)
        self.width = self.surface.get_rect().width
        self.center = center


class Gui(object):
    """ gui class """
    __slots__ = 'texts'
    
    def __init__(self):
        # level text
        self.texts = [Text('Level 0', scale(8), scale(136), scale(16), WHITE)]

        # score text
        self.texts.append(Text('Score', scale(8), scale(136), scale(40), WHITE))
        self.texts.append(Text('0', scale(8), scale(136), scale(56), WHITE))

        # next/hold piece text
        self.texts.append(Text('Next', scale(8), scale(136), scale(80), WHITE))
        self.texts.append(Text('Hold', scale(8), scale(136), scale(128), WHITE))

    def update(self, level, score):
        self.texts[0].update('Level ' + str(level))  # update level
        self.texts[2].update(str(score))  # update score

    def render(self, console):
        for text in self.texts:
            console.blit(text.surface, text)


class EventHandler(object):
    """ event handling class """
    __slots__ = ('move_left', 'move_right', 'move_down',
                 'rotate_left', 'rotate_right', 'drop', 'hold')
    
    def __init__(self):
        self.move_left = False
        self.move_right = False
        self.move_down = False
        self.rotate_left = False
        self.rotate_right = False
        self.drop = False
        self.hold = False

    def get_events(self):
        check_for_quit()

        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    self.move_left = True
                elif event.key == K_RIGHT:
                    self.move_right = True
                elif event.key == K_DOWN:
                    self.move_down = True
                elif event.key == K_SPACE:
                    self.drop = True
                elif event.key == K_x:
                    self.hold = True

                if event.key == K_z:
                    self.rotate_left = True
                elif event.key in (K_c, K_UP):
                    self.rotate_right = True

            elif event.type == KEYUP:
                if event.key == K_LEFT:
                    self.move_left = False
                elif event.key == K_RIGHT:
                    self.move_right = False
                elif event.key == K_DOWN:
                    self.move_down = False
                elif event.key == K_SPACE:
                    self.drop = False
                elif event.key == K_x:
                    self.hold = False
                elif event.key == K_z:
                    self.rotate_left = False
                elif event.key in (K_c, K_UP):
                    self.rotate_right = False
                    
    def reset(self):
        self.move_left = False
        self.move_right = False
        self.move_down = False
        self.rotate_left = False
        self.rotate_right = False
        self.drop = False
        self.hold = False


class Engine(object):
    """ game engine class """
    __slots__ = ('console', 'event_handler', 'fps_clock',
                 'gui', 'state', 'board')
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Tetris')
        self.console = pygame.display.set_mode((scale(WIN_WIDTH),
                                                scale(WIN_HEIGHT)))
        self.event_handler = EventHandler()
        self.fps_clock = pygame.time.Clock()
        self.gui = Gui()
        
        self.state = 'new'
        self.board = None

    def init(self):
        """ initialises a new game """
        self.state = 'playing'
        self.board = Board(8, 8, 10, 20)
        
    def update(self):
        # update the board, score and level
        self.event_handler.get_events()
        self.board.update(self.event_handler)

        for x in range(self.board.w):
            if self.board.grid[0][x]:  # pieces have hit the top of the screen
                self.state = 'new'  # reset abruptly
            
        # update GUI
        self.gui.update(self.board.level, self.board.score)
        
        self.fps_clock.tick(60)

    def render(self):
        self.console.fill(BLACK)

        self.gui.render(self.console)
        self.board.render(self.console)

        pygame.display.update()


def check_for_quit():
    if pygame.event.get(QUIT):
        terminate()
    for event in pygame.event.get(KEYUP):
        if event.key == K_ESCAPE:
            terminate()
        pygame.event.post(event)


def terminate():
    pygame.quit()
    sys.exit()


def scale(x):
    """ scales the window """
    return x * SCALE
    
    
def shift(x):
    """ aligns the toft left position """
    return 8 * x + 1


if __name__ == '__main__':
    description = """[Rotate] ↑ / Z / C
                     [Left] ←
                     [Right] →
                     [Down] ↓
                     [Drop] / Space
                     [Hold] Z"""
    parser = ArgumentParser(description=description)
    args = parser.parse_args()

    engine = Engine()

    while True:
        if engine.state == 'new':
            engine.init()
            
        engine.update()
        engine.render()

