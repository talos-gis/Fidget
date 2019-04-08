from __future__ import annotations

from typing import Generic, TypeVar, Optional, Callable, Tuple, Iterable, Type, Dict, Any, Union, List

from abc import abstractmethod
from contextlib import contextmanager
from pathlib import Path
from functools import partial, wraps, reduce
from itertools import chain

from fidget.backend.QtWidgets import QWidget, QPlainTextEdit, QPushButton, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, \
    QMessageBox, QFileDialog, QGroupBox, QGridLayout, QDialog, QSizePolicy, QBoxLayout
from fidget.backend.QtCore import Qt, pyqtSignal, __backend__

from fidget.core.plaintext_adapter import PlaintextParseError, PlaintextPrintError, \
    join_parsers, join_printers, PlaintextParser, PlaintextPrinter, \
    format_spec_input_printer, formatted_string_input_printer, exec_printer, eval_printer, \
    sort_adapters
from fidget.core.fidget_value import FidgetValue, BadValue, GoodValue, ParseError, ValidationError
from fidget.core.primitive_questions import FontQuestion
from fidget.core.__util__ import error_details, first_valid, error_attrs, optional_valid

T = TypeVar('T')


# todo automatically create template if QApplication isn't instantiated?⌡

class TemplateLike(Generic[T]):
    @abstractmethod
    def template_of(self) -> FidgetTemplate[T]:
        pass

    @classmethod
    @abstractmethod
    def template(cls, *args, **kwargs) -> FidgetTemplate[T]:
        pass


class FidgetTemplate(Generic[T], TemplateLike[T]):
    """
    A template for a Fidget
    """

    def __init__(self, widget_cls: Type[Fidget[T]], args: Tuple, kwargs: Dict[str, Any]):
        """
        :param widget_cls: the class of the Fidget
        :param args: the positional arguments of the template
        :param kwargs: the keyword arguments of the template
        """
        self.widget_cls = widget_cls
        self.args = args
        self.kwargs = kwargs
        self._instance: Optional[Fidget[T]] = None

    @property
    def title(self) -> Optional[str]:
        """
        The title of the template, or None if one has not been provided
        """
        if self.args:
            ret = self.args[0]
            if not isinstance(ret, str):
                raise TypeError('first parameter of a template must be the title string')
            return ret
        else:
            return None

    def _partial(self):
        return partial(self.widget_cls, *self.args, **self.kwargs)

    def __call__(self, *args, **kwargs) -> Fidget[T]:
        """
        Create a widget form the template. args and kwargs are forwarded to the class constructor.
        """
        return self._partial()(*args, **kwargs)

    def set_default(self, **kwargs):
        for key in list(kwargs.keys()):
            if key in self.kwargs:
                del kwargs[key]
        return self.template(**kwargs)

    def template(self, *args, **kwargs):
        """
        Create a further template from additional parameters
        """
        args = self.args + args
        kwargs = {**self.kwargs, **kwargs}
        return type(self)(self.widget_cls, args, kwargs)

    def template_of(self):
        """
        return a template representing this template
        """
        return self

    def extract_default(*templates: FidgetTemplate, sink: dict, upper_space, keys: Iterable[str] = ...,
                        union=True):
        """
        inject the default values from a template or collection of templates as defaults for keyword arguments.

        :param templates: A tuple of templates to extract from
        :param sink: the dict to set defaults for
        :param upper_space: a namespace, if a key exists in uppercase in that namespace as not None, the key is not
            filled into sink.
        :param keys: a list of keys to extract
        :param union: whether to perform a union or intersect in case of multiple, conflicting default values
        """

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

    def instance(self):
        """
        :return: a singleton instantiation of this template
        """
        if self._instance is None:
            self._instance = self()
        return self._instance


class Fidget(QWidget, Generic[T], TemplateLike[T]):
    """
    A QWidget that can contain a value, parsed form its children widgets.
    """
    on_change: pyqtSignal

    # region inherit_me
    """
    How do I inherit Fidget?
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
    FLAGS = Qt.WindowFlags()

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
                 help: str = None,
                 **kwargs):
        """
        :param title: the title of the Fidget
        :param args: additional arguments forwarded to QWidget
        :param validation_func: a validation callable, that will raise ValidationError if the parsed value is invalid
        :param auto_func: a function that returns an automatic value, to fill in the UI
        :param make_title: whether to create a title widget
        :param make_indicator: whether to make an indicator widget
        :param make_plaintext: whether to make a plaintext_edit widget
        :param help: a help string to describe the widget
        :param kwargs: additional arguments forwarded to QWidget

        :inheritors: don't set default values for these parameters, change the uppercase class variables instead.
        """
        if kwargs.get('flags', None) is None:
            kwargs['flags'] = self.FLAGS

        if 'flags' in kwargs and __backend__.__name__ == 'PySide2':
            kwargs['f'] = kwargs.pop('flags')

        try:
            super().__init__(*args, **kwargs)
        except (TypeError, AttributeError):
            print(f'args: {args}, kwargs: {kwargs}')
            raise
        self.title = title
        self.help = help

        self.make_title = first_valid(make_title=make_title, MAKE_TITLE=self.MAKE_TITLE, _self=self)
        self.make_indicator = first_valid(make_indicator=make_indicator, MAKE_INDICATOR=self.MAKE_INDICATOR, _self=self)
        self.make_plaintext = first_valid(make_plaintext=make_plaintext, MAKE_PLAINTEXT=self.MAKE_PLAINTEXT, _self=self)

        self.indicator_label: Optional[QLabel] = None
        self.auto_button: Optional[QPushButton] = None
        self.plaintext_button: Optional[QPushButton] = None
        self.title_label: Optional[QLabel] = None

        self._plaintext_widget: Optional[PlaintextEditWidget[T]] = None

        self.validation_func = validation_func
        self.auto_func = optional_valid(auto_func=auto_func, AUTO_FUNC=self.AUTO_FUNC, _self=self)

        self._suppress_update = False

        self._value: FidgetValue[T] = None
        self._joined_plaintext_printer = None
        self._joined_plaintext_parser = None

        self._plaintext_printer_delegates: List[Callable[[], Iterable[PlaintextPrinter[T]]]] = []
        self._plaintext_parser_delegates: List[Callable[[], Iterable[PlaintextParser[T]]]] = []

        if self.auto_func:
            if self.fill is None:
                raise Exception('auto_func can only be used on a Fidget with an implemented fill method')
            else:
                self.make_auto = True
        else:
            self.make_auto = False

    def init_ui(self) -> Optional[QBoxLayout]:
        """
        initialise the internal widgets of the Fidget
        :inheritors: If you intend your class to be subclassed, don't add any widgets to self.
        """
        self.setWindowTitle(self.title)

        if self.make_indicator:
            self.indicator_label = QLabel('')
            self.indicator_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
            self.indicator_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.indicator_label.linkActivated.connect(self._detail_button_clicked)

        if self.make_auto:
            self.auto_button = QPushButton('auto')
            self.auto_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.auto_button.clicked.connect(self._auto_btn_click)

        if self.make_plaintext:
            self.plaintext_button = QPushButton('text')
            self.plaintext_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.plaintext_button.clicked.connect(self._plaintext_btn_click)

            self._plaintext_widget = PlaintextEditWidget(parent=self)

        if self.make_title:
            self.title_label = QLabel(self.title)
            self.title_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            if self.help:
                self.title_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
                self.title_label.linkActivated.connect(self._help_clicked)

    # implement this method to allow the widget to be filled from outer elements (like plaintext or auto)
    # note that this function shouldn't be called form outside!, only call fill_value
    fill: Optional[Callable[[Fidget[T], T], None]] = None
    AUTO_FUNC: Optional[Callable[[Fidget[T]], T]] = None

    @abstractmethod
    def parse(self) -> T:
        """
        Parse the internal UI and returned a parsed value. Or raise ParseException.
        :return: the parsed value
        """
        pass

    def validate(self, value: T) -> None:
        """
        Raise a ValidationError if the value is invalid
        :param value: the parsed value
        :inheritors: always call super().validate
        """
        if self.validation_func:
            self.validation_func(value)

    @classmethod
    def cls_plaintext_printers(cls) -> Iterable[PlaintextPrinter[T]]:
        yield from cls._inner_cls_plaintext_printers()
        yield str
        yield repr
        yield format_spec_input_printer
        yield formatted_string_input_printer
        yield eval_printer
        yield exec_printer

    def plaintext_printers(self) -> Iterable[PlaintextPrinter[T]]:
        """
        :return: an iterator of plaintext printers for the widget
        """
        yield from self._inner_plaintext_printers()
        for d in self._plaintext_printer_delegates:
            yield from d()
        yield from self.cls_plaintext_printers()

    @classmethod
    def cls_plaintext_parsers(cls) -> Iterable[PlaintextParser[T]]:
        yield from cls._inner_cls_plaintext_parsers()

    def plaintext_parsers(self) -> Iterable[PlaintextParser[T]]:
        """
        :return: an iterator of plaintext parsers for the widget
        """
        yield from self._inner_plaintext_parsers()
        for d in self._plaintext_parser_delegates:
            yield from d()
        yield from self.cls_plaintext_parsers()

    def indication_changed(self, value: Union[GoodValue[T], BadValue]):
        pass

    # endregion

    # region call_me
    @contextmanager
    def suppress_update(self, new_value=True, call_on_exit=True):
        """
        A context manager, while called, will suppress updates to the indicator. will update the indicator when exited.
        """
        prev_value = self._suppress_update
        self._suppress_update = new_value
        yield new_value
        self._suppress_update = prev_value
        if call_on_exit:
            self.change_value()

    @property
    def joined_plaintext_parser(self):
        """
        :return: A joining of the widget's plaintext parsers
        """
        if not self._joined_plaintext_parser:
            self._joined_plaintext_parser = join_parsers(self.plaintext_parsers)
        return self._joined_plaintext_parser

    @property
    def joined_plaintext_printer(self):
        """
        :return: A joining of the widget's plaintext printers
        """
        if not self._joined_plaintext_printer:
            self._joined_plaintext_printer = join_printers(self.plaintext_printers)
        return self._joined_plaintext_printer

    def implicit_plaintext_parsers(self):
        for parser, priority in sort_adapters(self.plaintext_parsers()):
            if priority < 0:
                return
            yield parser

    def implicit_plaintext_printers(self):
        for printer, priority in sort_adapters(self.plaintext_printers()):
            if priority < 0:
                return
            yield printer

    @classmethod
    def implicit_cls_plaintext_parsers(cls):
        for parser, priority in sort_adapters(cls.cls_plaintext_parsers()):
            if priority < 0:
                return
            yield parser

    @classmethod
    def implicit_cls_plaintext_printers(cls):
        for printer, priority in sort_adapters(cls.cls_plaintext_printers()):
            if priority < 0:
                return
            yield printer

    def provided_pre(self, exclude=()):
        """
        Get an iterator of the widget's provided widgets that are to appear before the main UI.
        :param exclude: whatever widgets to exclude
        """
        return (yield from (
            y for y in (self.title_label,)
            if y and y not in exclude
        ))

    def provided_post(self, exclude=()):
        """
        Get an iterator of the widget's provided widgets that are to appear after the main UI.
        :param exclude: whatever widgets to exclude
        """
        return (yield from (
            y for y in (self.indicator_label,
                        self.auto_button,
                        self.plaintext_button)
            if y and y not in exclude
        ))

    @contextmanager
    def setup_provided(self, pre_layout: QVBoxLayout, post_layout=..., exclude=()):
        """
        a context manager that will add the pre_provided widgets before the block and the post_provided after it.
        :param pre_layout: a layout to add the pre_provided to
        :param post_layout: a layout to add teh post_provided to, default is to use pre_layout
        :param exclude: which provided widgets to exclude
        """
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
    def maybe_parse(self):
        if self._value is None or not self._value.is_ok():
            return self.parse()
        return self._value.value

    def maybe_validate(self, v):
        if self._value is None:
            self.validate(v)

    def fill_from_text(self, s: str):
        """
        fill the UI from a string, by parsing it
        :param s: the string to parse
        """
        if not self.fill:
            raise Exception(f'widget {self} does not have its fill function implemented')
        self.fill_value(self.joined_plaintext_parser(s))

    def value(self) -> Union[GoodValue[T], BadValue]:
        """
        :return: the current value of the widget
        """
        if self._value is None:
            self._reload_value()
        return self._value

    def change_value(self, *args):
        """
        a slot to refresh the value of the widget
        """
        self._invalidate_value()
        self._update_indicator()
        self.on_change.emit()

    _template_class: Type[FidgetTemplate[T]] = FidgetTemplate

    @classmethod
    @wraps(__init__)
    def template(cls, *args, **kwargs) -> FidgetTemplate[T]:
        """
        get a template of the type
        :param args: arguments for the template
        :param kwargs: keyword arguments for the template
        :return: the template
        """
        return cls._template_class(cls, args, kwargs)

    def template_of(self) -> FidgetTemplate[T]:
        """
        get a template to recreate the widget
        """
        a, k = self.__new_args
        ret = self.template(*a, **k)
        return ret

    @classmethod
    def template_class(cls, class_):
        """
        Assign a class to be this widget class's template class
        """
        cls._template_class = class_
        return class_

    def __str__(self):
        try:
            return super().__str__() + ': ' + self.title
        except AttributeError:
            return super().__str__()

    def fill_value(self, *args, **kwargs):
        with self.suppress_update():
            return self.fill(*args, **kwargs)

    def add_plaintext_printers_delegate(self, delegate: Callable[[], Iterable[PlaintextPrinter[T]]]):
        self._plaintext_printer_delegates.append(delegate)
        self._joined_plaintext_printer = None

    def add_plaintext_parsers_delegate(self, delegate: Callable[[], Iterable[PlaintextParser[T]]]):
        self._plaintext_parser_delegates.append(delegate)
        self._joined_plaintext_parser = None

    def add_plaintext_delegates(self, clone: Union[Fidget, Type[Fidget]]):
        if isinstance(clone, Fidget):
            self.add_plaintext_parsers_delegate(clone.plaintext_parsers)
            self.add_plaintext_printers_delegate(clone.plaintext_printers)
        elif isinstance(clone, type) and issubclass(clone, Fidget):
            self.add_plaintext_printers_delegate(clone.cls_plaintext_printers)
            self.add_plaintext_parsers_delegate(clone.cls_plaintext_parsers)
        else:
            raise TypeError(type(clone))

    # endregion

    def _invalidate_value(self):
        """
        Mark the cached value is invalid, forcing it to be re-processed when needed next
        """
        self._value = None

    def _auto_btn_click(self, click_args):
        """
        autofill the widget
        """
        try:
            value = self.auto_func()
        except DoNotFill as e:
            if str(e):
                QMessageBox.critical(self, 'error during autofill', str(e))
            return

        self.fill_value(value)

    def _plaintext_btn_click(self):
        """
        open the plaintext dialog
        """
        self._plaintext_widget.prep_for_show()
        self._plaintext_widget.show()

    def _update_indicator(self, *args):
        """
        update whatever indicators need updating when the value is changed
        """
        if self._suppress_update:
            return

        value = self.value()

        if self.indicator_label and self.indicator_label.parent():
            if value.is_ok():
                text = "<a href='...'>OK</a>"
            else:
                text = "<a href='...'>ERR</a>"
            tooltip = value.short_details

            self.indicator_label.setText(text)
            self.indicator_label.setToolTip(tooltip)

        if self.plaintext_button:
            self.plaintext_button.setEnabled(value.is_ok() or any(self.plaintext_parsers()))

        self.indication_changed(value)

    def _reload_value(self):
        """
        reload the cached value
        """
        assert self._value is None, '_reload called when a value is cached'
        try:
            value = self.parse()
            self.validate(value)
        except (ValidationError, ParseError) as e:
            self._value = BadValue.from_error(e)
            return

        try:
            details = self.joined_plaintext_printer(value)
        except PlaintextPrintError as e:
            details = 'details could not be loaded because of a parser error:\n' + error_details(e)
        self._value = GoodValue(value, details)

    def _detail_button_clicked(self, event):
        """
        show details of the value
        """
        value = self.value()
        if value.details:
            QMessageBox.information(self, value.type_details, value.details)

        if not value.is_ok():
            offender: QWidget = reduce(lambda x, y: y, error_attrs(value.exception, 'offender'), None)
            if offender:
                offender.setFocus()

    def _help_clicked(self, event):
        """
        show help message
        """
        if self.help:
            QMessageBox.information(self, self.title, self.help)

    @staticmethod
    def _inner_plaintext_parsers():
        """
        get the inner plaintext parsers
        """
        yield from ()

    @staticmethod
    def _inner_plaintext_printers():
        """
        get the inner plaintext printers
        """
        yield from ()

    @staticmethod
    def _inner_cls_plaintext_printers():
        yield from ()

    @staticmethod
    def _inner_cls_plaintext_parsers():
        yield from ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.on_change = pyqtSignal()

        inner_printers = []
        inner_parsers = []
        inner_cls_printers = []
        inner_cls_parsers = []
        for v in cls.__dict__.values():
            if getattr(v, '__plaintext_printer__', False):
                if getattr(v, '__is_cls__', False) or isinstance(v, (classmethod, staticmethod)):
                    inner_cls_printers.append(v)
                else:
                    inner_printers.append(v)
            if getattr(v, '__plaintext_parser__', False):
                if getattr(v, '__is_cls__', False) or isinstance(v, (classmethod, staticmethod)):
                    inner_cls_parsers.append(v)
                else:
                    inner_parsers.append(v)

        if inner_printers:
            def inner_printers_func(self):
                yield from (p.__get__(self, type(self)) for p in inner_printers)

            cls._inner_plaintext_printers = inner_printers_func

        if inner_parsers:
            def inner_parsers_func(self):
                yield from (p.__get__(self, type(self)) for p in inner_parsers)

            cls._inner_plaintext_parsers = inner_parsers_func

        if inner_cls_printers:
            def inner_cls_printers_func(cls):
                yield from (p.__get__(None, cls) for p in inner_cls_printers)

            cls._inner_cls_plaintext_printers = classmethod(inner_cls_printers_func)

        if inner_cls_parsers:
            def inner_cls_parsers_func(cls):
                yield from (p.__get__(None, cls) for p in inner_cls_parsers)

            cls._inner_cls_plaintext_parsers = classmethod(inner_cls_parsers_func)


class DoNotFill(Exception):
    """
    if this exception is raised from an auto_func, a value is not filled in.
    """
    pass


class PlaintextEditWidget(Generic[T], Fidget[T]):
    """
    plaintext dialog for a Fidget
    """

    class _ShiftEnterIgnoringPlainTextEdit(QPlainTextEdit):
        """
        A QPlainTextEdit that ignores shift+enter
        """

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
    FLAGS = Qt.Dialog

    def __init__(self, *args, **kwargs):
        super().__init__('plaintext edit', *args, **kwargs)

        self.current_value: T = self.NO_CURRENT_VALUE

        self.print_widget: QWidget = None
        self.print_edit: QPlainTextEdit = None
        self.print_combo: QComboBox = None
        self.ok_button: QPushButton = None
        self.apply_button: QPushButton = None

        self.font_button: QPushButton = None
        self.clone_button: QPushButton = None

        self.parse_widget: QWidget = None
        self.parse_edit: PlaintextEditWidget._ShiftEnterIgnoringPlainTextEdit = None
        self.parse_combo: QComboBox = None

        self.owner: Fidget = kwargs.get('parent')

        self.init_ui()

    def init_ui(self) -> Optional[QBoxLayout]:
        super().init_ui()
        self.setWindowModality(Qt.WindowModal)

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

        self.clone_button = QPushButton('🡇')
        self.clone_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.clone_button.clicked.connect(self._clone_btn_clicked)
        master_layout.addWidget(self.clone_button)

        self.parse_widget = QGroupBox('set value:')
        parse_master_layout = QVBoxLayout(self.parse_widget)

        parse_layout = QHBoxLayout()
        parse_master_layout.addLayout(parse_layout)

        self.parse_edit = self._ShiftEnterIgnoringPlainTextEdit()
        self.parse_edit.textChanged.connect(self.change_value)
        self.print_combo.activated.connect(self.update_print)
        parse_layout.addWidget(self.parse_edit)

        parse_extras_layout = QGridLayout()

        self.parse_combo = QComboBox()
        self.parse_combo.activated.connect(self.change_value)
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

        self.font_button = QPushButton('font...')
        self.font_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.font_button.clicked.connect(self._choose_font)
        master_layout.addWidget(self.font_button)

        self.on_change.connect(self._on_value_change)

        return master_layout

    def parse(self):
        parser: PlaintextParser = self.parse_combo.currentData()
        if not parser:
            raise ParseError('no parser configured', offender=self.parse_combo)

        try:
            return parser(self.parse_edit.toPlainText())
        except PlaintextParseError as e:
            raise ParseError(offender=self.parse_edit) from e

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
                    text = f'<printer error>\n{error_details(e)}'

        self.print_edit.setPlainText(text)

    def prep_for_show(self, clear_parse=True, clear_print=True):
        """
        prepare a dialog with a new owner and value.
        :param clear_parse: whether to clear and reset the parse UI
        :param clear_print: whether to clear and reset the print UI
        """

        self.setWindowTitle('plaintext edit for ' + self.owner.title)

        self.clone_button.setVisible(False)

        owner_value = self.owner.value()
        printers = list(self.owner.plaintext_printers())
        if not owner_value.is_ok() or not printers:
            self.print_widget.setVisible(False)
            printers = False
        else:
            self.current_value = owner_value.value

            self.print_widget.setVisible(True)
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
                self.print_combo.addItem('<all>', self.owner.joined_plaintext_printer)
            else:
                self.print_combo.setVisible(False)

            for printer, priority in sort_adapters(printers):
                name = printer.__name__
                if priority < 0:
                    name += '*'
                self.print_combo.addItem(name, printer)

            self.print_combo.setCurrentIndex(combo_index)
            self.print_combo.activated[int].emit(combo_index)

        parsers = list(self.owner.plaintext_parsers())
        if not parsers:
            self.parse_widget.setVisible(False)
        else:
            if printers:
                self.clone_button.setVisible(True)
            if not self.owner.fill:
                raise Exception(
                    f'parsers are defined but the widget has no implemented fill method (in widget {self.owner})')

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
                self.parse_combo.addItem('<all>', self.owner.joined_plaintext_parser)
            else:
                self.parse_combo.setVisible(False)

            for parser, priority in sort_adapters(parsers):
                name = parser.__name__
                if priority < 0:
                    name += '*'
                self.parse_combo.addItem(name, parser)
            self.parse_combo.setCurrentIndex(combo_index)
            self.parse_combo.activated[int].emit(combo_index)

        if not printers and not parsers:
            raise ValueError('plaintext edit widget prepped for owner without any plaintext adapters')

    def commit_parse(self):
        value = self.value()
        if not value.is_ok():
            QMessageBox.critical(self, 'error parsing plaintext', value.details)
        else:
            self.owner.fill(value.value)
            self.close()

    def apply_parse(self):
        value = self.value()
        if not value.is_ok():
            QMessageBox.critical(self, 'error parsing plaintext', value.details)
        else:
            self.owner.fill(value.value)
            self.prep_for_show(clear_parse=False, clear_print=False)
            self.parse_edit.setFocus()

    @property
    def has_parse(self):
        return bool(self.parsers)

    @property
    def has_print(self):
        return bool(self.printers)

    def _on_value_change(self, *a):
        value = self.value()

        self.ok_button.setEnabled(value.is_ok())
        self.apply_button.setEnabled(value.is_ok())

    def _detail_button_clicked(self, event):
        super()._detail_button_clicked(event)
        value = self.value()
        if not value.is_ok():
            cursor_pos = sum(
                (cp for cp in error_attrs(value.exception, 'cursor_pos') if cp is not None)
                , 0)
            if cursor_pos is not None:
                cursor = self.parse_edit.textCursor()
                if cursor:
                    cursor.setPosition(cursor_pos)
                    self.parse_edit.setTextCursor(cursor)

    def _choose_font(self, arg):
        instance = FontQuestion.instance()
        if instance.exec_() == QDialog.Rejected:
            return
        font_family, size = instance.ret
        for edit in (self.parse_edit, self.print_edit):
            font = edit.document().defaultFont()
            if font_family:
                font.setFamily(font_family)
            if size:
                font.setPointSize(size)
            edit.document().setDefaultFont(font)

    def _clone_btn_clicked(self, arg):
        text = self.print_edit.toPlainText()
        self.parse_edit.setPlainText(text)

    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Return) \
                or (event.modifiers() == Qt.KeypadModifier | Qt.ShiftModifier and event.key() == Qt.Key_Enter):
            self.ok_button.click()
        elif not event.modifiers() and event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
