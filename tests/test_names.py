#import testingutils
import unittest
import pymel.core.other, pymel.core.system

class testCase_attribNameParsing(unittest.TestCase):
    def test_attribNameParents(self):
        parser = pymel.core.other.AttributeName("Cube1.multiComp[3].child.otherchild")
        self.assertEqual(parser.getParent(), "Cube1.multiComp[3].child")

        self.assertEqual(parser.getParent(0), parser)
        self.assertEqual(parser.getParent(generations=1), "Cube1.multiComp[3].child")
        self.assertEqual(parser.getParent(2), "Cube1.multiComp[3]")
        self.assertEqual(parser.getParent(generations=3), None)
        self.assertEqual(parser.getParent(-1), "Cube1.multiComp[3]")
        self.assertEqual(parser.getParent(generations=-2), "Cube1.multiComp[3].child")
        self.assertEqual(parser.getParent(-3), parser)
        self.assertEqual(parser.getParent(generations=-4), None)
        self.assertEqual(parser.getParent(-63), None)
        self.assertEqual(parser.getParent(generations=32), None)

class testCase_DagNameParsing(unittest.TestCase):
    def test_attribNameParents(self):
        parser = pymel.core.other.DagNodeName("NS1:TopLevel|Next|ns2:Third|Fourth")
        self.assertEqual(parser.getParent(), "NS1:TopLevel|Next|ns2:Third")

        self.assertEqual(parser.getParent(0), parser)
        self.assertEqual(parser.getParent(generations=1), "NS1:TopLevel|Next|ns2:Third")
        self.assertEqual(parser.getParent(2), "NS1:TopLevel|Next")
        self.assertEqual(parser.getParent(generations=3), "NS1:TopLevel")
        self.assertEqual(parser.getParent(generations=4), None)
        self.assertEqual(parser.getParent(-1), "NS1:TopLevel")
        self.assertEqual(parser.getParent(generations=-2), "NS1:TopLevel|Next")
        self.assertEqual(parser.getParent(-3), "NS1:TopLevel|Next|ns2:Third")
        self.assertEqual(parser.getParent(generations=-4), parser)
        self.assertEqual(parser.getParent(generations=-5), None)
        self.assertEqual(parser.getParent(-63), None)
        self.assertEqual(parser.getParent(generations=32), None)


#testingutils.setupUnittestModule(__name__)