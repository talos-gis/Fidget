from typing import TypeVar, Generic, Callable, Union

from PyQt5.QtWidgets import QLineEdit, QHBoxLayout

from qtalos import ValueWidget, InnerPlaintextParser, PlaintextPrintError

T = TypeVar('T')


class ConvertedEdit(Generic[T], ValueWidget[T]):
    def __init__(self, title: str, *args, convert_func: Callable[[str], T], **kwargs):
        super().__init__(title, *args, **kwargs)

        self.convert_func = convert_func

        self.edit: QLineEdit = None

        self.init_ui()

    def init_ui(self):
        super().init_ui()
        layout = QHBoxLayout(self)

        with self.setup_provided(layout):
            self.edit = QLineEdit()
            self.edit.textChanged.connect(self.change_value)

            layout.addWidget(self.edit)

    def parse(self):
        return self.convert(self.edit.text())

    @InnerPlaintextParser
    def raw_text(self, v):
        return self.convert(v)

    def fill(self, v: Union[T, str]):
        try:
            text = self.joined_plaintext_printer(v)
        except PlaintextPrintError as e:
            raise Exception('unprintable value') from e
        self.edit.setText(text)

    def convert(self, v: str):
        # we leave this function for potential inheritors
        return self.convert_func(v)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from qtalos import wrap_parser

    app = QApplication([])
    w = ConvertedEdit('sample', convert_func=wrap_parser(ValueError, float))
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
