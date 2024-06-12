import numpy as np
from mpi4py import MPI

EMPTY = 0
CPU = 1
HUMAN = 2

class Board:
    def __init__(self, rows=6, cols=7):
        self.rows = rows
        self.cols = cols
        self.last_mover = EMPTY
        self.last_col = -1
        self.field = np.full((self.rows, self.cols), EMPTY)
        self.height = np.zeros(self.cols, dtype=int)

    def __getitem__(self, row):
        assert 0 <= row < self.rows
        return self.field[row]

    def move_legal(self, col: int):
        assert 0 <= col < self.cols
        return self.field[self.rows - 1, col] == EMPTY

    def move(self, col, player: int):
        if not self.move_legal(col):
            return False
        self.field[self.height[col], col] = player
        self.height[col] += 1
        self.last_mover = player
        self.last_col = col
        return True

    def undo_move(self, col: int):
        assert 0 <= col < self.cols
        if self.height[col] == 0:
            return False
        self.height[col] -= 1
        self.field[self.height[col], col] = EMPTY
        return True

    def game_end(self, last_col: int):
        assert 0 <= last_col < self.cols
        col = last_col
        row = self.height[last_col] - 1
        if row < 0:
            return False
        player = self.field[row, col]

        # Check vertical
        seq = 1
        r = row - 1
        while r >= 0 and self.field[r, col] == player:
            seq += 1
            r -= 1
        if seq >= 4:
            return True

        # Check horizontal
        seq = 0
        c = col
        while c > 0 and self.field[row, c - 1] == player:
            c -= 1
        while c < self.cols and self.field[row, c] == player:
            seq += 1
            c += 1
        if seq >= 4:
            return True

        # Check diagonal (bottom left to top right)
        seq = 0
        r, c = row, col
        while c > 0 and r > 0 and self.field[r - 1, c - 1] == player:
            c -= 1
            r -= 1
        while c < self.cols and r < self.rows and self.field[r, c] == player:
            seq += 1
            c += 1
            r += 1
        if seq >= 4:
            return True

        # Check diagonal (top left to bottom right)
        seq = 0
        r, c = row, col
        while c > 0 and r < self.rows - 1 and self.field[r + 1, c - 1] == player:
            c -= 1
            r += 1
        while c < self.cols and r >= 0 and self.field[r, c] == player:
            seq += 1
            c += 1
            r -= 1
        if seq >= 4:
            return True

        return False

    def load(self, fname):
        with open(fname, 'r') as f:
            self.rows, self.cols = map(int, f.readline().split())
            self.field = np.zeros((self.rows, self.cols), dtype=int)
            for r in range(self.rows - 1, -1, -1):
                self.field[r] = list(map(int, f.readline().split()))
            self.height = np.array([np.max(np.where(self.field[:, col] != EMPTY)[0]) + 1 if np.any(self.field[:, col] != EMPTY) else 0 for col in range(self.cols)])

    def save(self, fname):
        with open(fname, 'w') as f:
            f.write(f"{self.rows} {self.cols}\n")
            for r in range(self.rows - 1, -1, -1):
                f.write(" ".join(map(str, self.field[r])) + "\n")

# DODANO:

    def draw(self):
        for row in range(self.rows - 1, -1, -1):
            print(" ".join(map(str, self.field[row])))
