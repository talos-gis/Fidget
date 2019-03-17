from __future__ import annotations

from typing import TypeVar, Optional

from pathlib import Path
import os
from functools import wraps, lru_cache

from fidget.backend.QtWidgets import QWidget

from fidget.core import Fidget, ValidationError

T = TypeVar('T')

win_illegal_chars = frozenset(r'<>:"/\|?*').union(chr(i) for i in range(32))
win_illegal_base_names = frozenset(('', 'CON', 'PRN', 'AUX', 'NUL',
                                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'))
win_illegal_suffixes = frozenset(' .')


def filename_valid(path: Path):
    """
    Check whether a file path seems legal
    :param path: the file path
    :return: whether a file path seems legal
    """
    if os.name == 'nt':
        parts = path.parts
        if path.drive:
            parts = parts[1:]
        for part in parts:
            if any(c in win_illegal_chars for c in part):
                return False
            if part[-1] in win_illegal_suffixes:
                return False
            dot_index = part.find('.')
            if dot_index >= 0:
                part = part[:dot_index]
            if part in win_illegal_base_names:
                return False
        return True
    # todo implement for linux
    else:
        raise NotImplementedError


_trivial_printers = frozenset(Fidget.plaintext_printers(None))


def is_trivial_printer(p):
    """
    check if a printer is a trivial printer
    :param p: the printer to check
    """
    return p in _trivial_printers


def only_valid(_invalid=None, **kwargs: Optional[T]) -> T:
    """
    check that only one of the arguments is not None, and return its value
    :return: the value of the only not-None argument
    """
    valid = _invalid
    for k, v in kwargs.items():
        if v is _invalid:
            continue
        if valid is not _invalid:
            raise TypeError(f'both {valid[0]} and {k} provided')
        valid = k, v
    if valid is _invalid:
        raise TypeError(f'none of {", ".join(kwargs.keys())} provided')
    return valid[1]


def optional_valid(_invalid=None, **kwargs: Optional[T]) -> Optional[T]:
    """
    check at most one of the arguments is not None, and return its value
    :return: the value of the only not-None argument, or None
    """
    valid = None
    for k, v in kwargs.items():
        if v is _invalid:
            continue
        if valid is not _invalid:
            raise TypeError(f'both {valid[0]} and {k} provided')
        valid = k, v
    if valid is None:
        return _invalid
    return valid[1]


def last_focus_proxy(seed: QWidget):
    """
    This utility function is because SetTabOrder currently has a bug where it doesn't respect focus proxies, so we
    dynamically get the focus proxy of a widget
    """
    ret = seed
    while True:
        focus = ret.focusProxy()
        if not focus:
            return ret
        ret = focus


@lru_cache(None)
def wrap(func, **kwargs):
    @wraps(func)
    def ret(*a, **k):
        return func(*a, **k)

    for k, v in kwargs.items():
        setattr(ret, k, v)

    return ret


def repeat_last(iterable):
    i = iter(iterable)
    last = None
    while True:
        try:
            last = next(i)
        except StopIteration:
            break
        yield last
    while True:
        yield last


def valid_between(min, max):
    def ret(v):
        if min is not None and v < min:
            raise ValidationError(f'value must be at least {min}')
        if max is not None and v >= max:
            raise ValidationError(f'value must be less than {max}')

    return ret
