import pygame
from cell import Cell
from snake import Snake

def colordif(color1, color2):
    return (abs(color1[0]-color2[0])+abs(color1[1]-color2[1])+abs(color1[2]-color2[2]))/(3*255)

class Board:
    def __init__(self, w, h, img:pygame.Surface):
        self.colors = dict()

        self.headcolor = (0, 0, 0, 255)
        self.snake: Snake|None = None

        self.foodcolor = (0, 0, 0, 255)
        self.food: Cell|None = None

        self.w: int = w
        self.h: int = h

        Snake.w = w
        Snake.h = h

        self.getcolors(img)

        self.colorsum = 0
        for v in self.colors.values():
            self.colorsum+=v

        for k, v in self.colors.items():
            if 0.4 <= ((v * self.w * self.h) / self.colorsum) <= 1.4:
                self.foodcolor = k
                break

        for k, v in self.colors.items():
            if ((self.colors[self.foodcolor]* self.w * self.h) / self.colorsum) < ((v * self.w * self.h) / self.colorsum) <= self.w*self.h*0.85:
                self.headcolor = k
                break

    def getDirection(self, agent):
        dir = agent.getDirection()

        self.snake.applydir(dir)

        if self.food==self.snake.head():
            self.snake.reatachtail()
            self.food = None

        return dir

    def getcolors(self, img):
        for x in range(0, img.width, max(img.width//100, 1)):
            for y in range(0, img.height, max(img.height//100, 1)):
                c = tuple(img.get_at((x, y)))

                for k, v in self.colors.items():
                    if colordif(c, k)<0.2:
                        self.colors[k] += 1
                        break
                else:
                    self.colors[c] = 1

                if not self.colors:
                    self.colors[c] = 1

    def pixelcolorat(self, pos: Cell|tuple[int, int], img: pygame.Surface):
        cellw = img.width/self.w
        cellh = img.height/self.h

        c1 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2)))
        c2 = img.get_at((round(cellw*pos.x+cellw/2 + cellw/4), round(cellh*pos.y+cellh/2)))
        c3 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2 + cellh/4)))
        c4 = img.get_at((round(cellw*pos.x+cellw/2 - cellw/4), round(cellh*pos.y+cellh/2)))
        c5 = img.get_at((round(cellw*pos.x+cellw/2), round(cellh*pos.y+cellh/2 - cellh/4)))

        i = 0
        r = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)
        i+=1
        g = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)
        i += 1
        b = round((c1[i]+c2[i]+c3[i]+c4[i]+c5[i])/5)

        return r, g, b, 255

    def foodfind(self, img: pygame.Surface):
        for x in range(self.w):
            for y in range(self.h):
                pos = Cell(x, y)
                c = self.pixelcolorat(pos, img)

                for k, v in self.colors.items():
                    if colordif(c, k) < 0.20 and k == self.foodcolor:
                        self.food = pos
                        return

        self.food = None

    def headinsync(self, img):
        return colordif(self.pixelcolorat(self.snake.head(), img), self.headcolor)<0.2
