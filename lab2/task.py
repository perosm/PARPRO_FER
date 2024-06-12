from board import Board
import random

EMPTY = 0
CPU = 1
HUMAN = 2

class Task:
    which_task = None
    score: int = 0
    B: Board = None
    depth: int = -1

    def __init__(self, which_task: tuple, score, B: Board, depth: int) -> None:
        self.which_task = which_task
        self.score = score
        self.B = B
        self.depth = depth

    def evaluate(self, B : Board, last_mover : int, last_col : int, depth : int):
        if self.B.game_end(last_col): # provjera je li igra gotova
            return 1 if last_mover == CPU else -1
        if depth == 0:
            return 0

        new_mover = HUMAN if last_mover == CPU else CPU # tko je sljedeci na potezu
        total = 0
        moves = 0
        all_lose = True
        all_win = True

        for col in range(B.cols):
            if B.move_legal(col):
                moves += 1
                B.move(col, new_mover)
                result = self.evaluate(B, new_mover, col, depth - 1)
                B.undo_move(col)
                if result > -1:
                    all_lose = False
                if result != 1:
                    all_win = False
                if result == 1 and new_mover == CPU:
                    return 1
                if result == -1 and new_mover == HUMAN:
                    return -1
                total += result
        
        if all_win:
            return 1
        if all_lose:
            return -1
        return total / moves

    def execute(self):
        legalMove = True
        whose_turn = CPU
        
        for col in self.which_task: # odraduje taskove koje je master zada
            legalMove = self.B.move_legal(col)
            if legalMove: # ako je potez legalan
                self.B.move(col, whose_turn)
                whose_turn = HUMAN if whose_turn == CPU else CPU

        if legalMove == False:
            return
        self.score = self.evaluate(self.B, CPU, col, self.depth - len(self.which_task))
        

        for col in reversed(self.which_task):
            self.B.undo_move(col)
        

    def __str__(self) -> str:
        return f'{self.which_task}, score={self.score}'