from typing import *
from task import Task
from itertools import product
from board import Board
from mpi4py import MPI
import copy

class Master:
    num_slaves: int = -1
    cols: int = 7
    depth: int = 7
    task_depth : int = 1
    tasks: List[Task] = []
    B: Board = None

    def __init__(self, num_slaves: int, cols: int, depth: int, task_depth: int, B: Board) -> None:
        self.num_slaves = num_slaves
        self.cols = cols
        self.depth = depth
        self.task_depth = task_depth
        self.B = B

    def generate_tasks(self):
        # https://docs.python.org/3/library/itertools.html#itertools.product
        cartesian_tuple = product(range(self.cols), repeat=self.task_depth) # kartezijev produkt
        for ct in cartesian_tuple:
            self.tasks.append(Task(which_task=ct, score=0, B=self.B, depth=self.depth))
                

    def pick_best_move(self, tasks_dict: dict, curr_depth):
        if curr_depth == 0:
            for key, value in tasks_dict.items():
                print(f'Stupac {key[0]}, vrijednost: {value}')
            max_value = -1
            max_index = 0
            for key, value in tasks_dict.items():
                if tasks_dict[key] > max_value:
                    max_value = tasks_dict[key]
                    max_index = key[0]

            print(f'Najbolji: {max_index}, vrijednost: {max_value}')
            return max_index

        cartesian_tuple = [ct for ct in product(range(self.cols), repeat=curr_depth)]
        new_tasks_dict = {ct: 0 for ct in cartesian_tuple}

        for i in range(self.cols):
            for ct in cartesian_tuple:
                prev_tuple = (i,) + ct
                new_tasks_dict[ct] += tasks_dict[prev_tuple]
        
        for ct in cartesian_tuple:
            #print(f'{ct}={new_tasks_dict[ct]}')
            new_tasks_dict[ct] /= self.cols # svaki zadatak ima 7 podzadataka

        return self.pick_best_move(new_tasks_dict, curr_depth-1)
    

    def convert_tasks_to_dict(self):
        tasks_dict = {}
        for task in self.tasks:
            tasks_dict[task.which_task] = task.score

        return tasks_dict