"""
These are widgets to get a simple string reply. Users should instead use fidget.widgets.Question
"""

from fidget.backend.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QPlainTextEdit
from fidget.backend.QtCore import Qt

from fidget.core.__util__ import link_to
from fidget.core.code_editor import QPyCodeEditor


class PrimitiveQuestion(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit = self.get_edit()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        self.ret: str = None
        self.init_ui()

        @self.ok_btn.clicked.connect
        def ok_clicked(event):
            self.ret = self.get_text()
            self.accept()

        @self.cancel_btn.clicked.connect
        def cancel_clicked(event):
            self.reject()

        self.setWindowModality(Qt.ApplicationModal)

    def init_ui(self):
        master_layout = QVBoxLayout()

        inner_layout = self.inner_layout()
        master_layout.addLayout(inner_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        master_layout.addLayout(btn_layout)

        self.setLayout(master_layout)

        self.setWindowTitle(self.TITLE)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._instance = None

    @classmethod
    def get_edit(cls):
        return QLineEdit()

    def get_text(self):
        return self.edit.text()

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    TITLE: str


class FormatSpecQuestion(PrimitiveQuestion):
    def inner_layout(self):
        ret = QVBoxLayout()
        ret.addWidget(self.edit)
        ret.addWidget(link_to('python format mini-language specifications',
                              r'https://docs.python.org/3/library/string.html#format-specification-mini-language'))
        return ret

    TITLE = 'format specification'


class FormattedStringQuestion(PrimitiveQuestion):
    def inner_layout(self):
        ret = QVBoxLayout()
        ret.addWidget(self.edit)
        ret.addWidget(link_to('python formatted string specifications',
                              r'https://docs.python.org/3/library/string.html#format-string-syntax'))
        return ret
    TITLE = 'formatted string'


class EvalStringQuestion(PrimitiveQuestion):
    def inner_layout(self):
        ret = QHBoxLayout()
        ret.addWidget(link_to('eval("',
                              "https://docs.python.org/3/library/functions.html#eval"))
        ret.addWidget(self.edit)
        ret.addWidget(QLabel('", {"value":value})'))
        return ret
    TITLE = 'eval script'


class ExecStringQuestion(PrimitiveQuestion):
    def inner_layout(self):
        ret = QVBoxLayout()
        ret.addWidget(link_to('exec("def main(value):',
                              "https://docs.python.org/3/library/functions.html#exec"))
        ret.addWidget(self.edit)
        ret.addWidget(QLabel('")\nreturn main(value)'))
        return ret
    TITLE = 'exec script'

    @classmethod
    def get_edit(cls):
        return QPyCodeEditor()

    def get_text(self):
        return self.edit.toPlainText()
