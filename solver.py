#!/usr/bin/env python

from concurrent.futures import ProcessPoolExecutor
import sys
import time

def valid(queens: list, col: int) -> bool :
    for c in range(len(queens)) :
        if queens[c] and queens[col] and c != col :
            if queens[col] == queens[c] or abs(queens[col] - queens[c]) == abs(col - c) :
                return False
    return True

def place_queens(queens: list, col: int) :
    if valid(queens, col) :
        try :
            col = queens.index(None)
        except ValueError :
            print(queens)
        else :
            for row in range(1, len(queens) + 1) :
                queens[col] = row
                place_queens(queens, col)
            queens[col] = None

"""i = 1
queens = []

for i in range(1, len(sys.argv)) :
    queens.append(int(sys.argv[i]))

try :
    place_queens( queens.index(None) )
except ValueError :
    print(queens)"""

if __name__ == '__main__' :
    dim = int(input("Provide chessboard's dimension: "))
    queens = [None] * dim

    start = time.perf_counter()
    place_queens( queens, queens.index(None) )
    runtime = time.perf_counter() - start

    print("Chessboard's dimension:", dim)
    print('Elapsed time:', runtime)