
"""
Convert mel code into python code.

==========================
Mel To Python Translator
==========================


Known Limitations
=================

array index assignment
----------------------

In mel, you can directly assign the value of any element in an array, and all intermediate elements will be
automatically filled. This is not the case in python: if the list index is out of range an IndexError will be
raised. I've added fixes for several common array assignment conventions:

append new element
~~~~~~~~~~~~~~~~~~

MEL::

    string $strArray[];
    $strArray[`size $strArray`] = "foo";

Python::

    strArray = []
    strArray.append("foo")

assignment relative to end of array
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MEL::

    strArray[`size $strArray`-3] = "foo";

Python::

    strArray[-3] = "foo"

However, since the translator does not track values of variables, it does not know if any given index is out of
range or not. so, the following would raise a 'list assignment index out of range' error when converted to
python and would need to be manually fixed::

    string $strArray[];
    for ($i=0; $i<5; $i++)
        $strArray[$i] = "foo"


for(init; condition; update)
----------------------------

    the closest equivalent to this in python is something akin to::

        for i in range(start, end):
            ...

    in order for this type of for loop to be translated into a python for loop it must meet several requirements:

    1. the initialization, condition, and update expressions must not be empty.

        not translatable::

              for(; ; $i++) print $i;

    2. there can be only one conditional expression.

        not translatable::

              for($i=0; $i<10, $j<20; $i++) print $i;

    3. the variable which is being updated and tested in the condition (aka, the iterator) must exist alone on one
        side of the    conditional expression. this one is easy enough to fix, just do some algebra:

        not translatable::

              for($i=0; ($i-2)<10, $i++) print $i;

        translatable::

              for($i=0; $i<(10+2), $i++) print $i;

    4. the iterator can appear only once in the update expression:

        not translatable::

              for($i=0; $i<10; $i++, $i+=2) print $i;

    if these conditions are not met, the for loop will be converted into a while loop::

        i=0
        while 1:
            if not ( (i - 2)<10 ):
                break
            print i
            i+=1


Inconveniences
==============

Switch Statements
-----------------
Alas, switch statements are not supported by python. the translator will convert them into an if/elif/else statement.


Global Variables
----------------

Global variables are not shared between mel and python.  two functions have been added to pymel for this purpose:
`pymel.core.langauage.getMelGlobal` and `pymel.core.langauage.setMelGlobal`. by default, the translator will convert mel global variables into python global
variables AND intialize them to the value of their corresponding mel global variable using `getMelGlobal()`. if your
python global variable does not need to be shared with other mel scripts, you can remove the get- and
setMelGlobals lines (for how to filter global variables, see below). however, if it does need to be shared, it is very
important that you manually add `setMelGlobal()` to update the variable in the mel environment before calling any mel
procedures that will use the global variable.

In order to hone the accuracy of the translation of global variables, you will find two dictionary parameters below --
`global_var_include_regex` and `global_var_exclude_regex` -- which you can use to set a regular expression string
to tell the translator which global variables to share with the mel environment (i.e. which will use the get and set
methods described above) and which to not.  for instance, in my case, it is desirable for all of maya's global
variables to be initialized from their mel value but for our in-house variables not to be, since the latter are often
used to pass values within a single script. see below for the actual regular expressions used to accomplish this.


Comments
--------
Rules on where comments may be placed is more strict in python, so expect your comments to be shifted around a bit
after translation.


Formatting
----------

Much of the formatting of your original script will be lost. I apologize for this, but python is much more strict
about formatting than mel, so the conversion is infinitely simpler when the formatting is largely discarded
and reconstructed based on pythonic rules.


Solutions and Caveats
=====================

catch and catchQuiet
--------------------

There is no direct equivalent in python to the catch and catchQuiet command and it does not exist in maya.cmds so i wrote two
python commands of the same name and put them into pymel. these are provided primarily for compatibility with
automatically translated scripts. try/except statements should be used instead of catch or catchQuiet if coding
from scratch.

for( $elem in $list )
---------------------

This variety of for loop has a direct syntactical equivalent in python.  the only catch here is that maya.cmds
functions which are supposed to return lists, return None when there are no matches. life would be much simpler
if they returned empty lists instead.  the solution currently lies in pymel, where i have begun
correcting all of these command to return proper results.  i've started with the obvious ones, but there
are many more that i need to fix.  you'll know you hit the problem when you get this error: 'TypeError: iteration
over non-sequence'. just email me with commands that are giving you problems and i'll fix them as
quickly as i can.

"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from . import melparse
try:
    from pymel.util.external.ply.lex import LexError
except ImportError:
    from ply.lex import LexError

import pymel.util as util
import pymel.internal as internal
import pymel.internal.factories as _factories
import pymel
import pymel.core as pm
import os

if False:
    from typing import *

log = internal.getLogger(__name__)

"""
This is a dictionary for custom remappings of mel procedures into python functions, classes, etc. If you are like me you probably have a
library of helper mel scripts to make your life a bit easier. you will probably find that python has a built-in equivalent for many of
these.

i've provided a few entries as examples to show you how to implement remappings in mel2py. the first procedure in the dictionary is
'firstElem', which simply returns the first element of a string array, useful when the first element of a command is all you need. as you
can see, the key in the dictionary is the procedure name, and the value is a function which takes two inputs: a list of arguments to the
procedure being remapped, and a ply yacc token object, which you probably will not need to use. the function should return a string
representing the new command. also, note that the list of arguments will all be strings and will already be converted into their python
equivalents. in the case of 'firstElem', it will perform conversions like the following:

        firstElem( ls(sl=1) )     -->     ls(sl=1)[0]

        firstElem( myListVar )    -->        myListVar[0]

"""


custom_proc_remap = {
    'firstElem': ('string', lambda args, t: '%s[0]' % (args[0])),
    'firstFloatElem': ('float', lambda args, t: '%s[0]' % (args[0])),
    'stringArrayAppend': ('string[]', lambda args, t: '%s + %s' % (args[0], args[1])),
    'stringInArray': ('int', lambda args, t: '%s in %s' % (args[0], args[1])),
    'stringInStringArray': ('int', lambda args, t: '%s in %s' % (args[0], args[1])),
    'stringArrayPrefix': ('string[]', lambda args, t: '[ %s + x for x in %s ]' % (args[0], args[1])),
    'stringArraySuffix': ('string[]', lambda args, t: '[ x + %s for x in %s ]' % (args[0], args[1])),
    'addPad': ('string', lambda args, t: "'%0" + args[1] + "d' % " + args[0]),
    'getRefFileFromObject': ('string', lambda args, t: '%s.referenceFile()' % (args[0]))
}

# do not change the following line !!!
melparse.proc_remap.update(custom_proc_remap)


def resolvePath(melobj, recurse=False, exclude=(), melPathOnly=False, basePackage=''):
    """
    if passed a directory, get all mel files in the directory
    if passed a file, ensure it is a mel file
    if passed a procedure name, find its file

    Returns tuples of the form (moduleName, melfile).
    """
    if basePackage is None:
        basePackage = ''
    files = []
    recursedResults = []
    filepath = util.path(melobj)
    if filepath.isfile():
        if filepath.ext == '.mel':
            files = [filepath.truepath()]
        else:
            log.warning("File is not a mel script: %s" % (filepath))
            files = []
    elif filepath.isdir():
        files = [f.truepath() for f in filepath.files('[a-zA-Z]*.mel')]
        if recurse:
            for dir in filepath.dirs():
                recursedResults.extend(resolvePath(dir, recurse=recurse,
                                                   exclude=exclude, melPathOnly=melPathOnly,
                                                   basePackage=basePackage + '.' + melparse.pythonizeName(dir.basename())))
    # elif not filepath.exists():
    else:
        # see if it's a procedure that we can derive a path from
        try:
            info = pm.mel.whatIs(melobj).split(': ')[-1]
            assert info != 'Unknown', "If providing a procedure or a short file name, ensure the appropriate script is sourced"
            melfile = util.path(info)
            files = [melfile.truepath()]
        except Exception as msg:
            log.warning("Could not determine mel script from input '%s': %s." % (filepath, msg))
    if exclude:
        for i, badFile in enumerate(exclude):
            badFile = util.path(badFile).canonicalpath()
            if badFile.isdir():
                badFile = badFile + os.sep
            exclude[i] = badFile
        filteredFiles = []
        for f in files:
            fileGood = True
            for badFile in exclude:
                if f.samepath(badFile) \
                   or (badFile.isdir()
                       and f.canonicalpath().startswith(badFile)):
                    fileGood = False
            if fileGood:
                filteredFiles.append(f)
        files = filteredFiles
    if melPathOnly:
        files = [x for x in files if fileOnMelPath(x)]
    if basePackage and basePackage[-1] != '.':
        basePackage = basePackage + '.'
    return [(basePackage + melparse.getModuleBasename(x), x) for x in files] + recursedResults


def fileOnMelPath(file):
    """
    Return True if this file is on the mel path.
    """
    file = util.path(file)
    info = pm.mel.whatIs(file.basename()).split(': ', 1)
    if len(info) < 2:
        # If there wasn't a ':' character, the result was probably 'Unknown, or something similar -
        # anyway, not what we're looking for
        return False
    if info[0] not in ('Mel procedure found in', 'Script found in'):
        return False
    path = util.path(info[1])
    return path.samepath(file)


def _updateCurrentModules(newResults):
    currentModules = melparse.batchData.currentModules
    for moduleName, melfile in newResults:
        if not isinstance(melfile, pm.Path):
            melfile = util.path(melfile)
        if melfile in currentModules.values():
            oldModule = currentModules.get_key(melfile)
            if oldModule == moduleName:
                continue
            if moduleName.count('.') >= oldModule.count('.'):
                continue
        elif moduleName in currentModules:
            raise RuntimeError('two mel files result in same python module name: %s, %s => %s' % (currentModules[moduleName], melfile, moduleName))
        currentModules[moduleName] = melfile


def _makePackages():
    # Maps from a package (in tuple form) to base directory
    packages = {}

    for moduleName, melfile in melparse.batchData.currentModules.items():
        if moduleName.count('.') < 1:
            continue
        package = tuple(moduleName.split('.')[:-1])
        if melparse.batchData.outputDir:
            packages[package] = melparse.batchData.outputDir
        else:
            assert package == tuple(melfile.splitall()[-(len(package) + 1):-1]), \
                "package %s did not match melfile %s directory structure" % ('.'.join(package), melfile)
            packages[package] = util.path.joinpath(*(melfile.splitall()[:-(len(package) + 1)]))

    for packageTuple, baseDir in packages.items():
        if not baseDir.isdir():
            baseDir.makedirs()
        curDir = baseDir
        for nextDir in packageTuple:
            curDir = curDir / nextDir
            if not curDir.isdir():
                curDir.mkdir()
            initFile = curDir / '__init__.py'
            if not initFile.isfile():
                initFile.touch()


def _getInputFiles(input, recurse=False, exclude=(), melPathOnly=False, basePackage=''):
    """
    Returns tuples of the form (packageName, melfile)
    """
    results = []
    if not util.isIterable(input):
        input = [input]
    for f in input:
        results.extend(resolvePath(f, recurse=recurse, exclude=exclude, melPathOnly=melPathOnly, basePackage=basePackage))
    return results


def melInfo(input):
    # type: (str) -> Tuple[Iterable[str], dict, dict]
    """
    Get information about procedures in a mel file.

        >>> import pymel.tools.mel2py as mel2py
        >>> mel2py.melInfo('attributeExists')
        (['attributeExists'], {'attributeExists': {'returnType': 'int', 'args': [('string', '$attr'), ('string', '$node')]}}, {})

    Parameters
    ----------
    input : str
        can be a mel file or a sourced mel procedure

    Returns
    -------
    allProcs : Iterable[str]
        The list of procedures in the order the are defined
    globalProcs : dict
        A dictionary of global procedures, with the following entries:
            - returnType: mel type to be returned
            - args: a list of (type, variable_name) pairs
    localProcs : dict
        A dictionary of local procedures, formatted the same as with globals
    """

    # TODO: change this to use _getInputFiles, with an option to prevent recursing directories
    res = resolvePath(input)
    if len(res) != 1:
        raise ValueError("input must be a mel script or a known procedure from a sourced mel script.")
    f = res[0][1]

    cbParser = melparse.MelScanner()
    cbParser.build()
    return cbParser.parse(f.bytes())


def mel2pyStr(data, currentModule=None, pymelNamespace='', forceCompatibility=False, verbosity=0, basePackage=None):
    # type: (str, str, str, bool, int, Any) -> str
    """
    convert a string representing mel code into a string representing python code

        >>> import pymel.tools.mel2py as mel2py
        >>> print(mel2py.mel2pyStr('paneLayout -e -configuration "top3" test;'))
        from pymel.all import *
        paneLayout('test',configuration="top3",e=1)
        <BLANKLINE>

    Note that when converting single lines, the lines must end in a semi-colon,
    otherwise it is technically invalid syntax.

    Parameters
    ----------
    data : `str`
        string representing coe to convert
    currentModule : `str`
        the name of the module that the hypothetical code is executing in.
        In most cases you will leave it at its default, the __main__ namespace.
    pymelNamespace : `str`
        the namespace into which pymel will be imported.  the default is '',
        which means ``from pymel.all import *``
    forceCompatibility : `bool`
        If True, the translator will attempt to use non-standard python types in order to produce
        python code which more exactly reproduces the behavior of the original mel file, but which
        will produce "uglier" code.  Use this option if you wish to produce the most reliable code
        without any manual cleanup.
    verbosity : `int`
        Set to non-zero for a *lot* of feedback
    """

    mparser = melparse.MelParser()
    mparser.build(currentModule, pymelNamespace=pymelNamespace, forceCompatibility=forceCompatibility, verbosity=verbosity)

    results = mparser.parse(data)
    # print mparser.lexer.global_procs
    return results


def mel2py(input, outputDir=None,
           pymelNamespace='', forceCompatibility=False,
           verbosity=0, test=False,
           recurse=False, exclude=(), melPathOnly=False,
           basePackage=None):
    # type: (Any, str, str, bool, int, bool, bool, str, bool, str) -> None
    """
    Batch convert an entire directory

    Parameters
    ----------
    input
        May be a directory, a list of directories, the name of a mel file, a
        list of mel files, or the name of a sourced procedure.
        If only the name of the mel file is passed, mel2py will attempt to
        determine the location of the file using the 'whatIs' mel command,
        which relies on the script already being sourced by maya.
    outputDir : `str`
        Directory where resulting python files will be written to
    pymelNamespace : `str`
        the namespace into which pymel will be imported.  the default is '',
        which means ``from pymel.all import *``
    forceCompatibility : `bool`
        If True, the translator will attempt to use non-standard python types in order to produce
        python code which more exactly reproduces the behavior of the original mel file, but which
        will produce "uglier" code.  Use this option if you wish to produce the most reliable code
        without any manual cleanup.
    verbosity : `int`
        Set to non-zero for a *lot* of feedback
    test : `bool`
        After translation, attempt to import the modules to test for errors
    recurse : `bool`
        If the input is a directory, whether or not to recursively search subdirectories as well.
        Subdirectories will be converted into packages, and any mel files within those subdirectories
        will be submodules of that package.
    exclude : `str`
        A comma-separated list of files/directories to exclude from processing, if input is a directory.
    melPathOnly : `bool`
        If true, will only translate mel files found on the mel script path.
    basePackage : `str`
        Gives the package that all translated modules will be a part of; if None or an empty string, all
        translated modules are assumed to have no base package.
    """
    if basePackage is None:
        basePackage = ''
    melparse.batchData = melparse.BatchData()
    batchData = melparse.batchData
    batchData.basePackage = basePackage
    if outputDir is not None:
        outputDir = util.path(outputDir)
    batchData.outputDir = outputDir

    if outputDir and not os.path.exists(outputDir):
        os.makedirs(outputDir)

    currentFiles = _getInputFiles(input, recurse=recurse, exclude=exclude, melPathOnly=melPathOnly, basePackage=basePackage)
    if not currentFiles:
        raise ValueError("Could not find any scripts to operate on. Please pass a directory, a list of directories, the name of a mel file, a list of mel files, or the name of a sourced procedure")
    _updateCurrentModules(currentFiles)

    _makePackages()

    importCnt = 0
    succeeded = []
    for moduleName, melfile in batchData.currentModules.items():
        print(melfile, moduleName)

        if melfile in batchData.scriptPath_to_moduleText:
            print("Using pre-converted mel script", melfile)
            converted = batchData.scriptPath_to_moduleText[melfile]

        else:
            data = melfile.bytes()
            print("Converting mel script", melfile)
            try:
                converted = mel2pyStr(data, moduleName, pymelNamespace=pymelNamespace, verbosity=verbosity)
            except melparse.MelParseError as e:
                if e.file is None:
                    e.file = melfile
                raise

        header = """%s from mel file:
# %s

""" % (melparse.tag, melfile)

        converted = header + converted

        splitModule = moduleName.split('.')
        if outputDir is None:
            currOutDir = melfile.parent
        else:
            currOutDir = outputDir
            if len(splitModule) > 1:
                currOutDir = currOutDir.joinpath(*splitModule[:-1])

        pyfile = currOutDir.joinpath(splitModule[-1] + '.py')
        print("Writing converted python script: %s" % pyfile)
        pyfile.write_bytes(converted)
        succeeded.append(pyfile)

        # except (ValueError, IndexError, TypeError, LexError), msg:
        #    if ignoreErrors:
        #        print 'failed:', msg
        #    else:
        #        raise Exception, msg
        #
    if test:
        for pyfile in succeeded:
            print("Testing", pyfile)
            try:
                __import__(pyfile.namebase)
            except (SyntaxError, IndentationError) as msg:
                print('A syntax error exists in this file that will need to be manually fixed: %s' % msg)
            except RuntimeError as msg:
                print('This file has code which executed on import and failed: %s' % msg)
            except ImportError as msg:
                print('%s' % msg)
            except Exception as msg:
                print('This file has code which executed on import and failed: %s' % msg)
            else:
                importCnt += 1

    succCnt = len(succeeded)
    print("%d total processed for conversion" % len(batchData.currentModules))
    print("%d files succeeded" % succCnt)
    print("%d files failed" % (len(batchData.currentModules) - succCnt))
    if test:
        print("%d files imported without error" % (importCnt))

    succCnt = 0


