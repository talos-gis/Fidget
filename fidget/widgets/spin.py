from typing import Union, TypeVar, Generic, Iterable, Tuple

from fidget.backend.QtGui import QValidator
from fidget.backend.QtWidgets import QSpinBox, QDoubleSpinBox, QHBoxLayout
from fidget.core import Fidget
from fidget.core.__util__ import first_valid, optional_valid
from fidget.widgets.discrete import FidgetDiscreteChoice
from fidget.widgets.user_util import FidgetFloat, FidgetInt


# todo document

class FidgetSpin(Fidget[float]):
    MAKE_TITLE = False
    MAKE_INDICATOR = False
    MAKE_PLAINTEXT = False

    def __init__(self, title, minimum=None, maximum=None, step=None, force_float=None, prefix=None, suffix=None,
                 decimals=None, initial_value=None, **kwargs):
        super().__init__(title, **kwargs)
        minimum = first_valid(minimum=minimum, MINIMUM=self.MINIMUM, _self=self)
        maximum = first_valid(maximum=maximum, MAXIMUM=self.MAXIMUM, _self=self)
        step = first_valid(step=step, STEP=self.STEP, _self=self)
        decimals = optional_valid(decimals=decimals, DECIMALS=self.DECIMALS, _self=self)

        force_float = first_valid(force_float=force_float, FORCE_FLOAT=self.FORCE_FLOAT, _self=self)

        self.use_float = force_float or (decimals is not None) \
                         or any(isinstance(i, float) for i in (minimum, maximum, step))

        prefix = optional_valid(prefix=prefix, PREFIX=self.PREFIX, _self=self)
        suffix = optional_valid(suffix=suffix, SUFFIX=self.SUFFIX, _self=self)

        self.spin: Union[QSpinBox, QDoubleSpinBox] = None

        self.init_ui(minimum=minimum, maximum=maximum, step=step, use_float=self.use_float, prefix=prefix,
                     suffix=suffix, decimals=decimals, initial_value=initial_value)

    def init_ui(self, minimum=None, maximum=None, step=None, use_float=None, prefix=None, suffix=None, decimals=None,
                initial_value=None):
        super().init_ui()

        layout = QHBoxLayout()

        with self.setup_provided(layout):
            spin_cls = QDoubleSpinBox if use_float else QSpinBox
            self.spin = spin_cls()
            self.spin.valueChanged[str].connect(self.change_value)

            if minimum:
                self.spin.setMinimum(minimum)
            if maximum:
                self.spin.setMaximum(maximum)
            if step:
                self.spin.setSingleStep(step)
            if prefix:
                self.spin.setPrefix(prefix)
            if suffix:
                self.spin.setSuffix(suffix)
            if decimals:
                self.spin.setDecimals(decimals)

            layout.addWidget(self.spin)

        if use_float:
            self.add_plaintext_delegates(FidgetFloat)
        else:
            self.add_plaintext_delegates(FidgetInt)

        initial_value = optional_valid(initial_value=initial_value, INITIAL_VALUE=self.INITIAL_VALUE, _self=self)
        if initial_value:
            self.spin.setValue(initial_value)

        self.setFocusProxy(self.spin)
        self.setLayout(layout)

        return layout

    def parse(self):
        return self.spin.value()

    def fill(self, v):
        self.spin.setValue(v)

    MINIMUM = 0
    MAXIMUM = 99
    STEP = 1
    FORCE_FLOAT = False
    PREFIX = None
    SUFFIX = None
    DECIMALS = None
    INITIAL_VALUE = None


T = TypeVar('T')


class FidgetDiscreteSpin(Generic[T], FidgetDiscreteChoice[T]):
    MAKE_TITLE = False
    MAKE_INDICATOR = False
    MAKE_PLAINTEXT = False

    def __init__(self, title, wrap=None, **kwargs):
        super().__init__(title, **kwargs)
        wrap = first_valid(wrap=wrap, WRAP=self.WRAP, _self=self)

        self.spin: QSpinBox = None

        self.init_ui(wrap=wrap)

        self.fill_initial()

    WRAP = False

    def init_ui(self, wrap=None):
        super().init_ui()

        layout = QHBoxLayout()

        with self.setup_provided(layout):
            self.spin = QSpinBox()
            self.spin.valueChanged[str].connect(self.change_value)

            minimum = 0
            maximum = len(self.options) - 1

            if wrap:
                minimum -= 1
                maximum += 1
                self.spin.valueChanged[int].connect(self.check_wrap)

            self.spin.setMinimum(minimum)
            self.spin.setMaximum(maximum)

            self.spin.valueFromText = self._value_from_text
            self.spin.textFromValue = self._text_from_value
            self.spin.validate = self._validate

            layout.addWidget(self.spin)

        self.setFocusProxy(self.spin)
        self.setLayout(layout)

        return layout

    def _validate(self, s: str, pos: int):
        if s in self.name_lookup:
            return QValidator.Acceptable
        return QValidator.Intermediate

    def _value_from_text(self, t: str):
        return self.name_lookup.get(t, -2)[0]

    def _text_from_value(self, i: int):
        if i == len(self.options):
            i = 0
        return self.options[i][0][0]

    def check_wrap(self, new_val):
        if len(self.options) <= new_val or new_val < 0:
            v = new_val % len(self.options)
            self.spin.setValue(v)

    def parse(self):
        v = self.spin.value() % len(self.options)
        return self.options[v][1]

    def fill_index(self, index):
        self.spin.setValue(index)
