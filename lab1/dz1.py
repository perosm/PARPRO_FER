from mpi4py import MPI
import random
from time import sleep

comm = MPI.COMM_WORLD  # globalna grupa koja uključuje sve uključene procese
rank = comm.Get_rank()  # redni brojevi procesa
n = comm.Get_size()  # broj procesa


class Philosopher:
    """
    Inicijaliziramo svakog filozofa t.d. u svojoj lijevoj ruci ima vilicu
    """
    forks = {
        'L': 'D',
        'R': None
    }

    requests = []

    def __init__(self, rank):
        self.id = rank
        self.neighbors = {
            'R': 'L',  # desni susjed ima moju lijevu vilicu
            'L': 'R'  # lijevi susjed ima moju desnu vilicu
        }


def answer_pending_requests(p):
    to_remove = []
    for r in p.requests:
        if r[1] == 0:  # susjedni filozof daje vilicu
            p.forks[p.neighbors[r[0]]] = 'C'
            to_remove.append(r)
        elif r[1] == 1:  # susjedni filozof zahtijeva vilicu
            if p.forks[p.neighbors[r[0]]] == 'D':  # ako je vilica koju zahtjeva prljava
                to_remove.append(r)
                p.forks[p.neighbors[r[0]]] = None
                comm.send(p.neighbors[r[0]], dest=r[2], tag=0)

    for r in to_remove:
        p.requests.remove(r)


def eat(p):
    if philosopher.forks['L'] is not None and philosopher.forks['R'] is not None:
        print(('\t' * p.id) + f'Filozof {p.id} jede', flush=True)  # ('\t' * p.id) +
        philosopher.forks['L'] = 'D'
        philosopher.forks['R'] = 'D'
    sleep(3)

def send_request(p):
    if p.forks['L'] is None:
        print(('\t' * p.id) + f'Trazim vilicu ({p.id}) od ({(p.id + 1 + n) % n})', flush=True)
        comm.send('L', dest=(p.id + 1 + n) % n, tag=1)
    elif p.forks['R'] is None:
        print(('\t' * p.id) + f'Trazim vilicu ({p.id}) od ({(p.id - 1 + n) % n})', flush=True)
        comm.send('R', dest=(p.id - 1 + n) % n, tag=1)


def think(p):
    print(('\t' * p.id) + f'Filozof {p.id} misli', flush=True)
    for i in range(random.randint(2, 10)):
        sleep(1)
        # i istovremeno odgovaraj na zahtjeve!
        status = MPI.Status()
        dataFlag = comm.iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        if dataFlag is True:
            data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            p.forks[p.neighbors[data]] = None
            comm.send(p.neighbors[data], dest=status.source, tag=0)


def get_both_forks(philosopher):
    while philosopher.forks['L'] is None or philosopher.forks['R'] is None:
        # posalji zahtjev za vilicom;
        send_request(philosopher)
        # ponavljaj dok ne dobijes razenu vilicu
        while True:
            # cekaj poruku (bilo koju!);
            status = MPI.Status()
            dataFlag = comm.iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            if dataFlag is True:
                data = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
                # ako je poruka odgovor na zahtjev azuriraj vilice
                if status.tag == 0:
                    philosopher.forks[philosopher.neighbors[data]] = 'C'
                    break
                elif status.tag == 1:
                    # inace ako je poruka zahtjev -> obradi zahtjev (odobri ili zabiljezi);
                    if philosopher.forks[philosopher.neighbors[data]] == 'D':  # odobri
                        philosopher.forks[philosopher.neighbors[data]] = None
                        comm.send(philosopher.neighbors[data], dest=status.source, tag=0)
                    elif philosopher.forks[philosopher.neighbors[data]] == 'C':  # zabiljezi
                        philosopher.requests.append((data, status.tag, status.source))


if __name__ == '__main__':

    # pokretanje programa s n filozofa
    # mpiexec -n 4 python dz1.py
    philosopher = Philosopher(rank)  # filozof

    if philosopher.id == 0:  # za inicijaliziranje, uzimamo vilicu n-tom filozofu
        philosopher.forks['R'] = 'D'
    if philosopher.id == (n - 1 + n) % n:
        philosopher.forks['L'] = None

    #cnt = 0
    while True:
        # misli(slucajan broj sekundi);
        think(philosopher)
        # dok nemam obje vilice
        get_both_forks(philosopher)
        # jedi
        eat(p=philosopher)
        # odgovori na postojeće zahtjeve
        answer_pending_requests(p=philosopher)
        #cnt += 1
        #if cnt % 10 == 0:
        #    print(f'\n\nFilozof {philosopher.id} jeo {cnt} puta\n\n')
