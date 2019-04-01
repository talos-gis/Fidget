from __future__ import annotations

from typing import Mapping, Iterable, Type

from fidget.backend.QtWidgets import QVBoxLayout, QFrame, QScrollArea, QWidget, QBoxLayout

from fidget.core import ParseError, ValidationError
from fidget.core.__util__ import first_valid

from fidget.widgets.mapping import FidgetMapping, NamedTemplate


class FidgetDict(FidgetMapping):
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

        super().__init__(title, inner_templates, **kwargs)

        frame_style = frame_style or self.FRAME_STYLE

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls, scrollable=scrollable)

    LAYOUT_CLS = QVBoxLayout
    FRAME_STYLE = None
    SCROLLABLE = True
    INNER_TEMPLATES: Iterable[NamedTemplate] = None

    def init_ui(self, frame_style=None, layout_cls=None, scrollable=None):
        super().init_ui()

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        owner = self
        scrollable = first_valid(scrollable=scrollable, SCROLLABLE=self.SCROLLABLE, _self=self)

        owner_layout = QVBoxLayout()
        owner.setLayout(owner_layout)

        if scrollable:
            owner = QScrollArea(owner)
            owner.setWidgetResizable(True)
            owner_layout.addWidget(owner)

        master = QWidget()
        master_layout = layout_cls(master)

        if scrollable:
            owner.setWidget(master)
        else:
            owner_layout.addWidget(master)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout = layout_cls(frame)

        with self.setup_provided(master_layout, layout):
            for inner in self.make_inners().values():
                layout.addWidget(inner)

        master_layout.addWidget(frame)

        return master_layout

    def parse(self):
        d = {}
        for key, subwidget in self.inners.items():
            try:
                value = subwidget.maybe_parse()
            except ParseError as e:
                raise ParseError('error parsing ' + subwidget.title, offender=subwidget) from e
            d[key] = value
        return d

    def validate(self, d: Mapping[str, object]):
        super().validate(d)
        for k, v in d.items():
            subwidget = self.inners[k]
            try:
                subwidget.maybe_validate(v)
            except ValidationError as e:
                raise ValidationError('error validating ' + subwidget.title, offender=subwidget) from e
