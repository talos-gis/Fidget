from __future__ import annotations

from typing import TypeVar, Optional

from pathlib import Path
import os

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


def is_trivial_printer(p):
    """
    check if a printer is a trivial printer
    :param p: the printer to check
    """
    return p in (str, repr)


def only_valid(**kwargs: Optional[T]) -> T:
    """
    check that only one of the arguments is not None, and return its value
    :return: the value of the only not-None argument
    """
    valid = None
    for k, v in kwargs.items():
        if v is None:
            continue
        if valid is not None:
            raise TypeError(f'both {valid[0]} and {k} provided')
        valid = k, v
    if valid is None:
        raise TypeError(f'none of {", ".join(kwargs.keys())} provided')
    return valid[1]
