from typing import TypeVar, Generic, Iterable, Tuple, Union, Dict, List, Callable

from fidget.backend.QtWidgets import QComboBox, QHBoxLayout

from fidget.core import Fidget, PlaintextPrintError, inner_plaintext_parser, PlaintextParseError, ParseError

T = TypeVar('T')


class FidgetEditCombo(Generic[T], Fidget[T]):
    """
    A Fidget for an editable ComboBox
    """
    NO_DEFAULT_VALUE = object()
    CONVERT_NAME = object()

    def __init__(self, title, options: Iterable[Union[Tuple[str, T], T, str]],
                 convert_func: Callable[[str], T] = lambda x: x,
                 default_index=-1, default_value: T = NO_DEFAULT_VALUE,
                 **kwargs):
        """
        :param title: the title
        :param options: an iterable of options
        :param convert_func: a function to convert plaintext edited value to a value
        :param default_index: the default index of the ComboBox. ignored if a valid default_value is provided
        :param default_value: the default value of the ComboBox
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)
        self.default_index = default_index
        self.default_value = default_value
        self.options = options
        self.convert_func = convert_func

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
            self.combo_box.setEditable(True)
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
            self.combo_box.editTextChanged.connect(self.change_value)
            self.setFocusProxy(self.combo_box)

        return layout

    def parse(self):
        cur_text = self.combo_box.currentText()
        _, ret = self._opt_lookup_name.get(cur_text, (-1, self.CONVERT_NAME))
        if ret is self.CONVERT_NAME:
            ret = self.convert(cur_text)
        return ret

    def extract_name_and_value(self, value: Union[Tuple[str, T], T, str]) -> Tuple[str, T]:
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
            return value

        try:
            # first try to print like a value, if that fails, convert as a name
            name = self.joined_plaintext_printer(value)
        except (PlaintextPrintError, TypeError) as e:
            if isinstance(value, str):
                return value, self.convert(value)
            raise Exception('the joined printer raised an exception for a combo option') from e
        else:
            return name, value

    def fill(self, key: T):
        def fill_from_str(inner_exc):
            if isinstance(key, str):
                self.combo_box.setEditText(key)
                return
            raise KeyError(f'fill value {key} is not an option, and is not a string') from inner_exc

        try:
            index, _ = self._opt_lookup_hashable[key]
        except TypeError:
            # v is unhashable, look in non-hashables
            for k, (i, _) in self._opt_lookup_non_hashable:
                if k == key:
                    index = i
                    break
            else:
                return fill_from_str(None)
        except KeyError as e:
            # v is hashable, but not present
            return fill_from_str(e)

        self.combo_box.setCurrentIndex(index)

    @inner_plaintext_parser
    def by_name(self, name):
        try:
            _, ret = self._opt_lookup_name[name]
        except KeyError as e:
            raise PlaintextParseError() from e
        else:
            return ret

    @inner_plaintext_parser
    def by_convert(self, v):
        try:
            _ = self.convert(v)
        except ParseError as e:
            raise PlaintextParseError() from e
        return v

    def convert(self, v: str):
        # we leave this function for potential inheritors
        return self.convert_func(v)


if __name__ == '__main__':
    from fidget.backend.QtWidgets import QApplication
    from fidget.core import wrap_parser

    app = QApplication([])
    w = FidgetEditCombo('sample',
                        options=[
                           ('one', 1),
                           ('two', 2),
                           ('three', 3)
                       ],
                        convert_func=wrap_parser(ValueError, int),
                        make_title=True,
                        make_plaintext=True,
                        make_indicator=True
                        )
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
