from fidget.backend.QtWidgets import QHBoxLayout

from fidget.widgets import FidgetMinimal, FidgetInt, FidgetTuple, inner_fidget, SimplePlainEdit
from fidget.tests.gui.__util__ import test_as_main


@test_as_main()
class MinInt(FidgetMinimal):
    MAKE_TITLE = True
    OUTER_TEMPLATE = SimplePlainEdit.template('outer')

    @inner_fidget('sample')
    class _(FidgetTuple):
        MAKE_TITLE = False
        LAYOUT_CLS = QHBoxLayout
        MAKE_PLAINTEXT = True
        INNER_TEMPLATES = [
            FidgetInt.template('X'),
            FidgetInt.template('Y'),
        ]
