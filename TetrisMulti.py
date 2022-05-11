import pygame
from TetrisAgent import *


ROW_COUNT = 3
COL_COUNT = 10

GAME_COUNT = ROW_COUNT * COL_COUNT

GAME_WIDTH = 100
GAME_HEIGHT = GAME_WIDTH * 2
GAME_GRID_SIZE = GAME_WIDTH / GRID_COL_COUNT

PADDING = 10
PADDING_STATS = 300

SCREEN_WIDTH = GAME_WIDTH * COL_COUNT + PADDING * (COL_COUNT + 1) + PADDING_STATS
SCREEN_HEIGHT = GAME_HEIGHT * ROW_COUNT + PADDING * (ROW_COUNT + 1)

MUTATION_RATE = 0.1

TETRIS_GAMES = []
AGENTS = []
all_time_agent = []
all_time = False

gen_generation = 1
gen_previous_best_score = 0.0
gen_top_score = 0.0

time_elapsed = 0
time_limit = 1000


def update(screen):
    global GAME_COUNT, AGENTS
    global gen_generation, gen_previous_best_score, gen_top_score
    global time_elapsed, time_limit, all_time
    time_elapsed += 1

    if all(tetris.game_over for tetris in TETRIS_GAMES) or (time_limit != -1 and time_elapsed % time_limit == 0):
        time_elapsed = 0
        combos = zip(AGENTS, TETRIS_GAMES)
        parents = sorted(combos, key=lambda combo: combo[1].score, reverse=True)
        gen_generation += 1
        gen_previous_best_score = parents[0][1].score
        if gen_previous_best_score > gen_top_score:
            gen_top_score = gen_previous_best_score
        parents = [a[0] for a in parents]
        parents = parents[:GAME_COUNT // 2]
        AGENTS = [parents[0]]
        while len(AGENTS) < GAME_COUNT:
            parent1, parent2 = random.sample(parents, 2)
            AGENTS.append(parent1.cross_over(parent2))

        for tetris in TETRIS_GAMES:
            all_time = False
            tetris.reset_game()

    for a in range(GAME_COUNT):
        if TETRIS_GAMES[a].game_over:
            continue
        TETRIS_GAMES[a].step(AGENTS[a].get_action(TETRIS_GAMES[a]))

    draw(screen)
    pygame.event.get()


def draw(screen):
    global all_time_agent, all_time
    screen.fill(TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")))
    curr_x, curr_y = PADDING, PADDING
    for x in range(ROW_COUNT):
        for y in range(COL_COUNT):
            draw_board(screen, TETRIS_GAMES[x * COL_COUNT + y], curr_x, curr_y)
            curr_x += GAME_WIDTH + PADDING
        curr_x = PADDING
        curr_y += GAME_HEIGHT + PADDING

    curr_x, curr_y = GAME_WIDTH * COL_COUNT + PADDING * (COL_COUNT + 1), PADDING

    draw_text("Tetris", screen, (curr_x, curr_y), font_size=48)
    curr_y += 60
    best_indexes, best_score = get_high_score()
    draw_text(f"High Score: {best_score:.1f}", screen, (curr_x, curr_y))
    curr_y += 20
    draw_text(f"Best Agent: {SEP.join(map(str, best_indexes))}", screen, (curr_x, curr_y))
    curr_y += 20

    if gen_generation > -1:
        curr_y += 20
        draw_text(f"Generation #{gen_generation}", screen, (curr_x, curr_y), font_size=24)
        curr_y += 35
        draw_text(f"Time Limit: {time_elapsed}/{time_limit}", screen, (curr_x, curr_y))
        curr_y += 20

        survivor = len([a for a in TETRIS_GAMES if not a.game_over])
        draw_text(f"Survivors: {survivor}/{GAME_COUNT} ({survivor / GAME_COUNT * 100:.1f}%)", screen, (curr_x, curr_y))
        curr_y += 20
        draw_text(f"Prev H.Score: {gen_previous_best_score:.1f}", screen, (curr_x, curr_y))
        curr_y += 20
        draw_text(f"All Time H.S: {gen_top_score:.1f}", screen, (curr_x, curr_y))
        curr_y += 40

        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x, grid_y = mouse_x // (GAME_WIDTH + PADDING), mouse_y // (GAME_HEIGHT + PADDING)
        selected = grid_y * COL_COUNT + grid_x

        agent_index = -1
        highlight_selected = False
        if selected < GAME_COUNT and mouse_x < (GAME_WIDTH + PADDING) * COL_COUNT:
            agent_index = selected
            highlight_selected = True
        elif len(best_indexes) > 0:
            agent_index = best_indexes[0]

        if agent_index != -1:
            draw_text(f"Agent #{agent_index}:", screen, (curr_x, curr_y), font_size=24)
            curr_y += 35
            draw_text(f">> Agg Height: {AGENTS[agent_index].weight_height:.3f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Hole Count: {AGENTS[agent_index].weight_holes:.3f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Bumpiness:  {AGENTS[agent_index].weight_bumpiness:.3f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Line Clear: {AGENTS[agent_index].weight_line_clear:.3f}", screen, (curr_x, curr_y))
            curr_y += 20
            if highlight_selected:
                highlight(screen, selected, mode=1)
            else:
                for a in best_indexes:
                    highlight(screen, a, mode=0)
                if all_time and all_time_agent != [AGENTS[agent_index].weight_height, AGENTS[agent_index].weight_holes,
                                      AGENTS[agent_index].weight_bumpiness, AGENTS[agent_index].weight_line_clear]:
                    all_time_agent = [AGENTS[agent_index].weight_height, AGENTS[agent_index].weight_holes,
                                      AGENTS[agent_index].weight_bumpiness, AGENTS[agent_index].weight_line_clear]
                    print(all_time_agent)
            if len(all_time_agent) > 0:
                draw_text(f"All Time Agent :", screen, (curr_x, curr_y), font_size=24)
                curr_y += 35
                draw_text(f">> Agg Height: {all_time_agent[0]:.3f}", screen, (curr_x, curr_y))
                curr_y += 20
                draw_text(f">> Hole Count: {all_time_agent[1]:.3f}", screen, (curr_x, curr_y))
                curr_y += 20
                draw_text(f">> Bumpiness:  {all_time_agent[2]:.3f}", screen, (curr_x, curr_y))
                curr_y += 20
                draw_text(f">> Line Clear: {all_time_agent[3]:.3f}", screen, (curr_x, curr_y))
                curr_y += 20
        pygame.display.update()


def highlight(screen, index: int, mode: int):
    game_x = index % COL_COUNT
    game_y = index // COL_COUNT
    color = TUtils.get_color_tuple(COLORS.get("HIGHLIGHT_GREEN" if mode == 0 else "HIGHLIGHT_RED"))

    if mode == 1:
        temp_x = (GAME_WIDTH + PADDING) * game_x
        temp_y = (GAME_HEIGHT + PADDING) * game_y
        pygame.draw.rect(screen, color, (temp_x, temp_y, GAME_WIDTH + PADDING * 2, PADDING))
        pygame.draw.rect(screen, color, (temp_x, temp_y, PADDING, GAME_HEIGHT + PADDING * 2))
        temp_x = (GAME_WIDTH + PADDING) * (game_x + 1) + PADDING - 1
        temp_y = (GAME_HEIGHT + PADDING) * (game_y + 1) + PADDING - 1
        pygame.draw.rect(screen, color, (temp_x, temp_y, -GAME_WIDTH - PADDING, -PADDING))
        pygame.draw.rect(screen, color, (temp_x, temp_y, -PADDING, -GAME_HEIGHT - PADDING))
    elif mode == 0:
        temp_x = (GAME_WIDTH + PADDING) * game_x + PADDING / 2
        temp_y = (GAME_HEIGHT + PADDING) * game_y + PADDING / 2
        pygame.draw.rect(screen, color, (temp_x, temp_y, GAME_WIDTH + PADDING, PADDING / 2))
        pygame.draw.rect(screen, color, (temp_x, temp_y, PADDING / 2, GAME_HEIGHT + PADDING))
        temp_x = (GAME_WIDTH + PADDING) * (game_x + 1) + PADDING / 2 - 1
        temp_y = (GAME_HEIGHT + PADDING) * (game_y + 1) + PADDING / 2 - 1
        pygame.draw.rect(screen, color, (temp_x, temp_y, -GAME_WIDTH - PADDING + 2, -PADDING / 2))
        pygame.draw.rect(screen, color, (temp_x, temp_y, -PADDING / 2, -GAME_HEIGHT - PADDING + 2))


def get_high_score():
    global all_time
    best_indexes, best_score = [], 0
    for a in range(GAME_COUNT):
        if TETRIS_GAMES[a].game_over:
            continue
        score = TETRIS_GAMES[a].score
        if score > best_score:
            best_indexes = [a]
            best_score = score
            if gen_previous_best_score < best_score:
                all_time = True
        elif score == best_score:
            best_indexes.append(a)
    return best_indexes, best_score


def draw_text(message: str, screen, offsets, font_size=16, color="WHITE"):
    text_image = pygame.font.SysFont(FONT_NAME, font_size).render(
        message, False, TUtils.get_color_tuple(COLORS.get(color))
    )
    screen.blit(text_image, offsets)


def draw_board(screen, tetris: Tetris, x_offset: int, y_offset: int):
    for a in range(GRID_COL_COUNT):
        color = TUtils.get_color_tuple(COLORS.get("BACKGROUND_DARK" if a % 2 == 0 else "BACKGROUND_LIGHT"))
        pygame.draw.rect(screen, color, (x_offset + a * GAME_GRID_SIZE, y_offset, GAME_GRID_SIZE, GAME_HEIGHT))

    draw_tiles(screen, tetris.board, global_offsets=(x_offset, y_offset))
    draw_tiles(screen, tetris.tile_shape, offsets=(tetris.tile_x, tetris.tile_y), global_offsets=(x_offset, y_offset))

    if tetris.game_over:
        color = TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK"))
        ratio = 0.9
        pygame.draw.rect(screen, color,
                         (x_offset, y_offset + (GAME_HEIGHT * ratio) / 2, GAME_WIDTH, GAME_HEIGHT * (1 - ratio)))

        message = "GAME OVER"
        color = TUtils.get_color_tuple(COLORS.get("RED"))
        text_image = pygame.font.SysFont(FONT_NAME, GAME_WIDTH // 6).render(message, False, color)
        rect = text_image.get_rect()
        screen.blit(text_image, (x_offset + (GAME_WIDTH - rect.width) / 2, y_offset + (GAME_HEIGHT - rect.height) / 2))


def draw_tiles(screen, matrix, offsets=(0, 0), global_offsets=(0, 0), outline_only=False):
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val == 0:
                continue
            coord_x = global_offsets[0] + (offsets[0] + x) * GAME_GRID_SIZE
            coord_y = global_offsets[1] + (offsets[1] + y) * GAME_GRID_SIZE
            if not outline_only:
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x, coord_y, GAME_GRID_SIZE, GAME_GRID_SIZE))
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")),
                                 (coord_x, coord_y, GAME_GRID_SIZE, GAME_GRID_SIZE), 1)
                offset = int(GAME_GRID_SIZE / 10)
                pygame.draw.polygon(screen, TUtils.get_color_tuple(COLORS.get("TRIANGLE_GRAY")),
                                    ((coord_x + offset, coord_y + offset),
                                     (coord_x + 3 * offset, coord_y + offset),
                                     (coord_x + offset, coord_y + 3 * offset)))
            else:
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x + 1, coord_y + 1, GAME_GRID_SIZE - 2, GAME_GRID_SIZE - 2), 1)


if __name__ == "__main__":
    print(f"Hello world!")
    print(f">> Initializing {GAME_COUNT} Tetris games in parallel with a grid of {ROW_COUNT}×{COL_COUNT}...")

    pygame.init()
    pygame.font.init()
    display_screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
    print(f">> Screen size calculated to {SCREEN_WIDTH}×{SCREEN_HEIGHT}...")

    print(f">> Initializing {GAME_COUNT} Tetris agent(s)...")
    for _ in range(GAME_COUNT):
        TETRIS_GAMES.append(Tetris())
        AGENTS.append(GeneticAgent())

    print(f">> Initialization complete! Let the show begin!")
    while True:
        update(display_screen)
