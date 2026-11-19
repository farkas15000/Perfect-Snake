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


    def getDirection(self):

        if self.iter == len(self.steps):
            self.iter = 0
            origin = CellStep(self.snake.head.copy(), self.snake, None, self.food)
            self.steps = CellStep.A_star(origin, None, True, 0, False)
            #finished: Step = Step.finished
            #print(list(x.dir for x in self.steps))

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

                pass


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


class CellStep(Node):

    def __init__(self, pos, snake, dir, target):
        super().__init__()

        self.pos: Cell = pos
        self.snake: Snake = snake
        self.dir: Cell = dir if dir is not None else self.snake.direction
        self.target: Cell = target

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
        if (self.snake.lookat(nextpos) != Snake.BODY
                or (self.snake.getcellindex(nextpos) < self.depth and self.snake.in_cells(nextpos))):
            self.children[CellStep(nextpos, self.snake, dir, self.target)] = 1

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
        fail = checks > self.snake.w*self.snake.h * 2
        if fail:
            print("fail point reached!")
            pass
        return fail


def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
