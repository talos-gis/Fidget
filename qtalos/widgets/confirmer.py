from __future__ import annotations

from typing import TypeVar, Generic, Union, NoReturn, Callable, Type

from qtalos.backend.QtWidgets import QHBoxLayout, QApplication, QPushButton, QVBoxLayout, QBoxLayout, QMessageBox
from qtalos.backend.QtCore import Qt

from qtalos.core import ValueWidget, ValueWidgetTemplate, ParseError
from qtalos.core.__util__ import first_valid

from qtalos.widgets.widget_wrappers import SingleWidgetWrapper
from qtalos.widgets.__util__ import only_valid

T = TypeVar('T')
C = TypeVar('C')


class ConfirmValueWidget(Generic[T, C], SingleWidgetWrapper[T, Union[T, C]]):
    """
    A ValueWidget that wraps another ValueWidget. Adding an Ok and (potentially) Cancel buttons, that trigger this
    ValueWidget's validation. Useful for dialogs or for slow validations
    """
    NO_CANCEL: NoReturn = object()

    def __init__(self, inner_template: ValueWidgetTemplate[T] = None, layout_cls=None,
                 cancel_value: C = NO_CANCEL, close_on_confirm=None, ok_text=None, cancel_text=None,
                 **kwargs):
        """
        :param inner_template: an inner template to wrap
        :param layout_cls: the class of the layout
        :param cancel_value: the value to parse upon the cancel button being clicked. If this argument is provided,
         a cancel button is created.
        :param close_on_confirm: whether to close this widget if Ok or Cancel is clicked and the value is valid.
        :param ok_text: text for the ok button
        :param cancel_text: text for the cancel button
        :param kwargs: forwarded to ValueWidget
        """
        inner_template = only_valid(inner_template=inner_template, INNER_TEMPLATE=self.INNER_TEMPLATE).template_of()

        super().__init__(inner_template.title, **kwargs)

        self.inner_template = inner_template

        self.inner: ValueWidget[T] = None
        self.ok_button: QPushButton = None
        self.cancel_button: QPushButton = None

        self.cancel_value = cancel_value
        self.make_cancel = cancel_value is not self.NO_CANCEL
        self.cancel_flag = False

        self.close_on_confirm = first_valid(close_on_confirm=close_on_confirm, CLOSE_ON_CONFIRM=self.CLOSE_ON_CONFIRM)

        self.init_ui(layout_cls, ok_text=ok_text, cancel_text=cancel_text)

        self._inner_changed()

    INNER_TEMPLATE: ValueWidgetTemplate[T] = None
    LAYOUT_CLS = QVBoxLayout
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = False
    CLOSE_ON_CONFIRM = False
    OK_TEXT = 'Ok'
    CANCEL_TEXT = 'Cancel'

    def init_ui(self, layout_cls=None, ok_text=None, cancel_text=None):
        super().init_ui()
        layout_cls = first_valid(layout_cls=layout_cls, LAYOUT_CLS=self.LAYOUT_CLS)

        layout: QBoxLayout = layout_cls(self)

        self.inner = self.inner_template()

        with self.setup_provided(layout):
            self.inner.on_change.connect(self._inner_changed)

            layout.addWidget(self.inner)

            btn_layout = QHBoxLayout()
            if self.make_cancel:
                self.cancel_button = QPushButton(first_valid(cancel_text=cancel_text, CANCEL_TEXT=self.CANCEL_TEXT))
                self.cancel_button.clicked.connect(self._cancel_btn_clicked)
                btn_layout.addWidget(self.cancel_button)

            self.ok_button = QPushButton(first_valid(ok_text=ok_text, CANCEL_TEXT=self.OK_TEXT))
            self.ok_button.clicked.connect(self._ok_btn_clicked)
            btn_layout.addWidget(self.ok_button)

            layout.addLayout(btn_layout)

    def parse(self):
        if self.cancel_flag:
            return self.cancel_value
        inner_value = self.inner.value()
        if not inner_value.is_ok():
            raise ParseError(...) from inner_value.value
        return inner_value.value

    def _inner_changed(self):
        state = self.inner.value().value_state
        self.ok_button.setEnabled(state.is_ok())

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
        self.cancel_flag = True
        self.change_value()
        super().closeEvent(event)


# todo common superclass

@ConfirmValueWidget.template_class
class ConfirmTemplate(Generic[T], ValueWidgetTemplate[T]):
    @property
    def title(self):
        it = self._inner_template()
        if it:
            return it.title
        return super().title

    def _inner_template(self):
        if self.widget_cls.INNER_TEMPLATE:
            return self.widget_cls.INNER_TEMPLATE
        if self.args:
            return self.args[0].template_of()
        return None


def ask(*args, **kwargs) -> \
        Callable[[Union[Type[ValueWidget[T]], ValueWidget[T], ValueWidgetTemplate[T]]], ValueWidgetTemplate[T]]:
    """
    wrap a ValueWidget in a ConfirmValueWidget
    :param args: forwarded to ConfirmValueWidget
    :param kwargs: forwarded to ConfirmValueWidget
    :return: a ConfirmValueWidget template
    """
    kwargs.setdefault('close_on_confirm', True)
    kwargs.setdefault('flags', Qt.Dialog)

    def ret(c: Union[Type[ValueWidget[T]], ValueWidget[T], ValueWidgetTemplate[T]]) -> ValueWidgetTemplate[T]:
        if isinstance(c, type) and issubclass(c, ValueWidget):
            template_of = c.template()
        elif isinstance(c, (ValueWidget, ValueWidgetTemplate)):
            template_of = c.template_of()
        else:
            raise TypeError(f'cannot wrap {c} in ask')

        return ConfirmValueWidget.template(template_of, *args, **kwargs)

    return ret


if __name__ == '__main__':
    from qtalos.widgets import *

    app = QApplication([])

    w = ConverterWidget(
        ConfirmValueWidget(
            IntEdit.template('source ovr', make_title=True, make_indicator=True),
            cancel_value=None
        ),
        converter_func=lambda x: (x * x if isinstance(x, int) else 0)
    )
    w.on_change.connect(lambda: print(w.value()))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
