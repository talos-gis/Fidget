from typing import TypeVar, Generic

from fidget.core import format_printer, regex_parser, PlaintextParseError, wrap_plaintext_parser, Fidget, \
    TemplateLike, inner_plaintext_parser, ParseError

from fidget.widgets.line import FidgetLine
from fidget.widgets.text import FidgetPlainText
from fidget.widgets.converter import FidgetConverter
from fidget.widgets.__util__ import parse_int

T = TypeVar('T')


class SimpleLineEdit(Generic[T], FidgetConverter[str, T]):
    """
    A superclass for processing a single line edit. using the plaintext parsers to convert the value
    """

    MAKE_PLAINTEXT = MAKE_INDICATOR = False

    def __init__(self, title, **kwargs):
        line_edit_args = {}

        for k in ('placeholder',):
            if k in kwargs:
                line_edit_args[k] = kwargs[k]
                del kwargs[k]

        super().__init__(self.line_edit_cls.template(title, **line_edit_args), **kwargs)

    def back_convert(self, v: T):
        printer = self.joined_plaintext_printer
        ret = printer(v)
        return ret

    def convert(self, v: str) -> T:
        parser = self.joined_plaintext_parser
        try:
            return parser(v)
        except PlaintextParseError as e:
            raise ParseError(offender=self.inner) from e

    line_edit_cls: TemplateLike[str] = FidgetLine.template()

    _template_class = Fidget._template_class

    def plaintext_parsers(self):
        return Fidget.plaintext_parsers(self)


class SimplePlainEdit(Generic[T], FidgetConverter[str, T]):
    """
    A superclass for processing a plaintext edit. using the plaintext parsers to convert the value
    """

    MAKE_PLAINTEXT = MAKE_INDICATOR = False

    def __init__(self, title, **kwargs):
        line_edit_args = {}

        for k in ('placeholder',):
            if k in kwargs:
                line_edit_args[k] = kwargs[k]
                del kwargs[k]

        super().__init__(self.line_edit_cls.template(title, **line_edit_args), **kwargs)

    def back_convert(self, v: T):
        printer = self.joined_plaintext_printer
        return printer(v)

    def convert(self, v: str) -> T:
        parser = self.joined_plaintext_parser
        try:
            return parser(v)
        except PlaintextParseError as e:
            raise ParseError(offender=self.inner) from e

    line_edit_cls: TemplateLike[str] = FidgetPlainText.template()

    _template_class = Fidget._template_class

    def plaintext_parsers(self):
        return Fidget.plaintext_parsers(self)


class FidgetInt(SimpleLineEdit[int]):
    """
    A line edit that converts the value to int
    """
    _func = inner_plaintext_parser(staticmethod(wrap_plaintext_parser(ValueError, parse_int)))
    _cls_printers = [
        format_printer('n'),
        format_printer(','),
        format_printer('_b'),
        format_printer('_X')
    ]

    @classmethod
    def cls_plaintext_printers(cls):
        yield from super().cls_plaintext_printers()
        yield hex
        yield bin
        yield oct
        yield from cls._cls_printers


class FidgetFloat(SimpleLineEdit[float]):
    """
    A line edit that converts the value to float
    """
    _func = inner_plaintext_parser(staticmethod(wrap_plaintext_parser(ValueError, float)))
    _cls_printers = [
        format_printer('f'),
        format_printer('e'),
        format_printer('g'),
        format_printer('%'),
    ]

    @inner_plaintext_parser
    @staticmethod
    @regex_parser(r'([0-9]*(\.[0-9]+)?)%')
    def percentage(m):
        try:
            return float(m[1]) / 100
        except ValueError as e:
            raise PlaintextParseError() from e

    @inner_plaintext_parser
    @staticmethod
    @regex_parser(r'(?P<num>[0-9]+)\s*/\s*(?P<den>[0-9]*[1-9][0-9]*)')
    def ratio(m):
        n = m['num']
        d = m['den']

        try:
            n = float(n)
            d = float(d)
        except ValueError as e:
            raise PlaintextParseError() from e

        try:
            return n / d
        except ValueError as e:
            raise PlaintextParseError() from e

    @classmethod
    def cls_plaintext_printers(cls):
        yield from super().cls_plaintext_printers()
        yield from cls._cls_printers


class FidgetComplex(SimpleLineEdit[complex]):
    """
    A line edit that converts the value to complex
    """
    _func = inner_plaintext_parser(staticmethod(wrap_plaintext_parser(ValueError, complex)))


def template(*args, **kwargs):
    """
    a decorator to convert a class to a parameterized template
    """

    def ret(c: TemplateLike[T]) -> TemplateLike[T]:
        return c.template(*args, **kwargs)

    return ret


if __name__ == '__main__':
    from fidget.backend.QtWidgets import QApplication

    app = QApplication([])
    w = FidgetInt('sample', make_plaintext=True, make_indicator=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
