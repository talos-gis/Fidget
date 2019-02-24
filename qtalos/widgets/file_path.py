from typing import Optional

from pathlib import Path

from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QFileDialog, QLabel, QPushButton

from qtalos import ValueWidget
from qtalos.__util__ import filename_valid


class FilePathEditWidget(ValueWidget[Path]):
    def __init__(self, title: str, parent=None, flags=None, exist_cond: Optional[bool] = True,
                 **kwargs):
        super().__init__(title, parent=parent, flags=flags)
        self.exist_cond = exist_cond

        self.dialog: QFileDialog = None
        self.edit: QLineEdit = None

        self.init_ui(**kwargs)

    def init_ui(self, **kwargs):
        super().init_ui()
        self.dialog = QFileDialog(self, **kwargs)

        if self.exist_cond:
            self.dialog.setFileMode(QFileDialog.ExistingFile)
        else:
            self.dialog.setFileMode(QFileDialog.AnyFile)

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(self.title))

        self.edit = QLineEdit()
        self.edit.textChanged.connect(self.change_value)
        layout.addWidget(self.edit)

        browse_btn = QPushButton('...')
        browse_btn.pressed.connect(self.browse)
        layout.addWidget(browse_btn)

        if self.validation_label:
            layout.addWidget(self.validation_label)
        if self.auto_button:
            layout.addWidget(self.auto_button)
        if self.help_button:
            layout.addWidget(self.help_button)

    def browse(self, *args, **kwargs):
        if self.dialog.exec():
            self.edit.setText(self.dialog.selectedFiles()[0])

    def parse(self):
        return Path(self.edit.text())

    def validate(self, value):
        super().validate(value)
        try:
            exists = value.exists()
        except OSError:
            raise self.parse_exception('path seems invalid')

        if exists:
            if self.exist_cond not in (True, None):
                raise self.validation_exception(value, "path already exists")
            # if the file exists, we don't need to check it
        else:
            if self.exist_cond not in (False, None):
                raise self.validation_exception(value, "path doesn't exists")
            # so checking of a filename is valid is stupid complicated, slow, and fallible,
            # https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
            # we're just gonna check for invalid characters
            if not filename_valid(value):
                raise self.validation_exception(value, 'path seems invalid')

        if exists \
                and value.is_dir():
            raise self.validation_exception(value, 'path is a directory')


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    print(Path('.').absolute())

    app = QApplication([])
    w = FilePathEditWidget('sample')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
