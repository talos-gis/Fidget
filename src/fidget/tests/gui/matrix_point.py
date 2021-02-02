from fidget.widgets import FidgetMatrix, FidgetInt, inner_fidget, FidgetMinimal, FidgetTuple

from tests.gui.__util__ import test_as_main


@test_as_main()
class MyMatrix(FidgetMatrix[int]):
    @inner_fidget()
    class Element(FidgetMinimal):
        MAKE_TITLE = False

        @inner_fidget('sample')
        class _(FidgetTuple):
            MAKE_TITLE = False
            MAKE_PLAINTEXT = True
            INNER_TEMPLATES = [
                FidgetInt.template('X'),
                FidgetInt.template('Y'),
            ]

    MAKE_TITLE = True
    MAKE_INDICATOR = False
    MAKE_PLAINTEXT = True

    ROWS = 2, 1, 5
    COLUMNS = 2, 1, 5
