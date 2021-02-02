from time import sleep

from fidget.core import ValidationError

from fidget.widgets import FidgetInt, FidgetConfirmer, inner_fidget

from fidget.tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(FidgetConfirmer):
    @inner_fidget('sample', help='i am help')
    class _(FidgetInt):
        pass

    def validate(self, value: int):
        if isinstance(value, int):
            sleep(1)
            if value == 0:
                raise ValidationError('value cannot be 0')
