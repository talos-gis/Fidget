from __future__ import annotations

from typing import Optional, TypeVar, Generic, Callable

from itertools import chain
from functools import wraps

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout

from qtalos import ValueWidget, PlaintextPrintError, none_parser
from qtalos.widgets.idiomatic_inner import get_idiomatic_inner_widgets
from qtalos.widgets.__util__ import has_init

T = TypeVar('T')


class OptionalValueWidget(Generic[T], ValueWidget[Optional[T]]):
    def __init__(self, inner: ValueWidget[T] = None, default_state=False, layout_cls=..., none_value=None, **kwargs):
        if (inner is None) == (self.make_inner is None):
            if inner:
                raise Exception('inner provided when make_inner is implemented')
            raise Exception('inner not provided when make_inner is not implemented')

        inner = inner or self.make_inner()

        kwargs.setdefault('make_plaintext_button', inner.make_plaintext_button)
        kwargs.setdefault('make_validator_label', inner.make_validator_label)
        kwargs.setdefault('make_title_label', inner.make_title_label)

        super().__init__(inner.title, auto_func=inner.auto_func, **kwargs)

        self.inner = inner
        self.not_none_checkbox: QCheckBox = None

        self.none_value = none_value

        self.init_ui(layout_cls)

        self.not_none_checkbox.setChecked(default_state)

    make_inner: Callable[[OptionalValueWidget[T]], ValueWidget[T]] = None
    default_layout_cls = QHBoxLayout

    def init_ui(self, layout_cls=...):
        super().init_ui()
        if layout_cls is ...:
            layout_cls = self.default_layout_cls

        layout = layout_cls(self)

        for p in chain(self.inner.provided_pre(),
                       self.inner.provided_post()):
            p.hide()

        with self.setup_provided(layout):
            self.not_none_checkbox = QCheckBox()
            self.not_none_checkbox.toggled.connect(self._not_none_changed)
            layout.addWidget(self.not_none_checkbox)

            self.inner.on_change.connect(self.change_value)
            self.inner.setEnabled(False)

            layout.addWidget(self.inner)

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

    def mousePressEvent(self, a0):
        # todo this solution has a bunch of problems
        if not self.inner.isEnabled() and self.inner.underMouse():
            self.not_none_checkbox.setChecked(True)
            self.inner.setFocus()
        super().mousePressEvent(a0)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = list(get_idiomatic_inner_widgets(cls))
        if idiomatic_inners:
            if has_init(cls):
                raise Exception('cannot define idiomatic inner classes inside a class with an __init__')

            if len(idiomatic_inners) != 1:
                raise Exception('OptionalValueWidget can only have 1 idiomatic inner class')

            inner_cls, = idiomatic_inners

            @wraps(cls.__init__)
            def __init__(self, *args, **kwargs):
                return super(cls, self).__init__(inner_cls(*args, **kwargs))

            cls.__init__ = __init__


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos.widgets import *

    app = QApplication([])
    #w = OptionalValueWidget(LineEdit('sample', pattern='(a[^a]*a|[^a])*'), default_state=False)
    #w = OptionalValueWidget(FilePathWidget('t'))
    w = OptionalValueWidget(IntEdit('source ovr', placeholder=False))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
