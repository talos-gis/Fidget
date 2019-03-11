from __future__ import annotations

from typing import TypeVar, Generic, Union

from itertools import chain
from functools import wraps, partial

from qtalos.backend.QtWidgets import QCheckBox, QHBoxLayout, QWidget, QApplication
from qtalos.backend.QtCore import QObject, QEvent, __backend__

from qtalos.core import ValueWidget, PlaintextPrintError, none_parser, ValueWidgetTemplate
from qtalos.core.__util__ import first_valid

from qtalos.widgets.widget_wrappers import SingleWidgetWrapper
from qtalos.widgets.__util__ import only_valid

if __backend__.__name__ == 'PySide2':
    import shiboken2

T = TypeVar('T')
C = TypeVar('C')


# todo optional is only valid if none_value is None
class OptionalValueWidget(Generic[T, C], SingleWidgetWrapper[T, Union[T, C]]):
    class MouseWarden(QObject):
        def __init__(self, *args, target, dispatch, **kwargs):
            super().__init__(*args, **kwargs)
            self.target = target
            self.dispatch = dispatch

        def eventFilter(self, obj, event):
            if obj.isWidgetType() and event.type() == QEvent.MouseButtonPress \
                    and self.target in obj.window().findChildren(QWidget) \
                    and self.target.underMouse() and not self.target.isEnabled():
                self.dispatch()
                obj.setFocus()

            if __backend__.__name__ == 'PySide2' and not shiboken2.isValid(obj):
                return False
            return super().eventFilter(obj, event)

    def __init__(self, inner_template: ValueWidgetTemplate[T] = None, default_state=False, layout_cls=None,
                 none_value: C = None,
                 **kwargs):

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        inner_template.extract_default(sink=kwargs, upper_space=self)

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.inner: ValueWidget[T] = None
        self.not_none_checkbox: QCheckBox = None
        self.warden: OptionalValueWidget.MouseWarden = None

        self.none_value = none_value

        self.init_ui(layout_cls)

        self.not_none_checkbox.setChecked(default_state)

    INNER_TEMPLATE: ValueWidgetTemplate[T] = None
    LAYOUT_CLS = QHBoxLayout

    def init_ui(self, layout_cls=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        layout = layout_cls(self)

        with self.setup_provided(layout):
            self.not_none_checkbox = QCheckBox()
            self.not_none_checkbox.toggled.connect(self._not_none_changed)
            layout.addWidget(self.not_none_checkbox)

            self.inner = self.inner_template()
            self.inner.on_change.connect(self.change_value)
            self.inner.setEnabled(False)

            layout.addWidget(self.inner)

        for p in chain(self.inner.provided_pre(),
                       self.inner.provided_post()):
            p.hide()

        self.warden = self.MouseWarden(target=self.inner, dispatch=partial(self.not_none_checkbox.setChecked, True))
        QApplication.instance().installEventFilter(self.warden)

    def parse(self):
        if self.not_none_checkbox.isChecked():
            return self.inner.parse()
        return self.none_value

    def validate(self, v):
        super().validate(v)
        if v is not self.none_value:
            self.inner.validate(v)

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        for ip in self.inner.plaintext_printers():
            if ip in (str, repr):
                continue

            @wraps(ip)
            def wrapper(v):
                if v is self.none_value:
                    raise PlaintextPrintError(f'this printer cannot handle {v!r}')
                return ip(v)

            yield wrapper

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield from self.inner.plaintext_parsers()
        yield none_parser

    def _fill(self, v):
        if v is self.none_value:
            self.not_none_checkbox.setChecked(False)
        else:
            self.not_none_checkbox.setChecked(True)
            self.inner.fill(v)

    @property
    def fill(self):
        return self.inner.fill and self._fill

    def _not_none_changed(self, new_state):
        enable = new_state != 0
        self.inner.setEnabled(enable)
        self.change_value()


@OptionalValueWidget.template_class
class OptionalTemplate(Generic[T], ValueWidgetTemplate[T]):
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
    w = OptionalValueWidget(
        IntEdit.template('source ovr', placeholder=False, make_title=True, make_indicator=True),
    )
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
