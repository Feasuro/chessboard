#!/usr/bin/env python
"""N-queens program logic and CLI"""

from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from codetiming import Timer
import solver

class Terminal :
    """Terminal escape characters"""
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    DARKGREEN = '\033[32m'
    RED = '\033[91m'
    ENDCOLOR = '\033[0m'
    CLEAR = '\033c'

####################################
# Section: chessboard implementation
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
        self._dim = solver.dimension(dim)
        self.board = dict(((n, k), '_') for n in range(1, self.dim+1) for k in range(1, self.dim+1))
        if queens is None :
            self.queens = [None] * self.dim
        elif solver.input_check(self.dim, queens) :
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
        result += '\n' + Terminal.ENDCOLOR
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
        if col is None :
            col = self.dim
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
                            if self.queens[i] is not None and self.field_check(f, (i+1, self.queens[i])) :
                                self.board[f] = '+'
                                break
                return True
            else :
                print(f'{Terminal.RED}Cannot place Queen here!{Terminal.ENDCOLOR}')
                return False
        else :
            print(f'{Terminal.RED}Incorrect field coordinates - out of range.{Terminal.ENDCOLOR}')
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

##########################################
# Section: interactive mode implementation
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
            dim = solver.dimension(input("Provide chessboard's dimension: "))
            break
        except ValueError :
            print("Provide a non-negative integer!")
    global myboard
    myboard = ChessBoard(dim)

def command_solve() -> None :
    """ Picks an algorithm and prints time. """
    if verbose :
        solver_method = multiverbose_solve if multi else verbose_solve
        input_method = myboard
    else :
        solver_method = solver.multi_solve if multi else solver.basic_solve
        input_method = myboard.queens

    with Timer(logger=lambda x: print(x, file=sys.stderr)) as timer :
        solver_method( input_method )

def show() -> None :
    """ Prints help message and current chessboard. """
    print(Terminal.CLEAR, end='')
    print(f"{Terminal.DARKGREEN}############################################")
    print(f"#{Terminal.ENDCOLOR} multiprocess={multi}, verbose={verbose}")
    print(f"{Terminal.DARKGREEN}############################################{Terminal.ENDCOLOR}")
    print("N - new chessboard")
    print("C - clear chessboard")
    print("x y - place/remove queen on field (x, y)")
    print("S - print solutions")
    print("m - toggle multiprocessing")
    print("v - toggle verbose output (slower)")
    print("E - exit program")
    print(myboard)
    print("Enter command:")

if __name__ == '__main__' :
    """ The program's main loop. """
    verbose = False
    multi = False
    myboard = ChessBoard(0)
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
                    verbose = not verbose
                    show()
                case 'M' :
                    multi = not multi
                    show()
                case 'C' :
                    myboard.clear()
                    show()
                case 'N' :
                    command_new()
                    show()
                case 'S' :
                    command_solve()
                    print("Enter command:")
                case _ :
                    if myboard.place_queen(command) :
                        show()
                    else:
                        print("Enter command:")
