import heapq
from copy import deepcopy
from collections import deque
import pygame

from board import Board, Cell, Snake
from baseagent import BaseAgent

BLACK = 0
WHITE = 1
EMPTY = -1


def makenonloopmasks():
    masks = set()
    nonloopmasks = [[[1, 0, 0], [0, 0, 0], [0, 0, 0]]]
    nonloopmasks.extend([[a, 1, b], [0, 0, 0], [0, 0, 0]] for a in (0, 1) for b in (0, 1))
    nonloopmasks.extend([[a, 1, b], [0, 0, 1], [0, 0, c]] for a in (0, 1) for b in (0, 1) for c in (0, 1))
    nonloopmasks.extend([[a, 1, b], [0, 0, 1], [d, 1, c]] for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1))
    for r in range(4):
        for mask in nonloopmasks:
            masks.add(tuple(tuple(tuple(x for x in row) for row in mask)))
        for mask in nonloopmasks:
            n = 3
            res = [[0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    res[j][n - i - 1] = mask[i][j]
            for i in range(n):
                for j in range(n):
                    mask[i][j] = res[i][j]

    return masks


class BWAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.steps = []
        self.iter = 0

        self.grid = Grid(self.w+1, self.h+1)

        self.grid.whiteUnconnectedCount += 1
        self.grid.whiteUnconnectedDict[self.grid.whiteUnconnectedCount] = self.grid.whiteUnconnectedCount

        self.grid.set((1, 1), 1)
        self.grid.set((2, 1), 1)
        self.grid.printgrid()

    def getDirection(self):

        if self.iter == len(self.steps):
            self.iter = 0
            origin = Step(self.snake, self.grid, None, False, self.food)
            self.steps = Step.A_star(origin, None, True, 0, False)
            finished: Step = Step.finished

            if self.steps is None:
                return Cell.reversedir(self.snake.direction)
            else:
                self.grid = finished.grid

        dir = self.steps[self.iter].dir
        self.iter += 1

        return dir

    def draw_debug(self, screen, tlcorner, cellsize, w, h):
        arearect = pygame.Rect(tlcorner[0], tlcorner[1], w*cellsize, h*cellsize)
        for x in range(w+1):
            for y in range(h+1):
                rect = pygame.Rect(tlcorner.x + x * cellsize-cellsize/2, tlcorner.y + y * cellsize-cellsize/2, cellsize, cellsize)
                rect.scale_by_ip(0.6, 0.6)
                rect = rect.clip(arearect)

                if (cell:= Grid.connToBWE(self.grid.at(x, y)[0])) != EMPTY:
                    color = "Red"
                    if cell == WHITE:
                        color = "White"
                    elif cell == BLACK:
                        color = "Black"
                    pygame.draw.rect(screen, color, rect)

class Grid:
    """
    https://web.mit.edu/8.592/www/grades/projects/projects(2013)/MichaelCrossley.pdf
    """
    nonloopmasks = makenonloopmasks()
    illegals = {((1, 0), (0, 1)), ((0, 1), (1, 0)), ((1, 1), (1, 1)), ((0, 0), (0, 0))}
    sidewalk3x3 = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]

    def __init__(self, w, h, generate=True):
        # grid size includes exterior edge
        self.w = w
        self.h = h
        self.area = w * h
        self.odd = w % 2 == 1 and h % 2 == 1

        self.whiteUnconnectedCount = 0  # counted in positive
        self.whiteUnconnectedDict = dict()
        self.blackUnconnectedCount = 0  # counted in negative
        self.blackUnconnectedDict = dict()

        """<=1  white, -1 = base black, >=-1 black, 0 = empty"""
        self.grid:list[list[int]] | None = None

        if generate:
            self._init()

    def _init(self):
        self.blackUnconnectedCount -= 1
        self.blackUnconnectedDict[self.blackUnconnectedCount] = self.blackUnconnectedCount
        self.grid = [[0 for y in range(self.h)] for x in range(self.w)]

        for x in range(self.w):
            self.grid[x][0] = -1
            self.grid[x][self.h - 1] = -1
        for y in range(self.h):
            self.grid[0][y] = -1
            self.grid[self.w - 1][y] = -1

    def copy(self):
        grid =  Grid(self.w, self.h, False)
        grid.grid = deepcopy(self.grid)

        grid.whiteUnconnectedDict = self.whiteUnconnectedDict.copy()
        grid.whiteUnconnectedCount = self.whiteUnconnectedCount

        grid.blackUnconnectedDict = self.blackUnconnectedDict.copy()
        grid.blackUnconnectedCount = self.blackUnconnectedCount

        return grid

    def at(self, x, y):
        """
        return virtual group, real grid group
        """
        conn = self.grid[x][y]
        color = self.connToBWE(conn)
        virtual = self.blackUnconnectedDict.get(conn, conn) if color == BLACK else self.whiteUnconnectedDict.get(conn, conn)
        return virtual, conn

    def set(self, xy, value):
        self.grid[xy[0]][xy[1]] = value

    def checkselfloopconection(self, xy, black=True):
        """
        return true if conn color would not create a loop, else false
        """
        connpoints:dict[int, set[tuple[int, int]]] = dict()

        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3):
            ox, oy = oxy
            cx, cy = x + ox, y + oy
            conn = self.at(cx, cy)[0]
            if (black and conn <= -1) or (not black and conn >= 1):
                if conn not in connpoints:
                    connpoints[conn] = {(ox + 1, oy + 1),}
                else:
                    connpoints[conn].add((ox+1, oy+1))

        for points in connpoints.values():
            mask = tuple(tuple((1 if (x, y) in points else 0) for x in range(3)) for y in range(3))

            if mask not in self.nonloopmasks:
                return False

        return True

    def checksubgrids(self, xy, black:bool):
        """
        return true if conn color legal in subgrid else false
        """
        conn = self.grid[xy[0]][xy[1]]
        self.set(xy, -1 if black else 1)

        x, y = xy
        offsets = ((-1, -1), (0, -1), (-1, 0), (0, 0))
        for offset in offsets:
            ox, oy = offset
            cx, cy = x+ox, y+oy
            subgrid = ((self.connToBWE(self.at(cx, cy)[0]), self.connToBWE(self.at(cx+1, cy)[0])),
                       (self.connToBWE(self.at(cx, cy+1)[0]), self.connToBWE(self.at(cx+1, cy+1)[0])))

            if subgrid in self.illegals:
                self.set(xy, conn)
                return False

        self.set(xy, conn)
        return True

    @staticmethod
    def connToBWE(conn):
        """
        white = 1, black = 0, empty = -1
        """
        if conn >= 1:
            return WHITE
        elif conn <=-1:
            return BLACK
        else: # == 0
            return EMPTY

    def tryPlaceBW(self, xy, color, recursive=False):
        """
        white = 1, black = 0
        """
        def recurs(xy):
            x, y = xy
            for offset in self.sidewalk3x3:
                ox, oy = offset
                cx, cy = x+ox, y+oy
                cxy = cx, cy

                if self.at(cx, cy)[0]==0:
                    black = self.checksubgrids(cxy, black=True)
                    white = self.checksubgrids(cxy, black=False)

                    if white and not black:
                        if not self.tryPlaceBW(cxy, WHITE, True):
                            #raise Exception("shouldnt happen")
                            return False
                    elif black and not white:
                        if not self.tryPlaceBW(cxy, BLACK, True):
                            #raise Exception("shouldnt happen")
                            return False
                    elif not self.checkselfloopconection(cxy, black=True):
                        if not self.tryPlaceBW(cxy, WHITE, True):
                            #raise Exception("shouldnt happen")
                            return False
                    elif not self.checkselfloopconection(cxy, black=False):
                        if not self.tryPlaceBW(cxy, BLACK, True):
                            #raise Exception("shouldnt happen")
                            return False
            return True

        def placeBW(xy, color):
            conn = self.connToBWE(self.at(*xy)[0])
            if conn == color:
                return True
            if conn != EMPTY:
                return False

            if self.checksubgrids(xy, black=color == BLACK) and self.checkselfloopconection(xy, black=color == BLACK):
                self.placecolor(xy, color)
                return True
            return False

        empty = self.at(*xy)[0]==0
        recu = True

        res = placeBW(xy, color)
        if recursive and empty and res:
            recu = recurs(xy)

        return res and recu

    def placecolor(self, xy, color):
        connection = self.checkconnections(xy, black=color == BLACK)

        if connection is not None:  # found connection, connect everything
            self.set(xy, connection)
            self.connectCons(xy)

        else:  # new unconnected created
            if color == WHITE:
                self.whiteUnconnectedCount += 1
                self.whiteUnconnectedDict[self.whiteUnconnectedCount] = self.whiteUnconnectedCount
                self.set(xy, self.whiteUnconnectedCount)
            else:
                self.blackUnconnectedCount -= 1
                self.blackUnconnectedDict[self.blackUnconnectedCount] = self.blackUnconnectedCount
                self.set(xy, self.blackUnconnectedCount)

    def connectCons(self, xy):
        conn = self.at(*xy)[0]
        color = min(max(conn, -1), 1)
        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3):
            ox, oy = oxy[0]+x, oxy[1]+y
            unconn = self.at(ox, oy)
            if min(max(unconn[0], -1), 1) == color and unconn[0]!=conn:
                if self.connToBWE(conn) == BLACK:
                    for ck, v in self.blackUnconnectedDict.items():
                        if v == unconn[0]:
                            self.blackUnconnectedDict[ck] = conn
                else:
                    for ck, v in self.whiteUnconnectedDict.items():
                        if v == unconn[0]:
                            self.whiteUnconnectedDict[ck] = conn

    def checkconnections(self, xy, black):
        """
        return related to color: closest to 0 conn int if any else None
        """
        unconnected = set()
        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3):
            ox, oy = oxy
            conn = self.at(x + ox, y + oy)[0]
            if (black and conn <= -1) or (not black and conn >= 1):
                    unconnected.add(conn)

        return (max(unconnected) if black else min(unconnected)) if unconnected else None

    def printgrid(self, snake:Snake=None, food:Cell=None):
        print("White dict:", self.whiteUnconnectedDict)
        print("Black dict:", self.blackUnconnectedDict)
        p = " " if self.h >= 10 else ""
        print("-virtual" + "-" * (self.w * 3 + 2-8) +p+ "    -real conn" + "-" * (self.w * 3 + 2-10))
        for y in range(self.h):
            print("|", end="")
            for x in range(self.w):
                scell = ""
                if snake is not None:
                    if food.eq(x - 1, y - 1): scell = "⁼"
                    if f"({x-1}, {y-1})" in snake.cells:
                        scell = "°"
                        if snake.head.eq(x-1, y-1): scell = "⁰"
                        if snake.tail.eq(x-1, y-1): scell = "•"
                print(f"{scell}{self.at(x, y)[0]:>{3-len(scell)-(not x)}}", end='')
            print(f" |{y:<{1+(self.h >= 10)}}", end="   ")

            print("|", end="")
            for x in range(self.w):
                print(f"{self.at(x, y)[1]:>2}", end=' ')
            print(f"|{y:<{1+(self.h >= 10)}}", end="")

            print()
        print("-" * (self.w * 3 + 2) +p+ "    " + "-" * (self.w * 3 + 2))

        for x in range(self.w):
            print(f" {x:>2}", end="")
        print("      "+p, end="")
        for x in range(self.w):
            print(f" {x:>2}", end="")

        print()
        print()


class Node:
    finished = None
    best = None

    def __init__(self):
        self.satisfied = False
        self.depth = 0
        self.children = dict()
        self.hScore = float("inf")
        self.gScore = float("inf")
        self.fScore = float("inf")
        self.camefrom = None

    def neighbors(self, seen):
        return self.children.keys()

    def key(self):
        return self

    def distance(self, node):
        return self.children[node]

    def failpoint(self, openSetSize, gScoreSize, checks):
        return False

    def __lt__(self, other):
        return self.fScore < other.fScore

    @classmethod
    def A_star(cls, start, goal, first=False, depthlimit=0, includeStart=True):

        def generate_path(node):
            path = deque([node])
            cls.finished = node

            while node.camefrom is not None:
                node = node.camefrom
                path.appendleft(node)

            if not includeStart:
                path.popleft()

            return path

        openSet = []
        heapq.heappush(openSet, start)

        gScore = dict()
        gScore[start.key()] = 0

        checks = 0

        while openSet:
            checks += 1
            current: Node = heapq.heappop(openSet)
            cls.best = current

            if current.failpoint(len(openSet), len(gScore), checks): break

            if current.satisfied or current is goal or (depthlimit != 0 and current.depth>=depthlimit):
                return generate_path(current)

            for neighbor in current.neighbors(gScore):
                neighbor: Node
                neighbor.depth = current.depth+1
                tentative_gScore = gScore.get(current.key(), float("inf")) + current.distance(neighbor)

                if tentative_gScore < gScore.get(neighbor.key(), float("inf")):
                    neighbor.camefrom = current
                    gScore[neighbor.key()] = tentative_gScore
                    neighbor.gScore = tentative_gScore
                    neighbor.fScore = tentative_gScore + neighbor.hScore

                    if first and (neighbor.satisfied or neighbor is goal):
                        return generate_path(neighbor)

                    if neighbor not in openSet:
                        heapq.heappush(openSet, neighbor)

        cls.finished = None
        return None

class Step(Node):

    def __init__(self, snake, grid, dir, move, target):
        super().__init__()

        self.snake: Snake = snake
        self.grid: Grid = grid
        self.dir: Cell = dir if dir is not None else self.snake.direction
        self.target: Cell = target

        self.generated = False

        if move:
            self.snake.applydir(dir)

        self.hScore = self.target.distManhattan(self.snake.head)

        if self.hScore == 0:
            self.satisfied = True

    def neighbor(self, leftturn, seen):
        """
        white = 1, black = 0
        forwardmasks = ((1, 0),
                        (1, 0))
        leftmasks = ((0, 0),
                     (1, 0))
        rightmasks = ((1, 1),
                      (1, 0))
        """

        dir = self.dir
        if leftturn is not None:
            if leftturn:
                dir = Cell.leftturn(dir)
            if not leftturn:
                dir = Cell.rightturn(dir)
        #dirnum = Cell.dirtonum(dir)
        basedirnum = Cell.dirtonum(self.dir)

        if self.snake.lookat(self.snake.nexthead(dir)) != Snake.BODY:
            #self.grid.printgrid()
            #print(self.snake.head)

            backleftpos = self.celldirgridconverter(self.snake.head, basedirnum, 0)
            atbackleft = self.grid.connToBWE(self.grid.at(*backleftpos)[0])
            if atbackleft==EMPTY:
                raise Exception("no left color")
            invert = atbackleft == BLACK

            frontleftpos = self.celldirgridconverter(self.snake.head, basedirnum, 1)
            frontrightpos = self.celldirgridconverter(self.snake.head, basedirnum, 2)

            grid = Grid(self.grid.w, self.grid.h)
            if self.gridsnakecopy(grid, invert):

                if leftturn is None:
                    turnmask = (WHITE, BLACK)
                elif leftturn:
                    turnmask = (BLACK, BLACK)
                else:
                    turnmask = (WHITE, WHITE)

                if grid.tryPlaceBW(frontleftpos, turnmask[0] if not invert else not turnmask[0], True):
                    if grid.tryPlaceBW(frontrightpos, turnmask[1] if not invert else not turnmask[1], True):
                        snake = Snake.copy(self.snake)
                        snake.applydir(dir)

                        #grid.printgrid(snake, self.target)
                        #print(snake.head)

                        self.children[Step(snake, grid, dir, False, self.target)] = 1

    def celldirgridconverter(self, cell, basedirnum, i):
        """
        i = 0 backleft, i = 1 frontleft, i = 2 frontright, i = 3 backright
        """
        offsets = ((1, 1), (0, 1), (0, 0), (1, 0))
        offset = offsets[(basedirnum+i)%4]

        return cell.x+offset[0], cell.y+offset[1]

    def gridsnakecopy(self, grid, invert):
        body0 = iter(self.snake)
        body1 = iter(self.snake)
        prevdirnum = None
        next(body0)
        next(body1)
        next(body1)

        while (cell0 := next(body0, None)) is not None:
            cell1 = next(body1, None)
            if cell1 is None:
                break

            dirnum = Cell.dirtonum(cell0.dirto(cell1))
            if prevdirnum is not None and prevdirnum != dirnum:
                leftturn = (prevdirnum+3)%4==dirnum
                backcornerpos = self.celldirgridconverter(cell0, dirnum, 3 if leftturn else 0)
                if not grid.tryPlaceBW(backcornerpos, (not leftturn) if not invert else leftturn, True):
                    #raise Exception("not possible")
                    return False

            prevdirnum = dirnum
            frontleftpos = self.celldirgridconverter(cell0, dirnum, 1)
            frontrightpos = self.celldirgridconverter(cell0, dirnum, 2)

            if not grid.tryPlaceBW(frontleftpos, WHITE if not invert else BLACK, True):
                #raise Exception("not possible")
                return False

            if not grid.tryPlaceBW(frontrightpos, BLACK if not invert else WHITE, True):
                #raise Exception("not possible")
                return False

        return True

    def neighbors(self, seen):
        if self.generated: return self.children.keys()
        self.generated = True

        self.neighbor(None, seen)
        self.neighbor(True, seen)
        self.neighbor(False, seen)

        return self.children.keys()

    def key(self):
        return self

    def __lt__(self, other):
        hcomp = compls(self.hScore, other.hScore)
        if hcomp!=0: return hcomp>0

        gcomp = compls(self.gScore, other.gScore)
        if gcomp != 0: return gcomp > 0

        dcomp = compls(self.depth, other.depth)
        return dcomp > 0

    def failpoint(self, openSetSize, gScoreSize, checks):
        fail = checks > self.snake.w*self.snake.h * 200
        if fail:
            print("fail point reached!")
            pass
        return fail


def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
