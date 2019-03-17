from __future__ import annotations

from typing import Union, Mapping, Iterable, Tuple, TypeVar, Dict, Type, Any

from fidget.backend.QtWidgets import QVBoxLayout, QFrame, QScrollArea, QWidget, QBoxLayout

from fidget.core import Fidget, ParseError, ValidationError, inner_plaintext_parser, inner_plaintext_printer, \
    PlaintextPrintError, PlaintextParseError, FidgetTemplate, explicit, json_parser, TemplateLike, json_printer
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T')
NamedTemplate = Union[
    TemplateLike[T], Tuple[str, TemplateLike[T]]
]


class FidgetDict(MultiFidgetWrapper[Any, Mapping[str, Any]]):
    """
    A Fidget that wraps multiple Fidgets into a dict with str keys
    """
    def __init__(self, title, inner_templates: Iterable[NamedTemplate] = None, frame_style=None,
                 layout_cls: Type[QBoxLayout] = None, scrollable=None, **kwargs):
        """
        :param title: the title
        :param inner_templates: an iterable of name-templates to act as key-value pairs
        :param frame_style: the frame style to apply to the encompassing frame, if any
        :param layout_cls: the class of the layout
        :param scrollable: whether to make the widget scrollable
        :param kwargs: forwarded to Fidget
        """

        inner_templates = dict(
            self._to_name_subtemplate(o) for o in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES)
        )

        FidgetTemplate.extract_default(*inner_templates.values(), sink=kwargs, upper_space=self)

        super().__init__(title, **kwargs)

        self.inner_templates = inner_templates

        self.inners: Dict[str, Fidget] = None

        frame_style = frame_style or self.FRAME_STYLE

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls, scrollable=scrollable)

    INNER_TEMPLATES: Iterable[NamedTemplate] = None
    LAYOUT_CLS = QVBoxLayout
    FRAME_STYLE = None
    SCROLLABLE = True

    def init_ui(self, frame_style=None, layout_cls=None, scrollable=None):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        owner = self
        scrollable = first_valid(scrollable=scrollable, SCROLLABLE=self.SCROLLABLE)

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
