#execfile(r'D:\Projects\Dev\pymel\tests\compare_tests.py')

import sys
import re
import os

# Some utility funcs for printing out the list of tests run - useful for
# ensuring that the same set of tests are run if/when we fully transition to
# pytest

unittest_run_re = re.compile(r'^(?:(?P<normal_testname>(?:test[^ \n]*|runTest)) \((?P<normal_classname>test[^\n]*)\)|Doctest: (?P<doctest_name>[a-zA-Z0-9_\.]+)|(?P<generator_testname>[A-Za-z_][A-Za-z_0-9]+)) \.\.\. ')
def getTestNames_unittest_run(logPath, allLinesMatch=False):
    '''Parse test names from the output log of a "run_tests" (unittest) invocation'''
    names = []
    non_matches = []
    with open(logPath, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        match = unittest_run_re.match(line)
        if not match:
            if allLinesMatch:
                non_matches.append((i, line))
            continue
        if match.group('doctest_name'):
            name = 'doctest.DocTestCase.runTest - {}'.format(match.group('doctest_name'))
        elif match.group('generator_testname'):
            name = 'Generator - {}'.format(match.group('generator_testname'))
        else:
            name = '{}.{}'.format(match.group('normal_classname'), match.group('normal_testname'))
        names.append(name)
    if non_matches:
        for i, line in non_matches:
            print i + 1, line
        raise Exception("found non-matching lines")

    return names

def getTestNames_unittest_edited(logPath):
    return getTestNames_unittest_run(logPath, allLinesMatch=True)

# def getTestNames_unittest_edited(logPath):
#     names = []
#     with open(logPath, 'r') as f:
#         lines = f.readlines()
#     for line in lines:
#         name = line.split(' ... ', 1)[0]
#         if name.startswith('Doctest: '):
#             name = name.replace('Doctest: ', 'doctest.DocTestCase.runTest - ', 1)
#         names.append(name)
#     return names

DOCTEST_FORMAT = 'doctest.DocTestCase.runTest - {}'

unittest_collect_re = re.compile(r'^(?:(?P<normal_testname>[a-zA-Z0-9_\.]+)|doctest\.DocTestCase\.runTest - \<DocTest (?P<doctest_name>[a-zA-Z0-9_\.]+) from [^\n]*\:(?:[0-9]+|None) \([0-9]+ examples?\)\>)$', re.MULTILINE)
def getTestNames_unittest_collect(logPath):
    '''Parse test names from the output log of a "run_tests --collect-only" (unittest) invocation'''
    names = []
    with open(logPath, 'r') as f:
        text = f.read()
    for match in unittest_collect_re.finditer(text):
        if match.group('doctest_name'):
            name = DOCTEST_FORMAT.format(match.group('doctest_name'))
        else:
            name = match.group('normal_testname')
            if '.' not in name:
                continue
        names.append(name)
    return names
    
pytest_collect_re = re.compile(r'''^(?P<spaces>(?:  )*)\<(?P<type>[^ ]+) \'(?P<name>[^']+)\'\>$''', re.MULTILINE)
def getTestNames_pytest_collect(logPath):
    '''Parse test names from the output log of a "py.text --collect-only" (pytest) invocation'''
    names = []
    numNonMatching = 0
    with open(logPath, 'r') as f:
        text = f.read()
    stack = []
    # for match in pytest_collect_re.finditer(text):
    for line in text.splitlines():
        match = pytest_collect_re.match(line)
        if not match:
            numNonMatching += 1
            continue
        spaces = match.group('spaces')
        level = len(spaces) / 2
        objType = match.group('type')
        if objType not in ('Module', 'UnitTestCase', 'TestCaseFunction', 'Function', 'Generator', 'DoctestModule', 'DoctestItem'):
            # just to catch something unexpected
            raise ValueError(objType)
        name = match.group('name')
        if not name:
            raise RuntimeError(line)
        if name.endswith('.py'):
            name = name[:-3]
        name = name.replace('/', '.')

        stack[level:] = [name]

        if objType in ('TestCaseFunction', 'Function', 'DoctestItem'):
            if objType == 'DoctestItem':
                # the name for DoctestItems include the module already
                fullName = DOCTEST_FORMAT.format(name)
            else:
                fullName = ".".join(stack)            
            if fullName.startswith('tests.'):
                fullName = fullName[len('tests.'):]
            names.append(fullName)
    print "numNonMatching:", numNonMatching
    return names

testDir = r'D:\Projects\Dev\pymel\tests'

def getLogPath(logPath):
    if '\\' not in logPath:
        logPath = os.path.join(testDir, logPath)
    return logPath

def verify(names):
    print len(names)
    namesSet = set(names)
    if len(names) != len(namesSet):
        # find dupes
        counts = {}
        for name in names:
            counts[name] = counts.setdefault(name, 0) + 1
        print "found duplicate names:"
        for name in sorted(names):
            count = counts[name]
            if count > 1:
                print "{}: {}".format(name, count)
        raise Exception("found duplicate names")
    return namesSet

def verify_unittest(path):
    print "testing: {}".format(path)
    path = getLogPath(path)
    return verify(getTestNames_unittest_run(path))

def verify_unittest_edited(path):
    print "testing: {}".format(path)
    path = getLogPath(path)
    return verify(getTestNames_unittest_edited(path))

def verify_pytest(path):
    print "testing: {}".format(path)
    path = getLogPath(path)
    return verify(getTestNames_pytest_collect(path))

noseNamesNoDesc = verify_unittest('pymelTestOut_nose_all_noDesc.txt')
noseNamesNewExcludes = verify_unittest('pymelTestOut_nose_all_newExcludes.txt')
noseNamesNoDescEdited = verify_unittest_edited('pymelTestOut_nose_all_noDesc_edited.txt')

for i, pair in enumerate(zip(noseNamesNoDesc, noseNamesNoDescEdited)):
    if pair[0] != pair[1]:
        print i, pair
        break

pytestNames = verify_pytest('output_pytest.log')


pytestOnly = pytestNames - noseNamesNoDesc
noseOnly = noseNamesNoDesc - pytestNames

print "pytestOnly: {}".format(len(pytestOnly))
print "noseOnly: {}".format(len(noseOnly))

