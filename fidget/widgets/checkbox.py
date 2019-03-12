from typing import TypeVar, Generic, Tuple, Union, Mapping

from fidget.backend.QtWidgets import QCheckBox, QHBoxLayout

from fidget.core import ValueWidget, inner_plaintext_parser, PlaintextPrintError, PlaintextParseError

T = TypeVar('T')


class ValueCheckBox(Generic[T], ValueWidget[T]):
    """
    A checkbox that can contain one of two values
    """
    MAKE_INDICATOR = False
    MAKE_TITLE = False
    MAKE_PLAINTEXT = False
    TITLE_AS_TEXT = True

    def __init__(self, title, value_selector: Union[Tuple[T, T], Mapping[bool, T]] = (False, True),
                 initial: bool = False, **kwargs):
        """
        :param title: the title
        :param value_selector: a mapping from bool to the desired value
        :param initial: the initial boolean value
        :param kwargs: forwarded to ValueWidget
        """
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

    @inner_plaintext_parser
    def from_values(self, text):
        for printer in self.plaintext_printers():
            try:
                true_text = printer(self.true_val)
            except PlaintextPrintError:
                pass
            else:
                if true_text == text:
                    return self.true_val

            try:
                true_text = printer(self.false_val)
            except PlaintextPrintError:
                pass
            else:
                if true_text == text:
                    return self.false_val
        raise PlaintextParseError('text did not match any printed value')


if __name__ == '__main__':
    from fidget.backend.QtWidgets import QApplication
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
