from fidget.widgets import OptionalValueWidget, ValueCombo, inner_widget

from tests.gui.__util__ import test_as_main


@test_as_main(make_indicator=True, make_title=True, make_plaintext=True)
class OptionalEmployee(OptionalValueWidget):
    @inner_widget('sample', options=['jim', 'bob', 'joe'])
    class Employee(ValueCombo):
        pass
