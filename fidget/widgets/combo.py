from typing import TypeVar, Generic, Iterable, Tuple, Union, Dict, List

from fidget.backend.QtWidgets import QComboBox, QHBoxLayout

from fidget.core import ValueWidget, PlaintextPrintError, inner_plaintext_parser, PlaintextParseError, ParseError

T = TypeVar('T')


class ValueCombo(Generic[T], ValueWidget[T]):
    """
    A ComboBox with values for each option
    """
    NO_DEFAULT_VALUE = object()
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = False

    def __init__(self, title, options: Iterable[Union[Tuple[str, T], T]], default_index=-1,
                 default_value: T = NO_DEFAULT_VALUE, **kwargs):
        """
        :param title: the title
        :param options: an iterable of options: either bare values or str-value tuples
        :param default_index: the default index of the ComboBox, ignored if a valid DefaultValue is provided
        :param default_value: the default value of the widget
        :param kwargs: forwarded to ValueWidget
        """
        super().__init__(title, **kwargs)
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

        with self.setup_provided(layout):
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

    def parse(self):
        if self.combo_box.currentIndex() == -1:
            raise ParseError('value is unset')
        return self.combo_box.currentData()

    def extract_name_and_value(self, value: Union[Tuple[str, T], T]) -> Tuple[str, T]:
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
            return value

        try:
            name = self.joined_plaintext_printer(value)
        except PlaintextPrintError as e:
            raise Exception('the joined printer raised an exception for a combo option') from e

        return name, value

    def fill(self, key: Union[T, int]):
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
            if isinstance(key, int):
                index = key
            else:
                raise KeyError('fill value is not an option') from e

        self.combo_box.setCurrentIndex(index)

    @inner_plaintext_parser
    def by_name(self, name):
        try:
            _, ret = self._opt_lookup_name[name]
        except KeyError as e:
            raise PlaintextParseError('name not found') from e
        else:
            return ret


if __name__ == '__main__':
    from fidget.backend import QApplication
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
