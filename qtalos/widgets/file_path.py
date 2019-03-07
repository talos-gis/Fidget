from typing import Optional

from pathlib import Path
from glob import iglob

from qtalos.backend import QHBoxLayout, QLineEdit, QFileDialog, QPushButton

from qtalos import ValueWidget, ValidationError, PlaintextParseError

from qtalos.widgets.__util__ import filename_valid


def glob_search(pattern):
    i = iglob(pattern)
    try:
        ret = next(i)
    except StopIteration as e:
        raise PlaintextParseError('no paths match pattern') from e

    try:
        next(i)
    except StopIteration:
        pass
    else:
        raise PlaintextParseError('multiple paths match pattern')

    return Path(ret)


class FilePathWidget(ValueWidget[Path]):
    MAKE_INDICATOR = True
    MAKE_PLAINTEXT = False

    def __init__(self, title: str, parent=None, flags=None, exist_cond: Optional[bool] = True,
                 dialog: QFileDialog = ..., **kwargs):
        super().__init__(title, parent=parent, flags=flags, **kwargs)
        self.exist_cond = exist_cond

        self.dialog: QFileDialog = None
        self.edit: QLineEdit = None

        self.init_ui(dialog)

    def init_ui(self, dialog=...):
        super().init_ui()
        if dialog is ...:
            dialog = QFileDialog()
        self.dialog = dialog

        if self.exist_cond:
            self.dialog.setFileMode(QFileDialog.ExistingFile)
        else:
            self.dialog.setFileMode(QFileDialog.AnyFile)

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
            self.edit.textChanged.connect(self.change_value)
            layout.addWidget(self.edit)

            browse_btn = QPushButton('...')
            browse_btn.pressed.connect(self.browse)
            layout.addWidget(browse_btn)

    def browse(self, *a):
        # todo the dialog doesn't stick to a directory
        if self.dialog.exec():
            self.fill(self.dialog.selectedFiles()[0])

    def parse(self):
        return Path(self.edit.text())

    def validate(self, value):
        super().validate(value)
        try:
            exists = value.exists()
        except OSError:
            raise ValidationError('path seems invalid')

        if exists:
            if self.exist_cond not in (True, None):
                raise ValidationError("path already exists")
            # if the file exists, we don't need to check it
        else:
            if self.exist_cond not in (False, None):
                raise ValidationError("path doesn't exists")
            # so checking of a filename is valid is stupid complicated, slow, and fallible,
            # https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
            # we're just gonna check for invalid characters
            if not filename_valid(value):
                raise ValidationError('path seems invalid')

        if exists \
                and value.is_dir():
            raise ValidationError('path is a directory')

    def fill(self, v: Path):
        self.edit.setText(str(v))

    def plaintext_parsers(self):
        yield Path
        yield glob_search
        yield from super().plaintext_parsers()


if __name__ == '__main__':
    from qtalos.backend import QApplication

    app = QApplication([])
    w = FilePathWidget('sample', make_title=True, make_plaintext=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
