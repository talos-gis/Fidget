from fidget.widgets import FidgetLine, question, template

from fidget.tests.gui.__util__ import test_as_main


@test_as_main()
@question()
@template('sample')
class _(FidgetLine):
    PATTERN = '[^a]*(ab*)?'
