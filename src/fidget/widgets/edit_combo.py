from typing import TypeVar, Iterable, Tuple, Union, Dict

from fidget.backend.QtWidgets import QComboBox, QHBoxLayout

from fidget.core import inner_plaintext_parser, PlaintextParseError, Fidget
from fidget.core.__util__ import first_valid

from fidget.widgets.discrete import parse_option
from fidget.widgets.rawstring import FidgetRawString

T = TypeVar('T')


class FidgetEditCombo(FidgetRawString):
    """
    A Fidget for an editable ComboBox
    """
    NO_DEFAULT_VALUE = object()
    OPTIONS = None

    def __init__(self, title, options: Iterable[Union[Tuple[str, T], T]] = None,
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
        self.options = first_valid(options=options, OPTIONS=self.OPTIONS, _self=self)

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

            self._opt_lookup_name = {}

            for value in self.options:
                names, value = parse_option(self, value)
                name = names[0]
                self.combo_box.addItem(name, value)
                for n in names:
                    self._opt_lookup_name[n] = value

            self.combo_box.editTextChanged.connect(self.change_value)
            self.setFocusProxy(self.combo_box)

        return layout

    def parse(self):
        cur_text = self.combo_box.currentText()
        lookup = self._opt_lookup_name.get(cur_text, None)
        if lookup is None:
            return cur_text
        return lookup

    def validate(self, value):
        # super is expecting a string, don't call it if value isn't a string
        if isinstance(value, str):
            super().validate(value)
        else:
            Fidget.validate(self, value)

    def fill(self, key: T):
        self.combo_box.setEditText(key)

    @inner_plaintext_parser
    def by_name(self, name):
        if name in self._opt_lookup_name:
            return name
        raise PlaintextParseError() from KeyError(name)

    def fill_stylesheet(self, v):
        self.combo_box.setStyleSheet(v)
