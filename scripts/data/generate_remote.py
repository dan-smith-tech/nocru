import time

from data.main import FTPGenerator
from data import generate_dataset

if __name__ == "__main__":
    directory = input("Directory: ")
    size = int(input("Size of data: "))
    begin = int(input("Start index: "))
    threads = int(input("Number of threads: "))
    print("Dataset generating...")
    bt = time.time()
    generate_dataset(FTPGenerator, directory, size, begin, threads)
    et = time.time()
    print("Dataset completed in " + str(round(et - bt, 3)) + " seconds.")
