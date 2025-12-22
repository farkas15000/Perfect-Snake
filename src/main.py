import json
import os
import platform
import random
import time

import pygame

from board import Board, Cell, Snake
from baseagent import BaseAgent
from perfect_agent import PerfectAgent


class App:
    st = None
    state = "setup"
    states = {}

    def __init__(self):

        self.fullscreen = False

        self.controls = {
            "Esc": pygame.K_ESCAPE,
        }

        self.winResolution = 800, 900

        self.states.update({"setup": self.setup,
                            "game": self.game,
                            })
        App.st = self

        if hasattr(platform, "window"):
            self.mobile = platform.window.mobile_check() or platform.window.mobile_tablet()
        else:
            self.mobile = False

        pygame.init()
        self.clock = pygame.time.Clock()

        #self.logical_sizeRect = pygame.Rect(0, 0, 800, 900)

        self.window = pygame.Window(size=self.winResolution)
        self.window.resizable = True
        self.window.title = "Perfect Snake"

        self.display = self.window.get_surface()
        #self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

        self.font = pygame.font.Font(size=45)

        self.dt = 0.016
        self.running = True
        self.mousePos = None
        self.mouseClickPos = None
        self.mouseClicked = False
        self.mouse = None
        self.keyboard = None

        self.headcolor = pygame.Color(79, 125, 237, 255)
        self.facecolors = (pygame.Color(255, 255, 255, 255), pygame.Color(28, 70, 158, 255), pygame.Color(40, 83, 179, 255))
        self.bodygradient = (pygame.Color(23, 67, 159, 255), pygame.Color(79, 125, 237, 255))
        self.foodcolors = (pygame.Color(231, 71, 29, 255), pygame.Color(238, 117, 92, 255), pygame.Color(151, 110, 76, 255), pygame.Color(73, 197, 39, 255))
        self.boardcolor = (pygame.Color(170, 215, 81, 255), pygame.Color(162, 209, 73, 255))
        self.backgroundcolor = pygame.Color(59, 94, 35, 255)

        self.fps = 60
        self.timer = 0
        self.speed = 8
        self.skipto = 0
        self.skiptype = True
        self.selected = None
        self.seed = 0
        self.board: Board | None = None
        self.boardW = 10
        self.boardH = 10
        self.cellsize = 0
        self.tlcorner = None
        self.head = None
        self.tail = None
        self.agent: BaseAgent | None = None
        self.resoult = 0
        self.paused = False
        self.autosave = True
        self.debug = False

        self.save(load=True)

        c = max(min(800 // max(self.boardW, 1), 800 // max(self.boardH, 1)), 8)
        w = self.boardW * c
        h = self.boardH * c

        self.logical_sizeRect = pygame.Rect(0, 0,max(w, 800), h + 100)
        self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

        if self.head is not None:
            self.head = Cell(*self.head)
        if self.tail is not None:
            self.tail = Cell(*self.tail)

        self.seedimg = None
        self.startimg = self.font.render("Start", False, "white", None).convert_alpha()
        self.stopimg = self.font.render("Stop", False, "white", None).convert_alpha()
        self.pauseimg = self.font.render("Pause", False, "white", None).convert_alpha()
        self.resumeimg = self.font.render("Resume", False, "white", None).convert_alpha()
        self.nextimg = self.font.render("Next", False, "white", None).convert_alpha()
        self.autosaveonimg = self.font.render("Auto save: On", False, "white", None).convert_alpha()
        self.autosaveoffimg = self.font.render("Auto save: Off", False, "white", None).convert_alpha()
        self.whimg = None
        self.stepimg = self.font.render("steps", False, "white", None).convert_alpha()
        self.lengthimg = self.font.render("length", False, "white", None).convert_alpha()
        self.debugonimg = self.font.render("Debug: On", False, "white", None).convert_alpha()
        self.debugoffimg = self.font.render("Debug: Off", False, "white", None).convert_alpha()

    def setup(self):
        if self.mouse[1][0]:
            self.selected = None

        self.screen.fill(self.backgroundcolor)
        pygame.draw.rect(self.screen, "black", pygame.Rect(0, 0, self.screen.width, 100))

        boardWprev = self.boardW
        if pygame.Rect(8, 17, 102, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "boardW"
        if self.selected == "boardW":
            self.boardW = self.inputToNum(self.boardW, 0, 100)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "boardW" else (25, 25, 25), pygame.Rect(8, 17, 102, 32))
        widthimg = self.font.render("W: " + str(self.boardW), False, "white", None).convert_alpha()
        self.screen.blit(widthimg, (10, 20))

        boardHprev = self.boardH
        if pygame.Rect(8 + 108, 17, 98, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "boardH"
        if self.selected == "boardH":
            self.boardH = self.inputToNum(self.boardH, 0, 100)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "boardH" else (25, 25, 25), pygame.Rect(8 + 108, 17, 98, 32))
        heightimg = self.font.render("H: " + str(self.boardH), False, "white", None).convert_alpha()
        self.screen.blit(heightimg, (10 + 108, 20))

        if pygame.Rect(8 + 212, 17, 206, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "speed"
        if self.selected == "speed":
            self.speed = self.inputToNum(self.speed, 0, 9999)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "speed" else (25, 25, 25), pygame.Rect(8 + 212, 17, 206, 32))
        speedimg = self.font.render("Steps: " + str(self.speed) + "/s", False, "white", None).convert_alpha()
        self.screen.blit(speedimg, (10 + 212, 20))

        if pygame.Rect(8 + 424, 17, 188, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "seed"
        if self.selected == "seed":
            self.seed = self.inputToNum(self.seed, 0, 99999)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "seed" else (25, 25, 25), pygame.Rect(8 + 424, 17, 188, 32))
        self.seedimg = self.font.render("Seed: " + (str(self.seed) if self.seed!=0 else "rand"), False, "white", None).convert_alpha()
        self.screen.blit(self.seedimg, (10 + 424, 20))

        if pygame.Rect(8, 57, 236, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "skipto"
        if self.selected == "skipto":
            self.skipto = self.inputToNum(self.skipto, 0, 999999)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "skipto" else (25, 25, 25), pygame.Rect(8 , 57, 236, 32))
        skiptoimg = self.font.render("Skip to: " + (str(self.skipto) if self.skipto!=0 else "-"), False, "white", None).convert_alpha()
        self.screen.blit(skiptoimg, (10, 60))

        if pygame.Rect(8 + 240, 57, 102, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]:
            self.skiptype = not self.skiptype
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8 + 240, 57, 102, 32))
        self.screen.blit(self.lengthimg if self.skiptype else self.stepimg, (10 + 240, 60))

        if pygame.Rect(8 + 460, 57, 212, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]:
            self.autosave = not self.autosave
            if not self.autosave:
                self.save()
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8 + 460, 57, 212, 32))
        self.screen.blit(self.autosaveonimg if self.autosave else self.autosaveoffimg, (10 + 460, 60))

        if self.keys((pygame.K_b,))[0] or (pygame.Rect(8 + 618, 17, 164, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]):
            self.debug = not self.debug
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8 + 618, 17, 164, 32))
        self.screen.blit(self.debugonimg if self.debug else self.debugoffimg, (10 + 618, 20))

        c = max(min(800//max(self.boardW, 1), 800//max(self.boardH, 1)), 8)
        w = self.boardW*c
        h = self.boardH*c
        tlcorner = pygame.Vector2(max(w, 800) // 2 - w // 2, 100)

        if boardWprev!=self.boardW or boardHprev!=self.boardH:
            self.logical_sizeRect.size = (max(w, 800), h+100)
            self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

            self.head = None
            self.tail = None
        else:
            x = int((self.mousePos[1][0] - tlcorner.x) // c)
            if not (0 <= x <= self.boardW - 1):
                x = None

            y = int((self.mousePos[1][1] - tlcorner.y) // c)
            if not (0 <= y <= self.boardH - 1):
                y = None

            if x is not None and y is not None:
                if self.mouse[1][0]:
                    self.head = Cell(x, y)

                if self.mouse[1][2]:
                    self.tail = Cell(x, y)

        pygame.draw.rect(self.screen, (40, 40, 40, 255), pygame.Rect(*tlcorner, w, h), width=0)

        for x in range(self.boardW):
            for y in range(self.boardH):
                pygame.draw.rect(self.screen, self.boardcolor[(x + y) % 2], pygame.Rect(tlcorner.x + x * c, tlcorner.y + y * c, c, c), 0)

        narrowhead = round(c*(1/8))
        narrowface = round(c*(1/14))
        narrowmax = round(c*(1/7))
        narrowmin = round(c*(2/8))

        ready = False
        if self.boardW > 1 and self.boardH > 1 and self.head is not None and self.tail is not None and (self.head.x == self.tail.x or self.head.y == self.tail.y) and self.head.distManhattan(self.tail)>=2:
            ready = True
            pygame.draw.rect(self.screen, self.bodygradient[0], pygame.Rect(tlcorner.x+min(self.head.x, self.tail.x)*c+narrowmin, tlcorner.y+min(self.head.y, self.tail.y)*c+narrowmin, c*(abs(self.head.x-self.tail.x)+1)-narrowmin*2, c*(abs(self.head.y-self.tail.y)+1)-narrowmin*2), 0, round(c/2.5))

            facing = self.tail.dirto(self.head)
            facingnum = Cell.dirtonum(facing)
            l = self.head.distManhattan(self.tail)
            for i in range(l):
                c1 = Cell(self.tail.x+facing.x*i, self.tail.y+facing.y*i)
                c2 = Cell(self.tail.x+facing.x*(i+1), self.tail.y+facing.y*(i+1))
                narrow = round(pygame.math.lerp(narrowmin, narrowmax, i / l))
                if facingnum >=2:
                    rect = pygame.Rect(tlcorner.x + c1.x * c + narrow, tlcorner.y + c1.y * c + narrow, 0, 0)
                    if facingnum == 2:
                        rect.size = ((c-narrow)*2, c-narrow*2)
                    else:
                        rect.size = (c - narrow*2, (c-narrow)*2)
                else:
                    rect = pygame.Rect(tlcorner.x + c2.x * c + narrow, tlcorner.y + c2.y * c + narrow, 0, 0)
                    if facingnum == 0:
                        rect.size = ((c-narrow)*2, c-narrow*2)
                    else:
                        rect.size = (c - narrow*2, (c-narrow)*2)

                pygame.draw.rect(self.screen, self.colorgardient(self.bodygradient[0], self.bodygradient[1], i/l), rect, 0, round(c / 2.5))

        if ready:
            self.draw_face(pygame.Rect(tlcorner.x + self.head.x * c, tlcorner.y + self.head.y * c, c, c), narrowface, self.tail.dirto(self.head))
        elif self.head is not None:
            pygame.draw.rect(self.screen, self.headcolor, pygame.Rect(tlcorner.x + self.head.x * c + narrowhead, tlcorner.y + self.head.y * c + narrowhead, c-narrowhead*2, c-narrowhead*2), 0, round(c / 2.5))

        if not ready and self.tail is not None:
            pygame.draw.rect(self.screen, self.bodygradient[0], pygame.Rect(tlcorner.x + self.tail.x * c + narrowmin, tlcorner.y + self.tail.y * c + narrowmin, c-narrowmin*2, c-narrowmin*2), 0, round(c / 2.5))

        if ready:
            pygame.draw.rect(self.screen, (40, 40, 40), pygame.Rect(8 + 702, 57, 80, 32))
        self.screen.blit(self.startimg, (10 + 702, 60))

        if ready and (self.keys((pygame.K_RETURN,))[0] or (pygame.Rect(7 + 700, 57, 80, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0])):
            self.cellsize = c
            self.tlcorner = tlcorner
            self.whimg = self.font.render(f"W: {self.boardW}, H: {self.boardH}", False, "white", None).convert_alpha()

            if self.head.x == self.tail.x:
                snake = Snake(list(Cell(int(self.head.x), y) for y in range(int(self.tail.y), int(self.head.y) + (1 if self.tail.y <= self.head.y else -1), 1 if self.tail.y <= self.head.y else -1)), None)
            else:
                snake = Snake(list(Cell(x, int(self.head.y)) for x in range(int(self.tail.x), int(self.head.x) + (1 if self.tail.x <= self.head.x else -1), 1 if self.tail.x <= self.head.x else -1)), None)

            random.seed()
            seed = self.seed if self.seed != 0 else random.randint(1, 99999)
            self.seedimg = self.font.render("Seed: " + str(seed), False, "white", None).convert_alpha()

            self.board = Board(self.boardW, self.boardH, snake, seed)
            self.agent = PerfectAgent(self.board)

            self.timer = 0
            self.paused = self.speed == 0

            if self.skiptype:
                while len(self.board.snake)<self.skipto:
                    self.resoult = self.board.update(self.agent)
                    if self.resoult != 0:
                        break
            else:
                for x in range(self.skipto):
                    self.resoult = self.board.update(self.agent)
                    if self.resoult != 0:
                        break

            self.drawboard()

            if self.autosave:
                self.save()

            App.state = "game"

    def game(self):
        if not self.paused:
            self.timer += self.dt
            while self.resoult == 0 and self.speed>0 and self.timer>1/self.speed:
                self.timer-=1/self.speed
                self.resoult = self.board.update(self.agent)
        elif self.keys((pygame.K_n,))[0] or (pygame.Rect(7 + 600, 57, 80, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]):
            if self.resoult == 0:
                self.resoult = self.board.update(self.agent)

        self.screen.fill(self.backgroundcolor)
        pygame.draw.rect(self.screen, "black", pygame.Rect(0, 0, self.screen.width, 100))

        lengthimg = self.font.render("Length: " + str(len(self.board.snake.snake)), False, "white", None).convert_alpha()
        self.screen.blit(lengthimg, (10, 20))
        stepsimg = self.font.render("Steps: " + str(self.board.steps), False, "white", None).convert_alpha()
        self.screen.blit(stepsimg, (10, 60))

        self.screen.blit(self.whimg, (226, 20))

        if self.keys((pygame.K_SPACE,))[0] or (pygame.Rect(7 + 460, 57, 130, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]):
            self.paused = not self.paused

        if not self.paused:
            pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(7 + 460, 57, 100, 32))
            self.screen.blit(self.pauseimg, (10 + 460, 60))
        else:
            pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(7 + 460, 57, 130, 32))
            self.screen.blit(self.resumeimg, (10 + 460, 60))

            pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(7 + 600, 57, 80, 32))
            self.screen.blit(self.nextimg, (10 + 600, 60))

        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8 + 702, 57, 80, 32))
        self.screen.blit(self.stopimg, (10 + 702, 60))

        self.screen.blit(self.seedimg, (10 + 424, 20))

        if self.keys((pygame.K_b,))[0] or (pygame.Rect(8 + 618, 17, 164, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]):
            self.debug = not self.debug
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8 + 618, 17, 164, 32))
        self.screen.blit(self.debugonimg if self.debug else self.debugoffimg, (10 + 618, 20))

        self.drawboard()

        if self.keys((pygame.K_RETURN,))[0] or (pygame.Rect(7 + 700, 57, 80, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0] and not self.mouse[0][0]):
            self.selected = None
            self.board = None
            self.resoult = 0

            App.state = "setup"

    def drawboard(self):
        for x in range(self.boardW):
            for y in range(self.boardH):
                pygame.draw.rect(self.screen, self.boardcolor[(x + y) % 2], pygame.Rect(self.tlcorner.x + x * self.cellsize, self.tlcorner.y + y * self.cellsize, self.cellsize, self.cellsize), 0)

        l = len(self.board.snake.snake)-1
        i = 0
        snakeitter = self.board.snake.snake.__iter__()
        snakeitter.__next__()
        narrowmax = round(self.cellsize*(1/7))
        narrowmin = round(self.cellsize*(2/8))
        narrowhead = round(self.cellsize*(1/14))
        for c in self.board.snake.snake:
            if i == l: break
            c2 = snakeitter.__next__()
            facing = Cell.dirtonum(c.dirto(c2))
            narrow = round(pygame.math.lerp(narrowmin, narrowmax, i/l))
            if facing >=2:
                rect = pygame.Rect(self.tlcorner.x + c.x * self.cellsize + narrow, self.tlcorner.y + c.y * self.cellsize + narrow, 0, 0)
                if facing == 2:
                    rect.size = ((self.cellsize-narrow)*2, self.cellsize-narrow*2)
                else:
                    rect.size = (self.cellsize - narrow*2, (self.cellsize-narrow)*2)
            else:
                rect = pygame.Rect(self.tlcorner.x + c2.x * self.cellsize + narrow, self.tlcorner.y + c2.y * self.cellsize + narrow, 0, 0)
                if facing == 0:
                    rect.size = ((self.cellsize-narrow)*2, self.cellsize-narrow*2)
                else:
                    rect.size = (self.cellsize - narrow*2, (self.cellsize-narrow)*2)

            pygame.draw.rect(self.screen, self.colorgardient(self.bodygradient[0], self.bodygradient[1], i/l), rect, 0, round(self.cellsize / 2.5))
            i += 1

        #pygame.draw.rect(self.screen, self.headcolor, pygame.Rect(self.tlcorner.x + self.board.snake.head.x * self.cellsize + narrowhead, self.tlcorner.y + self.board.snake.head.y * self.cellsize + narrowhead, self.cellsize-narrowhead*2, self.cellsize-narrowhead*2), 0, round(self.cellsize / 2.5))
        headrect = pygame.Rect(self.tlcorner.x + self.board.snake.head.x * self.cellsize, self.tlcorner.y + self.board.snake.head.y * self.cellsize, self.cellsize, self.cellsize)
        self.draw_face(headrect, narrowhead, self.board.lastdir)

        if self.board.food.x != -1:
            self.draw_food(pygame.Rect(self.tlcorner.x + self.board.food.x * self.cellsize, self.tlcorner.y + self.board.food.y * self.cellsize, self.cellsize, self.cellsize))

        if self.debug:
            self.agent.draw_debug(self.screen, self.tlcorner, self.cellsize, self.boardW, self.boardH)

    def draw_face(self, rect, narrow, dir):
        surf = pygame.Surface(rect.size).convert_alpha()
        surf.fill((0, 0, 0, 0))
        w = rect.w-narrow*2
        h = rect.h-narrow*2
        center = pygame.Vector2(rect.w//2, rect.h//2)

        pygame.draw.rect(surf, self.headcolor, pygame.Rect(round(center.x-w*0.24), round(center.y-h*0.5), round(w*0.7), round(h*1)), 0, round(w*0.34))
        pygame.draw.rect(surf, self.headcolor, pygame.Rect(round(w*0.02), round(center.y-h*0.4), round(w*1.1), round(h*0.8)), 0, round(w*0.4))

        eye1 = pygame.Vector2(round(w*0.1), round(h*0.2))
        eye2 = pygame.Vector2(round(w*0.1), round(-h*0.2))

        pygame.draw.circle(surf, self.facecolors[0], eye1 + center, round(w*0.16))
        pygame.draw.circle(surf, self.facecolors[0], eye2 + center, round(w*0.16))

        innereye1 = pygame.Vector2(round(w * 0.022), round(h * 0.19))
        innereye2 = pygame.Vector2(round(w * 0.022), round(-h * 0.19))

        if round(w * 0.1)<round(w*0.16):
            pygame.draw.circle(surf, self.facecolors[1], innereye1 + center, round(w * 0.1))
            pygame.draw.circle(surf, self.facecolors[1], innereye2 + center, round(w * 0.1))

        nose1 = pygame.Vector2(round(-w * 0.35), round(h * 0.12))
        nose2 = pygame.Vector2(round(-w * 0.35), round(-h * 0.12))

        pygame.draw.circle(surf, self.facecolors[2], nose1 + center, int(w * 0.08))
        pygame.draw.circle(surf, self.facecolors[2], nose2 + center, int(w * 0.08))

        self.screen.blit(pygame.transform.rotate(surf, Cell.dirtonum(dir)*-90), rect)

    def draw_food(self, rect):
        w = rect.w
        h = rect.h
        center = pygame.Vector2(rect.center)

        pygame.draw.ellipse(self.screen, self.foodcolors[3], pygame.Rect(center.x+round(w*0.01), rect.y+round(h*0.015), round(w*0.3), round(h*0.13)))
        pygame.draw.rect(self.screen, self.foodcolors[2], pygame.Rect(center.x-round(w*0.035), rect.y+round(h*0.08), round(w*0.08), round(h*0.5)))

        pygame.draw.circle(self.screen, self.foodcolors[0], center + (0, round(h*0.12)), round(w * 0.38))
        pygame.draw.circle(self.screen, self.foodcolors[1], center + (round(-w*0.14), round(-h*0.08)), round(w * 0.12))

    def colorgardient(self, c1, c2, t):
        return c1.lerp(c2, t)

    def save(self, load=False):
        settings_attars = ("autosave", "speed", "skipto", "skiptype", "seed", "boardW", "boardH", "head", "tail", "debug")

        save = os.path.join('snake_settings.save')

        if load:
            try:
                with open(save, 'r') as file:
                    data = json.loads(file.read())
                print('reading save')

                for attr in settings_attars:
                    setattr(self, attr, data.get(attr, getattr(self, attr)))

            except FileNotFoundError:
                print('save not found, creating new save')
        else:
            #print("saving")
            pass

        settings_deafult = {attar: (getattr(self, attar) if not isinstance(getattr(self, attar), Cell) else (getattr(self, attar).toTouple())) for attar in settings_attars}
        with open(save, 'w') as file:
            file.write(json.dumps(settings_deafult, indent=4))

    def events(self) -> float:
        fps_start = time.perf_counter()
        self.key = -1
        self.chargot = False

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                self.key = event.key
            if event.type == pygame.TEXTINPUT:
                self.char = event.text
                self.chargot = True

            if event.type == pygame.WINDOWRESIZED and not self.fullscreen:
                self.winResolution = self.window.size

            if event.type == pygame.QUIT:
                self.quit()

        fps_end = time.perf_counter()

        self.keyboard = (self.keyboard[1], pygame.key.get_pressed())
        self.mouse = [self.mouse[1], pygame.mouse.get_pressed()]

        if self.keys((self.controls["Esc"],))[0]:
            self.quit()

        rect = self.logical_sizeRect.fit(pygame.Rect(0, 0, *self.window.size))

        self.mousePos[0].update(self.mousePos[1])
        self.mousePos[1].update(pygame.mouse.get_pos())
        self.mousePos[1].x -= rect.x
        self.mousePos[1].y -= rect.y
        if not (self.mouse[1][0] or self.mouse[1][2] or self.mouse[1][1]):
            self.mousePos[1].x = pygame.math.clamp(
                self.mousePos[1].x, 0, rect.w
            )
            self.mousePos[1].y = pygame.math.clamp(
                self.mousePos[1].y, 0, rect.h
            )
        self.mousePos[1].x *= self.logical_sizeRect.w / rect.w
        self.mousePos[1].y *= self.logical_sizeRect.h / rect.h
        self.mousePos[1].x = round(self.mousePos[1].x)
        self.mousePos[1].y = round(self.mousePos[1].y)

        self.mouseClicked = 0
        if self.mouse[1][0] and not self.mouse[0][0]:
            self.mouseClicked = 1
        if self.mouseClicked:
            self.mouseClickPos = self.mousePos[1]

        return fps_end - fps_start

    def inputToNum(self, value, minvalue, maxvalue):
        text = str(value)
        if self.keys((pygame.K_LCTRL,))[1] and self.keys((pygame.K_v,))[0]:
            temp = pygame.scrap.get_text()
            try:
                text = str(abs(int(temp)))
            except Exception:
                pass

        if self.keys((pygame.K_BACKSPACE,))[0]:
            text = text[:-1]
        if self.chargot and self.char in "0123456789":
            text += self.char
        text = min(int(text) if text else minvalue, maxvalue)

        if self.keys((pygame.K_LCTRL,))[1] and self.keys((pygame.K_c,))[0]:
            pygame.scrap.put_text(str(text))

        return text

    def keys(self, keys):
        pressed = 0
        held = 0
        released = 0
        for key in keys:
            if self.keyboard[1][key]:
                held += 1
                if not self.keyboard[0][key]:
                    pressed += 1
            elif self.keyboard[0][key]:
                released += 1

        return pressed, held, released

    def resize(self, scale=None):
        """
        if scale is None it toggles between fullscreen and last size
        if scale given it sets the window size to that
        """

        if hasattr(platform, "window"):
            return

        pygame.mouse.set_pos(0, 0)

        if scale is None:
            self.fullscreen = not self.fullscreen

            if self.fullscreen:
                self.window.set_fullscreen(True)
            else:
                self.window.set_windowed()
                self.winResolution = self.window.size
        else:
            rect = pygame.Rect(*self.window.position, *self.window.size)

            self.window.set_windowed()
            self.fullscreen = False
            self.winResolution = scale
            self.window.size = scale

            self.window.position = (
                rect.centerx - self.window.size[0] / 2,
                rect.centery - self.window.size[1] / 2,
            )

        rect = self.logical_sizeRect.fit(pygame.Rect(0, 0, *self.window.size))
        pygame.mouse.set_pos(
            self.mousePos[1].x / self.logical_sizeRect.w * rect.w + rect.x,
            self.mousePos[1].y / self.logical_sizeRect.h * rect.h + rect.y,
        )

    def quit(self):
        self.running = False
        pygame.mixer.music.stop()

        self.display.fill("Black")
        self.window.flip()

    def run(self):
        self.mousePos = (pygame.Vector2(0, 0), pygame.Vector2(0, 0))
        self.keyboard = (pygame.key.get_pressed(), pygame.key.get_pressed())
        self.mouse = (pygame.mouse.get_pressed(), pygame.mouse.get_pressed())
        self.mouseClickPos = self.mousePos[1]
        self.mouseClicked = 0
        self.events()
        frame = 0

        # sets window
        if self.fullscreen:
            self.resize(self.winResolution)
            self.resize()
        else:
            self.resize(self.winResolution)

        while self.running:  # main loop
            fps_start = time.perf_counter()

            prev_state = App.state

            event_time = self.events()

            if self.keys((pygame.K_f,))[0]:
                self.resize(None)

            self.display.fill(self.backgroundcolor)

            App.states[App.state]()  # runs current state

            rect = self.logical_sizeRect.fit(pygame.Rect(0, 0, *self.window.size))

            pygame.transform.scale(self.screen, rect.size, self.display.subsurface(rect))

            self.window.flip()

            App.prevState = prev_state

            # debug fps
            fps_end = time.perf_counter()
            dt = fps_end - fps_start - event_time
            if frame % 8 == 0 and dt:
                frame = 0
                self.window.title = (
                    f"Perfect Snake    "
                    f"FPS: {int(1 / dt):>4}, {round(self.clock.get_fps(), 1)} "
                    f"W:{self.window.size[0]} {self.window.size[1]} "
                )
            frame += 1

            self.clock.tick(self.fps)
            fps_end2 = time.perf_counter()
            self.dt = min(fps_end2 - fps_start - event_time, 0.1)

if __name__ == "__main__":
    app = App()
    app.run()
