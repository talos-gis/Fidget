from fidget.widgets import FidgetEditCombo, question, template

from tests.gui.__util__ import test_as_main


@test_as_main()
@question()
@template('sample')
class _(FidgetEditCombo):
    MAKE_TITLE = True
    MAKE_INDICATOR = MAKE_PLAINTEXT = False
    MAKE_PLAINTEXT=True

    PATTERN = '[^a]*(ab*)?'
    OPTIONS = [
        ('auto', ...),
        ('twelve', 12),
        'hello world'
    ]
