from qtalos.backend import prefer

from qtalos.backend import QWidget, QStackedWidget, QFileDialog
from qtalos.widgets import StackedValueWidget, FilePathWidget, inner_widget, ConverterWidget, DictWidget, LineEdit


class MakeProjectWidget(StackedValueWidget):
    @inner_widget('open', exist_cond=True)
    class Open(FilePathWidget):
        MAKE_PLAINTEXT = MAKE_TITLE = MAKE_INDICATOR = False

        # DIALOG = QFileDialog(filter='cerial project (*.cer);; all files (*.*)')

    @inner_widget()
    class New(ConverterWidget[dict, str]):
        @inner_widget('new')
        class _(DictWidget):
            @inner_widget('name', pattern='.+')
            class Name(LineEdit):
                pass

        def convert(self, v: dict):
            return v['name']

    SELECTOR_CLS = 'radio'


if __name__ == '__main__':
    print(MakeProjectWidget.show_as_main('sample'))
