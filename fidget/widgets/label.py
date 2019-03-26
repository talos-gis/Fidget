from typing import TypeVar

from fidget.backend.QtWidgets import QLabel, QHBoxLayout

from fidget.core import inner_plaintext_parser, PlaintextParseError

from fidget.widgets.discrete import parse_option
from fidget.widgets.rawstring import FidgetRawString

T = TypeVar('T')


class FidgetLabel(FidgetRawString):
    """
    A Fidget that immutably contains a single value
    """
    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False

    def __init__(self, title, **kwargs):
        """
        :param title: the title
        :param value: the single value to display
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)

        self.label: QLabel = None
        self.__value = None

        self.names = ()

        self.init_ui()
        self.fill_initial()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.label = QLabel()
            layout.addWidget(self.label)

        self.setFocusProxy(self.label)

        return layout

    def parse(self):
        return self.__value

    def fill(self, key):
        self.names, self.__value = parse_option(self, key)
        self.label.setText(self.names[0])

    @inner_plaintext_parser
    def singleton(self, v):
        if v not in self.names:
            raise PlaintextParseError(f'can only parse {self.names}')
        return self.__value

    def fill_stylesheet(self, v):
        self.label.setStyleSheet(v)
