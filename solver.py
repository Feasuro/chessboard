#!/usr/bin/env python
"""This module holds N-queens problem solving algorithm"""

import sys
from concurrent.futures import ProcessPoolExecutor
from argparse import ArgumentParser

from codetiming import Timer

def valid(queens: list, col: int) -> bool :
    """ Checks if in column 'col' queen is placed properly. """
    if queens[col] :
        for c, q in enumerate(queens):
            if q and c != col :
                if queens[col] == q or abs(queens[col] - q) == abs(col - c) :
                    return False
    return True

def basic_solve(queens: list, col=0) -> None :
    """ Recurrently tries to fill list with queens. """
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
    """ Wrapper that distributes calculations between processes. """
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

def dimension(x) -> int :
    """ Turns input into proper dimension or throws an error. """
    if (n := int(x)) >= 0 :
        return n
    raise ValueError("Chessboard's dimension must be a non-negative integer!")

def coordinate(x: str) -> int | None:
    """ Turns input into proper coordinate or throws an error. """
    if x in ['N', 'n', 'None', None] :
        return None
    if (n := int(x)) == 0 :
        return None
    if n > 0 :
        return n
    raise ValueError(f"Invalid coordinate value {x}")

def input_check(dim, queens) -> bool :
    """ Checks if provided queens setup is correct given chessboard's dimension. """
    if len(queens) > dim :
        raise ValueError(f"Too many columns given for dimension={dim}")
    queens += [None] * (dim - len(queens))
    for i, q in enumerate(queens) :
        if isinstance(q, int) and q > dim :
            raise ValueError(f"Coordinate {q} exceeds dimension={dim}")
        if not valid(queens, i) :
            raise ValueError("Initial setup is invalid. Queens cannot attack each other")
    return True

if __name__ == '__main__' :
    parser = ArgumentParser(
            description="Calculate solutions of the n-queens problem.",
            epilog="""
        Example: [1, None, None, None] represents 4x4 chessboard with one queen in bottom left corner.
        To solve call solver.py -d 4 -q 1
        """)
    parser.add_argument('-d', '--dim', required=True, type=dimension, help="Chessboard's dimension")
    parser.add_argument('-q', '--queens', nargs='*', type=coordinate, default=[],
                        help="""Initial arrangement of queens on the chessboard: c1 c2 ... cn,
                        where cn is row number in n'th column. For empty column use N or 0.""")
    parser.add_argument('-m', '--multi', action='store_true', help='Toggle multiprocessing.')
    args = parser.parse_args()

    if input_check(args.dim, args.queens) :
        solve = multi_solve if args.multi else basic_solve
        with Timer(logger=lambda x: print(x, file=sys.stderr)):
            solve( args.queens )
