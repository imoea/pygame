import json

""" initialise game variables """
with open('pong.ini', 'r') as fi:
    init = json.load(fi)

FPS = init['FPS'] # frames per second
WINWIDTH, WINHEIGHT = init['window_size'] # window's width and height
HALFWINWIDTH, HALFWINHEIGHT = int(WINWIDTH/2), int(WINHEIGHT/2)
XMARGIN, YMARGIN = init['margins']

FONT = init['font']
SMALLFONTSIZE, BIGFONTSIZE, HUGEFONTSIZE = init['font_size']

PLAYERWIDTH, PLAYERHEIGHT = init['player_size'] # player's width and height
MAXPLAYERVELY = init['player_velocity'] # player's max velocity
PLAYERACCELY = init['player_acceleration'] # player's acceleration

BALLSIZE = init['ball_size'] # ball's width and height
MINBALLVELX, MAXBALLVELX = init['ball_velocity_x'] # square of the ball's max x velocity
MINBALLVELY, MAXBALLVELY = init['ball_velocity_y'] # ball's min and max y velocities

MAXPOINTS = init['max_points'] # max points before the game ends
SHAMELIMIT = init['shame_limit'] # max score difference between the winner and loser

BGCOLOR = init['bg_color']
FGCOLOR = init['fg_color']