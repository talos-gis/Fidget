from qtalos.widgets import IntEdit, ConfirmValueWidget, inner_widget

from tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
class AskInt(ConfirmValueWidget):
    @inner_widget('sample')
    class _(IntEdit):
        MAKE_PLAINTEXT = True
