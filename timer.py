#!/usr/bin/env python
"""Simple timer as context manager module""" 

from time import perf_counter

class Timer:
    """Class implements context manager timer"""
    def __init__(self):
        self.start = 0
        self.stop = 0
        self.elapsed = 0

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, error, message, traceback):
        self.stop = perf_counter()
        self.elapsed = self.stop - self.start
        return False

if __name__ == '__main__' :
    with Timer() as timer :
        input("Wait some time and hit enter")

    print(f"You waited: {timer.elapsed} seconds.")
