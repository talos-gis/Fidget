from typing import TypeVar, Generic

from fidget.backend.QtWidgets import QLabel, QHBoxLayout

from fidget.core.__util__ import first_valid, optional_valid

from fidget.widgets.discrete import FidgetDiscreteChoice

T = TypeVar('T')


class FidgetConst(Generic[T], FidgetDiscreteChoice[T]):
    """
    A checkbox that can contain one of two values
    """
    MAKE_INDICATOR = False
    MAKE_TITLE = False
    MAKE_PLAINTEXT = False

    INITIAL_INDEX = 0

    OPTION = None

    def __init__(self, title, option=None, **kwargs):
        option = optional_valid(_self=self, option=option, OPTION=self.OPTION)
        if option:
            if 'options' in kwargs:
                raise TypeError('"option" and "options" arguments cannot be simultaneously used in FidgetConst')
            kwargs['options'] = [option]

        super().__init__(title, **kwargs)
        if len(self.options) != 1:
            raise ValueError('FidgetConst must have exactly 1 option, got ' + str(len(self.options)))

        self.label: QLabel = None

        self.init_ui()
        self.fill_initial()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.label = QLabel(self.options[0][0][0])
            layout.addWidget(self.label)

        self.setFocusProxy(self.label)
        return layout

    def parse(self):
        return self.options[0][1]

    def fill_index(self, index):
        pass
