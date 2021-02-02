from fidget.widgets.user_util import FidgetInt
from fidget.backend import prefer

prefer('PyQt5')

from fidget.backend.QtWidgets import QVBoxLayout
from fidget.widgets import FidgetQuestion, FidgetMatrix, FidgetMinimal, FidgetDict
from fidget.widgets.__util__ import CountBounds

if __name__ == '__main__':
    from fidget.backend.QtWidgets import QApplication

    app = QApplication([])
    q = FidgetQuestion(
        FidgetMatrix(
            FidgetMinimal(
                FidgetDict('sample',
                           [
                               FidgetInt('X'),
                               FidgetInt('Y')
                           ],
                           make_title=True, make_indicator=True, make_plaintext=True),
                make_plaintext=False, make_indicator=False, make_title=False, initial_value=None
            ),
            rows=CountBounds(1, 1, None),
            columns=1,
            make_plaintext=True, make_title=True, make_indicator=False, layout_cls=QVBoxLayout
        ),
        cancel_value=None
    )
    q.show()
    result = q.exec_()
    print(result)
    if result.is_ok() and result.value is not None:
        for d in result.value:
            print(d)
    # app.exec_()
