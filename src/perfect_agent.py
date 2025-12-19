from board import Board
from snake import Snake
from cell import Cell
from agent import Agent

class PerfectAgent(Agent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.grid = Grid(self.w, self.h)
        self.grid.print(self.snake, self.food)

        c = Cell(0, 0)
        print(self.grid.at(c).prev)
        print(self.grid.at(c).next)

    def getDirection(self):
        dir = self.grid.nextdir(self.snake.head())
        return dir

class Block:
    def __init__(self, x, y):
        self.pos: Cell = Cell(x, y)
        self.next: Cell|None = None
        self.prev: Cell|None = None

    def copy(self):
        block = Block(*self.pos)
        block.next = self.next
        block.prev = self.prev

    def set(self, prev: Cell, next: Cell):
        self.prev = prev
        self.next = next

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

class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h

        self.illegals = set()

        odd = False
        if w % 2 == 1 and h % 2 == 1:
            odd = True
            self.illegals.add( Cell(0, 0).toString())
            self.illegals.add( Cell(0, 1).toString())
            self.illegals.add( Cell(1, 0).toString())
            self.illegals.add( Cell(1, 1).toString())

        self.cells = [[Block(x, y) for y in range(h)] for x in range(w)]

        block = self.cells[0][0]
        while True:
            neighbors = block.pos.neighbors()
            dist = -1
            x = -1
            furthest = None
            for pos in neighbors:
                if 0 <= pos.x < w and 0 <= pos.y < h and self.at(pos).prev is None and (d:=pos.lengthSquared()) >= dist and pos.x>=x:
                    dist = d
                    x = pos.x
                    furthest = pos
            if furthest is None:
                break
            block.next = self.at(furthest).pos

            prev = block.pos
            block = self.at(furthest)
            block.prev = prev

        if odd and 1:
            self.cells[1][1].next = self.cells[1][0].pos
            self.cells[0][0].prev = self.cells[0][1].pos

    def at(self, cell: Cell):
        return self.cells[cell.x][cell.y]

    def nextdir(self, cell: Cell):
        return cell.dirto(self.at(cell).next)

    def print(self, snake: Snake, food: Cell):
        print("/"+"--"*self.w+"\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "
                if food.eq(x, y): cell = "O"
                if f"({x}, {y})" in snake.cells: cell = "▮"
                if snake.head().eq(x, y): cell = "@"
                if snake.tail().eq(x, y): cell = "X"

                row += str(self.cells[x][y])+cell
            row += "|"
            print(row)

        print("\\" + "--" * self.w + "/")
