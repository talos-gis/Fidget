from typing import TypeVar, Union, Pattern, Callable, Any, Match, Iterable, Tuple, Type

import re
import json
from functools import wraps, update_wrapper

from fidget.core.__util__ import exc_wrap

T = TypeVar('T')

PlaintextPrinter = Callable[[T], str]
PlaintextParser = Callable[[str], T]


# todo cursor position for parse errors?


class PlaintextParseError(Exception):
    """
    An exception for when a parser failed to parse a plaintext
    """
    pass


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
        @wraps(func)
        def ret(s: str, *args, **kwargs):
            try:
                json_obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise PlaintextParseError() from e
            else:
                if not isinstance(json_obj, acceptable_type):
                    raise PlaintextParseError(
                        f'object is not of an acceptable type (expected {acceptable_type}, got {type(json_obj)})')
                return func(json_obj, *args, **kwargs)

        return ret

    return ret


def join_parsers(parsers: Callable[[], Iterable[PlaintextParser]]):
    """
    joins parsers together, returning the first value that is processed without errors. skips explicit parsers.
    :param parsers: a callable to generate parsers.
    """

    def ret(s):
        first_error = None
        for p in parsers():
            if getattr(p, '__explicit__', False):
                continue

            try:
                return p(s)
            except PlaintextParseError as e:
                first_error = first_error or e
            except Exception as e:
                raise AssertionError('plaintext parser raised') from e
        raise first_error or PlaintextParseError('no parsers')

    ret.__name__ = '<all>'
    return ret


def join_printers(printers: Callable[[], Iterable[PlaintextPrinter]]):
    """
    joins printers together, returning the first value that is processed without errors. skips explicit printers.
    :param printers: a callable to generate parsers.
    """

    def ret(s):
        first_error = None
        for p in printers():
            if getattr(p, '__explicit__', False):
                continue

            try:
                return p(s)
            except PlaintextPrintError as e:
                first_error = first_error or e
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


def explicit(func):
    """
    mark a function as explicit, and return it
    """

    func.__explicit__ = True
    return func
