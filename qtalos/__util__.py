from __future__ import annotations

from typing import Union, Callable, Any, Tuple, Type

from pathlib import Path
from functools import wraps
import os

win_illegal_chars = frozenset(r'<>:"/\|?*').union(chr(i) for i in range(32))
win_illegal_base_names = frozenset(('', 'CON', 'PRN', 'AUX', 'NUL',
                                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'))
win_illegal_suffixes = frozenset(' .')

# todo move this
def filename_valid(path: Path):
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


def error_details(e: Exception):
    ret = []
    while e:
        ret.append(f'{type(e).__name__}: {e}')
        e = e.__cause__
    return '\nfrom:\n'.join(ret)


def exc_wrap(to_raise: Exception):
    def ret(exc_cls: Union[Type[Exception], Tuple[Type[Exception], ...]], func: Callable[[str], Any] = None):
        def ret(func):
            @wraps(func)
            def ret(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exc_cls as e:
                    raise to_raise from e

            return ret

        if func:
            return ret(func)
        return ret

    return ret
