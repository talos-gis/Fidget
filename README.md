# Fidget

Fidget is an adapter of Qt into a functional-style interface. Fidget can be used seamlessly with PyQt5 and PySide2. Fidget is designed to create an effortless and rich UI for data science and analysis.

## Concept
Usage of fidget is centered around the `Fidget` class. Simply put, a Fidget (short for Functional Widget) is a `QWidget` with a value. This value can then be read and used by parent widgets, or by the python program.

## Sample Usage
```python
from typing import Tuple

from fidget.backend.QtWidgets import QLineEdit, QHBoxLayout, QApplication
from fidget.core import Fidget, ParseError

class PointWidget(Fidget[Tuple[float, float]]):
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
```python
class PointWidget(Fidget[Tuple[float, float]]):
```
Every `Fidget` must extend the `Fidget` class (which extend the `QWidget` class). `Fidget` is a generic type, so it can be parametrized with its value type (in this case, a tuple of `float`s). Like all generic types, the generic parameter has no effect on the code.

```python
with self.setup_provided(layout):
```
`Fidget` provides some additional widgets called provided widgets, that can be added to it to improve usability. These can range from a simple title label, a label that changes to indicate whether the UI's state is valid, or even a button that opens a complex dialog with multiple methods to import/export the value as plain text. The `setup_provided` method returns a convenience context manager that adds these provided widgets before and after the main UI. All these provided widgets can be disabled either with constant values in the inheriting class, or with arguments when the widget is created (`PointWidget('point', make_indicator=True, make_plaintext=True, make_title=True)`).

```python
self.x_edit.textChanged.connect(self.change_value)
self.y_edit.textChanged.connect(self.change_value)
```
The `Fidget` must be notified for when its value changes due to its children's value changing. So its `change_value` slot must be connected to any such signal.

```python
def parse(self):
```
This is an abstract method that all `Fidget`s must implement. It processes the internal state of the widget's children, and returns a value (or raises a `ParseError`)

```python
print(w.value())
```
each `Fidget` has a value in store, that can be extracted and used as normal. Note that this value is either a `fidget.core.fidget_value.GoodValue` or a `fidget.core.fidget_value.BadValue`. These can be easily distinguished with the `is_ok()` method.

This is all a lot of work, fidget comes with many default implementations to make usage as effortless as possible:

```python
from fidget.backend.QtWidgets import QHBoxLayout, QApplication
from fidget.widgets import FidgetInt, FidgetTuple

class PointWidget(FidgetTuple):
    INNER_TEMPLATES = [
        FidgetInt.template('x', make_title=False),
        FidgetInt.template('y', make_title=False)
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
One of fidget's most extensive features is its plaintext conversion capability. Each `Fidget` has a set of plaintext printers and plaintext parsers, that can be selected to import/export a `Fidget`'s value. By default, a `Fidget` has no plaintext parsers, and only `str` and `repr` as printers.
### Adding printers and parsers
Printers and parsers can be added either by implementing the `Fidget`'s `plaintext_printers` or `plaintext_parsers` methods, or by creating a method in the class wrapped with `InnerPlaintextPrinter` or `InnerPlaintextParser`.

## Dual API
As seen in the example, almost all of the parameters the `Fidget` can provided upon creation can also have a default value filled in by extending classes.
```python
from fidget.widgets import FidgetCheckBox

w = FidgetCheckBox('title', ('YES', 'NO'), make_title=True)
# the following will create a widget equivalent to w
class MyFidgetCheckBox(FidgetCheckBox):
    MAKE_TITLE=True

w = MyFidgetCheckBox('title', ('YES', 'NO'))
```

## Support Widgets
Fidget comes with many builtin widgets to ease usage. Most usages will not have subclass `Fidget` or implement `parse` at all!

|`Fidget` subclass|description|
|-----------------|-----------|
|`FidgetCheckBox`|a checkbox holding one of two values|
|`FidgetCombo`|a combobox holding one of a number of values|
|`FidgetComplex`|a line edit for a `complex`|
|`FidgetConfirmer`|a fidget wrapper that includes an "OK" button to perform more complex validation|
|`FidgetConverter`|a fidget wrapper that converts an inner value to an outer value|
|`FidgetDict`|a fidget that aggregates multiple fidgets into a `dict`|
|`FidgetEditCombo`|an editable combobox holding one of a number of values or a converted string value|
|`FidgetFloat`|a line edit for a `float`|
|`FidgetFilePath`|a line edit and a browse button to select a file path|
|`FidgetInt`|a line edit for an `int`|
|`FidgetLabel`|a constant-value fidget with a label|
|`FidgetLineEdit`|a line edit holding any single-value string|
|`FidgetOptional`|a fidget wrapper that can disable the inner fidget and provide a default value|
|`FidgetQuestion`|a specialized `FidgetConfirmer` that opens as a dialog|
|`FidgetStacked`|multiple fidgets of the same type, only one of which is usable at any time|
|`FidgetTuple`|a fidget that aggregates multiple fidgets into a `tuple`|

## Compatibility
Fidget can use either PyQt5 and PySide2. By default, it will try to import both wrappers, starting with PySide2, and will use the first it successfully imported. This can be changed with `fidget.backend`'s function: `prefer`.

Users of fidget can also directly use whatever backend fidget is using (thus ensuring compatibility) by importing Qt's members from `fidget.backend` (currently, only imports from `QtWidgets` and `QtCore` are supported in this way)