import unittest
import pymel.api.allapi as api

class Test_toApiObject(unittest.TestCase):
    def test_multipleObjects(self):
        self.assertTrue(api.toApiObject('*') is None)