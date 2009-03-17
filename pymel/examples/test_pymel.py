import unittest
import test_dagTools

suite_dagTools = test_dagTools.suite()
#suite_anotherExample = test_anotherExample.suite()

suite = unittest.TestSuite()

suite.addTest(suite_dagTools)        
#suite.addTest(suite_anotherExample)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
