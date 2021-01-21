from typing import TypeVar, Generic

from fidget.backend.QtWidgets import QComboBox, QHBoxLayout
from fidget.core import ParseError
from fidget.widgets.discrete import FidgetDiscreteChoice

T = TypeVar('T')


class FidgetCombo(Generic[T], FidgetDiscreteChoice[T]):
    """
    A ComboBox with values for each option
    """
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = False

    def __init__(self, title, **kwargs):
        """
        :param title: the title
        :param options: an iterable of options: either bare values or str-value tuples
        :param default_index: the default index of the ComboBox, ignored if a valid DefaultValue is provided
        :param default_value: the default value of the widget
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)

        self.combo_box: QComboBox = None

        self.init_ui()
        self.fill_initial()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.combo_box = QComboBox()
            layout.addWidget(self.combo_box)

            for names, value in self.options:
                name = names[0]
                self.combo_box.addItem(name, value)

            self.combo_box.currentIndexChanged.connect(self.change_value)

        self.setFocusProxy(self.combo_box)
        return layout

    def parse(self):
        if self.combo_box.currentIndex() == -1:
            raise ParseError('value is unset', offender=self.combo_box)
        return self.combo_box.currentData()

    def fill_index(self, index):
        self.combo_box.setCurrentIndex(index)
