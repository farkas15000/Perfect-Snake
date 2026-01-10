import platform
import pygame
import time

import win32api
from PIL import ImageGrab
import keyboard

from board import Cell, Snake
from board_TAS import Board
from baseagent import BaseAgent

from perfect_agent import PerfectAgent as Agent

class App:
    st = None
    state = "start"
    states = {}

    def __init__(self):

        self.fullscreen = False

        self.controls = {
            "Esc": pygame.K_ESCAPE,
        }

        self.winResolution = 600, 600

        self.states.update({"start": self.start,
                            "board": self.board,
                            "game": self.game,
                            })
        App.st = self

        if hasattr(platform, "window"):
            self.mobile = platform.window.mobile_check() or platform.window.mobile_tablet()
        else:
            self.mobile = False

        pygame.init()
        self.clock = pygame.time.Clock()

        self.logical_sizeRect = pygame.Rect(0, 0, 600, 600)

        self.window = pygame.Window(size=self.winResolution)
        self.window.resizable = True
        self.window.title = "Snake TAS"

        self.display = self.window.get_surface()
        self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

        self.font = pygame.font.Font(size=45)

        self.dt = 0.016
        self.running = True
        self.mousePos = None
        self.mouseClickPos = None
        self.mouseClicked = False
        self.mouse = None
        self.keyboard = None

        self.tl = pygame.Vector2(60, 60)
        self.br = pygame.Vector2(0, 0)

        self.img = None
        self.field: Board|None = None
        self.fieldw = 0
        self.fieldh = 0
        self.cellw = 0
        self.cellh = 0
        self.head = None
        self.tail = None
        self.agent: BaseAgent|None = None

    def start(self):
        # to select screenshot space press q while mouse at top left corner on game and press e while mouse at bottom left on game board.
        # after selection press space

        self.screen.fill("black")

        if keyboard.is_pressed("q"):
            self.tl = pygame.Vector2(win32api.GetCursorPos())

        if keyboard.is_pressed("e"):
            self.br = pygame.Vector2(win32api.GetCursorPos())

        imgtl = ImageGrab.grab((self.tl.x-60, self.tl.y-60, *self.tl), False, True)
        imgtl = pygame.image.frombytes(imgtl.tobytes(), imgtl.size, imgtl.mode)
        self.screen.blit(imgtl, (0, 0))

        imgbr = ImageGrab.grab((*self.br, self.br.x + 60, self.br.y + 60), False, True)
        imgbr = pygame.image.frombytes(imgbr.tobytes(), imgbr.size, imgbr.mode)
        self.screen.blit(imgbr, (80, 0))

        if keyboard.is_pressed("space") and self.tl.x<self.br.x and self.tl.y<self.br.y:
            self.tl = getcorner(imgtl, pygame.Vector2(imgtl.size)-(1, 1), pygame.Vector2(-1, -1)) + self.tl-(60, 60)
            self.br = getcorner(imgbr, pygame.Vector2(0, 0), pygame.Vector2(1, 1)) + self.br - (1, 1)

            App.state = "board"

    def board(self):
        # set board width and height while mouse is hovering ower it.
        # place snake head with left click on board and place snake tail with right click on board.
        # plick back to real game to be in focus and press space to start.

        #if not self.img or self.keys((pygame.K_RETURN,))[0]:
        img = ImageGrab.grab((*self.tl, *self.br), False, True)
        self.img = pygame.image.frombytes(img.tobytes(), img.size, img.mode)

        if self.logical_sizeRect.w!=max(self.img.width, 500) or self.logical_sizeRect.height!=self.img.height+100:
            self.logical_sizeRect.size = (max(self.img.width, 500), self.img.height+100)
            self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

        self.screen.fill("black")

        tlcorner = pygame.Vector2(max(self.img.width, 500)//2-self.img.width//2, 100)
        self.screen.blit(self.img, tlcorner)

        fieldwprev = self.fieldw
        if pygame.Rect(8, 17, 100, 32).collidepoint(self.mousePos[1]):
            self.fieldw = self.inputToNum(self.fieldw, 0, 100)
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8, 17, 100, 32))

        fieldhprev = self.fieldh
        if pygame.Rect(8+110, 17, 100, 32).collidepoint(self.mousePos[1]):
            self.fieldh = self.inputToNum(self.fieldh, 0, 100)
        pygame.draw.rect(self.screen, (25, 25, 25), pygame.Rect(8+110, 17, 100, 32))

        widthimg = self.font.render("W: "+str(self.fieldw), False, "white", None).convert_alpha()
        self.screen.blit(widthimg, (10, 20))
        heightimg = self.font.render("H: "+str(self.fieldh), False, "white", None).convert_alpha()
        self.screen.blit(heightimg, (120, 20))

        cellw = self.img.width/max(self.fieldw, 1)
        cellh = self.img.height/max(self.fieldh, 1)
        for x in range(1, self.fieldw):
            pygame.draw.line(self.screen, "black", (tlcorner.x+int(x*cellw), 100), (tlcorner.x+int(x*cellw), self.screen.height-1))
            pygame.draw.line(self.screen, "black", (tlcorner.x+int(x*cellw)+1, 100), (tlcorner.x+int(x*cellw)+1, self.screen.height-1))

        for y in range(1, self.fieldh):
            pygame.draw.line(self.screen, "black", (tlcorner.x, tlcorner.y+int(y*cellh)), (tlcorner.x+self.img.width, tlcorner.y+int(y*cellh)))
            pygame.draw.line(self.screen, "black", (tlcorner.x, tlcorner.y+int(y*cellh)+1), (tlcorner.x+self.img.width, tlcorner.y+int(y*cellh)+1))

        if self.fieldw == fieldwprev and self.fieldh == fieldhprev:
            x = int((self.mousePos[1][0]-tlcorner.x)//cellw)
            if not (0<=x<=self.fieldw-1):
                x=None

            y = int((self.mousePos[1][1] - tlcorner.y) // cellh)
            if not (0 <= y <= self.fieldh-1):
                y = None

            if x is not None and y is not None:
                if self.mouse[1][0]:
                    self.head = Cell(x, y)

                if self.mouse[1][2]:
                    self.tail = Cell(x, y)
        else:
            self.head = None
            self.tail = None

        if self.tail is not None:
            pygame.draw.rect(self.screen, "orange", pygame.Rect(tlcorner.x+self.tail.x*cellw, tlcorner.y+self.tail.y*cellh, round(cellw), round(cellh)), 3, round(cellw/3))

        ready = False
        if self.head is not None and self.tail is not None and (self.head.x == self.tail.x or self.head.y == self.tail.y):
            ready = True
            pygame.draw.rect(self.screen, "orange", pygame.Rect(tlcorner.x+min(self.head.x, self.tail.x)*cellw, tlcorner.y+min(self.head.y, self.tail.y)*cellh, round(cellw)*(abs(self.head.x-self.tail.x)+1), round(cellh)*(abs(self.head.y-self.tail.y)+1)), 3, round(cellw/3))

        if self.head is not None:
            pygame.draw.rect(self.screen, "blue", pygame.Rect(tlcorner.x+self.head.x*cellw, tlcorner.y+self.head.y*cellh, round(cellw), round(cellh)), 3, round(cellw/3))

        if ready and keyboard.is_pressed("space") and not self.window.focused:
            img = ImageGrab.grab((*self.tl, *self.br), False, True)
            self.img = pygame.image.frombytes(img.tobytes(), img.size, img.mode)

            self.cellw = cellw
            self.cellh = cellh

            if self.head.x == self.tail.x:
                snake = Snake(list(Cell(int(self.head.x), y) for y in range(int(self.tail.y), int(self.head.y)+(1 if self.tail.y<=self.head.y else -1), 1 if self.tail.y<=self.head.y else -1)), None)
            else:
                snake = Snake(list(Cell(x, int(self.head.y)) for x in range(int(self.tail.x), int(self.head.x)+(1 if self.tail.x<=self.head.x else -1), 1 if self.tail.x<=self.head.x else -1)), None)

            self.field = Board(self.fieldw, self.fieldh, snake)

            self.agent = Agent(self.field)

            App.state = "game"

    def game(self):
        # press enter to restart setup

        if keyboard.is_pressed("esc"):
            self.quit()

        if self.field.resoult == 0:
            img = ImageGrab.grab((*self.tl, *self.br), False, True)
            self.img = pygame.image.frombytes(img.tobytes(), img.size, img.mode)

        tlcorner = pygame.Vector2(max(self.img.width, 500) // 2 - self.img.width // 2, 100)
        self.screen.fill("black")
        self.screen.blit(self.img, tlcorner)

        pygame.draw.rect(self.screen, self.field.headcolor, pygame.Rect(10, 10, 30, 30))
        pygame.draw.rect(self.screen, self.field.foodcolor, pygame.Rect(50, 10, 30, 30))

        dir = self.field.update(self.agent, self.img)
        if dir is not None:
            keyboard.press_and_release(Cell.dirtokeycode(dir))

        if self.field.food is not None:
            pygame.draw.rect(self.screen, "red", pygame.Rect(tlcorner.x + self.field.food.x * self.cellw + 3, tlcorner.y + self.field.food.y * self.cellh + 3, round(self.cellw)-6, round(self.cellh)-6), 3, round(self.cellw / 3))

        for cell in self.field.snake.snake:
            pygame.draw.rect(self.screen, "blue", pygame.Rect(tlcorner.x + cell.x * self.cellw, tlcorner.y + cell.y * self.cellh, round(self.cellw), round(self.cellh)), 3, round(self.cellw / 3))

        if self.keys((pygame.K_RETURN,))[0]:
            self.agent = None
            self.field = None
            self.img = None
            App.state = "board"

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

    def inputToNum(self, value, minvalue, maxvalue):
        text = str(value)
        if self.keys((pygame.K_LCTRL,))[1] and self.keys((pygame.K_v,))[0] and not self.web:
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

        if self.keys((pygame.K_LCTRL,))[1] and self.keys((pygame.K_c,))[0] and not self.web:
            pygame.scrap.put_text(str(text))

        return text

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

            self.display.fill((25, 25, 25, 255))

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
                    f"Snake TAS    "
                    f"FPS: {int(1 / dt)}, {round(self.clock.get_fps(), 1)} "
                    f"W:{self.window.size[0]} {self.window.size[1]} "
                )
            frame += 1

            self.clock.tick(60)
            fps_end2 = time.perf_counter()
            self.dt = min(fps_end2 - fps_start - event_time, 0.1)

def getcorner(surf:pygame.Surface, start, dir):
    c = surf.get_at(start)

    xpos = start.x
    for x in range(60):
        if surf.get_at((x*dir.x + start.x, start.y))!=c:
            xpos = x*dir.x+start.x+1
            break

    ypos = start.y
    for y in range(60):
        if surf.get_at((start.x, y * dir.y + start.y)) != c:
            ypos = y * dir.y + start.y+1
            break

    return pygame.Vector2(xpos, ypos)

def colordif(color1, color2):
    return (abs(color1[0]-color2[0])+abs(color1[1]-color2[1])+abs(color1[2]-color2[2]))/(3*255)

if __name__ == "__main__":
    app = App()
    app.run()
