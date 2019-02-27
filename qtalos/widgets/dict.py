from __future__ import annotations

from typing import Callable, Union, Mapping, Iterable, Tuple
import json
from functools import wraps

from PyQt5.QtWidgets import QVBoxLayout, QFrame, QScrollArea
from PyQt5.QtCore import Qt

from qtalos import ValueWidget, ParseError, ValidationError, InnerPlaintextParser, InnerPlaintextPrinter, \
    PlaintextPrintError, PlaintextParseError
from qtalos.widgets.idiomatic_inner import get_idiomatic_inner_widgets
from qtalos.widgets.__util__ import has_init


class DictWidget(ValueWidget[Mapping[str, object]]):
    def __init__(self, title, inner: Iterable[Union[ValueWidget, Tuple[str, ValueWidget]]] = None, frame_style=None,
                 layout_cls=..., scrollable=False, **kwargs):
        super().__init__(title, **kwargs)
        if (inner is None) == (self.make_inner is None):
            if inner:
                raise Exception('inner provided when make_inner is implemented')
            raise Exception('inner not provided when make_inner is not implemented')

        inner = inner or self.make_inner()
        self.inner = dict(self._to_name_subwidget(o) for o in inner)

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls, scrollable=scrollable)

    make_inner: Callable[[DictWidget], Iterable[Union[ValueWidget, Tuple[str, ValueWidget]]]] = None
    default_layout_cls = QVBoxLayout

    def init_ui(self, frame_style=None, layout_cls=..., scrollable=False):
        super().init_ui()

        if layout_cls is ...:
            layout_cls = self.default_layout_cls

        owner = self
        if scrollable:
            owner = QScrollArea(self)
            owner.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            owner.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        master_layout = layout_cls(owner)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            for name, option in self.inner.items():
                option.on_change.connect(self.change_value)
                layout.addWidget(option)

        frame.setLayout(layout)
        master_layout.addWidget(frame)


        #owner.setLayout(master_layout)

    @staticmethod
    def _to_name_subwidget(option: Union[ValueWidget, Tuple[str, ValueWidget]]) -> Tuple[str, ValueWidget]:
        try:
            a, b = option
        except TypeError:
            return option.title, option
        return a, b

    def parse(self):
        d = {}
        for key, subwidget in self.inner.items():
            try:
                value = subwidget.parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title) from e
            d[key] = value
        return d

    def validate(self, d: Mapping[str, object]):
        super().validate(d)
        for k, v in d.items():
            subwidget = self.inner[k]
            try:
                subwidget.validate(v)
            except ValidationError as e:
                raise ValidationError('error validating ' + subwidget.title) from e

    @InnerPlaintextParser
    def from_json(self, v: str, exact=True):
        try:
            d = json.loads(v)
        except json.JSONDecodeError as e:
            raise PlaintextParseError(...) from e

        if not isinstance(d, dict):
            raise PlaintextParseError(f'json is a {type(d).__name__} instead of dict')

        ret = {}

        for k, v in d.items():
            subwidget = self.inner.get(k)
            if not subwidget:
                if exact:
                    raise PlaintextParseError(f'key {k} has no appropriate widget')
                continue
            if not isinstance(v, str):
                raise PlaintextParseError(f'in key: {k}, value must be str, got {type(v).__name__}')

            try:
                parsed = subwidget.joined_plaintext_parser(v)
            except PlaintextParseError as e:
                raise PlaintextParseError(f'error parsing {k}') from e

            ret[k] = parsed

        return ret

    @InnerPlaintextParser
    def from_json_wildcard(self, v: str):
        return self.from_json(v, exact=False)

    @InnerPlaintextPrinter
    def to_json(self, d: Mapping[str, object]):
        ret = {}
        for k, subwidget in self.inner.items():
            v = d[k]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {k}') from e
            ret[k] = s

        return json.dumps(ret)

    def plaintext_parsers(self):
        if self.fill:
            yield from super().plaintext_parsers()

    def _fill(self, d: Mapping[str, object]):
        for k, v in d.items():
            sw = self.inner[k]
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inner.values()):
            return None
        return self._fill

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        idiomatic_inners = list(get_idiomatic_inner_widgets(cls))
        if idiomatic_inners:
            if has_init(cls):
                raise Exception('cannot define idiomatic inner classes inside a class with an __init__')

            @wraps(cls.__init__)
            def __init__(self, *args, **kwargs):
                return super(cls, self).__init__(*args, inners=idiomatic_inners, **kwargs)

            cls.__init__ = __init__


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos.widgets import *


    class PointWidget(DictWidget):
        def make_inner(self):
            yield FloatEdit('X', make_validator_label=False)
            yield FloatEdit('Y', make_validator_label=False)
            yield OptionalValueWidget(FloatEdit('Z', make_validator_label=False))


    app = QApplication([])
    w = PointWidget('sample', make_plaintext_button=True, scrollable=False)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
