from fidget.widgets import FidgetOptional, FidgetCombo, inner_fidget

from fidget.tests.gui.__util__ import test_as_main


@test_as_main(make_indicator=True, make_title=True, make_plaintext=True)
class OptionalEmployee(FidgetOptional):
    @inner_fidget('sample', options=['jim', 'bob', 'joe'])
    class Employee(FidgetCombo):
        pass
