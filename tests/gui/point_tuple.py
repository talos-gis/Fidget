from fidget.backend.QtWidgets import QHBoxLayout
from fidget.widgets import FidgetInt, FidgetTuple

from tests.gui.__util__ import test_as_main


@test_as_main('sample')
class PointWidget(FidgetTuple):
    INNER_TEMPLATES = [
        FidgetInt.template('x', make_title=False),
        FidgetInt.template('y', make_title=False)
    ]
    MAKE_PLAINTEXT = True
    MAKE_TITLE = True
    MAKE_INDICATOR = True
    LAYOUT_CLS = QHBoxLayout
