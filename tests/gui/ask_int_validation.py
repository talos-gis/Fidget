from fidget.widgets import FidgetInt, FidgetConfirmer, inner_fidget

from tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(FidgetConfirmer):
    @inner_fidget('sample')
    class _(FidgetInt):
        MAKE_PLAINTEXT = True
