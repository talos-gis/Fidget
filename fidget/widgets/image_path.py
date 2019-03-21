from pathlib import Path

from fidget.backend.QtWidgets import QVBoxLayout, QLabel
from fidget.backend.QtCore import Qt
from fidget.backend.QtGui import QPixmap

from fidget.core import Fidget
from fidget.core.__util__ import first_valid

from fidget.widgets.converter import FidgetTransparentConverter
from fidget.widgets.file_path import FidgetFilePath


class ImageFilePath(FidgetFilePath):
    DIALOG = {'filter': 'image files (*.png *.jpg *.gif *.bmp);;all files (*.*)'}
    EXIST_COND = True
    MAKE_INDICATOR = False
    MAKE_PLAINTEXT = False


class FidgetImagePath(FidgetTransparentConverter[Path]):
    def __init__(self, title, preview_height = None, preview_width = None, **kwargs):
        template = ImageFilePath.template(title)

        self.preview_label: QLabel = None

        super().__init__(template, **kwargs)

        self.preview_height = first_valid(preview_height = preview_height, PREVIEW_HEIGHT=self.PREVIEW_HEIGHT, _self=self)
        self.preview_width = first_valid(preview_width=preview_width, PREVIEW_WIDTH=self.PREVIEW_WIDTH, _self=self)

    LAYOUT_CLS = QVBoxLayout

    def init_ui(self, *args, **kwargs):
        layout = super().init_ui(*args, **kwargs)
        self.preview_label = QLabel()
        layout.addWidget(self.preview_label)
        self.inner.on_change.connect(self.update_preview)

    _template_class = Fidget._template_class
    PREVIEW_WIDTH = None
    PREVIEW_HEIGHT = None

    def update_preview(self):
        v = self.value()
        if not v.is_ok():
            self.preview_label.setPixmap(None)
        else:
            pixmap = QPixmap(str(v.value))
            if self.preview_width:
                if self.preview_height:
                    pixmap = pixmap.scaled(self.preview_width, self.preview_height, Qt.KeepAspectRatio)
                else:
                    pixmap = pixmap.scaledToWidth(self.preview_width)
            else:
                if self.preview_height:
                    pixmap = pixmap.scaledToHeight(self.preview_height)
            self.preview_label.setPixmap(pixmap)
