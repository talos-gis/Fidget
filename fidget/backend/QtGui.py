from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    import PyQt5.QtGui

__backend__ = load()

_QtGui = __backend__.partial('QtGui')

QDesktopServices: Type[PyQt5.QtGui.QDesktopServices] = _QtGui['QDesktopServices']
QColor: Type[PyQt5.QtGui.QColor] = _QtGui['QColor']
QPainter: Type[PyQt5.QtGui.QPainter] = _QtGui['QPainter']
QTextFormat: Type[PyQt5.QtGui.QTextFormat] = _QtGui['QTextFormat']


def __getattr__(name):
    return _QtGui[name]
