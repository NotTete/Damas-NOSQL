import math
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

def getXY(i):
    i *= 2
    y = i // 8
    x = i % 8 + (y % 2 == 1)

    return x, y

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

def decodeBoard(p1n, p2n, p1q, p2q):
    board = [[0 for j in range(8)] for i in range(8)]

    for i in range(32):
        x, y = getXY(i)
        if p1n & (1 << i): board[y][x] = 1
        elif p2n & (1 << i): board[y][x] = -1
        elif p1q & (1 << i): board[y][x] = 2
        elif p2q & (1 << i): board[y][x] = -2

    return board

def inside(x, y):
    return 0 <= x and x < 8 and 0 <= y and y < 8

def getPossibleMoves(board, x, y, sgn):

    eat = False

    for nx in range(8):
        for ny in range(8):
            if(sgn * board[ny][nx] > 0):
                _, eat = getPossibleMovesPerPieces(board, nx, ny, sgn)

                if eat: break
        if eat: break

    res, eat2 = getPossibleMovesPerPieces(board, x, y, sgn)

    print(res, eat, eat2)
    if eat2 or not eat:
        return res
    else:
        return []

def encodeMoves(*args):
    result = 0

    for x, y in args:
        i = (y * 8 + x) // 2
        result += 1 << i
    
    return result

def getPossibleMovesPerPieces(board, x, y, sgn):
    res = []


    dirs = [(-1, 1), (1, 1)] if sgn == 1 else [(-1, -1), (1, -1)]  # Regular piece moves (forward)
    eat = False
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

def move(board, ox, oy, dx, dy):
    d = abs(ox - dx)
    dirX = 2 * (dx - ox > 0) - 1   
    dirY = 2 * (dy - oy > 0) - 1   


    board[dy][dx] = board[oy][ox] 
    eat = False
    for i in range(d):
        if i > 0 and board[oy + dirY * i][ox + dirX * i] != 0: eat = True
        board[oy + dirY * i][ox + dirX * i] = 0

    if (dy == 0 or dy == 7) and abs(board[dy][dx]) == 1:
        board[dy][dx] *= 2
    
    return board, eat

def win(board):
    pos = 0
    neg = 0

    for x in range(8):
        for y in range(8):
            pos += board[y][x] > 0
            neg += board[y][x] < 0
    print(neg, pos, (neg > 0) - (pos > 0))
    return (neg > 0) - (pos > 0)