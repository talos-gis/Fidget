from time import sleep

from qtalos.core import ValidationError

from qtalos.widgets import IntEdit, ConfirmValueWidget, inner_widget

from tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(ConfirmValueWidget):
    @inner_widget('sample')
    class _(IntEdit):
        pass

    def validate(self, value: int):
        if isinstance(value, int):
            sleep(1)
            if value == 0:
                raise ValidationError('value cannot be 0')