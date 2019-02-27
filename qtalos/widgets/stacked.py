from __future__ import annotations

from typing import TypeVar, Generic, Iterable, Tuple, Union, Callable

from collections import namedtuple
from functools import wraps

from PyQt5.QtWidgets import QVBoxLayout, QStackedWidget, QComboBox, QFrame

from qtalos import ValueWidget
from qtalos.widgets.idiomatic_inner import get_idiomatic_inner_widgets
from qtalos.widgets.__util__ import has_init

T = TypeVar('T')


class StackedValueWidget(Generic[T], ValueWidget[T]):
    targeted_fill = namedtuple('targeted_fill', 'option_name value')

    def __init__(self, title, options: Iterable[Union[ValueWidget[T], Tuple[str, ValueWidget[T]]]] = None,
                 frame_style=None,
                 **kwargs):
        super().__init__(title, **kwargs)

        if (options is None) == (self.make_options is None):
            if options:
                raise Exception('options provided when make_options is implemented')
            raise Exception('options not provided when make_options is not implemented')

        self.options = dict(self._to_name_subwidget(o) for o in (options or self.make_options()))

        self.selector: QComboBox = None  # todo other selector methods (radio?, checkbox?)
        self.stacked: QStackedWidget = None

        self.init_ui(frame_style)

    make_options: Callable[[StackedValueWidget[T]], Iterable[Union[ValueWidget[T], Tuple[str, ValueWidget[T]]]]] = None

    def init_ui(self, frame_style=None):
        super().init_ui()

        master_layout = QVBoxLayout(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = QVBoxLayout()

        with self.setup_provided(master_layout, layout):
            self.selector = QComboBox()
            self.stacked = QStackedWidget()

            for name, option in self.options.items():
                self.stacked.addWidget(option)
                self.selector.addItem(name)

                option.on_change.connect(self.change_value)

            self.selector.currentIndexChanged.connect(self._selector_changed)
            layout.addWidget(self.selector)
            layout.addWidget(self.stacked)

        frame.setLayout(layout)
        master_layout.addWidget(frame)

    def parse(self):
        return self.current_subwidget().parse()

    def validate(self, v):
        return self.current_subwidget().validate(v)

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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = list(get_idiomatic_inner_widgets(cls))
        if idiomatic_inners:
            if has_init(cls):
                raise Exception('cannot define idiomatic inner classes inside a class with an __init__')

            @wraps(cls.__init__)
            def __init__(self, *args, **kwargs):
                return super(cls, self).__init__(*args, options=(ii() for ii in idiomatic_inners), **kwargs)

            cls.__init__ = __init__


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos import wrap_parser

    from qtalos.widgets import ConvertedEdit, ValueCheckBox, ValueCombo

    app = QApplication([])
    w = StackedValueWidget('number', [
        ConvertedEdit('raw text', convert_func=wrap_parser(ValueError, int)),
        ValueCheckBox('sign', (0, 1)),
        ValueCombo('named', [('dozen', 12), ('one', 1), ('seven', 7)])
    ], make_plaintext_button=True, frame_style=QFrame.Box)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
