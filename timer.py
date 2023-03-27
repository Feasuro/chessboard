#!/usr/bin/env python

from time import perf_counter

class Timer:
    def __init__(self):
        self.elapsed = 0

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop = perf_counter()
        self.elapsed = self.stop - self.start
        return False

if __name__ == '__main__' :
    with Timer() as timer :
        input("Wait some time and hit enter")

    print(f"You waited: {timer.elapsed} seconds.")