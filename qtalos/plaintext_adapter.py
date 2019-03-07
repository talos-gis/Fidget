from typing import TypeVar, Union, Pattern, Callable, Any, Match, Iterable, Tuple, Type

import re
import json
from functools import wraps, update_wrapper

from qtalos.__util__ import exc_wrap

T = TypeVar('T')

PlaintextPrinter = Callable[[T], str]
PlaintextParser = Callable[[str], T]


class PlaintextParseError(Exception):
    pass


class PlaintextPrintError(Exception):
    pass


def regex_parser(*patterns: Union[Pattern[str], str], name=...) \
        -> Callable[[Callable[[Match[str]], Any]], PlaintextParser]:
    patterns = [re.compile(p) for p in patterns]

    def ret(func):
        @wraps(func)
        def ret(s: str):
            for p in patterns:
                m = p.fullmatch(s)
                if m:
                    return func(m)
            raise PlaintextParseError('string did not match pattern')

        if name is not ...:
            ret.__name__ = name

        return ret

    return ret


def json_parser(acceptable_types=(str, dict, list, int, float)):
    def ret(func):
        @wraps(func)
        def ret(s: str):
            try:
                json_obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise PlaintextParseError(...) from e
            else:
                if not isinstance(json_obj, acceptable_types):
                    raise PlaintextParseError(
                        f'object is not of an acceptable type (expected {acceptable_types}, got {type(json_obj)})')
                return func(json_obj)

        return ret

    return ret


def join_parsers(parsers: Callable[[], Iterable[PlaintextParser]]):
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


def none_parser(s: str):
    if s.lower() == 'none':
        return None
    raise PlaintextParseError('this parser only accepts "None"')


class InnerPlaintextParser:
    def __init__(self, func):
        self.__func__ = func
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)

    @property
    def __explicit__(self):
        return self.__func__.__explicit__

    @__explicit__.setter
    def __explicit__(self, v):
        self.__func__.__explicit__ = v

    def __get__(self, instance, owner):
        return self.__func__.__get__(instance, owner)


class InnerPlaintextPrinter:
    def __init__(self, func):
        self.__func__ = func
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)

    @property
    def __explicit__(self):
        return self.__func__.__explicit__

    @__explicit__.setter
    def __explicit__(self, v):
        self.__func__.__explicit__ = v

    def __get__(self, instance, owner):
        return self.__func__.__get__(instance, owner)


wrap_plaintext_parser = exc_wrap(PlaintextParseError)
wrap_plaintext_printer = exc_wrap(PlaintextPrintError)


def format_printer(format_spec):
    @wraps(str)
    def ret(v):
        return format(v, format_spec)

    ret.__name__ = f'format({format_spec})'
    return ret


def explicit(func):
    func.__explicit__ = True
    return func
