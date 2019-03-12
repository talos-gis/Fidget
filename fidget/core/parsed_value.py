from __future__ import annotations

from typing import Generic, TypeVar, Union

from dataclasses import dataclass
from enum import IntEnum

from fidget.core.__util__ import error_details

T = TypeVar('T')


# todo focus on the offending widget

class ParseError(Exception):
    """
    an exception class for when parsing UI fails
    """
    pass


class ValidationError(Exception, Generic[T]):
    """
    an exception class fro when a parsed value is invalid
    """
    pass


class ValueState(IntEnum):
    """
    State of a parsed value. Positive values indicate that the value has been successfully processed
    """
    ok = 1
    invalid = -1
    unparsable = -2

    def is_ok(self):
        """
        :return: whether the value is in a successful state
        """
        return self > 0


@dataclass(frozen=True)
class ParsedValue(Generic[T]):
    """
    A packed parsed value holding either a successfully parsed value or an exception.
    """
    value_state: ValueState
    value: Union[T, ParseError, ValidationError[T]]
    details: str

    def is_ok(self):
        """
        :return: whether parsing and validation has succeeded
        """
        return self.value_state.is_ok()

    @classmethod
    def from_error(cls, exc: Union[ParseError, ValidationError]):
        """
        create a ParsedValue from an error
        :param exc: the error that was thrown
        :return: a new, failure parsed value
        """
        if isinstance(exc, ParseError):
            value_state = ValueState.unparsable
        elif isinstance(exc, ValidationError):
            value_state = ValueState.invalid
        else:
            raise TypeError('exc is of invalid type ' + str(type(exc)))
        return cls(value_state, exc, error_details(exc))

    @classmethod
    def from_value(cls, v, details):
        """
        create a ParsedValue from a successful parsing
        :param v: the parsed value
        :param details: detail string of the parsed value
        :return: a new, successful value
        """
        return cls(ValueState.ok, v, details)

    def __str__(self):
        if self.is_ok():
            return str(self.value)
        return super().__str__()
