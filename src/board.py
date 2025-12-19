import pygame
from cell import Cell
from snake import Snake
import random

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
        self.lastdir = self.snake.tail().dirto(self.snake.head())

        self.food: Cell|None = None
        self.spawnfood()

    def update(self, agent):
        dir = agent.getDirection()

        if not dir.isdir() or self.timeout<=0:
            return -1

        self.lastdir = dir

        if self.snake.lookat(self.snake.nexthead(dir)) == Snake.BODY:
            return -1

        self.snake.applydir(dir)
        self.steps+=1
        self.timeout-=1

        if self.snake.head()==self.food:
            self.snake.reatachtail()
            if len(self.snake)<self.area:
                self.spawnfood()
                self.timeout = int(self.area*2.5)
            else:
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
