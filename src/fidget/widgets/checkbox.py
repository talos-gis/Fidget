from typing import TypeVar, Generic

from fidget.backend.QtWidgets import QCheckBox, QHBoxLayout

from fidget.core.__util__ import first_valid

from fidget.widgets.discrete import FidgetDiscreteChoice

T = TypeVar('T')


class FidgetCheckBox(Generic[T], FidgetDiscreteChoice[T]):
    """
    A checkbox that can contain one of two values
    """
    MAKE_INDICATOR = False
    MAKE_TITLE = False
    MAKE_PLAINTEXT = False

    UPDATE_TEXT = True
    OPTIONS = (False, True)

    def __init__(self, title, update_text = None, **kwargs):
        super().__init__(title, **kwargs)
        if len(self.options) != 2:
            raise ValueError('FidgetCheckBox must have exactly 2 options, got '+str(len(self.options)))

        self.checkbox: QCheckBox = None

        self.update_text = first_valid(update_text=update_text, UPDATE_TEXT=self.UPDATE_TEXT, _self=self)

        self.init_ui()
        self.fill_initial()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.checkbox = QCheckBox()
            self.checkbox.toggled.connect(self.change_value)
            layout.addWidget(self.checkbox)

        self.setFocusProxy(self.checkbox)
        return layout

    def parse(self):
        return self.options[self.checkbox.isChecked()][1]

    def fill_index(self, index):
        self.checkbox.setChecked(index)

    def change_value(self, *args):
        super().change_value(*args)
        if self.update_text:
            option_name = self.options[self.checkbox.isChecked()][0]
            self.checkbox.setText(option_name[0])
