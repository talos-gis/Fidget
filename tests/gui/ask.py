from fidget.backend import prefer

#prefer('PyQt5')

from fidget.widgets import *

from tests.gui.__util__ import test_as_main

test_as_main()(FidgetInt.template('sample'))
#@question(cancel_value=None)
#@template('sample')
#class _(FidgetInt):
#    MAKE_PLAINTEXT = True
