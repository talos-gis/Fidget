from typing import TypeVar, Generic, Iterable, Tuple, Union

from itertools import chain
from collections import namedtuple
from functools import wraps

from PyQt5.QtWidgets import QVBoxLayout, QStackedWidget, QComboBox

from qtalos import ValueWidget
from qtalos.widgets.__util__ import rename

T = TypeVar('T')


class StackedValueWidget(Generic[T], ValueWidget[T]):
    targeted_fill = namedtuple('targeted_fill', 'option_name value')

    def __init__(self, title, options: Iterable[Union[ValueWidget[T], Tuple[str, ValueWidget[T]]]], **kwargs):
        super().__init__(title, **kwargs)
        self.options = dict(self._to_name_subwidget(o) for o in options)

        self.selector: QComboBox = None  # todo other selector methods (radio?, checkbox?)
        self.stacked: QStackedWidget = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()

        layout = QVBoxLayout(self)

        with self.setup_provided(layout):
            self.selector = QComboBox()
            self.stacked = QStackedWidget()

            for name, option in self.options.items():
                for p in chain(option.provided_pre(),
                               option.provided_post()):
                    p.hide()
                self.stacked.addWidget(option)
                self.selector.addItem(name)

                option.on_change.connect(self.change_value)

            self.selector.currentIndexChanged.connect(self._selector_changed)
            layout.addWidget(self.selector)
            layout.addWidget(self.stacked)

    def parse(self):
        return self.current_subwidget().parse()

    def plaintext_printers(self):
        return self.current_subwidget().plaintext_printers()

    def plaintext_parsers(self):
        current = self.current_subwidget()
        yield from current.plaintext_parsers()
        for n, o in self.options.items():
            if o is current:
                continue
            for p in o.plaintext_parsers():
                @wraps(p)
                def new_parser(*args, **kwargs):
                    return self.targeted_fill(option_name=n, value=p(*args, **kwargs))

                new_parser.__name__ = n + ': ' + p.__name__
                yield new_parser

    def current_subwidget(self) -> ValueWidget[T]:
        v: ValueWidget[T] = self.stacked.currentWidget()
        return v

    def fill(self, v: Union[T, targeted_fill]):
        if isinstance(v, self.targeted_fill):
            name = v.option_name
            v = v.value
            self.selector.setCurrentText(name)
        self.current_subwidget().fill(v)

    @staticmethod
    def _to_name_subwidget(option: Union[ValueWidget[T], Tuple[str, ValueWidget[T]]]) -> Tuple[str, ValueWidget[T]]:
        if isinstance(option, ValueWidget):
            return option.title, option
        return option

    def _selector_changed(self, new_index):
        self.stacked.setCurrentIndex(new_index)
        self.change_value()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos import wrap_parser

    from qtalos.widgets import ConvertedEdit, ValueCheckBox, ValueCombo

    app = QApplication([])
    w = StackedValueWidget('number', [
        ConvertedEdit('raw text', convert_func=wrap_parser(ValueError, int)),
        ValueCheckBox('sign', (0, 1)),
        ValueCombo('named', [('dozen', 12), ('one', 1), ('seven', 7)])
    ], make_plaintext_button=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
