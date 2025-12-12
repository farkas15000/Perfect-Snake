import platform
import pygame
import time
import random

import win32api
from PIL import ImageGrab
import keyboard


class App:
    st = None
    state = "menu"
    states = {}

    def __init__(self):

        self.fullscreen = False

        self.controls = {
            "Esc": pygame.K_ESCAPE,
        }

        self.winResolution = 600, 600

        self.states.update({"menu": self.menu,
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
        self.window.title = "Perfect Snake"

        self.display = self.window.get_surface()
        self.screen = pygame.Surface(self.logical_sizeRect.size).convert()

        self.dt = 0.016
        self.running = True
        self.mousePos = None
        self.mouseClickPos = None
        self.mouseClicked = False
        self.mouse = None
        self.keyboard = None

        self.tl = pygame.Vector2(60, 60)
        self.br = pygame.Vector2(0, 0)

    def menu(self):
        self.screen.fill("black")

        if self.keys((pygame.K_q,))[0]:
            self.tl = pygame.Vector2(win32api.GetCursorPos())

        if self.keys((pygame.K_e,))[0]:
            self.br = pygame.Vector2(win32api.GetCursorPos())

        imgtl = ImageGrab.grab((self.tl.x-60, self.tl.y-60, *self.tl), False, True)
        imgtl = pygame.image.frombytes(imgtl.tobytes(), imgtl.size, imgtl.mode)
        self.screen.blit(imgtl, (0, 0))

        imgbr = ImageGrab.grab((*self.br, self.br.x + 60, self.br.y + 60), False, True)
        imgbr = pygame.image.frombytes(imgbr.tobytes(), imgbr.size, imgbr.mode)
        self.screen.blit(imgbr, (80, 0))

        if self.keys((pygame.K_SPACE,))[0]:
            self.tl += getcorner(imgtl, pygame.Vector2(imgtl.size)-(1, 1), pygame.Vector2(-1, -1))
            self.br += getcorner(imgbr, pygame.Vector2(0, 0), pygame.Vector2(1, 1))-(61, 61)


    def game(self):
        pass

    def events(self) -> float:
        fps_start = time.perf_counter()

        for event in pygame.event.get():
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

if __name__ == "__main__":
    app = App()
    app.run()
