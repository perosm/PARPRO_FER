import pyopencl as cl
import numpy as np
import time
import os

N = np.int32(2**15)  # vrijednost potencije
L = np.int32(32) # veličina grupe dretvi (broj dretvi po work-grupi)
G = np.int32(256) # globalna velicina skupa dretvi (ukupan broj work-itema)

kernel_code = """
__kernel void is_prime(__global const int* numbers, __global int* result, int G, int N) {
    int gid = get_global_id(0);
    //int lid = get_local_id(0);
    //printf("GID: %d ", gid);
    //printf("%d ", lid);
    //printf("%d ", result[0]);
    volatile __global int* counter = &result[0]; //https://stackoverflow.com/questions/38922985/how-to-atomic-increment-a-global-counter-in-opencl

    for(int i = gid; i < N; i+=G){
        int num = numbers[i];
        int is_prime = 1;
        if(num > 1){
            for(int j = 2; j < num; j++){
                if(num % j == 0){
                    is_prime = 0;
                    break;
                }
            }
            if(is_prime == 1){
                //counter += 1;
                atomic_add(counter, 1); //atomic_inc(counter);
                //printf("%d ", *counter);
            }
        }
    }
}
"""
                         
def specs(device):
    print(f"Device: {device.name}")
    print(f"Vendor: {device.vendor}")
    print(f"Version: {device.version}")
    print(f"Driver Version: {device.driver_version}")
    # Print out maximum work-group size
    max_work_group_size = device.get_info(cl.device_info.MAX_WORK_GROUP_SIZE)
    print(f"Max work-group size: {max_work_group_size}")

    # Print out maximum number of work-items in each dimension
    max_work_item_sizes = device.get_info(cl.device_info.MAX_WORK_ITEM_SIZES)
    print(f"Max work-item sizes: {max_work_item_sizes}")

    # Print out the number of compute units
    compute_units = device.get_info(cl.device_info.MAX_COMPUTE_UNITS)
    print(f"Max compute units: {compute_units}")

    # Print out global memory size
    global_mem_size = device.get_info(cl.device_info.GLOBAL_MEM_SIZE)
    print(f"Global memory size: {global_mem_size / (1024**3):.2f} GB")

    # Print out local memory size
    local_mem_size = device.get_info(cl.device_info.LOCAL_MEM_SIZE)
    print(f"Local memory size: {local_mem_size / 1024:.2f} KB")

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

    # specs(device)

    # stvaranje podataka za zadatak 
    numbers = np.arange(1, N, dtype=np.int32)
    result = np.zeros(1, dtype=np.int32)

    # priprema struktura podataka
    mf = cl.mem_flags
    numbers_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=numbers)
    results_buf = cl.Buffer(context, mf.WRITE_ONLY, result.nbytes)

    start = time.time()
    
    # https://stackoverflow.com/questions/50373192/pyopencl-kernel-parameters
    # queue, global_size, local_size, *args... 
    program.is_prime(queue, (G,), (L,), numbers_buf, results_buf, G, N)# .wait()
        
    # citamo rezultat od devicea
    cl.enqueue_copy(queue, result, results_buf)

    end = time.time()

    duration = end - start

    print(f"Trajanje (sek): {duration}")
    print(f"Broj prim brojeva: {result[0]}")
