import os
import sys
import maya.utils
import traceback
import unittest
import re
import pymel.versions

import shutil
import string

thisFile = os.path.basename(__file__)

# don't want to bother matching on directories, because they can have
# relative paths, like '../myfile.py'
fileReStr = r'(?:(?:(?P<dir>[^\n]*?)(?P<file>[^\n/\\]*)\.pyc?)|(?P<special_file><maya console>|<string>))'
fileLineRe1 = re.compile(r'file %s line \d+' % fileReStr)
fileLineRe2 = re.compile(r'File "%s", line \d+' % fileReStr)

def replacePath(match):
    groups = match.groupdict()
    file = groups.get('file', '')
    if file:
        dir = groups.get('dir', '')
        if dir:
            dir = '<py_dir>/' 
        path = '%s%s.py' % (dir, file)
    else:
        path = groups['special_file']
    return path
    
def fileLineReplacer1(match):
    return 'file %s line <lineno>' % replacePath(match)

def fileLineReplacer2(match):
    return 'File "%s", line <lineno>' % replacePath(match)


errorCodes = [
( 'shutil.move("this_does_not_exist.txt", "this_either.txt")',
(
"""IOError: [Errno 2] No such file or directory: 'this_does_not_exist.txt'""",
"""IOError: file <py_dir>/shutil.py line <lineno>: [Errno 2] No such file or directory: 'this_does_not_exist.txt'""",
"""[Errno 2] No such file or directory: 'this_does_not_exist.txt'
# Traceback (most recent call last):
#   File "<maya console>", line <lineno>, in <module>
#   File "<string>", line <lineno>, in <module>
#   File "<py_dir>/shutil.py", line <lineno>, in move
#     copy2(src, real_dst)
#   File "<py_dir>/shutil.py", line <lineno>, in copy2
#     copyfile(src, dst)
#   File "<py_dir>/shutil.py", line <lineno>, in copyfile
#     fsrc = open(src, 'rb')
# IOError: [Errno 2] No such file or directory: 'this_does_not_exist.txt'"""
)),

('foo : bar',
(
"""SyntaxError: invalid syntax""",
"""SyntaxError: file <maya console> line <lineno>: invalid syntax""",
"""invalid syntax
# Traceback (most recent call last):
#   File "<maya console>", line <lineno>, in <module>
#   File "<string>", line <lineno>
#     foo : bar
#         ^
# SyntaxError: invalid syntax"""
)),

("string.join(['one', 'two', 3])",
(
"""TypeError: sequence item 2: expected string, int found""",
"""TypeError: file <py_dir>/string.py line <lineno>: sequence item 2: expected string, int found""",
"""sequence item 2: expected string, int found
# Traceback (most recent call last):
#   File "<maya console>", line <lineno>, in <module>
#   File "<string>", line <lineno>, in <module>
#   File "<py_dir>/string.py", line <lineno>, in join
#     return sep.join(words)
# TypeError: sequence item 2: expected string, int found"""
)),
]


class TestMayaIntegration(unittest.TestCase):
    if pymel.versions.current() >= pymel.versions.v2011:
        import pymel.core
        def test_guiExceptionFormatting(self):
            for codeStr, messages in errorCodes:
                try:
                    eval(codeStr)
                except Exception, e:
                    type, value, traceback = sys.exc_info()
                    for level in range(3):
                        res = maya.utils.formatGuiException(type, value, traceback, level)
                        rawres = res
                        res = fileLineRe1.sub(fileLineReplacer1, res)
                        res = fileLineRe2.sub(fileLineReplacer2, res)
                        res = res.replace('test_guiExceptionFormatting', '<module>')
                        res = res.replace('<py_dir>/test_mayaIntegration.py', '<maya console>')
                        res = res.replace('#     eval(codeStr)\n', '')
                        
                        expected = messages[level]
                        if res != expected:
                            print 'level: %d' % level
                            print '*' * 60
                            print "raw res:"
                            print rawres
                            print '*' * 60
    
                            print '*' * 60
                            print "res:"
                            print res
                            print '*' * 60
    
                            print '*' * 60
                            print "expected:"
                            print expected
                            print '*' * 60
                        self.assertEqual( res, expected )
                finally:
                    del traceback
