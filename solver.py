#!/usr/bin/env python

from concurrent.futures import ProcessPoolExecutor
import sys

def valid(queens: list, col: int) -> bool :
    for c in range(len(queens)) :
        if queens[c] and queens[col] and c != col :
            if queens[col] == queens[c] or abs(queens[col] - queens[c]) == abs(col - c) :
                return False
    return True

def basic_solve(queens: list, col=0) -> None :
    if valid(queens, col) :
        try :
            col = queens.index(None)
        except ValueError :
            print(queens)
        else :
            for row in range(1, len(queens) + 1) :
                queens[col] = row
                basic_solve(queens, col)
            queens[col] = None

def multi_solve(queens: list, col=0) -> None :
    try :
        col = queens.index(None)
    except ValueError :
        print(queens)
    else :
        with ProcessPoolExecutor() as executor :
            for row in range(1, len(queens) + 1) :
                queens[col] = row
                executor.submit(basic_solve, list(queens), col)
            queens[col] = None


if __name__ == '__main__' :
    dim = int(input("Provide chessboard's dimension: "))
    queens = [None] * dim

    multi_solve( queens )