import pygame

def colordif(color1, color2):
    return (abs(color1[0]-color2[0])+abs(color1[1]-color2[1])+abs(color1[2]-color2[2]))/(3*255)


class Board:
    def __init__(self, img:pygame.Surface):
        self.colors = dict()

        self.snake = None

        self.w = 1
        self.h = 1

        self.getcolors(img)

        self.colorsum = 0
        for v in self.colors.values():
            self.colorsum+=v

    def getcolors(self, img):
        for x in range(0, img.width, max(img.width//100, 1)):
            for y in range(0, img.height, max(img.height//100, 1)):
                c = tuple(img.get_at((x, y)))

                for k, v in self.colors.items():
                    if colordif(c, k)<0.20:
                        self.colors[k] += 1
                        break
                else:
                    self.colors[c] = 1

                if not self.colors:
                    self.colors[c] = 1
