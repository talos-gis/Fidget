from __future__ import annotations

from typing import TYPE_CHECKING, Type

from qtalos.backend import load

if TYPE_CHECKING:
    import PyQt5.QtCore

__backend__ = load()

QEvent: Type[PyQt5.QtCore.QEvent] = __backend__['QtCore', 'QEvent']
QObject: Type[PyQt5.QtCore.QObject] = __backend__['QtCore', 'QObject']
Qt: Type[PyQt5.QtCore.Qt] = __backend__['QtCore', 'Qt']
pyqtSignal: Type[PyQt5.QtCore.pyqtSignal] = __backend__['QtCore', 'pyqtSignal']
