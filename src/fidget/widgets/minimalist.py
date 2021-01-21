from __future__ import annotations

from typing import TypeVar, Generic

from fidget.backend.QtWidgets import QHBoxLayout, QPushButton, QBoxLayout, QSizePolicy

from fidget.core import FidgetTemplate, TemplateLike, Fidget
from fidget.core.__util__ import first_valid

from fidget.widgets.__util__ import only_valid
from fidget.widgets.label import FidgetLabel
from fidget.widgets.confirmer import FidgetQuestion
from fidget.widgets.idiomatic_inner import SingleFidgetWrapper

T = TypeVar('T')


# todo document

class FidgetMinimal(Generic[T], SingleFidgetWrapper[T, T]):
    NOT_INITIAL = object()

    def __init__(self, inner_template: TemplateLike[T] = None, outer_template: TemplateLike[T] = None, layout_cls=None,
                 initial_value: T = NOT_INITIAL, **kwargs):
        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE,
                                    _self=self).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template
        self.outer_template = only_valid(outer_template=outer_template,
                                         OUTER_TEMPLATE=self.OUTER_TEMPLATE, _self=self).template_of()

        self.browse_btn: QPushButton = None

        self.question: FidgetQuestion[T] = None
        self.outer: Fidget[T] = None

        self.__value = None

        self.init_ui(layout_cls=layout_cls)

        initial_value = first_valid(initial_value=initial_value, INITIAL_VALUE=self.INITIAL_VALUE,
                                    _invalid=self.NOT_INITIAL, _self=self)

        self.fill_value(initial_value)

    def init_ui(self, layout_cls=None, ok_text=None, cancel_text=None, modality=None,
                pre_widget=None, post_widget=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        layout: QBoxLayout = layout_cls(self)
        with self.setup_provided(layout):
            self.browse_btn = QPushButton('...')
            self.browse_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.browse_btn.clicked.connect(self._browse_btn_clicked)
            layout.addWidget(self.browse_btn)

            self.outer = self.outer_template()
            self.outer.on_change.connect(self.change_value)
            layout.addWidget(self.outer)

            self.question = FidgetQuestion(self.inner_template, parent=self)

        self.outer.add_plaintext_delegates(self.question)

        return layout

    def _browse_btn_clicked(self, event):
        v = self.value()
        if v.is_ok():
            self.question.fill_value(v.value)
        v = self.question.exec_()
        if not v.is_ok():
            return
        value = v.value

        self.fill_value(value)

    def fill(self, value: T):
        self.outer.fill_value(value)

    def parse(self):
        return self.outer.maybe_parse()

    def indication_changed(self, value):
        Fidget.indication_changed(self, value)

    def plaintext_parsers(self):
        yield from self.question.plaintext_parsers()

    def plaintext_printers(self):
        yield from self.question.plaintext_printers()

    INNER_TEMPLATE: FidgetTemplate[T] = None
    OUTER_TEMPLATE: FidgetTemplate[T] = FidgetLabel.template('outer')
    LAYOUT_CLS = QHBoxLayout
    MAKE_INDICATOR = MAKE_PLAINTEXT = False
    INITIAL_VALUE: T = NOT_INITIAL
