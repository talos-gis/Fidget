from __future__ import annotations

from typing import TypeVar, Generic, Union, Callable

from qtalos.backend.QtWidgets import QHBoxLayout, QApplication, QPushButton, QVBoxLayout, QBoxLayout

from qtalos.core import ValueWidget, ValueWidgetTemplate, ParseError
from qtalos.core.__util__ import first_valid

from qtalos.widgets.widget_wrappers import SingleWidgetWrapper
from qtalos.widgets.__util__ import only_valid

T = TypeVar('T')
F = TypeVar('F')
C = TypeVar('C')


class ConfirmValueWidget(Generic[F, T, C], SingleWidgetWrapper[F, Union[T, C]]):
    def __init__(self, inner_template: ValueWidgetTemplate[F] = None, layout_cls=None, make_cancel=None,
                 cancel_value: C = None, converter_func: Callable[[F], T] = None,
                 **kwargs):

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.make_cancel = first_valid(make_cancel=make_cancel, MAKE_CANCEL=self.MAKE_CANCEL)

        self.converter_func = converter_func

        self.inner_template = inner_template

        self.inner: ValueWidget[T] = None
        self.ok_button: QPushButton = None
        self.cancel_button: QPushButton = None

        self.cancel_value = cancel_value
        self.cancel_flag = False

        self.init_ui(layout_cls)

    INNER_TEMPLATE: ValueWidgetTemplate[T] = None
    LAYOUT_CLS = QVBoxLayout
    MAKE_CANCEL = False
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = False

    def init_ui(self, layout_cls=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        layout: QBoxLayout = layout_cls(self)

        self.inner = self.inner_template()

        with self.setup_provided(layout):
            self.inner.on_change.connect(self._inner_changed)

            layout.addWidget(self.inner)

            btn_layout = QHBoxLayout()
            if self.make_cancel:
                self.cancel_button = QPushButton('Cancel')
                self.cancel_button.clicked.connect(self._cancel_btn_clicked)
                btn_layout.addWidget(self.cancel_button)

            self.ok_button = QPushButton('Ok')
            self.ok_button.clicked.connect(self._ok_btn_clicked)
            btn_layout.addWidget(self.ok_button)

            layout.addLayout(btn_layout)

    def parse(self):
        if self.cancel_flag:
            return self.cancel_value
        state, value, _ = self.inner.value()
        if not state.is_ok():
            raise ParseError(...) from value
        return self.convert(value)

    def convert(self, v: F) -> T:
        if not self.converter_func:
            raise Exception('a converter function must be provided')
        return self.converter_func(v)

    def _inner_changed(self):
        state, _, _ = self.inner.value()
        self.ok_button.setEnabled(state.is_ok())

    def _ok_btn_clicked(self, *a):
        self.cancel_flag = False
        self.change_value()

    def _cancel_btn_clicked(self, *a):
        self.cancel_flag = True
        self.change_value()


@ConfirmValueWidget.template_class
class ConfirmTemplate(Generic[T], ValueWidgetTemplate[T]):
    @property
    def title(self):
        it = self._inner_template()
        if it:
            return it.title
        return super().title

    def _inner_template(self):
        if self.widget_cls.INNER_TEMPLATE:
            return self.widget_cls.INNER_TEMPLATE
        if self.args:
            return self.args[0].template_of()
        return None


if __name__ == '__main__':
    from qtalos.widgets import *

    app = QApplication([])
    w = ConfirmValueWidget(
        IntEdit.template('source ovr', placeholder=False, make_title=True, make_indicator=True),
        converter_func=lambda x: x * x, make_cancel=True
    )
    w.on_change.connect(lambda: print(w.value()))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
