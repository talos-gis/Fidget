from typing import TypeVar, Generic, Tuple, Union

from fidget.backend.QtWidgets import QLabel, QHBoxLayout

from fidget.core import Fidget, inner_plaintext_parser, PlaintextParseError, PlaintextPrintError, ParseError

T = TypeVar('T')


class FidgetLabel(Generic[T], Fidget[T]):
    """
    A Fidget that immutably contains a single value
    """
    NO_VALUE = object()

    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False

    def __init__(self, title, value: Union[Tuple[str, T], T] = NO_VALUE, **kwargs):
        """
        :param title: the title
        :param value: the single value to display
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)

        self.label: QLabel = None

        self.__value = self.NO_VALUE
        self.names = ()

        self.init_ui()
        self.fill(value)

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.label = QLabel()
            layout.addWidget(self.label)

        self.setFocusProxy(self.label)

        return layout

    def parse(self):
        if self.__value is self.NO_VALUE:
            raise ParseError('no value is set')
        return self.__value

    def fill(self, key: T = NO_VALUE):
        if key is self.NO_VALUE:
            name = '<no value>'
            self.names = ()
            self.__value = key
        else:
            name, self.names, self.__value = self._names_and_value(key)
        self.label.setText(name)

    def _names_and_value(self, value):
        names = []
        first_name = None
        try:
            name, v = value
            if not isinstance(name, str):
                raise TypeError
        except (TypeError, ValueError):
            pass
        else:
            value = v
            names.append(name)
            first_name = name

        names.append(self.title)

        for printer in self.implicit_plaintext_printers():
            try:
                name = printer(value)
            except PlaintextPrintError:
                continue
            else:
                names.append(name)
                if not first_name:
                    first_name = name

        if not first_name:
            first_name = self.title

        return first_name, frozenset(names), value

    @inner_plaintext_parser
    def singleton(self, v):
        if v not in self.names:
            raise PlaintextParseError(f'can only parse {self.names}')
        return self.__value

    def indication_changed(self, value):
        super().indication_changed(value)
        if value.is_ok():
            self.edit.setStyleSheet('')
        else:
            self.edit.setStyleSheet('color: red;')


if __name__ == '__main__':
    from fidget.backend import QApplication

    app = QApplication([])
    w = FidgetLabel('sample', ('Hi', 1245))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
