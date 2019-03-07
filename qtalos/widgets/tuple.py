from __future__ import annotations

from typing import Type, Iterable, Tuple, Union, TypeVar, Sequence, Any
import json
from itertools import chain

from qtalos.backend import QVBoxLayout, QFrame, QBoxLayout

from qtalos import ValueWidget, ParseError, ValidationError, InnerPlaintextParser, InnerPlaintextPrinter, \
    PlaintextPrintError, PlaintextParseError, ValueWidgetTemplate, explicit
from qtalos.__util__ import first_valid

from qtalos.widgets.widget_wrappers import MultiWidgetWrapper
from qtalos.widgets.__util__ import only_valid

T = TypeVar('T')
Template = Union[
    ValueWidgetTemplate[T],
    ValueWidget[T]
]


class TupleWidget(MultiWidgetWrapper[Any, Tuple]):
    def __init__(self, title, inner_templates: Iterable[Template] = None, frame_style=None,
                 layout_cls: Type[QBoxLayout] = None, **kwargs):

        self.inner_templates = tuple(
            t.template_of() for t in only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES)
        )
        ValueWidgetTemplate.extract_default(*self.inner_templates, upper_space=self, sink=kwargs)

        super().__init__(title, **kwargs)
        self.inners: Sequence[ValueWidget] = None

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls)

    INNER_TEMPLATES: Iterable[Template] = None
    LAYOUT_CLS: Type[QBoxLayout] = QVBoxLayout

    def init_ui(self, frame_style=None, layout_cls: Type[QBoxLayout] = None):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        master_layout = layout_cls(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            self.inners = []
            for inner_template in self.inner_templates:
                inner = inner_template()
                for p in chain(inner.provided_pre(),
                               inner.provided_post()):
                    p.hide()
                self.inners.append(inner)
                inner.on_change.connect(self.change_value)
                layout.addWidget(inner)

        frame.setLayout(layout)
        master_layout.addWidget(frame)

    def parse(self):
        d = []
        for subwidget in self.inners:
            try:
                value = subwidget.parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title) from e
            d.append(value)
        return tuple(d)

    def validate(self, d: Tuple):
        super().validate(d)
        for i, v in enumerate(d):
            subwidget = self.inners[i]
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
            if i >= len(self.inners):
                if exact:
                    raise PlaintextParseError(f'too many values (expected {len(self.inners)})')
                continue
            subwidget = self.inners[i]
            if not isinstance(v, str):
                raise PlaintextParseError(f'in index: {i}, value must be str, got {type(v).__name__}')

            try:
                parsed = subwidget.joined_plaintext_parser(v)
            except PlaintextParseError as e:
                raise PlaintextParseError(f'error parsing {subwidget.title}') from e

            ret.append(parsed)

        return tuple(ret)

    @explicit
    @InnerPlaintextParser
    def from_json_wildcard(self, v: str):
        return self.from_json(v, exact=False)

    @InnerPlaintextPrinter
    def to_json(self, d: Tuple):
        ret = []
        for i, subwidget in enumerate(self.inners):
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
        for sw, v in zip(self.inners, d):
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inners):
            return None
        return self._fill


if __name__ == '__main__':
    from qtalos.backend import QApplication, QHBoxLayout
    from qtalos.widgets import IntEdit


    class PointWidget(TupleWidget):
        MAKE_PLAINTEXT = True
        MAKE_INDICATOR = True
        MAKE_TITLE = True

        LAYOUT_CLS = QHBoxLayout

        INNER_TEMPLATES = [
            IntEdit.template('X', make_indicator=False),
            IntEdit.template('Y', make_indicator=False)
        ]


    app = QApplication([])
    w = PointWidget('sample')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
