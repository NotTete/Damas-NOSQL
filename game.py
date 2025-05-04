'''
    Script con las funciones de la lógica
    del juego de las damas

    Autor: Jorge Hernández Palop
'''

import math

# Crea un tablero de damas inicial
def createCheckersBoard():
    board = [[0 for j in range(8)] for i in range(8)]

    for i in range(0, 8, 2):
        board[0][i] = 1
        board[1][i + 1] = 1
        board[2][i] = 1
        board[6][i] = -1
        board[7][i + 1] = -1
        board[6][i] = -1
        board[5][i + 1] = -1
    return board

# Función de utilidad para la codificación
# y decodificación

# Dado el indice de un bit lo traduce a coordenas
# en el tablero
def getXY(i):
    i *= 2
    y = i // 8
    x = i % 8 + (y % 2 == 1)

    return x, y

# Codifica el tablero de formato a lista
# a 4 numeros de 32bits donde el bit i a 0 representa
# que no está la pieza en la i-ésima posición
# y 1 que sí
#
# p1n: Piezas normales del jugador 1
# p1q: Reyes del jugador 1
# p2n: Piezas normales del jugador 2
# p2q: Reyes del jugador 2
def encodeBoard(board):
    p1n = 0
    p2n = 0
    p1q = 0
    p2q = 0

    for i in range(32):
        x, y = getXY(i)
        if board[y][x] == 1: p1n += 1 << i;
        if board[y][x] == -1: p2n += 1 << i;
        if board[y][x] == 2: p1q += 1 << i;
        if board[y][x] == -2: p2q += 1 << i;

    return p1n, p2n, p1q, p2q

# Decodificar el tablero de formato númerico
# a lista
def decodeBoard(p1n, p2n, p1q, p2q):
    board = [[0 for j in range(8)] for i in range(8)]

    for i in range(32):
        x, y = getXY(i)
        if p1n & (1 << i): board[y][x] = 1
        elif p2n & (1 << i): board[y][x] = -1
        elif p1q & (1 << i): board[y][x] = 2
        elif p2q & (1 << i): board[y][x] = -2

    return board

# Función de utilidad para determinar si la posición
# está dentro del tablero
def inside(x, y):
    return 0 <= x and x < 8 and 0 <= y and y < 8

# Obtiene los posibles movimientos
# que puede hacer una pieza
def getPossibleMoves(board, x, y, sgn):

    eat = False

    # Comprobamos que otras piezas no puedan comer
    for nx in range(8):
        for ny in range(8):
            if(sgn * board[ny][nx] > 0):
                _, eat = getPossibleMovesPerPieces(board, nx, ny, sgn)

                if eat: break
        if eat: break

    # Los movimientos de la pieza que vamos a mover
    res, eat2 = getPossibleMovesPerPieces(board, x, y, sgn)

    # Verificación de si podríamos comer o no
    if eat2 or not eat:
        return res
    else:
        return []

# Códifica los movimientos en base a la posición del tablero
def encodeMoves(*args):
    result = 0

    for x, y in args:
        i = (y * 8 + x) // 2
        result += 1 << i
    
    return result

# Devuelve los posibles movimiento de una pieza independientemente
# de si se puede comer o no con otras
def getPossibleMovesPerPieces(board, x, y, sgn):
    res = []


    dirs = [(-1, 1), (1, 1)] if sgn == 1 else [(-1, -1), (1, -1)]
    eat = False

    # Pieza normal
    if abs(board[y][x]) == 1:
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if inside(nx, ny) and board[ny][nx] == 0:
                res.append((nx, ny))
        for dx, dy in dirs:
            mx, my = x + dx, y + dy
            nx, ny = x + 2 * dx, y + 2 * dy
            
            if inside(nx, ny) and board[ny][nx] == 0 and board[my][mx] * sgn < 0:
                if eat == False: res = []
                eat = True

                res.append((nx, ny))

    # Rey
    elif abs(board[y][x]) == 2:
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            nx, ny = x + dx, y + dy
            while inside(nx, ny) and board[ny][nx] == 0:
                res.append((nx, ny))
                nx += dx
                ny += dy

            if inside(nx, ny) and board[ny][nx] * sgn < 0:
                nx += dx
                ny += dy
                while inside(nx, ny) and board[ny][nx] == 0:
                    if eat == False: res = []
                    eat = True
                    res.append((nx, ny))
                    nx += dx
                    ny += dy      


    return res, eat

# Simula el movimiento de la ficha en el tablero
def move(board, ox, oy, dx, dy):
    d = abs(ox - dx)
    dirX = 2 * (dx - ox > 0) - 1   
    dirY = 2 * (dy - oy > 0) - 1   

    # Comemos todos lo que está entre el principio y el final del movimiento
    board[dy][dx] = board[oy][ox] 
    eat = False
    for i in range(d):
        if i > 0 and board[oy + dirY * i][ox + dirX * i] != 0: eat = True
        board[oy + dirY * i][ox + dirX * i] = 0

    # Coronación
    if (dy == 0 or dy == 7) and abs(board[dy][dx]) == 1:
        board[dy][dx] *= 2
    
    return board, eat

# Detecta si ha habido una victoria.
# 1. Victoria del jugador 1
# 0. Empate
# -1. Victoria del jugador 2
def win(board):
    pos = 0
    neg = 0

    for x in range(8):
        for y in range(8):
            pos += board[y][x] > 0
            neg += board[y][x] < 0
    return (neg > 0) - (pos > 0)