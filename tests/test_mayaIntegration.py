import os
import sys
import maya.utils
import traceback
import unittest
import re
import pymel.versions

import shutil
import string

pythonlib = os.path.dirname(os.__file__)

errorCodes = [
( 'shutil.move("this_does_not_exist.txt", "this_either.txt")',
(
"""IOError: [Errno 2] No such file or directory: 'this_does_not_exist.txt'""",
"""IOError: file %(site_packages)s/shutil.py line 52: [Errno 2] No such file or directory: 'this_does_not_exist.txt'""",
"""[Errno 2] No such file or directory: 'this_does_not_exist.txt'
# Traceback (most recent call last):
#   File "<maya console>", line 1, in <module>
#   File "<string>", line 1, in <module>
#   File "%(site_packages)s/shutil.py", line 264, in move
#     copy2(src, real_dst)
#   File "%(site_packages)s/shutil.py", line 99, in copy2
#     copyfile(src, dst)
#   File "%(site_packages)s/shutil.py", line 52, in copyfile
#     fsrc = open(src, 'rb')
# IOError: [Errno 2] No such file or directory: 'this_does_not_exist.txt'"""
)),

('foo : bar',
(
"""SyntaxError: invalid syntax""",
"""SyntaxError: file <maya console> line 1: invalid syntax""",
"""invalid syntax
# Traceback (most recent call last):
#   File "<maya console>", line 1, in <module>
#   File "<string>", line 1
#     foo : bar
#         ^
# SyntaxError: invalid syntax"""
)),

("string.join(['one', 'two', 3])",
(
"""TypeError: sequence item 2: expected string, int found""",
"""TypeError: file %(site_packages)s/string.py line 318: sequence item 2: expected string, int found""",
"""sequence item 2: expected string, int found
# Traceback (most recent call last):
#   File "<maya console>", line 1, in <module>
#   File "<string>", line 1, in <module>
#   File "%(site_packages)s/string.py", line 318, in join
#     return sep.join(words)
# TypeError: sequence item 2: expected string, int found"""
)),
]


class TestMayaIntegration(unittest.TestCase):
    if pymel.versions.current() >= pymel.versions.v2011:
        def test_guiExceptionFormatting(self):
            for codeStr, messages in errorCodes:
                try:
                    eval(codeStr)
                except Exception, e:
                    type, value, traceback = sys.exc_info()
                    for level in range(3):
                        res = maya.utils.formatGuiException(type, value, traceback, level)
                        # remove context of this function
                        #print repr('#   File "%s", line \d+, in test_guiExceptionFormatting\n#     eval(codeStr)\n' % __file__)
                        #print 
                        #print repr(res)
                        #res = re.sub( '([fF]ile "?)%s("?,?) line \d+(, in test_guiExceptionFormatting)?' % __file__, r'\1<maya console>\2 line 1, in <module>', res)
                        res = re.sub( 'file %s line \d+' % __file__, r'file <maya console> line 1', res)
                        res = re.sub( 'File "%s", line \d+, in test_guiExceptionFormatting' % __file__, r'File "<maya console>", line 1, in <module>', res)
                        res = res.replace('#     eval(codeStr)\n', '')
                        self.assertEqual( res, messages[level] % {'site_packages':pythonlib} )
                finally:
                    del traceback
