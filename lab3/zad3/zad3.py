import numpy as np
from typing import *
import time


def jacobi_step(psinew: np.array, psi: float, m: int, n: int):
    for i in range(1, m+1, 1):
        for j in range(1, n+1, 1):
            psinew[i*(m+2)+j] = 0.25*(psi[(i-1)*(m+2)+j]+psi[(i+1)*(m+2)+j]+psi[i*(m+2)+j-1]+psi[i*(m+2)+j+1])


def deltasq(newarr: np.array, oldar: np.array, m: int, n: int):
    dsq = 0.0
    tmp = None

    for i in range(1, m+1, 1):
        for j in range(1, m+1, 1):
            tmp = newarr[i*(m+2)+j] - oldar[i*(m+2)+j]
            dsq += tmp**2

    return dsq


def boundary_psi(psi: np.array, m: int, n: int, b: int, h: int, w: int):
    # BCs on bottom edge
    for i in range(b + 1, b + w):
        psi[i * (m + 2) + 0] = np.float32(i - b)

    for i in range(b + w, m + 1):
        psi[i * (m + 2) + 0] = np.float32(w)

    # BCs on RHS
    for j in range(1, h + 1):
        psi[(m + 1) * (m + 2) + j] = np.float32(w)

    for j in range(h + 1, h + w):
        psi[(m + 1) * (m + 2) + j] = np.float32(w - j + h)



if __name__ == '__main__':
    """
    Program simulira dinamiku fluida u 2D prostoru
    """
    print_freq = 1000
    error, bnorm = None, None
    tolerance = 0.0 # <= 0.0 -> ne provjeravaj

    # glavno polje 
    psi: np.array = None
    # privremene verzije glavnog polja
    psitmp: np.array = None

    # argumenti komandne linije
    scalefactor, numiter = None, None

    # velicina simulacije
    bbase, hbase, wbase, mbase, nbase = 10, 15, 5, 32, 32

    irrotational, checkerr = 1, 1

    m, n, b, h, w = None, None, None, None, None
    iter = None
    i, j = None, None

    # stajemo li zbog tolerancije ? 
    if tolerance > 0:
        checkerr = 1

    # ulazne vrijednosti kao u primjeru
    # hardkodirane su zasad
    scalefactor = 64
    numiter = 1000
    
    print("Irrotational flow\n")

    # racunamo b, h & w te m & n
    b = bbase * scalefactor
    h = hbase * scalefactor
    w = wbase * scalefactor
    m = mbase * scalefactor
    n = nbase * scalefactor

    print(f'Running CFD on {m} x {n} grid in serial')

    # alociramo prostor
    psi = np.zeros((m+2)*(n+2), dtype=np.float32)
    psitmp = np.zeros((m+2)*(n+2), dtype=np.float32)

    # granice uvjeta psi
    boundary_psi(psi, m, n, b, h, w)

    # normalizacijski faktor za pogresku
    bnorm = 0.0

    for i in range(0, m+2, 1):
        for j in range(0, n+2, 1):
            bnorm += psi[i*(m+2)+j] * psi[i*(m+2)+j]

    bnorm = np.sqrt(bnorm)

    print("\nStarting main loop..\n\n")
    ttot = 0.0
    for iter in range(1, numiter+1, 1):
        start = time.time()
        jacobi_step(psitmp, psi, m, n)
        
        # racunamo trenutni error ako je potrebno
        if checkerr or iter == numiter:
            error = deltasq(psitmp, psi, m, n)
            error = np.sqrt(error)
            error /= bnorm

        # zavrsimo ranije ako smo zadovoljili zadanu toleranciju
        if checkerr:
            if error < tolerance:
                print(f'Konvergirali u iteraciji {iter}\n')
                break

        # kopiramo natrag
        for i in range(1, m+1, 1):
            for j in range(1, n+1, 1):
                psi[i*(m+2)+j] = psitmp[i*(m+2)+j]

        if iter % print_freq == 0:
            if not checkerr:
                print(f'Completed iteration {iter}\n')
            else:
                print(f'Completed iteration {iter}, error = {error}\n')
        stop = time.time()
        ttot += stop - start
        print(ttot)

    if iter > numiter: iter = numiter

    titer = ttot / float(iter)

    print("\n... finished")
    print(f"After {iter} iterations, the error is {error}")
    print(f"Time for {iter} iterations was {ttot} seconds")
    print(f"Each iteration took {titer} seconds")

    print("... finished") 

