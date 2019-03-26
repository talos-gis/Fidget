from typing import TypeVar, Generic, Tuple, Union, List, Iterable

from abc import abstractmethod

from fidget.core import Fidget, inner_plaintext_parser, PlaintextPrintError, PlaintextParseError, \
    inner_plaintext_printer
from fidget.core.__util__ import first_valid

T = TypeVar('T')


def parse_option(fidget, value):
    names = []

    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
        names.append(value[0])
        value = value[1]

    for printer in fidget.implicit_cls_plaintext_printers():
        try:
            names.append(printer(value))
        except PlaintextPrintError:
            pass

    if not names:
        raise Exception(f'no names for {value}')

    return names, value


class FidgetDiscreteChoice(Generic[T], Fidget[T]):
    def __init__(self, title, options: Iterable[Union[T, Tuple[str, T]]] = None,
                 initial_index: int = None, initial_value=None, **kwargs):
        super().__init__(title, **kwargs)
        options = first_valid(options=options, OPTIONS=self.OPTIONS, _self=self)
        self.options = [parse_option(self, o) for o in options]
        self.name_lookup = {}
        for i, (names, o) in enumerate(self.options):
            for name in names:
                v = (i, o)
                if self.name_lookup.setdefault(name, v) != v:
                    raise ValueError('duplicate name: ' + name)

        self.initial_index = first_valid(initial_index=initial_index, INITIAL_INDEX=self.INITIAL_INDEX, _self=self)
        self.initial_value = first_valid(initial_value=initial_value, INITIAL_VALUE=self.INITIAL_VALUE, _self=self)

    INITIAL_INDEX = -1
    INITIAL_VALUE = object()
    OPTIONS = None

    def fill_initial(self):
        for i, (_, o) in enumerate(self.options):
            if o == self.initial_value:
                ind = i
                break
        else:
            ind = self.initial_index

        self.fill_index(ind)

    @abstractmethod
    def fill_index(self, index):
        pass

    def fill(self, key: Union[T, int, str]):
        # try by value equation
        for i, (_, option) in enumerate(self.options):
            if option == key:
                self.fill_index(i)
                return
        # try by name
        if isinstance(key, str):
            for i, (names, _) in enumerate(self.options):
                if key in names:
                    self.fill_index(i)
                    return
        # try by index
        if isinstance(key, int):
            self.fill_index(key)
            return

        raise ValueError('value is not a valid fill value')

    @inner_plaintext_parser
    def from_values(self, text):
        try:
            return self.name_lookup[text][1]
        except KeyError as e:
            raise PlaintextParseError(e)

    @inner_plaintext_printer
    def name(self, v):
        for names, o in self.options:
            if o == v:
                return names[0]
        raise PlaintextPrintError('no values matched')
