import heapq
from collections import deque
import pygame

from board import Board, Cell, Snake
from baseagent import BaseAgent


def makenonloopmasks():
    masks = set()
    nonloopmasks = [[[1, 0, 0], [0, 1, 0], [0, 0, 0]]]
    nonloopmasks.extend([[a, 1, b], [0, 1, 0], [0, 0, 0]] for a in (0, 1) for b in (0, 1))
    nonloopmasks.extend([[a, 1, b], [0, 1, 1], [0, 0, c]] for a in (0, 1) for b in (0, 1) for c in (0, 1))
    nonloopmasks.extend([[a, 1, b], [0, 1, 1], [d, 1, c]] for a in (0, 1) for b in (0, 1) for c in (0, 1) for d in (0, 1))
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

        self.grid.set((1, 1), 1)
        self.grid.set((2, 1), 1)
        self.grid.printgrid()


        print(self.grid.tryBlackplace((5, 1)))
        self.grid.printgrid()

    def getDirection(self):

        if self.iter == len(self.steps):
            self.iter = 0
            origin = Step(self.snake.copy(), None, False, self.food)
            self.steps = Step.A_star(origin, None, True, 0, False)

            if self.steps is None:
                return Cell.reversedir(self.snake.direction)

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

                if (cell:= self.grid.at(x, y)[0]) != 0:
                    if cell == 1:
                        color = "White"
                    elif cell >= 2:
                        color = "Black"
                    else:
                        color = "Black"

                    pygame.draw.rect(screen, color, rect)

class Grid:
    """
    https://web.mit.edu/8.592/www/grades/projects/projects(2013)/MichaelCrossley.pdf
    """
    nonloopmasks = makenonloopmasks()
    illegals = {((1, 0), (0, 1)), ((0, 1), (1, 0)), ((1, 1), (1, 1)), ((0, 0), (0, 0))}
    sidewalk3x3 = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]

    def __init__(self, w, h):
        # grid size includes exterior edge
        self.w = w
        self.h = h
        self.area = w * h
        self.odd = w % 2 == 1 and h % 2 == 1

        self.unconnectedCount = 0  # counted in negative!
        self.unconnectedDict = {0: 0, }

        """0 = empty, 1 = white, >=2 =  black connected, <=-1 = black unconnected"""
        self.grid = [[0 for x in range(self.w)] for y in range(self.h)]

        for x in range(self.w):
            self.grid[x][0] = 2
            self.grid[x][self.h-1] = 2
        for y in range(self.h):
            self.grid[0][y] = 2
            self.grid[self.w-1][y] = 2

    def at(self, x, y):
        """
        return virtual group, real grid group
        """
        conn = self.grid[x][y]
        if conn in self.unconnectedDict:
            return self.unconnectedDict[conn], conn
        else:
            return conn, conn

    def set(self, xy, value):
        self.grid[xy[0]][xy[1]] = value

    def checkselfloopconection(self, xy, black=True):
        """
        return true if conn color would not create a loop, else false
        """
        connpoints = dict()

        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3):
            ox, oy = oxy
            cx, cy = x + ox, y + oy
            conn = self.at(cx, cy)[0]
            if (black and (conn < 0 or conn > 1)) or (not black and conn == 1):
                if conn not in connpoints:
                    connpoints[conn] = [(ox+1, oy+1)]
                else:
                    connpoints[conn].append((ox+1, oy+1))

        for points in connpoints.values():
            mask = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
            for point in points:
                mask[point[0]][point[1]] = 1

            mask = tuple(tuple(tuple(x for x in row) for row in mask))

            if mask not in self.nonloopmasks:
                return False

        return True

    def checksubgrids(self, xy, black:bool):
        """
        return true if legal in subgrid else false
        """
        conn = self.at(xy[0], xy[1])[0]
        self.set((xy[0], xy[1]), 2 if black else 1)

        x, y = xy
        offsets = ((-1, -1), (0, -1), (-1, 0), (0, 0))
        for offset in offsets:
            ox, oy = offset
            cx, cy = x+ox, y+oy
            subgrid = ((self.conToBWE(self.at(cx, cy)[0]), self.conToBWE(self.at(cx+1, cy)[0])),
                       (self.conToBWE(self.at(cx, cy+1)[0]), self.conToBWE(self.at(cx+1, cy+1)[0])))

            if subgrid in self.illegals:
                self.set((xy[0], xy[1]), conn)
                return False

        self.set((xy[0], xy[1]), conn)
        return True

    def conToBWE(self, conn):
        if conn == 1:
            return 0
        elif conn == 0:
            return -1
        else:
            return 1

    def tryWhiteplace(self, xy):
        if self.at(xy[0], xy[1])[0] == 1:
            return True

        if self.checksubgrids(xy, black=False) and self.checkselfloopconection(xy, black=False):
            self.whiteplace(xy)
            return True
        return False

    def whiteplace(self, xy):
        self.set(xy, 1)

    def tryBlackplace(self, xy):
        if (cell:=self.at(xy[0], xy[1])[0]) != 0 and cell != 1:
            return True

        if self.checksubgrids(xy, black=True) and self.checkselfloopconection(xy, black=True):
            self.blackplace(xy)
            return True
        return False

    def blackplace(self, xy):

        self.set(xy, 1)
        excheck = self.checkexternalconnections(xy)
        if not excheck[0]:
            raise Exception("Not possible, boundary connections merge", xy)

        if excheck[1] is not None: # found connection, connect everything
            self.set(xy, excheck[1])
            self.connectCons(xy)

        elif excheck[3] is not None: # found unconnections, connect them
            self.set(xy, excheck[3])
            self.connectCons(xy)

        else: # new unconnected created
            self.unconnectedCount -= 1
            self.unconnectedDict[self.unconnectedCount] = self.unconnectedCount

            self.set(xy, self.unconnectedCount)

    def connectCons(self, xy):
        conn = self.at(*xy)[0]
        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3):
            ox, oy = oxy[0]+x, oxy[1]+y
            unconn = self.at(ox, oy)
            if unconn[0] < 0 and unconn[0]!=conn:
                for ck, v in self.unconnectedDict.items():
                    if v == unconn[0]:
                        self.unconnectedDict[ck] = conn

    def checkexternalconnections(self, xy, cross=False):
        """
        return tuple(true if conns <2, conn int if only 1 else None, true if all unconns unique, max unconn int if any)
        """
        connections = set()
        unconnections = []
        x, y = xy
        for k, oxy in enumerate(self.sidewalk3x3 if not cross else ((0, -1), (-1, 0), (0, 1), (1, 0))):
            ox, oy = oxy
            conn = self.at(x + ox, y + oy)[0]
            if conn >= 2:
                connections.add(conn)
            elif conn < 0:
                    unconnections.append(conn)

        connectionslen = len(connections)
        unconnectionslen = len(unconnections)
        return (connectionslen<2, connections.pop() if connectionslen == 1 else None,
                unconnectionslen == len(set(unconnections)), max(unconnections) if unconnectionslen else None)

    def printgrid(self):
        print("-" * (self.w * 3 + 2))
        for x in range(self.w):
            print("|", end="")
            for y in range(self.h):
                print(f"{self.at(y, x)[0]:>2}", end=' ')
            print(f"|{x}", end="")

            print()
        print("-" * (self.w * 3 + 2))

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
            current: cls = heapq.heappop(openSet)
            cls.best = current

            if current.failpoint(len(openSet), len(gScore), checks): break

            if current.satisfied or current is goal or (depthlimit != 0 and current.depth>=depthlimit):
                return generate_path(current)

            for neighbor in current.neighbors(gScore):
                neighbor: cls
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
    def __init__(self, snake, dir, move, target):
        super().__init__()

        self.snake: Snake = snake
        self.dir: Cell = dir if dir is not None else self.snake.direction
        self.target: Cell = target

        self.generated = False

        if move:
            self.snake.applydir(dir)

        self.hScore = self.target.distManhattan(self.snake.head)

        if self.hScore == 0:
            self.satisfied = True

    def neighbor(self, leftturn, seen):
        dir = self.dir
        if leftturn is not None:
            if leftturn:
                dir = Cell.leftturn(dir)
            if not leftturn:
                dir = Cell.rightturn(dir)

        if self.snake.lookat(self.snake.nexthead(dir)) != Snake.BODY:
            snake = Snake.copy(self.snake)
            snake.applydir(dir)

            self.children[Step(snake, dir, False, self.target)] = 1

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
        return checks > self.snake.w*self.snake.h * 2


def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
