import time

N = 1 << 15

def is_prime(num):
    if num <= 1:
        return False
    for i in range(2, num):
        if num % i == 0:
            return False
    return True

def main():
    prime_counter = 0

    start = time.time()

    for i in range(1, N):
        prime_counter += 1 if is_prime(i) else 0

    end = time.time()

    duration = end - start

    print(f"Trajanje (sek): {duration}")
    print(f"Broj prim brojeva: {prime_counter}")

if __name__ == "__main__":
    main()
