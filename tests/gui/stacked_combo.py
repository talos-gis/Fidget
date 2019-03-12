from fidget.backend import QApplication, QFrame

from fidget.widgets import FidgetCheckBox, FidgetCombo, FidgetInt, FidgetStacked

if __name__ == '__main__':

    app = QApplication([])
    w = FidgetStacked('number', [
        FidgetInt('raw text'),
        FidgetCheckBox('sign', (0, 1)),
        FidgetCombo('named', [('dozen', 12), ('one', 1), ('seven', 7)])
    ], make_plaintext=True, frame_style=QFrame.Box)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)