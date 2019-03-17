from collections import namedtuple

from fidget.backend.QtWidgets import QVBoxLayout

from fidget.widgets import FidgetMatrix, FidgetInt, inner_fidget, FidgetTuple, FidgetConverter

from tests.gui.__util__ import test_as_main

Point = namedtuple('Point', 'x y')


@test_as_main()
class MyMatrix(FidgetMatrix[Point]):
    MAKE_TITLE = True
    MAKE_PLAINTEXT = True
    MAKE_INDICATOR = True

    @inner_fidget()
    class PointConverter(FidgetConverter[tuple, Point]):
        @inner_fidget('point')
        class PointFidget(FidgetTuple):
            MAKE_TITLE = False
            MAKE_PLAINTEXT = False
            MAKE_INDICATOR = False
            INNER_TEMPLATES = [
                FidgetInt.template('X'),
                FidgetInt.template('Y'),
            ]
            LAYOUT_CLS = QVBoxLayout

        def convert(self, v: tuple):
            return Point(x=v[0], y=v[1])

        def back_convert(self, v: Point):
            return v.x, v.y

    ROWS = 1
    COLUMNS = (1, 1, None)
    SCROLLABLE = False
