#!/usr/bin/env python

import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from timer import Timer
import solver


class ChessBoard :
    """ Class implements the N Queens problem.

    Values of the 'board' attribute say if the field is:
    'Q' - occupied,
    '+' - threatened,
    '_' - empty.
    Methods (see examples below) allow user to manually look for solutions
    by placing/removing queens on the chessboard
    or print result in human readable format. """

    def __init__(self, dim: int, queens=None) :
        """ Gets chessboard's dimension and populates initial setup if one is given. """
        self._dim = dimension(dim)
        self.board = dict( ((n, k), '_') for n in range(1, self.dim+1) for k in range(1, self.dim+1) )
        if queens is None :
            self.queens = [None] * self.dim
        elif input_check(self.dim, queens) :
            self.queens = queens
            for field in enumerate(self.queens, start=1) :
                if field[1] is None :
                    continue
                self.place_queen(field)

    @property
    def dim(self) -> int:
        """ Chessboard's dimension. """
        return self._dim

    def __bool__(self) -> bool:
        return self.dim != 0

    def __str__(self) -> str:
        """ Use print() to view chessboard on the screen. """
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

    def clear(self) -> bool:
        """ Cleans the chessboard empty """
        for f in self.board :
            self.board[f] = '_'
        self.queens = [None] * self.dim
        return True

    @staticmethod
    def field_check(f, h) -> bool:
        """ Checks if queens on fields f and h are attacking each other. """
        if f[0] == h[0] :
            return True
        elif f[1] == h[1] :
            return True
        elif abs(f[1] - h[1]) == abs(f[0] - h[0]) :
            return True
        else :
            return False

    def get_fields(self, col=None) :
        """ Returns empty fields up to given column, all empty fields by default. """
        if col is None : col = self.dim
        return (f for f in self.board if f[0] <= col and self.board[f] == '_')

    def place_queen(self, field) -> bool:
        """ Place or remove a queen from given field. Marks appropriate fields as threatened. """
        if field in self.board :
            if self.board[field] == '_' :
                self.queens[field[0] - 1] = field[1]
                self.board[field] = 'Q'
                for f in self.board :
                    if self.board[f] == '_' and self.field_check(f, field) :
                        self.board[f] = '+'
                return True
            elif self.board[field] == 'Q' :
                self.queens[field[0] - 1] = None
                self.board[field] = '_'
                for f in self.board :
                    if self.board[f] == '+' and self.field_check(f, field) :
                        self.board[f] = '_'
                        for i in range(self.dim) :
                            if self.queens[i] != None and self.field_check(f, (i+1, self.queens[i])) :
                                self.board[f] = '+'
                                break
                return True
            else :
                print('Cannot place Queen here!')
                return False
        else :
            print('Incorrect field coordinates - out of range.')
            return False

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

        output = print if verbose else alt_print

        solver = multi_solver if multi else mono_solver

        start = time.perf_counter()
        solver(self, output)
        stop = time.perf_counter()
        print('Elapsed time:', stop - start, 'seconds', file=sys.stderr)


def alt_print(chessboard: ChessBoard) :
    """ Alternative, less verbose, printing method. """
    print(chessboard.queens)

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

def dimension(x) :
    """ Turns input into proper dimension or throws an error. """
    if int(x) >= 0 :
        return int(x)
    else :
        raise ValueError("Chessboard's dimension can't be negative!")

def coordinate(x) :
    """ Turns input into proper coordinate or throws an error. """
    if x in ['N', 'n', 'None', None] :
        return None
    elif int(x) == 0 :
        return None
    elif int(x) > 0 :
        return int(x)
    else :
        raise ValueError(f"Invalid coordinate value {x}")

def input_check(dim, queens) -> bool :
    """ Checks if provided queens setup is correct given chessboard's dimension. """
    queens += [None] * (dim - len(queens))
    if len(queens) > dim :
        raise ValueError(f"Too many columns given for dimension={dim}")
    for i in range(len(queens)) :
        if isinstance(queens[i], int) and queens[i] > dim :
            raise ValueError(f"Coordinate {queens[i]} exceeds dimension={dim}")
        elif not solver.valid(queens, i) :
            raise ValueError(f"Initial setup is invalid. Queens cannot attack each other")
    return True

def get_command(x) :
    """ Handles user input. """
    if (y := x.upper()) in ['N', 'C', 'S', 'V', 'M', 'E'] :
        return y
    elif len(y := x.split()) == 2 :
        return (int(y[0]), int(y[1]))
    else :
        raise ValueError("Command not recognized")

def command_new() -> None :
    """ Creates new chessboard with user provided dimension. """
    while True :
        try :
            args.dim = dimension(input("Provide chessboard's dimension: "))
            break
        except ValueError :
            print("Provide a non-negative integer!")
    args.myboard = ChessBoard(args.dim)

def command_solve() -> None :
    """ Prints solutions """
    #output_method = args.myboard if args.verbose else args.myboard.queens
    solver_method = solver.multi_solve if args.multi else solver.basic_solve
    with Timer() as timer :
        solver_method( args.myboard.queens )
    print(f"Elapsed time: {timer.elapsed} seconds")

def show() -> None :
    """ Prints help message and current chessboard. """
    print("\033c", end='')
    print("############################################")
    print(f"# multiprocess={args.multi}, verbose={args.verbose}")
    print("############################################")
    print("N - new chessboard")
    print("C - clear chessboard")
    print("x y - place/remove queen on field (x, y)")
    print("S - print solutions")
    print("m - toggle multiprocessing")
    print("v - toggle verbose output (slower)")
    print("E - exit program")
    print(args.myboard)
    print("Enter command:")

def main() -> None :
    """ The program's main loop. """
    args.myboard = ChessBoard(0)
    show()
    while True :
        try :
            command = get_command(input())
        except ValueError :
            print("Command not recognized")
        else :
            match command :
                case 'E' :
                    break
                case 'V' :
                    args.verbose = not args.verbose
                    show()
                case 'M' :
                    args.multi = not args.multi
                    show()
                case 'C' :
                    args.myboard.clear()
                    show()
                case 'N' :
                    command_new()
                    show()
                case 'S' :
                    command_solve()
                    print("Enter command:")
                case _ :
                    if args.myboard.place_queen(command) :
                        show()
                    else:
                        print("Enter command:")
        

if __name__ == '__main__' :
    from argparse import ArgumentParser
    
    parser = ArgumentParser(
            description='Calculate solutions of the n-queens problem.',
            epilog="""
        Either use interactive mode (without commandline arguments),
        or provide (at least) dimension of chessboard to solve.
        """)
    parser.add_argument('-d', '--dim', type=dimension, help="Chessboard's dimension.")
    parser.add_argument('-q', '--queens', nargs='*', type=coordinate, default=[], help="Initial arrangement of queens on the chessboard: c1 c2 ... cn, where cn is row number in n'th column. For empty column use N or 0.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Produce verbose output.')
    parser.add_argument('-m', '--multi', action='store_true', help='Toggle multiprocessing.')
    args = parser.parse_args()

    if isinstance(args.dim, int) and input_check(args.dim, args.queens) :
        args.myboard = ChessBoard(args.dim, args.queens)
        command_solve()

    else :
        main()