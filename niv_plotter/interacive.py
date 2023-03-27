import sys
from PyQt5 import QtWidgets, QtGui, QtCore

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        # call super class constructor
        super(MainWindow, self).__init__()
        # build the objects one by one
        layout = QtWidgets.QVBoxLayout(self)
        self.pb_load = QtWidgets.QPushButton('Load')
        self.pb_clear= QtWidgets.QPushButton('Clear')
        self.edit = QtWidgets.QTextEdit()
        layout.addWidget(self.edit)
        layout.addWidget(self.pb_load)
        layout.addWidget(self.pb_clear)
        # connect the callbacks to the push-buttons
        self.pb_load.clicked.connect(self.callback_pb_load)
        self.pb_clear.clicked.connect(self.callback_pb_clear)

    def callback_pb_load(self):
        self.edit.append('hello world')
    def callback_pb_clear(self):
        self.edit.clear()

def create_window(window_class):
    """Create a Qt window in Python, or interactively in IPython with Qt GUI
    event loop integration.
    """
    app_created = False
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        app_created = True
    app.references = set()
    window = window_class()
    app.references.add(window)
    window.show()
    if app_created:
        app.exec_()
    return window
