from __future__ import annotations

from typing import Union, Mapping, Iterable, Tuple, TypeVar, Dict, Any

from fidget.backend.QtWidgets import QVBoxLayout, QTabWidget, QWidget
from fidget.backend.Resources import ok_icon, error_icon

from fidget.core import Fidget, ParseError, ValidationError, inner_plaintext_parser, inner_plaintext_printer, \
    PlaintextPrintError, PlaintextParseError, FidgetTemplate, explicit, json_parser, TemplateLike, json_printer

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T')
NamedTemplate = Union[
    TemplateLike[T], Tuple[str, TemplateLike[T]]
]

# todo document

class FidgetTabs(MultiFidgetWrapper[Any, Mapping[str, Any]]):
    def __init__(self, title, inner_templates: Iterable[NamedTemplate] = None, **kwargs):
        inner_templates = dict(
            self._to_name_subtemplate(o) for o in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES, _self=self)
        )

        FidgetTemplate.extract_default(*inner_templates.values(), sink=kwargs, upper_space=self)

        super().__init__(title, **kwargs)
        self.tabbed: QTabWidget = None
        self.summary_layout = None

        self.inner_templates = inner_templates

        self.inners: Dict[str, Fidget] = None

        self.init_ui()

    INNER_TEMPLATES: Iterable[NamedTemplate] = None

    def init_ui(self):
        super().init_ui()

        layout = QVBoxLayout()

        self.tabbed = QTabWidget()
        self.summary_layout = QVBoxLayout()

        self.inners = {}
        for name, template in self.inner_templates.items():
            inner = template.set_default(make_title = False)()

            if self.inners.setdefault(name, inner) is not inner:
                raise TypeError(f'duplicate inner name: {name}')
            inner.on_change.connect(self.change_value)
            self.tabbed.addTab(inner, inner.title)

        with self.setup_provided(self.summary_layout):
            pass
        if self.summary_layout.count():
            summary = QWidget()
            summary.setLayout(self.summary_layout)
            self.tabbed.addTab(summary, 'summary')
        else:
            self.summary_layout = None

        if not self.inners:
            raise ValueError('at least one inner fidget must be provided')
        self.setFocusProxy(
            next(iter(self.inners.values()))
        )

        layout.addWidget(self.tabbed)
        self.setLayout(layout)

        return layout

    @staticmethod
    def _to_name_subtemplate(option: NamedTemplate) -> Tuple[str, FidgetTemplate[T]]:
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
                raise ParseError('error parsing ' + subwidget.title, offender=subwidget) from e
            d[key] = value
        return d

    def validate(self, d: Mapping[str, object]):
        super().validate(d)
        for k, v in d.items():
            subwidget = self.inners[k]
            try:
                subwidget.validate(v)
            except ValidationError as e:
                raise ValidationError('error validating ' + subwidget.title, offender=subwidget) from e

    @inner_plaintext_parser
    @json_parser(dict)
    def from_json(self, d: dict, exact=True):
        not_seen = dict(self.inners)

        ret = {}

        for k, v in d.items():
            subwidget = not_seen.pop(k, None)
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

        if exact and not_seen:
            k, _ = not_seen.popitem()
            raise PlaintextParseError(f'key not found: {k}') from KeyError(k)

        return ret

    @explicit
    @inner_plaintext_parser
    def from_json_wildcard(self, v: str):
        return self.from_json(v, exact=False)

    @inner_plaintext_printer
    @json_printer
    def to_json(self, d: Mapping[str, object]):
        ret = {}
        for k, subwidget in self.inners.items():
            v = d[k]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {k}') from e
            ret[k] = s
        return ret

    def _fill(self, d: Mapping[str, object]):
        for k, v in d.items():
            sw = self.inners[k]
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inners.values()):
            return None
        return self._fill

    def indication_changed(self, value):
        if self.summary_layout:
            icon = ok_icon if value.is_ok() else error_icon
            self.tabbed.setTabIcon(len(self.inners), icon())

