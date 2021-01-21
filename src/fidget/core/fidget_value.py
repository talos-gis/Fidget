from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from fidget.backend.QtWidgets import QWidget
from fidget.core.__util__ import error_details, shorten

T = TypeVar('T')


class ChildWidgetError(Exception):
    """
    An error that might be traced to a child widget, to focus on
    """

    def __init__(self, *args, offender: QWidget = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.offender = offender


class ParseError(ChildWidgetError):
    """
    an exception class for when parsing UI fails
    """
    pass


class ValidationError(ChildWidgetError, Generic[T]):
    """
    an exception class fro when a parsed value is invalid
    """
    pass


class FidgetValue(ABC):
    """
    A value of a Fidget, representing either a valid processed value or an error
    """
    SHORT_WIDTH = 50

    def __init__(self, type_details: str, details: str, short_details: str = ...):
        """
        :param type_details: a description of the type of the value's state, either an error name or a type name
        :param details: a detailed description of the value
        :param short_details: a short description of the value
        """
        self.details = details
        if short_details is ...:
            short_details = self.details
        short_details = shorten(short_details, self.SHORT_WIDTH)
        self.short_details = short_details
        self.type_details = type_details

    @abstractmethod
    def is_ok(self) -> bool:
        """
        :return: whether the value is successfully processed
        """
        pass

    def __str__(self):
        return f'{type(self).__name__}: {self.details}'


class GoodValue(Generic[T], FidgetValue):
    """
    A processed value
    """

    def __init__(self, value, details):
        super().__init__(type(value).__name__, details, str(value))
        self.value = value

    def is_ok(self):
        return True

    def __str__(self):
        return f'{type(self).__name__}[{type(self.value).__qualname__}]: {self.details}'


ET = TypeVar('ET', bound=Exception)


class BadValue(Generic[ET], FidgetValue):
    """
    An error during processing
    """

    def __init__(self, exc: ET):
        details = error_details(exc)
        short = details.splitlines(keepends=False)[0]
        super().__init__(type(exc).__name__, details, short)
        self.exception = exc

    def is_ok(self):
        return False

    @staticmethod
    def from_error(exc):
        if isinstance(exc, ParseError):
            return Unparseable(exc)
        if isinstance(exc, ValidationError):
            return Invalid(exc)
        raise TypeError(f'bad exception type {type(exc)}')


class Unparseable(BadValue[ParseError]):
    pass


class Invalid(BadValue[ValidationError]):
    pass
