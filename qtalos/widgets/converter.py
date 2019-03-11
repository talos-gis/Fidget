from __future__ import annotations

from typing import TypeVar, Generic, Callable, Optional

from functools import wraps
from qtalos.backend.QtWidgets import QHBoxLayout

from qtalos.core import ValueWidget, ParseError, PlaintextParseError, ValueWidgetTemplate

from qtalos.widgets.widget_wrappers import SingleWidgetWrapper
from qtalos.widgets.__util__ import is_trivial_printer, only_valid

T = TypeVar('T')
F = TypeVar('F')


# todo common superclass for this & optional
class ConverterWidget(Generic[F, T], SingleWidgetWrapper[F, T]):
    def __init__(self, inner_template: ValueWidgetTemplate[F] = None,
                 converter_func: Callable[[F], T] = None,
                 back_converter_func: Optional[Callable[[T], F]] = None,
                 **kwargs):

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        template_args = {}

        for key in ('make_plaintext', 'make_indicator', 'make_title', 'make_auto'):
            if key in kwargs:
                template_args[key] = kwargs[key]
            kwargs[key] = False
        inner_template = inner_template.template(**template_args)

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template
        self.inner: ValueWidget[F] = None
        self.converter_func = converter_func
        self.back_converter_func = back_converter_func

        self.init_ui()

    INNER_TEMPLATE: ValueWidgetTemplate[F] = None

    def init_ui(self):
        super().init_ui()
        layout = QHBoxLayout(self)

        self.inner = self.inner_template()
        layout.addWidget(self.inner)
        self.setMinimumSize(self.inner.minimumSize())
        self.setMaximumSize(self.inner.maximumSize())

        if self.inner.title_label:
            self.make_title = True

        if self.inner.auto_button:
            self.inner.auto_button.clicked.disconnect(self.inner._auto_btn_click)
            self.inner.auto_button.clicked.connect(self._auto_btn_click)
            self.make_auto = True

        if self.inner.plaintext_button:
            self.inner.plaintext_button.clicked.disconnect(self.inner._plaintext_btn_click)
            self.inner.plaintext_button.clicked.connect(self._plaintext_btn_click)
            self._plaintext_widget = self.inner._plaintext_widget
            self.make_plaintext = True

        if self.inner.indicator_label:
            self.inner.indicator_label.mousePressEvent = self._detail_button_clicked
            self.indicator_label = self.inner.indicator_label
            self.make_indicator = True

        self.inner.on_change.connect(self.change_value)

    def provided_pre(self, *args, **kwargs):
        return self.inner.provided_pre(*args, **kwargs)

    def provided_post(self, *args, **kwargs):
        return self.inner.provided_post(*args, **kwargs)

    def parse(self):
        f = self.inner.parse()
        return self.convert(f)

    def validate(self, value: T):
        if self.back_convert:
            self.inner.validate(self.back_convert(value))
        super().validate(value)

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

    def template_of(self):
        ret = super().template_of()
        template_args = {}
        for key in ('make_plaintext', 'make_indicator', 'make_title', 'make_auto'):
            if key in self.inner_template.kwargs:
                template_args[key] = self.inner_template.kwargs[key]
        return ret.template(**template_args)


@ConverterWidget.template_class
class ConverterWidgetTemplate(Generic[T], ValueWidgetTemplate[T]):
    @property
    def title(self):
        it = self._inner_template()
        if it:
            return it.title
        return super().title

    def _inner_template(self):
        if self.widget_cls.INNER_TEMPLATE:
            return self.widget_cls.INNER_TEMPLATE
        if self.args:
            return self.args[0].template_of()
        return None


if __name__ == '__main__':
    from qtalos.backend import QApplication
    from qtalos import wrap_parser
    from qtalos.widgets import LineEdit, OptionalValueWidget

    app = QApplication([])
    w = ConverterWidget(LineEdit('sample', pattern='(1[^1]*1|[^1])*', make_plaintext=True),
                        converter_func=wrap_parser(ValueError, int),
                        back_converter_func=str, make_indicator=True)
    w = OptionalValueWidget(w, make_title=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
