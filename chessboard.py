#!/usr/bin/env python

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from collections.abc import MutableSequence
import solver


def convert_args(queens: list | None, dim: int) -> list | None:
    """ Converts queens arrangement provided from commandline, to proper format. """
    if queens is None :
        return None
    result = []
    for i in queens :
        if i == 0 :
            result.append(None)
        elif i > dim :
            raise ValueError(f"Row number {i} out of range, cannot be greater than dim={dim}")
        elif i < 0 :
            raise ValueError(f"Row number cannot be negative, but {i} was given.")
        else :
            result.append(i)
    return result

class Queens(MutableSequence) :
    def __init__(self, iterable) :
        self.data = [int(item) for item in iterable]

    def __setitem__(self, index, item) :
        super().__setitem__(index, int(item))

    def __getitem__(self, index) :
        print(item)

    def __delitem__(self, index) :
        super().__setitem__(index, None)
        
    def __len__(self, index, item) :
        super().__len__()
    
    def insert(self, index, item) :
        pass

    @property
    def dim(self) :
        return len(self)

class ChessBoard :       
    """ Class implements the N Queens problem.

    Values of the 'board' attribute say if the field is:
    'Q' - occupied,
    '+' - threatened,
    '_' - empty.
    Methods (see examples below) allow user to manually look for solutions
    by placing/removing queens on the chessboard
    or print result in human readable format. """

    def __init__(self, N: int, queens=None) :
        """ Pass chessboard's dimension as argument 
        
        example: B=ChessBoard(8)
        creates standard 8x8 chessboard named B"""
        self._dim = int(N) if N > 0 else 0
        self.board = dict( ((n, k), '_') for n in range(1, self.dim+1) for k in range(1, self.dim+1) )
        self.queens = [None] * self.dim
        if queens is not None :
            self.from_list(queens)

    @property
    def dim(self) :
        """ Chessboard's dimension """
        return self._dim

    def __bool__(self) -> bool:
        return self.dim != 0

    def __str__(self) -> str:
        """ Use print() to view chessboard on the screen. 
        
        example: print(B)
        view chessboard B"""
        # Upper line
        result = '    '
        for n in range(self.dim) :
            result += '_ '
        result += '\n'
        # Chessboard
        for k in range(self.dim, 0, -1) :
            result += f'{k:>2} |'
            for n in range(1, self.dim+1) :
                result += self.board[n, k] + '|'
            result += '\n'
        # Column numeration
        result += '    '
        for n in range(1, self.dim+1) :
            result += f'{n:<2}'
        result += '\n'
        return result

    def clean(self) :
        """ Cleans the chessboard empty 
        
        example: B.clean()"""
        for f in self.board :
            self.board[f] = '_'
        self.queens = [None] * self.dim
        return 0

    def get_field(self) :
        """ Looks for an empty field to place a Queen. """
        try :
            return min(f for f in self.board if self.board[f] == '_')
        except ValueError :
            print('No more unthreatened fields on the chessboard!')
            return None

    def get_fields(self, col=None) :
        """ Returns empty fields up to given column, all empty fields by default. """
        if col is None : col = self.dim
        return (f for f in self.board if f[0] <= col and self.board[f] == '_')

    def place_queen(self, field) :
        """ Place or remove a queen from given field. Marks appropriate fields as threatened. 
        
        example: B.place_queen((2,3))
        puts (or deletes) queen in 2'nd column and 3'rd row of the chessboard B"""
        if field in self.board :
            if self.board[field] == '_' :
                self.queens[field[0] - 1] = field[1]
                self.board[field] = 'Q'
                for f in self.board :
                    if self.board[f] == '_' and check(f, field) :
                        self.board[f] = '+'
                return True
            elif self.board[field] == 'Q' :
                self.queens[field[0] - 1] = None
                self.board[field] = '_'
                for f in self.board :
                    if self.board[f] == '+' and check(f, field) :
                        self.board[f] = '_'
                        for i in range(self.dim) :
                            if self.queens[i] != None and check(f, (i+1, self.queens[i])) :
                                self.board[f] = '+'
                                break
                return True
            else :
                print('Cannot place Queen here!')
                return False
        else :
            raise ValueError('Incorrect field coordinates (out of range?)')

    def from_list(self, queens):
        """ Populates board's initial values when queens arrangement is given to the constructor """
        #for field in zip( range(1, self.dim+1), queens, strict=True ) :
        for field in enumerate(queens, start=1) :
            if field[1] is None :
                continue
            if not self.place_queen(field) :
                raise ValueError('Incorrect queens arrangement provided - attacking each other!)')

    def solve(self) :
        """ Yields all possible solutions """
        try :
            col = self.queens.index(None) + 1
        except ValueError :
            yield self.queens
        else :
            for f in self.get_fields(col) :
                self.place_queen(f)
                yield from self.solve()
                self.place_queen(f)

    def solutions(self, multi=False, verbose=False) :
        """ Wrapper method for printing solutions.

        This method picks solver fuction and output format:
        if multi=True uses multiprocessing.
        if verbose=True prints human readable visualisation of solutions
    
        example1: B.solutions()
        Prints all solutions for chessboard B

        example2: B.solutions(verbose=True)
        The same as above but uses human readable output
        
        example3: B.solutions(multi=True)
        Takes advantage of multiprocess concurrent calculations """

        if verbose :
            output = print
        else :
            output = alt_print

        if multi :
            solver = multi_solver
        else :
            solver = mono_solver

        start = time.perf_counter()
        solver(self, output)
        stop = time.perf_counter()
        print('Elapsed time:', stop - start, 'seconds', file=sys.stderr)


def alt_print(chessboard: ChessBoard) :
    """ Alternative, less verbose, printing method. """
    print(chessboard.queens)

def check(f, h) -> bool:
    """ Checks if queens on fields f and h are attacking each other. """
    if f[0] == h[0] :
        return True
    elif f[1] == h[1] :
        return True
    elif abs(f[1] - h[1]) == abs(f[0] - h[0]) :
        return True
    else :
        return False

def mono_solver(chessboard: ChessBoard, output) :
    """ Actual, recurrent solving procedure - monoprocess """
    try :
        col = chessboard.queens.index(None) + 1
    except ValueError :
        output(chessboard)
    else :
        for f in chessboard.get_fields(col) :
            chessboard.place_queen(f)
            mono_solver(chessboard, output)
            chessboard.place_queen(f)

def multi_solver(chessboard: ChessBoard, output) :
    """ Actual, recurrent solving procedure - multiprocess """
    try :
        col = chessboard.queens.index(None) + 1
    except ValueError :
        output(chessboard)
    else :
        with ProcessPoolExecutor() as executor :
            for f in chessboard.get_fields(col) :
                chessboard.place_queen(f)
                executor.submit(mono_solver, deepcopy(chessboard), output)
                chessboard.place_queen(f)

def convert_args(queens: list | None, dim: int) -> list | None:
    """ Converts queens arrangement provided from commandline, to proper format. """
    if queens is None :
        return None
    result = []
    for i in queens :
        if i == 0 :
            result.append(None)
        elif i > dim :
            raise ValueError(f"Row number {i} out of range, cannot be greater than dim={dim}")
        elif i < 0 :
            raise ValueError(f"Row number cannot be negative, but {i} was given.")
        else :
            result.append(i)
    return result

def dimension(x) :
    if int(x) >= 0 :
        return int(x)
    else :
        raise ValueError("Chessboard's dimension can't be negative!")

def coordinate(x) :
    if x in ['N', 'n', 'None', None] :
        return None
    elif int(x) == 0 :
        return None
    elif int(x) > 0 :
        return int(x)
    else :
        raise ValueError(f"Invalid coordinate value {x}")

def input_check(dim, queens) :
    queens += [None] * (dim - len(queens))
    if len(queens) > dim :
        raise ValueError(f"Too many columns given for dimension={dim}")
    for i in range(len(queens)) :
        if isinstance(queens[i], int) and queens[i] > dim :
            raise ValueError(f"Coordinate {queens[i]} exceeds dimension={dim}")
        elif not solver.valid(queens, i) :
            raise ValueError(f"Initial setup is invalid. Queens cannot attack each other")
    return True


if __name__ == '__main__' :
    from argparse import ArgumentParser
    
    parser = ArgumentParser(
            description='Calculate solutions of the n-queens problem.',
            epilog="""
        Either use interactive mode (python -i chessboard.py),
        or provide dimension of chessboard to solve.
        Use help(ChessBoard) for help in interactive mode.
        """)
    parser.add_argument('-d', '--dim', type=dimension, help="Chessboard's dimension.")
    parser.add_argument('-q', '--queens', nargs='*', type=coordinate, default=[], help='Provide initial arrangement of queens on the chessboard: c1 c2 ... cn, where c1 indicates position in first column. When column is empty use 0.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Produce verbose output.')
    parser.add_argument('-m', '--multi', action='store_true', help='Toggle multiprocessing.')
    args = parser.parse_args()

    if isinstance(args.dim, int) and input_check(args.dim, args.queens) :
        print(args)
        start = time.perf_counter()
        solver.place_queens( args.queens, args.queens.index(None) ) #empty list or full list
        runtime = time.perf_counter() - start

    else :
        while True :
            try :
                args.dim = int(input("Provide chessboard's dimension: "))
                if args.dim < 0 :
                    raise ValueError
                break
            except ValueError :
                print("Provide a non-negative integer!")