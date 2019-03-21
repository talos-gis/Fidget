from __future__ import annotations

from typing import Type, Iterable, Tuple, Sequence, Any, NamedTuple

from collections import namedtuple

from fidget.backend.QtWidgets import QVBoxLayout, QFrame, QBoxLayout

from fidget.core import Fidget, ParseError, ValidationError, inner_plaintext_parser, inner_plaintext_printer, \
    PlaintextPrintError, PlaintextParseError, FidgetTemplate, explicit, json_parser, TemplateLike, json_printer
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.__util__ import only_valid, to_identifier


class FidgetTuple(MultiFidgetWrapper[Any, NamedTuple]):
    """
    A Fidget that wraps multiple Fidgets into a tuple
    """

    def __init__(self, title, inner_templates: Iterable[TemplateLike] = None, frame_style=None,
                 layout_cls: Type[QBoxLayout] = None, **kwargs):
        """
        :param title: the title
        :param inner_templates: an iterable of templates to act as elements
        :param frame_style: the frame style to apply to the encompassing frame, if any
        :param layout_cls: the class of the layout
        :param kwargs: forwarded to Fidget
        """
        self.inner_templates = tuple(
            t.template_of() for t in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES, _self=self)
        )
        FidgetTemplate.extract_default(*self.inner_templates, upper_space=self, sink=kwargs)

        super().__init__(title, **kwargs)
        self.inners: Sequence[Fidget] = None
        self.value_type: Type[NamedTuple] = None

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls)

    INNER_TEMPLATES: Iterable[TemplateLike] = None
    LAYOUT_CLS: Type[QBoxLayout] = QVBoxLayout

    def init_ui(self, frame_style=None, layout_cls: Type[QBoxLayout] = None):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        master_layout = layout_cls(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            self.inners = []
            for inner_template in self.inner_templates:
                inner = inner_template()
                self.inners.append(inner)
                inner.on_change.connect(self.change_value)
                layout.addWidget(inner)

        if not self.inners:
            raise ValueError('at least one inner fidget must be provided')
        self.setFocusProxy(
            next(iter(self.inners))
        )
        self.value_type = namedtuple(to_identifier(self.title), (to_identifier(i.title) for i in self.inners),
                                     rename=True)

        frame.setLayout(layout)
        master_layout.addWidget(frame)

        return master_layout

    def parse(self):
        d = []
        for subwidget in self.inners:
            try:
                value = subwidget.parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title, offender=subwidget) from e
            d.append(value)
        return self.value_type._make(d)

    def validate(self, d: Tuple):
        super().validate(d)
        for i, v in enumerate(d):
            subwidget = self.inners[i]
            try:
                subwidget.validate(v)
            except ValidationError as e:
                raise ValidationError('error validating ' + subwidget.title, offender=subwidget) from e

    @inner_plaintext_parser
    @json_parser(list)
    def from_json(self, d: list, exact_len=True):
        if exact_len and len(d) != len(self.inners):
            raise PlaintextParseError(f'value number mismatch (expected {len(self.inners)}, got {len(d)})')

        ret = []

        for s, v in zip(self.inners, d):
            if not isinstance(v, str):
                raise PlaintextParseError(f'in {s.title}:, value must be str, got {type(v).__name__}')

            try:
                parsed = s.joined_plaintext_parser(v)
            except PlaintextParseError as e:
                raise PlaintextParseError(f'error parsing {s.title}') from e

            ret.append(parsed)

        return tuple(ret)

    @explicit
    @inner_plaintext_parser
    def from_json_inexact(self, v: str):
        return self.from_json(v, exact_len=False)

    @inner_plaintext_printer
    @json_printer
    def to_json(self, d: Tuple):
        ret = []
        for i, subwidget in enumerate(self.inners):
            v = d[i]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {subwidget.title}') from e
            ret.append(s)

        return ret

    def _fill(self, d: Tuple):
        for sw, v in zip(self.inners, d):
            sw.fill(v)

    @property
    def fill(self):
        if not all(sw.fill for sw in self.inners):
            return None
        return self._fill
