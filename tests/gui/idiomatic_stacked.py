from fidget.backend import QHBoxLayout

from fidget.widgets import ValueCombo, inner_widget, StackedValueWidget, LabelValueWidget, IntEdit

from tests.gui.__util__ import test_as_main


@test_as_main('number', make_indicator=True, make_title=True, make_plaintext=True, selector_cls='radio')
class Number(StackedValueWidget[float]):
    LAYOUT_CLS = QHBoxLayout

    @inner_widget('builtin', options=[('one', 1), ('two', 2), ('three', 3)])
    class Named(ValueCombo):
        pass

    @inner_widget('pi', 3.14)
    class Pi(LabelValueWidget):
        def plaintext_printers(self):
            yield from super().plaintext_printers()

    @inner_widget('text')
    class Text(IntEdit):
        pass
