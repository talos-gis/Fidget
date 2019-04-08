from __future__ import annotations

from collections import namedtuple
from typing import Type, Iterable, Tuple, NamedTuple

from fidget.backend.QtWidgets import QVBoxLayout, QFrame, QBoxLayout
from fidget.core import PlaintextPrintError, PlaintextParseError, TemplateLike
from fidget.core.__util__ import first_valid
from fidget.widgets.__util__ import to_identifier
from fidget.widgets.compound import FidgetCompound


class FidgetTuple(FidgetCompound[tuple]):
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
        super().__init__(title, inner_templates, **kwargs)

        self.value_type: Type[NamedTuple] = None

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls)

    INNER_TEMPLATES: Iterable[TemplateLike] = None
    LAYOUT_CLS: Type[QBoxLayout] = QVBoxLayout

    @classmethod
    def _make_inner_templates(cls, inner_templates_param: Iterable[TemplateLike]):
        return [i.template_of() for i in inner_templates_param]

    @classmethod
    def inner_templates_values(cls, inner_templates):
        return inner_templates

    @classmethod
    def _make_inners(cls, inner_templates):
        return [i() for i in inner_templates]

    @classmethod
    def inners_values(cls, inners):
        return inners

    @classmethod
    def inners_items(cls, inners):
        return enumerate(inners)

    @classmethod
    def init_result(cls):
        return []

    @classmethod
    def insert_result(cls, res, key, value):
        res.append(value)

    @classmethod
    def result_zip_subwidget(cls, res, inners):
        return zip(enumerate(res), inners)

    def init_ui(self, frame_style=None, layout_cls: Type[QBoxLayout] = None):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        master_layout = layout_cls(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            for inner in self.make_inners():
                layout.addWidget(inner)
            self.value_type = namedtuple(to_identifier(self.title), (to_identifier(i.title) for i in self.inners),
                                         rename=True)


        frame.setLayout(layout)
        master_layout.addWidget(frame)

        return master_layout

    def parse(self):
        seq = super().parse()
        return self.value_type._make(seq)

    def _from_json(self, d: list, exact=True):
        if not isinstance(d, list):
            raise PlaintextParseError from TypeError('expected list, got '+type(d).__name__)
        if exact and len(d) != len(self.inners):
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

    def _to_json(self, d: Tuple):
        if not isinstance(d, tuple):
            raise PlaintextPrintError('can only print tuples')
        ret = []
        for i, subwidget in enumerate(self.inners):
            v = d[i]
            try:
                s = subwidget.joined_plaintext_printer(v)
            except PlaintextPrintError as e:
                raise PlaintextPrintError(f'error printing {subwidget.title}') from e
            ret.append(s)

        return ret
