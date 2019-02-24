from __future__ import annotations

from typing import Generic, TypeVar, Optional, Callable, Tuple, Union, Iterable, Sequence

from abc import abstractmethod
from enum import Enum, auto
from contextlib import contextmanager
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QDialog, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal

from qtalos.plaintext_adapter import PlaintextPrinter, PlaintextParser, PlaintextParseError, PlaintextPrintError, \
    join_parsers, join_printers, InnerPlaintextParser, InnerPlaintextPrinter
from qtalos.__util__ import error_details

T = TypeVar('T')


# todo document this bullcrap

class ValueState(Enum):
    ok = auto()
    invalid = auto()
    unparsable = auto()


class ValueWidget(QWidget, Generic[T]):
    # todo help button
    # todo fast/slow validation/parse
    on_change = pyqtSignal()

    # region inherit_me
    """
    How do I inherit ValueWidget?
    * __init__: Call super().__init__ and all's good.
        Don't fill validation_func or auto_func here, instead re-implement validate.
        At the end of your __init__, call init_ui **only if your class isn't going to be subclassed**.
    * init_ui: initialize all the widgets here. call super().init_ui.
        If you intend your class to be subclassed, don't add any widgets to self.
        if you want to add the provided widgets (see below), always do it in an if clause,
        since all provided widgets can be None.
        connect all widgets that change the outcome of parse to self's change_value slot.
        Provided Widgets:
        * validation_label: a label that reads OK or ERR, depending on whether the value is parsed/valid.
        * plaintext_button: a button that allows raw plaintext reading and writing of the value.
        * auto_button: a button to automatically fill the widget's value according to external widgets.
        * help_button (not implemented yet): a button to display a help message concerning the value.
    * validate: call super().validate(value) (it will call validate_func, if provided).
        You can raise self.validation_exception if the value is invalid.
    * parse: implement, convert the data on the widgets to a value, or raise self.parse_exception.
    * plaintext_printers: yield from super().plaintext_printer, and yield whatever printers you want.
    * plaintext_parsers: yield from super().plaintext_parsers (empty by default), and yield whatever parsers you want.
        * NOTE: you can also just wrap class function with InnerParser / InnerPrinter
    * fill: optional, set the widget's values based on a value
    """

    def __init__(self, title,
                 *args,
                 validation_func: Callable[[T], None] = None,
                 auto_func: Callable[[], T] = None,
                 **kwargs):
        if kwargs.get('flags', object()) is None:
            kwargs['flags'] = Qt.WindowFlags()
        super().__init__(*args, **kwargs)
        self.title = title
        self.make_validator_label = True
        self.make_plaintext_button = True

        self.validation_label: Optional[QLabel] = None
        self.auto_button: Optional[QPushButton] = None
        self.plaintext_button: Optional[QPushButton] = None
        self.help_button: Optional[QPushButton] = None

        self._plaintext_widget: Optional[PlaintextEditWidget[T]] = None

        self.validation_func = validation_func
        self.auto_func = auto_func

        self._suppress_update = False

        self._value: \
            Tuple[Union[ValueState, None], Union[ParseError, ValidationError, T], str] = (None, None, None)
        self._joined_plaintext_printer = None
        self._joined_plaintext_parser = None

        if self.auto_func:
            if self.fill is None:
                raise Exception('auto_func can only be used on a ValueWidget with an implemented fill method')
            else:
                self.make_auto_button = True
        else:
            self.make_auto_button = False

    def init_ui(self):
        if self.make_validator_label:
            self.validation_label = QLabel('')
            self.validation_label.mousePressEvent = self._detail_button_clicked

        if self.make_auto_button:
            self.auto_button = QPushButton('auto')
            self.auto_button.clicked.connect(self._auto_btn_click)

        if self.make_plaintext_button:
            self.plaintext_button = QPushButton('text')
            self.plaintext_button.clicked.connect(self._plaintext_btn_click)

            self._plaintext_widget = PlaintextEditWidget(self)

            if self._plaintext_widget.has_parse and self.fill is None:
                raise Exception('parsers are defined but the widget has no implemented fill method')

    fill: Optional[Callable[[ValueWidget[T], T], None]] = None

    def validate(self, value: T) -> None:
        if self.validation_func:
            self.validation_func(value)

    @abstractmethod
    def parse(self) -> T:
        pass

    def plaintext_printers(self) -> Iterable[PlaintextPrinter[T]]:
        yield from (ip.__get__(self, type(self)) for ip in self._inner_printers)
        yield str
        yield repr

    def plaintext_parsers(self) -> Iterable[PlaintextParser[T]]:
        yield from (ip.__get__(self, type(self)) for ip in self._inner_parsers)
    # endregion

    # region call_me
    def parse_exception(self, *args, **kwargs):
        return ParseError(self, *args, **kwargs)

    def validation_exception(self, value: T, *args, **kwargs):
        return ValidationError(self, value, *args, **kwargs)

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
        state, value, _ = self.value()
        if state != ValueState.ok:
            value = PlaintextEditWidget.NO_CURRENT_VALUE
        self._plaintext_widget.set_current_value(value)
        if self._plaintext_widget.exec_() == QDialog.Accepted:
            self.fill(self._plaintext_widget.result_value)

    def _update_indicator(self, *args, **kwargs):
        if self._suppress_update:
            return

        state, val, details = self._value = self.value()

        if self.validation_label and self.validation_label.parent():
            if state == ValueState.ok:
                text = 'OK'
            else:
                text = 'ERR'
            tooltip = str(val)

            self.validation_label.setText(text)
            self.validation_label.setToolTip(tooltip)

        if self.plaintext_button and self.plaintext_button.parent():
            if not self._plaintext_widget.has_parse:
                self.plaintext_button.setEnabled(state == ValueState.ok)

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
    def __init__(self, sender: ValueWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender


class ValidationError(Exception, Generic[T]):
    def __init__(self, sender: ValueWidget, value: T, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender = sender
        self.value = value


class DoNotFill(Exception):
    pass


class ValueDialog(Generic[T], QDialog, ValueWidget[T]):
    @abstractmethod
    def parse(self) -> T:
        pass


class PlaintextEditWidget(Generic[T], ValueDialog[T]):
    NO_CURRENT_VALUE = object()

    def __init__(self, owner: ValueWidget[T], *args, **kwargs):
        super().__init__('plaintext edit for ' + owner.title, *args, **kwargs)
        self.make_auto_button = self.make_plaintext_button = False

        self.owner = owner
        self.printers: Sequence[PlaintextPrinter] = list(self.owner.plaintext_printers())
        self.parsers: Sequence[PlaintextParser] = list(self.owner.plaintext_parsers())

        self.make_validator_label = bool(self.parsers)

        if not self.printers and not self.parsers:
            raise ValueError('plaintext edit widget created for owner without plaintext adapters')

        self.current_value: T = self.NO_CURRENT_VALUE

        self.print_widget: Optional[QHBoxLayout] = None
        self.print_edit: Optional[QPlainTextEdit] = None
        self.print_combo: Optional[QComboBox] = None

        self.parse_edit: Optional[QPlainTextEdit] = None
        self.parse_combo: Optional[QComboBox] = None

        self.result_value: T = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()
        self.setWindowModality(Qt.ApplicationModal)

        master_layout = QVBoxLayout(self)
        if self.printers:
            self.print_widget = QWidget()
            print_master_layout = QVBoxLayout(self.print_widget)
            print_master_layout.addWidget(QLabel('current value:'))

            print_layout = QHBoxLayout()
            print_master_layout.addLayout(print_layout)

            self.print_edit = QPlainTextEdit()
            self.print_edit.setReadOnly(True)
            print_layout.addWidget(self.print_edit)

            if len(self.printers) > 1:
                self.print_combo = QComboBox()
                self.print_combo.addItem('<all>', self.owner.joined_plaintext_printer)
                for printer in self.printers:
                    self.print_combo.addItem(printer.__name__, printer)
                self.print_combo.setCurrentIndex(0)
                self.print_combo.currentIndexChanged[int].connect(self.update_print)
                print_layout.addWidget(self.print_combo)

            master_layout.addWidget(self.print_widget)

        if self.parsers:
            parse_widget = QWidget()

            parse_layout = QHBoxLayout()
            parse_widget.setLayout(parse_layout)

            master_layout.addWidget(QLabel('set value:'))

            self.parse_edit = QPlainTextEdit()
            self.parse_edit.textChanged.connect(self.change_value)
            parse_layout.addWidget(self.parse_edit)

            if self.validation_label:
                parse_layout.addWidget(self.validation_label)

            if len(self.parsers) > 1:
                self.parse_combo = QComboBox(parse_layout.widget())
                self.parse_combo.addItem('<all>', self.owner.joined_plaintext_parser)
                for parser in self.parsers:
                    self.parse_combo.addItem(parser.__name__, parser)
                self.parse_combo.setCurrentIndex(0)
                self.parse_combo.currentIndexChanged[int].connect(self.change_value)
                parse_layout.addWidget(self.parse_combo)

            master_layout.addWidget(parse_widget)

            file_button = QPushButton('from file...')
            file_button.clicked.connect(self.load_file)
            master_layout.addWidget(file_button)

            ok_button = QPushButton('OK')
            ok_button.clicked.connect(self.commit_parse)
            master_layout.addWidget(ok_button)

    def parse(self):
        if not self.parsers:
            raise self.parse_exception('this widget cannot parse')
        parser: PlaintextParser = self.parse_combo.currentData() if self.parse_combo else self.parsers[0]
        if not parser:
            raise self.parse_exception('no parser configured')

        try:
            return parser(self.parse_edit.toPlainText())
        except PlaintextParseError as e:
            raise self.parse_exception('parser failed') from e

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

    def update_print(self, *args):
        if self.current_value is self.NO_CURRENT_VALUE:
            text = '<no current value>'
        else:
            printer: PlaintextPrinter = self.print_combo.currentData() if self.print_combo else self.printers[0]
            if not printer:
                text = '<no printer configured>'
            else:
                try:
                    text = printer(self.current_value)
                except PlaintextPrintError as e:
                    text = f'<printer error: {e}>'

        self.print_edit.setPlainText(text)

    def set_current_value(self, value: T):
        self.current_value = value
        self.print_widget.setVisible(value is not self.NO_CURRENT_VALUE)
        self.update_print()

    def commit_parse(self):
        try:
            self.result_value = self.parse()
        except ParseError as e:
            QMessageBox.critical(self, 'error during parse', str(e))
        else:
            self.result_outcome = True
            self.accept()

    @property
    def has_parse(self):
        return bool(self.parsers)

    @property
    def has_print(self):
        return bool(self.printers)
