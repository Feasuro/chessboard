#!/usr/bin/env python

import time


def promising(col: int) -> bool :
    for c in range(col) :
        if queens[col] == queens[c] or abs(queens[col] - queens[c]) == col - c :
            return False
    return True

def place_queens(col: int) :
    global rozw
    if promising(col) :
        if col == dim - 1 :
            rozw += 1
            print(queens)
        else :
            for row in range(1, dim + 1) :
                queens[col + 1] = row
                place_queens(col + 1)

if __name__ == '__main__' :
    dim = int(input("Provide chessboard's dimension: "))
    queens = [0] * dim
    rozw = 0

    start = time.perf_counter()
    place_queens(-1)
    runtime = time.perf_counter() - start

    print("Chessboard's dimension:", dim)
    print('Number of solutions found:', rozw)
    print('Elapsed time:', runtime)