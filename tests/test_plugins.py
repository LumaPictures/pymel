import inspect
import os
import unittest

import pymel.core as pm

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)

pluginName = 'dynamicNodes.py'
pluginPath = os.path.join(THIS_DIR, 'plugins', pluginName)

class TestDynamicNodeCreation(unittest.TestCase):
    def test_lateNodeCreation(self):
        # makes sure that we can still access a node from pymel.core.nodetypes,
        # even if it's created outside of a plugin initialization
        #
        # This isn't just a hypothetical / academic possibility = ie, mtoa
        # creates nodes outside of it's initialize, due to it's plugin system
        allNodes = set(pm.allNodeTypes())
        self.assertNotIn('initialNode', allNodes)
        self.assertNotIn('myLateCreatedNode', allNodes)
        self.assertFalse(hasattr(pm.nt, 'InitialNode'))
        self.assertFalse(hasattr(pm.nt, 'MyLateCreatedNode'))
        pm.loadPlugin(pluginPath)
        try:
            # first, check that the "initialNode" was created
            allNodes = set(pm.allNodeTypes())
            self.assertIn('initialNode', allNodes)
            self.assertNotIn('myLateCreatedNode', allNodes)
            self.assertTrue(hasattr(pm.nt, 'InitialNode'))
            self.assertFalse(hasattr(pm.nt, 'MyLateCreatedNode'))
            myInitialNode = pm.nt.InitialNode()
            myInitialNode.attr('aFloat').set(5)
            self.assertEqual(pm.getAttr('{}.aFloat'.format(myInitialNode)), 5)
            pm.addDynamicNode('myLateCreatedNode')
            allNodes = set(pm.allNodeTypes())
            self.assertIn('initialNode', allNodes)
            self.assertIn('myLateCreatedNode', allNodes)
            self.assertTrue(hasattr(pm.nt, 'InitialNode'))
            self.assertTrue(hasattr(pm.nt, 'MyLateCreatedNode'))
            myLateNode = pm.nt.MyLateCreatedNode()
            myLateNode.attr('aFloat').set(8)
            self.assertEqual(pm.getAttr('{}.aFloat'.format(myLateNode)), 8)
        finally:
            pm.newFile(f=1)
            pm.unloadPlugin(pluginName)

        allNodes = set(pm.allNodeTypes())
        self.assertNotIn('initialNode', allNodes)
        self.assertNotIn('myLateCreatedNode', allNodes)
        self.assertFalse(hasattr(pm.nt, 'InitialNode'))
        self.assertFalse(hasattr(pm.nt, 'MyLateCreatedNode'))