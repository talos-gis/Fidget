from typing import Optional, Pattern

import re

from PyQt5.QtWidgets import QLineEdit, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser, ValidationError


class LineEdit(ValueWidget[str]):
    def __init__(self, title: str, *args, pattern=None, **kwargs):
        kwargs.setdefault('make_validator_label', pattern is not None)

        super().__init__(title, *args, **kwargs)

        self.pattern: Optional[Pattern[str]] = re.compile(pattern) if pattern else None

        self.edit: QLineEdit = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()
        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
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
        return v

    def fill(self, v : str):
        self.edit.setText(v)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = LineEdit('sample', pattern='(a[^a]*a|[^a])*')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
