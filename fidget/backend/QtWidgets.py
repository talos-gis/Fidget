from __future__ import annotations

from typing import TYPE_CHECKING, Type

from fidget.backend import load

if TYPE_CHECKING:
    import PyQt5.QtWidgets

__backend__ = load()
_QtWidgets = __backend__.partial('QtWidgets')

QtWidgets = __backend__.module('QtWidgets')

QAction: Type[PyQt5.QtWidgets.QAction] = _QtWidgets['QAction']
QApplication: Type[PyQt5.QtWidgets.QApplication] = _QtWidgets['QApplication']
QBoxLayout: Type[PyQt5.QtWidgets.QBoxLayout] = _QtWidgets['QBoxLayout']
QCheckBox: Type[PyQt5.QtWidgets.QCheckBox] = _QtWidgets['QCheckBox']
QComboBox: Type[PyQt5.QtWidgets.QComboBox] = _QtWidgets['QComboBox']
QDialog: Type[PyQt5.QtWidgets.QDialog] = _QtWidgets['QDialog']
QDoubleSpinBox: Type[PyQt5.QtWidgets.QDoubleSpinBox] = _QtWidgets['QDoubleSpinBox']
QFileDialog: Type[PyQt5.QtWidgets.QFileDialog] = _QtWidgets['QFileDialog']
QFontComboBox: Type[PyQt5.QtWidgets.QFontComboBox] = _QtWidgets['QFontComboBox']
QFrame: Type[PyQt5.QtWidgets.QFrame] = _QtWidgets['QFrame']
QGridLayout: Type[PyQt5.QtWidgets.QGridLayout] = _QtWidgets['QGridLayout']
QGroupBox: Type[PyQt5.QtWidgets.QGroupBox] = _QtWidgets['QGroupBox']
QHBoxLayout: Type[PyQt5.QtWidgets.QHBoxLayout] = _QtWidgets['QHBoxLayout']
QLabel: Type[PyQt5.QtWidgets.QLabel] = _QtWidgets['QLabel']
QLineEdit: Type[PyQt5.QtWidgets.QLineEdit] = _QtWidgets['QLineEdit']
QMainWindow: Type[PyQt5.QtWidgets.QMainWindow] = _QtWidgets['QMainWindow']
QMenu: Type[PyQt5.QtWidgets.QMenu] = _QtWidgets['QMenu']
QMessageBox: Type[PyQt5.QtWidgets.QMessageBox] = _QtWidgets['QMessageBox']
QPlainTextEdit: Type[PyQt5.QtWidgets.QPlainTextEdit] = _QtWidgets['QPlainTextEdit']
QTextEdit: Type[PyQt5.QtWidgets.QTextEdit] = _QtWidgets['QTextEdit']
QPushButton: Type[PyQt5.QtWidgets.QPushButton] = _QtWidgets['QPushButton']
QRadioButton: Type[PyQt5.QtWidgets.QRadioButton] = _QtWidgets['QRadioButton']
QScrollArea: Type[PyQt5.QtWidgets.QScrollArea] = _QtWidgets['QScrollArea']
QSizePolicy: Type[PyQt5.QtWidgets.QSizePolicy] = _QtWidgets['QSizePolicy']
QSpinBox: Type[PyQt5.QtWidgets.QSpinBox] = _QtWidgets['QSpinBox']
QStackedWidget: Type[PyQt5.QtWidgets.QStackedWidget] = _QtWidgets['QStackedWidget']
QStyle: Type[PyQt5.QtWidgets.QStyle] = _QtWidgets['QStyle']
QTabWidget: Type[PyQt5.QtWidgets.QTabWidget] = _QtWidgets['QTabWidget']
QToolButton: Type[PyQt5.QtWidgets.QToolButton] = _QtWidgets['QToolButton']
QTreeWidget: Type[PyQt5.QtWidgets.QTreeWidget] = _QtWidgets['QTreeWidget']
QTreeWidgetItem: Type[PyQt5.QtWidgets.QTreeWidgetItem] = _QtWidgets['QTreeWidgetItem']
QVBoxLayout: Type[PyQt5.QtWidgets.QVBoxLayout] = _QtWidgets['QVBoxLayout']
QWidget: Type[PyQt5.QtWidgets.QWidget] = _QtWidgets['QWidget']


def __getattr__(name):
    return _QtWidgets[name]
