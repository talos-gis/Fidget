from __future__ import annotations

from typing import TypeVar, Generic, Union

from itertools import chain
from functools import wraps, partial

from fidget.core.plaintext_adapter import high_priority

from fidget.backend.QtWidgets import QCheckBox, QHBoxLayout, QWidget, QApplication
from fidget.backend.QtCore import QObject, QEvent, __backend__

from fidget.core import Fidget, PlaintextPrintError, PlaintextParseError, FidgetTemplate
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import SingleFidgetWrapper
from fidget.widgets.__util__ import only_valid, is_trivial_printer

if __backend__.__name__ == 'PySide2':
    import shiboken2

T = TypeVar('T')
C = TypeVar('C')


class FidgetOptional(Generic[T, C], SingleFidgetWrapper[T, Union[T, C]]):
    """
    A Fidget wrapper that allows an inner Fidget to be disabled, setting the value to None or another singleton
    """
    singleton_names = {
        None: frozenset(['none']),
        NotImplemented: frozenset(['notimplemented', 'not implemented']),
        ...: frozenset(['...', 'ellipsis']),
        (): frozenset(['()']),
        0: frozenset(['0']),
        '': frozenset(['""', "''"])
    }

    class MouseWarden(QObject):
        """
        An event filter that enables the disabled inner widget when clicked
        """
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

    def __init__(self, inner_template: FidgetTemplate[T] = None, default_state=False, layout_cls=None,
                 none_value: C = None,
                 **kwargs):
        """
        :param inner_template: the template to wrap
        :param default_state: whether the default value of the widget will be enabled
        :param layout_cls: the layout class
        :param none_value: the value to set when the widget is disabled
        :param kwargs: forwarded to Fidget
        """

        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE, _self=self).template_of()

        inner_template.extract_default(sink=kwargs, upper_space=type(self))

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.inner: Fidget[T] = None
        self.not_none_checkbox: QCheckBox = None
        self.warden: FidgetOptional.MouseWarden = None

        self.none_value = none_value
        none_names = self.singleton_names.get(self.none_value)
        if none_names:
            @high_priority
            def NoneParser(s: str):
                if s.lower() in none_names:
                    return self.none_value
                raise PlaintextParseError(f'this parser only accepts {next(iter(none_names))}')
            self.none_parser = NoneParser
        else:
            self.none_parser = None

        self.init_ui(layout_cls)

        self.not_none_checkbox.setChecked(default_state)

    INNER_TEMPLATE: FidgetTemplate[T] = None
    LAYOUT_CLS = QHBoxLayout

    def init_ui(self, layout_cls=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

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

        return layout

    def parse(self):
        if self.not_none_checkbox.isChecked():
            return self.inner.maybe_parse()
        return self.none_value

    def validate(self, v):
        super().validate(v)
        if v is not self.none_value:
            self.inner.maybe_validate(v)

    def plaintext_printers(self):
        def printer_wrapper(ip):
            @wraps(ip)
            def wrapper(v):
                if v is self.none_value:
                    raise PlaintextPrintError(f'this printer cannot handle {v!r}')
                return ip(v)

            return wrapper

        yield from super().plaintext_printers()
        for ip in self.inner.plaintext_printers():
            if is_trivial_printer(ip):
                continue

            yield printer_wrapper(ip)

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield from self.inner.plaintext_parsers()
        if self.none_parser:
            yield self.none_parser

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


if __name__ == '__main__':
    from fidget.widgets import *

    app = QApplication([])
    w = FidgetOptional(
        FidgetInt.template('source ovr', placeholder=False, make_title=True, make_indicator=True),
    )
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
