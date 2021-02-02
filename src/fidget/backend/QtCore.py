from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    from PySide6 import QtCore as __QtCore

__backend__ = load()

_QtCore = __backend__.partial('QtCore')

QtCore = __backend__.module('QtCore')
QEvent: Type[__QtCore.QEvent] = _QtCore['QEvent']
QEventLoop: Type[__QtCore.QEventLoop] = _QtCore['QEventLoop']
QObject: Type[__QtCore.QObject] = _QtCore['QObject']
Qt: Type[__QtCore.Qt] = _QtCore['Qt']
pyqtSignal: Type[__QtCore.Signal] = _QtCore['pyqtSignal']
QRect: Type[__QtCore.QRect] = _QtCore['QRect']
QSize: Type[__QtCore.QSize] = _QtCore['QSize']
QRegularExpression: Type[__QtCore.QRegularExpression] = _QtCore['QRegularExpression']
QRegExp = QRegularExpression
# QRegExp: Type[__QtCore.QRegExp] = _QtCore['QRegExp']


def __getattr__(name):
    return _QtCore[name]
