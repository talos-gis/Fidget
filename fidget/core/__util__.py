from __future__ import annotations

from typing import Union, Callable, Any, Tuple, Type, TypeVar, Optional

from fidget.backend.QtWidgets import QLabel
from fidget.backend.QtCore import Qt, QtCore

from functools import wraps, lru_cache

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


def first_valid(_self, _invalid=None, **kwargs: Optional[T]) -> T:
    try:
        return next(a for a in kwargs.values() if a is not _invalid)
    except StopIteration as e:
        if _self:
            self_str = f' in {_self}'
        else:
            self_str = ''
        raise TypeError(f'none of {", ".join(kwargs.keys())} provided{self_str}') from e


def optional_valid(_self, _invalid=None, **kwargs: Optional[T]) -> Optional[T]:
    """
    check at most one of the arguments is not None, and return its value
    :return: the value of the only not-None argument, or None
    """
    valid = _invalid
    for k, v in kwargs.items():
        if v is _invalid:
            continue
        if valid is not _invalid:
            if _self:
                self_str = f' in {_self}'
            else:
                self_str = ''
            raise TypeError(f'both {valid[0]} and {k} provided{self_str}')
        valid = k, v
    if valid is _invalid:
        return _invalid
    return valid[1]


def shorten(s: str, width: int, filler='...'):
    if len(s) <= width:
        return s
    half_width = (width - len(filler)) // 2
    return s[:half_width] + filler + s[-half_width:]


def link_to(text: str, url: str):
    ret = QLabel(f'''<a href='{url}'>{text}</a>''')
    ret.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
    ret.setOpenExternalLinks(True)
    return ret


@lru_cache(None)
def mask(func, **kwargs):
    @wraps(func)
    def ret(*a, **k):
        return func(*a, **k)

    for k, v in kwargs.items():
        setattr(ret, k, v)

    return ret


def update(**kwargs):
    def ret(func):
        for k, v in kwargs.items():
            setattr(func, k, v)
        return func

    return ret
