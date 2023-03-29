#!/usr/bin/env python

import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from timer import Timer

####################################
# Section: chessboard implementation
class Terminal :
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    DARKGREEN = '\033[32m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    CLEAR = '\033c'
class ChessBoard :
    """ Class implements the N Queens problem.

    Values of the 'board' attribute say if the field is:
    'Q' - occupied,
    '+' - threatened,
    '_' - empty.
    Methods allow user to manually look for solutions
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
    def dim(self) -> int :
        """ Chessboard's dimension. """
        return self._dim

    def __bool__(self) -> bool :
        return self.dim != 0

    def __str__(self) -> str :
        """ Use print() to view chessboard on the screen. """
        # Upper line
        result = Terminal.WHITE + '    '
        for n in range(self.dim) :
            result += '_ '
        result += '\n'
        # Chessboard
        for k in range(self.dim, 0, -1) :
            result += f'{k:>2} |'
            for n in range(1, self.dim+1) :
                if self.board[n, k] == 'Q' :
                    result += Terminal.GREEN
                elif self.board[n, k] == '+' :
                    result += Terminal.RED
                result += self.board[n, k] + Terminal.WHITE + '|'
            result += '\n'
        # Column numeration
        result += '    '
        for n in range(1, self.dim+1) :
            result += f'{n:<2}'
        result += '\n' + Terminal.ENDC
        return result

    def clear(self) -> bool :
        """ Cleans the chessboard empty. """
        for f in self.board :
            self.board[f] = '_'
        self.queens = [None] * self.dim
        return True

    @staticmethod
    def field_check(f, h) -> bool :
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

    def place_queen(self, field) -> bool :
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
                print(f'{Terminal.RED}Cannot place Queen here!{Terminal.ENDC}')
                return False
        else :
            print(f'{Terminal.RED}Incorrect field coordinates - out of range.{Terminal.ENDC}')
            return False

    def solve(self) :
        """ Yields all possible solutions. """
        try :
            col = self.queens.index(None) + 1
        except ValueError :
            yield self
        else :
            for f in self.get_fields(col) :
                self.place_queen(f)
                yield from self.solve()
                self.place_queen(f)

#############################
# Section: solving algorithms
def valid(queens: list, col: int) -> bool :
    """ Checks if in column 'col' queen is placed properly. """
    for c in range(len(queens)) :
        if queens[c] and queens[col] and c != col :
            if queens[col] == queens[c] or abs(queens[col] - queens[c]) == abs(col - c) :
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

def verbose_solve(chessboard: ChessBoard) -> None :
    """ Verbose recurrent solver, it operates on the whole board structure. """
    try :
        col = chessboard.queens.index(None) + 1
    except ValueError :
        print(chessboard)
    else :
        for f in chessboard.get_fields(col) :
            chessboard.place_queen(f)
            verbose_solve(chessboard)
            chessboard.place_queen(f)

def multiverbose_solve(chessboard: ChessBoard) -> None :
    """ Multiprocess wraper for verbose algorithm. """
    try :
        col = chessboard.queens.index(None) + 1
    except ValueError :
        print(chessboard)
    else :
        with ProcessPoolExecutor() as executor :
            for f in chessboard.get_fields(col) :
                chessboard.place_queen(f)
                executor.submit(verbose_solve, deepcopy(chessboard))
                chessboard.place_queen(f)

############################
# Section: user input checks
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
        elif not valid(queens, i) :
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

##########################################
# Section: interactive mode implementation
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
    """ Picks an algorithm and prints time. """
    if args.verbose :
        solver_method = multiverbose_solve if args.multi else verbose_solve
        output_method = args.myboard
    else :
        solver_method = multi_solve if args.multi else basic_solve
        output_method = args.myboard.queens

    with Timer() as timer :
        solver_method( output_method )
    print(f"Elapsed time: {timer.elapsed} seconds", file=sys.stderr)

def show() -> None :
    """ Prints help message and current chessboard. """
    print(Terminal.CLEAR, end='')
    print(f"{Terminal.DARKGREEN}############################################")
    print(f"#{Terminal.ENDC} multiprocess={args.multi}, verbose={args.verbose}")
    print(f"{Terminal.DARKGREEN}############################################{Terminal.ENDC}")
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