from typing import Tuple, Match

from fidget.backend.QtWidgets import QLineEdit, QHBoxLayout

from fidget.core import Fidget, regex_parser, json_parser, PlaintextParseError, ParseError, wrap_plaintext_parser

from fidget.tests.gui.__util__ import test_as_main


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


@regex_parser(r'(?P<x>[0-9\.]+)\s*[,\s:\-|]\s*(?P<y>[0-9\.]+)',
              r'\((?P<x>[0-9\.]+)\s*[,\s:\-|]\s*(?P<y>[0-9\.]+)\)',
              r'\[(?P<x>[0-9\.]+)\s*[,\s:\-|]\s*(?P<y>[0-9\.]+)\]',
              r'\{(?P<x>[0-9\.]+)\s*[,\s:\-|]\s*(?P<y>[0-9\.]+)\}')
def tuple_(m: Match[str]):
    x = m['x']
    y = m['y']
    return parse_point(x, y)


tuple_.__name__ = 'tuple'


@json_parser(dict)
@wrap_plaintext_parser(KeyError)
def json_dict(m: dict):
    x = m.get('X') or m['x']
    y = m.get('Y') or m['y']
    return parse_point(x, y)


@test_as_main('sample', help='sample help')
class PointWidget(Fidget[Tuple[float, float]]):
    MAKE_TITLE = MAKE_PLAINTEXT = MAKE_INDICATOR = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.x_edit = None
        self.y_edit = None
        self.init_ui()
        self.change_value()

    def init_ui(self):
        super().init_ui()

        layout = QHBoxLayout()
        with self.setup_provided(layout):
            self.x_edit = QLineEdit()
            self.x_edit.setPlaceholderText('X')
            self.x_edit.textChanged.connect(self.change_value)
            layout.addWidget(self.x_edit)

            self.y_edit = QLineEdit()
            self.y_edit.setPlaceholderText('Y')
            self.y_edit.textChanged.connect(self.change_value)
            layout.addWidget(self.y_edit)
        self.setLayout(layout)

    def parse(self):
        try:
            x = float(self.x_edit.text())
        except ValueError as e:
            raise ParseError('error in x') from e

        try:
            y = float(self.y_edit.text())
        except ValueError as e:
            raise ParseError('error in y') from e

        return x, y

    def plaintext_parsers(self):
        yield from super().plaintext_parsers()
        yield tuple_
        yield json_dict

    def fill(self, t):
        x, y = t
        self.x_edit.setText(str(x))
        self.y_edit.setText(str(y))
