from collections import OrderedDict
import random
import sys
from pygame import Rect
import pygame
import numpy as np


WINDOW_WIDTH, WINDOW_HEIGHT = 500, 601
GRID_WIDTH, GRID_HEIGHT = 300, 600
TILE_SIZE = 30


def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
    for colid, col in enumerate(arr.T):
        if col.max() == 0:
            if _keep_counting:
                _x_offset += 1
            arr, _x_offset = remove_empty_columns(
                np.delete(arr, colid, 1), _x_offset, _keep_counting
            )
            break
        else:
            _keep_counting = False
    return arr, _x_offset


class BottomReached(Exception):
    pass


class TopReached(Exception):
    pass


class Block(pygame.sprite.Sprite):
    @staticmethod
    def collide(block, group):
        for other_block in group:
            if block == other_block:
                continue
            if pygame.sprite.collide_mask(block, other_block) is not None:
                return True
        return False

    def __init__(self):
        super().__init__()
        self.color = random.choice(
            (
                (144, 238, 144),
                (154, 205, 50),
                (102, 205, 170),
                (143, 188, 143),
                (107, 142, 35),
                (60, 179, 113),
            )
        )
        self.current = True
        self.struct = np.array(self.struct)
        if random.randint(0, 1):
            self.struct = np.rot90(self.struct)
        if random.randint(0, 1):
            self.struct = np.flip(self.struct, 0)
        self._draw()

    def _draw(self, x=4, y=0):
        width = len(self.struct[0]) * TILE_SIZE
        height = len(self.struct) * TILE_SIZE
        self.image = pygame.surface.Surface([width, height])
        self.image.set_colorkey((0, 0, 0))
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image,
                        self.color,
                        Rect(
                            x * TILE_SIZE + 1,
                            y * TILE_SIZE + 1,
                            TILE_SIZE - 2,
                            TILE_SIZE - 2,
                        ),
                    )
        self._create_mask()

    def redraw(self):
        self._draw(self.x, self.y)

    def _create_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def initial_draw(self):
        raise NotImplementedError

    @property
    def group(self):
        return self.groups()[0]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value * TILE_SIZE

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value * TILE_SIZE

    def move_left(self, group):
        self.x -= 1
        if self.x < 0 or Block.collide(self, group):
            self.x += 1

    def move_right(self, group):
        self.x += 1
        if self.rect.right > GRID_WIDTH or Block.collide(self, group):
            self.x -= 1

    def move_down(self, group):
        self.y += 1
        if self.rect.bottom > GRID_HEIGHT or Block.collide(self, group):
            self.y -= 1
            self.current = False
            raise BottomReached

    def rotate(self, group):
        self.image = pygame.transform.rotate(self.image, 90)
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._create_mask()
        while self.rect.right > GRID_WIDTH:
            self.x -= 1
        while self.rect.left < 0:
            self.x += 1
        while self.rect.bottom > GRID_HEIGHT:
            self.y -= 1
        while True:
            if not Block.collide(self, group):
                break
            self.y -= 1
        self.struct = np.rot90(self.struct)

    def update(self):
        if self.current:
            self.move_down()


class SquareBlock(Block):
    with open("sqrt.txt") as f1:
        a = ()
        for i in f1.readlines():
            a += tuple(i.split())
    struct = ((int(a[0]), int(a[1])), (int(a[2]), int(a[3])))


class Block1(Block):
    with open("t.txt") as f2:
        a = ()
        for i in f2.readlines():
            a += tuple(i.split())
    struct = ((int(a[0]), int(a[1]), int(a[2])), (int(a[3]), int(a[4]), int(a[5])))


class Block2(Block):
    with open("line.txt") as f3:
        a = ()
        for i in f3.readlines():
            a += tuple(i.split())
    struct = ((int(a[0]),), (int(a[1]),), (int(a[2]),), (int(a[3]),))


class Block3(Block):
    with open("horse.txt") as f4:
        a = ()
        for i in f4.readlines():
            a += tuple(i.split())
    struct = ((int(a[0]), int(a[1])), (int(a[2]), int(a[3])), (int(a[4]), int(a[5])))


class Block4(Block):
    with open("fence.txt") as f5:
        a = ()
        for i in f5.readlines():
            a += tuple(i.split())
    struct = ((int(a[0]), int(a[1])), (int(a[2]), int(a[3])), (int(a[4]), int(a[5])))


class BlocksGroup(pygame.sprite.OrderedUpdates):
    @staticmethod
    def get_random_block():
        return random.choice((SquareBlock, Block1, Block2, Block3, Block4))()

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self._reset_grid()
        self._ignore_next_stop = False
        self.score = 0
        self.next_block = None
        self.stop_moving_current_block()
        self._create_new_block()

    def _check_line_completion(self):
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score += 5
                affected_blocks = list(OrderedDict.fromkeys(self.grid[-1 - i]))

                for block, y_offset in affected_blocks:
                    block.struct = np.delete(block.struct, y_offset, 0)
                    if block.struct.any():
                        block.struct, x_offset = remove_empty_columns(block.struct)
                        block.x += x_offset
                        block.redraw()
                    else:
                        self.remove(block)

                for block in self:
                    if block.current:
                        continue
                    while True:
                        try:
                            block.move_down(self)
                        except BottomReached:
                            break

                self.update_grid()
                self._check_line_completion()
                break

    def _reset_grid(self):
        self.grid = [[0 for _ in range(10)] for _ in range(20)]

    def _create_new_block(self):
        new_block = self.next_block or BlocksGroup.get_random_block()
        if Block.collide(new_block, self):
            raise TopReached
        self.add(new_block)
        self.next_block = BlocksGroup.get_random_block()
        self.update_grid()
        self._check_line_completion()

    def update_grid(self):
        self._reset_grid()
        for block in self:
            for y_offset, row in enumerate(block.struct):
                for x_offset, digit in enumerate(row):
                    if digit == 0:
                        continue
                    rowid = block.y + y_offset
                    colid = block.x + x_offset
                    self.grid[rowid][colid] = (block, y_offset)

    @property
    def current_block(self):
        return self.sprites()[-1]

    def update_current_block(self):
        try:
            self.current_block.move_down(self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()

    def move_current_block(self):
        if self._current_block_movement_heading is None:
            return
        action = {
            pygame.K_DOWN: self.current_block.move_down,
            pygame.K_LEFT: self.current_block.move_left,
            pygame.K_RIGHT: self.current_block.move_right,
        }
        try:
            action[self._current_block_movement_heading](self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()

    def start_moving_current_block(self, key):
        if self._current_block_movement_heading is not None:
            self._ignore_next_stop = True
        self._current_block_movement_heading = key

    def stop_moving_current_block(self):
        if self._ignore_next_stop:
            self._ignore_next_stop = False
        else:
            self._current_block_movement_heading = None

    def rotate_current_block(self):
        if not isinstance(self.current_block, SquareBlock):
            self.current_block.rotate(self)
            self.update_grid()


def draw_grid(background):
    grid_color = 50, 50, 50
    for i in range(11):
        x = TILE_SIZE * i
        pygame.draw.line(background, grid_color, (x, 0), (x, GRID_HEIGHT))
    for i in range(21):
        y = TILE_SIZE * i
        pygame.draw.line(background, grid_color, (0, y), (GRID_WIDTH, y))


def draw_centered_surface(screen, surface, y):
    screen.blit(surface, (400 - surface.get_width() // 2, y))


def main():
    pygame.init()
    pygame.display.set_caption("Tetris with PyGame")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    run = True
    paused = False
    game_over = False
    background = pygame.Surface(screen.get_size())
    bgcolor = (0, 0, 0)
    background.fill(bgcolor)
    draw_grid(background)
    background = background.convert()
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    next_block_text = font.render("NEXT:", True, (255, 255, 255), bgcolor)
    score_msg_text = font.render("SCORE:", True, (255, 255, 255), bgcolor)
    game_over_text = font.render("GAME OVER", True, (255, 220, 0), bgcolor)

    MOVEMENT_KEYS = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
    EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
    EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
    pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 1000)
    pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)

    blocks = BlocksGroup()

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.KEYUP:
                if not paused and not game_over:
                    if event.key in MOVEMENT_KEYS:
                        blocks.stop_moving_current_block()
                    elif event.key == pygame.K_UP:
                        blocks.rotate_current_block()
                if event.key == pygame.K_p:
                    paused = not paused

            if game_over or paused:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in MOVEMENT_KEYS:
                    blocks.start_moving_current_block(event.key)

            try:
                if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                    blocks.update_current_block()
                elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                    blocks.move_current_block()
            except TopReached:
                game_over = True

        screen.blit(background, (0, 0))
        blocks.draw(screen)
        draw_centered_surface(screen, next_block_text, 50)
        draw_centered_surface(screen, blocks.next_block.image, 100)
        draw_centered_surface(screen, score_msg_text, 240)
        score_text = font.render(str(blocks.score), True, (255, 255, 255), bgcolor)
        draw_centered_surface(screen, score_text, 270)
        if game_over:
            draw_centered_surface(screen, game_over_text, 360)
            pygame.time.delay(1000)
            end_screen()
        pygame.display.flip()

    pygame.quit()


def end_screen():
    clock = pygame.time.Clock()
    intro_text = [
        "Ну что, искатель?",
        "Ты оказался слишком слаб",
        "Может попробуешь в другой раз?",
        "Может быть тогда получится?",
        "Хотя...",
        "Ты точно правильно понял правила?",
        "Заполненный слой исчезает, тебе начисляются очки",
        "Фигуры можно двигать и переворачивать",
        "Кнопкой > подвинь текущую фигуру вправо",
        "Кнопкой < подвинь текущую фигуру влево",
        "Кнопокой ^ переверни текущую фигуру",
        "Теперь ты точно готов!",
        "Давай начнем игру!",
    ]

    background_colour = (0, 0, 0)
    pygame.font.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Плохо стараешься")
    screen.fill(background_colour)
    font = pygame.font.Font(None, 50)
    text = font.render("GAME OVER", True, (100, 255, 100))
    text_x = 700 // 2 - text.get_width() // 2
    text_y = 30
    text_w = text.get_width()
    text_h = text.get_height()
    screen.blit(text, (text_x, text_y))
    pygame.draw.rect(
        screen, (0, 255, 0), (text_x - 10, text_y - 10, text_w + 20, text_h + 20), 1
    )
    font = pygame.font.Font(None, 30)
    text_coord = 100
    pygame.display.flip()
    for line in intro_text:
        pygame.time.delay(1000)
        string_rendered = font.render(line, 1, pygame.Color(100, 255, 100))
        intro_rect = string_rendered.get_rect()
        text_coord += 15
        intro_rect.top = text_coord
        intro_rect.x = 30
        text_coord += intro_rect.h
        screen.blit(string_rendered, intro_rect)
        pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                main()
                return
        clock.tick(FPS)


def start_screen():
    clock = pygame.time.Clock()
    intro_text = [
        "Сверху по одной падают различные фигуры",
        "Важно, чтобы фигуры не коснулись верхней части игрового поля",
        "Иначе игра окончится",
        "Хочешь выиграть?",
        "Попробуй набрать побольше очков",
        "Они начисляются за заполненный фигурами слой клеток",
        "Заполненный слой исчезает, тебе начисляются очки",
        "Фигуры можно двигать и переворачивать",
        "Кнопкой > подвинь текущую фигуру вправо",
        "Кнопкой < подвинь текущую фигуру влево",
        "Кнопокой ^ переверни текущую фигуру",
        "Думаешь, это просто?",
        "Тогда давай начнем игру!",
    ]

    background_colour = (0, 0, 0)
    pygame.font.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Обязательно к прочтению")
    screen.fill(background_colour)
    font = pygame.font.Font(None, 50)
    text = font.render("Правила Игры", True, (100, 255, 100))
    text_x = 700 // 2 - text.get_width() // 2
    text_y = 30
    text_w = text.get_width()
    text_h = text.get_height()
    screen.blit(text, (text_x, text_y))
    pygame.draw.rect(
        screen, (0, 255, 0), (text_x - 10, text_y - 10, text_w + 20, text_h + 20), 1
    )
    font = pygame.font.Font(None, 30)
    text_coord = 100
    pygame.display.flip()
    for line in intro_text:
        pygame.time.delay(1000)
        string_rendered = font.render(line, 1, pygame.Color(100, 255, 100))
        intro_rect = string_rendered.get_rect()
        text_coord += 15
        intro_rect.top = text_coord
        intro_rect.x = 30
        text_coord += intro_rect.h
        screen.blit(string_rendered, intro_rect)
        pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        clock.tick(FPS)


def terminate():
    pygame.quit()
    sys.exit()


FPS = 50
start_screen()
pygame.time.delay(1000)
if __name__ == "__main__":
    main()
