from fidget.widgets import FidgetTable, FidgetInt, FidgetCheckBox

from tests.gui.__util__ import test_as_main


@test_as_main('sample')
class MyTable(FidgetTable):
    MAKE_TITLE = True
    MAKE_PLAINTEXT = True
    MAKE_INDICATOR = True

    INNER_TEMPLATES = [
        FidgetInt.template('X'),
        FidgetCheckBox.template('pos'),
    ]

    ROWS = 1, 1, None
    SCROLLABLE = False
