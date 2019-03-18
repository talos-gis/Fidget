from typing import Optional, Pattern, Union, Container

import re

from fidget.backend.QtWidgets import QLineEdit, QHBoxLayout

from fidget.core import Fidget, inner_plaintext_parser, ValidationError

from fidget.widgets.__util__ import optional_valid


class FidgetLineEdit(Fidget[str]):
    """
    A string Fidget, in the form of a QLineEdit
    """
    MAKE_INDICATOR = MAKE_TITLE = MAKE_PLAINTEXT = False
    PATTERN = None
    ALLOWED_CHARACTERS: Container[str] = None
    FORBIDDEN_CHARACTERS: Container[str] = None

    def __init__(self, title: str, pattern: Union[str, Pattern[str]] = None,
                 allowed_characters: Container[str] = None, forbidden_characters: Container[str] = None,
                 placeholder=True,
                 **kwargs):
        """
        :param title: the title
        :param pattern: a regex pattern the value must match to be validated
        :param placeholder: whether to display the widget's title in a placeholder
        :param allowed_characters: if provided, only characters in this container will pass validation
        :param forbidden_characters: if provided, only characters not in this container will pass validation
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)

        pattern = optional_valid(pattern=pattern, PATTERN=self.PATTERN)

        self.pattern: Optional[Pattern[str]] = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.allowed_characters = optional_valid(allowed_characters=allowed_characters,
                                                 ALLOWED_CHARACTERS=self.ALLOWED_CHARACTERS)
        self.forbidden_characters = optional_valid(forbidden_characters=forbidden_characters,
                                                   FORBIDDEN_CHARACTERS=self.FORBIDDEN_CHARACTERS)

        self.edit: QLineEdit = None

        self.init_ui(placeholder=placeholder and self.title)

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

    def validate(self, value):
        super().validate(value)
        if self.pattern and not self.pattern.fullmatch(value):
            raise ValidationError(f'value must match pattern {self.pattern}', offender=self.edit)
        if self.allowed_characters is not None:
            try:
                i, c = next(
                    ((i, c) for (i, c) in enumerate(value) if c not in self.allowed_characters)
                )
            except StopIteration:
                pass
            else:
                raise ValidationError(f'character {c} (position {i}) is not allowed')
        if self.forbidden_characters is not None:
            try:
                i, c = next(
                    ((i, c) for (i, c) in enumerate(value) if c in self.forbidden_characters)
                )
            except StopIteration:
                pass
            else:
                raise ValidationError(f'character {c} (position {i}) is forbidden')

    @inner_plaintext_parser
    def raw_text(self, v):
        return v

    def fill(self, v: str = ''):
        self.edit.setText(v)

    def indication_changed(self, value):
        super().indication_changed(value)
        if value.is_ok():
            self.edit.setStyleSheet('')
        else:
            self.edit.setStyleSheet('color: red;')


if __name__ == '__main__':
    from fidget.backend.QtWidgets import QApplication

    app = QApplication([])
    w = FidgetLineEdit('sample', pattern='(a[^a]*a|[^a])*', make_plaintext=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
