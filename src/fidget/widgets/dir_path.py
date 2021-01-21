from typing import Optional, Dict, Union, Callable, Any, Type

from pathlib import Path
from glob import iglob

from fidget.backend.QtWidgets import QHBoxLayout, QLineEdit, QFileDialog, QPushButton

from fidget.core import Fidget, ValidationError, PlaintextParseError, inner_plaintext_parser, explicit
from fidget.core.__util__ import first_valid

from fidget.widgets.__util__ import filename_valid, RememberingFileDialog

FileDialogArgs = Union[Callable[..., QFileDialog], Dict[str, Any], QFileDialog]


# todo superclass with filepath

class FidgetDirPath(Fidget[Path]):
    """
    A Fidget to store a Path to a file
    """

    MAKE_INDICATOR = True
    MAKE_PLAINTEXT = False

    def __init__(self, title: str, exist_cond: Optional[bool] = None, dialog: FileDialogArgs = None, **kwargs):
        """
        :param title: the title
        :param exist_cond: whether the file must exist (True), or must not exist (False)
        :param dialog: either a QFileDialog, a constructor, or arguments for a QFileDialog.
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)
        self.exist_cond = exist_cond if exist_cond is not None else self.EXIST_COND

        self.dialog: QFileDialog = None
        self.edit: QLineEdit = None

        self.init_ui(dialog)

    DEFAULT_DIALOG_CLS: Type[QFileDialog] = RememberingFileDialog
    DIALOG: FileDialogArgs = RememberingFileDialog
    EXIST_COND = None

    def init_ui(self, dialog=None):
        super().init_ui()
        self.dialog = self._args_to_filedialog(first_valid(dialog=dialog, DIALOG=self.DIALOG, _self=self))

        self.dialog.setFileMode(QFileDialog.DirectoryOnly)

        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
            self.edit.textChanged.connect(self.change_value)
            layout.addWidget(self.edit)

            browse_btn = QPushButton('...')
            browse_btn.pressed.connect(self.browse)
            layout.addWidget(browse_btn)

        self.setFocusProxy(self.edit)

        return layout

    def browse(self, *a):
        if self.dialog.exec():
            self.fill_value(self.dialog.selectedFiles()[0])

    def parse(self):
        return Path(self.edit.text())

    def validate(self, value):
        super().validate(value)
        try:
            exists = value.exists()
        except OSError:
            raise ValidationError('path seems invalid', offender=self.edit)

        if exists:
            if self.exist_cond not in (True, None):
                raise ValidationError("path already exists", offender=self.edit)
            # if the file exists, we don't need to check it
        else:
            if self.exist_cond not in (False, None):
                raise ValidationError("path doesn't exists", offender=self.edit)
            # so checking of a filename is valid is stupid complicated, slow, and fallible,
            # https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
            # we're just gonna check for invalid characters
            if not filename_valid(value):
                raise ValidationError('path seems invalid', offender=self.edit)

        if exists \
                and not value.is_dir():
            raise ValidationError('path not is a directory', offender=self.edit)

    def fill(self, v: Path):
        self.edit.setText(str(v))

    @inner_plaintext_parser
    @explicit
    @staticmethod
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

    @classmethod
    def cls_plaintext_parsers(cls):
        yield Path
        yield from super().cls_plaintext_parsers()

    @classmethod
    def _args_to_filedialog(cls, arg):
        if isinstance(arg, QFileDialog):
            return arg
        if isinstance(arg, dict):
            return cls.DEFAULT_DIALOG_CLS(**arg)
        if callable(arg):
            return arg()
