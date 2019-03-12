from fidget.widgets import question, FidgetFloat, template

from tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
@question(cancel_value=None)
@template('sample')
class _(FidgetFloat):
    MAKE_PLAINTEXT = True
