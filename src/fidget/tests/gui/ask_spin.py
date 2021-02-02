from fidget.widgets import FidgetDiscreteSpin, FidgetConfirmer, inner_fidget

from fidget.tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(FidgetConfirmer):
    @inner_fidget('sample')
    class _(FidgetDiscreteSpin):
        MAKE_PLAINTEXT = True
        OPTIONS = ('one', 1), ('two', 2), ('three', 3)
