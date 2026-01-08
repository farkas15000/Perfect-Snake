from collections import deque
import heapq

import pygame

from board import Board, Cell, Snake
from baseagent import BaseAgent

class PerfectAgent(BaseAgent):
    def __init__(self, board: Board):
        super().__init__(board)

        self.grid = Grid(self.w, self.h).generatePath()

        self.fallback = False
        self.steps = []
        self.iter = 0

        self.onpath = True
        self.onpathcheck(self.snake)

    def getDirection(self):
        #print("stp:", self.game.steps)

        self.grid.reroutefood(self.snake, self.food)

        if len(self.grid.rulesets) > (self.grid.w+self.grid.h+self.grid.odd)//2:
            self.grid.burninsplitsdict()
            self.grid.burninrulesets()

        if len(self.snake)==self.area-1 and self.snake.head.distManhattan(self.food) == 1:
            dir = self.snake.head.dirto(self.food)
            return dir

        if not self.onpath:
            dir = self.grid.nextdir(self.snake.head)
            if self.snake.nexthead(dir).toString() in self.snake.cells:
                dir = self.snake.head.dirto(self.grid.at(self.snake.head).getPrev(self.grid.splitsdict))
                if self.snake.nexthead(dir).toString() in self.snake.cells:
                    dir = Cell.reversedir(self.grid.nextdir(self.snake.head))
                    if self.snake.nexthead(dir).toString() in self.snake.cells:
                        for n in self.snake.head.neighbors():
                            dir = self.snake.head.dirto(n)
                            if self.snake.nexthead(dir).toString() not in self.snake.cells:
                                break

            snake = Snake2.copy(self.snake)
            snake.applydir(dir)
            if snake.head == self.food:
                snake.reatachtail()

            self.onpathcheck(snake)
            return dir

        if not self.fallback and self.iter == len(self.steps):
            headorigin = HeadStep(self.snake, self.grid.copy(), None, False, self.food, 0)
            self.steps = HeadStep.A_star(headorigin, None, True, 0, False)
            fin1 = HeadStep.finished

            if self.steps is None:
                self.steps = []

            else:
                headorigin2 = HeadStep(self.snake, HeadStep.finished.grid.copy(), None, False, self.food, 0)
                fin2steps = HeadStep.A_star(headorigin2, None, True, 0, False)
                if fin2steps is not None:
                    self.steps = fin2steps

                finished: HeadStep = HeadStep.finished if HeadStep.finished is not None else fin1
                finished.snake.reatachtail()

                repaired = finished.grid.repair(finished.snake)

                if not repaired:
                    self.steps = []
                else:
                    self.grid = finished.grid
                    self.grid.burninsplitsdict()
                    self.grid.burninrulesets()

            self.iter = 0

        if not self.fallback and self.iter == len(self.steps):
            origin = Step(self.snake, self.grid, None, False, self.food)
            self.steps = Step.A_star(origin, None, True, 0, False)

            if self.steps is None:
                self.fallback = True
                self.steps = []
            else:
                self.grid = Step.finished.grid

            self.iter = 0

        if not self.fallback:
            dir = self.steps[self.iter].dir
            self.iter += 1

        else:
            self.grid.shortenroute(self.snake, self.food)
            dir = self.grid.nextdir(self.snake.head)

        if self.snake.nexthead(dir) == self.food:
            self.fallback = False

        if self.fallback and (self.snake.head.x+self.snake.head.y)%2 == (self.food.x+self.food.y)%2:
            snake = Snake2.copy(self.snake)

            hit = False
            while True:
                closest = self.food
                head = snake.head
                distance = self.w + self.h
                for c in head.neighbors():
                    if c.distManhattan(self.food) < distance:
                        distance = c.distManhattan(self.food)
                        closest = c

                if closest == self.food:
                    break
                if snake.lookat(closest) == Snake.BODY:
                    hit = True
                    break

                snake.applydir(head.dirto(closest))

            self.fallback = hit

        return dir

    def onpathcheck(self, snake):
        self.onpath = True
        start = self.grid.at(snake.head)
        for i in range(len(snake) - 1):
            start = self.grid.at(start.getPrev(self.grid.splitsdict))
            if not snake.in_cells(start.pos):
                self.onpath = False
                break

        if not self.onpath:
            self.onpath = True
            start = self.grid.at(snake.head)
            for i in range(len(snake) - 1):
                start = self.grid.at(start.next)
                if not snake.in_cells(start.pos):
                    self.onpath = False
                    break
            if self.onpath:
                self.grid.reversePath()

    def draw_debug(self, screen, tlcorner, cellsize, w, h):
        for x in range(w):
            for y in range(h):
                self.grid.cells[x][y].draw(screen, pygame.Rect(tlcorner.x + x * cellsize, tlcorner.y + y * cellsize, cellsize, cellsize), self.grid.splitsdict)

class Snake2(Snake):
    def __init__(self, snake, cells): # not for instancing use!
        super().__init__(snake, cells)

        self.gainsset = set()
        self.gainlist = []
        self.lostset = set()

        self.maxchanges = 0

    @classmethod
    def copy(cls, snake):
        snake2 = Snake2((None,), {None,})

        snake2.snake = snake.snake
        snake2.cells = snake.cells
        snake2.losttail = snake.losttail
        snake2._head = snake._head
        snake2._tail = snake._tail
        snake2._dir = snake._dir

        snake2.maxchanges = len(snake.snake)//3

        if isinstance(snake, Snake2):
            snake2.gainlist = snake.gainlist.copy()
            snake2.gainsset = snake.gainsset.copy()
            snake2.lostset = snake.lostset.copy()

        return snake2

    @property
    def direction(self):
        return self._dir

    def applydir(self, dir: Cell):
        if len(self.gainsset) >= self.maxchanges:
            self.snake = self.snake.copy()
            self.snake.extend(self.gainlist)

            for x in range(len(self.lostset)):
                self.snake.popleft()

            self.maxchanges = len(self.snake) // 3

            self.cells = self.cells - self.lostset
            self.cells |= self.gainsset

            self.gainlist.clear()
            self.gainsset.clear()
            self.lostset.clear()

        self.removeTail()
        self.addHead(self.nexthead(dir))

    def addHead(self, head:Cell):
        neck = self._head
        self._dir = neck.dirto(head)

        self._head = head
        self.gainsset.add(head.toString())
        self.gainlist.append(head)

    def removeTail(self):
        tail = self.snake[len(self.gainsset)]
        self.losttail = tail
        self.lostset.add(tail.toString())

        self._tail = self.snake[len(self.gainsset)+1]

    def reatachtail(self):
        self._tail = self.losttail
        self.lostset.remove(self.losttail.toString())

    def in_cells(self, cell):
        ct = cell.toString()
        return ct in self.gainsset or (ct not in self.lostset and ct in self.cells)

    def __len__(self):
        return len(self.snake)+len(self.gainsset)-len(self.lostset)

    def lookat(self, cell):
        if not(0 <= cell.x < Snake.w and 0 <= cell.y < Snake.h):
            return Snake.BODY

        t = self.tail
        if not cell==t and self.in_cells(cell):
            return Snake.BODY

        return Snake.EMPTY

    def print(self, food: Cell):
        print("/"+"--"*self.w+"\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "
                if food.eq(x, y): cell = "O"
                if self.in_cells(Cell(x, y)): cell = "#"
                if self.head.eq(x, y): cell = "@"
                if self.tail.eq(x, y): cell = "X"

                row += " "+cell
            row += "|"
            print(row)

        print("\\" + "--" * self.w + "/")

class Block:
    def __init__(self, x, y):
        self.pos: Cell = Cell(x, y)
        self.next: Cell|None = None
        self.prev: Cell|None = None
        self._index = -1

    def getIndex(self, rulesets):
        i = self._index
        for rules in rulesets:
            for rule in rules:
                if rule[0] <= i:
                    i += rule[1]
                    break
        return i

    def getPrev(self, splitsdict: dict):
        prev = splitsdict.get(self.pos.toTouple())
        return Cell(*prev[0]) if prev else self.prev

    def getNext(self, splitsdict: dict):
        next = splitsdict.get(self.pos.toTouple())
        return Cell(*next[1]) if next else self.next

    def copy(self):
        block = Block(*self.pos)
        block.next = self.next
        block.prev = self.prev
        block._index = self._index

        return block

    def set(self, prev: Cell, next: Cell):
        self.prev = prev
        self.next = next

    def flip(self, area):
        temp = self.next
        self.next = self.prev
        self.prev = temp

        if self._index != -1:
            self._index = area - self._index - 1

    def strindex(self, area, rulesets):
        i = self.getIndex(rulesets)

        return f"{i:>{len(str(area))}}"

    def __str__(self):
        return self.pos.toString()

    def toString(self, splitsdict):
        l = Cell.numtodir(0)
        u = Cell.numtodir(1)
        r = Cell.numtodir(2)
        d = Cell.numtodir(3)

        if self.next is None or self.prev is None: return " "

        p = self.getPrev(splitsdict).dirto(self.pos)
        n = self.pos.dirto(self.getNext(splitsdict))

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
    def draw(self, screen, rect, splitsdict):
        w, h = round(rect.w*(1/10)), round(rect.h*(1/10))
        center = pygame.Rect(0, 0, w, h)
        center.center = rect.center

        if self.prev is not None:
            prev = center.copy()
            prev.move_ip(*(self.pos.dirto(self.getPrev(splitsdict))*(rect.w/2.5)))
            pygame.draw.rect(screen, Block.COLOR, prev.union(center))

        if self.next is not None:
            next = center.copy()
            nextdirrot = Cell.dirtonum(self.pos.dirto(self.getNext(splitsdict)))*90
            next.move_ip(*(self.pos.dirto(self.getNext(splitsdict))*(rect.w/4)))
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
        self.maxchanges = (self.w + self.h + self.odd)//2

        self.illegals = set()
        self.cells: list[list[Block]]|None = None

        self.rulesets:list[tuple[tuple[int, int]]] = []

        self.splitsdict: dict[tuple[int, int], tuple[tuple[int, int], tuple[int, int]]] = dict()

    def generatePath(self):
        if self.odd:
            self.illegals.add( Cell(0, 0).toString())
            self.illegals.add( Cell(0, 1).toString())
            self.illegals.add( Cell(1, 0).toString())
            self.illegals.add( Cell(1, 1).toString())

        self.cells = [[Block(x, y) for y in range(self.h)] for x in range(self.w)]

        block = self.cells[0][0]
        i = 0
        while True:
            block._index = i % self.area
            i += 1
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

        if self.odd:
            self.cells[1][1].next = self.cells[1][0].pos
            self.cells[1][0].prev = self.cells[1][1].pos
            self.cells[0][0].prev = self.cells[0][1].pos

            self.cells[0][0]._index = -1
            self.cells[1][1]._index = 0

        return self

    def addrule(self, Agate, Bgate):
        Agate1, Afacing, Aturning = Agate
        Agate2 = self.at(Agate1.pos.copy()+Aturning)
        Agate3 = self.at((Acell := Agate1.pos.copy() + Afacing))
        Agate4 = self.at(Acell.copy() + Aturning)
        Agates = Agate1.getIndex(self.rulesets), Agate2.getIndex(self.rulesets), Agate3.getIndex(self.rulesets), Agate4.getIndex(self.rulesets)

        Bgate1, Bfacing, Bturning = Bgate
        Bgate2 = self.at(Bgate1.pos.copy() + Bturning)
        Bgate3 = self.at((Bcell := Bgate1.pos.copy() + Bfacing))
        Bgate4 = self.at(Bcell.copy() + Bturning)
        Bgates = Bgate1.getIndex(self.rulesets), Bgate2.getIndex(self.rulesets), Bgate3.getIndex(self.rulesets), Bgate4.getIndex(self.rulesets)

        Ag = [min(Agates)+1, max(Agates)]
        Bg = [min(Bgates)+1, max(Bgates)]

        if Ag[0] != Bg[0] and Ag[1] != Bg[1]:
            rl = Ag + Bg
            rl.sort()

            rules = ((rl[3], 0),
                     (rl[2], rl[0] - rl[2]),
                     (rl[1], rl[0] - rl[2] + rl[3] - rl[1]),
                     (rl[0], rl[3] - rl[1]))

            self.rulesets.append(rules)

    def addhalfrule(self, Agate):
        Agate1, Afacing, Aturning = Agate
        Agate2 = self.at(Agate1.pos.copy() + Aturning)
        Agate3 = self.at((Acell := Agate1.pos.copy() + Afacing))
        Agate4 = self.at(Acell.copy() + Aturning)

        rl = [Agate1.getIndex(self.rulesets), Agate2.getIndex(self.rulesets), Agate3.getIndex(self.rulesets), Agate4.getIndex(self.rulesets)]

        rules = [(rl[0], -rl[0]),
                 (rl[1], -rl[1] + 1),
                 (0, (self.area-self.odd+1 - rl[1]) if rl[2] < rl[3] else -self.area-self.odd-1),
                 (rl[2], -self.area-self.odd-1)]
        rules.sort(key=lambda r: r[0], reverse=True)

        self.rulesets.append(tuple(rules))

    def poprule(self):
        return self.rulesets.pop()

    def burninrulesets(self):
        head = self.at(Cell(0, 1))
        i = head.getIndex(self.rulesets)
        for x in range(self.area-self.odd):
            i += 1
            head = self.at(head.getNext(self.splitsdict))
            head._index = i%(self.area-self.odd)
        self.rulesets = []

    def burninsplitsdict(self):
        for pos, pn in self.splitsdict.items():
            self.at(pos).set(self.at(pn[0]).pos, self.at(pn[1]).pos)

        self.splitsdict = dict()

    def copy(self):
        if len(self.rulesets) > self.maxchanges:
            self.cells = [[self.cells[x][y].copy() for y in range(self.h)] for x in range(self.w)]
            self.burninsplitsdict()
            self.burninrulesets()

        grid = Grid(self.w, self.h)

        grid.illegals = self.illegals

        grid.cells = self.cells

        grid.rulesets = self.rulesets.copy()

        grid.splitsdict = self.splitsdict.copy()

        return grid

    def reversePath(self):
        for x in range(self.w):
            for y in range(self.h):
                self.cells[x][y].flip(self.area-self.odd)

    def at(self, cell: Cell|tuple[int, int]):
        if isinstance(cell, Cell):
            return self.cells[cell.x][cell.y]
        return self.cells[cell[0]][cell[1]]

    def nextdir(self, cell: Cell):
        return cell.dirto(self.at(cell).getNext(self.splitsdict))

    def reroutefood(self, snake, food: Cell):
        if not self.odd: return

        foodblock: Block = self.at(food)

        if self.at(foodblock.prev).next==food: return

        self.burninsplitsdict()

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

                    tempindex = foodblock._index
                    foodblock._index = corner._index
                    corner._index = tempindex

                    d = self.fooddistance(snake.head, food)
                    if d < dist:
                        dist = d
                        shortest = corner

                    corner._index = foodblock._index
                    foodblock._index = tempindex

                    prevblock.next = corner.pos
                    nextblock.prev = corner.pos

        if shortest is None:
            raise Exception("Couldn't reroute food")

        prevblock: Block = self.at(shortest.prev)
        prevblock.next = foodblock.pos
        nextblock: Block = self.at(shortest.next)
        nextblock.prev = foodblock.pos
        foodblock.set(prevblock.pos, nextblock.pos)

        self.illegals = {food.toString(), shortest.pos.toString(), prevblock.pos.toString(), nextblock.pos.toString()}

        tempindex = foodblock._index
        foodblock._index = shortest._index
        shortest._index = tempindex

    def fooddistance(self, start: Cell, food: Cell):
        headindex = self.at(start).getIndex(self.rulesets)
        foodindex = self.at(food).getIndex(self.rulesets)

        dist = self.area*2
        if headindex >=0 and foodindex >=0:
            dist = self.area-self.odd - abs(headindex - foodindex) if headindex > foodindex else foodindex - headindex
        elif headindex == -1 or foodindex == -1:
            dist = self.area-self.odd

        return dist

    def gatesturn(self, gate1, gate2, gate3, gate4):
        """gate1.next = gate2.pos
        gate2.prev = gate1.pos

        gate3.prev = gate4.pos
        gate4.next = gate3.pos"""

        g1 = gate1.pos.toTouple()
        g1pn = self.splitsdict.get(g1)
        g2 = gate2.pos.toTouple()
        g2pn = self.splitsdict.get(g2)
        g3 = gate3.pos.toTouple()
        g3pn = self.splitsdict.get(g3)
        g4 = gate4.pos.toTouple()
        g4pn = self.splitsdict.get(g4)

        if g1pn and gate1.next == gate2.pos and gate1.prev.eq(*g1pn[0]):
            self.splitsdict.pop(g1)
        else:
            self.splitsdict[g1] = (g1pn[0] if g1pn else gate1.prev.toTouple(), g2)

        if g2pn and gate2.prev == gate1.pos and gate2.next.eq(*g2pn[1]):
            self.splitsdict.pop(g2)
        else:
            self.splitsdict[g2] = (g1, g2pn[1] if g2pn else gate2.next.toTouple())

        if g3pn and gate3.prev == gate4.pos and gate3.next.eq(*g3pn[1]):
            self.splitsdict.pop(g3)
        else:
            self.splitsdict[g3] = (g4, g3pn[1] if g3pn else gate3.next.toTouple())

        if g4pn and gate4.next == gate3.pos and gate4.prev.eq(*g4pn[0]):
            self.splitsdict.pop(g4)
        else:
            self.splitsdict[g4] = (g4pn[0] if g4pn else gate4.prev.toTouple(), g3)

    def split(self,  snake: Snake|None, leftturn: bool, safegatepos: Cell|None):
        gate1 = None
        if snake is not None:
            gate1 = self.at(snake.head)
        if safegatepos is not None:
            gate1 = self.at(safegatepos)

        facing = gate1.pos.dirto(gate1.getNext(self.splitsdict))
        turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)

        gate2pos = gate1.pos.copy()+turning

        if not (0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h): return None

        gate2 = self.at(gate2pos)
        if snake is not None and (snake.in_cells(gate2.pos) or snake.in_cells(gate2.getPrev(self.splitsdict)) or
                                  (snake.in_cells(gate1.getNext(self.splitsdict)) and gate1.getNext(self.splitsdict)!=snake.tail)):
            return None

        if snake is not None and (gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                                  gate2.getPrev(self.splitsdict).toString() in self.illegals or gate1.getNext(self.splitsdict).toString() in self.illegals):
            return None

        if gate2.pos.dirto(gate2.getPrev(self.splitsdict))==facing:
            gate3 = self.at((cell:= gate1.pos.copy()+facing))
            gate4 = self.at(cell.copy()+turning)

            self.gatesturn(gate1, gate2, gate3, gate4)

            return gate1, facing, turning

        return None

    def unsplit(self,  snake: Snake|None, leftturn: bool, safegatepos: Cell|None):
        res = self.split(snake, not leftturn, safegatepos)
        if not res:
            raise Exception("Couldn't unsplit!")
        return res

    def joinaftersplit(self, split, snake: Snake, food: Cell, basedist: int, firstjoin=False):
        self.addhalfrule(split)

        shortestgate = None
        shortestturn = None

        gate1 = self.at(self.at(snake.head).getNext(self.splitsdict))
        snaketailnext = self.at(snake.tail).getNext(self.splitsdict)
        while True:
            facing = gate1.pos.dirto(gate1.getNext(self.splitsdict))
            for leftturn in (False, True):
                turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)
                gate2pos = gate1.pos.copy() + turning

                if 0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h:
                    gate2 = self.at(gate2pos)
                    if gate2.getIndex(self.rulesets) < -1:
                        illegal = False

                        if (snake.in_cells(gate2.pos) or snake.in_cells(gate2.getPrev(self.splitsdict)) or
                                 (snake.in_cells(gate1.getNext(self.splitsdict)) and gate1.getNext(self.splitsdict)!=snake.tail)):
                            illegal = True

                        if not illegal and (
                                gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                                gate2.getPrev(self.splitsdict).toString() in self.illegals or gate1.getNext(self.splitsdict).toString() in self.illegals):
                            illegal = True

                        if not illegal and gate2.pos.dirto(gate2.getPrev(self.splitsdict)) == facing:
                            self.poprule()

                            gate2 = self.at(gate1.pos.copy() + turning)
                            gate3 = self.at((cell := gate1.pos.copy() + facing))
                            gate4 = self.at(cell.copy() + turning)

                            #self.gatesturn(gate1, gate2, gate3, gate4)

                            self.addrule(split, (gate1, facing, turning))

                            passed = False
                            if basedist == self.area * 2 or (dist := (self.fooddistance(snake.head, food))) <= basedist:
                                basedist = 0 if basedist == self.area * 2 else dist
                                shortestgate = gate1
                                shortestturn = leftturn
                                passed = True

                            self.poprule()

                            if firstjoin and passed:
                                self.gatesturn(gate1, gate2, gate3, gate4)
                                return shortestgate, facing, turning

                            #self.gatesunturn(gate1, gate2, gate3, gate4)

                            self.addhalfrule(split)

            if gate1.pos == snaketailnext: break
            gate1 = self.at(gate1.getNext(self.splitsdict))

        self.poprule()

        if shortestgate is not None:
            return self.split(None, shortestturn, shortestgate.pos)

        return None

    def shortenroute(self, snake: Snake, food: Cell):
        basedist = self.fooddistance(snake.head, food)
        if basedist > self.area:
            raise Exception("Food not on route!")

        leftdist = self.area*2
        sl1 = self.split(snake, True, None)
        if sl1:
            self.addhalfrule(sl1)
            leftdist = self.fooddistance(snake.head, food)
            self.poprule()
            self.unsplit(None, True, snake.head)

        rightdist = self.area * 2
        sl2 = self.split(snake, False, None)
        if sl2:
            self.addhalfrule(sl2)
            rightdist = self.fooddistance(snake.head, food)
            self.poprule()
            self.unsplit(None, False, snake.head)

        if leftdist<basedist or rightdist<basedist:
            sl1 = self.split(None, leftdist<rightdist, snake.head)

            jsl1 = self.joinaftersplit(sl1, snake, food, basedist, False)
            if not jsl1:
                self.unsplit(None, leftdist<rightdist, snake.head)

                if max(leftdist, rightdist)<basedist:
                    sl2 = self.split(None, not(leftdist < rightdist), snake.head)

                    jsl2 = self.joinaftersplit(sl2, snake, food, basedist, False)
                    if not jsl2:
                        self.unsplit(None, not(leftdist < rightdist), snake.head)
                    else:
                        self.addrule(sl2, jsl2)

            else:
                self.addrule(sl1, jsl1)

    def repair(self, snake: Snake):
        baseroute = set()
        gates = list()

        gate1 = self.at(self.at(snake.head).getNext(self.splitsdict))
        snaketailnext = self.at(snake.tail).getNext(self.splitsdict)
        i = self.area+2
        while True:
            if i <= 0:
                return None
            i -= 1
            baseroute.add(gate1.pos.toString())
            facing = gate1.pos.dirto(gate1.getNext(self.splitsdict))
            for leftturn in (False, True):
                turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)
                gate2pos = gate1.pos.copy() + turning

                if 0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h:
                    gate2 = self.at(gate2pos)
                    illegal = False

                    if (snake.in_cells(gate2.pos) or snake.in_cells(gate2.getPrev(self.splitsdict)) or
                             (snake.in_cells(gate1.getNext(self.splitsdict)) and gate1.getNext(self.splitsdict) != snake.tail)):
                        illegal = True

                    if not illegal and (
                            gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                            gate2.getPrev(self.splitsdict).toString() in self.illegals or gate1.getNext(self.splitsdict).toString() in self.illegals):
                        illegal = True

                    if not illegal and gate2.pos.dirto(gate2.getPrev(self.splitsdict)) == facing:
                        gates.append((gate1, leftturn))

            if gate1.pos == snaketailnext: break
            gate1 = self.at(gate1.getNext(self.splitsdict))

        pathlength = len(baseroute) + len(snake) - 2

        while pathlength < self.area - self.odd and gates:
            gate1, turn = gates.pop()
            facing = gate1.pos.dirto(gate1.getNext(self.splitsdict))
            turning = Cell.leftturn(facing) if turn else Cell.rightturn(facing)
            gate2pos = gate1.pos.copy() + turning

            if gate2pos.toString() not in baseroute:
                gate2 = self.at(gate2pos)
                gate3 = self.at((cell := gate1.pos.copy() + facing))
                gate4 = self.at(cell.copy() + turning)
                end = gate4

                self.gatesturn(gate1, gate2, gate3, gate4)

                while True:
                    baseroute.add(gate1.pos.toString())
                    facing = gate1.pos.dirto(gate1.getNext(self.splitsdict))
                    for leftturn in (False, True):
                        turning = Cell.leftturn(facing) if leftturn else Cell.rightturn(facing)
                        gate2pos = gate1.pos.copy() + turning

                        if 0 <= gate2pos.x < self.w and 0 <= gate2pos.y < self.h:
                            gate2 = self.at(gate2pos)
                            illegal = False

                            if (snake.in_cells(gate2.pos) or snake.in_cells(gate2.getPrev(self.splitsdict)) or
                                     (snake.in_cells(gate1.getNext(self.splitsdict)) and gate1.getNext(self.splitsdict) != snake.tail)):
                                illegal = True

                            if not illegal and (
                                    gate1.pos.toString() in self.illegals or gate2.pos.toString() in self.illegals or
                                    gate2.getPrev(self.splitsdict).toString() in self.illegals or gate1.getNext(self.splitsdict).toString() in self.illegals):
                                illegal = True

                            if not illegal and gate2.pos.dirto(gate2.getPrev(self.splitsdict)) == facing:
                                gates.append((gate1, leftturn))

                    if gate1.pos == end.pos: break
                    gate1 = self.at(gate1.getNext(self.splitsdict))

                pathlength = len(baseroute) + len(snake) - 2

        return pathlength == self.area - self.odd

    def print(self, snake: Snake|None = None, food: Cell|None = None):
        print("/"+"--"*self.w+"\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "
                if food is not None and food.eq(x, y): cell = "O"
                if snake is not None:
                    if f"({x}, {y})" in snake.cells if not isinstance(snake, Snake2) else snake.in_cells(Cell(x ,y)): cell = "#"
                    if snake.head.eq(x, y): cell = "@"
                    if snake.tail.eq(x, y): cell = "X"

                row += self.cells[x][y].toString(self.splitsdict)+cell
            row += "|"
            print(row)

        print("\\" + "--" * self.w + "/")

    def printindexes(self):
        print("/" + "-"*self.w*(len(str(self.area))+1) + "\\")

        for y in range(self.h):
            row = "|"
            for x in range(self.w):
                cell = " "

                row += self.cells[x][y].strindex(self.area, self.rulesets)+cell
            row += "|"
            print(row)

        print("\\" + "-"*self.w*(len(str(self.area))+1) + "/")

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
    def __init__(self, snake, grid, dir, move, target, priority=0):
        super().__init__()

        self.dir: Cell = dir
        self.snake: Snake = snake
        self.grid: Grid = grid
        self.target: Cell = target
        self.priority = priority

        if move:
            self.snake.applydir(dir)

        self.hScore = self.target.distManhattan(self.snake.head)

        if self.hScore == 0:
            self.satisfied = True

    def neighbor(self, leftturn, seen):
        if leftturn is None:
            grid = self.grid
        else:
            grid = self.grid.copy()
            sl1 = grid.split(self.snake, leftturn, None)
            if sl1:
                jsl1 = grid.joinaftersplit(sl1, self.snake, self.target, self.grid.area*2, True)
                if not jsl1:
                    return
                else:
                    grid.addrule(sl1, jsl1)
            else: return

        dir = grid.nextdir(self.snake.head)

        k = self
        if 1 or k not in seen:
            snake = Snake2.copy(self.snake)
            snake.applydir(dir)

            self.children[Step(snake, grid, dir, False, self.target, int(leftturn is None))] = 1

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

        pcomp = compls(other.priority, self.priority)
        if pcomp != 0: return pcomp > 0

        gcomp = compls(self.gScore, other.gScore)
        if gcomp != 0: return gcomp > 0

        dcomp = compls(self.depth, other.depth)
        return dcomp > 0

    def failpoint(self, openSetSize, gScoreSize, checks):
        return checks > self.grid.area * 1.5

class HeadStep(Node):
    def __init__(self, snake, grid, dir, move, target, wallhugs):
        super().__init__()

        self.snake: Snake = snake
        self.dir: Cell = dir if dir is not None else self.snake.direction
        self.grid: Grid = grid
        self.target: Cell = target
        self.wallhugs = wallhugs

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


        griddir = self.grid.nextdir(self.snake.head)

        if griddir != dir:
            turnnum =  (Cell.dirtonum(dir) - Cell.dirtonum(griddir))%4

            if turnnum == 1:
                if self.grid.split(self.snake, False, None):
                    grid = self.grid.copy()
                    self.grid.unsplit(None, False, self.snake.head)
                else: return

            elif turnnum == 3:
                if self.grid.split(self.snake, True, None):
                    grid = self.grid.copy()
                    self.grid.unsplit(None, True, self.snake.head)
                else: return
            else:
                return
        else:
            grid = self.grid

        k = str(self.snake.nexthead(dir)) + str(dir)
        if self.snake.lookat(self.snake.nexthead(dir)) != Snake.BODY and k not in seen:
            snake = Snake2.copy(self.snake)
            snake.applydir(dir)

            wallhugs = 0
            for cell in snake.head.neighbors():
                if not (cell==self.snake.head or cell==snake.tail) and (cell.toString() in snake.cells if not isinstance(snake, Snake2) else snake.in_cells(cell)):
                    wallhugs += 1

            self.children[HeadStep(snake, grid, dir, False, self.target, wallhugs)] = 1

    def neighbors(self, seen):
        if self.children: return self.children

        self.neighbor(None, seen)
        self.neighbor(True, seen)
        self.neighbor(False, seen)

        return self.children.keys()

    def key(self):
        return str(self.snake.head) + str(self.dir)

    def __lt__(self, other):
        hcomp = compls(self.hScore, other.hScore)
        if hcomp!=0: return hcomp>0

        wcomp = compls(other.wallhugs, self.wallhugs)
        if wcomp != 0: return wcomp > 0

        gcomp = compls(self.gScore, other.gScore)
        if gcomp != 0: return gcomp > 0

        dcomp = compls(self.depth, other.depth)
        return dcomp > 0

    def failpoint(self, openSetSize, gScoreSize, checks):
        return checks > self.grid.area * 1.5

def compls(a, b):
    if a == b: return 0
    return (a<b)*2-1
