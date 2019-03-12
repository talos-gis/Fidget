from fidget.backend.QtWidgets import QApplication, QHBoxLayout, QFrame

from fidget.widgets import FidgetLabel, FidgetInt, FidgetStacked

if __name__ == '__main__':

    app = QApplication([])
    w = FidgetStacked('number', [
        FidgetInt('raw text'),
        FidgetLabel('auto', ('auto', 123456))
    ], make_plaintext=True, frame_style=QFrame.Box, selector_cls=FidgetStacked.CheckBoxSelector,
                      layout_cls=QHBoxLayout, make_indicator=False)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)