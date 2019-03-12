from __future__ import annotations

from fidget.backend.QtWidgets import QApplication

from typing import Union, Callable, Any, Tuple, Type, TypeVar, Optional

from functools import wraps

T = TypeVar('T')


def error_chain(e: Exception):
    while e:
        yield e
        e = e.__cause__


def error_details(e: Exception):
    ret = []
    type_names = []
    for e in error_chain(e):
        if e.args != ():
            ret.append(f'{type(e).__name__}: {e}')
        type_names.append(type(e).__name__)
    if ret:
        return '\n\tfrom:\n'.join(ret)
    return '\n\tfrom:\n'.join(type_names)


def error_tooltip(e: Exception):
    ret = None
    for e in error_chain(e):
        if e.args:
            ret = f'{type(e).__name__}: ...'
        else:
            return f'{type(e).__name__}: {e}'
    return ret


_missing = object()


def error_attrs(e: Exception, attr_name: str):
    for e in error_chain(e):
        attr = getattr(e, attr_name, _missing)
        if attr is not _missing:
            yield attr


def exc_wrap(to_raise: Type[Exception]):
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

    ret.__doc__ = \
        f"""
        wraps a function so it catches all exceptions of a type and re-throws it as a {to_raise.__name__}  
        """

    return ret


def first_valid(**kwargs: Optional[T]) -> T:
    try:
        return next(a for a in kwargs.values() if a is not None)
    except StopIteration as e:
        raise TypeError(f'none of {", ".join(kwargs.keys())} provided') from e


def shorten(s: str, width: int, filler='...'):
    if len(s) <= width:
        return s
    half_width = (width - len(filler)) // 2
    return s[:half_width] + filler + s[-half_width:]
