from __future__ import annotations

from fidget.backend.QtWidgets import QApplication

from typing import Union, Callable, Any, Tuple, Type, TypeVar, Optional

from functools import wraps

T = TypeVar('T')


def error_details(e: Exception):
    ret = []
    type_names = []
    while e:
        if e.args != ():
            ret.append(f'{type(e).__name__}: {e}')
        type_names.append(type(e).__name__)
        e = e.__cause__
    if ret:
        return '\n\tfrom:\n'.join(ret)
    return '\n\tfrom:\n'.join(type_names)


def error_tooltip(e: Exception):
    ret = None
    while e:
        if e.args == ():
            ret = f'{type(e).__name__}: ...'
            e = e.__cause__
            continue
        return f'{type(e).__name__}: {e}'
    return ret


def error_attr(e: Exception, attr_name: str, default=None):
    ret = default
    while e:
        if hasattr(e, attr_name):
            ret = getattr(e, attr_name)
        e = e.__cause__
    return ret


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
