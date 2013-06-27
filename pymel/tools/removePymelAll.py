#!/usr/bin/env python
'''This script may be used to "fix" python code that uses
"from pymel.all import *" so that it uses the approved "import pymel.core as pm"

Can be called on a single file, or on a directory to recurse through, looking
for .py files.
'''


import argparse
import os
import sys
import inspect
import re
import shutil
import subprocess
import types
import itertools
import ast
import __builtin__

THIS_FILE = os.path.abspath(inspect.getsourcefile(lambda:None))
THIS_DIR = os.path.dirname(THIS_FILE)

_READMODE = 'r'
if hasattr(file, 'newlines'):
    _READMODE = 'U'

def getStubPymelCore():
    if 'PYMEL_STUBS' in os.environ:
        stubPath = os.environ['PYMEL_STUBS']
    else:
        # this file should be in:
        #       pymel/tools/removePymelAll.py
        # while stubs usually at:
        #       extras/completion/py
        stubPath = os.path.join(os.dirname(os.dirname(THIS_DIR)), 'extras',
                                'completion', 'py')
    # make sure you've got the stubs loaded!
    #print stubPath
    sys.path.insert(0, stubPath)
    try:
        oldModules = {}
        for moduleName, mod in sys.modules.items():
            if (moduleName == 'pymel' or moduleName.startswith('pymel.')
                    or moduleName == 'maya' or moduleName.startswith('maya.')):
                oldModules[moduleName] = mod
                del sys.modules[moduleName]
        try:
            import pymel.core as pm
            return pm
        finally:
            for moduleName, mod in sys.modules.items():
                if (moduleName == 'pymel' or moduleName.startswith('pymel.')
                        or moduleName == 'maya' or moduleName.startswith('maya.')):
                    del sys.modules[moduleName]

            for moduleName, mod in oldModules.iteritems():
                sys.modules[moduleName] = mod
    finally:
        del sys.path[0]

def getModuleNames(module):
    names = set()
    for name, obj in inspect.getmembers(module):
        if name.startswith('_') or hasattr(__builtin__, name):
            #print "skipping: %s" % name
            continue
        names.add(name)
    return names

class Namespace(object):
    '''Represents a pymel namespace

    A global namespace is simply one with no parent
    '''
    def __init__(self, parent):
        self.parent = parent
        self.names = set()
        self._cachedAll = None

    def parents(self):
        if self.parent is None:
            return []
        else:
            return self.parent.parents() + [self.parent]

    def globals(self, name):


        if self.parent is None:
            return self
        else:
            return self.parents()[0]

    def add(self, name):
        self.names.add(name)

    def all(self):
        names = frozenset(self.names)
        if self.parent is None:
            return names
        else:
            return self.parent.all() | names


class PymelAllRemoveVisitor(ast.NodeVisitor):
    PYMEL_MODULE_NAMES = ('pm', 'pm.nt', 'pm.ui', 'pm.dt')

    def __init__(self):
        self.pymelAllNames = []
        self.globals = Namespace(None)
        self.currentNamespace = self.globals
        self.pymelNames = self.getPymelModuleNames()

    def getPymelModuleNames(self):
        pm = getStubPymelCore()
        pymelModules = {}
        for modName in self.PYMEL_MODULE_NAMES:
            split = modName.split('.', 1)
            if len(split) > 1:
                subName = split[1]
            else:
                subName = None
            if subName:
                mod = getattr(pm, subName)
            else:
                mod = pm
            pymelModules[modName] = mod

        pymelNames = {}
        for modName, module in pymelModules.iteritems():
            pymelNames[modName] = getModuleNames(module)

        return pymelNames

    def visit(self, node):
        # There are three classes of "special" nodes we care about:
        #    nodes which define a new namespace
        #    nodes which can define a new name in the current namespace
        #    "name" nodes (which we may need to replace)

        newNamespace = None
        # new namespace nodes
        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            if isinstance(node, ast.FunctionDef):
                # if it's a function def, we need to add it's name to the OLD
                # namespace...
                self.addNames(node.name)
            newNamespace = Namespace(self.currentNamespace)
            self.currentNamespace = newNamespace

        try:
            # new name statement nodes
            if isinstance(node, (ast.Assign,
                                 ast.ClassDef,
                                 ast.FunctionDef,
                                 ast.Import,
                                 ast.ImportFrom,
                                 ast.For,
                                 ast.With,
                                 ast.TryExcept,
                                )):
                self.addNames(node)

            elif isinstance(node, ast.Name):
                if not isinstance(node.ctx, (ast.Store, ast.AugStore,
                                             ast.Param)):
                    name = node.id
                    if name not in self.currentNamespace.all():
                        for module in self.PYMEL_MODULE_NAMES:
                            names = self.pymelNames[module]
                            if name in names:
                                # We found a name that was unrecognized, but WAS in
                                # one of the pymel modules... assume it's from pymel.all
                                self.addPymelAllName(node, module)
                                break

            # recurse into child nodes...
            self.generic_visit(node)
        finally:
            if newNamespace:
                self.currentNamespace = newNamespace.parent

    def addNames(self, obj):
        #print "addNames: %r" % obj
        # string... add it!
        if isinstance(obj, basestring):
            self.currentNamespace.add(obj)

        # A name node... add if the context is right
        elif isinstance(obj, ast.Name):
            if isinstance(obj.ctx, (ast.Store, ast.AugStore, ast.Param)):
                self.addNames(obj.id)

        # An alias... check for 'foo as bar'
        elif isinstance(obj, ast.alias):
            if obj.asname:
                name = obj.asname
            else:
                name = obj.name
            if name != '*':
                self.addNames(name)

        # list/tuple.. iterate...
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self.addNames(item)
        elif isinstance(obj, (ast.Tuple, ast.List)):
            self.addNames(obj.elts)

        # Statements (or subparts)...
        elif isinstance(obj, ast.Assign):
            self.addNames(obj.targets)
        elif isinstance(obj, ast.ClassDef):
            self.addNames(obj.name)
        elif isinstance(obj, ast.FunctionDef):
            # We should have already added the function's name to the OLD
            # namespace... if we're passing in the function def, assume we're
            # INSIDE the function's namespace, and only add in it's args...
            #self.addNames(obj.name)
            self.addNames(obj.args)
        elif isinstance(obj, ast.Import):
            self.addNames(obj.names)
        elif isinstance(obj, ast.ImportFrom):
            self.addNames(obj.names)
        elif isinstance(obj, ast.For):
            self.addNames(obj.target)
        elif isinstance(obj, ast.With):
            self.addNames(obj.optional_vars)
        elif isinstance(obj, ast.TryExcept):
            self.addNames(obj.handlers)
        elif isinstance(obj, ast.ExceptHandler):
            self.addNames(obj.name)
        elif isinstance(obj, ast.arguments):
            self.addNames(obj.args)
            self.addNames(obj.vararg)
            self.addNames(obj.kwarg)

    def addPymelAllName(self, nameNode, pymelModule):
        if not isinstance(nameNode, ast.Name):
            raise TypeError
        self.pymelAllNames.append((nameNode, pymelModule))

class PymelAllRemover(object):
    # oops - pm.nt.mm is a module, pm.mel is a pymel.core.language.Mel object!
    #REPLACEMENTS = {'pm.nt.mm':'pm.mel'}
    REPLACEMENTS = {}

    def __init__(self, filepath, text=None):
        self.filepath = filepath
        if text is None:
            with open(self.filepath, _READMODE) as f:
                text = f.read()
        if not text.endswith('\n'):
            # for some reason, the parser requires the text end with a newline...
            text += '\n'
        self.text = text
        self.moduleAst = ast.parse(self.text, self.filepath)

    def newText(self):
        newText = self.text.splitlines()
        visitor = PymelAllRemoveVisitor()
        visitor.visit(self.moduleAst)

        editOffsets = {}
        for nameNode, pymelModule in visitor.pymelAllNames:
            lineIndex = nameNode.lineno - 1
            editOffset = editOffsets.get(lineIndex, 0)
            line = newText[lineIndex]
            nameStart = nameNode.col_offset + editOffset
            nameEnd = nameStart + len(nameNode.id)
            before = line[:nameStart]
            name = line[nameStart:nameEnd]
            after = line[nameEnd:]
            if name != nameNode.id:
                msg = "expected to find %r at line %d, offset %d - got %r (full line: %r)" % (
                    nameNode.id, nameNode.lineno, col, lineSubstring, line)
                raise RuntimeError(msg)
            newName = pymelModule + '.' + name
            if newName in self.REPLACEMENTS:
                newName = self.REPLACEMENTS[newName]
            newText[lineIndex] = before + newName + after
            editOffsets[lineIndex] = editOffset + (len(newName) - len(name))
        return '\n'.join(newText)

PYTHON_FILE_RE = re.compile(r'^(?!\._).*(?<!\.noPymelAll)(?<!\.withPymelAll)\.pyw?$')
FROM_PYMEL_ALL_RE = re.compile(r'^from pymel\.all import \*[ \t]*(#[^\n]*)?\n', re.MULTILINE)
PYMEL_CORE_AS_PM_RE = re.compile(r'^import pymel.core as pm[ \t]*(#[^\n]*)?\n', re.MULTILINE)
def removePymelAll(filepath, p4merge=True, replace='ask', text=None):
    print "removePymelAll: %s" % filepath

    # if we have a directory, recurse
    if os.path.isdir(filepath):
        if text is not None:
            raise ValueError("when passing in a directory to removePymelAll, text may not be specified")
        for root, dirs, files in os.walk(filepath):
            for f in files:
                if not PYTHON_FILE_RE.match(f):
                    continue
                path = os.path.join(root, f)
                with open(path, _READMODE) as filehandle:
                    text = filehandle.read()
                if FROM_PYMEL_ALL_RE.search(text):
                    removePymelAll(os.path.join(root, f), p4merge=p4merge, replace=replace, text=text)
        return

    # otherwise, act on the single file
    remover = PymelAllRemover(filepath, text=text)
    filepath = remover.filepath
    newText = remover.newText()

    if FROM_PYMEL_ALL_RE.search(newText):
        if not PYMEL_CORE_AS_PM_RE.search(newText):
            newText = FROM_PYMEL_ALL_RE.sub('import pymel.core as pm\n', newText, 1)
        newText = FROM_PYMEL_ALL_RE.sub('', newText, 1)

    base, ext = os.path.splitext(filepath)
    newPath = base + '.noPymelAll' + ext
    with open(newPath, 'w') as f:
        f.write(newText)

    if os.path.isfile(newPath):
        if p4merge:
            subprocess.check_call(['p4merge', filepath, newPath])

        if os.path.isfile(newPath):
            oldPath = base + '.withPymelAll' + ext
            if replace == 'ask':
                prompt = "Do you wish to move %s to %s?\n(Old file will be moved to %s)\n" % (newPath, filepath, oldPath)
                answer = raw_input(prompt)
                replace = answer and answer[0].lower() == 'y'
            if replace:
                if os.path.isfile(oldPath):
                    os.remove(oldPath)
                shutil.move(filepath, oldPath)
                shutil.move(newPath, filepath)

def get_parser():
    parser = argparse.ArgumentParser(description='Convert scripts that use "from pymel.all import *" to use "import pymel.core as pm"')
    parser.add_argument('file', help='the .py script file to convert, or '
                        'directory to recurse for python files')
    parser.add_argument('--no-p4merge', dest='p4merge', action='store_false',
                        help="don't launch p4merge after conversion")
    parser.add_argument('--replace', dest='replace', action='store_true',
                        default='ask', help="automatically replace the original"
                        " file without asking")
    parser.add_argument('--no-replace', dest='replace', action='store_false',
                        default='ask', help="don't replace the original file "
                        "(and don't ask)")
    return parser

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(argv)
    removePymelAll(args.file, p4merge=args.p4merge, replace=args.replace)

if __name__ == '__main__':
    main()
