from fidget.core import validator

from fidget.widgets import FidgetInt, FidgetConfirmer, inner_fidget

from tests.gui.__util__ import test_as_main


@validator()
def divisible_by_3(v):
    """
    value must be divisible by 3
    """
    return v % 3 == 0


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(FidgetConfirmer):
    @inner_fidget('sample', validation_func=divisible_by_3)
    class _(FidgetInt):
        MAKE_PLAINTEXT = True
