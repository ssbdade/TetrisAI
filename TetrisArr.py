import random
import TetrisUtils as TUtils
from Settings import *


class Tetris:

    def __init__(self):
        self.game_over = True
        self.board = []
        self.tile_pool = []
        self.current_tile = ""
        self.next_tile = ""
        self.tile_x = 0
        self.tile_y = 0
        self.tile_shape = []
        self.score = 0.0
        self.line_clear = 0
        self.reset_game()

    def reset_game(self):
        self.game_over = False
        self.board = [[0] * GRID_COL_COUNT for _ in range(GRID_ROW_COUNT)]
        self.spawn_tile()
        self.score = 0.0

    def step(self, action: int):
        assert action in list(range(8 + 1)), "Invalid action, use 0-8 for actions"
        if self.game_over:
            return
        if action in [1, 2, 3, 4]:
            self.move_tile((-1 if action in [1, 3] else 1) * (1 if action in [1, 2] else 2))
        elif action == 5:
            self.rotate_tile()
        elif action == 6:
            self.swap_tile()
        elif action in [7, 8]:
            self.drop_tile(instant=(action == 8))
        self.drop_tile()

    def spawn_tile(self) -> bool:
        self.current_tile = self.get_next_tile(pop=True)
        self.tile_shape = TILE_SHAPES[self.current_tile][:]
        self.tile_x = int(GRID_COL_COUNT / 2 - len(self.tile_shape[0]) / 2)
        self.tile_y = 0
        return TUtils.check_collision(self.board, self.tile_shape, (self.tile_x, self.tile_y))

    def generate_tile_pool(self):
        self.tile_pool = list(TILE_SHAPES.keys())
        random.shuffle(self.tile_pool)

    def on_tile_collision(self):
        for cy, row in enumerate(self.tile_shape):
            for cx, val in enumerate(row):
                if val == 0:
                    continue
                self.board[cy + self.tile_y - 1][min(cx + self.tile_x, 9)] = val

        row_completed = 0
        row_index = 0
        while True:
            if row_index >= len(self.board):
                break
            if 0 in self.board[row_index]:
                row_index += 1
                continue
            del self.board[row_index]
            self.board.insert(0, [0] * GRID_COL_COUNT)
            row_completed += 1
            self.line_clear +=1

        self.score += MULTI_SCORE_ALGORITHM(row_completed)

        self.game_over = self.spawn_tile()

    def drop_tile(self, instant=False):

        if instant:
            new_y = TUtils.get_effective_height(self.board, self.tile_shape, (self.tile_x, self.tile_y))
            self.tile_y = new_y + 1
            self.score += PER_STEP_SCORE_GAIN * (new_y - self.tile_y)
        else:
            self.tile_y += 1
            self.score += PER_STEP_SCORE_GAIN

        if not instant and not TUtils.check_collision(self.board, self.tile_shape, (self.tile_x, self.tile_y)):
            return
        self.on_tile_collision()

    def move_tile(self, delta: int):
        assert delta in [-2, -1, 1, 2], "Invalid move distance"
        new_x = self.tile_x + delta
        new_x = max(0, min(new_x, GRID_COL_COUNT - len(self.tile_shape[0])))  # clamping
        if TUtils.check_collision(self.board, self.tile_shape, (new_x, self.tile_y)):
            return
        self.tile_x = new_x

    def rotate_tile(self):
        new_tile_shape = TUtils.get_rotated_tile(self.tile_shape)
        new_x = self.tile_x
        if self.tile_x + len(new_tile_shape[0]) > GRID_COL_COUNT:
            new_x = GRID_COL_COUNT - len(new_tile_shape[0])

        if TUtils.check_collision(self.board, new_tile_shape, (new_x, self.tile_y)):
            return

        self.tile_x = new_x
        self.tile_shape = new_tile_shape

    def swap_tile(self):
        new_tile = self.get_next_tile(pop=False)
        new_tile_shape = TILE_SHAPES[new_tile][:]
        temp_x, temp_y = self.tile_x, self.tile_y

        if temp_x + len(self.tile_shape[0]) > GRID_COL_COUNT:
            temp_x = GRID_COL_COUNT - len(self.tile_shape[0])
        if temp_y + len(self.tile_shape) > GRID_ROW_COUNT:
            temp_y = GRID_ROW_COUNT - len(self.tile_shape)

        if TUtils.check_collision(self.board, new_tile_shape, (temp_x, temp_y)):
            return
        self.tile_pool[0] = self.current_tile
        self.current_tile = new_tile
        self.tile_shape = new_tile_shape
        self.tile_x, self.tile_y = temp_x, temp_y

    def get_next_tile(self, pop=False):
        if not self.tile_pool:
            self.generate_tile_pool()
        return self.tile_pool[0] if not pop else self.tile_pool.pop(0)


if __name__ == "__main__":
    tetris = Tetris()
    while True:
        if not tetris.game_over:
            TUtils.print_board(
                TUtils.get_board_with_tile(tetris.board, tetris.tile_shape, (tetris.tile_x, tetris.tile_y)))

        message = input("Next action (0-8): ")
        if message == "q":
            break
        elif message == "r":
            tetris.reset_game()
            continue
        tetris.step(int(message))
