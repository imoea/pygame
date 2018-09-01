#!/usr/bin/env python
""" the Dollar Game by Joshua Wong """

from argparse import ArgumentParser
from pygame.locals import *
import networkx as nx
import numpy as np
import pygame
import random


BORDER = 50
WIN_WIDTH = 800
WIN_HEIGHT = 600

FONT = 'freesansbold.ttf'
FONT_SIZE = 30
RADIUS = 30
RADIUS2 = RADIUS**2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


class Game():
    """ game class """
    __slots__ = ('graph', 'focus', 'money', 'moves', 'nodes', 'pos') 

    def __init__(self, height, width, graph, *args):
        """ initialise the game state """
        g = graph(*args)
        n_nodes, n_edges = g.number_of_nodes(), g.number_of_edges()
        self.graph = g  # the graph
        self.focus = None
        self.moves = 0  # number of moves taken
        self.nodes = sorted(g.nodes)  # nodes of the graph
        
        # determine node positions
        pos = {}
        offset = np.array([width, height]) / 2
        for k, v in nx.kamada_kawai_layout(g).items():
            pos[k] = np.around(v * offset + offset).astype(int)
            pos[k] += np.array([BORDER, BORDER])
        self.pos = [pos[node] for node in self.nodes]  # node positions
        
        self.money = np.zeros(n_nodes, dtype=int)  # node wealth
        # distribute starting wealth
        for _ in range(n_edges - n_nodes + 1):
            self.money[random.choice(self.nodes)] += 1
        # make random donations to set the starting game state
        for _ in range(n_edges):
            self.make_donation(random.choice(self.nodes))


    def set_difficulty(self, donations):
        """ increase the difficulty by making more random donations """
        for _ in range(donations):
            self.make_donation(random.choice(self.nodes))


    def get_win(self):
        """ check winning condition """
        return all(self.money >= 0)


    def make_donation(self, node, move=0):
        """ redistribute the wealth of a given node """
        for nbr in self.graph.neighbors(node):
            self.money[nbr] += 1
            self.money[node] -= 1
        self.moves += move


    def render(self, console):
        """ render the graph """
        # render edges
        for start, end in self.graph.edges:
            pygame.draw.line(console, WHITE, self.pos[start], self.pos[end])

        # highlight edges adjacent to the node in focus
        if self.focus is not None:
            node = self.focus
            for nbr in self.graph.neighbors(node):
                pygame.draw.line(console, GREEN,
                                 self.pos[node], self.pos[nbr], 3)

        # render nodes
        for node in self.graph.nodes:
            color = RED if self.money[node] < 0 else BLUE
            pygame.draw.circle(console, color, self.pos[node], RADIUS)
            text = Text(self.money[node], self.pos[node], WHITE)
            console.blit(text.surface, text)


    def update(self, event):
        """ update the game state """
        for node, pos in enumerate(self.pos):
            if sum((pos - np.array(event.mousexy))**2) < RADIUS2:
                self.focus = node
                if event.mousebutton == 1:
                    self.make_donation(node, move=1)
                break
        else:
            self.focus = None


class Text(pygame.Rect):
    """ text class """
    __slots__ = ('font', 'fg', 'bg', 'surface')
    
    def __init__(self, text, xy, fg, bg=None):
        self.font = pygame.font.Font(FONT, FONT_SIZE)
        self.fg, self.bg = fg, bg  # foreground and background colours
        self.surface = self.font.render(str(text), False, fg, bg)
        super().__init__(self.surface.get_rect())
        self.center = xy  # position of the centre of the text


class EventHandler():
    """ event handling class """
    __slots__ = ('mousexy', 'mousebutton')
    
    def __init__(self):
        self.mousexy = (0, 0)
        self.mousebutton = 0


    def get_events(self):
        """ get mouse and key events """
        self.reset_events()
        event = pygame.event.wait()

        if event.type == QUIT or \
                (event.type == KEYUP and event.key in {K_ESCAPE, K_q}):
            pygame.quit()
            exit()

        elif event.type == MOUSEBUTTONUP:
            self.mousexy = event.pos
            self.mousebutton = event.button

        elif event.type == MOUSEMOTION:
            self.mousexy = event.pos


    def reset_events(self):
        self.mousebutton = 0


class Engine():
    """ game engine class """
    __slots__ = ('console', 'event_handler', 'game')

    def __init__(self):
        pygame.init()
        pygame.display.set_caption('The Dollar Game')
        self.console = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.event_handler = EventHandler()


    def init(self, graph, *args):
        """ initialise a new game """
        self.game = Game(WIN_HEIGHT - 2*BORDER,
                         WIN_WIDTH - 2*BORDER,
                         graph, *args)


    def update(self):
        """ update the game state """
        self.event_handler.get_events()
        self.game.update(self.event_handler)


    def render(self):
        """ render the game state """
        self.console.fill(BLACK)
        self.game.render(self.console)
        pygame.display.update()


graph = dict(PETERSEN=nx.petersen_graph,
             MAZE=nx.sedgewick_maze_graph,
             COMPLETE=nx.complete_graph,
             STROGATZ=nx.watts_strogatz_graph,
             BARABASI=nx.barabasi_albert_graph)


def get_graph_params(args):
    if args.name in {'PETERSEN', 'MAZE'}:
        params = []
    elif args.name == 'COMPLETE':
        params = [6 if args.n is None else args.n]
    elif args.name == 'STROGATZ':
        params = [5 if args.n is None else args.n, args.e, args.p]
    elif args.name == 'BARABASI':
        params = [10 if args.n is None else args.n, args.e]

    return [graph[args.name]] + params


if __name__ == '__main__':
    parser = ArgumentParser(description='Press Esc or Q to quit.')
    parser.add_argument('-name', default='PETERSEN',
                        help="""PETERSEN,
                                MAZE,
                                COMPLETE(n),
                                STROGATZ(n, e, p),
                                BARABASI(n, e)""")
    parser.add_argument('-n', default=None, type=int,
                        help='number of nodes')
    parser.add_argument('-e', default=2, type=int,
                        help='number of edges per node')
    parser.add_argument('-p', default=0.5, type=float,
                        help='probability of rewiring')
    parser.add_argument('-d', default=0, type=int,
                        help='difficulty')
    args = parser.parse_args()

    if args.name not in graph:
        print('Graph `{}` not found.'.format(args.name))
        exit()

    instructions = """
    THE DOLLAR GAME
    ===============

    Each graph represents a social network.
    The value of each node shows the amount of money each person has.
    Positive values represent wealth while negative ones represent poverty.
    The aim of this game is to get everyone out of poverty.
    When clicking a person, s/he donates $1 to each friend.
    Help get everyone out of poverty!
    """
    print(instructions)

    engine = Engine()
    # start a new game
    engine.init(*get_graph_params(args))
    engine.game.set_difficulty(args.d)

    while True:
        engine.update()
        engine.render()
        
        if engine.game.get_win():
            # start a new game with a new graph
            args.name = random.choice(list(graph))
            engine.init(*get_graph_params(args))
            engine.game.set_difficulty(args.d)

