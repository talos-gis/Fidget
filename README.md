#qTalos
## About
qTalos is an adapter of Qt into a functional-style interface. qTalos can be used seamlessly with PyQt5 and PySide2. qTalos is designed to create an effortless and rich UI for data science and analysis.

## Concept
Usage of qTalos is centered around the `ValueWidget` class. Simply put, a ValueWidget is a `QWidget` with a value. This value can then be read and used by parent widgets, or by the python program.

## Sample Usage
```
from typing import Tuple

from qtalos.backend.QtWidgets import QLineEdit, QHBoxLayout, QApplication
from qtalos.core import ValueWidget, ParseError

class PointWidget(ValueWidget[Tuple[float, float]]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x_edit = None
        self.y_edit = None
        self.init_ui()
        self.change_value()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout()
        with self.setup_provided(layout):
            self.x_edit = QLineEdit()
            self.x_edit.setPlaceholderText('X')
            self.x_edit.textChanged.connect(self.change_value)
            layout.addWidget(self.x_edit)

            self.y_edit = QLineEdit()
            self.y_edit.setPlaceholderText('Y')
            self.y_edit.textChanged.connect(self.change_value)
            layout.addWidget(self.y_edit)
        self.setLayout(layout)

    def parse(self):
        try:
            x = float(self.x_edit.text())
        except ValueError as e:
            raise ParseError('error in x') from e

        try:
            y = float(self.y_edit.text())
        except ValueError as e:
            raise ParseError('error in y') from e

        return x, y

app = QApplication([])
w = PointWidget('point', make_indicator=True, make_plaintext=True, make_title=True)
w.show()
res = app.exec_()
print(w.value())
if res != 0:
    exit(res)
```

<!-- todo add images -->

Phew, a lot of this is standard `QWidget` usage, so we'll just go over the new bits:
```
class PointWidget(ValueWidget[Tuple[float, float]]):
```
Every `ValueWidget` must extend the `ValueWidget` class (which extend the `QWidget` class). `ValueWidget` is a generic type, so it can be parametrized with its value type (in this case, a tuple of `int`s).

```
with self.setup_provided(layout):
```
`ValueWidget` provides some additional widgets called provided widgets, that can be added to it to improve usability. These can range from a simple title label, a label that changes to indicate whether the UI's state is valid, or even a button that opens a complex dialog with multiple methods to import/export the value as plain text. The `setup_provided` method returns a convenience context manager that adds these provided widgets before or after the main UI. All these provided widgets can be disabled either with constant values in the inheriting class, or with arguments when the widget is created (`PointWidget('point', make_indicator=True, make_plaintext=True, make_title=True)`).

```
self.x_edit.textChanged.connect(self.change_value)
self.y_edit.textChanged.connect(self.change_value)
```
The `ValueWidget` must be notified for when its value changes due to its children's value changing. So its `change_value` slot must be connected to any such signal.

```
def parse(self):
```
This is an abstract method that all `ValueWidget`s must implement. It processes the internal state of the widget's children, and returns a value (or raises a `ParseError`)

```
print(w.value())
```
each `ValueWidget` has a value in store, that can be extracted and used as normal.

This is all a lot of work, qTalos comes with many default implementations to make usage as effortless as possible:

```
from qtalos.backend.QtWidgets import QHBoxLayout
from qtalos.widgets import IntEdit, TupleWidget

from tests.gui.__util__ import test_as_main

class PointWidget(TupleWidget):
    INNER_TEMPLATES = [
        IntEdit.template('x', make_title=False),
        IntEdit.template('y', make_title=False)
    ]
    MAKE_PLAINTEXT = True
    MAKE_TITLE = True
    MAKE_INDICATOR = True
    LAYOUT_CLS = QHBoxLayout

app = QApplication([])
w = PointWidget('point')
w.show()
res = app.exec_()
print(w.value())
if res != 0:
    exit(res)
```

This will create a widget with similar capabilities as the one above.

## Plaintext Capability
One of qTalos's most extensive features is its plaintext conversion capability. Each `ValueWidget` has a set of plaintext printers and plaintext parsers, that can be selected to import/export a `ValueWidget`'s value. By default, a `ValueWidget` has no plaintext parsers, and only `str` and `repr` as printers.
### Adding printers and parsers
Printers and parsers can be added either by implementing the `ValueWidget`'s `plaintext_printers` or `plaintext_parsers` methods, or by creating a method in the class wrapped with `InnerPlaintextPrinter` or `InnerPlaintextParser`.

## Dual API
As seen in the example, almost all of the parameters the `ValueWidget` can provided upon creation can also have a default value filled in by extending classes.
```
from qtalos.widgets import ValueCheckBox

w = ValueCheckBox('title', ('YES', 'NO'), make_title=True)
# the following will create a widget equivelant to w
class MyValueCheckBox(ValueCheckBox):
    MAKE_TITLE=True

w = ValueCheckBox('title', ('YES', 'NO'))
```

## Support Widgets
qTalos comes with many builtin widgets to ease usage. Most usages will not have subclass 

## Compatibility
qTalos can use both PyQt5 and PySide2. By default, it will try to import both wrappers, starting with PySide2, and will use the first it successfully imported. This can be changed with `qtalos.backend`'s function: `prefer`.

Users of qTalos can also directly use whatever backend qTalos is using (thus ensuring compatibility) by importing Qt's members from `qtalos.backend` (currently, only imports from `QtWidgets` and `QtCore` are supported in this way)