from fidget.backend import QApplication, QFrame

from fidget.widgets import ValueCheckBox, ValueCombo, IntEdit, StackedValueWidget

if __name__ == '__main__':

    app = QApplication([])
    w = StackedValueWidget('number', [
        IntEdit('raw text'),
        ValueCheckBox('sign', (0, 1)),
        ValueCombo('named', [('dozen', 12), ('one', 1), ('seven', 7)])
    ], make_plaintext=True, frame_style=QFrame.Box)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)