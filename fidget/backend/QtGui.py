from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    import PyQt5.QtGui

__backend__ = load()

_QtGui = __backend__.partial('QtGui')

QDesktopServices: Type[PyQt5.QtGui.QDesktopServices] = _QtGui['QDesktopServices']
QColor: Type[PyQt5.QtGui.QColor] = _QtGui['QColor']
QCursor: Type[PyQt5.QtGui.QCursor] = _QtGui['QCursor']
QFontDatabase: Type[PyQt5.QtGui.QFontDatabase] = _QtGui['QFontDatabase']
QIcon: Type[PyQt5.QtGui.QIcon] = _QtGui['QIcon']
QPainter: Type[PyQt5.QtGui.QPainter] = _QtGui['QPainter']
QTextFormat: Type[PyQt5.QtGui.QTextFormat] = _QtGui['QTextFormat']


def __getattr__(name):
    return _QtGui[name]
