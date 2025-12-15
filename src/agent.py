from board import Board
from cell import Cell
from snake import Snake

class Agent:
    def __init__(self, board:Board):
        self.game = board

    def getDirection(self):

        closest = self.game.food
        head = self.game.snake.head()
        distance = self.game.w+self.game.h
        for c in head.neighbors():
            if self.game.snake.lookat(c) != Snake.BODY and c.distManhattan(self.game.food) < distance:
                distance = c.distManhattan(self.game.food)
                closest = c

        dir = head.dirto(closest)
        return dir
