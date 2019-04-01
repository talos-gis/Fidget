from __future__ import annotations

from typing import TypeVar, Optional, Tuple, Iterable, List, Callable, MutableMapping, Generic, Container, Dict, \
    Iterator

from pathlib import Path
import os

from fidget.backend.QtWidgets import QWidget, QFileDialog

from fidget.core import Fidget, ValidationError

T = TypeVar('T')

win_illegal_chars = frozenset(r'<>:"/\|?*').union(chr(i) for i in range(32))
win_illegal_base_names = frozenset(('', 'CON', 'PRN', 'AUX', 'NUL',
                                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'))
win_illegal_suffixes = frozenset(' .')

lin_illegal_chars = frozenset('/\0')


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
    elif os.name == 'posix':
        parts = path.parts
        for part in parts:
            if any(c in lin_illegal_chars for c in part):
                return False
        return True
    else:
        raise NotImplementedError


_trivial_printers = frozenset(Fidget.cls_plaintext_printers())


def is_trivial_printer(p):
    """
    check if a printer is a trivial printer
    :param p: the printer to check
    """
    return p in _trivial_printers


def only_valid(_self, _invalid=None, **kwargs: Optional[T]) -> T:
    """
    check that only one of the arguments is not None, and return its value
    :return: the value of the only not-None argument
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
        if _self:
            self_str = f' in {_self}'
        else:
            self_str = ''
        raise TypeError(f'none of {", ".join(kwargs.keys())} provided{self_str}')
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


class CountBounds:
    def __init__(self, initial: int, min: int = None, max: Optional[int] = None):
        self.initial = initial
        self.max = max
        self.min = min

    def in_bounds(self, num):
        if num < self.min:
            return False
        if self.max is not None and num >= self.max:
            return False
        return True

    def __class_getitem__(cls, item):
        if isinstance(item, int):
            return cls(item, item, item + 1)
        if isinstance(item, slice):
            initial = item.start or 1
            min = item.stop or 1
            max = item.step
            return cls(initial, min, max)
        if isinstance(item, cls):
            return item
        return cls(*item)

    @property
    def is_const(self):
        return self.max is not None and self.max - self.min == 1


def parse_int(s):
    if isinstance(s, int):
        return s
    return int(s, base=0)


parse_int.__name__ = 'int'


def table_printer(row_binders: Tuple[Iterable[str], Iterable[str], Iterable[str]], col_sep: str, row_sep: str,
                  header_row: Callable[[object], Iterable[str]] = None):
    first_binder, mid_binder, last_binder = row_binders

    def ret(self, v: List[List[T]]):
        strings = self.string_matrix(v)
        if header_row:
            strings.insert(0, header_row(self))
        elements = []
        binders = []
        max_lens = [0 for _ in range(len(strings[0]))]
        for row_num, row in enumerate(strings):
            if row_num == 0:
                binder = first_binder
            elif row_num == len(v) - 1:
                binder = last_binder
            else:
                binder = mid_binder
            binders.append(binder)
            row_str = []
            for col_num, e in enumerate(row):
                max_lens[col_num] = max(max_lens[col_num], len(e))
                row_str.append(e)
            elements.append(row_str)
        if header_row:
            header_elements = ['-' * ml for ml in max_lens]
            binders.insert(1, mid_binder)
            elements.insert(1, header_elements)

        ret = []
        for (opener, closer), row in zip(binders, elements):
            row_str = []
            for length, element in zip(max_lens, row):
                row_str.append(element.rjust(length))
            row_str = opener + col_sep.join(row_str) + closer
            ret.append(row_str)
        return row_sep.join(ret)

    return ret


K = TypeVar('K')
V = TypeVar('V')


class TolerantDict(Generic[K, V], MutableMapping[K, V]):
    def __init__(self, *args, **kwargs):
        self.hashable = {}
        self.unhashable_k = []
        self.unhashable_v = []

        self.update(*args, **kwargs)

    def __getitem__(self, item):
        try:
            return self.hashable[item]
        except TypeError:
            # item is unhashable
            for k, v in zip(self.unhashable_k, self.unhashable_v):
                if k == item:
                    return v

    def __setitem__(self, key, value):
        try:
            self.hashable[key] = value
        except TypeError:
            # item is unhashable
            for i, (k, v) in enumerate(zip(self.unhashable_k, self.unhashable_v)):
                if k == key:
                    self.unhashable_v[i] = v
                    return
            self.unhashable_k.append(key)
            self.unhashable_v.append(value)

    def __delitem__(self, key):
        try:
            del self.hashable[key]
        except TypeError:
            # item is unhashable
            for i, (k, v) in enumerate(zip(self.unhashable_k, self.unhashable_v)):
                if k == key:
                    del self.unhashable_k[i]
                    del self.unhashable_v[i]
                    return
            raise KeyError(key)

    def __iter__(self):
        yield from iter(self.hashable)
        yield from iter(self.unhashable_k)

    def items(self):
        yield from iter(self.hashable.items())
        yield from iter(zip(self.unhashable_k, self.unhashable_v))

    def __len__(self):
        return len(self.hashable) + len(self.unhashable_k)


class PrefixTrie(Container[str]):
    """
    >>> t = PrefixTrie()
    >>> t.add('abc')
    >>> t.add('bca')
    >>> 'ab' in t
    True
    >>> 'a' in t
    True
    >>> 'abc' in t
    True
    >>> '' in t
    True
    >>> 'bc' in t
    True
    >>> 'c' not in t
    True
    """

    def __init__(self):
        self.children: Dict[str, PrefixTrie] = {}

    def add(self, s: Iterator[str]):
        s = iter(s)
        char = next(s, None)
        if char is None:
            return
        if char not in self.children:
            self.children[char] = type(self)()
        self.children[char].add(s)

    def __contains__(self, s: Iterator[str]):
        s = iter(s)
        char = next(s, None)
        if char is None:
            return True
        if char not in self.children:
            return False
        return s in self.children[char]


def to_identifier(s: str):
    if s.isidentifier():
        return s

    s = s.strip().replace(' ', '_')
    if s.isidentifier():
        return s

    if not s[0].isidentifier():
        s = '_' + s
    s = ''.join(c for c in s if c.isalnum() or c == '_')
    if not s.isidentifier():
        return s

    return '_'


class RememberingFileDialog(QFileDialog):
    """
    A QFileDialog that remembers its last directory
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_dir = None

    def exec(self):
        if self.last_dir:
            self.setDirectory(self.last_dir)
        ret = super().exec_()
        self.last_dir = super().directory()
        return ret
