# game.py
import random


class MinesweeperGame:
    def __init__(self, width, height, num_mines):
        if num_mines >= width * height:
            raise ValueError("Number of mines must be less than the total number of cells.")

        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.board = [[' ' for _ in range(width)] for _ in range(height)]

        self.mines = set()
        self.flags = set()
        self.questioned = set()
        self.revealed = set()

        self.first_move = True
        self.game_over = False
        self.win = False

    def _initialize_board(self, first_x, first_y):
        while len(self.mines) < self.num_mines:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) != (first_x, first_y) and (x, y) not in self.mines:
                self.mines.add((x, y))

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.mines: continue
                count = 0
                for ny in range(y - 1, y + 2):
                    for nx in range(x - 1, x + 2):
                        if (nx, ny) in self.mines:
                            count += 1
                if count > 0:
                    self.board[y][x] = str(count)
        self.first_move = False

    def reveal(self, x, y):
        if self.game_over or (x, y) in self.revealed or (x, y) in self.flags or (x, y) in self.questioned:
            return

        if self.first_move:
            self._initialize_board(x, y)

        self.revealed.add((x, y))

        if (x, y) in self.mines:
            self.game_over = True
            self.win = False
            return

        if self.board[y][x] == ' ':
            for ny in range(y - 1, y + 2):
                for nx in range(x - 1, x + 2):
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        self.reveal(nx, ny)

        if len(self.revealed) == self.width * self.height - self.num_mines:
            self.win = True
            self.game_over = True

    def mark_flag(self, x: int, y: int):
        """Toggles a flag on a tile. Removes a question mark if present."""
        if self.game_over or (x, y) in self.revealed:
            return
        pos = (x, y)
        if pos in self.flags:
            self.flags.remove(pos)
        else:
            if pos in self.questioned:
                self.questioned.remove(pos)
            self.flags.add(pos)

        if not self.first_move and self.flags == self.mines:
            self.win = True
            self.game_over = True

    def mark_question(self, x: int, y: int):
        """Toggles a question mark on a tile. Removes a flag if present."""
        if self.game_over or (x, y) in self.revealed:
            return
        pos = (x, y)
        if pos in self.questioned:
            self.questioned.remove(pos)
        else:
            if pos in self.flags:
                self.flags.remove(pos)
            self.questioned.add(pos)