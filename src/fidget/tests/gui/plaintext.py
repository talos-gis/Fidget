from fidget.widgets import FidgetPlainText, question, template

from tests.gui.__util__ import test_as_main


@test_as_main()
@question()
@template('sample')
class _(FidgetPlainText):
    PATTERN = '[^a]*(ab*)?'
