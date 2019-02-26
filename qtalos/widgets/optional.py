from typing import Optional, TypeVar, Generic

from itertools import chain
from functools import wraps

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout

from qtalos import ValueWidget, PlaintextPrintError, none_parser

T = TypeVar('T')


class OptionalValueWidget(Generic[T], ValueWidget[Optional[T]]):
    def __init__(self, inner: ValueWidget[T], default_state=False, layout_cls=QHBoxLayout, **kwargs):
        kwargs.setdefault('make_plaintext_button', inner.make_plaintext_button)
        kwargs.setdefault('make_validator_label', inner.make_validator_label)
        kwargs.setdefault('make_title_label', inner.make_title_label)

        super().__init__(inner.title, auto_func=inner.auto_func, **kwargs)

        self.inner = inner
        self.not_none_checkbox: QCheckBox = None

        self.init_ui(layout_cls)

        self.not_none_checkbox.setChecked(default_state)

    def init_ui(self, layout_cls=QHBoxLayout):
        super().init_ui()
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
        return None

    def validate(self, v):
        super().validate(v)
        if v is not None:
            self.inner.validate(v)

    def plaintext_printers(self):
        yield from super().plaintext_printers()
        for ip in self.inner.plaintext_printers():
            if ip in (str, repr):
                continue

            @wraps(ip)
            def wrapper(v):
                if v is None:
                    raise PlaintextPrintError('this printer cannot handle None')
                return ip(v)

            yield wrapper

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield from self.inner.plaintext_parsers()
        yield none_parser

    def _fill(self, v):
        if v is None:
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
        if not self.inner.isEnabled() and self.inner.underMouse():
            self.not_none_checkbox.setChecked(True)
        super().mousePressEvent(a0)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos.widgets import LineEdit

    app = QApplication([])
    w = OptionalValueWidget(LineEdit('sample', pattern='(a[^a]*a|[^a])*'), default_state=False)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
