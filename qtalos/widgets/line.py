from typing import Optional, Pattern

import re

from PyQt5.QtWidgets import QLineEdit, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser


class LineEdit(ValueWidget[str]):
    def __init__(self, title: str, *args, pattern=None, **kwargs):
        super().__init__(title, *args, **kwargs)

        self.pattern: Optional[Pattern[str]] = re.compile(pattern) if pattern else None

        self.edit: QLineEdit = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()
        layout = QHBoxLayout(self)
        self.edit = QLineEdit()
        self.edit.textChanged.connect(self.change_value)

        layout.addWidget(self.edit)

        if self.validation_label:
            layout.addWidget(self.validation_label)
        if self.auto_button:
            layout.addWidget(self.auto_button)
        if self.help_button:
            layout.addWidget(self.help_button)

    def parse(self):
        return self.edit.text()

    def validate(self, value):
        super().validate(value)
        if self.pattern and not self.pattern.fullmatch(value):
            raise self.validation_exception(value, f'value must match pattern {self.pattern}')

    @InnerPlaintextParser
    def raw_text(self, v):
        return v

    def fill(self, v):
        self.edit.setText(v)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = LineEdit('sample', pattern='(a[^a]*a|[^a])*')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
