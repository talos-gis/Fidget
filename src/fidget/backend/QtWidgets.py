from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    from PySide6 import QtWidgets as __QtWidgets

__backend__ = load()
_QtWidgets = __backend__.partial('QtWidgets')

QtWidgets = __backend__.module('QtWidgets')

QApplication: Type[__QtWidgets.QApplication] = _QtWidgets['QApplication']
QBoxLayout: Type[__QtWidgets.QBoxLayout] = _QtWidgets['QBoxLayout']
QCheckBox: Type[__QtWidgets.QCheckBox] = _QtWidgets['QCheckBox']
QComboBox: Type[__QtWidgets.QComboBox] = _QtWidgets['QComboBox']
QDialog: Type[__QtWidgets.QDialog] = _QtWidgets['QDialog']
QDoubleSpinBox: Type[__QtWidgets.QDoubleSpinBox] = _QtWidgets['QDoubleSpinBox']
QFileDialog: Type[__QtWidgets.QFileDialog] = _QtWidgets['QFileDialog']
QFontComboBox: Type[__QtWidgets.QFontComboBox] = _QtWidgets['QFontComboBox']
QFrame: Type[__QtWidgets.QFrame] = _QtWidgets['QFrame']
QGridLayout: Type[__QtWidgets.QGridLayout] = _QtWidgets['QGridLayout']
QGroupBox: Type[__QtWidgets.QGroupBox] = _QtWidgets['QGroupBox']
QHBoxLayout: Type[__QtWidgets.QHBoxLayout] = _QtWidgets['QHBoxLayout']
QLabel: Type[__QtWidgets.QLabel] = _QtWidgets['QLabel']
QLineEdit: Type[__QtWidgets.QLineEdit] = _QtWidgets['QLineEdit']
QMainWindow: Type[__QtWidgets.QMainWindow] = _QtWidgets['QMainWindow']
QMenu: Type[__QtWidgets.QMenu] = _QtWidgets['QMenu']
QMessageBox: Type[__QtWidgets.QMessageBox] = _QtWidgets['QMessageBox']
QPlainTextEdit: Type[__QtWidgets.QPlainTextEdit] = _QtWidgets['QPlainTextEdit']
QTextEdit: Type[__QtWidgets.QTextEdit] = _QtWidgets['QTextEdit']
QPushButton: Type[__QtWidgets.QPushButton] = _QtWidgets['QPushButton']
QRadioButton: Type[__QtWidgets.QRadioButton] = _QtWidgets['QRadioButton']
QScrollArea: Type[__QtWidgets.QScrollArea] = _QtWidgets['QScrollArea']
QSizePolicy: Type[__QtWidgets.QSizePolicy] = _QtWidgets['QSizePolicy']
QSpinBox: Type[__QtWidgets.QSpinBox] = _QtWidgets['QSpinBox']
QStackedWidget: Type[__QtWidgets.QStackedWidget] = _QtWidgets['QStackedWidget']
QStyle: Type[__QtWidgets.QStyle] = _QtWidgets['QStyle']
QTabWidget: Type[__QtWidgets.QTabWidget] = _QtWidgets['QTabWidget']
QToolButton: Type[__QtWidgets.QToolButton] = _QtWidgets['QToolButton']
QTreeWidget: Type[__QtWidgets.QTreeWidget] = _QtWidgets['QTreeWidget']
QTreeWidgetItem: Type[__QtWidgets.QTreeWidgetItem] = _QtWidgets['QTreeWidgetItem']
QVBoxLayout: Type[__QtWidgets.QVBoxLayout] = _QtWidgets['QVBoxLayout']
QWidget: Type[__QtWidgets.QWidget] = _QtWidgets['QWidget']


def __getattr__(name):
    return _QtWidgets[name]
