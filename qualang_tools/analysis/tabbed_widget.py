import keyword
import os
import pkgutil
import re
import subprocess
import sys
from argparse import Namespace
from collections import OrderedDict
from functools import lru_cache

import pyqtgraph as pg
from pyqtgraph.Qt import QT_LIB, QtCore, QtGui, QtWidgets

app = pg.mkQApp()


path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, path)

import exampleLoaderTemplate_generic as ui_template
import utils

# based on https://github.com/art1415926535/PyQt5-syntax-highlighting

QRegularExpression = QtCore.QRegularExpression

QFont = QtGui.QFont
QColor = QtGui.QColor
QTextCharFormat = QtGui.QTextCharFormat
QSyntaxHighlighter = QtGui.QSyntaxHighlighter


def charFormat(color, style='', background=None):
    """
    Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    if type(color) is not str:
        _color.setRgb(color[0], color[1], color[2])
    else:
        _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Weight.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)
    if background is not None:
        _format.setBackground(pg.mkColor(background))

    return _format


def unnestedDict(exDict):
    """Converts a dict-of-dicts to a singly nested dict for non-recursive parsing"""
    out = {}
    for kk, vv in exDict.items():
        if isinstance(vv, dict):
            out.update(unnestedDict(vv))
        else:
            out[kk] = vv
    return out



class ExampleLoader(QtWidgets.QMainWindow):
    # update qtLibCombo item order to match bindings in the UI file and recreate
    # the templates files if you change bindings.
    bindings = {'PyQt6': 0, 'PySide6': 1, 'PyQt5': 2, 'PySide2': 3}
    modules = tuple(m.name for m in pkgutil.iter_modules())
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = ui_template.Ui_Form()
        self.cw = QtWidgets.QWidget()
        self.setCentralWidget(self.cw)
        self.ui.setupUi(self.cw)
        self.setWindowTitle("PyQtGraph Examples")
        self.codeBtn = QtWidgets.QPushButton('Run Edited Code')
        self.codeLayout = QtWidgets.QGridLayout()
        self.ui.readoutViewer.setLayout(self.codeLayout)
        app = QtWidgets.QApplication.instance()
        app.paletteChanged.connect(self.updateTheme)
        policy = QtWidgets.QSizePolicy.Policy.Expanding
        self.codeLayout.addItem(QtWidgets.QSpacerItem(100,100, policy, policy), 0, 0)
        self.codeLayout.addWidget(self.codeBtn, 1, 1)
        self.codeBtn.hide()

        self.curListener = None
        self.ui.qtLibCombo.addItems(self.bindings.keys())
        self.ui.qtLibCombo.setCurrentIndex(self.bindings[QT_LIB])



        self.itemCache = []
        self.populateTree(self.ui.qubitsList.invisibleRootItem(), utils.examples_)
        self.ui.qubitsList.expandAll()

        self.resize(1000,500)
        self.show()
        self.ui.splitter.setSizes([250,750])

        self.oldText = self.ui.readoutViewer.toPlainText()
        self.ui.loadBtn.clicked.connect(self.loadFile)
        self.ui.qubitsList.currentItemChanged.connect(self.showFile)
        self.ui.qubitsList.itemDoubleClicked.connect(self.loadFile)
        self.ui.readoutViewer.textChanged.connect(self.onTextChange)
        self.codeBtn.clicked.connect(self.runEditedCode)
        self.updateCodeViewTabWidth(self.ui.readoutViewer.font())

    def updateCodeViewTabWidth(self,font):
        """
        Change the codeView tabStopDistance to 4 spaces based on the size of the current font
        """
        fm = QtGui.QFontMetrics(font)
        tabWidth = fm.horizontalAdvance(' ' * 4)
        # the default value is 80 pixels! that's more than 2x what we want.
        self.ui.readoutViewer.setTabStopDistance(tabWidth)

    def showEvent(self, event) -> None:
        super(ExampleLoader, self).showEvent(event)
        disabledColor = QColor(QtCore.Qt.GlobalColor.red)
        for name, idx in self.bindings.items():
            disableBinding = name not in self.modules
            if disableBinding:
                item = self.ui.qtLibCombo.model().item(idx)
                item.setData(disabledColor, QtCore.Qt.ItemDataRole.ForegroundRole)
                item.setEnabled(False)
                item.setToolTip(f'{item.text()} is not installed')

    def onTextChange(self):
        """
        textChanged fires when the highlighter is reassigned the same document.
        Prevent this from showing "run edited code" by checking for actual
        content change
        """
        newText = self.ui.readoutViewer.toPlainText()
        if newText != self.oldText:
            self.oldText = newText
            self.codeEdited() 

    def filterByTitle(self, text):
        self.showExamplesByTitle(self.getMatchingTitles(text))
        self.hl.setDocument(self.ui.readoutViewer.document())

    def filterByContent(self, text=None):
        # If the new text isn't valid regex, fail early and highlight the search filter red to indicate a problem
        # to the user
        validRegex = True
        try:
            re.compile(text)
            self.ui.exampleFilter.setStyleSheet('')
        except re.error:
            colors = DarkThemeColors if app.property('darkMode') else LightThemeColors
            errorColor = pg.mkColor(colors.Red)
            validRegex = False
            errorColor.setAlpha(100)
            # Tuple prints nicely :)
            self.ui.exampleFilter.setStyleSheet(f'background: rgba{errorColor.getRgb()}')
        if not validRegex:
            return
        checkDict = unnestedDict(utils.examples_)
        self.hl.searchText = text
        # Need to reapply to current document
        self.hl.setDocument(self.ui.readoutViewer.document())
        titles = []
        text = text.lower()
        for kk, vv in checkDict.items():
            if isinstance(vv, Namespace):
                vv = vv.filename
            filename = os.path.join(path, vv)
            contents = self.getExampleContent(filename).lower()
            if text in contents:
                titles.append(kk)
        self.showExamplesByTitle(titles)

    def getMatchingTitles(self, text, exDict=None, acceptAll=False):
        if exDict is None:
            exDict = utils.examples_
        text = text.lower()
        titles = []
        for kk, vv in exDict.items():
            matched = acceptAll or text in kk.lower()
            if isinstance(vv, dict):
                titles.extend(self.getMatchingTitles(text, vv, acceptAll=matched))
            elif matched:
                titles.append(kk)
        return titles

    def showExamplesByTitle(self, titles):
        QTWI = QtWidgets.QTreeWidgetItemIterator
        flag = QTWI.IteratorFlag.NoChildren
        treeIter = QTWI(self.ui.qubitsList, flag)
        item = treeIter.value()
        while item is not None:
            parent = item.parent()
            show = (item.childCount() or item.text(0) in titles)
            item.setHidden(not show)

            # If all children of a parent are gone, hide it
            if parent:
                hideParent = True
                for ii in range(parent.childCount()):
                    if not parent.child(ii).isHidden():
                        hideParent = False
                        break
                parent.setHidden(hideParent)

            treeIter += 1
            item = treeIter.value()

    def simulate_black_mode(self):
        """
        used to simulate MacOS "black mode" on other platforms
        intended for debug only, as it manage only the QPlainTextEdit
        """
        # first, a dark background
        c = QtGui.QColor('#171717')
        p = self.ui.readoutViewer.palette()
        p.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base, c)
        p.setColor(QtGui.QPalette.ColorGroup.Inactive, QtGui.QPalette.ColorRole.Base, c)
        self.ui.readoutViewer.setPalette(p)
        # then, a light font
        f = QtGui.QTextCharFormat()
        f.setForeground(QtGui.QColor('white'))
        self.ui.readoutViewer.setCurrentCharFormat(f)
        # finally, override application automatic detection
        app = QtWidgets.QApplication.instance()
        app.setProperty('darkMode', True)

    def updateTheme(self):
        self.hl = PythonHighlighter(self.ui.readoutViewer.document())

    def populateTree(self, root, examples):
        bold_font = None
        for key, val in examples.items():
            item = QtWidgets.QTreeWidgetItem([key])
            self.itemCache.append(item) # PyQt 4.9.6 no longer keeps references to these wrappers,
                                        # so we need to make an explicit reference or else the .file
                                        # attribute will disappear.
            if isinstance(val, OrderedDict):
                self.populateTree(item, val)
            elif isinstance(val, Namespace):
                item.file = val.filename
                if 'recommended' in val:
                    if bold_font is None:
                        bold_font = item.font(0)
                        bold_font.setBold(True)
                    item.setFont(0, bold_font)
            else:
                item.file = val
            root.addChild(item)

    def currentFile(self):
        item = self.ui.qubitsList.currentItem()
        if hasattr(item, 'file'):
            return os.path.join(path, item.file)
        return None

    def loadFile(self, edited=False):
        qtLib = self.ui.qtLibCombo.currentText()
        env = dict(os.environ, PYQTGRAPH_QT_LIB=qtLib)
        example_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.dirname(os.path.dirname(example_path))
        env['PYTHONPATH'] = f'{path}'
        if edited:
            proc = subprocess.Popen([sys.executable, '-'], stdin=subprocess.PIPE, cwd=example_path, env=env)
            code = self.ui.readoutViewer.toPlainText().encode('UTF-8')
            proc.stdin.write(code)
            proc.stdin.close()
        else:
            fn = self.currentFile()
            if fn is None:
                return
            subprocess.Popen([sys.executable, fn], cwd=path, env=env)

    def showFile(self):
        fn = self.currentFile()
        text = self.getExampleContent(fn)
        self.ui.readoutViewer.setPlainText(text)
        self.ui.loadedFileLabel.setText(fn)
        self.codeBtn.hide()

    @lru_cache(100)
    def getExampleContent(self, filename):
        if filename is None:
            self.ui.readoutViewer.clear()
            return
        if os.path.isdir(filename):
            filename = os.path.join(filename, '__main__.py')
        with open(filename, "r") as currentFile:
            text = currentFile.read()
        return text

    def codeEdited(self):
        self.codeBtn.show()

    def runEditedCode(self):
        self.loadFile(edited=True)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if not (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            return
        key = event.key()
        Key = QtCore.Qt.Key

        # Allow quick navigate to search
        if key == Key.Key_F:
            self.ui.exampleFilter.setFocus()
            event.accept()
            return

        if key not in [Key.Key_Plus, Key.Key_Minus, Key.Key_Underscore, Key.Key_Equal, Key.Key_0]:
            return
        font = self.ui.readoutViewer.font()
        oldSize = font.pointSize()
        if key == Key.Key_Plus or key == Key.Key_Equal:
            font.setPointSize(oldSize + max(oldSize*.15, 1))
        elif key == Key.Key_Minus or key == Key.Key_Underscore:
            newSize = oldSize - max(oldSize*.15, 1)
            font.setPointSize(max(newSize, 1))
        elif key == Key.Key_0:
            # Reset to original size
            font.setPointSize(10)
        self.ui.readoutViewer.setFont(font)
        self.updateCodeViewTabWidth(font)
        event.accept()

def main():
    app = pg.mkQApp()
    loader = ExampleLoader()
    loader.ui.qubitsList.setCurrentIndex(
        loader.ui.qubitsList.model().index(0, 0)
    )
    pg.exec()

if __name__ == '__main__':
    main()