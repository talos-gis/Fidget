from qtalos.backend import QApplication, QHBoxLayout, QFrame

from qtalos.widgets import ValueCheckBox, ValueCombo, IntEdit, StackedValueWidget

if __name__ == '__main__':

    app = QApplication([])
    w = StackedValueWidget('number', [
        IntEdit('raw text'),
        ValueCheckBox('sign', (0, 1)),
        ValueCombo('named', [('dozen', 12), ('one', 1), ('seven', 7)])
    ], make_plaintext=True, frame_style=QFrame.Box, selector_cls=StackedValueWidget.RadioSelector,
                           layout_cls=QHBoxLayout, make_title=True, make_indicator=True)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)