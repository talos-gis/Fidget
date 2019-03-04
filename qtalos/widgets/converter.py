from __future__ import annotations

from typing import TypeVar, Generic, Callable, Optional

from functools import wraps
from PyQt5.QtWidgets import QHBoxLayout

from qtalos import ValueWidget, ParseError, PlaintextParseError
from qtalos.widgets.idiomatic_inner import get_idiomatic_inner_widgets
from qtalos.widgets.__util__ import has_init, is_trivial_printer

T = TypeVar('T')
F = TypeVar('F')


class ConverterWidget(Generic[F, T], ValueWidget[T]):
    def __init__(self, inner: ValueWidget[F] = None,
                 converter_func: Callable[[F], T] = None,
                 back_converter_func: Optional[Callable[[T], F]] = None,
                 **kwargs):
        if (inner is None) == (self.make_inner is None):
            if inner:
                raise Exception('inner provided when make_inner is implemented')
            raise Exception('inner not provided when make_inner is not implemented')

        inner = inner or self.make_inner()

        super().__init__(inner.title, make_plaintext_button=False, make_validator_label=False, make_title_label=False,
                         make_auto_button=False, **kwargs)

        self.inner = inner
        self.converter_func = converter_func
        self.back_converter_func = back_converter_func

        self.init_ui()

    make_inner: Callable[[ConverterWidget[T]], ValueWidget[T]] = None

    def init_ui(self):
        super().init_ui()
        layout = QHBoxLayout(self)
        layout.addWidget(self.inner)
        self.setMinimumSize(self.inner.minimumSize())
        self.setMaximumSize(self.inner.maximumSize())

        if self.inner.title_label:
            self.make_title_label = True

        if self.inner.auto_button:
            self.inner.auto_button.clicked.disconnect(self.inner._auto_btn_click)
            self.inner.auto_button.clicked.connect(self._auto_btn_click)
            self.make_auto_button = True

        if self.inner.plaintext_button:
            self.inner.plaintext_button.clicked.disconnect(self.inner._plaintext_btn_click)
            self.inner.plaintext_button.clicked.connect(self._plaintext_btn_click)
            self._plaintext_widget = self.inner._plaintext_widget
            self.make_plaintext_button = True

        if self.inner.validation_label:
            self.inner.validation_label.mousePressEvent = self._detail_button_clicked
            self.validation_label = self.inner.validation_label
            self.make_validator_label = True

        self.inner.on_change.connect(self.change_value)

    def provided_pre(self, *args, **kwargs):
        return self.inner.provided_pre(*args, **kwargs)

    def provided_post(self, *args, **kwargs):
        return self.inner.provided_post(*args, **kwargs)

    def parse(self):
        f = self.inner.parse()
        return self.convert(f)

    def convert(self, v: F) -> T:
        if not self.converter_func:
            raise Exception('a converter function must be provided')
        return self.converter_func(v)

    @property
    def back_convert(self):
        return self.back_converter_func

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        for parser in self.inner.plaintext_parsers():
            @wraps(parser)
            def p(*args, **kwargs):
                f = parser(*args, **kwargs)
                try:
                    return self.convert(f)
                except ParseError as e:
                    raise PlaintextParseError(...) from e

            yield p

    def plaintext_printers(self):
        if self.back_convert:
            yield from super().plaintext_printers()
            for printer in self.inner.plaintext_printers():
                if is_trivial_printer(printer):
                    continue

                @wraps(printer)
                def p(*args, **kwargs):
                    f = self.back_convert(*args, **kwargs)
                    return printer(f)

                yield p
        else:
            yield from super().plaintext_printers()

    def _fill(self, v: T):
        f = self.back_convert(v)
        # todo if the back_converter fails, just fill the initial value
        self.inner.fill(f)

    @property
    def fill(self):
        return (self.inner.fill and self.back_convert) and self._fill

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = list(get_idiomatic_inner_widgets(cls))
        if idiomatic_inners:
            if has_init(cls):
                raise Exception('cannot define idiomatic inner classes inside a class with an __init__')

            if len(idiomatic_inners) != 1:
                raise Exception('ConverterWidget can only have 1 idiomatic inner class')

            inner_cls, = idiomatic_inners

            @wraps(cls.__init__)
            def __init__(self, *args, **kwargs):
                return super(cls, self).__init__(inner_cls(*args, **kwargs))

            cls.__init__ = __init__


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos import wrap_parser
    from qtalos.widgets import LineEdit

    app = QApplication([])
    w = ConverterWidget(LineEdit('sample', pattern='(a[^a]*a|[^a])*', make_plaintext_button=True),
                        converter_func=wrap_parser(ValueError, int),
                        back_converter_func=str)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
