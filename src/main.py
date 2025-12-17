import platform
import pygame
import time

from board import Board
from cell import Cell
from snake import Snake
from agent import Agent


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

        self.logical_sizeRect = pygame.Rect(0, 0, 800, 900)

        self.window = pygame.Window(size=self.winResolution)
        self.window.resizable = True
        self.window.title = "Perfect Snake"

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

        self.fps = 60
        self.speed = 8
        self.selected = None
        self.board: Board | None = None
        self.boardW = 10
        self.boardH = 10
        self.cellsize = 0
        self.tlcorner = None
        self.head = None
        self.tail = None
        self.agent: Agent|None = None
        self.resoult = 0

    def setup(self):
        if self.mouse[1][0]:
            self.selected = None

        self.screen.fill("black")

        boardWprev = self.boardW
        if pygame.Rect(8, 17, 110, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "boardW"
        if self.selected == "boardW":
            self.boardW = self.inputToNum(self.boardW, 0, 100)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "boardW" else (25, 25, 25), pygame.Rect(8, 17, 110, 32))
        widthimg = self.font.render("W: " + str(self.boardW), False, "white", None).convert_alpha()
        self.screen.blit(widthimg, (10, 20))

        boardHprev = self.boardH
        if pygame.Rect(8 + 120, 17, 110, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "boardH"
        if self.selected == "boardH":
            self.boardH = self.inputToNum(self.boardH, 0, 100)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "boardH" else (25, 25, 25), pygame.Rect(8 + 120, 17, 110, 32))
        heightimg = self.font.render("H: " + str(self.boardH), False, "white", None).convert_alpha()
        self.screen.blit(heightimg, (10 + 120, 20))

        if pygame.Rect(8 + 240, 17, 210, 32).collidepoint(self.mousePos[1]) and self.mouse[1][0]:
            self.selected = "speed"
        if self.selected == "speed":
            self.speed = self.inputToNum(self.speed, 0, 1000)
        pygame.draw.rect(self.screen, (60, 60, 60) if self.selected == "speed" else (25, 25, 25), pygame.Rect(8 + 240, 17, 210, 32))
        speedimg = self.font.render("Steps: " + str(self.speed) + "/s", False, "white", None).convert_alpha()
        self.screen.blit(speedimg, (10 + 240, 20))

        c = max(min(800//max(self.boardW, 1), 800//max(self.boardH, 1)), 8)
        w = self.boardW*c
        h = self.boardH*c
        tlcorner = pygame.Vector2(max(w, 600) // 2 - w // 2, 100)

        if boardWprev!=self.boardW or boardHprev!=self.boardH:
            self.logical_sizeRect.size = (max(w, 600), h+100)
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
                    self.head = pygame.Vector2(x, y)

                if self.mouse[1][2]:
                    self.tail = pygame.Vector2(x, y)

        pygame.draw.rect(self.screen, (40, 40, 40, 255), pygame.Rect(*tlcorner, w, h), width=0)

        for x in range(1, self.boardW):
            pygame.draw.line(self.screen, "black", (tlcorner.x + x * c, 100), (tlcorner.x + x * c, self.screen.height - 1))
            pygame.draw.line(self.screen, "black", (tlcorner.x + x * c + 1, 100), (tlcorner.x + x * c + 1, self.screen.height - 1))

        for y in range(1, self.boardH):
            pygame.draw.line(self.screen, "black", (tlcorner.x, tlcorner.y + y * c), (tlcorner.x + w, tlcorner.y + y * c))
            pygame.draw.line(self.screen, "black", (tlcorner.x, tlcorner.y + y * c + 1), (tlcorner.x + h, tlcorner.y + y * c + 1))

        ready = False
        if self.head is not None and self.tail is not None and (self.head.x == self.tail.x or self.head.y == self.tail.y) and self.head.distance_to(self.tail)>=2:
            ready = True
            pygame.draw.rect(self.screen, "orange", pygame.Rect(tlcorner.x+min(self.head.x, self.tail.x)*c, tlcorner.y+min(self.head.y, self.tail.y)*c, c*(abs(self.head.x-self.tail.x)+1), c*(abs(self.head.y-self.tail.y)+1)), 3, round(c/2.5))
        elif self.tail is not None:
            pygame.draw.rect(self.screen, "orange", pygame.Rect(tlcorner.x+self.tail.x*c, tlcorner.y+self.tail.y*c, c, c), 3, round(c/2.5))

        if self.head is not None:
            pygame.draw.rect(self.screen, "blue", pygame.Rect(tlcorner.x+self.head.x*c, tlcorner.y+self.head.y*c, c, c), 3, round(c/2.5))

        if ready and self.keys((pygame.K_SPACE,))[0]:
            self.cellsize = c
            self.tlcorner = tlcorner

            if self.head.x == self.tail.x:
                snake = Snake(list(Cell(int(self.head.x), y) for y in range(int(self.tail.y), int(self.head.y) + (1 if self.tail.y <= self.head.y else -1), 1 if self.tail.y <= self.head.y else -1)), None)
            else:
                snake = Snake(list(Cell(x, int(self.head.y)) for x in range(int(self.tail.x), int(self.head.x) + (1 if self.tail.x <= self.head.x else -1), 1 if self.tail.x <= self.head.x else -1)), None)

            self.board = Board(self.boardW, self.boardH, snake)
            self.agent = Agent(self.board)

            self.drawboard()

            App.state = "game"

    def game(self):
        if self.resoult == 0 :
            self.resoult = self.board.update(self.agent)

        self.screen.fill("black")

        lengthimg = self.font.render("Length: " + str(len(self.board.snake.snake)), False, "white", None).convert_alpha()
        self.screen.blit(lengthimg, (10, 20))
        stepsimg = self.font.render("Steps: " + str(self.board.steps), False, "white", None).convert_alpha()
        self.screen.blit(stepsimg, (10, 55))

        self.drawboard()

        if self.keys((pygame.K_SPACE,))[0]:
            self.selected = None
            self.board = None
            self.resoult = 0

            App.state = "setup"


    def drawboard(self):
        for x in range(self.boardW):
            for y in range(self.boardH):
                pos = Cell(x, y)
                color = (30, 30, 30, 255) if (x + y) % 2 else (40, 40, 40, 255)
                pygame.draw.rect(self.screen, color, pygame.Rect(self.tlcorner.x + x * self.cellsize, self.tlcorner.y + y * self.cellsize, self.cellsize, self.cellsize), 0)
                if pos.toString() in self.board.snake.cells:
                    pygame.draw.rect(self.screen, (0, 0, 120, 255), pygame.Rect(self.tlcorner.x + x * self.cellsize, self.tlcorner.y + y * self.cellsize, self.cellsize, self.cellsize), 0, round(self.cellsize / 3))

        pygame.draw.rect(self.screen, "red", pygame.Rect(self.tlcorner.x + self.board.food.x * self.cellsize, self.tlcorner.y + self.board.food.y * self.cellsize, self.cellsize, self.cellsize), 0, round(self.cellsize / 2))

        pygame.draw.rect(self.screen, (0, 0, 80, 255), pygame.Rect(self.tlcorner.x + self.board.snake.head().x * self.cellsize, self.tlcorner.y + self.board.snake.head().y * self.cellsize, self.cellsize, self.cellsize), 0, round(self.cellsize / 2.5))

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
        if self.keys((pygame.K_BACKSPACE,))[0]:
            text = text[:-1]
        if self.chargot and self.char in "0123456789":
            text += self.char
        text = min(int(text) if text else minvalue, maxvalue)
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
                    f"FPS: {int(1 / dt)}, {round(self.clock.get_fps(), 1)} "
                    f"W:{self.window.size[0]} {self.window.size[1]} "
                )
            frame += 1

            self.clock.tick(self.fps)
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

if __name__ == "__main__":
    app = App()
    app.run()
