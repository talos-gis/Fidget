from typing import TypeVar, Generic, Iterable, Tuple, Union, Dict, List

from PyQt5.QtWidgets import QComboBox, QHBoxLayout

from qtalos import ValueWidget, PlaintextPrintError, InnerPlaintextParser, PlaintextParseError

T = TypeVar('T')


class ValueCombo(Generic[T], ValueWidget[T]):
    NO_DEFAULT_VALUE = object()

    def __init__(self, title, *args, options: Iterable[Union[Tuple[str, T], T]], default_index=-1,
                 default_value: T = NO_DEFAULT_VALUE, **kwargs):
        super().__init__(title, *args, **kwargs)
        self.default_index = default_index
        self.default_value = default_value
        self.options = options

        self._opt_lookup_hashable: Dict[T, Tuple[int, str]] = None
        self._opt_lookup_non_hashable: List[Tuple[T, Tuple[int, str]]] = None
        self._opt_lookup_name: Dict[str, Tuple[int, T]] = None

        self.combo_box: QComboBox = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        self.combo_box = QComboBox()
        layout.addWidget(self.combo_box)

        self._opt_lookup_hashable = {}
        self._opt_lookup_non_hashable = []
        self._opt_lookup_name = {}

        ind = self.default_index
        for i, value in enumerate(self.options):
            name, value = self.extract_name_and_value(value)
            self.combo_box.addItem(name, value)
            if value == self.default_value:
                ind = i

            self._opt_lookup_name[name] = (i, value)

            try:
                self._opt_lookup_hashable[value] = (i, name)
            except TypeError:
                self._opt_lookup_non_hashable.append((value, (i, name)))

        self.combo_box.setCurrentIndex(ind)
        self.combo_box.currentIndexChanged.connect(self.change_value)

        if self.validation_label:
            layout.addWidget(self.validation_label)
        if self.auto_button:
            layout.addWidget(self.auto_button)
        if self.help_button:
            layout.addWidget(self.help_button)

    def parse(self):
        if self.combo_box.currentIndex() == -1:
            raise self.parse_exception('value is unset')
        return self.combo_box.currentData()

    def extract_name_and_value(self, value: Union[Tuple[str, T], T]) -> Tuple[str, T]:
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
            return value

        try:
            name = self.joined_plaintext_printer(value)
        except PlaintextPrintError as e:
            raise Exception('the joined printer raised an exception for a combo option') from e

        return name, value

    def fill(self, key: T):
        if isinstance(key, int):
            index = key
        else:
            try:
                index, _ = self._opt_lookup_hashable[key]
            except TypeError:
                # v is unhashable, look in non-hashables
                for k, (i, _) in self._opt_lookup_non_hashable:
                    if k == key:
                        index = i
                        break
                else:
                    raise KeyError(f'fill value {key} is not an option')
            except KeyError as e:
                # v is hashable, but not present
                raise KeyError('fill value is not an option') from e

        self.combo_box.setCurrentIndex(index)

    @InnerPlaintextParser
    def by_name(self, name):
        try:
            _, ret = self._opt_lookup_name[name]
        except KeyError as e:
            raise PlaintextParseError('name not found') from e
        else:
            return ret


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from enum import Enum, auto


    class Options(Enum):
        first = auto()
        second = auto()
        third = auto()


    app = QApplication([])
    w = ValueCombo('sample', options=Options)
    w.show()
    w.fill_from_text('Options.first')
    res = app.exec_()
    print(w.value())
    exit(res)
