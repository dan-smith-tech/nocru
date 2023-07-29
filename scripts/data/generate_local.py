import time

from data.main import LocalGenerator
from data import generate_dataset

if __name__ == "__main__":
    size = int(input("Size of data: "))
    begin = int(input("Start index: "))
    threads = int(input("Number of threads: "))
    print("Dataset generating...")
    bt = time.time()
    generate_dataset(LocalGenerator, "../../data/dataset/", size, begin, threads)
    et = time.time()
    print("Dataset completed in " + str(round(et - bt, 3)) + " seconds.")
