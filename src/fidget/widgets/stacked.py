from __future__ import annotations

from typing import TypeVar, Generic, Iterable, Tuple, Union, Type, List, Dict

from collections import namedtuple
from functools import partial, update_wrapper
from abc import abstractmethod
from itertools import chain

from fidget.backend.QtWidgets import QVBoxLayout, QStackedWidget, QComboBox, QFrame, QRadioButton, QGroupBox, \
    QCheckBox, QBoxLayout

from fidget.core import Fidget, ParseError, FidgetTemplate, TemplateLike
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import MultiFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T')
NamedTemplate = Union[
    TemplateLike[T], Tuple[str, TemplateLike[T]]
]


class FidgetStacked(Generic[T], MultiFidgetWrapper[T, T]):
    """
    Compounded Fidgets, only one of which has a value at any time
    """
    class Selector(Fidget[int]):
        """
        A fidget that selects from fidget options, and stores the active fidget index
        """
        MAKE_INDICATOR = MAKE_PLAINTEXT = MAKE_TITLE = False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.options = {}

        @abstractmethod
        def add_option(self, name):
            index = len(self.options)
            if self.options.setdefault(name, index) != index:
                raise ValueError('duplicate name: ' + name)

        @abstractmethod
        def fill(self, index):
            if isinstance(index, str):
                self.fill(self.options[index])

    class ComboSelector(Selector):
        """
        a selector using a combobox
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.combo_box: QComboBox = None

            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            self.combo_box = QComboBox()
            self.combo_box.currentIndexChanged.connect(self.change_value)
            layout.addWidget(self.combo_box)

            return layout

        def parse(self):
            return self.combo_box.currentIndex()

        def add_option(self, name):
            self.combo_box.addItem(name)
            if self.combo_box.currentIndex() < 0:
                self.combo_box.setCurrentIndex(0)
            super().add_option(name)

        def fill(self, index):
            if isinstance(index, int):
                self.combo_box.setCurrentIndex(index)
            super().fill(index)

    class RadioSelector(Selector):
        """
        a selector using radio buttons
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.group_box: QGroupBox = None
            self.layout: QVBoxLayout = None
            self.radio_buttons: List[QRadioButton] = None

            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            self.group_box = QGroupBox()
            self.layout = QVBoxLayout(self.group_box)
            self.radio_buttons = []

            layout.addWidget(self.group_box)

            return layout

        def parse(self):
            for i, rb in enumerate(self.radio_buttons):
                if rb.isChecked():
                    return i
            raise ParseError('no radio buttons')

        def add_option(self, name):
            rb = QRadioButton()
            rb.setText(name)
            self.layout.addWidget(rb)
            if not self.radio_buttons:
                rb.setChecked(True)
            self.radio_buttons.append(rb)
            rb.toggled.connect(self.change_value)
            super().add_option(name)

        def fill(self, index):
            if isinstance(index, int):
                self.radio_buttons[index].setChecked(True)
            super().fill(index)

    class CheckBoxSelector(Selector):
        """
        a selector between two options, using a checkbox
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.check_box: QCheckBox = None

            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            self.check_box = QCheckBox()
            self.check_box.toggled.connect(self.change_value)
            layout.addWidget(self.check_box)

            return layout

        def parse(self):
            ret = int(self.check_box.isChecked())
            if ret >= len(self.options):
                raise Exception('option not implemented')
            return ret

        def add_option(self, name):
            if len(self.options) >= 2:
                raise Exception('CheckBoxSelector can only contain 2 values')
            if len(self.options) == 1:
                self.check_box.setText(name)
            else:
                self.check_box.setChecked(False)
            super().add_option(name)

        def fill(self, index):
            if isinstance(index, int):
                if index >= len(self.options):
                    raise Exception('option not implemented')
                self.check_box.setChecked(bool(index))
            super().fill(index)

    selectors = {'combo': ComboSelector, 'radio': RadioSelector, 'checkbox': CheckBoxSelector}

    targeted_fill = namedtuple('targeted_fill', 'option_name value')

    def __init__(self, title, inner_templates: Iterable[NamedTemplate[T]] = None,
                 frame_style=None, selector_cls: Union[Type[Selector], str] = None,
                 layout_cls: Type[QBoxLayout] = None,
                 **kwargs):
        """
        :param title: the title
        :param inner_templates: an iterable of name-templates to act as key-value pairs
        :param frame_style: the frame style to apply to the encompassing frame, if any
        :param selector_cls: the class (or name) of a selector
        :param layout_cls: the class of the layout
        :param scrollable: whether to make the widget scrollable
        :param kwargs: forwarded to Fidget
        """
        self.inner_templates = dict(
            self._to_name_subtemplate(o) for o in
            only_valid(inner_templates=inner_templates, INNER_TEMPLATES=self.INNER_TEMPLATES, _self=self)
        )

        FidgetTemplate.extract_default(*self.inner_templates.values(), sink=kwargs, upper_space=type(self), union=True)

        super().__init__(title, **kwargs)

        self.inners: Dict[str, Fidget[T]] = None

        self.selector: FidgetStacked.Selector = None

        selector_cls = first_valid(selector_cls=selector_cls, SELECTOR_CLS=self.SELECTOR_CLS, _self=self)
        if isinstance(selector_cls, str):
            selector_cls = self.selectors[selector_cls]
        self.selector_cls = selector_cls
        self.stacked: QStackedWidget = None

        self.init_ui(frame_style=frame_style, layout_cls=layout_cls)

    INNER_TEMPLATES: Iterable[NamedTemplate[T]] = None
    LAYOUT_CLS: Type[QBoxLayout] = QVBoxLayout
    SELECTOR_CLS: Union[Type[Selector], str] = 'combo'

    def init_ui(self, frame_style=None, layout_cls=None):
        super().init_ui()

        master_layout = QVBoxLayout(self)

        frame = QFrame()
        if frame_style is not None:
            frame.setFrameStyle(frame_style)

        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)

        layout = layout_cls()

        with self.setup_provided(master_layout, layout):
            self.selector = self.selector_cls('select option')
            self.stacked = QStackedWidget()

            self.inners = {}
            for name, inner_template in self.inner_templates.items():
                inner: Fidget[T] = inner_template()
                if self.inners.setdefault(name, inner) is not inner:
                    raise TypeError(f'duplicate inner name: {name}')

                for p in chain(inner.provided_pre(),
                               inner.provided_post()):
                    p.hide()

                self.stacked.addWidget(inner)
                self.selector.add_option(name)

                inner.on_change.connect(self.change_value)

            self.selector.on_change.connect(self._selector_changed)
            layout.addWidget(self.selector)
            layout.addWidget(self.stacked)

        if not self.inners:
            raise ValueError('at least one inner fidget must be provided')
        self.setFocusProxy(
            next(iter(self.inners.values()))
        )

        frame.setLayout(layout)
        master_layout.addWidget(frame)

        return master_layout

    def parse(self):
        return self.current_subwidget().maybe_parse()

    def validate(self, v):
        return self.current_subwidget().maybe_validate(v)

    def plaintext_printers(self):
        return self.current_subwidget().plaintext_printers()

    def plaintext_parsers(self):
        def parser_wrap(option_name, parser, *args, **kwargs):
            return self.targeted_fill(option_name=option_name, value=parser(*args, **kwargs))

        current = self.current_subwidget()
        yield from current.plaintext_parsers()
        for n, o in self.inners.items():
            if o is current:
                continue
            for p in o.plaintext_parsers():
                new_parser = partial(parser_wrap, n, p)
                update_wrapper(new_parser, p)

                new_parser.__name__ = n + ': ' + p.__name__
                yield new_parser

    def current_subwidget(self) -> Fidget[T]:
        v: Fidget[T] = self.stacked.currentWidget()
        return v

    def fill(self, v: Union[T, targeted_fill]):
        if isinstance(v, self.targeted_fill):
            name = v.option_name
            self.selector.fill_value(name)
            v = v.value
        self.current_subwidget().fill(v)

    @staticmethod
    def _to_name_subtemplate(option: NamedTemplate) -> Tuple[str, FidgetTemplate[T]]:
        try:
            template = option.template_of()
        except AttributeError:
            name, option = option
            option = option.template_of()
            return name, option

        if not template.title:
            raise ValueError(f'stacked option {option} must have a title')
        return template.title, template

    def _selector_changed(self):
        index = self.selector.value()
        if not index.is_ok():
            raise index.exception
        self.stacked.setCurrentIndex(index.value)
        self.change_value()
