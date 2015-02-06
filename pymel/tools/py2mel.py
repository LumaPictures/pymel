"""
Convert python callables into MEL procedures
"""
import inspect
import re
import types
from pymel.util.arguments import isMapping, isIterable
from pymel.core.language import getMelType, isValidMelType, MELTYPES
import pymel.api.plugins as plugins
import maya.mel as _mm
import maya.OpenMayaMPx as mpx
import maya.OpenMaya as om

MAX_VAR_ARGS = 10
MAX_FLAG_ARGS = 6

_functionStore = {}

def _getFunction(function):
    # function is a string, so we must import its module and get the function object
    if isinstance(function, basestring):
        buf = function.split()
        funcName = buf.pop(-1)
        moduleName = '.'.join(buf)
        module = __import__(moduleName, globals(), locals(), [''])
        func = getattr(module, funcName)
    # function is a python object
    elif callable(function):
        func = function
    else:
        raise TypeError, "argument must be a callable python object or the full, dotted path to the callable object as a string."

    return func

# Flatten a multi-list argument so that in can be passed as
# a list of arguments to a command.

def getMelArgs(function, exactMelType=True):
    """
    given a python function, return ( ( argName, melType ), { argName : default }, { argName : description } )

        function
        This can be a callable python object or the full, dotted path to the callable object as a string.

        If a string representing the python function is passed, it should include all packages and sub-modules, along
        with the function's name:  'path.to.myFunc'

    """

    melArgs = []
    melArgDefaults = {}

    parsedTypes = {}
    parsedDescr = {}

    function = _getFunction(function)

    funcName = function.__name__
    moduleName = function.__module__

    args, varargs, kwargs, defaults = inspect.getargspec(function)
    if inspect.ismethod(function):
        # remove self/cls
        args = args[1:]
#    # epydoc docstring parsing
#    try:
#        import epydoc.docbuilder
#    except ImportError:
#        pass
#    else:
#        try:
#            docindex = epydoc.docbuilder.build_doc_index( [moduleName], parse=True, introspect=True, add_submodules=False)
#            linker = epydoc.markup.DocstringLinker()
#            api_doc = docindex.get_valdoc( moduleName + '.' + funcName )
#        except Exception, msg:
#            print "epydoc parsing failed: %s" % msg
#        else:
#            arg_types = api_doc.arg_types
#            #print api_doc.arg_descrs
#            #print arg_types
#            for arg, descr in api_doc.arg_descrs:
#                # filter out args that are not actually in our function.  that means currently no support for *args and **kwargs
#                # not yet sure why, but the keys to arg_types are lists
#                arg = arg[0]
#                if arg in args: # or kwargs:
#                    parsedDescr[arg] = descr.to_plaintext( linker )
#                    try:
#                        argtype = arg_types[ arg ].to_plaintext( linker )
#                        parsedTypes[arg] = getMelType( pyType=argtype, exactMelType=exactMelType )
#                        #print arg, argtype, parsedTypes.get(arg)
#                    except KeyError: pass

    try:
        ndefaults = len(defaults)
    except:
        ndefaults = 0

    # print args, varargs, kwargs, defaults

    nargs = len(args)
    offset = nargs - ndefaults
    for i, arg in enumerate(args):

        if i >= offset:
            # keyword args with defaults
            default = defaults[i - offset]
            melType = getMelType(default, exactOnly=exactMelType)
            # a mel type of None means there is no mel analogue for this python object
#            if not isValidMelType( melType ):
#                # if it's None, then we go to parsed docs
#                if melType is None:
#                    melType = parsedTypes.get( arg, None )
#                try:
#                    default = default.__repr__()
#                except AttributeError:
#                    default = str(default)
            melArgDefaults[arg] = default
        else:
            # args without defaults
            # a mel type of None means there is no mel analogue for this python object
            melType = parsedTypes.get(arg, None)

        melArgs.append((arg, melType))

    return tuple(melArgs), melArgDefaults, parsedDescr

def py2melProc(function, returnType=None, procName=None, evaluateInputs=True, argTypes=None):
    """This is a work in progress.  It generates and sources a mel procedure which wraps the passed
    python function.  Theoretically useful for calling your python scripts in scenarios where Maya
    does not yet support python callbacks.

    The function is inspected in order to generate a MEL procedure which relays its
    arguments on to the python function.  However, Python features a very versatile argument structure whereas
    MEL does not.

        - python args with default values (keyword args) will be set to their MEL analogue, if it exists.
        - normal python args without default values default to strings. If 'evaluteInputs' is True, string arguments passed to the
            MEL wrapper proc will be evaluated as python code before being passed to your wrapped python
            function. This allows you to include a typecast in the string representing your arg::

                myWrapperProc( "Transform('persp')" );

        - *args : not yet implemented
        - **kwargs : not likely to be implemented


    function
        This can be a callable python object or the full, dotted path to the callable object as a string.

        If passed as a python object, the object's __name__ and __module__ attribute must point to a valid module
        where __name__ can be found.

        If a string representing the python object is passed, it should include all packages and sub-modules, along
        with the function's name:  'path.to.myFunc'

    procName
        Optional name of the mel procedure to be created.  If None, the name of the function will be used.

    evaluateInputs
        If True (default), string arguments passed to the generated mel procedure will be evaluated as python code, allowing
        you to pass a more complex python objects as an argument. For example:

        In python:
            >>> import pymel.tools.py2mel as py2mel
            >>> def myFunc( arg ):
            ...    for x in arg:
            ...       print x
            >>> py2mel.py2melProc( myFunc, procName='myFuncWrapper', evaluateInputs=True )

        Then, in mel::
            // execute the mel-to-python wrapper procedure
            myFuncWrapper("[ 1, 2, 3]");

        the string "[1,2,3]" will be converted to a python list [1,2,3] before it is executed by the python function myFunc
    """

    function = _getFunction(function)

    funcName = function.__name__

    melCompile = []
    melArgs = []
    melArrayToStrDecls = []
    argList, defaults, description = getMelArgs(function)

    if argTypes:
        if isMapping(argTypes):
            pass
        elif isIterable(argTypes):
            tmp = argTypes
            argTypes = {}
            for i, argType in enumerate(tmp):
                argTypes[argList[i][0]] = argType
        else:
            raise ValueError, "argTypes must be iterable or mapping type"
        for argType in argTypes.values():
            if not isValidMelType(argType):
                raise TypeError, "%r is not a valid mel type: %s" % (argType, ', '.join(MELTYPES))
    else:
        argTypes = {}

    for arg, melType in argList:
        melType = argTypes.get(arg, melType)
        if melType == 'string':
            compilePart = "'\" + $%s + \"'" % arg
            melCompile.append(compilePart)
        elif melType == None:
            melType = 'string'
            compilePart = "'\" + $%s + \"'" % arg
            compilePart = r'eval(\"\"\"%s\"\"\")' % compilePart
            melCompile.append(compilePart)
        elif melType.count('[]'):
            melArrayToStrDecls.append('string $_%s ="("; int $i=0;for($i; $i<size($%s); $i++) { $_%s += ($%s[$i] + ",");  } $_%s += ")";' % (arg, arg, arg, arg, arg))
            melCompile.append("'\" + $_%s + \"'" % arg)
        else:
            melCompile.append("\" + $%s + \"" % arg)

        if melType.count('[]'):
            melType = melType.replace('[]', '')
            melArgs.append('%s $%s[]' % (melType, arg))
        else:
            melArgs.append('%s $%s' % (melType, arg))

    if procName is None:
        procName = funcName

    procDef = """global proc %s %s( %s ){ %s
    python("import %s; %s._functionStore[%r](%s)");}""" % (returnType if returnType else '',
                                                           procName,
                                                           ', '.join(melArgs),
                                                           ''.join(melArrayToStrDecls),
                                                           __name__,
                                                           __name__,
                                                           repr(function),
                                                           ','.join(melCompile))
    _functionStore[repr(function)] = function

    _mm.eval(procDef)
    return procName
#--------------------------------------------------------
#  Scripted Command Wrapper
#--------------------------------------------------------

def _shortnameByCaps(name):
    """
    uses hungarian notation (aka camelCaps) to generate a shortname, with a maximum of 3 letters
        ex.

            myProc --> mp
            fooBar --> fb
            superCrazyLongProc --> scl
    """

    shortname = name[0]
    count = 1
    for each in name[1:]:
        if each.isupper() or each.isdigit():
            shortname += each.lower()
            count += 1
            if count == 3:
                break
    return shortname

def _shortnameByUnderscores(name):
    """
    for python methods that use underscores instead of camelCaps, with a maximum of 3 letters
    """

    buf = name.split('_')
    shortname = ''
    for i, token in enumerate(buf):
        shortname += token[0].lower()
        if i == 2:
            break
    return shortname

def _shortnameByConvention(name):
    """
    chooses between byUnderscores and ByCaps
    """

    if '_' in name:
        return _shortnameByUnderscores(name)
    return _shortnameByCaps(name)

def _shortnameByDoc(method):
    """
    a shortname can be explicitly set by adding the keyword shortname followed by a colon followed by the shortname

            ex.

            class foo():
                def bar():
                    'shortname: b'
                    # do some things
                    return

    """
    if hasattr(method, "__doc__") and method.__doc__:
        m = re.search('.*shortname: (\w+)', method.__doc__)
        if m:
            return m.group(1)

def _nonUniqueName(longname, shortname, shortNames, operation):
    if operation in ['skip', 'warn', 'error'] and shortname in shortNames:
        message = "default short name %r for flag %r is taken" % (shortname, longname)
        if operation == 'warn':
            print 'warning: ' + message
            return False
        elif operation == 'skip':
            print 'skipping: ' + message
            return True
        else:
            raise TypeError(message)

def _invalidName(commandName, longname, operation):
    if len(longname) < 4 and operation in ['skip', 'warn', 'error']:
        message = 'long flag names must be at least 4 characters long: %s -%r' % (commandName, longname.lower())
        if operation == 'warn':
            print 'warning: ' + message
            return False
        elif operation == 'skip':
            print 'skipping: ' + message
            return True
        else:
            raise TypeError(message)


def _getShortNames(objects, nonUniqueName):
    """uses several different methods to generate a shortname flag from the long name"""
    shortNames = []
    nonunique = {}
    for obj in objects:
        if isinstance(obj, (list, tuple)):
            longname = obj[0]
            if obj[0] is not None:
                shortname = _shortnameByDoc(obj[1])
        else:
            longname = obj
            shortname = None
        # try _shortnameByDoc first

        if not shortname:
            shortname = _shortnameByConvention(longname)

        if not shortname or shortname in shortNames:
            if _nonUniqueName(longname, shortname, shortNames, nonUniqueName):
                shortname = None
            else:
                shortname = longname[0]
                unique = False
                for each in longname[1:3]:
                    shortname += each.lower()
                    if shortname not in shortNames:
                        unique = True
                        break
                if not unique:
                    baseshort = shortname[:2]
                    while True:
                        count = nonunique.get(baseshort, 0) + 1
                        nonunique[baseshort] = count
                        shortname = baseshort + str(count)
                        if shortname not in shortNames:
                            break
                    # print 'could not find a unique shortname for %s: using %s'% ( methodName, shortname )
        shortNames.append((longname, shortname))
    return tuple(shortNames)

def _getArgInfo(obj, allowExtraKwargs=True, maxVarArgs=MAX_VAR_ARGS,
                filter=None):
    '''Returns a dict giving info about the arugments for the function/property

    If obj is None, will return the 'defaults'.
    '''
    # per flag query and edit settings
    canQuery = False
    canEdit = False
    defaults = {}
    argNames = []

    # object.__init__ is a 'slot wrapper', but can't find that type defined
    # anywhere...
    if isinstance(obj, (types.BuiltinFunctionType, type(object.__init__),
                        types.NoneType)):
        maxArgs = 0
    elif isinstance(obj, property):
        # enable edit and query to determine what the user intends to do with this get/set property
        if obj.fget:
            canQuery = True
        if obj.fset:
            canEdit = True
        maxArgs = 1
    else:
        argNames, extraArgs, extraKwargs, defaults = inspect.getargspec(obj)
        if defaults is None:
            defaults = {}
        if isinstance(obj, types.MethodType):
            # remove the self arg
            del argNames[0]
        if extraKwargs and not allowExtraKwargs:
            raise ValueError('arguments of the format **kwargs are not supported')

        # turn defaults into a dict
        defaults = dict(zip(argNames[-len(defaults):], defaults))

        if filter:
            newArgNames = []
            for argName in argNames:
                # can only filter out optional args
                if argName not in defaults or filter(argName):
                    newArgNames.append(argName)
                else:
                    del defaults[argName]
            argNames = newArgNames

        # a variable number of args can be passed to the flag. set the maximum number
        if extraArgs:
            maxArgs = maxVarArgs
        else:
            maxArgs = len(argNames)

    return {'maxArgs': maxArgs, 'canQuery': canQuery, 'canEdit': canEdit,
            'argNames': argNames, 'defaults': defaults}


class WrapperCommand(plugins.Command):
    _syntax = None
    _flagInfo = None
    _mainArgInfo = None

    @classmethod
    def createSyntax(cls):
        return cls._syntax

    def setResult(self, result):
        """
        convert to a valid result type
        """

#        int
#        double
#        bool
#        const MString
#        const MIntArray
#        const MDoubleArray
#        const MStringArray

        if result is None:
            return

        if isinstance(result, dict):
            # convert a dictionary into a 2d list
            newResult = []
            for key, value in result.items():
                newResult.append(key)
                newResult.append(value)
            mpx.MPxCommand.setResult(newResult)
        else:
            # try:
            mpx.MPxCommand.setResult(result)

    def parseCommandArgs(self, argData):
        argValues = []
        i = 0
        while(1):
            try:
                argValues.append(argData.commandArgumentString(i).encode())
            except RuntimeError:
                break
            else:
                i += 1
        return argValues

    def parseFlagArgs(self, argData):
        """
        cycle through known flags looking for any that have been set.

        :rtype: a list of (flagLongName, flagArgList) tuples
        """

        argValues = []
        for flag in self._flagInfo:
            if argData.isFlagSet(flag):
                canQuery = self._flagInfo[flag].get('canQuery', False)
                canEdit = self._flagInfo[flag].get('canEdit', False)
                if argData.isQuery():
                    if not canQuery:
                        raise SyntaxError, 'cannot use the query flag with %s' % flag
                elif argData.isEdit():
                    if not canEdit:
                        raise SyntaxError, 'cannot use the query edit with %s' % flag
                elif canQuery or canEdit:
                    raise SyntaxError, 'the %s flag must be used with either query or edit' % flag

                flagArgs = []
                maxArgs = self._flagInfo[flag]['maxArgs']
                for i in range(maxArgs):
                    try:
                        flagArgs.append(argData.flagArgumentString(flag, i))
                    except Exception:
                        break

                argValues.append((flag, flagArgs))
        return argValues

def py2melCmd(pyObj, commandName=None, register=True, includeFlags=None,
              excludeFlags=[], includeFlagArgs=None, excludeFlagArgs={},
              nonUniqueName='warn', invalidName='warn'):
    """
    Create a MEL command from a python function or class.

    A MEL command has two types of arguments: command arguments and flag arguments.  In the case of passing a function, the function's
    non-keyword arguments become the command arguments and the function's keyword arguments become the flag arguments.
    for example::

        def makeName( first, last, middle=''):
            if middle:
                return first + ' ' + middle + ' ' + last
            return first + ' ' + last

        import pymel as pm
        from pymel.tools.py2mel import py2melCmd
        cmd = py2melCmd( makeName, 'makeNameCmd' )
        pm.makeNameCmd( 'Homer', 'Simpson')
        # Result: Homer Simpson #
        pm.makeNameCmd( 'Homer', 'Simpson', middle='J.')
        # Result: Homer J. Simpson #

    Of course, the real advantage of this tool is that now your python function is available from within MEL as a command::

        makeNameCmd "Homer" "Simpson";
        // Result: Homer Simpson //
        makeNameCmd "Homer" "Simpson" -middle "J.";
        // Result: Homer J. Simpson //

    To remove the command, call the deregister method of the class returned by py2melCmd::

        cmd.deregister()

    This function attempts to automatically create short names (3 character max) based on the long names of the methods or arguments of the pass python object.
    It does this by looping through long names in alphabetical order and trying the following techniques until a unique short name is found:

            1. by docstring (methods only): check the method docstring looking for something of the form ``shortname: xyz``::
                class Foo():
                    def bar():
                        'shortname: b'
                        # do some things
                        return
            2. by convention:  if the name uses under_scores or camelCase, use the first letter of each "word" to generate a short name up to 3 letters long
            3. first letter
            4. first two letters
            5. first three letters
            6. first two letters plus a unique digit

    .. warning:: if you edit the python object that is passed to this function it may result in short names changing!  for example, if you have a class like the following::

                class Foo():
                    def bar():
                        pass

            ``Foo.bar`` will be assigned the short flag name 'b'. but if you later add the method ``Foo.baa``, it will be assigned the short flag name 'b' and 'bar' will be given 'ba'.
            **The only way to be completely sure which short name is assigned is to use the docstring method described above.**

    Parameters
    ----------
    commandName : str
        name given to the generated MEL command
    register : bool
        whether or not to automatically register the generated command.  If
        False, you will have to manually call the `register` method of the
        returned `WrapperCommand` instance
    includeFlags : list of str
        list of flags to include. if given, other flags will be ignored
    exludeFlags : list of str
        list of flags to exclude
    includeFlagArgs : dict from str to list of str
        for each flag, a list of arg names to include; if given, other args will
        be ignored
    excludeFlagArgs : dict from str to list of str
        for each flag, a list of arg names to exclude
    nonUniqueName : 'force', 'warn', 'skip', or 'error'
        what to do if a flag name is not unique
    invalidName: 'force', 'warn', 'skip', or 'error'
        what to do if a flag name is invalid

    """
    if not commandName:
        commandName = pyObj.__name__
    if includeFlagArgs is None:
        includeFlagArgs = {}

    def goodFlag(flag):
        return ((includeFlags is None or flag in includeFlags)
                and flag not in excludeFlags and not flag.startswith('_'))

    syntax = om.MSyntax()
    flagInfo = {}
    flags = []   # ordered list of flags
    if inspect.isfunction(pyObj):
        # args         --> command args
        # keyword args --> flags
        classWrap = False

        mainArgInfo = _getArgInfo(pyObj, allowExtraKwargs=False,
                                  filter=goodFlag)
        ndefaults = len(mainArgInfo['defaults'])

        # positional args become the command args
        cmdArgs = mainArgInfo['argNames'][:-ndefaults]

        # keyword args become the flags
        flags = mainArgInfo['argNames'][-ndefaults:]
        flags = [x for x in flags if goodFlag(x)]
        mainArgInfo['maxArgs'] = len(cmdArgs)
        mainArgInfo['argNames'] = cmdArgs

        for flag in flags:
            # currently keyword args only support one item per flag. eventually we may
            # detect when a keyword expects a list as an argument
            flagInfo[flag] = {'maxArgs': 1}

    elif inspect.isclass(pyObj):
        # init/new args--> command args
        # methods      --> flags
        # method args  --> flag args
        classWrap = True

        # __init__ or __new__ becomes the command args
        try:
            initFunc = pyObj.__init__
        except AttributeError:
            initFunc = None
        if initFunc is None or initFunc == object.__init__:
            initFunc = object.__new__
        mainArgInfo = _getArgInfo(initFunc, filter=goodFlag)

        # methods become the flag args
        for longname, method in inspect.getmembers(pyObj, lambda x: inspect.ismethod(x) or isinstance(x, property)):
            if not goodFlag(longname):
                continue
            flags.append(longname)

            includeArgs = includeFlagArgs.get(longname)
            excludeArgs = excludeFlagArgs.get(longname, ())

            def goodFlagArg(flagArg):
                return ((includeArgs is None or flagArg in includeArgs)
                        and flagArg not in excludeArgs)

            argInfo = _getArgInfo(method, maxVarArgs=MAX_FLAG_ARGS,
                                  filter=goodFlagArg)
            argInfo['method'] = method
            argInfo['methodName'] = longname
            argInfo['type'] = type(method)
            flagInfo[longname] = argInfo

    # command args
    for _ in range(mainArgInfo['maxArgs']):
        syntax.addArg(om.MSyntax.kString)

    for origname, shortname in _getShortNames(flags, nonUniqueName):
        if shortname is None:
            # we skipped the flag
            continue
        longname = origname
        if _invalidName(commandName, longname, invalidName):
            continue
        if len(longname) < 4:
            longname = longname.ljust(4, 'x')

        # TODO: currently no check that LONG name is unique...
        # ...maybe roll this into _getShortNames... make it _getNames?
        if longname != origname:
            flagInfo[longname] = flagInfo.pop(origname)

        thisFlagInfo = flagInfo[longname]
        # NOTE: shortname and longname MUST be stored on the class or they will
        # get garbage collected and the names will be destroyed
        thisFlagInfo['shortname'] = shortname

        if thisFlagInfo['canQuery']:
            syntax.enableQuery(True)
        if thisFlagInfo['canEdit']:
            syntax.enableEdit(True)

        # currently keyword args only support one item per flag. eventually we may
        # detect when a keyword expects a list as an argument
        syntaxArgs = [shortname, longname] + ([om.MSyntax.kString] * thisFlagInfo['maxArgs'])
        syntax.addFlag(*syntaxArgs)

    class dummyCommand(WrapperCommand):
        _syntax = syntax
        _flagInfo = flagInfo
        _mainArgInfo = mainArgInfo

        def doIt(self, argList):

            argData = om.MArgParser(self.syntax(), argList)

            cmdArgs = self.parseCommandArgs(argData)
            flagArgs = self.parseFlagArgs(argData)

            if not classWrap:
                # doing a function wrap...

                # unpack the flag arguments, there should always only be 1
                kwargs = dict([(x[0], x[1][0]) for x in flagArgs])

                res = pyObj(*cmdArgs, **kwargs)
            else:
                # doing a class wrap...

                if len(flagArgs) != 1:
                    raise RuntimeError('only one flag can be used at a time for command %s' % commandName)
                longname, flagArgs = flagArgs[0]

                inst = pyObj(*cmdArgs)
                flagInfo = self._flagInfo[longname]
                attrType = flagInfo['type']
                methodName = flagInfo['methodName']

                if issubclass(attrType, types.MethodType):  # method
                    # build out the args and kwargs...
                    # ...can't just pass flagArgs straight into our method using
                    #   myMethod(*flagArgs)
                    # ...because we may have filtered out some optional args, so
                    # the positional information isn't right...
                    ndefaults = len(flagInfo['defaults'])
                    args = flagArgs[:-ndefaults]

                    defaultNames = flagInfo['argNames'][-ndefaults:]
                    defaultVals = flagArgs[-ndefaults:]
                    kwargs = dict(zip(defaultNames, defaultVals))

                    res = getattr(inst, methodName)(*args, **kwargs)
                else:  # property
                    if argData.isQuery():
                        res = getattr(inst, methodName)
                    elif argData.isEdit():
                        # property-defined flags can only take one arg
                        if len(flagArgs) != 1:
                            raise RuntimeError('flag %s for command %s may only have one arg' % (longname, commandName))
                        res = setattr(inst, methodName, flagArgs[0])
                    else:
                        raise SyntaxError, "properties must either be edited or queried"
            return self.setResult(res)

    dummyCommand.__name__ = commandName
    if register:
        dummyCommand.register()
    return dummyCommand
