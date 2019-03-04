from typing import Callable, TypeVar

from qtalos import wrap_parser

from qtalos.widgets.line import LineEdit
from qtalos.widgets.converter import ConverterWidget

T = TypeVar('T')


def simple_edit(converter_func: Callable[[str], T], name=...):
    class Ret(ConverterWidget[str, T]):
        def __init__(self, title, **kwargs):
            line_edit_args = {'make_validator_label': True}

            for k in ('make_title_label', 'make_plaintext_button', 'make_auto_button', 'make_validator_label',
                      'pattern', 'convert', 'back_convert', 'placeholder'):
                if k in kwargs:
                    line_edit_args[k] = kwargs[k]
                    del kwargs[k]

            super().__init__(LineEdit(title, **line_edit_args), **kwargs)

        def convert(self, v: str):
            return converter_func(v)

        def back_convert(self, v: T):
            return str(v)

    if name is ...:
        name = f'{converter_func.__name__.capitalize()}Edit'

    Ret.__name__ = name
    Ret.__qualname__ = simple_edit.__qualname__[:-len(simple_edit.__name__)]+name

    return Ret


IntEdit = simple_edit(wrap_parser(ValueError, int))
FloatEdit = simple_edit(wrap_parser(ValueError, float))
ComplexEdit = simple_edit(wrap_parser(ValueError, complex))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = ComplexEdit('sample', make_plaintext_button=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
