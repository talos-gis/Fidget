from typing import Dict, Union, Callable, Any, Type, List

from pathlib import Path
from glob import iglob

from fidget.backend.QtWidgets import QHBoxLayout, QLineEdit, QFileDialog, QPushButton

from fidget.core import Fidget, ValidationError, inner_plaintext_parser, explicit
from fidget.core.__util__ import first_valid

from fidget.widgets.__util__ import RememberingFileDialog

FileDialogArgs = Union[Callable[..., QFileDialog], Dict[str, Any], QFileDialog]


# todo common superclass with FidgetFilePath

class FidgetFilePaths(Fidget[List[Path]]):
    """
    A Fidget to store a Path to a file
    """

    MAKE_INDICATOR = True
    MAKE_PLAINTEXT = False

    def __init__(self, title: str, dialog: FileDialogArgs = None, **kwargs):
        """
        :param title: the title
        :param exist_cond: whether the file must exist (True), or must not exist (False)
        :param dialog: either a QFileDialog, a constructor, or arguments for a QFileDialog.
        :param kwargs: forwarded to Fidget
        """
        super().__init__(title, **kwargs)

        self.dialog: QFileDialog = None
        self.edit: QLineEdit = None

        self.init_ui(dialog)

    DEFAULT_DIALOG_CLS: Type[QFileDialog] = RememberingFileDialog
    DIALOG: FileDialogArgs = RememberingFileDialog

    def init_ui(self, dialog=None):
        super().init_ui()
        self.dialog = self._args_to_filedialog(first_valid(dialog=dialog, DIALOG=self.DIALOG, _self=self))

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
            self.fill_value(self.dialog.selectedFiles())

    def parse(self):
        return [Path(s) for s in self.edit.text().split(';;')]

    def validate(self, value):
        super().validate(value)
        for p in value:
            try:
                exists = p.exists()
            except OSError:
                raise ValidationError('path seems invalid', offender=self.edit)

            if not exists:
                raise ValidationError("path doesn't exists", offender=self.edit)

            if exists \
                    and p.is_dir():
                raise ValidationError('path is a directory', offender=self.edit)

    def fill(self, v: List[Path]):
        self.edit.setText(';;'.join(str(i) for i in v))

    @inner_plaintext_parser
    @explicit
    @staticmethod
    def glob_search(pattern):
        g = iglob(pattern)
        return [Path(i) for i in g]

    @classmethod
    def cls_plaintext_parsers(cls):
        yield Path
        yield from super().cls_plaintext_parsers()

    @classmethod
    def _args_to_filedialog(cls, arg):
        if isinstance(arg, QFileDialog):
            ret = arg
        elif isinstance(arg, dict):
            ret = cls.DEFAULT_DIALOG_CLS(**arg)
        elif callable(arg):
            ret = arg()
        else:
            raise TypeError("can't parse argument as dialog: " + str(arg))
        ret.setFileMode(QFileDialog.ExistingFiles)
        return ret
