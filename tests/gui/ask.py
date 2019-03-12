from fidget.widgets import ask, FloatEdit, template

from tests.gui.__util__ import test_as_main


@test_as_main(close_on_confirm=True, cancel_value=None)
@ask(cancel_value=None)
@template('sample')
class _(FloatEdit):
    MAKE_PLAINTEXT = True
