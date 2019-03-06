from qtalos.backend import QApplication, QHBoxLayout, QFrame

from qtalos.widgets import LabelValueWidget, IntEdit, StackedValueWidget

if __name__ == '__main__':

    app = QApplication([])
    w = StackedValueWidget('number', [
        IntEdit('raw text'),
        LabelValueWidget('auto', ('auto', 123456))
    ], make_plaintext=True, frame_style=QFrame.Box, selector_cls=StackedValueWidget.CheckBoxSelector,
                           layout_cls=QHBoxLayout)
    w.show()
    res = app.exec_()
    print(w.value())
    exit(res)