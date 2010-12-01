from __future__ import with_statement

import sys
import unittest
import maya.cmds as cmds
import pymel.core as pm
import pymel.core.uitypes as ui

if not hasattr(pm, 'currentMenuParent'):
    def currentMenuParent():
        return ui.PyUI(cmds.setParent(q=1, menu=1))
    pm.currentMenuParent = currentMenuParent


class TestWithStatement(unittest.TestCase):
    def setUp(self):
        cmds.setParent(None, menu=1)
        self.win = cmds.window()
    def tearDown(self):
        cmds.deleteUI(self.win, window=True)
        
    def test_classInit(self):
        with ui.FormLayout() as fl:
            self.assertEqual(pm.currentParent(), fl)
        self.assertEqual(pm.currentParent(), self.win)
        with ui.RowLayout() as rl:
            self.assertEqual(pm.currentParent(), rl)
        # Since there can only be one top-level layout,
        # what happens is that before creating the row layout, the
        # parent is set to the window; but that automatically gets translated
        # to mean the top-level layout for that window, which is the form
        # layout... so the row layout has it's parent set to the form
        # layout
        self.assertEqual(pm.currentParent(), fl)
        with ui.ColumnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), fl)

    def test_cmdInit(self):
        with pm.formLayout() as fl:
            self.assertEqual(pm.currentParent(), fl)
        self.assertEqual(pm.currentParent(), self.win)
        with pm.rowLayout() as rl:
            self.assertEqual(pm.currentParent(), rl)
        # Since there can only be one top-level layout,
        # what happens is that before creating the row layout, the
        # parent is set to the window; but that automatically gets translated
        # to mean the top-level layout for that window, which is the form
        # layout... so the row layout has it's parent set to the form
        # layout
        self.assertEqual(pm.currentParent(), fl)
        with pm.columnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), fl)

    def test_parentJump(self):
        cl = ui.ColumnLayout()
        rl1 = ui.RowLayout()
        with pm.rowLayout(parent=cl) as rl2:
            self.assertEqual(pm.currentParent(), rl2)
        self.assertEqual(pm.currentParent(), cl)

    def test_nested(self):
        with ui.ColumnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
            with pm.rowLayout() as rl:
                self.assertEqual(pm.currentParent(), rl)
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), self.win)

    def test_nestedParentJump(self):
        with ui.ColumnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
            with pm.rowLayout() as rl:
                self.assertEqual(pm.currentParent(), rl)
                with cl:
                    # set the parent BACK to the column layout
                    self.assertEqual(pm.currentParent(), cl)
                self.assertEqual(pm.currentParent(), rl)
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), self.win)

    def test_nestedMenu(self):
        self.assertEqual(pm.currentParent(), self.win)
        self.assertEqual(pm.currentMenuParent(), None)
        with ui.ColumnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
            self.assertEqual(pm.currentMenuParent(), None)
            cmds.button()
            with pm.popupMenu() as m:
                self.assertEqual(pm.currentParent(), cl)
                self.assertEqual(pm.currentMenuParent(), m)
                with ui.MenuItem(subMenu=1) as sm:
                    self.assertEqual(pm.currentParent(), cl)
                    self.assertEqual(pm.currentMenuParent(), sm)
                self.assertEqual(pm.currentParent(), cl)
                self.assertEqual(pm.currentMenuParent(), m)
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), self.win)
        
    def test_rowGroupLayout(self):
        self.assertEqual(pm.currentParent(), self.win)
        self.assertEqual(pm.currentMenuParent(), None)
        with pm.textFieldButtonGrp( label='Label', text='Text', buttonLabel='Button' ) as tfbg:
            self.assertEqual(pm.currentParent(), tfbg)
            self.assertEqual(pm.currentMenuParent(), None)
            cmds.button()
            with pm.popupMenu() as m:
                self.assertEqual(pm.currentParent(), tfbg)
                self.assertEqual(pm.currentMenuParent(), m)
                with pm.menuItem(subMenu=1) as sm:
                    self.assertEqual(pm.currentParent(), tfbg)
                    self.assertEqual(pm.currentMenuParent(), sm)
                self.assertEqual(pm.currentParent(), tfbg)
                self.assertEqual(pm.currentMenuParent(), m)
            self.assertEqual(pm.currentParent(), tfbg)
        self.assertEqual(pm.currentParent(), self.win)

        fl = pm.formLayout()
        tfbg2 = pm.textFieldButtonGrp( label='Label', text='Text', buttonLabel='Button' )
        self.assertEqual(pm.currentParent(), fl)
        with pm.columnLayout() as cl:
            cmds.button()
            with pm.popupMenu() as m:
                self.assertEqual(pm.currentParent(), cl)
                self.assertEqual(pm.currentMenuParent(), m)
                with pm.menuItem(subMenu=1) as sm:
                    self.assertEqual(pm.currentParent(), cl)
                    self.assertEqual(pm.currentMenuParent(), sm)
                self.assertEqual(pm.currentParent(), cl)
                self.assertEqual(pm.currentMenuParent(), m)
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), fl)
        
    def test_optionMenuGrp(self):
        self.assertEqual(pm.currentParent(), self.win)
        self.assertEqual(pm.currentMenuParent(), None)
        with ui.ColumnLayout() as cl:
            self.assertEqual(pm.currentParent(), cl)
            self.assertEqual(pm.currentMenuParent(), None)
            cmds.button()
            with ui.OptionMenuGrp() as m:
                self.assertEqual(pm.currentParent(), m)
                self.assertEqual(pm.currentMenuParent(), m.menu())
            self.assertEqual(pm.currentParent(), cl)
        self.assertEqual(pm.currentParent(), self.win)
        
    def test_windowExit(self):
        self.assertEqual(pm.currentParent(), self.win)
        newWin = ui.Window()
        try: 
            with newWin:
                self.assertEqual(pm.currentParent(), newWin)
                with pm.formLayout() as fl:
                    self.assertEqual(pm.currentParent(), fl)
                self.assertEqual(pm.currentParent(), newWin)
            self.assertTrue(pm.currentParent() in (None, newWin, fl))
        finally:
            pm.deleteUI(newWin, window=True)
            
        otherWin = ui.Window()
        # try NOT using with statement, to make sure the last newWin
        # statement's exit popped it off the stack correctly
        try:
            with pm.formLayout() as fl:
                self.assertEqual(pm.currentParent(), fl)
            self.assertEqual(pm.currentParent(), otherWin)
        finally:
            pm.deleteUI(otherWin, window=True)

class TestTextScrollList(unittest.TestCase):
    def setUp(self):
        cmds.setParent(None, menu=1)
        self.win = cmds.window()
    def tearDown(self):
        cmds.deleteUI(self.win, window=True)

    def test_selectItemEmptyList(self):
        with ui.Window(self.win):
            with pm.formLayout():
                tsl = pm.textScrollList()
                tsl.extend(['a','b','c'])
        # Make sure this is NOT None
        self.assertEqual(tsl.getSelectItem(), [])
    
        
if not pm.about(batch=1):
    for key, obj in globals().items():
        if isinstance(obj, unittest.TestCase):
            del globals()[key]
            obj.__name__ = '_canceledTest_' + obj.__name__
