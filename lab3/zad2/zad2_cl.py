import time
import math
import numpy as np
import pyopencl as cl

#L = np.int32(256) # veličina grupe dretvi (broj dretvi po work-grupi)
#G = np.int32(256*256) # globalna velicina skupa dretvi (ukupan broj work-itema)

kernel_code = """
__kernel void calculate_pi(__global double* results, int M, int N){
    int gid = get_global_id(0);
    double partial_sum = 0.0;   
    double h = 1.0 / (double) N;
    //printf("%d ", gid);

    for(int i = gid * M + 1; i <= gid * M + M + 1; i++){
        double x = h * ((double)i - 0.5);
        partial_sum += 4.0 / (1.0 + x * x);
    }

    results[gid] = partial_sum;

}
"""

if __name__ == "__main__":
    # Inicijalizacija OpenCL
    # otkrivanje platformi i dohvacanje prve platforme 
    platform = cl.get_platforms()[0]
    # detekiranje uredaja na platformi i dohvacanje prvog GPU-a
    device = platform.get_devices()[0]

    # stvaranje konteksta
    context = cl.Context([device])
    # stvaranje reda izvodenja
    queue = cl.CommandQueue(context)

    # stvaranje objekta programa i ucitaanje kernela u program te stvaranje izvrsnog programa
    program = cl.Program(context, kernel_code).build()


    PI25DT = 3.141592653589793238462643

    while True:
        N = np.int32(input("Enter the number of intervals: (0 quits) ")) # 10000000
        M = np.int32(input("Enter the number of tasks per thread: ")) # 1000
        if N == 0:
            break
        
        G = N // M

        results = np.zeros(G, dtype=np.float64)
        mf = cl.mem_flags
        results_buf = cl.Buffer(context, mf.READ_WRITE, results.nbytes)
        
        start = time.time()

        # h = 1.0 / n
        # mypi = calculate_pi(h, n)
        # https://stackoverflow.com/questions/50373192/pyopencl-kernel-parameters
        # queue, global_size, local_size, *args... 
        program.calculate_pi(queue, (G,), None, results_buf, M, np.int32(N))
        
        # citamo rezultate od devicea
        cl.enqueue_copy(queue, results, results_buf)
        #print(results)

        mypi = np.sum(results) / N
        end = time.time()
        duration = end - start

        print(f"Duration (sec): {duration}")
        print(f"pi is approximately {mypi} , Error is {abs(mypi - PI25DT)}")
