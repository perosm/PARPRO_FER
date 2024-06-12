import sys
import random
import time
from board import Board
from mpi4py import MPI
from master import Master
from task import Task
from typing import *
import copy

EMPTY = 0
CPU = 1
HUMAN = 2
DEPTH = 7 # dubina na koju pretrazujemo
TASK_DEPTH = 1 # 2 # 3 # 7^TASK_DEPTH -> ukupan broj zadataka koji generiramo 
#DEPTH - TASK_DEPTH -> koliko svaki proces pretrazuje odakle mu je zadan zadatak

comm = MPI.COMM_WORLD  # globalna grupa koja uključuje sve uključene procese
rank = comm.Get_rank()  # redni brojevi procesa
status = MPI.Status()
num_of_processes = comm.Get_size()  # broj procesa

B = Board()

TAG_RESULT = 0
TAG_REQUEST = 1
TAG_SEND = 2
TAG_END = 3


def play_move(filename: str, best_col: int, current_move: int):
    
    for col in range(B.cols):
        if B.game_end(col):
            B.draw()
            print("Igra zavrsena! (nasa pobjeda)")
            return True


    B.move(best_col, current_move)
    B.save(filename)

    for col in range(B.cols):
        if B.game_end(col):
            B.draw()
            print("Igra zavrsena! (pobjeda racunala)")
            return True
    
    return False


def send_tasks_and_work(master: Master):
    to_complete_tasks: List[Task] = copy.copy(master.tasks)
    completed_tasks: List[Task] = []
    
    
    while 0 < len(to_complete_tasks) or len(completed_tasks) < len(master.tasks):
        status = MPI.Status()
        flag = comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        if flag: # ako je neko slao zahtjev za zadatkom
            task = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            source = status.Get_source()
            tag = status.Get_tag()
            if tag == TAG_REQUEST and len(to_complete_tasks) != 0: # radnik trazi zahtjev
                comm.send(to_complete_tasks.pop(0), dest=source, tag=TAG_SEND)
            if tag == TAG_RESULT: # radnik
                completed_tasks.append(task)
        else: # ako nema zahtjeva -> master radi
            if len(to_complete_tasks) != 0:
                task = to_complete_tasks.pop(0)
                task.execute()
                completed_tasks.append(task)

    completed_tasks = sorted(completed_tasks, key=lambda task: task.which_task)

    return completed_tasks


def worker_process():
    while True:
        status = MPI.Status()
        comm.send(None, dest=0, tag=TAG_REQUEST)
        task = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        if status.tag == TAG_END: # gotovi smo s igrom
            break
        elif status.tag == TAG_SEND: # process master salje zadatak workeru
            task.execute()
            comm.send(task, dest=0, tag=TAG_RESULT)
    
    return


def master_process():
    filename = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else DEPTH
    B.load(filename)
    master = Master(num_slaves=num_of_processes - 1, depth=depth, cols=7, task_depth=TASK_DEPTH, B=copy.copy(B))

    while True:
        master.generate_tasks() # generira zadatke
        start_time = time.time()
        master.tasks = send_tasks_and_work(master) # salje ih radnicima i sam radi
        tasks_dict = master.convert_tasks_to_dict()
        best_col = master.pick_best_move(tasks_dict, TASK_DEPTH - 1)
        master.tasks = []
        flag = play_move(filename, best_col, CPU)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f'Vrijeme potrebno: {elapsed_time}')
        if flag:
            for pid in range(1, num_of_processes):
                comm.send(None, dest=pid, tag=TAG_END)
            break

        if B.last_mover == CPU: # ako je CPU zadnji igra, sad korisnik igra
            B.draw()
            col = int(input("Upisite stupac (0...6):"))
            while B.move_legal(col) is False:
                col = int(input("Upisite ispravan broj (0...6)"))

            play_move(filename, col, HUMAN)
        
    return



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uporaba: <program> <fajl s trenutnim stanjem> [<dubina>]")

    else:
        if rank == 0:
            master_process()
            B.load('prazna_ploca.txt')
            B.save('ploca.txt')
        else:
            worker_process()
            
    MPI.Finalize()

        