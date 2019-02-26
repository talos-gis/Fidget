from typing import TypeVar, Generic, Tuple, Union, Mapping

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout

from qtalos import ValueWidget

T = TypeVar('T')


class ValueCheckBox(Generic[T], ValueWidget[T]):
    NO_DEFAULT_VALUE = object()

    def __init__(self, title, value_selector: Union[Tuple[T, T], Mapping[bool, T]] = (False, True),
                 initial: bool = False, **kwargs):
        kwargs.setdefault('make_validator_label', False)
        super().__init__(title, **kwargs)

        self.value_selector = value_selector
        self.checkbox: QCheckBox = None

        self.init_ui()
        self.checkbox.setChecked(initial)

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.checkbox = QCheckBox()
            self.checkbox.toggled.connect(self.change_value)
            layout.addWidget(self.checkbox)

    @property
    def true_val(self):
        return self.value_selector[True]

    @property
    def false_val(self):
        return self.value_selector[False]

    def parse(self):
        return self.value_selector[self.checkbox.isChecked()]

    def fill(self, key: Union[T, bool]):
        if key == self.true_val:
            v = True
        elif key == self.false_val:
            v = False
        elif isinstance(key, bool):
            v = key
        else:
            raise ValueError('value is not a valid fill value')

        self.checkbox.setChecked(v)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from enum import Enum, auto


    class Options(Enum):
        first = auto()
        second = auto()
        third = auto()


    app = QApplication([])
    w = ValueCheckBox('sample', ('NO', 'YES'))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
