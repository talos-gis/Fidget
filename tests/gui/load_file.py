from fidget.backend import prefer

from fidget.backend import QWidget, QStackedWidget, QFileDialog
from fidget.widgets import FidgetStacked, FidgetFilePath, inner_fidget, FidgetConverter, FidgetDict, FidgetLineEdit


class MakeProjectWidget(FidgetStacked):
    @inner_fidget('open', exist_cond=True)
    class Open(FidgetFilePath):
        MAKE_PLAINTEXT = MAKE_TITLE = MAKE_INDICATOR = False

        # DIALOG = QFileDialog(filter='cerial project (*.cer);; all files (*.*)')

    @inner_fidget()
    class New(FidgetConverter[dict, str]):
        @inner_fidget('new')
        class _(FidgetDict):
            @inner_fidget('name', pattern='.+')
            class Name(FidgetLineEdit):
                pass

        def convert(self, v: dict):
            return v['name']

    SELECTOR_CLS = 'radio'


if __name__ == '__main__':
    print(MakeProjectWidget.show_as_main('sample'))
