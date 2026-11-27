import heapq
from copy import deepcopy
from collections import deque
import pygame

from board import Board, Cell, Snake
from baseagent import BaseAgent

BLACK = 0
WHITE = 1
EMPTY = -1

class ReverseBWAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.steps = []
        self.iter = 0

        self.grid = Grid(self.w + 1, self.h + 1)

    def getDirection(self):

        if self.iter == len(self.steps):
            self.iter = 0
            guideorigin = CellStep(self.snake.head.copy(), self.snake, None, self.food)
            guidesteps = CellStep.A_star(guideorigin, None, True, 0, True)
            if guidesteps is None:
                #raise Exception("No steps guide found, not possible")
                print("No steps guide found, not possible")
                return Cell.reversedir(self.snake.direction)

            guidesteps.reverse()
            guidelen = len(guidesteps)
            guidecells = {cell.pos.toTuple(): guidelen-k-1 for k, cell in enumerate(guidesteps)}

            #print(guidecells)
            #print(self.snake.cellindexes)

            origin = ReverseBWStep(self.food.copy(), self.snake, Grid(self.w + 1, self.h + 1), guidecells, None, self.snake.head.copy(), None, None)
            origin.startneighbors()
            steps:deque[ReverseBWStep] = ReverseBWStep.A_star(origin, None, True, 0, True)
            if steps is None:
                #raise Exception("No steps found, not possible")
                print("No steps found, not possible")
                print(list(k for k in reversed(guidecells.keys())))
                self.grid = Node.best.grid
                steps = Node.generate_path(Node.best, True)
                steps.popleft()
                self.steps = list(Cell.reversedir(step.dir) for step in reversed(steps))
                return Cell.reversedir(self.snake.direction)

            steps.popleft()

            print(list(k for k in reversed(guidecells.keys())))
            print(list(step.pos for step in reversed(steps)))
            print(list(Cell.reversedir(step.dir) for step in reversed(steps)))
            print(list(step.camefrom.hScore - step.hScore for step in steps))
            print()

            self.steps = list(Cell.reversedir(step.dir) for step in reversed(steps))
            self.grid = Node.finished.grid


        dir = self.steps[self.iter]
        self.iter += 1

        return dir

    def draw_debug(self, screen, tlcorner, cellsize, w, h):
        arearect = pygame.Rect(tlcorner[0], tlcorner[1], w * cellsize, h * cellsize)
        for x in range(w + 1):
            for y in range(h + 1):
                rect = pygame.Rect(tlcorner.x + x * cellsize - cellsize / 2, tlcorner.y + y * cellsize - cellsize / 2,
                                   cellsize, cellsize)
                rect.scale_by_ip(0.6, 0.6)
                rect = rect.clip(arearect)

                if (cell := Grid.connToBWE(self.grid.at(x, y)[0])) != EMPTY:
                    color = "Red"
                    if cell == WHITE:
                        color = "White"
                    elif cell == BLACK:
                        color = "Black"
                    pygame.draw.rect(screen, color, rect)

        if self.steps:
            orinin =self.snake.head if self.iter == len(self.steps) else self.food
            prev = orinin.copy()-self.steps[-1]
            pos = orinin.copy()
            nextpos = None
            for k in reversed(range(0, len(self.steps)-1)):
                self.drawarrows(screen, pygame.Rect(tlcorner.x + pos.x * cellsize, tlcorner.y + pos.y * cellsize, cellsize, cellsize), prev, pos, nextpos)
                nextpos = pos
                pos = prev
                prev = prev.copy() - self.steps[k]

            self.drawarrows(screen, pygame.Rect(tlcorner.x + pos.x * cellsize, tlcorner.y + pos.y * cellsize, cellsize, cellsize), prev, pos, nextpos)
            nextpos = pos
            pos = prev
            prev = None
            self.drawarrows(screen, pygame.Rect(tlcorner.x + pos.x * cellsize, tlcorner.y + pos.y * cellsize, cellsize, cellsize), prev, pos, nextpos)

    COLOR = (163, 73, 164, 255)
    @staticmethod
    def drawarrows(screen, rect, prev, pos, nextpos):
        w, h = round(rect.w * (1 / 10)), round(rect.h * (1 / 10))
        center = pygame.Rect(0, 0, w, h)
        center.center = rect.center

        if prev is not None:
            prev = Cell(*prev)
        pos = Cell(*pos)
        if nextpos is not None:
            nextpos = Cell(*nextpos)

        if prev is not None:
            prevR = center.copy()
            prevR.move_ip(*(pos.dirto(prev) * (rect.w / 2.5)))
            pygame.draw.rect(screen, ReverseBWAgent.COLOR, prevR.union(center))

        if nextpos is not None:
            nextposR = center.copy()
            nextdirrot = Cell.dirtonum(pos.dirto(nextpos)) * 90
            nextposR.move_ip(*(pos.dirto(nextpos) * (rect.w / 4)))
            pygame.draw.rect(screen, ReverseBWAgent.COLOR, nextposR.union(center))

            center = pygame.Vector2(rect.center)
            arrowhead = pygame.Vector2(-round(rect.w * 0.45), 0).rotate(nextdirrot) + center
            arrowleft = pygame.Vector2(-round(rect.w * 0.245), round(rect.h * 0.20)).rotate(nextdirrot) + center
            arrowright = pygame.Vector2(-round(rect.w * 0.245), -round(rect.h * 0.20)).rotate(nextdirrot) + center
            pygame.draw.polygon(screen, ReverseBWAgent.COLOR, (arrowhead, arrowleft, arrowright))

        if prev is not None and nextpos is None:
            pygame.draw.circle(screen, ReverseBWAgent.COLOR, rect.center, (rect.w * 0.17))

        if prev is None and nextpos is not None:
            pygame.draw.circle(screen, ReverseBWAgent.COLOR, rect.center, (rect.w * 0.14))


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

    @staticmethod
    def generate_path(node, includeStart=True):
        path = deque([node])
        Node.finished = node

        while node.camefrom is not None:
            node = node.camefrom
            path.appendleft(node)

        if not includeStart:
            path.popleft()

        return path

    @classmethod
    def A_star(cls, start, goal, first=False, depthlimit=0, includeStart=True):
        openSet = []
        heapq.heappush(openSet, start)

        gScore = dict()
        gScore[start.key()] = 0

        checks = 0

        while openSet:
            checks += 1
            current: Node = heapq.heappop(openSet)
            Node.best = current

            if current.failpoint(len(openSet), len(gScore), checks): break

            if current.satisfied or current is goal or (depthlimit != 0 and current.depth>=depthlimit):
                return Node.generate_path(current, includeStart)

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
                        return Node.generate_path(neighbor, includeStart)

                    if neighbor not in openSet:
                        heapq.heappush(openSet, neighbor)

        Node.finished = None
        return None


class CellStep(Node):

    def __init__(self, pos, snake, dir, target, beenthere=None, grid=None):
        super().__init__()

        self.pos: Cell = pos
        self.snake: Snake = snake
        self.dir: Cell = dir if dir is not None else self.snake.direction
        self.target: Cell = target
        self.beenthere:set = beenthere.copy() if beenthere is not None else set()
        self.beenthere.add(self.pos.toTuple())
        self.grid = grid

        self.generated = False

        self.hScore = self.target.distManhattan(self.pos)

        if self.hScore == 0:
            self.satisfied = True

    def neighbor(self, leftturn, seen):
        dir = self.dir
        if leftturn is not None:
            if leftturn:
                dir = Cell.leftturn(dir)
            if not leftturn:
                dir = Cell.rightturn(dir)

        nextpos = self.pos.copy()+dir
        if ((self.snake.lookat(nextpos) != Snake.BODY and nextpos.toTuple() not in self.beenthere)
                or (self.snake.getcellindex(nextpos) <= self.depth and self.snake.in_cells(nextpos))):

            self.children[CellStep(nextpos, self.snake, dir, self.target, self.beenthere, self.grid)] = 1

    def neighbors(self, seen):
        #print("d", self.depth, " f", self.fScore, "g ",  self.gScore, " h ", self.hScore)
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

                    if not white and not black:
                        return False

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


class ReverseBWStep(Node):

    def __init__(self, pos,  snake, grid, guide,  dir, target, beenthere=None, hScore=None):
        super().__init__()

        self.pos:Cell = pos
        self.snake: Snake = snake
        self.grid: Grid = grid
        self.guide: dict[tuple[int, int], int] = guide
        self.dir: Cell = dir
        self.target: Cell = target
        self.beenthere: set = beenthere.copy() if beenthere is not None else set()
        self.beenthere.add(self.pos.toTuple())

        self.generated = False

        self.hScore = hScore
        if self.hScore is None:
            closest = None
            dist = float("inf")
            for cell in self.guide.keys():
                if (d:=Cell.distManhattan(self.pos, Cell(*cell))) < dist:
                    dist = d
                    closest = cell
            self.hScore = self.guide[closest]+dist

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
        if leftturn is None:
            turnmask = (WHITE, BLACK)
        elif leftturn:
            turnmask = (BLACK, BLACK)
        else:
            turnmask = (WHITE, WHITE)

        dir = self.dir
        if leftturn is not None:
            if leftturn:
                dir = Cell.leftturn(dir)
            if not leftturn:
                dir = Cell.rightturn(dir)
        #dirnum = Cell.dirtonum(dir)
        basedirnum = Cell.dirtonum(self.dir)

        nextpos = self.pos.copy() + dir

        closest = None
        dist = float("inf")
        for cell in self.guide.keys():
            if (d := Cell.distManhattan(nextpos, Cell(*cell))) < dist:
                dist = d
                closest = cell
        hScore = self.guide[closest] + dist

        if self.hScore-hScore >= 3:
            return
        #print(self.hScore-hScore)

        if (((notbeenthere:=nextpos.toTuple() not in self.beenthere) and self.snake.lookat(nextpos) != Snake.BODY)
            or (notbeenthere and self.snake.getcellindex(nextpos) <= hScore and self.snake.in_cells(nextpos)) or hScore == 0):

            if self.depth < len(self.snake):

                frontleftpos = self.celldirgridconverter(self.pos, basedirnum, 1)
                frontrightpos = self.celldirgridconverter(self.pos, basedirnum, 2)

                backleftpos = self.celldirgridconverter(self.pos, basedirnum, 0)
                atbackleft = self.grid.connToBWE(self.grid.at(*backleftpos)[0])
                if atbackleft == EMPTY:
                    raise Exception("no back left color")
                invert = atbackleft == BLACK

                grid: Grid = self.grid.copy()
                if grid.tryPlaceBW(frontleftpos, turnmask[0] if not invert else not turnmask[0], True):
                    if grid.tryPlaceBW(frontrightpos, turnmask[1] if not invert else not turnmask[1], True):

                        if hScore == 0 and (lendiff:=(len(self.snake)-1-self.depth)): # overlapping long snake check
                            if not self.overlapcheck(self.pos, grid, lendiff):
                                return

                        self.children[ReverseBWStep(nextpos, self.snake, grid, self.guide, dir, self.target, self.beenthere, hScore)] = 1

            else:
                self.children[ReverseBWStep(nextpos, self.snake, self.grid, self.guide, dir, self.target, self.beenthere, hScore)] = 1

    def overlapcheck(self, pos, grid, lendiff):
        prev:Cell = pos
        nextiter = reversed(self.snake.snake)
        next(nextiter)

        for cell in reversed(self.snake.snake):
            if lendiff <= 0:
                break
            lendiff -= 1
            cell = Cell(*cell)
            nextcell = Cell(*next(nextiter))


            basedirnum = Cell.dirtonum(prev.dirto(cell))
            nextdirnum = Cell.dirtonum(cell.dirto(nextcell))

            frontleftpos = self.celldirgridconverter(cell, basedirnum, 1)
            frontrightpos = self.celldirgridconverter(cell, basedirnum, 2)

            backleftpos = self.celldirgridconverter(cell, basedirnum, 0)
            atbackleft = grid.connToBWE(grid.at(*backleftpos)[0])
            if atbackleft == EMPTY:
                raise Exception("no back left color")
            invert = atbackleft == BLACK

            if basedirnum == nextdirnum:
                turnmask = (WHITE, BLACK)
            elif (basedirnum+3)%4 == nextdirnum:
                turnmask = (BLACK, BLACK)
            else:
                turnmask = (WHITE, WHITE)

            passed = False
            if grid.tryPlaceBW(frontleftpos, turnmask[0] if not invert else not turnmask[0], True):
                if grid.tryPlaceBW(frontrightpos, turnmask[1] if not invert else not turnmask[1], True):
                    passed = True

            if not passed:
                return False

            prev = cell

        return True

    @staticmethod
    def celldirgridconverter(cell, basedirnum, i):
        """
        i = 0 backleft, i = 1 frontleft, i = 2 frontright, i = 3 backright
        """
        offsets = ((1, 1), (0, 1), (0, 0), (1, 0))
        offset = offsets[(basedirnum+i)%4]

        return cell.x+offset[0], cell.y+offset[1]

    def neighbors(self, seen):
        #print("d", self.depth, " f", self.fScore, "g ",  self.gScore, " h ", self.hScore)
        """if self.hScore ==1:
            self.grid.printgrid()
            print(self.pos, self.dir)
            self.camefrom.grid.printgrid()
            pass"""
        if self.generated: return self.children.keys()
        self.generated = True

        self.neighbor(None, seen)
        self.neighbor(True, seen)
        self.neighbor(False, seen)

        return self.children.keys()

    def startneighbors(self):
        if self.generated: return self.children.keys()
        self.generated = True
        turnmask = (WHITE, BLACK)

        for dir in range(4):
            direction = Cell.numtodir(dir)
            grid = self.grid.copy()
            frontleftpos = self.celldirgridconverter(self.pos, dir, 1)
            frontrightpos = self.celldirgridconverter(self.pos, dir, 2)
            for invert in (False, True):
                if grid.tryPlaceBW(frontleftpos, turnmask[0] if not invert else not turnmask[0], True):
                    if grid.tryPlaceBW(frontrightpos, turnmask[1] if not invert else not turnmask[1], True):

                        nextpos = self.pos.copy() + direction

                        closest = None
                        dist = float("inf")
                        for cell in self.guide.keys():
                            if (d := Cell.distManhattan(nextpos, Cell(*cell))) < dist:
                                dist = d
                                closest = cell
                        hScore = self.guide[closest] + dist

                        self.children[ReverseBWStep(nextpos, self.snake, grid, self.guide, direction, self.target, self.beenthere, hScore)] = 1

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
        fail = checks > self.snake.w*self.snake.h * 100
        if fail:
            print("fail point reached!")
            pass
        return fail


def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
