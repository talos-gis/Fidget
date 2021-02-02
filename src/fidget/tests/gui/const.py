from fidget.widgets import FidgetConst, question, template

from tests.gui.__util__ import test_as_main


@test_as_main()
@question()
@template('sample')
class _(FidgetConst[int]):
    OPTION = ('twenty', 20)
