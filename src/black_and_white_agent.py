import heapq
from collections import deque

from board import Board, Cell, Snake
from baseagent import BaseAgent

class BWAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.steps = []
        self.iter = 0

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
