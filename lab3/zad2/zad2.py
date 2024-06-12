import time
import math

def calculate_pi(h, n):
    sum = 0.0
    for i in range(1, n + 1):
        x = h * (i - 0.5)
        sum += 4.0 / (1.0 + x * x)
    return sum * h

def main():
    PI25DT = 3.141592653589793238462643

    while True:
        n = int(input("Enter the number of intervals: (0 quits) ")) # 100000000
        if n == 0:
            break

        start = time.time()

        h = 1.0 / n
        mypi = calculate_pi(h, n)

        end = time.time()
        duration = end - start

        print(f"Duration (sec): {duration}")
        print(f"pi is approximately {mypi} , Error is {abs(mypi - PI25DT)}")

if __name__ == "__main__":
    main()
