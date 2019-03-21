from typing import Union, TypeVar, Generic, Iterable, Tuple, List, Dict

from fidget.backend.QtWidgets import QSpinBox, QDoubleSpinBox, QHBoxLayout
from fidget.backend.QtGui import QValidator

from fidget.core import Fidget, PlaintextPrintError, inner_plaintext_parser, PlaintextParseError
from fidget.core.__util__ import first_valid

from fidget.widgets.user_util import FidgetFloat, FidgetInt
from fidget.widgets.__util__ import optional_valid, only_valid, TolerantDict


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

    def init_ui(self, minimum=None, maximum=None, step=None, use_float=None, prefix=None, suffix=None, decimals=None, initial_value=None):
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


class FidgetDiscreteSpin(Generic[T], Fidget[T]):
    MAKE_TITLE = False
    MAKE_INDICATOR = False
    MAKE_PLAINTEXT = False

    def __init__(self, title, *, options: Iterable[Union[T, Tuple[str, T]]] = None, initial_index=None,
                 initial_value=None, wrap=None,
                 **kwargs):
        super().__init__(title, **kwargs)

        options = only_valid(options=options, OPTIONS=self.OPTIONS, _self=self)
        initial_index = optional_valid(initial_index=initial_index, INITIAL_INDEX=self.INITIAL_INDEX, _self=self)
        initial_value = first_valid(initial_value=initial_value, INITIAL_VALUE=self.INITIAL_VALUE, _self=self)
        wrap = first_valid(wrap=wrap, WRAP=self.WRAP, _self=self)

        self.options: List[Tuple[str, T]] = []
        self.opt_lookup: TolerantDict[T, int] = TolerantDict()
        self.names: Dict[str, int] = {}

        index = initial_index
        for i, option in enumerate(options):
            names, value = self.extract_names_and_value(option)
            if value == initial_value:
                index = i
            self.options.append((names[0], value))
            for name in names:
                self.names.setdefault(name, i)
            self.opt_lookup[value] = i

        self.spin: QSpinBox = None

        self.init_ui(index=index, wrap=wrap)

    OPTIONS: Iterable[Union[T, Tuple[str, T]]] = None
    WRAP = True
    INITIAL_INDEX = None
    INITIAL_VALUE = object()

    def init_ui(self, index=None, wrap=None):
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
        if s in self.names:
            return QValidator.Acceptable
        return QValidator.Intermediate

    def _value_from_text(self, t: str):
        return self.names.get(t, -2)

    def _text_from_value(self, i: int):
        if i == len(self.options):
            i = 0
        return self.options[i][0]

    def extract_names_and_value(self, value: Union[Tuple[str, T], T]) -> Tuple[List[str], T]:
        names = []

        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
            names.append(value[0])
            value = value[1]

        for printer in self.implicit_plaintext_printers():
            try:
                names.append(printer(value))
            except PlaintextPrintError:
                pass

        if not names:
            raise Exception(f'no names for {value}')

        return names, value

    def check_wrap(self, new_val):
        if len(self.options) <= new_val or new_val < 0:
            v = new_val % len(self.options)
            self.spin.setValue(v)

    def parse(self):
        v = self.spin.value() % len(self.options)
        return self.options[v][1]

    @inner_plaintext_parser
    def by_name(self, v):
        try:
            return self.names[v]
        except KeyError as e:
            raise PlaintextParseError from e

    def fill(self, key):
        try:
            index, _ = self.opt_lookup[key]
        except KeyError as e:
            if isinstance(key, int):
                index = key
            else:
                raise KeyError('fill value is not an option') from e

        self.spin.setValue(index)
