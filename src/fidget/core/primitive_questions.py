"""
These are widgets to get a simple string reply. Users should instead use fidget.widgets.Question
"""

from fidget.backend.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFontComboBox, \
    QSpinBox
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
        super().__init__(*args, **kwargs)

        self.setWindowModality(Qt.ApplicationModal)

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

        self.combo_box = QFontComboBox()
        self.combo_box.setCurrentIndex(-1)
        self.combo_box.currentTextChanged.connect(self._update_preview)
        ret.addWidget(self.combo_box)

        self.size_edit = QSpinBox()
        self.size_edit.setValue(8)
        self.size_edit.setRange(6, 50)
        self.size_edit.valueChanged[int].connect(self._update_preview)
        ret.addWidget(self.size_edit)

        self.preview_label = QLabel('preview\n1234567')
        ret.addWidget(self.preview_label)

        self.default_btn = QPushButton('default')

        @self.default_btn.clicked.connect
        def fill_default(a):
            self.fill(QFontDatabase.systemFont(QFontDatabase.GeneralFont))

        ret.addWidget(self.default_btn)

        self.monospace_btn = QPushButton('monospace')

        @self.monospace_btn.clicked.connect
        def fill_mono(a):
            self.fill(QFontDatabase.systemFont(QFontDatabase.FixedFont))

        ret.addWidget(self.monospace_btn)

        return ret

    def fill(self, font):
        self.combo_box.setCurrentText(font.family())
        self.size_edit.setValue(font.pointSize())

    def _update_preview(self, a):
        font = self.preview_label.font()
        font.setFamily(self.combo_box.currentText())
        font.setPointSize(self.size_edit.value())
        self.preview_label.setFont(font)

    def get_value(self):
        family = self.combo_box.currentText()
        size = self.size_edit.value()
        return family, size
