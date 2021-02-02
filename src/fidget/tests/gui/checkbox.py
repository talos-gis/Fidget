from fidget.widgets import FidgetCheckBox, question, template

from tests.gui.__util__ import test_as_main


@test_as_main()
@question()
@template('sample')
class _(FidgetCheckBox[int]):
    OPTIONS = (10, 20)
