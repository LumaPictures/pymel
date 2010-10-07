import sys
import unittest
import maya.cmds as cmds
import pymel.core as pm
import pymel.core.uitypes as ui
import pymel.core.windows as windows

class TestMenu(unittest.TestCase):
    def setUp(self):
        cmds.setParent(None, menu=1)
        self.win = cmds.window()
    def tearDown(self):
        cmds.deleteUI(self.win, window=True)
        
    def testOptionMenuAsMenu(self):
        cmds.formLayout()
        om = ui.OptionMenu('someOptionMenu', create=True)
        cmds.menuItem( label='Yellow' )
        self.assertEqual(windows.menu(om, q=1, numberOfItems=1), 1)
        self.assertEqual(windows.menu(om.name(), q=1, numberOfItems=1), 1)
        self.assertEqual(windows.menu(om.shortName(), q=1, numberOfItems=1), 1)
        ui.Menu(om)
        ui.Menu(om.name())
        ui.Menu(om.shortName())        
        
if not pm.about(batch=1):
    for key, obj in globals().items():
        if isinstance(obj, unittest.TestCase):
            del globals()[key]
            obj.__name__ = '_canceledTest_' + obj.__name__
