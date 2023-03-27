#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Exmaple pattern of setting up PyQt to run
under iPython and not block, by default.
Code modified from:
ZetCode PyQt4 tutorial
In this example, we receive data from
a QtGui.QInputDialog dialog.
author: Jan Bodnar
website: zetcode.com
last edited: October 2011
"""

import sys
from PyQt5 import QtGui, QtCore

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class Example(QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        self.btn = QPushButton('Dialog', self)
        self.btn.move(20, 20)
        self.btn.clicked.connect(self.showDialog)

        self.le = QLineEdit(self)
        self.le.move(130, 22)

        self.setGeometry(300, 300, 290, 150)
        self.setWindowTitle('Input dialog')
        self.show()

    def showDialog(self):

        text, ok = QInputDialog.getText(self, 'Input Dialog',
            'Enter your name:')

        if ok:
            self.le.setText(str(text))

def start_gui(block=False):
    try:
        if not block & __IPYTHON__:
            from IPython.lib.inputhook import enable_gui
            app = enable_gui('qt4')
        else:
            raise ImportError
    except (ImportError, NameError):
        app = QtCore.QCoreApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

    ex = Example()

    try:
        from IPython.lib.guisupport import start_event_loop_qt4
        start_event_loop_qt4(app)
        return ex
    except ImportError:
        app.exec_()

def _main():
    start_gui(block=True)

if __name__ == '__main__':
    _main()