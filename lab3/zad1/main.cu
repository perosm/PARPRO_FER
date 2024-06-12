#include <iostream>
#include <vector>
#include <chrono>

#define N (1 << 20) // vrijednost potencije
#define L 256 // veličina grupe dretvi -----> threads per block


//#if !defined(__CUDA_ARCH__) || __CUDA_ARCH__ >= 600
//#else
//__device__ double atomicAdd(double* address, double val) {
//    unsigned long long int* address_as_ull = (unsigned long long int*)address;
//    unsigned long long int old = *address_as_ull, assumed;
//
//    do {
//        assumed = old;
//        old = atomicCAS(address_as_ull, assumed,
//            __double_as_longlong(val + __longlong_as_double(assumed)));
//    } while (assumed != old);
//
//    return __longlong_as_double(old);
//}
//#endif



using namespace std;

__global__ void count_primes(int *device_array, int* device_prime_count, int n) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    int stride = gridDim.x * blockDim.x;
    
    for (int i = idx; i < n; i += stride) {
        bool is_prime = true;
        int num = device_array[i];
        if (num > 1){
            for (int j = 2; j < num; j++){
                if (num % j == 0) {
                    is_prime = false;
                    break;
                }
            }
            if(is_prime){
            	*device_prime_count += 1;
                //atomicAdd(device_prime_count, 1);
            }
        }
    }
}

int main() { // nvcc main.cu -o main_cu
    int *host_array = (int*) malloc(N * sizeof(int)); // brojevi

    for (int i = 0; i < N; i++) {
        host_array[i] = i + 1;
    }
    chrono::duration<double> min_duration = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::seconds::max() - std::chrono::seconds::min());
    
    int threadsPerBlock_min = -1;
    int blocksPerGrid_min = -1;
	int *device_array;
	cudaMalloc(&device_array, N * sizeof(int));
	cudaMemcpy(device_array, host_array, N * sizeof(int), cudaMemcpyHostToDevice);
	int *device_prime_counter;
	for(int l = 1; l <= L; l*=2){
		int host_prime_count = 0;

		// zauzimanje memorije na device-u
		cudaMalloc(&device_prime_counter, sizeof(int));
		// kopiranje vektora iz host memorije u device memoriju
		cudaMemcpy(device_prime_counter, &host_prime_count, sizeof(int), cudaMemcpyHostToDevice);

		// pozivanje kernela
		int threadsPerBlock = l;
		int blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
		auto start = chrono::high_resolution_clock::now();
		
		count_primes<<<blocksPerGrid, threadsPerBlock>>>(device_array, device_prime_counter, N);
		
		// sinkronizacija
		//cudaDeviceSynchronize();

		auto end = chrono::high_resolution_clock::now();
		chrono::duration<double> duration = end - start;

		if(duration < min_duration || min_duration.count() == -1){
			min_duration = duration;
			blocksPerGrid_min = blocksPerGrid;
			threadsPerBlock_min = threadsPerBlock;
		}
		// kopiranje rezultata iz device u host memoriju
		cudaMemcpy(&host_prime_count, device_prime_counter, sizeof(int), cudaMemcpyDeviceToHost);
		
		cout << "Broj blokova: " << blocksPerGrid << " , broj dretvi po bloku: " << threadsPerBlock << endl;
		cout << "Trajanje (sek): " << duration.count() << endl;
		cout << "Broj prim brojeva: " << host_prime_count << endl;

		cudaFree(device_array);
		cudaFree(device_prime_counter);
	}
	free(host_array);
	
	cout << endl;
	cout << "Broj blokova: " << blocksPerGrid_min << " , broj dretvi po bloku: " << threadsPerBlock_min << endl;
	cout << "Trajanje (sek): " << min_duration.count() << endl;

    return 0;
}
