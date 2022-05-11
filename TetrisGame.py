import sys
import random
import pygame
import threading
from datetime import datetime
import TetrisUtils as TUtils
from Settings import *


class TetrisGame:
    def __init__(self):
        self.tile_shape = None
        self.tile = None
        self.key_actions = None
        self.paused = False
        self.grid_size = None
        self.active = None
        self.score = 0.0
        self.lines = 0
        self.high_score = 0.0
        self.high_score_lines = 0
        self.fitness = 0.0

        if HAS_DISPLAY:
            self.log("Initializing system...", 3)
            pygame.init()
            pygame.font.init()

            self.screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
            self.log("Screen size set to: (" + str(SCREEN_WIDTH) + ", " + str(SCREEN_HEIGHT) + ")", 2)
            self.obs_size = GRID_ROW_COUNT * GRID_COL_COUNT
            pygame.event.set_blocked(pygame.MOUSEMOTION)
            self.init_game()

            self.on_score_changed_callbacks = []

            self.start()

    def init_game(self):
        self.log("Initializing game...", 2)
        self.active = True

        self.reset_board()

        self.grid_size = int(SCREEN_HEIGHT / GRID_ROW_COUNT)
        self.log("Tetris grid size calculated to: " + str(self.grid_size), 2)

        self.key_actions = {
            "ESCAPE": self.toggle_pause,
            "LEFT": lambda: self.move_tile(-1),
            "RIGHT": lambda: self.move_tile(1),
            "DOWN": lambda: self.drop(False),
            "SPACE": lambda: self.drop(True),
            "UP": self.rotate_tile,
            "TAB": self.swap_tile
        }

        self.generate_tile_bank()
        self.spawn_tile()

        self.score = 0
        self.lines = 0
        self.fitness = 0.0

    def start(self):
        self.active = True
        self.paused = False

        pygame.time.set_timer(pygame.USEREVENT + 1, SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(
            max(50, SPEED_DEFAULT - self.score * SPEED_SCALE)))
        clock = pygame.time.Clock()

        def loop():
            while True:

                if not STEP_ACTION:
                    self.update()

                if not STEP_ACTION or ALWAYS_DRAW:
                    self.draw()
                clock.tick(MAX_FPS)

        if STEP_ACTION:
            th = threading.Thread(target=loop, daemon=False)
            th.start()
        else:
            loop()

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:
                self.drop()
            elif event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN:
                for key in self.key_actions:
                    if event.key == eval("pygame.K_" + key):
                        self.key_actions[key]()

    def draw(self):

        self.screen.fill(TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")))

        for a in range(GRID_COL_COUNT):
            color = TUtils.get_color_tuple(COLORS.get("BACKGROUND_DARK" if a % 2 == 0 else "BACKGROUND_LIGHT"))
            pygame.draw.rect(self.screen, color,
                             (a * self.grid_size, 0, self.grid_size, SCREEN_HEIGHT))  # x, y, width, height

        self.draw_tiles(self.board)

        if DISPLAY_PREDICTION:
            self.draw_tiles(self.tile_shape, (
                self.tile_x, TUtils.get_effective_height(self.board, self.tile_shape, (self.tile_x, self.tile_y))),
                            True)

        self.draw_tiles(self.tile_shape, (self.tile_x, self.tile_y))

        margin = 20
        text_x_start = GRID_COL_COUNT * self.grid_size + margin
        text_y_start = margin

        message = MESSAGES.get("TITLE")
        if not self.active:
            message = "Game Over"
        elif self.paused:
            message = "= PAUSED ="
        text_image = pygame.font.SysFont(FONT_NAME, 32).render(message, False,
                                                               TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start = 60

        for msg in MESSAGES.get("CONTROLS").split("\n"):
            text_image = pygame.font.SysFont(FONT_NAME, 16).render(msg, False,
                                                                   TUtils.get_color_tuple(COLORS.get("WHITE")))
            self.screen.blit(text_image, (text_x_start, text_y_start))
            text_y_start += 20
        text_y_start += 10

        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("SCORE").format(self.score, self.lines),
                                                               False, TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        high_score = self.score if self.score > self.high_score else self.high_score
        high_score_lines = self.lines if self.lines > self.high_score_lines else self.high_score_lines
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(
            MESSAGES.get("HIGH_SCORE").format(high_score, high_score_lines), False,
            TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("FITNESS").format(self.fitness), False,
                                                               TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        speed = SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(max(50, SPEED_DEFAULT - self.score * SPEED_SCALE))
        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("SPEED").format(speed), False,
                                                               TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        text_image = pygame.font.SysFont(FONT_NAME, 16).render(MESSAGES.get("NEXT_TILE").format(self.get_next_tile()),
                                                               False, TUtils.get_color_tuple(COLORS.get("WHITE")))
        self.screen.blit(text_image, (text_x_start, text_y_start))
        text_y_start += 20

        self.draw_next_tile((text_x_start, text_y_start))
        text_y_start += 60

        pygame.display.update()

    def draw_tiles(self, matrix, offsets=(0, 0), outline_only=False):
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val == 0:
                    continue
                coord_x = (offsets[0] + x) * self.grid_size
                coord_y = (offsets[1] + y) * self.grid_size
                if not outline_only:
                    pygame.draw.rect(self.screen,
                                     TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x, coord_y, self.grid_size, self.grid_size))
                    pygame.draw.rect(self.screen,
                                     TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")),
                                     (coord_x, coord_y, self.grid_size, self.grid_size), 1)
                    offset = int(self.grid_size / 10)
                    pygame.draw.polygon(self.screen, TUtils.get_color_tuple(COLORS.get("TRIANGLE_GRAY")),
                                        ((coord_x + offset, coord_y + offset),
                                         (coord_x + 3 * offset, coord_y + offset),
                                         (coord_x + offset, coord_y + 3 * offset)))
                else:
                    pygame.draw.rect(self.screen,
                                     TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                     (coord_x + 1, coord_y + 1, self.grid_size - 2, self.grid_size - 2), 1)

    def draw_next_tile(self, offsets):
        size = int(self.grid_size * 0.75)
        for y, row in enumerate(TILE_SHAPES.get(self.get_next_tile())):
            for x, val in enumerate(row):
                if val == 0:
                    continue
                coord_x = offsets[0] + x * size
                coord_y = offsets[1] + y * size

                pygame.draw.rect(self.screen, TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x, coord_y, size, size))
                pygame.draw.rect(self.screen, TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")),
                                 (coord_x, coord_y, size, size), 1)

                offset = int(size / 10)
                pygame.draw.polygon(self.screen, TUtils.get_color_tuple(COLORS.get("TRIANGLE_GRAY")),
                                    ((coord_x + offset, coord_y + offset),
                                     (coord_x + 3 * offset, coord_y + offset),
                                     (coord_x + offset, coord_y + 3 * offset)))

    def spawn_tile(self):
        self.tile = self.get_next_tile(pop=True)
        self.tile_shape = TILE_SHAPES.get(self.tile)[:]
        self.tile_x = int(GRID_COL_COUNT / 2 - len(self.tile_shape[0]) / 2)
        self.tile_y = 0

        self.log("Spawning a new " + self.tile + " tile!", 1)
        if TUtils.check_collision(self.board, self.tile_shape, (self.tile_x, self.tile_y)):
            self.active = False
            self.paused = True

    def get_next_tile(self, pop=False):
        if not self.tile_bank:
            self.generate_tile_bank()
        return self.tile_bank[0] if not pop else self.tile_bank.pop(0)

    def drop(self, instant=False):
        if not self.active or self.paused:
            return
        if instant:
            destination = TUtils.get_effective_height(self.board, self.tile_shape, (self.tile_x, self.tile_y))
            self.score += PER_STEP_SCORE_GAIN * (destination - self.tile_y)
            self.tile_y = destination + 1
        else:
            self.tile_y += 1
            self.score += PER_STEP_SCORE_GAIN

        if not TUtils.check_collision(self.board, self.tile_shape, (self.tile_x, self.tile_y)) and not instant:
            return
        self.add_tile_to_board()
        self.calculate_scores()
        self.spawn_tile()

    def move_tile(self, delta):
        if not self.active or self.paused:
            return
        new_x = self.tile_x + delta
        new_x = max(0, min(new_x, GRID_COL_COUNT - len(self.tile_shape[0])))
        if TUtils.check_collision(self.board, self.tile_shape, (new_x, self.tile_y)):
            return
        self.tile_x = new_x

    def rotate_tile(self, pseudo=False):
        if not self.active or self.paused:
            return False, self.tile_x, self.tile_shape
        new_shape = TUtils.get_rotated_tile(self.tile_shape)
        temp_x = self.tile_x

        if self.tile_x + len(new_shape[0]) > GRID_COL_COUNT:
            temp_x = GRID_COL_COUNT - len(new_shape[0])

        if TUtils.check_collision(self.board, new_shape, (temp_x, self.tile_y)):
            return False, self.tile_x, self.tile_shape
        if not pseudo:
            self.tile_x = temp_x
            self.tile_shape = new_shape
        return True, temp_x, new_shape

    def swap_tile(self, pseudo=False):
        if not self.active or self.paused:
            return False, (self.tile_x, self.tile_y), self.tile_shape
        new_tile = self.get_next_tile(False)
        new_tile_shape = TILE_SHAPES.get(new_tile)[:]
        temp_x, temp_y = self.tile_x, self.tile_y

        if temp_x + len(self.tile_shape[0]) > GRID_COL_COUNT:
            temp_x = GRID_COL_COUNT - len(self.tile_shape[0])
        if temp_y + len(self.tile_shape) > GRID_ROW_COUNT:
            temp_y = GRID_ROW_COUNT - len(self.tile_shape)

        if TUtils.check_collision(self.board, new_tile_shape, (temp_x, temp_y)):
            return False, (self.tile_x, self.tile_y), self.tile_shape

        if not pseudo:
            self.get_next_tile(True)
            self.tile_bank.insert(0, self.tile)

            self.tile = new_tile
            self.tile_shape = new_tile_shape
            self.tile_x, self.tile_y = temp_x, temp_y
        return True, (temp_x, temp_y), new_tile_shape

    def calculate_scores(self):
        score_count = 0
        row = 0
        while True:
            if row >= len(self.board):
                break
            if 0 in self.board[row]:
                row += 1
                continue

            del self.board[row]

            self.board.insert(0, [0] * GRID_COL_COUNT)
            score_count += 1

        self.fitness = TUtils.get_fitness_score(self.board)

        if score_count == 0:
            return

        total_score = MULTI_SCORE_ALGORITHM(score_count)
        for callback in self.on_score_changed_callbacks:
            callback(self.score, self.score + total_score)

        self.score += total_score
        self.lines += score_count
        self.log("Cleared " + str(score_count) + " rows with score " + str(total_score), 3)
        pygame.time.set_timer(pygame.USEREVENT + 1, SPEED_DEFAULT if not SPEED_SCALE_ENABLED else int(
            max(50, SPEED_DEFAULT - self.score * SPEED_SCALE)))

    def add_tile_to_board(self):
        for cy, row in enumerate(self.tile_shape):
            for cx, val in enumerate(row):
                if val == 0:
                    continue
                self.board[cy + self.tile_y - 1][min(cx + self.tile_x, 9)] = val

    def reset(self):
        self.log("Resetting game...", 2)
        if self.score > self.high_score:
            self.high_score = self.score
        if self.lines > self.high_score_lines:
            self.high_score_lines = self.lines
        self.init_game()
        return self.board[:]

    def reset_board(self):
        self.board = [[0] * GRID_COL_COUNT for _ in range(GRID_ROW_COUNT)]

    def toggle_pause(self):
        if not self.active:
            self.reset()
            self.paused = False
            return
        self.paused = not self.paused
        self.log(("Pausing" if self.paused else "Resuming") + " game...", 2)

    def quit(self):
        sys.exit()

    def generate_tile_bank(self):
        self.tile_bank = list(TILE_SHAPES.keys())
        random.shuffle(self.tile_bank)

    def print_board(self, flattened=False):
        TUtils.print_board(
            TUtils.get_board_with_tile(self.board, self.tile_shape, (self.tile_x, self.tile_y), flattened))

    def log(self, message, level):
        if MIN_DEBUG_LEVEL > level:
            return
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        print(f"[{level}] {current_time} >> {message}")

    def subscribe_on_score_changed(self, callback):
        self.on_score_changed_callbacks.append(callback)

    def step(self, action=0, use_fitness=False):

        if HAS_DISPLAY:
            pygame.event.get()

        previous_fitness = self.fitness
        previous_score = self.score

        if action in [1, 2, 3, 4]:
            self.move_tile((-1 if action in [1, 3] else 1) * (1 if action in [1, 2] else 2))

        elif action == 5:
            self.rotate_tile()

        elif action == 6:
            self.swap_tile()

        elif action in [7, 8]:
            self.drop(instant=(action == 8))
        self.drop()
        measurement = self.score - previous_score
        if use_fitness:
            measurement = self.fitness - previous_fitness
        board = TUtils.get_board_with_tile(self.board, self.tile_shape, (self.tile_x, self.tile_y), True)
        return board, measurement, not self.active, self.get_next_tile()


if __name__ == "__main__":
    print("Hello world!")
    HAS_DISPLAY = True
    STEP_ACTION = False
    TetrisGame()
    print("Goodbye world!")
