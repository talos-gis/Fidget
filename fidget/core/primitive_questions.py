"""
These are widgets to get a simple string reply. Users should instead use fidget.widgets.Question
"""

from fidget.backend.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox
from fidget.backend.QtCore import Qt
from fidget.backend.QtGui import QFontDatabase

from fidget.core.__util__ import link_to
from fidget.core.code_editor import QPyCodeEditor


class PrimitiveQuestion(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")
        self.ret: str = None

        @self.ok_btn.clicked.connect
        def ok_clicked(event):
            self.ret = self.get_value()
            self.accept()

        @self.cancel_btn.clicked.connect
        def cancel_clicked(event):
            self.reject()

        self.setWindowModality(Qt.ApplicationModal)
        self.init_ui()

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
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    TITLE: str


class PrimitiveTextQuestion(PrimitiveQuestion):
    def __init__(self, *args, **kwargs):
        self.edit = self.get_edit()

        self.setWindowModality(Qt.ApplicationModal)
        super().__init__(*args, **kwargs)

    @classmethod
    def get_edit(cls):
        return QLineEdit()

    def get_value(self):
        return self.edit.text()


class FormatSpecQuestion(PrimitiveTextQuestion):
    def inner_layout(self):
        ret = QVBoxLayout()
        ret.addWidget(self.edit)
        ret.addWidget(link_to('python format mini-language specifications',
                              r'https://docs.python.org/3/library/string.html#format-specification-mini-language'))
        return ret

    TITLE = 'format specification'


class FormattedStringQuestion(PrimitiveTextQuestion):
    def inner_layout(self):
        ret = QVBoxLayout()
        ret.addWidget(self.edit)
        ret.addWidget(link_to('python formatted string specifications',
                              r'https://docs.python.org/3/library/string.html#format-string-syntax'))
        return ret

    TITLE = 'formatted string'


class EvalStringQuestion(PrimitiveTextQuestion):
    def inner_layout(self):
        ret = QHBoxLayout()
        ret.addWidget(link_to('eval("',
                              "https://docs.python.org/3/library/functions.html#eval"))
        ret.addWidget(self.edit)
        ret.addWidget(QLabel('", {"value":value})'))
        return ret

    TITLE = 'eval script'


class ExecStringQuestion(PrimitiveTextQuestion):
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

    def get_value(self):
        return self.edit.toPlainText()


class FontQuestion(PrimitiveQuestion):
    TITLE = 'choose font'

    def inner_layout(self):
        ret = QHBoxLayout()

        self.combo_box = QComboBox()
        for f in QFontDatabase().families():
            self.combo_box.addItem(f)
        self.combo_box.setCurrentIndex(-1)
        ret.addWidget(self.combo_box)

        self.size_edit = QLineEdit()
        self.size_edit.setPlaceholderText('size')
        ret.addWidget(self.size_edit)

        return ret

    def get_value(self):
        family = self.combo_box.currentText()
        size = None
        try:
            size = int(self.size_edit.text())
        except ValueError:
            pass
        return family, size
