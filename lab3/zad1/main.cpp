#include <iostream>
#include <vector>
#include <chrono>

#define N (1 << 20) //vrijednost potencije

using namespace std;


bool is_prime(int num){
    if (num <= 1) return false;
    for(int i = 2; i < num; i++){
        if(num % i == 0) return false;
    }

    return true;
}

int main(){

    int prime_counter = 0;

    auto start = chrono::high_resolution_clock::now();

    for(int i = 1; i < N; i++){
        prime_counter += is_prime(i) == true ? 1 : 0; 
    }

    auto end = chrono::high_resolution_clock::now();

    chrono::duration<double> duration = end - start;

    cout << "Trajanje (sek): " << duration.count() << endl;
    cout << "Broj prim brojeva: " << prime_counter << endl;

    return 0;
}

