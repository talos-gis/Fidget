from fidget.widgets import FidgetFloat, FidgetOptional, FidgetDict

from tests.gui.__util__ import test_as_main


@test_as_main('sample')
class PointWidget(FidgetDict):
    MAKE_PLAINTEXT = True
    MAKE_TITLE = True
    MAKE_INDICATOR = True
    SCROLLABLE = False

    INNER_TEMPLATES = [
        FidgetFloat.template('X'),
        FidgetFloat.template('Y'),
        FidgetOptional.template(
            FidgetFloat.template('Z', make_indicator=False, make_title=False)),
    ]
