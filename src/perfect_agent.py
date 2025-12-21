import pygame
from collections import deque
import heapq

from board import Board
from snake import Snake
from cell import Cell
from baseagent import BaseAgent

class PerfectAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.grid = Grid(self.w, self.h).generatePath()

        self.falback = False
        self.steps = []
        self.iter = 0

        self.onpath = True
        self.onpathcheck(self.snake)

    def getDirection(self):
        self.grid.reroutefood(self.snake, self.food)

        if len(self.snake)==self.area-1 and self.snake.head.distManhattan(self.food) == 1:
            dir = self.snake.head.dirto(self.food)
            return dir

        if not self.onpath:
            dir = self.grid.nextdir(self.snake.head)
            if self.snake.nexthead(dir).toString() in self.snake.cells:
                dir = self.snake.head.dirto(self.grid.at(self.snake.head).prev)
                if self.snake.nexthead(dir).toString() in self.snake.cells:
                    dir = Cell.reversedir(self.grid.nextdir(self.snake.head))
                    if self.snake.nexthead(dir).toString() in self.snake.cells:
                        for n in self.snake.head.neighbors():
                            dir = self.snake.head.dirto(n)
                            if self.snake.nexthead(dir).toString() not in self.snake.cells:
                                break

            snake = self.snake.copy()
            snake.applydir(dir)
            if snake.head == self.food:
                snake.reatachtail()

            self.onpathcheck(snake)
            return dir

        if not self.falback and self.iter == len(self.steps):
            origin = Step(self.snake, self.grid, None, False, self.food)
            self.steps = Step.A_star(origin, None, True, 0, False)

            if self.steps is None:
                self.falback = True
                self.steps = []
            else:
                self.grid = Step.finished.grid

            self.iter = 0

        if not self.falback:
            dir = self.steps[self.iter].dir
            self.iter += 1

        else:
            self.grid.shortenroute(self.snake, self.food)
            dir = self.grid.nextdir(self.snake.head)

        if self.snake.nexthead(dir) == self.food:
            self.falback = False

        return dir

    def onpathcheck(self, snake):
        self.onpath = True
        start = self.grid.at(snake.head)
        for i in range(len(snake) - 1):
            start = self.grid.at(start.prev)
            if start.pos.toString() not in snake.cells:
                self.onpath = False
                break

        if not self.onpath:
            self.onpath = True
            start = self.grid.at(snake.head)
            for i in range(len(snake) - 1):
                start = self.grid.at(start.next)
                if start.pos.toString() not in snake.cells:
                    self.onpath = False
                    break
            if self.onpath:
                self.grid.reversePath()

    def draw_debug(self, screen, tlcorner, cellsize, w, h):
        for x in range(w):
            for y in range(h):
                self.grid.cells[x][y].draw(screen, pygame.Rect(tlcorner.x + x * cellsize, tlcorner.y + y * cellsize, cellsize, cellsize))

class Block:
    def __init__(self, x, y):
        self.pos: Cell = Cell(x, y)
        self.next: Cell|None = None
        self.prev: Cell|None = None

    def copy(self):
        block = Block(*self.pos)
        block.next = self.next
        block.prev = self.prev

        return block

    def set(self, prev: Cell, next: Cell):
        self.prev = prev
        self.next = next

    def flip(self):
        temp = self.next
        self.next = self.prev
        self.prev = temp

    def __str__(self):
        l = Cell.numtodir(0)
        u = Cell.numtodir(1)
        r = Cell.numtodir(2)
        d = Cell.numtodir(3)

        if self.next is None or self.prev is None: return " "

        p = self.prev.dirto(self.pos)
        n = self.pos.dirto(self.next)

        if p == l:
            if n == l: return "←"
            if n == u: return "↖"
            if n == d: return "↙"
        if p == r:
            if n == r: return "→"
            if n == u: return "↗"
            if n == d: return "↘"
        if p == u:
            if n == u: return "↑"
            if n == l: return "↖"
            if n == r: return "↗"
        if p == d:
            if n == d: return "↓"
            if n == l: return "↙"
            if n == r: return "↘"

        return " "

    COLOR = (163, 73, 164, 255)
    def draw(self, screen, rect):
        w, h = round(rect.w*(1/10)), round(rect.h*(1/10))
        center = pygame.Rect(0, 0, w, h)
        center.center = rect.center

        if self.prev is not None:
            prev = center.copy()
            prev.move_ip(*(self.pos.dirto(self.prev)*(rect.w/2.5)))
            pygame.draw.rect(screen, Block.COLOR, prev.union(center))

        if self.next is not None:
            next = center.copy()
            nextdirrot = Cell.dirtonum(self.pos.dirto(self.next))*90
            next.move_ip(*(self.pos.dirto(self.next)*(rect.w/4)))
            pygame.draw.rect(screen, Block.COLOR, next.union(center))

            center = pygame.Vector2(rect.center)
            arrowhead = pygame.Vector2(-round(rect.w*0.45), 0).rotate(nextdirrot)+center
            arrowleft = pygame.Vector2(-round(rect.w*0.245), round(rect.h*0.20)).rotate(nextdirrot)+center
            arrowright = pygame.Vector2(-round(rect.w*0.245), -round(rect.h*0.20)).rotate(nextdirrot)+center
            pygame.draw.polygon(screen, Block.COLOR, (arrowhead, arrowleft, arrowright))

class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.area = w*h
        self.odd = w % 2 == 1 and h % 2 == 1

        self.illegals = set()
        self.cells: list[list[Block]]|None = None

    def generatePath(self):
        if self.odd:
            self.illegals.add( Cell(0, 0).toString())
            self.illegals.add( Cell(0, 1).toString())
            self.illegals.add( Cell(1, 0).toString())
            self.illegals.add( Cell(1, 1).toString())

        self.cells = [[Block(x, y) for y in range(self.h)] for x in range(self.w)]

        block = self.cells[0][0]
        while True:
            neighbors = block.pos.neighbors()
            dist = -1
            x = -1
            furthest = None
            for pos in neighbors:
                if 0 <= pos.x < self.w and 0 <= pos.y < self.h and self.at(pos).prev is None and (d:=pos.lengthSquared()) >= dist and pos.x>=x:
                    dist = d
                    x = pos.x
                    furthest = pos
            if furthest is None:
                break
            block.next = self.at(furthest).pos

            prev = block.pos
            block = self.at(furthest)
            block.prev = prev

        if self.odd and 1:
            self.cells[1][1].next = self.cells[1][0].pos
            self.cells[1][0].prev = self.cells[1][1].pos
            self.cells[0][0].prev = self.cells[0][1].pos

        return self

    def copy(self):
        grid = Grid(self.w, self.h)

        grid.illegals = self.illegals

        grid.cells = [[self.cells[x][y].copy() for y in range(self.h)] for x in range(self.w)]

        return grid

    def reversePath(self):
        for x in range(self.w):
            for y in range(self.h):
                self.cells[x][y].flip()

    def at(self, cell: Cell):
        return self.cells[cell.x][cell.y]

    def nextdir(self, cell: Cell):
        return cell.dirto(self.at(cell).next)


    def reroutefood(self, snake, food: Cell):
        if not self.odd: return

        foodblock: Block = self.at(food)

        if self.at(foodblock.prev).next==food: return

        shortest = None
        dist = self.area*2

        corners = (Cell(-1, -1), Cell(1, -1), Cell(-1, 1), Cell(1, 1))
        for c in corners:
            c += food
            if 0 <= c.x < self.w and 0 <= c.y < self.h:
                corner: Block = self.at(c)
                if corner.prev.distManhattan(food)==1 and corner.next.distManhattan(food)==1:
                    prevblock: Block = self.at(corner.prev)
                    prevblock.next = foodblock.pos
                    nextblock: Block = self.at(corner.next)
                    nextblock.prev = foodblock.pos
                    foodblock.set(prevblock.pos, nextblock.pos)

                    d = self.fooddistance(snake.head, food)
                    if d < dist:
                        dist = d
                        shortest = corner

                    prevblock.next = corner.pos
                    nextblock.prev = corner.pos

        if shortest is None:
            raise Exception("Couldn't reroute food")

        prevblock: Block = self.at(shortest.prev)
        prevblock.next = foodblock.pos
        nextblock: Block = self.at(shortest.next)
        nextblock.prev = foodblock.pos
        foodblock.set(prevblock.pos, nextblock.pos)

        self.illegals = set()
        self.illegals.add(food.toString())
        self.illegals.add(shortest.pos.toString())
        self.illegals.add(prevblock.pos.toString())
        self.illegals.add(nextblock.pos.toString())

    def fooddistance(self, start: Cell, food: Cell):
        dist = 0
        head = self.at(start)

        while head.pos!=food:
            head = self.at(head.next)
            if head.pos==start: return self.area*2
            dist += 1

        return dist

    def split(self,  snake: Snake|None, leftturn: bool, safegatepos: Cell|None):
        gate1 = None
        if snake is not None:
            gate1 = self.at(snake.head)
        if safegatepos is not None:
            gate1 = self.at(safegatepos)

        facing = gate1.pos.dirto(gate1.next)
        turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)

        gate2pos = gate1.pos.copy()+turning

        if not (0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h): return False

        gate2 = self.at(gate2pos)
        if snake is not None and (gate2.pos.toString() in snake.cells or gate2.prev.toString() in snake.cells or
                                  (gate1.next.toString() in snake.cells and gate1.next!=snake.tail)):
            return False

        if snake is not None and (gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                                  gate2.prev.toString() in self.illegals or gate1.next.toString() in self.illegals):
            return False

        if gate2.pos.dirto(gate2.prev)==facing:
            gate3 = self.at((cell:= gate1.pos.copy()+facing))
            gate4 = self.at(cell.copy()+turning)

            gate1.next = gate2.pos
            gate2.prev = gate1.pos

            gate3.prev = gate4.pos
            gate4.next = gate3.pos

            return True

        return False

    def unsplit(self,  snake: Snake|None, leftturn: bool, safegatepos: Cell|None):
        if not self.split(snake, not leftturn, safegatepos):
            raise Exception("Couldn't unsplit!")

    def joinaftersplit(self, snake: Snake, food: Cell, basedist: int, firstjoin=False):
        foodroute = set()
        gates = []
        gateturns = []

        gate1 = self.at(self.at(snake.head).next)
        snaketailnext = self.at(snake.tail).next
        while True:
            foodroute.add(gate1.pos.toString())
            facing = gate1.pos.dirto(gate1.next)
            for leftturn in (False, True):
                turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)
                gate2pos = gate1.pos.copy()+turning

                if 0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h:
                    gate2 = self.at(gate2pos)
                    illegal = False

                    if (gate2.pos.toString() in snake.cells or gate2.prev.toString() in snake.cells or
                        (gate1.next.toString() in snake.cells and gate1.next != snake.tail)):
                        illegal = True

                    if not illegal and (gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                                        gate2.prev.toString() in self.illegals or gate1.next.toString() in self.illegals):
                        illegal = True

                    if not illegal and gate2.pos.dirto(gate2.prev)==facing:
                        gates.append(gate1)
                        gateturns.append(leftturn)

            if gate1.pos==snaketailnext: break
            gate1 = self.at(gate1.next)

        shortestgate = None
        shortestturn = None

        i = 0
        for gate1 in gates:
            facing = gate1.pos.dirto(gate1.next)
            turning = Cell.leftturn(facing) if gateturns[i] else Cell.rightturn(facing)
            gate2pos = gate1.pos.copy() + turning

            if gate2pos.toString() not in foodroute:
                gate2 = self.at(gate2pos)
                gate3 = self.at((cell := gate1.pos.copy() + facing))
                gate4 = self.at(cell.copy() + turning)

                gate1.next = gate2.pos
                gate2.prev = gate1.pos

                gate3.prev = gate4.pos
                gate4.next = gate3.pos

                dist = self.fooddistance(snake.head, food)
                if dist <= basedist:
                    basedist = dist
                    shortestgate = gate1
                    shortestturn = gateturns[i]

                    if firstjoin:
                        return True

                gate1.next = gate3.pos
                gate2.prev = gate4.pos

                gate3.prev = gate1.pos
                gate4.next = gate2.pos

            i += 1

        if shortestgate is not None:
            self.split(None, shortestturn, shortestgate.pos)
            return True

        return False

    def shortenroute(self, snake: Snake, food: Cell):
        basedist = self.fooddistance(snake.head, food)
        if basedist > self.area:
            raise Exception("Food not on route!")

        leftdist = self.area*2
        if self.split(snake, True, None):
            leftdist = self.fooddistance(snake.head, food)
            self.unsplit(None, True, snake.head)

        rightdist = self.area * 2
        if self.split(snake, False, None):
            rightdist = self.fooddistance(snake.head, food)
            self.unsplit(None, False, snake.head)

        if leftdist<basedist or rightdist<basedist:
            self.split(None, leftdist<rightdist, snake.head)

            if not self.joinaftersplit(snake, food, basedist, False):
                self.unsplit(None, leftdist<rightdist, snake.head)

                if max(leftdist, rightdist)<basedist:
                    self.split(None, not(leftdist < rightdist), snake.head)

                    if not self.joinaftersplit(snake, food, basedist, False):
                        self.unsplit(None, not(leftdist < rightdist), snake.head)

    def print(self, snake: Snake, food: Cell):
        print("/"+"--"*self.w+"\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "
                if food.eq(x, y): cell = "O"
                if f"({x}, {y})" in snake.cells: cell = "▮"
                if snake.head.eq(x, y): cell = "@"
                if snake.tail.eq(x, y): cell = "X"

                row += str(self.cells[x][y])+cell
            row += "|"
            print(row)

        print("\\" + "--" * self.w + "/")

class Node:
    finished = None

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
    def __init__(self, snake, grid, dir, move, target):
        super().__init__()

        self.dir: Cell = dir
        self.snake: Snake = snake
        self.grid: Grid = grid
        self.target: Cell = target

        if move:
            self.snake.applydir(dir)

        self.hScore = self.target.distManhattan(self.snake.head)

        if self.hScore == 0:
            self.satisfied = True

    def neighbor(self, leftturn, seen):
        if leftturn is None:
            grid = self.grid
        else:
            if self.grid.split(self.snake, leftturn, None):
                grid = self.grid.copy()
                self.grid.unsplit(None, leftturn, self.snake.head)
                if not grid.joinaftersplit(self.snake, self.target, float("inf"), True):
                    return
            else: return

        dir = grid.nextdir(self.snake.head)

        k = self
        if k not in seen or 1:
            snake = self.snake.copy()
            snake.applydir(dir)

            self.children[Step(snake, grid, dir, False, self.target)] = 1

    def neighbors(self, seen):
        if self.children: return self.children

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
        return checks > self.grid.area * 1.5

def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
