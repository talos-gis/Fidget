from fidget.backend.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from fidget.widgets import FidgetInt, FidgetQuestion

from tests.gui.__util__ import test_as_main


@test_as_main()
class Factor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        b = 0
        num_dialog = FidgetQuestion(FidgetInt('b', make_plaintext=True), parent=self, cancel_value=None)

        layout = QVBoxLayout()

        line_edit = FidgetInt('a')
        layout.addWidget(line_edit)

        label = QLabel('0')
        layout.addWidget(label)

        browse_btn = QPushButton('...')
        layout.addWidget(browse_btn)

        @browse_btn.clicked.connect
        def _(click_event):
            nonlocal b

            value = num_dialog.exec()
            if value.is_ok() and value.value is not None:
                b = value.value
                label.setText(str(b))

        show_btn = QPushButton('show')
        layout.addWidget(show_btn)

        @show_btn.clicked.connect
        def _(ce):
            a = line_edit.value()
            if not a.is_ok():
                print(a)
                return
            print(a.value*b)

        self.setLayout(layout)
