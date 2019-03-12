from typing import TypeVar, Generic

from functools import partial

from fidget.backend.QtCore import Qt

from fidget.core import format_printer, regex_parser, PlaintextParseError, wrap_plaintext_parser, Fidget, \
    TemplateLike, inner_plaintext_parser, ParseError, explicit, PlaintextPrintError

from fidget.widgets.line import FidgetLineEdit
from fidget.widgets.converter import FidgetConverter
from fidget.widgets.confirmer import FidgetQuestion
from fidget.widgets.__util__ import link_to

T = TypeVar('T')

# todo shortcut to the python format spec mini-language
format_spec_question_template = FidgetQuestion.template(
    FidgetLineEdit.template('format specification'),
    window_modality=Qt.ApplicationModal, cancel_value=None,
    post_widget=partial(link_to, 'python format mini-language specifications',
                        r'https://docs.python.org/3/library/string.html#format-specification-mini-language')
)


@explicit
def format_input(v):
    format_spec = format_spec_question_template.instance().exec_()
    if not format_spec.is_ok():
        raise PlaintextPrintError from format_spec.exception
    format_spec: str = format_spec.value
    if format_spec is None:
        raise PlaintextPrintError('format_spec not provided')

    try:
        return format(v, format_spec)
    except ValueError as e:
        raise PlaintextPrintError from e


formatted_string_question_template = FidgetQuestion.template(
    FidgetLineEdit.template('format specification'),
    window_modality=Qt.ApplicationModal, cancel_value=None,
    post_widget=partial(link_to, 'python formatted string specifications',
                        r'https://docs.python.org/3/library/string.html#format-string-syntax')
)


@explicit
def formatted_string(v):
    formatted_string_value = formatted_string_question_template.instance().exec_()
    if not formatted_string_value.is_ok():
        raise PlaintextPrintError from formatted_string_value.exception
    formatted_string_value: str = formatted_string_value.value
    if formatted_string_value is None:
        raise PlaintextPrintError('formatted string not provided')

    try:
        return formatted_string_value.format(v)
    except (ValueError, AttributeError, LookupError) as e:
        raise PlaintextPrintError from e


class SimpleEdit(Generic[T], FidgetConverter[str, T]):
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
        return printer(v)

    def convert(self, v: str) -> T:
        parser = self.joined_plaintext_parser
        try:
            return parser(v)
        except PlaintextParseError as e:
            raise ParseError(offender=self.inner) from e

    line_edit_cls: TemplateLike[str] = FidgetLineEdit.template()

    _template_class = Fidget._template_class

    def plaintext_parsers(self):
        return Fidget.plaintext_parsers(self)

    # todo these should really be standard (somehow...)
    def plaintext_printers(self):
        yield from super().plaintext_printers()
        yield format_input
        yield formatted_string


class FidgetInt(SimpleEdit[int]):
    """
    A line edit that converts the value to int
    """
    _func = inner_plaintext_parser(staticmethod(wrap_plaintext_parser(ValueError, partial(int, base=0))))

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        yield hex
        yield bin
        yield oct
        yield format_printer('n')
        yield format_printer(',')
        yield format_printer('_b')
        yield format_printer('_X')


class FidgetFloat(SimpleEdit[float]):
    """
    A line edit that converts the value to float
    """
    _func = inner_plaintext_parser(staticmethod(wrap_plaintext_parser(ValueError, float)))

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
    @regex_parser(r'(?P<num>[0-9]+)\s*/\s*(?P<den>[1-9][0-9]*)')
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

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        yield format_printer('f')
        yield format_printer('e')
        yield format_printer('g')
        yield format_printer('%')


class FidgetComplex(SimpleEdit[complex]):
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
