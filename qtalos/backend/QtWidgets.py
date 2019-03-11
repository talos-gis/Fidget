from __future__ import annotations

from typing import TYPE_CHECKING, Type

from qtalos.backend import load

if TYPE_CHECKING:
    import PyQt5.QtWidgets

__backend__ = load()


QApplication: Type[PyQt5.QtWidgets.QApplication] = __backend__['QtWidgets', 'QApplication']
QBoxLayout: Type[PyQt5.QtWidgets.QBoxLayout] = __backend__['QtWidgets', 'QBoxLayout']
QCheckBox: Type[PyQt5.QtWidgets.QCheckBox] = __backend__['QtWidgets', 'QCheckBox']
QComboBox: Type[PyQt5.QtWidgets.QComboBox] = __backend__['QtWidgets', 'QComboBox']
QDialog: Type[PyQt5.QtWidgets.QDialog] = __backend__['QtWidgets', 'QDialog']
QFileDialog: Type[PyQt5.QtWidgets.QFileDialog] = __backend__['QtWidgets', 'QFileDialog']
QFrame: Type[PyQt5.QtWidgets.QFrame] = __backend__['QtWidgets', 'QFrame']
QGridLayout: Type[PyQt5.QtWidgets.QGridLayout] = __backend__['QtWidgets', 'QGridLayout']
QGroupBox: Type[PyQt5.QtWidgets.QGroupBox] = __backend__['QtWidgets', 'QGroupBox']
QHBoxLayout: Type[PyQt5.QtWidgets.QHBoxLayout] = __backend__['QtWidgets', 'QHBoxLayout']
QLabel: Type[PyQt5.QtWidgets.QLabel] = __backend__['QtWidgets', 'QLabel']
QLineEdit: Type[PyQt5.QtWidgets.QLineEdit] = __backend__['QtWidgets', 'QLineEdit']
QMessageBox: Type[PyQt5.QtWidgets.QMessageBox] = __backend__['QtWidgets', 'QMessageBox']
QPlainTextEdit: Type[PyQt5.QtWidgets.QPlainTextEdit] = __backend__['QtWidgets', 'QPlainTextEdit']
QPushButton: Type[PyQt5.QtWidgets.QPushButton] = __backend__['QtWidgets', 'QPushButton']
QRadioButton: Type[PyQt5.QtWidgets.QRadioButton] = __backend__['QtWidgets', 'QRadioButton']
QScrollArea: Type[PyQt5.QtWidgets.QScrollArea] = __backend__['QtWidgets', 'QScrollArea']
QStackedWidget: Type[PyQt5.QtWidgets.QStackedWidget] = __backend__['QtWidgets', 'QStackedWidget']
QVBoxLayout: Type[PyQt5.QtWidgets.QVBoxLayout] = __backend__['QtWidgets', 'QVBoxLayout']
QWidget: Type[PyQt5.QtWidgets.QWidget] = __backend__['QtWidgets', 'QWidget']