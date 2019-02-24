from typing import TypeVar, Union, Pattern, Callable, Any, Match, Iterable

import re
import json
from functools import wraps, update_wrapper

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

        return ret

    return ret


def json_parser(acceptable_types=(str, dict, list, int, float)):
    def ret(func):
        @wraps(func)
        def ret(s: str):
            try:
                json_obj = json.loads(s)
            except json.JSONDecodeError as e:
                raise PlaintextParseError('could not parse json') from e
            else:
                if not isinstance(json_obj, acceptable_types):
                    raise PlaintextParseError('object is not of an acceptable type')
                return func(json_obj)

        return ret

    return ret


def join_parsers(parsers: Callable[[], Iterable[PlaintextParser]]):
    def ret(s):
        first_error = None
        for p in parsers():
            try:
                return p(s)
            except PlaintextParseError as e:
                first_error = first_error or e
        raise first_error or PlaintextParseError('no parsers')

    ret.__name__ = '<all>'
    return ret


def join_printers(printers: Callable[[], Iterable[PlaintextPrinter]]):
    def ret(s):
        first_error = None
        for p in printers():
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

    def __get__(self, instance, owner):
        return self.__func__.__get__(instance, owner)


class InnerPlaintextPrinter:
    def __init__(self, func):
        self.__func__ = func
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)

    def __get__(self, instance, owner):
        return self.__func__