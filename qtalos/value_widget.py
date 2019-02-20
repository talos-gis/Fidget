from __future__ import annotations

from typing import Generic, TypeVar, Optional, Callable, Tuple, Union, Iterable, Sequence

from abc import abstractmethod
from enum import Enum, auto
from contextlib import contextmanager

from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QDialog
from PyQt5.QtCore import Qt

from qtalos.plaintext_adapter import PlaintextPrinter, PlaintextParser, PlaintextParseError, PlaintextPrintError, \
    StrPrinter, ReprPrinter
from qtalos.__util__ import throwaway_cache, error_details

T = TypeVar('T')


# todo document this bulcrap

class ValueState(Enum):
    ok = auto()
    invalid = auto()
    unparsable = auto()


class ValueWidget(QWidget, Generic[T]):
    NO_RESULT = object()

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

        self._plaintext_widget: Optional[PlaintextEditWidget[T]] = None

        self.validation_func = validation_func
        self.auto_func = auto_func

        self._suppress_update = False
        self._validation_details = None

        if self.auto_func:
            if self.fill is None:
                raise Exception('auto_func can only be used on a ValueWidget with an implemented fill method')
            else:
                self.make_auto_button = True
        else:
            self.make_auto_button = False

        self.result = self.NO_RESULT, self.NO_RESULT

    def init_ui(self):
        if self.make_validator_label:
            self.validation_label = QLabel('')
            self.validation_label.mousePressEvent = self.show_validation_details

        if self.make_auto_button:
            self.auto_button = QPushButton('auto')
            self.auto_button.clicked.connect(self.auto_fill)

        if self.make_plaintext_button:
            self.plaintext_button = QPushButton('text')
            self.plaintext_button.clicked.connect(self.show_plaintext_dialog)

            self._plaintext_widget = PlaintextEditWidget(self)

            if self._plaintext_widget.has_parse and self.fill is None:
                raise Exception('parsers are defined but the widget has no implemented fill method')

    def parse_exception(self, *args, **kwargs):
        return ParseError(self, *args, **kwargs)

    def validation_exception(self, value: T, *args, **kwargs):
        return ValidationError(self, value, *args, **kwargs)

    def update_indicator(self, *args, **kwargs):
        if self._suppress_update:
            return

        value_func = throwaway_cache(self.value)

        if self.validation_label and self.validation_label.parent():
            state, val = value_func()
            if state == ValueState.ok:
                text = 'OK'
                self._validation_details = repr(val)
            else:
                text = 'ERR'
                self._validation_details = error_details(val)
            explanation = str(val)

            self.validation_label.setText(text)
            self.validation_label.setToolTip(explanation)

        if self.plaintext_button and self.plaintext_button.parent():
            if not self._plaintext_widget.has_parse:
                state, _ = value_func()
                self.plaintext_button.setEnabled(state == ValueState.ok)

    def show_validation_details(self, event):
        if self._validation_details:
            QMessageBox.information(self, 'error during validation', self._validation_details)

    def auto_fill(self, click_args):
        try:
            value = self.auto_func()
        except DoNotFill as e:
            if str(e):
                QMessageBox.critical(self, 'error during autofill', str(e))
            return

        with self.suppress_update():
            self.fill(value)

    def show_plaintext_dialog(self):
        state, value = self.value()
        if state != ValueState.ok:
            value = PlaintextEditWidget.NO_CURRENT_VALUE
        self._plaintext_widget.set_current_value(value)
        if self._plaintext_widget.exec_() == QDialog.Accepted:
            self.fill(self._plaintext_widget.result_value)

    def validate(self, value: T) -> None:
        if self.validation_func:
            self.validation_func(value)

    def value(self) -> Tuple[ValueState, Union[ParseError, ValidationError, T]]:
        try:
            value = self.parse()
        except ParseError as e:
            return ValueState.unparsable, e

        try:
            self.validate(value)
        except ValidationError as e:
            return ValueState.invalid, e

        return ValueState.ok, value

    @abstractmethod
    def parse(self) -> T:
        pass

    fill: Optional[Callable[[ValueWidget[T], T], None]] = None

    @contextmanager
    def suppress_update(self, new_value=True, call_on_exit=True):
        prev_value = self._suppress_update
        self._suppress_update = new_value
        yield new_value
        self._suppress_update = prev_value
        if call_on_exit:
            self.update_indicator()

    @classmethod
    def plaintext_printers(cls) -> Iterable[PlaintextPrinter[T]]:
        yield StrPrinter
        yield ReprPrinter

    @classmethod
    def plaintext_parsers(cls) -> Iterable[PlaintextParser[T]]:
        yield from ()

    def closeEvent(self, a0):
        super().closeEvent(a0)
        self.result = self.value()


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


# todo default parser (try everything)
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
            print_layout = QHBoxLayout(self.print_widget)

            print_layout.addWidget(QLabel('current value:'))

            self.print_edit = QPlainTextEdit()
            self.print_edit.setReadOnly(True)
            print_layout.addWidget(self.print_edit)

            self.print_combo = QComboBox()
            for printer in self.printers:
                self.print_combo.addItem(printer.name, printer)
            self.print_combo.setCurrentIndex(0)
            self.print_combo.currentIndexChanged[int].connect(self.update_print)
            print_layout.addWidget(self.print_combo)

            master_layout.addWidget(self.print_widget)

        if self.parsers:
            parse_widget = QWidget()

            parse_layout = QHBoxLayout()
            parse_widget.setLayout(parse_layout)

            parse_layout.addWidget(QLabel('set value:'))

            self.parse_edit = QPlainTextEdit()
            self.parse_edit.textChanged.connect(self.update_parse)
            parse_layout.addWidget(self.parse_edit)

            if self.validation_label:
                parse_layout.addWidget(self.validation_label)

            self.parse_combo = QComboBox(parse_layout.widget())
            for parser in self.parsers:
                self.parse_combo.addItem(parser.name, parser)
            self.parse_combo.setCurrentIndex(0)
            self.parse_combo.currentIndexChanged[int].connect(self.update_parse)
            parse_layout.addWidget(self.parse_combo)

            master_layout.addWidget(parse_widget)

            ok_button = QPushButton('OK')
            ok_button.clicked.connect(self.commit_parse)
            master_layout.addWidget(ok_button)

    def parse(self):
        if not self.parsers:
            raise self.parse_exception('this widget cannot parse')
        parser: PlaintextParser = self.parse_combo.currentData()
        if not parser:
            raise self.parse_exception('no parser configured')

        try:
            return parser.from_string(self.parse_edit.toPlainText())
        except PlaintextParseError as e:
            raise self.parse_exception('parser failed') from e

    def update_print(self, *args):
        if self.current_value is self.NO_CURRENT_VALUE:
            text = '<no current value>'
        else:
            printer: PlaintextPrinter = self.print_combo.currentData()
            if not printer:
                text = '<no printer configured>'
            else:
                try:
                    text = printer.to_string(self.current_value)
                except PlaintextPrintError as e:
                    text = f'<printer error: {e}>'

        self.print_edit.setPlainText(text)

    def update_parse(self, *args):
        self.update_indicator()

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
