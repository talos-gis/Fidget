from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    import PyQt5.QtGui

__backend__ = load()

_QtGui = __backend__.partial('QtGui')

QDesktopServices: Type[PyQt5.QtGui.QDesktopServices] = _QtGui['QDesktopServices']


def __getattr__(name):
    return _QtGui[name]
