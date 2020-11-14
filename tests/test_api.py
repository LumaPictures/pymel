from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest
import pymel.api.allapi as api

class Test_toApiObject(unittest.TestCase):
    def test_multipleObjects(self):
        self.assertTrue(api.toApiObject('*') is None)