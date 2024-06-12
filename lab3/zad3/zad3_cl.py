import numpy as np
from typing import *
import time
import pyopencl as cl

kernel_code = """
/**
  *  def jacobi_step(psinew: np.array, psi: float, m: int, n: int):
  *  for i in range(1, m+1, 1):
  *      for j in range(1, n+1, 1):
  *          psinew[i*(m+2)+j] = 0.25*(psi[(i-1)*(m+2)+j]+psi[(i+1)*(m+2)+j]+psi[i*(m+2)+j-1]+psi[i*(m+2)+j+1])
  **/
    
    __kernel void jacobi_step(__global double* psinew, __global const double* psi, int m, int n){
        int i = get_global_id(0) + 1; //x
        int j = get_global_id(1) + 1; //y

        if(i < m + 1 && j < n + 1){
            psinew[i*(m+2)+j] = 0.25*(psi[(i-1)*(m+2)+j]+psi[(i+1)*(m+2)+j]+psi[i*(m+2)+j-1]+psi[i*(m+2)+j+1]);
        }
    }

/**
  * for i in range(1, m+1, 1):
  *     for j in range(1, n+1, 1):
  *         psi[i*(m+2)+j] = psitmp[i*(m+2)+j]
  **/

    __kernel void copy_back(__global double* psi, __global const double* psitmp, int m, int n){
        int i = get_global_id(0) + 1; // x
        int j = get_global_id(1) + 1; // y

        psi[i*(m+2)+j] = psitmp[i*(m+2)+j];
}
"""

def deltasq(newarr: np.array, oldar: np.array, m: int, n: int):
    delta = newarr[1:m+1, 1:n+1] - oldar[1:m+1, 1:n+1]
    deltasq = delta**2
    return np.sum(deltasq)


def boundary_psi(psi: np.array, m: int, n: int, b: int, h: int, w: int):
    # BCs on bottom edge
    for i in range(b + 1, b + w):
        psi[i, 0] = i - b

    for i in range(b + w, m + 1):
        psi[i, 0] = w

    # BCs on RHS
    for j in range(1, h + 1):
        psi[m+1, j] = w

    for j in range(h + 1, h + w):
        psi[m+1, j] = w - j + h
    
    return psi



if __name__ == '__main__':
    """
    Program simulira dinamiku fluida u 2D prostoru
    """
    print_freq = 1000
    error, bnorm = None, None
    tolerance = 0.0 # <= 0.0 -> ne provjeravaj

    # argumenti komandne linije ---> hardkodirano zbog provjere
    scalefactor, numiter = 64, 1000

    # velicina simulacije
    bbase, hbase, wbase, mbase, nbase = 10, 15, 5, 32, 32

    irrotational, checkerr = 1, 0

    # stajemo li zbog tolerancije ? 
    if tolerance > 0:
        checkerr = 1
    
    print("Irrotational flow\n")

    # racunamo b, h & w te m & n
    b = bbase * scalefactor
    h = hbase * scalefactor
    w = wbase * scalefactor
    # mbase i nbase su istih dimenzija
    m = mbase * scalefactor  
    n = nbase * scalefactor 

    print(f'Running CFD on {m} x {n} grid in serial')

    # alociramo prostor
    # glavno polje 
    psi = np.zeros((m+2, n+2), dtype=np.float64)
    # privremene verzije glavnog polja
    psitmp = np.zeros((m+2, n+2), dtype=np.float64)

    # granice uvjeta psi
    psi = boundary_psi(psi, m, n, b, h, w)
    # normalizacijski faktor za pogresku
    bnorm = 0.0
    bnorm = np.sqrt(np.sum(psi**2))
    

    # Inicijalizacija OpenCL
    # otkrivanje platformi i dohvacanje prve platforme 
    platform = cl.get_platforms()[0] # mozda promijenit na 1??
    # detekiranje uredaja na platformi i dohvacanje prvog GPU-a
    device = platform.get_devices()[0]

    # stvaranje konteksta
    context = cl.Context([device])
    # stvaranje reda izvodenja
    queue = cl.CommandQueue(context)

    # stvaranje objekta programa i ucitaanje kernela u program te stvaranje izvrsnog programa
    program = cl.Program(context, kernel_code).build()
    
    mf = cl.mem_flags
    psi_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=psi)
    psitmp_buf = cl.Buffer(context, mf.WRITE_ONLY, psitmp.nbytes)
    
    print("\nStarting main loop..\n\n")
    start = time.time()
    for iter in range(1, numiter+1, 1):
        # queue, local_size, args*...
        program.jacobi_step(queue, (m, n), (16, 16), psitmp_buf, psi_buf, np.int32(m), np.int32(n))

        # racunamo trenutni error ako je potrebno ili kad smo dosli do zavrsetka iteracija
        if checkerr or iter == numiter:
            #tmp_end = time.time()
            #print(tmp_end - start)
            cl.enqueue_copy(queue, psi, psi_buf)
            cl.enqueue_copy(queue, psitmp, psitmp_buf)
            error = deltasq(psitmp, psi, m, n)
            error = np.sqrt(error)
            error /= bnorm

        # zavrsimo ranije ako smo zadovoljili zadanu toleranciju
        if checkerr:
            if error < tolerance:
                print(f'Converged on iteration {iter}\n')
                break

        # kopiramo natrag
        program.copy_back(queue, (m, n), (16, 16), psi_buf, psitmp_buf, np.int32(m), np.int32(n))

        if iter % print_freq == 0:
            if not checkerr:
                print(f'Completed iteration {iter}\n')
            else:
                print(f'Completed iteration {iter}, error = {error}\n')
        
    stop = time.time()
    ttot = stop - start

    if iter > numiter: iter = numiter

    ttot = stop - start
    titer = ttot / float(iter)

    print(f"After {iter} iterations, the error is {error:.8f}")
    print(f"Time for {iter} iterations was {ttot} seconds")
    print(f"Each iteration took {titer} seconds")

    print("... finished") 
