from __future__ import annotations

from typing import Union, Mapping, Iterable, Tuple, TypeVar, Dict, Type, Any
import json

from qtalos.backend.QtWidgets import QVBoxLayout, QFrame, QScrollArea, QWidget, QBoxLayout

from qtalos.core import ValueWidget, ParseError, ValidationError, InnerPlaintextParser, InnerPlaintextPrinter, \
    PlaintextPrintError, PlaintextParseError, ValueWidgetTemplate, explicit
from qtalos.core.__util__ import first_valid

from qtalos.widgets.widget_wrappers import MultiWidgetWrapper
from qtalos.widgets.__util__ import only_valid

T = TypeVar('T')
NamedTemplate = Union[
    ValueWidgetTemplate[T], Tuple[str, ValueWidgetTemplate[T]],
    ValueWidget[T], Tuple[str, ValueWidget[T]]
]


class DictWidget(MultiWidgetWrapper[Any, Mapping[str, Any]]):
    def __init__(self, title, inner_templates: Iterable[NamedTemplate] = None, frame_style=None,
                 layout_cls: Type[QBoxLayout] = None, scrollable=False, **kwargs):

        inner_templates = dict(
            self._to_name_subtemplate(o) for o in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES)
        )

        ValueWidgetTemplate.extract_default(*inner_templates.values(), sink=kwargs, upper_space=self)

        super().__init__(title, **kwargs)

        self.inner_templates = inner_templates

        self.inners: Dict[str, ValueWidget] = None

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls, scrollable=scrollable)

    INNER_TEMPLATES: Iterable[NamedTemplate] = None
    LAYOUT_CLS = QVBoxLayout

    def init_ui(self, frame_style=None, layout_cls=None, scrollable=False):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        owner = self
        if scrollable:
            owner_layout = QVBoxLayout()
            owner.setLayout(owner_layout)

            owner = QScrollArea(owner)
            owner.setWidgetResizable(True)
            owner_layout.addWidget(owner)

        master = QWidget()
        master_layout = layout_cls(master)

        if scrollable:
            owner.setWidget(master)
        else:
            master.setParent(owner)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls(frame)

        self.inners = {}
        with self.setup_provided(master_layout, layout):
            for name, template in self.inner_templates.items():
                inner = template()

                if self.inners.setdefault(name, inner) is not inner:
                    raise TypeError(f'duplicate inner name: {name}')
                inner.on_change.connect(self.change_value)
                layout.addWidget(inner)

        master_layout.addWidget(frame)

    @staticmethod
    def _to_name_subtemplate(option: NamedTemplate) -> Tuple[str, ValueWidgetTemplate[T]]:
        try:
            template = option.template_of()
        except AttributeError:
            name, option = option
            option = option.template_of()
            return name, option

        if not template.title:
            raise ValueError(f'stacked option {option} must be ')
        return template.title, template

    def parse(self):
        d = {}
        for key, subwidget in self.inners.items():
            try:
                value = subwidget.parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title) from e
            d[key] = value
        return d

    def validate(self, d: Mapping[str, object]):
        super().validate(d)
        for k, v in d.items():
            subwidget = self.inners[k]
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
            subwidget = self.inners.get(k)
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

    @explicit
    @InnerPlaintextParser
    def from_json_wildcard(self, v: str):
        return self.from_json(v, exact=False)

    @InnerPlaintextPrinter
    def to_json(self, d: Mapping[str, object]):
        ret = {}
        for k, subwidget in self.inners.items():
            v = d[k]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {k}') from e
            ret[k] = s

        try:
            return json.dumps(ret)
        except TypeError as e:
            raise PlaintextPrintError(...) from e

    def plaintext_parsers(self):
        if self.fill:
            yield from super().plaintext_parsers()

    def _fill(self, d: Mapping[str, object]):
        for k, v in d.items():
            sw = self.inners[k]
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inners.values()):
            return None
        return self._fill


if __name__ == '__main__':
    from qtalos.backend import QApplication
    from qtalos.widgets import *


    class PointWidget(DictWidget):
        MAKE_PLAINTEXT = True
        MAKE_TITLE = True
        MAKE_INDICATOR = True

        INNER_TEMPLATES = [
            FloatEdit.template('X'),
            FloatEdit.template('Y'),
            OptionalValueWidget.template(
                FloatEdit.template('Z', make_indicator=False, make_title=False)),
        ]


    app = QApplication([])
    w = PointWidget('sample', scrollable=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
