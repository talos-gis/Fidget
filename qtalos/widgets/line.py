from typing import Optional, Pattern, Union

import re

from PyQt5.QtWidgets import QLineEdit, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser, ValidationError, PlaintextParseError


class LineEdit(ValueWidget[str]):
    def __init__(self, title: str, *args, pattern: Union[str, Pattern[str]] = None, placeholder=True,
                 **kwargs):
        kwargs.setdefault('make_validator_label', pattern is not None)
        if placeholder:
            kwargs.setdefault('make_title_label', False)

        super().__init__(title, *args, **kwargs)

        provided_pattern = self.make_pattern()
        if provided_pattern and pattern:
            raise Exception('pattern provided when make_pattern is implemented')

        pattern = pattern or provided_pattern

        self.pattern: Optional[Pattern[str]] = re.compile(pattern) if pattern else None

        self.edit: QLineEdit = None

        self.init_ui(placeholder=placeholder and self.title)

    def make_pattern(self) -> Union[str, Pattern[str], None]:
        return None

    def init_ui(self, placeholder=None):
        super().init_ui()
        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
            if placeholder:
                self.edit.setPlaceholderText(placeholder)
            self.edit.textChanged.connect(self.change_value)

            layout.addWidget(self.edit)

    def parse(self):
        return self.edit.text()

    def validate(self, value):
        super().validate(value)
        if self.pattern and not self.pattern.fullmatch(value):
            raise ValidationError(f'value must match pattern {self.pattern}')

    @InnerPlaintextParser
    def raw_text(self, v):
        if self.pattern and not self.pattern.fullmatch(v):
            raise PlaintextParseError('string does not match pattern')
        return v

    def fill(self, v: str):
        self.edit.setText(v)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = LineEdit('sample', pattern='(a[^a]*a|[^a])*')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
