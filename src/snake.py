from collections import deque
from cell import Cell

class Snake:
    w = 0
    h = 0

    EMPTY = 0
    BODY = 1
    FOOD = 2

    def copy(self):
        return Snake(self.snake, self.losttail)

    def __init__(self, snake, losttail=None):
        self.snake = deque(snake)
        self.cells = set(cell.toString() for cell in snake)
        self.losttail = losttail

        self._head: Cell = self.snake.pop()
        self.snake.append(self._head)

        self._tail: Cell = self.snake.popleft()
        self.snake.appendleft(self._tail)

    @property
    def head(self):
        return self._head

    @property
    def tail(self):
        return self._tail

    def nexthead(self, dir: Cell):
        return  self.head.copy()+dir

    def addHead(self, head:Cell):
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

    def lookat(self, cell):
        if not(0 <= cell.x < Snake.w and 0 <= cell.y < Snake.h):
            return Snake.BODY

        t = self.tail
        if not cell==t and cell.toString() in self.cells:
            return Snake.BODY

        return Snake.EMPTY

    def __len__(self):
        return len(self.snake)
