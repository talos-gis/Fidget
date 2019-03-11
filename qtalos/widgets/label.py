from typing import TypeVar, Generic, Tuple, Union

from qtalos.backend import QLabel, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser, PlaintextParseError, PlaintextPrintError

T = TypeVar('T')


class LabelValueWidget(Generic[T], ValueWidget[T]):
    NO_DEFAULT_VALUE = object()

    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False

    def __init__(self, title, value: Union[Tuple[str, T], T], **kwargs):
        super().__init__(title, **kwargs)

        self.label: QLabel = None
        self.name, self.names, self.single_value = self._names_and_value(value)

        self.init_ui()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.label = QLabel(self.name)
            layout.addWidget(self.label)

    def parse(self):
        return self.single_value

    def fill(self, key: Union[T, bool]):
        if key != self.single_value:
            raise ValueError('value is not a valid fill value')

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

        for printer in self.plaintext_printers():
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

    @InnerPlaintextParser
    def singleton(self, v):
        if v not in self.names:
            raise PlaintextParseError(f'can only parse {self.names}')
        return self.single_value


if __name__ == '__main__':
    from qtalos.backend import QApplication

    app = QApplication([])
    w = LabelValueWidget('sample', ('Hi', 1245))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
