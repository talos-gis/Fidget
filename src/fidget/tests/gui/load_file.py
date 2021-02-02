from fidget.widgets import FidgetStacked, FidgetFilePath, inner_fidget, FidgetConverter, FidgetDict, FidgetLine

from fidget.tests.gui.__util__ import test_as_main


@test_as_main('sample')
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
            class Name(FidgetLine):
                pass

        def convert(self, v: dict):
            return v['name']

    SELECTOR_CLS = 'radio'
