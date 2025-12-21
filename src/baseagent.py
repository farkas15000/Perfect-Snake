from board import Board
from snake import Snake
from cell import Cell

class BaseAgent:
    def __init__(self, board:Board):
        self.game = board

    def getDirection(self):

        closest = self.food
        head = self.snake.head()
        distance = self.w+self.h
        for c in head.neighbors():
            if self.snake.lookat(c) != Snake.BODY and c.distManhattan(self.food) < distance:
                distance = c.distManhattan(self.food)
                closest = c

        dir = head.dirto(closest)
        return dir

    def draw_debug(self, screen, tlcorner, cellsize, w, h):
        pass

    @property
    def w(self):
        return self.game.w

    @property
    def h(self):
        return self.game.h

    @property
    def area(self):
        return self.game.area

    @property
    def snake(self):
        s: Snake = self.game.snake
        return s

    @property
    def food(self):
        f: Cell = self.game.food
        return f

