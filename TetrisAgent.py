import random
from typing import *
from TetrisArr import Tetris
import TetrisUtils as TUtils
from Settings import *


class BaseAgent:
    def __init__(self):
        self.action_queue = []

    def get_action(self, tetris: Tetris) -> int:
        if len(self.action_queue) == 0:
            self.action_queue = self.calculate_actions(tetris.board, tetris.tile_shape,
                                                       TILE_SHAPES[tetris.get_next_tile()],
                                                       (tetris.tile_x, tetris.tile_y))
        return self.action_queue.pop(0)

    def calculate_actions(self, board, current_tile, next_tile, offsets) -> List[int]:
        return [0]


class GeneticAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.weight_height = random.random()
        self.weight_holes = random.random()
        self.weight_bumpiness = random.random()
        self.weight_line_clear = random.random()

    def get_fitness(self, board):
        score = 0

        future_board, rows_cleared = TUtils.get_board_and_lines_cleared(board)
        score += self.weight_height * sum(TUtils.get_col_heights(future_board))
        score += self.weight_bumpiness * TUtils.get_bumpiness(future_board)
        score += self.weight_holes * TUtils.get_hole_count(future_board)
        score += self.weight_line_clear * rows_cleared
        return score

    def cross_over(self, agent, MUTATION_RATE=0.1):
        child = GeneticAgent()
        child.weight_height = self.weight_height if random.getrandbits(1) else agent.weight_height
        child.weight_holes = self.weight_holes if random.getrandbits(1) else agent.weight_holes
        child.weight_bumpiness = self.weight_bumpiness if random.getrandbits(1) else agent.weight_bumpiness
        child.weight_line_clear = self.weight_line_clear if random.getrandbits(1) else agent.weight_line_clear

        if random.random() < MUTATION_RATE:
            child.weight_height = TUtils.random_weight()
        if random.random() < MUTATION_RATE:
            child.weight_holes = TUtils.random_weight()
        if random.random() < MUTATION_RATE:
            child.weight_bumpiness = TUtils.random_weight()
        if random.random() < MUTATION_RATE:
            child.weight_line_clear = TUtils.random_weight()
        return child

    def calculate_actions(self, board, current_tile, next_tile, offsets) -> List[int]:

        best_fitness = -9999
        best_tile_index = -1
        best_rotation = -1
        best_x = -1

        tiles = [current_tile, next_tile]
        for tile_index in range(len(tiles)):
            tile = tiles[tile_index]
            for rotation_count in range(0, 4):
                for x in range(0, GRID_COL_COUNT - len(tile[0]) + 1):
                    new_board = TUtils.get_future_board_with_tile(board, tile, (x, offsets[1]), True)
                    fitness = self.get_fitness(new_board)
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_tile_index = tile_index
                        best_rotation = rotation_count
                        best_x = x
                tile = TUtils.get_rotated_tile(tile)
        actions = []
        if tiles[best_tile_index] != current_tile:
            actions.append(ACTIONS.index("SWAP"))
        for _ in range(best_rotation):
            actions.append(ACTIONS.index("ROTATE"))
        temp_x = offsets[0]
        while temp_x != best_x:
            direction = 1 if temp_x < best_x else -1
            magnitude = 1 if abs(temp_x - best_x) == 1 else 2
            temp_x += direction * magnitude
            actions.append(ACTIONS.index(("" if magnitude == 1 else "2") + ("R" if direction == 1 else "L")))
        actions.append(ACTIONS.index("INSTA_FALL"))
        return actions
