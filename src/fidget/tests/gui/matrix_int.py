from fidget.widgets import FidgetMatrix, FidgetInt, inner_fidget

from tests.gui.__util__ import test_as_main


@test_as_main()
class MyMatrix(FidgetMatrix[int]):
    @inner_fidget('sample')
    class Element(FidgetInt):
        pass
    MAKE_TITLE = True
    MAKE_PLAINTEXT = True
    MAKE_INDICATOR = True

    ROWS = (1, 1, None)
    COLUMNS = (2, 1, None)
