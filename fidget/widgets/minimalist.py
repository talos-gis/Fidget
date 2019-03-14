from __future__ import annotations

from typing import TypeVar, Generic

from fidget.backend.QtWidgets import QHBoxLayout, QPushButton, QBoxLayout, QLabel

from fidget.core import FidgetTemplate, TemplateLike, PlaintextPrintError
from fidget.core.__util__ import first_valid, error_tooltip

from fidget.widgets.__util__ import only_valid
from fidget.widgets.confirmer import FidgetQuestion
from fidget.widgets.idiomatic_inner import SingleFidgetWrapper

T = TypeVar('T')


# todo document

class FidgetMinimal(Generic[T], SingleFidgetWrapper[T, T]):
    NOT_INITIAL = object()

    def __init__(self, inner_template: TemplateLike[T] = None, layout_cls=None, initial_value: T = NOT_INITIAL,
                 printer=None, **kwargs):
        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.question: FidgetQuestion[T] = None
        self.browse_btn: QPushButton = None
        self.label: QLabel = None

        self.__value = None

        self.init_ui(layout_cls=layout_cls)

        initial_value = first_valid(initial_value=initial_value, INITIAL_VALUE=self.INITIAL_VALUE,
                                    _invalid=self.NOT_INITIAL)
        self.printer = first_valid(printer=printer, PRINTER=self.PRINTER)
        self.fill(initial_value)

    def init_ui(self, layout_cls=None, ok_text=None, cancel_text=None, modality=None,
                pre_widget=None, post_widget=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        layout: QBoxLayout = layout_cls(self)
        with self.setup_provided(layout):
            self.label = QLabel('<no value>')
            layout.addWidget(self.label)

            self.browse_btn = QPushButton('...')
            self.browse_btn.clicked.connect(self._browse_btn_clicked)
            layout.addWidget(self.browse_btn)

        self.question = FidgetQuestion(self.inner_template, cancel_value=self.NOT_INITIAL)

    def _browse_btn_clicked(self, event):
        v = self.question.exec_()
        if not v.is_ok():
            return
        value = v.value
        if value is self.NOT_INITIAL:
            return
        self.fill(value)

    def fill(self, value: T):
        self.__value = value

        printer = self.printer
        if printer is ...:
            printer = self.question.inner.joined_plaintext_printer

        try:
            t = printer(value)
        except PlaintextPrintError as e:
            t = error_tooltip(e)

        self.label.setText(t)
        self.change_value()

    def parse(self):
        return self.__value

    INNER_TEMPLATE: FidgetTemplate[T] = None
    LAYOUT_CLS = QHBoxLayout
    MAKE_INDICATOR = MAKE_PLAINTEXT = False
    INITIAL_VALUE: T = NOT_INITIAL
    PRINTER = ...
