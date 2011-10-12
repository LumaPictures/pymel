import unittest

import pymel.core.language as lang

class testCase_pythonToMelCmd(unittest.TestCase):
    def test_bool_arg(self):
        self.assertEqual(lang.pythonToMelCmd('xform', rao=1).strip(),
                         'xform -rao')

    def test_multi_arg(self):
        self.assertEqual(lang.pythonToMelCmd('xform', translation=(1,2,3)).strip(),
                         'xform -translation 1 2 3')
