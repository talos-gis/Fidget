from enum import Enum, auto
from typing import Dict, Tuple

from abc import ABC, abstractmethod
from types import ModuleType

from importlib import import_module


class QtWrapper(Enum):
    PYQT = auto()
    PYSIDE = auto()


class PartialItemGetter:
    def __init__(self, owner, *args):
        self.owner = owner
        self.args = args

    def __getitem__(self, *items):
        item = (*self.args, *items)
        return self.owner[item]


class QtBackend(ABC):
    """
    Abstract class for Qt python backends
    """
    def __init__(self, wrapper: QtWrapper, qt_version: int):
        self.wrapper: QtWrapper = wrapper
        self.qt_version: int = qt_version

    @abstractmethod
    def load(self):
        """
        load the backend, should raise ImportError on failure.
        """
        pass

    @abstractmethod
    def __getitem__(self, item: Tuple[str, str]):
        """
        import a member from qt. Must only be called after load() has been called without errors.
        :param item: a namespace-name tuple representing the object to import
        :return: the imported object
        """
        pass

    @abstractmethod
    def module(self, name):
        """
        import the module and returns it
        """
        pass

    def partial(self, name: str):
        """
        :param name: the namespace to import from
        :return: a partial itemgetter for self
        """
        return PartialItemGetter(self, name)

    __name__: str


class NamePrefixQtBackend(QtBackend):
    """
    A Qt python backend that imports packages with standard names
    """
    def __init__(self, wrapper: QtWrapper, qt_version: int, name: str):
        super().__init__(wrapper=wrapper, qt_version=qt_version)
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

    def module(self, name):
        return self.load_module(name)

    def __getitem__(self, item):
        sub_mod, symbol = item
        mod = self.load_module(sub_mod)
        return getattr(mod, symbol)


class PyQtQtBackend(NamePrefixQtBackend):
    def __getitem__(self, item):
        if item == ('QtCore', 'Signal'):
            _signal = self['QtCore', 'pyqtSignal']

            def ret(args):
                return _signal(*args)

            return ret
        else:
            return super().__getitem__(item)


PyQt6_backend = PyQtQtBackend(wrapper=QtWrapper.PYQT, qt_version=6, name='PyQt6')
PyQt5_backend = PyQtQtBackend(wrapper=QtWrapper.PYQT, qt_version=5, name='PyQt5')


class PySideQtBackend(NamePrefixQtBackend):
    def __getitem__(self, item):
        if item == ('QtCore', 'pyqtSignal'):
            _signal = self['QtCore', 'Signal']

            def ret(*args):
                return _signal(args)

            return ret
        else:
            return super().__getitem__(item)


PySide6_backend = PySideQtBackend(wrapper=QtWrapper.PYSIDE, qt_version=6, name='PySide6')
PySide2_backend = PySideQtBackend(wrapper=QtWrapper.PYSIDE, qt_version=5, name='PySide2')
