from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    import PyQt5.QtCore

__backend__ = load()

_QtCore = __backend__.partial('QtCore')

QtCore = __backend__.module('QtCore')
QEvent: Type[PyQt5.QtCore.QEvent] = _QtCore['QEvent']
QEventLoop: Type[PyQt5.QtCore.QEventLoop] = _QtCore['QEventLoop']
QObject: Type[PyQt5.QtCore.QObject] = _QtCore['QObject']
Qt: Type[PyQt5.QtCore.Qt] = _QtCore['Qt']
pyqtSignal: Type[PyQt5.QtCore.pyqtSignal] = _QtCore['pyqtSignal']
QRect: Type[PyQt5.QtCore.QRect] = _QtCore['QRect']
QSize: Type[PyQt5.QtCore.QSize] = _QtCore['QSize']
QRegExp: Type[PyQt5.QtCore.QRegExp] = _QtCore['QRegExp']


def __getattr__(name):
    return _QtCore[name]
