from __future__ import annotations

from typing import TypeVar, Generic, Union, NoReturn, Callable

from fidget.backend.QtWidgets import QHBoxLayout, QApplication, QPushButton, QVBoxLayout, QBoxLayout, QMessageBox, \
    QWidget
from fidget.backend.QtCore import Qt, QEventLoop

from fidget.core import Fidget, FidgetTemplate, ParseError, TemplateLike, inner_plaintext_printer, PlaintextPrintError
from fidget.core.__util__ import first_valid

from fidget.widgets.idiomatic_inner import SingleFidgetWrapper
from fidget.widgets.__util__ import only_valid

T = TypeVar('T')
C = TypeVar('C')


class FidgetConfirmer(Generic[T, C], SingleFidgetWrapper[T, Union[T, C]]):
    """
    A Fidget that wraps another Fidget. Adding an Ok and (potentially) Cancel buttons, that trigger this
    Fidget's validation. Useful for dialogs or for slow validations
    """
    NO_CANCEL: NoReturn = object()

    def __init__(self, inner_template: TemplateLike[T] = None, layout_cls=None,
                 cancel_value: C = NO_CANCEL, close_on_confirm=None, ok_text=None, cancel_text=None,
                 window_modality=None, **kwargs):
        """
        :param inner_template: an inner template to wrap
        :param layout_cls: the class of the layout
        :param cancel_value: the value to parse upon the cancel button being clicked. If this argument is provided,
         a cancel button is created.
        :param close_on_confirm: whether to close this widget if Ok or Cancel is clicked and the value is valid.
        :param ok_text: text for the ok button
        :param cancel_text: text for the cancel button
        :param window_modality: the modality of the widget, convenience parameter
        :param kwargs: forwarded to Fidget
        """
        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE, _self=self).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.inner: Fidget[T] = None
        self.ok_button: QPushButton = None
        self.cancel_button: QPushButton = None

        self.cancel_value = cancel_value
        self.make_cancel = cancel_value is not self.NO_CANCEL
        self.cancel_flag = False

        self.close_on_confirm = first_valid(close_on_confirm=close_on_confirm, CLOSE_ON_CONFIRM=self.CLOSE_ON_CONFIRM, _self=self)

        self.init_ui(layout_cls=layout_cls, ok_text=ok_text, cancel_text=cancel_text, modality=window_modality)

        self._inner_changed()

    INNER_TEMPLATE: FidgetTemplate[T] = None
    LAYOUT_CLS = QVBoxLayout
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = False
    CLOSE_ON_CONFIRM = False
    WINDOW_MODALITY = None
    OK_TEXT = 'OK'
    CANCEL_TEXT = 'Cancel'

    def init_ui(self, layout_cls=None, ok_text=None, cancel_text=None, modality=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS, _self=self)
        modality = modality or self.WINDOW_MODALITY

        layout: QBoxLayout = layout_cls(self)

        self.inner = self.inner_template()

        with self.setup_provided(layout):
            self.inner.on_change.connect(self._inner_changed)

            layout.addWidget(self.inner)

            btn_layout = QHBoxLayout()
            if self.make_cancel:
                self.cancel_button = QPushButton(first_valid(cancel_text=cancel_text, CANCEL_TEXT=self.CANCEL_TEXT, _self=self))
                self.cancel_button.clicked.connect(self._cancel_btn_clicked)
                btn_layout.addWidget(self.cancel_button)

            self.ok_button = QPushButton(first_valid(ok_text=ok_text, CANCEL_TEXT=self.OK_TEXT, _self=self))
            self.ok_button.clicked.connect(self._ok_btn_clicked)
            btn_layout.addWidget(self.ok_button)

            layout.addLayout(btn_layout)

        self.setFocusProxy(self.inner)

        if modality:
            self.setWindowModality(modality)
        #if not self.make_cancel:
            #self.setWindowFlags(Qt.WindowMinimizeButtonHint)

        self.add_plaintext_delegates(self.inner)
        return layout

    def parse(self):
        if self.cancel_flag:
            if self.make_cancel:
                return self.cancel_value
            raise ParseError('invalid cancel value')
        inner_value = self.inner.value()
        if not inner_value.is_ok():
            raise ParseError(offender=self.inner) from inner_value.exception
        return inner_value.value

    @staticmethod
    def to_widget(w: Union[QWidget, Callable[[], QWidget], None]):
        if not w or isinstance(w, QWidget):
            return w
        return w()

    def _inner_changed(self):
        value = self.inner.value()
        self.ok_button.setEnabled(value.is_ok())

    def _ok_btn_clicked(self, *a):
        self.cancel_flag = False
        self.change_value()
        if self.close_on_confirm:
            value = self.value()
            if value.is_ok():
                self.close()
            else:
                QMessageBox.critical(self, 'error parsing value', value.details)

    def _cancel_btn_clicked(self, *a):
        self.cancel_flag = True
        self.change_value()
        if self.close_on_confirm:
            value = self.value()
            if value.is_ok():
                self.close()
            else:
                QMessageBox.critical(self, 'error parsing value', value.details)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return \
                or (event.modifiers() == Qt.KeypadModifier and event.key() == Qt.Key_Enter):
            self.ok_button.click()
        elif self.cancel_button and (not event.modifiers() and event.key() == Qt.Key_Escape):
            self.cancel_button.click()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if event.spontaneous():
            self.cancel_flag = True
            self.change_value()
        super().closeEvent(event)

    @inner_plaintext_printer
    def cancel_printer(self, v):
        if v is self.cancel_value:
            return str(v)
        raise PlaintextPrintError('cannot print non-cancel value')

    def fill(self, v):
        self.inner.fill(v)


class FidgetQuestion(Generic[T, C], FidgetConfirmer[T, C]):
    """
    A specialization of FidgetConfirmer designed for dialogs
    """
    CLOSE_ON_CONFIRM = True
    FLAGS = Qt.Dialog
    WINDOW_MODALITY = Qt.WindowModal

    def exec(self):
        """
        show the widget and block until its value is set
        """
        self.show()
        event_loop = QEventLoop()
        self.on_change.connect(event_loop.quit)
        event_loop.exec_()
        return self.value()

    exec_ = exec


def question(*args, **kwargs) -> \
        Callable[[TemplateLike[T]], FidgetTemplate[T]]:
    """
    decorator to wrap a Fidget template in a FidgetQuestion template
    :param args: forwarded to ConfirmFidget
    :param kwargs: forwarded to FidgetConfirmer
    :return: a FidgetConfirmer template
    """

    def ret(c: TemplateLike[T]) -> FidgetTemplate[T]:
        if isinstance(c, type) and issubclass(c, TemplateLike):
            template_of = c.template()
        elif isinstance(c, TemplateLike):
            template_of = c.template_of()
        else:
            raise TypeError(f'cannot wrap {c} in ask')

        return FidgetQuestion.template(template_of, *args, **kwargs)

    return ret


if __name__ == '__main__':
    from fidget.widgets import *

    app = QApplication([])

    w = FidgetConverter(
        FidgetConfirmer(
            FidgetInt.template('source ovr', make_title=True, make_indicator=True),
            cancel_value=None
        ),
        converter_func=lambda x: (x * x if isinstance(x, int) else None)
    )
    w.on_change.connect(lambda: print(w.value()))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
