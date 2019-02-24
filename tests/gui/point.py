from typing import Tuple, Match

from PyQt5.QtWidgets import QLineEdit, QHBoxLayout

from qtalos import ValueWidget, regex_parser, json_parser, PlaintextParseError

point_pat = r'(?P<x>[0-9\.]+)\s*,\s*(?P<y>[0-9\.]+)'


def parse_point(x, y):
    try:
        x = float(x)
    except ValueError as e:
        raise PlaintextParseError('could not parse x') from e

    try:
        y = float(y)
    except ValueError as e:
        raise PlaintextParseError('could not parse y') from e

    return x, y


@regex_parser(point_pat,
              r'\(' + point_pat + r'\)',
              r'\[' + point_pat + r'\]',
              r'\{' + point_pat + r'\}')
def tuple_(m: Match[str]):
    x = m['x']
    y = m['y']
    return parse_point(x, y)


tuple_.__name__ = 'tuple'


@json_parser(dict)
def json_dict(m: dict):
    x = m['X']
    y = m['Y']
    return parse_point(x, y)


class PointWidget(ValueWidget[Tuple[float, float]]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x_edit = None
        self.y_edit = None
        self.init_ui()
        self.change_value()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout(self)

        self.x_edit = QLineEdit()
        self.x_edit.setPlaceholderText('X')
        self.x_edit.textChanged.connect(self.change_value)
        layout.addWidget(self.x_edit)

        self.y_edit = QLineEdit()
        self.y_edit.setPlaceholderText('Y')
        self.y_edit.textChanged.connect(self.change_value)
        layout.addWidget(self.y_edit)

        layout.addWidget(self.validation_label)
        layout.addWidget(self.plaintext_button)

    def parse(self):
        try:
            x = float(self.x_edit.text())
        except ValueError as e:
            raise self.parse_exception('error in x') from e

        try:
            y = float(self.y_edit.text())
        except ValueError as e:
            raise self.parse_exception('error in y') from e

        return x, y

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield tuple_
        yield json_dict

    def fill(self, t):
        x, y = t
        self.x_edit.setText(str(x))
        self.y_edit.setText(str(y))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    w = PointWidget('sample')
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)
