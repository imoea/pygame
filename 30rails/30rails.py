#!/usr/bin/env python3

"""
A Python implementation of the
Print and Play, Roll and Write
game 30 Rails by Julian Anstey
"""

from argparse import ArgumentParser
from copy import deepcopy
from enum import Enum
import random


__author__ = "Joshua Wong"
__version__ = "0.1"


class Tile(Enum):
    BONUS = '*'
    BORDER = ' '
    EMPTY = '.'
    MINE = u'\u27F0'
    MOUNTAIN = u'\u25B2'
    STATION1 = '1'
    STATION2 = '2'
    STATION3 = '3'
    STATION4 = '4'
    TRACK = '+'


class Way(Enum):
    N = 0
    E = 1
    S = 2
    W = 3


class Cell:
    __slots__ = ('tile', 'edges')
    def __init__(self, tile, edges=None):
        """ initialise a cell """
        self.tile = tile    # tile type
        self.edges = None   # list of edges for stations and tracks
        if edges is not None:
            self.edges = tuple(map(tuple, edges))


class Game:
    def __init__(self, size=6, demo=False, verbose=False):
        """ initialise an empty board """
        self._size = size                   # size of the board
        self._n_rounds = size*(size-1)      # number of game rounds
        self._curr_round = -size-5          # current game round

        self._mine = None                   # position of the mine
        self._station = {}                  # positions of the stations
        self._bonus = None                  # position of the bonus
        self._curr_src = None               # source for scoring
        self._curr_dst = None               # destination for scoring
        self._n_connected_mines = 0         # number of stations connected to the mine
        self._score = 0                     # final score

        self._white = None                  # value of the white die
        self._black = None                  # value of the black die
        self._allow_white_override = True   # override for the white die
        self._allow_black_override = True   # override for the black die
        self._n_die_rolls = 0               # number of die-rolls
        self._valid_placements = None       # placements determined by the white die
        self._demo = demo                   # demo mode
        self._verbose = verbose             # verbose

        # for scoring
        self._scoring = {(1, 2): 1, (1, 3): 2, (1, 4): 3, (2, 3): 3, (2, 4): 4, (3, 4): 5,
                         1: 2, 2: 6, 3: 12, 4: 20}

        # empty grid
        self._grid = [[Cell(Tile.BORDER) for _ in range(size+2)]]
        for y in range(1, size+1):
            self._grid.append([Cell(Tile.BORDER)])
            for x in range(1, size+1):
                self._grid[y].append(Cell(Tile.EMPTY))
            self._grid[y].append(Cell(Tile.BORDER))
        self._grid.append([Cell(Tile.BORDER) for _ in range(size+2)])


    def _is_empty(self, y, x):
        """ check if a cell is empty """
        return self._grid[y][x].tile is Tile.EMPTY


    def _is_type(self, y, x, tile):
        """ check if a cell is of a given tile type """
        return self._grid[y][x].tile is tile


    def _check_border(self, y, x):
        """ check for valid border placement """
        assert ((y == 0 or y == self._size+1) and 1 <= x <= self._size) or \
               ((x == 0 or x == self._size+1) and 1 <= y <= self._size),   \
               "({}, {}) is not on the border".format(x, y)
        assert self._grid[y][x].tile is Tile.BORDER, "the cell is already occupied"


    def _check_grid(self, y, x):
        """ check for valid grid placement """
        assert 1 <= y <= self._size and 1 <= x <= self._size, \
               "({}, {}) is not on the grid".format(x, y)
        assert self._is_empty(y, x), "the cell is already occupied"


    def _set_cell(self, y, x, tile, edges=None):
        """ set a cell to be a given tile """
        assert isinstance(tile, Tile), "{} is not a tile instance".format(tile)

        self._grid[y][x] = Cell(tile, edges)
        if self._verbose:
            print("[{}] Placing a {} at ({}, {})".format(
                  "Turn {:<2}".format(self._curr_round+1) if self._curr_round >= 0 else "Setup  ",
                  tile.name, y, x))


    def set_mountain(self, y, x):
        """ set a cell to be a mountain """
        self._check_grid(y, x)
        assert self._curr_round < -6, \
               "the number of mountains is exceeded"

        self._set_cell(y, x, Tile.MOUNTAIN)
        self._curr_round += 1


    def set_mine(self, y, x):
        """ set a cell to be a mine """
        self._check_grid(y, x)
        assert self._mine is None, "a mine already exists"
        assert self._grid[y-1][x].tile is Tile.MOUNTAIN or \
               self._grid[y+1][x].tile is Tile.MOUNTAIN or \
               self._grid[y][x-1].tile is Tile.MOUNTAIN or \
               self._grid[y][x+1].tile is Tile.MOUNTAIN,   \
               "the mine is not beside a mountain"

        self._set_cell(y, x, Tile.MINE, [[Way(i)] for i in range(4)])
        self._mine = (y, x)
        self._curr_round += 1


    def set_station(self, y, x, station):
        """ set a cell to be a station """
        self._check_border(y, x)
        assert station is Tile.STATION1 or \
               station is Tile.STATION2 or \
               station is Tile.STATION3 or \
               station is Tile.STATION4,   \
               "{} is not a station tile".format(station)
        assert station not in self._station, \
               "station {} already exists".format(station.value)

        if   y == 0:            edges = [[Way.S]]
        elif y == self._size+1: edges = [[Way.N]]
        elif x == 0:            edges = [[Way.E]]
        elif x == self._size+1: edges = [[Way.W]]

        self._set_cell(y, x, station, edges)
        self._station[int(station.value)] = (y, x)
        self._curr_round += 1


    def set_bonus(self, y, x):
        """ set a cell to be the bonus """
        self._check_grid(y, x)
        assert self._bonus is None, "the bonus already exists"

        self._bonus = (y, x)
        if self._verbose:
            print("[Setup  ] Placing a BONUS at ({}, {})".format(self._curr_round+1, y, x))

        self._curr_round += 1


    def set_track(self, y, x, track, flip=False, rotate=0,
                  white_override=False, black_override=False):
        """ set a cell to be a track """
        self._check_grid(y, x)
        assert track in {1, 2, 3, 4, 5, 6}, "the track is not valid"

        if not self._demo:
            assert self._n_die_rolls == self._curr_round+1, "CHEATER!"

            if white_override:
                assert self._allow_white_override, "white override has been used"
                self._allow_white_override = False
            else:
                assert (y, x) in self._valid_placements, \
                       "the placement does not match the die-roll"

            if black_override:
                assert self._allow_black_override, "black override has been used"
                self._allow_black_override = False
            else:
                assert track == self._black, "the track does not match the die-roll"

        edges = []
        if track in {1, 3, 5, 6}:
            edges += [[Way.S, Way.E], [Way.E, Way.S]]
        if track in {2, 4, 6}:
            edges += [[Way.N, Way.S], [Way.S, Way.N]]
        if track == 3:
            edges += [[Way.N, Way.W], [Way.W, Way.N]]
        if track == 4:
            edges += [[Way.W, Way.E], [Way.E, Way.W]]
        if track == 5:
            edges += [[Way.W, Way.S], [Way.S, Way.W]]

        if flip:
            for edge in edges:
                for i in range(2):
                    if edge[i].value % 2:
                        edge[i] = Way((edge[i].value+2) % 4)

        if rotate:
            for edge in edges:
                for i in range(2):
                    edge[i] = Way((edge[i].value+rotate) % 4)

        self._set_cell(y, x, Tile.TRACK, tuple(map(tuple, edges)))
        self._curr_round += 1


    def _get_bonus(self, path):
        """ get bonus points if the path passes through the bonus cell """
        for y, x, *_ in path:
            if (y, x) == self._bonus:
                return 2
        return 0


    def _get_edges(self, y, x):
        """ get the edges of a cell """
        return self._grid[y][x].edges


    def _has_node(self, y, x, way):
        """ check if an edge travels a given way"""
        edges = self._get_edges(y, x)
        if edges is not None:
            for edge in edges:
                if edge[0] is way:
                    return True
        return False


    def _trace(self, y, x, prev_edge, path=[], paths=[]):
        """ trace a path between a given source and its destination """
        src, dst = self._curr_src, self._curr_dst
        subpath = (y, x, *sorted(x.value for x in prev_edge))  # path signature

        if (y, x) == dst:
            paths.append(path)  # completed path from source to destination

        elif (y, x) == src or (self._is_type(y, x, Tile.TRACK) and subpath not in path):
            # to prevent loopbacks
            if (y, x) != src:
                path.append(subpath)
            # trace all possible edges
            edges = self._get_edges(y, x)
            if edges is not None:
                for edge in edges:
                    if (edge[0].value+2) % 4 == prev_edge[-1].value or (y, x) == src:

                        if   edge[-1] is Way.N and self._has_node(y-1, x, Way.S):
                            self._trace(y-1, x, edge, deepcopy(path), paths)

                        elif edge[-1] is Way.E and self._has_node(y, x+1, Way.W):
                            self._trace(y, x+1, edge, deepcopy(path), paths)

                        elif edge[-1] is Way.S and self._has_node(y+1, x, Way.N):
                            self._trace(y+1, x, edge, deepcopy(path), paths)

                        elif edge[-1] is Way.W and self._has_node(y, x-1, Way.E):
                            self._trace(y, x-1, edge, deepcopy(path), paths)


    def is_over(self):
        """ check if the game is over """
        return self._curr_round >= self._n_rounds


    def start(self):
        """ surround the grid with mountains and start the game """
        assert self._curr_round == 0, "the game setup is not complete"


    def get_empty_cells(self, value=None, override=False):
        """ get empty cells of a given row and column
            or all empty cells on the board """
        if value is None or override:
            empty_cells = [(y, x) for y in range(1, self._size+1)
                                  for x in range(1, self._size+1)
                                  if self._is_empty(y, x)]

        else:
            assert 1 <= value <= self._size, \
                   "{} is not a valid row or column".format(value)
            empty_cells = {(y, value) for y in range(1, self._size)
                                      if self._is_empty(y, value)} | \
                          {(value, x) for x in range(1, self._size)
                                      if self._is_empty(value, x)}
            # when the row and column of a given value is filled
            if len(empty_cells) == 0:
                return self.get_empty_cells()

        self._valid_placements = sorted(empty_cells)

        return self._valid_placements


    def get_game_state(self):
        """ get the current state of the game """
        return deepcopy(self._grid)


    def roll_dice(self):
        """ roll a pair of black and white dice """
        self._white = random.randint(1, self._size)
        self._black = random.randint(1, self._size)
        self._n_die_rolls += 1
        return self._white, self._black


    def randomise_setup(self, demo=False, verbose=False):
        """ seed the game setup """
        self.__init__(self._size, demo, verbose)

        # seed the game with mountains
        n_mountains = 0

        for y in range(1, self._size+1):
            if y - n_mountains < 2 and random.randint(0, 1):
                continue

            self.set_mountain(y, random.randint(1, self._size))
            n_mountains += 1

        # seed the game with a mine
        mountains_pos = [(y, x) for y in range(1, self._size+1)
                                for x in range(1, self._size+1)
                                if self._grid[y][x].tile is Tile.MOUNTAIN]

        mines_pos = [(y+dy, x+dx) for y, x in mountains_pos
                                  for dy, dx in [(-1, 0), (1, 0),
                                                 (0, -1), (0, 1)]
                                  if self._is_empty(y+dy, x+dx)]

        self.set_mine(*random.choice(mines_pos))

        # seed the game with stations
        stations = [Tile.STATION1, Tile.STATION2, Tile.STATION3, Tile.STATION4]
        random.shuffle(stations)

        y = 0
        x = random.choice([x for x in range(1, self._size+1)
                             if self._is_empty(1, x)])
        self.set_station(y, x, stations.pop())

        y = random.choice([y for y in range(1, self._size+1)
                             if self._is_empty(y, 1)])
        x = 0
        self.set_station(y, x, stations.pop())

        y = self._size+1
        x = random.choice([x for x in range(1, self._size+1)
                             if self._is_empty(self._size, x)])
        self.set_station(y, x, stations.pop())

        y = random.choice([y for y in range(1, self._size+1)
                             if self._is_empty(y, self._size)])
        x = self._size+1
        self.set_station(y, x, stations.pop())

        # seed the game with a bonus
        self.set_bonus(*random.choice(self.get_empty_cells()))


    def display(self):
        """ display the board """
        print()
        for row in self._grid:
            print('  ' + ' '.join(cell.tile.value for cell in row))
        print()


    def end(self):
        """ compute the final score and end the game """
        # for connecting stations
        for i in range(1, 4):
            for j in range(i+1, 5):
                self._curr_src, self._curr_dst = self._station[i], self._station[j]
                y, x = self._curr_src
                paths = []
                self._trace(y, x, self._grid[y][x].edges[0], paths=paths)

                if len(paths) != 0:
                    shortest_path = min(paths, key=len)
                    score = [self._scoring[(i, j)],             # score for connection
                             len(shortest_path),                # score for the shortest path
                             self._get_bonus(shortest_path)]    # score bonus
                    self._score += sum(score)

                else:
                    score = [0, 0, 0]

                if self._verbose:
                    print("[Scoring] {}->{}".format(i, j),
                          "  {:>2} = {:>2} + {:>2} + {:>2}".format(sum(score), *score))

        # for connecting stations to the mine
        for i in range(1, 5):
            self._curr_src, self._curr_dst = self._station[i], self._mine
            y, x = self._curr_src
            paths = []
            self._trace(y, x, self._grid[y][x].edges[0], paths=paths)

            if len(paths) != 0:
                self._n_connected_mines += 1

            if self._verbose:
                print("[Scoring] {}->{}  ".format(i, Tile.MINE.value),
                        "\u2714" if len(paths) != 0 else "\u2718")

        self._score += self._scoring[self._n_connected_mines]  # score for the mine

        print("======================================")
        print("[Scoring] TOTAL {:>3}".format(self._score))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--seed', default=None, type=int,
                        help="seed for a deterministic game")
    parser.add_argument('--size', default=6, type=int,
                        help="size of the board; default is 6")
    parser.add_argument('--demo', action='store_true',
                        help="run in demo mode")
    args = parser.parse_args()

    assert args.size >= 6, "the board size must be at least 6x6"

    if args.demo:
        random.seed(0)

        game = Game()
        game.randomise_setup(demo=True, verbose=True)
        game.start()
        # targeted placements for sanity check
        game.set_track(3, 6, 6, flip=1, rotate=-1)
        game.set_track(3, 5, 6, rotate=-1)
        game.set_track(2, 5, 2)
        game.set_track(1, 5, 6, rotate=2)
        game.set_track(3, 4, 6, rotate=1)
        game.set_track(3, 3, 6, rotate=-1)
        game.set_track(2, 3, 6, flip=1)
        game.set_track(1, 3, 6, flip=1, rotate=-1)
        game.set_track(1, 4, 2, rotate=-1)
        game.set_track(2, 2, 6, rotate=1)
        game.set_track(2, 1, 6, flip=1, rotate=1)
        game.set_track(1, 2, 2, rotate=-1)
        game.set_track(1, 1, 1)
        game.set_track(4, 6, 6, flip=1)
        game.set_track(5, 6, 2)
        game.set_track(6, 6, 1, rotate=2)
        game.set_track(4, 4, 1, rotate=-1)
        game.set_track(4, 5, 2, rotate=-1)
        game.set_track(3, 2, 6)
        game.set_track(4, 2, 2)
        game.set_track(5, 2, 2)
        game.set_track(6, 2, 2)
        # random placements
        while not game.is_over():
            black, white = game.roll_dice()
            valid_placements = game.get_empty_cells(white)
            game.set_track(*random.choice(valid_placements), black,
                           flip=random.randint(0, 1), rotate=random.randint(0, 3))
        game.end()
        game.display()

