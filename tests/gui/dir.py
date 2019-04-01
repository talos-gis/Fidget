from fidget.widgets import FidgetDirPath
from tests.gui.__util__ import test_as_main

qfd = {'filter': 'py (*.py);;all (*.*)'}

test_as_main('sample', make_title=True, make_plaintext=True, dialog=qfd) \
    (FidgetDirPath)
