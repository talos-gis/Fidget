from typing import TypeVar, Generic, Union, Pattern, Callable, Any, Match

from abc import abstractmethod
from functools import update_wrapper
import re

T = TypeVar('T')


class PlaintextPrinter(Generic[T]):
    name: str

    @abstractmethod
    def to_string(self, value: T) -> str:
        raise PlaintextPrintError('cannot print value')


class PlaintextParser(Generic[T]):
    name: str

    @abstractmethod
    def from_string(self, value: str) -> T:
        raise PlaintextParseError('cannot parse string')


class PlaintextParseError(Exception):
    pass


class PlaintextPrintError(Exception):
    pass


class FuncPrinter(PlaintextPrinter):
    err = PlaintextPrintError

    def __init__(self, name, callable_):
        self.name = name
        self.callable = callable_
        update_wrapper(self, callable_)

    def to_string(self, value: T):
        return self.callable(value)

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)


class FuncParser(PlaintextParser):
    err = PlaintextParseError

    def __init__(self, name, callable_):
        self.name = name
        self.callable = callable_
        update_wrapper(self, callable_)

    def from_string(self, value: str):
        return self.callable(value)

    def __call__(self, *args, **kwargs):
        return self.callable(*args, **kwargs)


def clean_name(name: str):
    return name.strip('_')


def parser(name: str = ...) -> Callable[[Callable[[str], Any]], PlaintextParser]:
    def ret(func):
        nonlocal name
        if name is ...:
            name = clean_name(func.__name__)
        return FuncParser(name, func)

    return ret


def printer(name: str = ...) -> Callable[[Callable[[Any], str]], PlaintextPrinter]:
    def ret(func):
        nonlocal name
        if name is ...:
            name = clean_name(func.__name__)
        return FuncPrinter(name, func)

    return ret


StrPrinter = printer()(str)
ReprPrinter = printer()(repr)


def regex_parser(*patterns: Union[Pattern[str], str], name=...)\
        -> Callable[[Callable[[Match[str]], Any]], PlaintextParser]:
    patterns = [re.compile(p) for p in patterns]

    def ret(func):
        nonlocal name
        if name is ...:
            name = clean_name(func.__name__)

        @parser(name)
        def ret(s: str):
            for p in patterns:
                m = p.fullmatch(s)
                if m:
                    return func(m)
            raise PlaintextParseError('string did not match pattern')

        return ret

    return ret
