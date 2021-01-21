from typing import TypeVar, Union, Pattern, Callable, Any, Match, Iterable, Tuple, Type, Dict, List

import re
import json
from functools import wraps, lru_cache, partial
from textwrap import indent
from enum import IntEnum

from fidget.backend.QtWidgets import QDialog, QApplication

from fidget.core.primitive_questions import FormatSpecQuestion, FormattedStringQuestion, ExecStringQuestion, \
    EvalStringQuestion
from fidget.core.__util__ import exc_wrap, update

T = TypeVar('T')

PlaintextPrinter = Callable[[T], str]
PlaintextParser = Callable[[str], T]


class PlaintextParseError(Exception):
    """
    An exception for when a parser failed to parse a plaintext
    """

    def __init__(self, *args, cursor_pos=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_pos = cursor_pos


class PlaintextPrintError(Exception):
    """
    An exception for when a parser failed to print an object
    """
    pass


def regex_parser(*patterns: Union[Pattern[str], str]) \
        -> Callable[[Callable[[Match[str]], Any]], PlaintextParser]:
    """
    A wrapper for a function that accepts a regex match object. The function will accept only a plaintext that fully
     matches one of the regular expression pattern, and forward that match to the function.
    :param patterns: the patterns to match against.
    """
    patterns = [
        (re.compile(p) if isinstance(p, str) else p) for p in patterns
    ]

    def ret(func):
        @wraps(func)
        def ret(s: str):
            for p in patterns:
                m = p.fullmatch(s)
                if m:
                    return func(m)
            raise PlaintextParseError('string did not match pattern')

        return ret

    return ret


def json_parser(acceptable_type: Union[Type, Tuple[Type, ...]] = object):
    """
    A wrapper for a function that accepts an object. The function will accept only a plaintext that parses as JSON, and
     forwards that object to the function.
    :param acceptable_type: The wrapper will only accept objects of this type(s)
    """

    def ret(func):
        return JsonParser(func, acceptable_type)

    return ret


def json_printer(func):
    @wraps(func)
    def ret(*args, **kwargs):
        return json.dumps(func(*args, **kwargs))

    return ret


class JsonParser:
    def __init__(self, inner_func, acceptable_type):
        self.__func__ = inner_func
        self.__name__ = inner_func.__name__
        self.acceptable_type = acceptable_type

    def __get__(self, instance, owner):
        func = self.__func__.__get__(instance, owner)

        @wraps(func)
        def ret(s: str, *args, **kwargs):
            try:
                json_obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise PlaintextParseError(cursor_pos=e.pos) from e
            else:
                if not isinstance(json_obj, self.acceptable_type):
                    raise PlaintextParseError(
                        f'object is not of an acceptable type (expected {self.acceptable_type}, got {type(json_obj)})')
                return func(json_obj, *args, **kwargs)

        return ret

    def __call__(self, *args, **kwargs):
        return self.__func__.__get__(*args, **kwargs)


def join_parsers(parsers: Callable[[], Iterable[PlaintextParser]]):
    """
    joins parsers together, returning the first value that is processed without errors. skips explicit parsers.
    :param parsers: a callable to generate parsers.
    """

    def ret(s):
        seen = set()
        first_error = None
        for p, prio in sort_adapters(parsers()):
            if p in seen:
                continue
            if prio < 0:
                break

            seen.add(p)

            try:
                return p(s)
            except PlaintextParseError as e:
                first_error = first_error or e
        raise first_error or PlaintextParseError('no parsers')

    ret.__name__ = '<all>'
    return ret


def join_printers(printers: Callable[[], Iterable[PlaintextPrinter]]):
    """
    joins printers together, returning the first value that is processed without errors. skips explicit printers.
    :param printers: a callable to generate parsers.
    """

    def ret(s):
        seen = set()
        first_error = None
        for p, prio in sort_adapters(printers()):
            if p in seen:
                continue
            if prio < 0:
                break
            seen.add(p)

            try:
                ret = p(s)
            except PlaintextPrintError as e:
                first_error = first_error or e
            else:
                return ret
        raise first_error or PlaintextPrintError('no printers')

    ret.__name__ = '<all>'
    return ret


def inner_plaintext_parser(func):
    """
    mark a method as plaintext parser
    """
    func.__plaintext_parser__ = True
    return func


def inner_plaintext_printer(func):
    """
    mark a method as plaintext printer
    """
    func.__plaintext_printer__ = True
    return func


wrap_plaintext_parser = exc_wrap(PlaintextParseError)

wrap_plaintext_printer = exc_wrap(PlaintextPrintError)


def format_printer(format_spec):
    """
    A printer that prints with specific format spec
    :param format_spec: the format specifications to print under.
    :return: a plaintext printer
    """

    @wraps(str)
    def ret(v):
        return format(v, format_spec)

    ret.__name__ = f'format({format_spec})'
    return ret


def formatted_string_printer(formatted_string):
    @wraps(str)
    def ret(v):
        return formatted_string.format(v)

    ret.__name__ = f'{formatted_string!r}.format'
    return ret


class AdapterPriority(IntEnum):
    explicit = -1  # never even run implicitly
    low = 0
    mid = 1
    high = 2
    default = mid


explicit = update(__explicit__=AdapterPriority.explicit)
low_priority = update(__priority__=AdapterPriority.low)
high_priority = update(__priority__=AdapterPriority.high)
mid_priority = update(__priority__=AdapterPriority.mid)


def sort_adapters(it: Iterable[T]):
    """
    sort between explicit and non-explicit elements, returning the explicit elements last, with an indicator,
     and avoiding duplicate elements
    """
    deffered: Dict[AdapterPriority, List[T]] = {}
    seen = set()

    for i in it:
        if i in seen:
            continue
        else:
            seen.add(i)

        if hasattr(i, '__priority__'):
            priority = i.__priority__
        elif getattr(i, '__explicit__', False):
            priority = AdapterPriority.explicit
        else:
            priority = AdapterPriority.default

        deffered.setdefault(priority, []).append(i)

    del seen
    for priority in sorted(deffered.keys(), reverse=True):
        for i in deffered[priority]:
            yield i, priority


@explicit
def format_spec_input_printer(v):
    instance = FormatSpecQuestion.instance()

    result = instance.exec_()
    if result == QDialog.Rejected:
        raise PlaintextPrintError("format spec cancelled")
    format_spec = instance.ret

    try:
        return format(v, format_spec)
    except ValueError as e:
        raise PlaintextPrintError from e


format_spec_input_printer.__name__ = 'format(...)'


@explicit
def formatted_string_input_printer(v):
    instance = FormattedStringQuestion.instance()

    if instance.exec_() == QDialog.Rejected:
        raise PlaintextPrintError("formatted string cancelled")
    formatted_string = instance.ret

    try:
        return formatted_string.format(v)
    except (ValueError, AttributeError, LookupError) as e:
        raise PlaintextPrintError from e


formatted_string_input_printer.__name__ = 'formatted_string(...)'


@explicit
def exec_printer(v):
    instance = ExecStringQuestion.instance()
    if instance.exec_() == QDialog.Rejected:
        raise PlaintextPrintError('exec cancelled')
    script = instance.ret
    script = """def main(value):\n""" + indent(script, '\t')
    try:
        globs = {}
        exec(script, globs)
    except Exception as e:
        raise PlaintextPrintError from e

    if 'main' not in globs:
        raise PlaintextParseError('main function not found') from KeyError('main')

    try:
        ret = globs['main'](v)
    except Exception as e:
        raise PlaintextPrintError from e

    return str(ret)


exec_printer.__name__ = "exec"


@explicit
def eval_printer(v):
    instance = EvalStringQuestion.instance()
    if instance.exec_() == QDialog.Rejected:
        raise PlaintextPrintError('eval cancelled')
    script = instance.ret

    try:
        ret = eval(script, {'value': v})
    except Exception as e:
        raise PlaintextPrintError from e

    return str(ret)


eval_printer.__name__ = "eval"
