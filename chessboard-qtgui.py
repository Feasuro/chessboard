#!/usr/bin/env python
"""Qt6 graphic user interface for N-queens solver program"""

import re
import sys
import os
import time

from PyQt6.QtCore import QPoint, QProcess, QRect, QSize, Qt, QTranslator, QLibraryInfo, QLocale
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QAction, QBrush, QIcon, QPainter
from PyQt6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDockWidget, QGridLayout,
                             QInputDialog, QLabel, QListWidget, QListWidgetItem, QMainWindow,
                             QMessageBox, QSizePolicy, QToolBar, QWidget)

from chessboard import ChessBoard
import resources

DEBUG = os.getenv("DEBUG")

class Solution(QListWidgetItem):
    """It is made from list not str and stores it for later use"""
    def __init__(self, queens: list, *args, **kwargs):
        super().__init__(str(queens), *args, **kwargs)
        self.queens = list(queens)

class FieldButton(QAbstractButton):
    """Button that looks like a chessboard field"""
    click = Signal(tuple)

    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #fieldbutton is aware of it's position and color
        self.col, self.row = field

        if self.col % 2 * self.row % 2 == 0 and self.col % 2 + self.row % 2 == 1:
            self.setProperty('color', 'white')
        else:
            self.setProperty('color', 'black')

        #emits it's coordinates when clicked
        self.clicked.connect(self.on_click)

        #wants to be square
        square = QSizePolicy()
        square.setHeightForWidth(True)
        square.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        square.setVerticalPolicy(QSizePolicy.Policy.Ignored)
        self.setSizePolicy(square)

    def heightForWidth(self, width: int) -> int:
        """ Be a square """
        return width

    def sizeHint(self) -> QSize:
        """ Propose a size of an icon """
        return QSize(36, 36)

    def paintEvent(self, event) -> None:
        """ Configure how it actually looks. """
        painter = QPainter(self)
        if self.property('color') == 'white':
            painter.setBrush(QBrush(Qt.GlobalColor.white))
        elif self.property('color') == 'black':
            painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawRect(QRect(QPoint(0, 0), self.size()))
        self.icon().paint(painter, int(self.width() / 6), int(self.height() / 6),
                          int(self.width() * 2/3), int(self.height() * 2/3))

    def on_click(self) -> None:
        """ Make this signal emit coordinates """
        self.click.emit((self.col, self.row))


class Board(QWidget):
    """Widget that stores the chessboard and draws it"""
    def __init__(self, dim, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #here's the chessboard and it's fields graphic representation
        self.chess = ChessBoard(dim)
        self.buttons = {field: FieldButton(field, click=self.field_state) for field in self.chess.board}

        #field-buttons arranged properly
        layout = QGridLayout()
        layout.setSpacing(0)
        for i in range(self.chess.dim):
            layout.addWidget(QLabel(str(i+1)+' '), self.chess.dim - i -1, 0)
            layout.addWidget(QLabel(str(i+1)), self.chess.dim, i + 1, alignment=Qt.AlignmentFlag.AlignCenter)
        for field in self.buttons:
            layout.addWidget(self.buttons[field], self.chess.dim - field[1], field[0])
        self.setLayout(layout)

    def paintEvent(self, event) -> None:
        """ Always stay square. """ 
        self.setFixedWidth(self.height())
        super().paintEvent(event)

    def field_state(self, field) -> None:
        """ Updates chessboard's state when a field is clicked. """
        if self.chess.place_queen(field):
            self.update_state()
        else:
            QMessageBox.critical(self, self.tr("Forbidden"), self.tr("Cannot place Queen here!"))

    def update_state(self) -> None:
        """ Redraws icons after underlying chessboard's change. """
        for field in self.chess.board:
            if self.chess.board[field] == 'Q' and self.buttons[field].property('color') == 'white':
                self.buttons[field].setIcon(QIcon(':/icons/qblack'))
            elif self.chess.board[field] == 'Q' and self.buttons[field].property('color') == 'black':
                self.buttons[field].setIcon(QIcon(':/icons/qwhite'))
            elif self.chess.board[field] == '+':
                self.buttons[field].setIcon(QIcon(':/icons/cross'))
            else:
                self.buttons[field].setIcon(QIcon())


class MainWindow(QMainWindow):
    """Provides graphic interface for playing with and solving the n-Queens problem"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #size and title bar
        self.setWindowTitle(self.tr("N-Queens solver"))
        self.setWindowIcon(QIcon(':/icons/qwhite'))
        self.setGeometry(100,100,700,500)
        #setup control of worker proces for computation
        self.solver = QProcess()
        self.solver.setProgram('./solver.py')
        self.solver.finished.connect(self.finish_computation)
        self.solver.readyReadStandardOutput.connect(self.populate_solutions)
        self.solver.readyReadStandardError.connect(self.handle_stderr)
        self.solver.time = '?'
        #make the window and show it
        self.ui_setup()
        self.show()

    def ui_setup(self) -> None:
        """ Arranges all window elements. """
        #put chessboard in the center
        self.body = Board(0)
        self.setCentralWidget(self.body)
        #list of solutions in dock widget
        self.solutions = QListWidget()
        self.solutions.itemDoubleClicked.connect(self.show_solution)
        dock = QDockWidget(self.tr("Solutions"))
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        dock.setMaximumWidth(250)
        dock.setWidget(self.solutions)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        #available actions creation and configuration
        names = ('new', 'clear', 'solve', 'cancel')
        self.actions = {name: QAction(self.tr(name).capitalize(), self) for name in names}
        self.actions['new'].triggered.connect(self.new_chessboard)
        self.actions['clear'].triggered.connect(self.clear_chessboard)
        self.actions['solve'].triggered.connect(self.solve_chessboard)
        self.actions['cancel'].triggered.connect(self.finish_computation)
        self.actions['cancel'].setDisabled(True)
        self.multi = QCheckBox(self.tr("Multiprocess solving"), self)
        #toolbar arrangement and styling
        toolbar = QToolBar()
        toolbar.addAction(self.actions['new'])
        toolbar.addAction(self.actions['clear'])
        toolbar.addSeparator()
        toolbar.addAction(self.actions['solve'])
        toolbar.addWidget(self.multi)
        toolbar.addAction(self.actions['cancel'])
        for name, action in self.actions.items():
            toolbar.widgetForAction(action).setObjectName(name)
        toolbar.setStyleSheet( " QToolButton#cancel::enabled { color: red; } " )
        self.addToolBar(toolbar)
        #statusbar setup
        self.statusbar = self.statusBar()
        self.statuslabel = QLabel(self.tr("{} known solutions").format(self.solutions.count()))
        self.statusbar.addPermanentWidget(self.statuslabel)

    def new_chessboard(self) -> None:
        """ Ask user for dimension, clear the solution list and create new chessboard. """
        dim, ok = QInputDialog.getInt(self, self.tr("New Chessboard"), self.tr("Provide new chessboard's dimension:"))
        if ok :
            self.solutions.clear()
            self.body = Board(dim)
            self.setCentralWidget(self.body)

    def clear_chessboard(self) -> None:
        """ Clear chessboard and update icons. """
        self.body.chess.clear()
        self.body.update_state()

    def solve_chessboard(self) -> None:
        """ 'Solve' action handler. """
        #remove previous solutions
        self.solutions.clear()
        #change actions' availability when computations are in progress
        for name, action in self.actions.items():
            if name == 'cancel':
                action.setDisabled(False)
            else:
                action.setDisabled(True)
        self.multi.setDisabled(True)
        #pass actual chessboard arrangement as commandline arguments
        M = ['-m'] if self.multi.isChecked() else []
        self.solver.setArguments(M + ['-d', str(self.body.chess.dim), '-q'] + [str(q) if q else 'N' for q in self.body.chess.queens])
        #give some feedback on what is being done
        if DEBUG: print(time.strftime('%x %X'), 'NOTICE: Starting solver process.', file=sys.stderr)
        self.statusbar.showMessage(self.tr("Computation in progress"))
        #fire up the calculations
        self.solver.start()

    def finish_computation(self) -> None:
        """ Handle computation finish and user interrupt. """
        #if process is still running cancel it
        if self.solver.state() is not QProcess.ProcessState.NotRunning :
            if DEBUG: print(time.strftime('%x %X'), 'NOTICE: Terminating solver process', file=sys.stderr)
            self.solver.terminate()
        #print some feedback
        if DEBUG: print(time.strftime('%x %X'), 'NOTICE: Solver process stopped -', self.solver.exitStatus(), file=sys.stderr)
        self.statusbar.showMessage(self.tr("Finished"), 4000)
        #restore default actions' availability
        self.multi.setDisabled(False)
        for name, action in self.actions.items():
            if name == 'cancel':
                action.setDisabled(True)
            else:
                action.setDisabled(False)
        #display a summary messages
        self.statuslabel.setText(self.tr("{} known solutions").format(self.solutions.count()))
        QMessageBox.information(self, self.tr("Solved"), self.tr("Found {} solutions in {} seconds.").format(self.solutions.count(), self.solver.time))
        self.solver.time = '?'

    def populate_solutions(self) -> None:
        """ Read results, reformat and append them to the list. """
        while data := self.solver.readLine(): # data is a QByteArray
            text = str(data).strip("bn[']\\")
            queens = [int(i) for i in text.split(', ')] if text else []
            Solution(queens, self.solutions)

    def show_solution(self, solution: Solution) -> None:
        """ Maps given solution to the current chessboard. """
        self.body.chess.clear()
        for field in enumerate(solution.queens, start=1):
            self.body.chess.place_queen(field)
        self.body.update_state()

    def handle_stderr(self) -> None:
        """ Print worker stderr output to terminal, remember running time. """
        regex = r'Elapsed time: (\d+.\d+e?-?\d*) seconds'
        data = self.solver.readAllStandardError()
        text = bytes(data).decode("utf8")
        try:
            self.solver.time = float( re.search(regex, text).group(1) )
        except Exception as e:
            if DEBUG: print(time.strftime('%x %X'), "ERROR: Cannot read time -", file=sys.stderr)
        else:
            if DEBUG: print(text, file=sys.stderr)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(QLocale(), "qtbase", "_", path):
        app.installTranslator(translator)
    translator = QTranslator(app)
    if translator.load(QLocale(), "queens", "_", ":/i18n"):
        app.installTranslator(translator)

    window = MainWindow()
    sys.exit(app.exec())
