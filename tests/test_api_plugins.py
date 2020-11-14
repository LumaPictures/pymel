from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# this is segregated into it's own, separate test file from test_api both
# because I'd like to start standardzing on one test-file per python module,
# and because this test requires maya.standalone to be initialized

import os
import re
import unittest
import pymel.api.plugins

class Test_plugins(unittest.TestCase):
    def test_mayaPlugins(self):
        # this test needs to initialize maya, to ensure MAYA_PLUG_IN_PATH
        # is set correctly
        import pymel.core

        knownPlugins = ['mayaHIK', 'objExport', 'tiffFloatReader']

        # to deal with os-differences, strip any extensions
        def mayaPlugins(*args, **kwargs):
            mayaPlugins = pymel.api.plugins.mayaPlugins(*args, **kwargs)
            return [os.path.splitext(x)[0] for x in mayaPlugins]

        allPlugs = mayaPlugins()
        for plug in knownPlugins:
            self.assertIn(plug, allPlugs)

        unknownPlugs = set(allPlugs) - set(knownPlugins)

        filtered1 = mayaPlugins(filters=knownPlugins)
        self.assertEqual(set(filtered1), unknownPlugs)

        regexs = [re.compile(r'^{}.*$'.format(x)) for x in knownPlugins]
        filtered2 = mayaPlugins(filters=regexs)
        self.assertEqual(filtered2, filtered1)

        funcs = []
        for known in knownPlugins:
            # use kwarg to "freeze" the value of known in the function
            def filterFunc(testPlug, knownPlug=known):
                return os.path.splitext(testPlug)[0] == knownPlug
            funcs.append(filterFunc)
        filtered3 = mayaPlugins(filters=funcs)
        self.assertEqual(filtered3, filtered1)
