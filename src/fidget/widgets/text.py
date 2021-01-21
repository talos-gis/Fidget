from typing import Type

from fidget.backend.QtWidgets import QPlainTextEdit, QHBoxLayout
from fidget.core.__util__ import first_valid
from fidget.widgets.rawstring import FidgetRawString


class FidgetPlainText(FidgetRawString):
    """
    A string Fidget, in the form of a QLineEdit
    """
    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False

    EDIT_CLS: Type[QPlainTextEdit] = QPlainTextEdit
    PLACEHOLDER = True

    def __init__(self, title: str,
                 placeholder=None, edit_cls=None,
                 **kwargs):
        super().__init__(title, **kwargs)

        placeholder = first_valid(placeholder=placeholder, PLACEHOLDER=self.PLACEHOLDER, _self = self)

        self.edit: QPlainTextEdit = None

        self.init_ui(placeholder=placeholder, edit_cls=edit_cls)

        self.fill_initial()

    def init_ui(self, placeholder=None, edit_cls=None):
        super().init_ui()
        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            edit_cls = first_valid(edit_cls=edit_cls, EDIT_CLS=self.EDIT_CLS, _self=self)
            self.edit = edit_cls()
            if placeholder:
                self.edit.setPlaceholderText(self.title)
            self.edit.textChanged.connect(self.change_value)

            layout.addWidget(self.edit)

        self.setFocusProxy(self.edit)

        return layout

    def parse(self):
        return self.edit.toPlainText()

    def fill(self, v: str = ''):
        self.edit.setPlainText(v)

    def fill_stylesheet(self, value):
        self.edit.setStyleSheet(value)
