from typing import Dict, Tuple

from abc import ABC, abstractmethod
from types import ModuleType

from importlib import import_module


class QtBackend(ABC):
    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def __getitem__(self, item: Tuple[str, str]):
        pass

    __name__: str


class NamePrefixQtBackend(QtBackend):
    def __init__(self, name):
        self.modules: Dict[str, ModuleType] = {}
        self.__name__ = name

    def load(self):
        for submodule in ['', 'QtWidgets', 'QtCore', 'QtGui']:
            self.load_module(submodule)

    def load_module(self, sub_name):
        if sub_name in self.modules:
            return self.modules[sub_name]

        name = self.__name__
        if sub_name:
            name += '.' + sub_name
        self.modules[sub_name] = ret = import_module(name)
        return ret

    def __getitem__(self, item):
        sub_mod, symbol = item
        mod = self.load_module(sub_mod)
        return getattr(mod, symbol)


PyQt5_backend = NamePrefixQtBackend('PyQt5')


class PySide2QtBackend(NamePrefixQtBackend):
    def __getitem__(self, item):
        if item == ('QtCore', 'pyqtSignal'):
            _signal = self['QtCore', 'Signal']

            def ret(*args):
                return _signal(args)

            return ret
        return super().__getitem__(item)


PySide2_backend = PySide2QtBackend('PySide2')
