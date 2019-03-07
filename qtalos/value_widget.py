from __future__ import annotations

from typing import Generic, TypeVar, Optional, Callable, Tuple, Union, Iterable, Type, Dict, Any

from abc import abstractmethod
from enum import IntEnum
from contextlib import contextmanager
from pathlib import Path
from functools import partial, wraps
from itertools import chain

from qtalos.backend import \
 \
    QWidget, QPlainTextEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QFileDialog, QGroupBox, QGridLayout, \
 \
    Qt, pyqtSignal, \
 \
    __backend__

from qtalos.plaintext_adapter import PlaintextPrinter, PlaintextParser, PlaintextParseError, PlaintextPrintError, \
    join_parsers, join_printers, InnerPlaintextParser, InnerPlaintextPrinter
from qtalos.__util__ import error_details, error_tooltip, first_valid

T = TypeVar('T')


# todo fix the init_ui mess
# todo document this bullcrap

class ValueState(IntEnum):
    ok = 1
    invalid = -1
    unparsable = -2

    def is_ok(self):
        return self > 0


class ValueWidgetTemplate(Generic[T]):
    def __init__(self, widget_cls: Type[ValueWidget[T]], args: Tuple, kwargs: Dict[str, Any]):
        self.widget_cls = widget_cls
        self.args = args
        self.kwargs = kwargs

    @property
    def title(self):
        if self.args:
            ret = self.args[0]
            if not isinstance(ret, str):
                raise TypeError('first parameter of a template must be the title string')
            return ret
        else:
            return None

    def _partial(self):
        return partial(self.widget_cls, *self.args, **self.kwargs)

    def __call__(self, *args, **kwargs) -> ValueWidget[T]:
        return self._partial()(*args, **kwargs)

    def template(self, *args, **kwargs):
        args = self.args + args
        kwargs = {**self.kwargs, **kwargs}
        return type(self)(self.widget_cls, args, kwargs)

    def template_of(self):
        return self

    NO_VALUE = object()

    def extract_default(*templates: ValueWidgetTemplate, sink: dict, upper_space, keys: Iterable[str] = ...,
                        union=True):
        def combine_key(k):
            ret = None
            for t in templates:
                v = t.kwargs.get(k)
                if v is None:
                    v = getattr(t.widget_cls, k.upper(), None)
                if v is not None:
                    if v == union:
                        return union
                    else:
                        ret = v
            return ret

        if keys is ...:
            keys = ('make_plaintext', 'make_indicator', 'make_title', 'auto_func')

        for k in keys:
            if k in sink or getattr(upper_space, k.upper(), None) is not None:
                continue
            v = combine_key(k)
            if v is not None:
                sink[k] = v

    def __repr__(self):
        params = ', '.join(chain(
            (repr(a) for a in self.args),
            (k + '=' + repr(v) for k, v in self.kwargs.items())
        ))
        return f'{self.widget_cls.__name__}.template({params})'


class ValueWidget(QWidget, Generic[T]):
    # todo fast/slow validation/parse
    on_change = pyqtSignal()

    # region inherit_me
    """
    How do I inherit ValueWidget?
    * MAKE_TITLE, MAKE_INDICATOR, MAKE_PLAINTEXT, set these for true or false to implement default values.
    * __init__: Call super().__init__ and all's good.
        Don't fill validation_func or auto_func here, instead re-implement validate.
        At the end of your __init__, call init_ui **only if your class isn't going to be subclassed**.
    * init_ui: initialize all the widgets here. call super().init_ui.
        If you intend your class to be subclassed, don't add any widgets to self.
        if you want to add the provided widgets (see below), always do it in an if clause,
            since all provided widgets can be None.
        connect all widgets that change the outcome of parse to self's change_value slot.
        Provided Widgets:
        * title_label: a label that only contains the title of the widget.
            If help is provided, the label displays the help when clicked.
        * validation_label: a label that reads OK or ERR, depending on whether the value is parsed/valid.
        * plaintext_button: a button that allows raw plaintext reading and writing of the value.
        * auto_button: a button to automatically fill the widget's value according to external widgets.
    * validate: call super().validate(value) (it will call validate_func, if provided).
        You can raise ValidationError if the value is invalid.
    * parse: implement, convert the data on the widgets to a value, or raise ParseError.
    * plaintext_printers: yield from super().plaintext_printer, and yield whatever printers you want.
    * plaintext_parsers: yield from super().plaintext_parsers (empty by default), and yield whatever parsers you want.
        * NOTE: you can also just wrap class function with InnerParser / InnerPrinter
    * fill: optional, set the widget's values based on a value
    """
    MAKE_TITLE: bool = None
    MAKE_INDICATOR: bool = None
    MAKE_PLAINTEXT: bool = None

    def __new__(cls, *args, **kwargs):
        ret = super().__new__(cls, *args, **kwargs)
        ret.__new_args = (args, kwargs)
        return ret

    def __init__(self, title,
                 *args,
                 validation_func: Callable[[T], None] = None,
                 auto_func: Callable[[], T] = None,
                 make_title: bool = None,
                 make_indicator: bool = None,
                 make_plaintext: bool = None,
                 make_auto: bool = None,
                 help: str = None,
                 **kwargs):
        if kwargs.get('flags', ()) is None:
            kwargs['flags'] = Qt.WindowFlags()

        if 'flags' in kwargs and __backend__.__name__ == 'PySide2':
            kwargs['f'] = kwargs.pop('flags')

        try:
            super().__init__(*args, **kwargs)
        except (TypeError, AttributeError):
            print(f'args: {args}, kwargs: {kwargs}')
            raise
        self.title = title
        self.help = help

        self.make_title = first_valid(make_title=make_title, MAKE_TITLE=self.MAKE_TITLE)
        self.make_indicator = first_valid(make_indicator=make_indicator, MAKE_INDICATOR=self.MAKE_INDICATOR)
        self.make_plaintext = first_valid(make_plaintext=make_plaintext, MAKE_PLAINTEXT=self.MAKE_PLAINTEXT)

        self.indicator_label: Optional[QLabel] = None
        self.auto_button: Optional[QPushButton] = None
        self.plaintext_button: Optional[QPushButton] = None
        self.title_label: Optional[QLabel] = None

        self._plaintext_widget: Optional[PlaintextEditWidget[T]] = None

        self.validation_func = validation_func
        self.auto_func = auto_func

        self._suppress_update = False

        self._value: \
            Tuple[Union[ValueState, None], Union[ParseError, ValidationError, T], str] = (None, None, None)
        self._joined_plaintext_printer = None
        self._joined_plaintext_parser = None

        if make_auto is ...:
            if self.auto_func:
                if self.fill is None:
                    raise Exception('auto_func can only be used on a ValueWidget with an implemented fill method')
                else:
                    self.make_auto = True
            else:
                self.make_auto = False
        else:
            self.make_auto = make_auto

    def init_ui(self):
        self.setWindowTitle(self.title)

        if self.make_indicator:
            self.indicator_label = QLabel('')
            self.indicator_label.mousePressEvent = self._detail_button_clicked

        if self.make_auto:
            self.auto_button = QPushButton('auto')
            self.auto_button.clicked.connect(self._auto_btn_click)

        if self.make_plaintext:
            self.plaintext_button = QPushButton('text')
            self.plaintext_button.clicked.connect(self._plaintext_btn_click)

            self._plaintext_widget = PlaintextEditWidget()

        if self.make_title:
            self.title_label = QLabel(self.title)
            if self.help:
                self.title_label.mousePressEvent = self._help_clicked

    fill: Optional[Callable[[ValueWidget[T], T], None]] = None

    @abstractmethod
    def parse(self) -> T:
        pass

    def validate(self, value: T) -> None:
        if self.validation_func:
            self.validation_func(value)

    def inner_plaintext_parsers(self):
        yield from (ip.__get__(self, type(self)) for ip in self._inner_parsers)

    def inner_plaintext_printers(self):
        yield from (ip.__get__(self, type(self)) for ip in self._inner_printers)

    def plaintext_printers(self) -> Iterable[PlaintextPrinter[T]]:
        yield from self.inner_plaintext_printers()
        yield str
        yield repr

    def plaintext_parsers(self) -> Iterable[PlaintextParser[T]]:
        yield from self.inner_plaintext_parsers()

    # endregion

    # region call_me
    @contextmanager
    def suppress_update(self, new_value=True, call_on_exit=True):
        prev_value = self._suppress_update
        self._suppress_update = new_value
        yield new_value
        self._suppress_update = prev_value
        if call_on_exit:
            self.change_value()

    @property
    def joined_plaintext_parser(self):
        if not self._joined_plaintext_parser:
            self._joined_plaintext_parser = join_parsers(self.plaintext_parsers)
        return self._joined_plaintext_parser

    @property
    def joined_plaintext_printer(self):
        if not self._joined_plaintext_printer:
            self._joined_plaintext_printer = join_printers(self.plaintext_printers)
        return self._joined_plaintext_printer

    def provided_pre(self, exclude=()):
        return (yield from (
            y for y in (self.title_label,)
            if y and y not in exclude
        ))

    def provided_post(self, exclude=()):
        return (yield from (
            y for y in (self.indicator_label,
                        self.auto_button,
                        self.plaintext_button)
            if y and y not in exclude
        ))

    @contextmanager
    def setup_provided(self, pre_layout: QVBoxLayout, post_layout=..., exclude=()):
        for p in self.provided_pre(exclude=exclude):
            pre_layout.addWidget(p)
        yield
        if post_layout is ...:
            post_layout = pre_layout
        for p in self.provided_post(exclude=exclude):
            post_layout.addWidget(p)

        self._update_indicator()

    # endregion

    # region call_me_from_outside
    def fill_from_text(self, s: str):
        if not self.fill:
            raise Exception(f'widget {self} does not have its fill function implemented')
        self.fill(self.joined_plaintext_parser(s))

    def value(self) -> Tuple[ValueState, Union[ParseError, ValidationError, T], str]:
        if self._value[0] is None:
            self._reload_value()
        return self._value

    def change_value(self, *args):
        self._invalidate_value()
        self._update_indicator()
        self.on_change.emit()

    _template_class = ValueWidgetTemplate

    @classmethod
    @wraps(__init__)
    def template(cls, *args, **kwargs):
        return cls._template_class(cls, args, kwargs)

    def template_of(self):
        a, k = self.__new_args
        return self.template(*a, **k)

    @classmethod
    def template_class(cls, class_):
        cls._template_class = class_
        return class_

    def __str__(self):
        return super().__str__() + ': ' + self.title

    # endregion

    def _invalidate_value(self):
        self._value = None, None, None

    def _auto_btn_click(self, click_args):
        try:
            value = self.auto_func()
        except DoNotFill as e:
            if str(e):
                QMessageBox.critical(self, 'error during autofill', str(e))
            return

        with self.suppress_update():
            self.fill(value)

    def _plaintext_btn_click(self):
        self._plaintext_widget.prep_for_show(self)
        self._plaintext_widget.show()

    def _update_indicator(self, *args, **kwargs):
        if self._suppress_update:
            return

        state, val, details = self._value = self.value()

        if self.indicator_label and self.indicator_label.parent():
            if state.is_ok():
                text = 'OK'
                tooltip = str(val)
            else:
                text = 'ERR'
                tooltip = error_tooltip(val)

            self.indicator_label.setText(text)
            self.indicator_label.setToolTip(tooltip)

        if self.plaintext_button and self.plaintext_button.parent():
            self.plaintext_button.setEnabled(state == ValueState.ok or any(self.plaintext_parsers()))

    def _reload_value(self):
        try:
            value = self.parse()
        except ParseError as e:
            self._value = ValueState.unparsable, e, error_details(e)
            return

        try:
            self.validate(value)
        except ValidationError as e:
            self._value = ValueState.invalid, e, error_details(e)
            return

        try:
            details = self.joined_plaintext_printer(value)
        except PlaintextPrintError as e:
            details = 'details could not be loaded because of a parser error:\n' + error_details(e)

        self._value = ValueState.ok, value, details

    def _detail_button_clicked(self, event):
        if self._value[-1]:
            QMessageBox.information(self, 'validation details', self._value[-1])

    def _help_clicked(self, event):
        if self.help:
            QMessageBox.information(self, self.title, self.help)

    _inner_printers: Iterable[PlaintextPrinter[T]] = ()
    _inner_parsers: Iterable[PlaintextParser[T]] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.on_change = pyqtSignal()

        cls._inner_printers = []
        cls._inner_parsers = []
        for v in cls.__dict__.values():
            if isinstance(v, InnerPlaintextPrinter):
                cls._inner_printers.append(v)
            if isinstance(v, InnerPlaintextParser):
                cls._inner_parsers.append(v)
        for base in cls.__bases__:
            cls._inner_printers.extend(getattr(base, '_inner_printers', ()))
            cls._inner_parsers.extend(getattr(base, '_inner_parsers', ()))


class ParseError(Exception):
    pass


class ValidationError(Exception, Generic[T]):
    pass


class DoNotFill(Exception):
    pass


class PlaintextEditWidget(Generic[T], ValueWidget[T]):
    class _ShiftEnterIgnoringPlainTextEdit(QPlainTextEdit):
        def keyPressEvent(self, event):
            if (event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Return) \
                    or (event.modifiers() == Qt.KeypadModifier | Qt.ShiftModifier and event.key() == Qt.Key_Enter):
                event.ignore()
            else:
                return super().keyPressEvent(event)

    NO_CURRENT_VALUE = object()

    MAKE_INDICATOR = True

    MAKE_PLAINTEXT = False
    MAKE_TITLE = False

    def __init__(self, *args, **kwargs):
        # todo set window title?
        kwargs.setdefault('make_title', False)
        super().__init__('plaintext edit', *args, **kwargs)

        self.current_value: T = self.NO_CURRENT_VALUE

        self.print_widget: QWidget = None
        self.print_edit: QPlainTextEdit = None
        self.print_combo: QComboBox = None
        self.ok_button: QPushButton = None
        self.apply_button: QPushButton = None

        self.parse_widget: QWidget = None
        self.parse_edit: PlaintextEditWidget._ShiftEnterIgnoringPlainTextEdit = None
        self.parse_combo: QComboBox = None

        self.owner: Optional[ValueWidget[T]] = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()
        self.setWindowModality(Qt.ApplicationModal)

        master_layout = QVBoxLayout(self)

        self.print_widget = QGroupBox('current value:')
        print_master_layout = QVBoxLayout(self.print_widget)

        print_layout = QHBoxLayout()
        print_master_layout.addLayout(print_layout)

        self.print_edit = QPlainTextEdit()
        self.print_edit.setReadOnly(True)
        print_layout.addWidget(self.print_edit)

        print_extras_layout = QGridLayout()

        self.print_combo = QComboBox()
        file_button = QPushButton('to file...')
        file_button.clicked.connect(self.save_file)
        print_extras_layout.addWidget(file_button, 0, 0)
        print_extras_layout.addWidget(self.print_combo, 1, 0)

        print_layout.addLayout(print_extras_layout)

        master_layout.addWidget(self.print_widget)

        self.parse_widget = QGroupBox('set value:')
        parse_master_layout = QVBoxLayout(self.parse_widget)

        parse_layout = QHBoxLayout()
        parse_master_layout.addLayout(parse_layout)

        self.parse_edit = self._ShiftEnterIgnoringPlainTextEdit()
        self.parse_edit.textChanged.connect(self.change_value)
        self.print_combo.currentIndexChanged[int].connect(self.update_print)
        parse_layout.addWidget(self.parse_edit)

        parse_extras_layout = QGridLayout()

        self.parse_combo = QComboBox()
        self.parse_combo.currentIndexChanged[int].connect(self.change_value)
        parse_extras_layout.addWidget(self.parse_combo, 0, 0)

        if self.indicator_label:
            parse_extras_layout.addWidget(self.indicator_label, 0, 1)

        file_button = QPushButton('from file...')
        file_button.clicked.connect(self.load_file)
        parse_extras_layout.addWidget(file_button, 1, 0, 1, 2)

        self.apply_button = QPushButton('apply')
        self.apply_button.clicked.connect(self.apply_parse)
        parse_extras_layout.addWidget(self.apply_button, 2, 0)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.commit_parse)
        parse_extras_layout.addWidget(self.ok_button, 2, 1)

        parse_layout.addLayout(parse_extras_layout)

        master_layout.addWidget(self.parse_widget)

        self.on_change.connect(self._on_value_change)

    def parse(self):
        parser: PlaintextParser = self.parse_combo.currentData()
        if not parser:
            raise ParseError('no parser configured')

        try:
            return parser(self.parse_edit.toPlainText())
        except PlaintextParseError as e:
            raise ParseError(...) from e

    def load_file(self, *args):
        filename, _ = QFileDialog.getOpenFileName(self, 'open file', filter='text files (*.txt *.csv);;all files (*.*)')
        if not filename:
            return

        try:
            text = Path(filename).read_text()
        except IOError as e:
            QMessageBox.critical(self, 'could not read file', str(e))
        else:
            self.parse_edit.setPlainText(text)

    def save_file(self, *args):
        filename, _ = QFileDialog.getSaveFileName(self, 'save file', filter='text files (*.txt *.csv);;all files (*.*)')
        if not filename:
            return

        try:
            Path(filename).write_text(self.print_edit.toPlainText())
        except IOError as e:
            QMessageBox.critical(self, 'could not write to file', str(e))

    def update_print(self, *args):
        if self.current_value is self.NO_CURRENT_VALUE:
            text = '<no current value>'
        else:
            printer: PlaintextPrinter = self.print_combo.currentData()
            if not printer:
                text = '<no printer configured>'
            else:
                try:
                    text = printer(self.current_value)
                except PlaintextPrintError as e:
                    text = f'<printer error: {e}>'

        self.print_edit.setPlainText(text)

    def prep_for_show(self, owner: ValueWidget[T], clear_parse=True, clear_print=True):
        self.owner = owner

        self.setWindowTitle('plaintext edit for ' + owner.title)

        state, self.current_value, _ = owner.value()
        if not state.is_ok():
            self.print_widget.setVisible(False)
            printers = False
        else:
            self.print_widget.setVisible(True)
            printers = list(owner.plaintext_printers())
            # setup the print

            combo_index = 0
            if clear_print:
                pass
            else:
                combo_index = self.print_combo.currentIndex()
                if combo_index == -1:
                    combo_index = 0

            self.print_combo.clear()
            if len(printers) > 1:
                self.print_combo.setVisible(True)
                self.print_combo.addItem('<all>', owner.joined_plaintext_printer)
            else:
                self.print_combo.setVisible(False)

            for printer in printers:
                name = printer.__name__
                if getattr(printer, '__explicit__', False):
                    name += '*'
                self.print_combo.addItem(name, printer)

            self.print_combo.setCurrentIndex(combo_index)

        parsers = list(owner.plaintext_parsers())
        if not parsers:
            self.parse_widget.setVisible(False)
        else:
            if not owner.fill:
                raise Exception(
                    f'parsers are defined but the widget has no implemented fill method (in widget {owner})')

            self.parse_widget.setVisible(True)
            combo_index = 0

            if clear_parse:
                self.parse_edit.clear()
            else:
                combo_index = self.parse_combo.currentIndex()
                if combo_index == -1:
                    combo_index = 0

            self.parse_combo.clear()
            if len(parsers) > 1:
                self.parse_combo.setVisible(True)
                self.parse_combo.addItem('<all>', owner.joined_plaintext_parser)
            else:
                self.parse_combo.setVisible(False)

            for parser in parsers:
                name = parser.__name__
                if getattr(parser, '__explicit__', False):
                    name += '*'
                self.parse_combo.addItem(name, parser)
            self.parse_combo.setCurrentIndex(combo_index)

        if not printers and not parsers:
            raise ValueError('plaintext edit widget prepped for owner without plaintext adapters')

    def commit_parse(self):
        status, value, _ = self.value()
        if not status.is_ok():
            QMessageBox.critical(self, 'error parsing plaintext', error_details(self.result_value))
        else:
            self.owner.fill(value)
            self.close()

    def apply_parse(self):
        status, value, _ = self.value()
        if not status.is_ok():
            QMessageBox.critical(self, 'error parsing plaintext', error_details(self.result_value))
        else:
            self.owner.fill(value)
            self.prep_for_show(self.owner, clear_parse=False, clear_print=False)
            self.parse_edit.setFocus()

    @property
    def has_parse(self):
        return bool(self.parsers)

    @property
    def has_print(self):
        return bool(self.printers)

    def _on_value_change(self, *a):
        state, _, _ = self.value()

        self.ok_button.setEnabled(state.is_ok())
        self.apply_button.setEnabled(state.is_ok())

    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Return) \
                or (event.modifiers() == Qt.KeypadModifier | Qt.ShiftModifier and event.key() == Qt.Key_Enter):
            self.ok_button.click()
        elif not event.modifiers() and event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
