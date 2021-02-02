from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    from PySide6 import QtGui as __QtGui

__backend__ = load()

_QtGui = __backend__.partial('QtGui')
_QtWidgets = __backend__.partial('QtWidgets')

QtGui = __backend__.module('QtGui')

QAction: Type[__QtGui.QAction] = _QtGui['QAction'] if __backend__.qt_version >= 6 else _QtWidgets['QAction']
QDesktopServices: Type[__QtGui.QDesktopServices] = _QtGui['QDesktopServices']
QColor: Type[__QtGui.QColor] = _QtGui['QColor']
QTextCharFormat: Type[__QtGui.QTextCharFormat] = _QtGui['QTextCharFormat']
QFont: Type[__QtGui.QFont] = _QtGui['QFont']
QSyntaxHighlighter: Type[__QtGui.QSyntaxHighlighter] = _QtGui['QSyntaxHighlighter']
QCursor: Type[__QtGui.QCursor] = _QtGui['QCursor']
QFontDatabase: Type[__QtGui.QFontDatabase] = _QtGui['QFontDatabase']
QIcon: Type[__QtGui.QIcon] = _QtGui['QIcon']
QPainter: Type[__QtGui.QPainter] = _QtGui['QPainter']
QPixmap: Type[__QtGui.QPixmap] = _QtGui['QPixmap']
QTextFormat: Type[__QtGui.QTextFormat] = _QtGui['QTextFormat']
QValidator: Type[__QtGui.QValidator] = _QtGui['QValidator']


def __getattr__(name):
    return _QtGui[name]
