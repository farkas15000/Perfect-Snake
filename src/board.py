import traceback
from collections import deque
import random
import sys

class Board:
    def __init__(self, w, h, snake, seed=None):
        self.w: int = w
        self.h: int = h
        self.area: int = w*h
        Snake.w = w
        Snake.h = h

        self.seed = seed
        random.seed(self.seed if self.seed!=0 else None)
        self.steps = 0
        self.timeout = int(self.area*2.5)

        self.snake: Snake = snake
        self.lastdir = self.snake.tail.dirto(self.snake.head)

        self.food: Cell|None = None
        self.spawnfood()

        print("Starting")
        print("Seed:", self.seed, "W:", self.w, "H:", self.h, "Head:", self.snake.head, "Tail:", self.snake.tail)
        print()

    def update(self, agent):
        try:
            dir = agent.getDirection()

        except Exception:
            print("Step:", str(self.steps), "Error!")
            print()
            print(traceback.format_exc(), file=sys.stderr)
            exit(1)

        if not dir.isdir():
            print("Step:", str(self.steps), "| Invalid direction!")
            return -1

        if self.timeout<=0:
            print("Step:", str(self.steps), "| Time out, no food eaten in time!")
            return -1

        self.lastdir = dir

        if self.snake.lookat(self.snake.nexthead(dir)) == Snake.BODY:
            print("Step:", str(self.steps), "| Died, hit wall or tail!")
            return -1

        self.snake.applydir(dir)
        self.timeout-=1
        self.steps += 1

        if self.snake.head==self.food:
            self.snake.reatachtail()
            if len(self.snake)<self.area:
                self.spawnfood()
                self.timeout = int(self.area*2.5)
            else:
                self.food = Cell(-1, -1)
                print("Step:", str(self.steps), "| Won, eaten all food!")
                return 1

        return 0

    def spawnfood(self):
        index = random.randrange(0, self.area-len(self.snake))

        i = -1
        for x in range(self.w):
            for y in range(self.h):
                pos = Cell(x, y)
                if pos.toString() not in self.snake.cells:
                    i+=1
                    if i == index:
                        self.food = pos
                        return

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def toString(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return self.toString()

    def toTouple(self):
        return self.x, self.y

    def __add__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __mul__(self, other):
        if hasattr(other, "x") and hasattr(other, "y"):
            self.x *= other.x
            self.y *= other.y
        else:
            self.x *= other
            self.y *= other
        return self

    def copy(self):
        return Cell(self.x, self.y)

    def __eq__(self, other):
        return self.x==other.x and self.y==other.y

    def eq(self, x, y):
        return self.x == x and self.y == y

    def __iter__(self):
        return (self.x, self.y).__iter__()

    def distManhattan(self, other):
        return abs(self.x-other.x)+abs(self.y-other.y)

    def distSquared(self, other):
        return (self.x-other.x)**2+(self.y-other.y)**2

    def lengthSquared(self):
        return self.x**2+self.y**2

    def dirto(self, other):
        if  abs(other.x-self.x) > abs(other.y-self.y):
            return Cell(min(max(other.x-self.x, -1), 1), 0)
        else:
            return Cell(0, min(max(other.y - self.y, -1), 1))

    def isdir(self):
        return abs(self.x)+abs(self.y)==1


    def converttodir(self):
        self.x = min(max(self.x, -1), 1)
        self.y = min(max(self.y, -1), 1)

    def neighbors(self):
        return tuple(self.copy()+Cell.numtodir(d) for d in range(4))

    @staticmethod
    def dirtonum(dir):
        if dir.x == -1: return 0
        if dir.y == -1: return 1
        if dir.x == 1: return 2
        if dir.y == 1: return 3
        return 4

    @staticmethod
    def dirtostr(dir):
        return str(Cell.dirtonum(dir))

    @staticmethod
    def numtodir(num):
        return [Cell(-1, 0), Cell(0, -1), Cell(1, 0), Cell(0, 1)][num]

    @staticmethod
    def dirtokeycode(dir):
        return ["left", "up", "right", "down"][Cell.dirtonum(dir)]

    @staticmethod
    def reversedir(dir):
        return Cell.numtodir((Cell.dirtonum(dir)+2)%4)

    @staticmethod
    def leftturn(dir):
        return Cell.numtodir((Cell.dirtonum(dir) + 3) % 4)

    @staticmethod
    def rightturn(dir):
        return Cell.numtodir((Cell.dirtonum(dir) + 1) % 4)

class Snake:
    w = 0
    h = 0

    EMPTY = 0
    BODY = 1
    FOOD = 2

    def copy(self):
        return Snake(self.snake, self.cells, self.losttail)

    def __init__(self, snake, cells=None, losttail=None):
        self.snake = deque(snake)
        self.cells = set(cell.toString() for cell in snake) if cells is None else cells.copy()
        self.losttail = losttail

        self._head: Cell = self.snake.pop()
        self.snake.append(self._head)

        self._tail: Cell = self.snake.popleft()
        self.snake.appendleft(self._tail)

        self._dir = None
        self.direction

    @property
    def head(self):
        return self._head

    @property
    def tail(self):
        return self._tail

    def nexthead(self, dir: Cell):
        return  self.head.copy()+dir

    @property
    def direction(self):
        if self._dir is None:
            head = self.snake.pop()
            neck = self.snake.pop()
            dir = neck.dirto(head)
            self.snake.append(neck)
            self.snake.append(head)
            self._dir = dir

        return self._dir

    def addHead(self, head:Cell):
        neck = self._head
        self._dir = neck.dirto(head)

        self._head = head
        self.snake.append(head)
        self.cells.add(head.toString())

    def removeTail(self):
        tail = self.snake.popleft()
        self.losttail = tail
        self.cells.remove(tail.toString())

        self._tail = self.snake.popleft()
        self.snake.appendleft(self._tail)

    def applydir(self, dir: Cell):
        self.removeTail()
        self.addHead(self.nexthead(dir))

    def reatachtail(self):
        self._tail = self.losttail
        self.snake.appendleft(self.losttail)
        self.cells.add(self.losttail.toString())

    def in_cells(self, cell):
        return cell.toString() in self.cells

    def lookat(self, cell):
        if not(0 <= cell.x < Snake.w and 0 <= cell.y < Snake.h):
            return Snake.BODY

        t = self.tail
        if not cell==t and self.in_cells(cell):
            return Snake.BODY

        return Snake.EMPTY

    def __len__(self):
        return len(self.snake)

    def print(self, food: Cell):
        print("/"+"--"*self.w+"\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "
                if food.eq(x, y): cell = "O"
                if f"({x}, {y})" in self.cells: cell = "#"
                if self.head.eq(x, y): cell = "@"
                if self.tail.eq(x, y): cell = "X"

                row += " "+cell
            row += "|"
            print(row)

        print("\\" + "--" * self.w + "/")
