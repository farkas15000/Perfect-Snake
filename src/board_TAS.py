import traceback
import sys
import pygame
from board import Cell, Snake

def colordif(color1, color2):
    return (abs(color1[0]-color2[0])+abs(color1[1]-color2[1])+abs(color1[2]-color2[2]))/(3*255)

class Board:
    def __init__(self, w, h, snake):
        self.w: int = w
        self.h: int = h
        self.area: int = w * h
        Snake.w = w
        Snake.h = h

        self.alivecolor = pygame.Color(170, 215, 81, 255)

        self.headcolor = pygame.Color(79, 125, 237, 255)
        self.snake: Snake = snake
        self.lastdir = self.snake.tail.dirto(self.snake.head)

        self.foodcolor = pygame.Color(231, 71, 29, 255)
        self.food: Cell|None = None
        self.lastfood = Cell(-1, -1)

        self.steps = 0
        self.resoult = 0

    def update(self, agent, image):
        if image.get_at((0, 0)) != self.alivecolor and not self.snake.in_cells(Cell(0, 0)):
            self.resoult = -1
            return None

        if self.resoult != 0:
            return None

        if self.steps == 0:
            self.steps += 1
            self.resoult = 0
            return self.lastdir

        if self.food is None:
            self.foodfind(image)
            if self.food is None:
                return None

        if not self.headinsync(image):
            return None

        try:
            dir = agent.getDirection()

        except Exception:
            print("Step:", str(self.steps), "Error!")
            print()
            print(traceback.format_exc(), file=sys.stderr)
            self.resoult = -1
            return None

        if not dir.isdir():
            print("Step:", str(self.steps), "| Invalid direction!")
            self.resoult = -1
            return None

        self.lastdir = dir

        if self.snake.lookat(self.snake.nexthead(dir)) == Snake.BODY:
            print("Step:", str(self.steps), "| Died, hit wall or tail!")
            self.resoult = -1
            return None

        self.snake.applydir(dir)
        self.steps += 1

        if self.snake.head == self.food:
            self.snake.reatachtail()
            if len(self.snake) < self.area:
                self.food = None
            else:
                print("Step:", str(self.steps), "| Won, eaten all food!")
                self.resoult = 1
                return None

        self.resoult = 0
        return dir

    def headinsync(self, img):
        return colordif(self.pixelcolorat(self.snake.head, img), self.headcolor) < 0.2

    def foodfind(self, img: pygame.Surface):
        for x in range(self.w):
            for y in range(self.h):
                pos = Cell(x, y)
                c = self.pixelcolorat(pos, img)

                if c == self.foodcolor and pos != self.lastfood:
                    self.food = pos
                    self.lastfood = pos
                    return

        self.food = None

    def pixelcolorat(self, pos: Cell|tuple[int, int], img: pygame.Surface):
        cellw = img.width/self.w
        cellh = img.height/self.h

        c1 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2)))
        """c2 = img.get_at((round(cellw*pos.x+cellw/2 + cellw/4), round(cellh*pos.y+cellh/2)))
        c3 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2 + cellh/4)))
        c4 = img.get_at((round(cellw*pos.x+cellw/2 - cellw/4), round(cellh*pos.y+cellh/2)))
        c5 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2 - cellh/4)))

        i = 0
        r = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)
        i+=1
        g = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)
        i += 1
        b = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)"""

        return c1 #r, g, b, 255
