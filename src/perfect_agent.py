from operator import index

from board import Board
from snake import Snake
from cell import Cell
from baseagent import BaseAgent

class PerfectAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)
        self.grid = Grid(self.w, self.h)

    def getDirection(self):
        self.grid.reroutefood(self.food)

        self.grid.shortenroute(self.snake, self.food)

        dir = self.grid.nextdir(self.snake.head)
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
        self.area = w*h

        self.illegals = set()

        self.odd = False
        if w % 2 == 1 and h % 2 == 1:
            self.odd = True
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

        if self.odd and 1:
            self.cells[1][1].next = self.cells[1][0].pos
            self.cells[0][0].prev = self.cells[0][1].pos

    def at(self, cell: Cell):
        return self.cells[cell.x][cell.y]

    def nextdir(self, cell: Cell):
        return cell.dirto(self.at(cell).next)

    def reroutefood(self, food: Cell):
        if not self.odd: return

        foodblock = self.at(food)
        foodprev = self.at(foodblock.prev)
        prevnext = self.at(foodprev.next)

        if foodprev != prevnext:
            foodprev.next = foodblock.pos
            self.at(foodblock.next).prev = foodblock.pos

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

    def joinaftersplit(self, snake: Snake, food: Cell, basedist: int):
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

            if not self.joinaftersplit(snake, food, basedist):
                self.unsplit(None, leftdist<rightdist, snake.head)

                if max(leftdist, rightdist)<basedist:
                    self.split(None, not(leftdist < rightdist), snake.head)

                    if not self.joinaftersplit(snake, food, basedist):
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
