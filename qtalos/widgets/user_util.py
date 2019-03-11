from typing import Callable, TypeVar, Generic

from functools import partial

from qtalos.core import format_printer, regex_parser, PlaintextParseError, wrap_parser, ValueWidget

from qtalos.widgets.line import LineEdit
from qtalos.widgets.converter import ConverterWidget

T = TypeVar('T')


class SimpleEdit(Generic[T], ConverterWidget[str, T]):
    MAKE_PLAINTEXT = False
    converter_func: Callable[[str], T]

    def __init__(self, title, **kwargs):
        line_edit_args = {'make_indicator': False}

        for k in ('make_title', 'make_plaintext', 'make_auto', 'make_indicator',
                  'pattern', 'convert', 'back_convert', 'placeholder'):
            if k in kwargs:
                line_edit_args[k] = kwargs[k]
                del kwargs[k]

        super().__init__(LineEdit(title, **line_edit_args), converter_func=type(self).converter_func, **kwargs)

    def back_convert(self, v: T):
        return str(v)

    _template_class = ValueWidget._template_class

    def template_of(self):
        return ValueWidget.template_of(self)


class IntEdit(SimpleEdit[int]):
    converter_func = wrap_parser(ValueError, partial(int, base=0))

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        yield hex
        yield bin
        yield oct
        yield format_printer('n')
        yield format_printer('X')


class FloatEdit(SimpleEdit[float]):
    converter_func = wrap_parser(ValueError, float)

    @staticmethod
    @regex_parser(r'([0-9]*(\.[0-9]+)?)%')
    def percentage(m):
        try:
            return float(m[0])
        except ValueError as e:
            raise PlaintextParseError(...) from e

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        yield format_printer('f')
        yield format_printer('e')
        yield format_printer('g')
        yield format_printer('%')

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield self.percentage


class ComplexEdit(SimpleEdit[complex]):
    converter_func = wrap_parser(ValueError, complex)


if __name__ == '__main__':
    from qtalos.backend import QApplication

    app = QApplication([])
    w = IntEdit('sample', make_plaintext=True, make_indicator=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
