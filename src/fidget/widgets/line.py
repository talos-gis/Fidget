from fidget.backend.QtWidgets import QLineEdit, QHBoxLayout

from fidget.core.__util__ import first_valid

from fidget.widgets.rawstring import FidgetRawString


class FidgetLine(FidgetRawString):
    """
    A string Fidget, in the form of a QLineEdit
    """
    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False

    PLACEHOLDER = True

    def __init__(self, title: str, placeholder=None,
                 **kwargs):
        super().__init__(title, **kwargs)

        placeholder = first_valid(placeholder=placeholder, PLACEHOLDER=self.PLACEHOLDER, _self=self)

        self.edit: QLineEdit = None

        self.init_ui(placeholder=placeholder and self.title)

        self.fill_initial()

    def init_ui(self, placeholder=None):
        super().init_ui()
        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
            if placeholder:
                self.edit.setPlaceholderText(placeholder)
            self.edit.textChanged.connect(self.change_value)

            layout.addWidget(self.edit)

        self.setFocusProxy(self.edit)

        return layout

    def parse(self):
        return self.edit.text()

    def fill(self, v: str = ''):
        self.edit.setText(v)

    def fill_stylesheet(self, style):
        self.edit.setStyleSheet(style)
