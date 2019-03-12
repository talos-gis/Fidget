from fidget.backend import QHBoxLayout

from fidget.widgets import FidgetCombo, inner_fidget, FidgetStacked, FidgetLabel, FidgetInt

from tests.gui.__util__ import test_as_main


@test_as_main('number', make_indicator=True, make_title=True, make_plaintext=True, selector_cls='radio')
class Number(FidgetStacked[float]):
    LAYOUT_CLS = QHBoxLayout

    @inner_fidget('builtin', options=[('one', 1), ('two', 2), ('three', 3)])
    class Named(FidgetCombo):
        pass

    @inner_fidget('pi', 3.14)
    class Pi(FidgetLabel):
        def plaintext_printers(self):
            yield from super().plaintext_printers()

    @inner_fidget('text')
    class Text(FidgetInt):
        pass
