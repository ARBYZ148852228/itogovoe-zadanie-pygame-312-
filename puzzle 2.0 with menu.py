import pygame
import random
import os
import sys
import time
import abc

# ----------- Настройки ------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
BACKGROUND = (0, 50, 0)
FPS = 60
ROWS, COLS = 3, 3
MARGIN = 2

# ----------- Инициализация ------------
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Пазлы")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 64)

# ----------- Абстрактный экран ------------
class State(abc.ABC):
    @abc.abstractmethod
    def handle_events(self, events): pass
    @abc.abstractmethod
    def update(self): pass
    @abc.abstractmethod
    def draw(self, screen): pass

# ----------- Экран заставки ------------
class SplashScreen(State):
    def __init__(self):
        self.title = font.render("ПАЗЛЫ", True, (255, 255, 255))
        self.hint = font.render("Нажмите любую клавишу", True, (200, 255, 200))
        self.blink = True
        self.last_blink = pygame.time.get_ticks()

    def handle_events(self, events):
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return MenuScreen()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return self

    def update(self):
        if pygame.time.get_ticks() - self.last_blink > 500:
            self.blink = not self.blink
            self.last_blink = pygame.time.get_ticks()

    def draw(self, screen):
        screen.fill(BACKGROUND)
        screen.blit(self.title, self.title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
        if self.blink:
            screen.blit(self.hint, self.hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))

# ----------- Экран меню ------------
class MenuScreen(State):
    def __init__(self):
        self.play_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 300, 200, 50)
        self.quit_button = pygame.Rect(SCREEN_WIDTH//2 - 100, 370, 200, 50)
        self.input_box = pygame.Rect(SCREEN_WIDTH//2 - 100, 200, 200, 50)
        self.input_active = False
        self.name = ""

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.play_button.collidepoint(event.pos):
                    return GameScreen(self.name or "Игрок")
                elif self.quit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif self.input_box.collidepoint(event.pos):
                    self.input_active = True
                else:
                    self.input_active = False
            elif event.type == pygame.KEYDOWN and self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif len(self.name) < 12:
                    self.name += event.unicode
        return self

    def update(self):
        pass

    def draw(self, screen):
        screen.fill((20, 20, 20))
        pygame.draw.rect(screen, (100, 100, 100), self.input_box, 2)
        pygame.draw.rect(screen, (70, 130, 70), self.play_button)
        pygame.draw.rect(screen, (130, 70, 70), self.quit_button)

        input_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(input_text, (self.input_box.x + 10, self.input_box.y + 10))
        screen.blit(font.render("Играть", True, (255, 255, 255)), (self.play_button.x + 40, self.play_button.y + 10))
        screen.blit(font.render("Выход", True, (255, 255, 255)), (self.quit_button.x + 40, self.quit_button.y + 10))

# ----------- Экран игры ------------
class GameScreen(State):
    def __init__(self, player_name):
        self.player_name = player_name
        self.load_puzzle()
        self.start_time = time.time()

    def load_puzzle(self):
        pics = [f for f in os.listdir('pictures') if f.endswith(('.png','.jpg','.jpeg'))]
        img = pygame.image.load(os.path.join('pictures', random.choice(pics)))
        img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.tiles = []
        self.original = []
        tile_w, tile_h = SCREEN_WIDTH // COLS, SCREEN_HEIGHT // ROWS

        for i in range(ROWS):
            for j in range(COLS):
                rect = pygame.Rect(j*tile_w, i*tile_h, tile_w, tile_h)
                surf = img.subsurface(rect)
                self.tiles.append(surf)

        self.original = self.tiles.copy()
        random.shuffle(self.tiles)
        self.selected = None
        self.swaps = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                col = x // (SCREEN_WIDTH // COLS)
                row = y // (SCREEN_HEIGHT // ROWS)
                index = row * COLS + col

                if self.selected is not None and self.selected != index:
                    self.tiles[self.selected], self.tiles[index] = self.tiles[index], self.tiles[self.selected]
                    self.swaps += 1
                    self.selected = None
                else:
                    self.selected = index
        return self

    def update(self):
        if time.time() - self.start_time > 15:
            return GameOverScreen(f"{self.player_name}, время вышло!")
        if self.tiles == self.original:
            return GameOverScreen(f"{self.player_name}, победа!")
        return self

    def draw(self, screen):
        screen.fill((0, 0, 0))
        tile_w, tile_h = SCREEN_WIDTH // COLS, SCREEN_HEIGHT // ROWS
        for i in range(ROWS * COLS):
            x = (i % COLS) * tile_w
            y = (i // COLS) * tile_h
            screen.blit(self.tiles[i], (x, y))
        swap_text = font.render(f"Перестановки: {self.swaps}", True, (255,255,255))
        time_text = font.render(f"Время: {int(15 - (time.time() - self.start_time))}", True, (255,255,255))
        screen.blit(swap_text, (10, 10))
        screen.blit(time_text, (10, 70))

# ----------- Экран конца игры ------------
class GameOverScreen(State):
    def __init__(self, message):
        self.message = message
        self.timer = pygame.time.get_ticks()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        return self

    def update(self):
        if pygame.time.get_ticks() - self.timer > 3000:
            return SplashScreen()
        return self

    def draw(self, screen):
        screen.fill((0, 0, 0))
        msg = font.render(self.message, True, (255,255,255))
        screen.blit(msg, msg.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

# ----------- Главный цикл ------------
state = SplashScreen()
while True:
    events = pygame.event.get()
    next_state = state.handle_events(events)
    if next_state is not None:
        state = next_state
    state = state.update() or state
    state.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)
