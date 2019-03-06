from __future__ import annotations

from typing import Callable, Iterable, Tuple
import json
from functools import wraps

from qtalos.backend import QVBoxLayout, QFrame

from qtalos import ValueWidget, ParseError, ValidationError, InnerPlaintextParser, InnerPlaintextPrinter, \
    PlaintextPrintError, PlaintextParseError
from qtalos.widgets.idiomatic_inner import get_idiomatic_inner_widgets
from qtalos.widgets.__util__ import has_init


class TupleWidget(ValueWidget[Tuple]):
    def __init__(self, title, inner: Iterable[ValueWidget] = None, frame_style=None,
                 layout_cls=..., **kwargs):
        super().__init__(title, **kwargs)
        if (inner is None) == (self.make_inner is None):
            if inner:
                raise Exception('inner provided when make_inner is implemented')
            raise Exception('inner not provided when make_inner is not implemented')

        inner = inner or self.make_inner()
        self.inner = tuple(inner)

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls)

    make_inner: Callable[[TupleWidget], Iterable[ValueWidget]] = None
    default_layout_cls = QVBoxLayout

    def init_ui(self, frame_style=None, layout_cls=...):
        super().init_ui()

        if layout_cls is ...:
            layout_cls = self.default_layout_cls

        master_layout = layout_cls(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            for option in self.inner:
                option.on_change.connect(self.change_value)
                layout.addWidget(option)

        frame.setLayout(layout)
        master_layout.addWidget(frame)

    def parse(self):
        d = []
        for subwidget in self.inner:
            try:
                value = subwidget.parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title) from e
            d.append(value)
        return tuple(d)

    def validate(self, d: Tuple):
        super().validate(d)
        for i, v in enumerate(d):
            subwidget = self.inner[i]
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

        if not isinstance(d, list):
            raise PlaintextParseError(f'json is a {type(d).__name__} instead of list')

        ret = []

        for i, v in enumerate(d):
            if i >= len(self.inner):
                if exact:
                    raise PlaintextParseError(f'too many values (expected {len(self.inner)})')
                continue
            subwidget = self.inner[i]
            if not isinstance(v, str):
                raise PlaintextParseError(f'in index: {i}, value must be str, got {type(v).__name__}')

            try:
                parsed = subwidget.joined_plaintext_parser(v)
            except PlaintextParseError as e:
                raise PlaintextParseError(f'error parsing {subwidget.title}') from e

            ret.append(parsed)

        return tuple(ret)

    @InnerPlaintextParser
    def from_json_wildcard(self, v: str):
        return self.from_json(v, exact=False)

    @InnerPlaintextPrinter
    def to_json(self, d: Tuple):
        ret = []
        for i, subwidget in enumerate(self.inner):
            v = d[i]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {subwidget.title}') from e
            ret.append(s)

        return json.dumps(ret)

    def plaintext_parsers(self):
        if self.fill:
            yield from super().plaintext_parsers()

    def _fill(self, d: Tuple):
        for sw, v in zip(self.inner, d):
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inner):
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
    from qtalos.backend import QApplication, QHBoxLayout
    from qtalos.widgets import IntEdit


    class PointWidget(TupleWidget):
        MAKE_PLAINTEXT = True
        MAKE_INDICATOR = True
        MAKE_TITLE = True

        default_layout_cls = QHBoxLayout

        def make_inner(self):
            yield IntEdit('X', make_indicator=False)
            yield IntEdit('Y', make_indicator=False)


    app = QApplication([])
    w = PointWidget('sample')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
