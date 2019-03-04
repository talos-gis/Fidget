from typing import TypeVar, Generic, Tuple, Union

from PyQt5.QtWidgets import QLabel, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser, PlaintextParseError

T = TypeVar('T')


class LabelValueWidget(Generic[T], ValueWidget[T]):
    NO_DEFAULT_VALUE = object()

    def __init__(self, title, value: Union[Tuple[str, T], T], **kwargs):
        kwargs.setdefault('make_title_label', False)
        super().__init__(title, **kwargs)

        self.label: QLabel = None
        self.single_value = self._name_and_value(value)

        self.init_ui()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.label = QLabel(self.single_value[0])
            layout.addWidget(self.label)

    def parse(self):
        return self.single_value[1]

    def fill(self, key: Union[T, bool]):
        if key != self.single_value[1]:
            raise ValueError('value is not a valid fill value')

    @staticmethod
    def _name_and_value(v):
        try:
            a, b = v
            if not isinstance(a, str):
                raise TypeError
        except (TypeError, ValueError):
            return str(v), v
        return v

    @InnerPlaintextParser
    def singleton(self, v):
        if v != self.single_value[0]:
            raise PlaintextParseError(f'can only parse {self.single_value[0]!r}')
        return self.single_value[1]


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = LabelValueWidget('sample', ('Hi', 1245))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
