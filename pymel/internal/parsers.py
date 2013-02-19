import re, os.path, platform
from HTMLParser import HTMLParser
import pymel.util as util
import pymel.versions as versions
import plogging
from pymel.mayautils import getMayaLocation

try:
    from pymel.util.external.BeautifulSoup import BeautifulSoup, NavigableString
except ImportError:
    from BeautifulSoup import BeautifulSoup, NavigableString
from keyword import iskeyword as _iskeyword

FLAGMODES = ('create', 'query', 'edit', 'multiuse')

_logger = plogging.getLogger(__name__)

def mayaIsRunning():
    """
    Returns True if maya.cmds have  False otherwise.

    Early in interactive startup it is possible for commands to exist but for Maya to not yet be initialized.

    :rtype: bool
    """

    # Implementation is essentially just a wrapper for getRunningMayaVersionString -
    # this function was included for clearer / more readable code

    try :
        from maya.cmds import about
        about(version=True)
        return True
    except :
        return False

def mayaDocsLocation(version=None):
    docLocation = os.environ.get('MAYA_DOC_DIR')

    if (not docLocation and (version is None or version == versions.installName() )
            and mayaIsRunning()):
        # Return the doc location for the running version of maya
        from maya.cmds import showHelp
        docLocation = showHelp("", q=True, docs=True)

        # Older implementations had no trailing slash, but the result returned by
        # showHelp has a trailing slash... so eliminate any trailing slashes for
        # consistency
        while docLocation != "" and os.path.basename(docLocation) == "":
            docLocation = os.path.dirname(docLocation)

    # Want the docs for a different version, or maya isn't initialized yet
    if not docLocation or not os.path.isdir(docLocation):
        docBaseDir = os.environ.get('MAYA_DOC_BASE_DIR')
        if not docBaseDir:
            docBaseDir = getMayaLocation(version) # use original version
            if docBaseDir is None and version is not None:
                docBaseDir = getMayaLocation(None)
                _logger.warning("Could not find an installed Maya for exact version %s, using first installed Maya location found in %s" % (version, docBaseDir) )

            if platform.system() == 'Darwin':
                docBaseDir = os.path.dirname(os.path.dirname(docBaseDir))
            docBaseDir = os.path.join(docBaseDir, 'docs')

        if version:
            short_version = versions.parseVersionStr(version, extension=False)
        else:
            short_version = versions.shortName()
        docLocation = os.path.join(docBaseDir , 'Maya%s' % short_version, 'en_US')

    return os.path.realpath(docLocation)

#---------------------------------------------------------------
#        Doc Parser
#---------------------------------------------------------------
class CommandDocParser(HTMLParser):

    def __init__(self, command):
        self.command = command
        self.flags = {}  # shortname, args, docstring, and a list of modes (i.e. edit, create, query)
        self.currFlag = ''
        # iData is used to track which type of data we are putting into flags, and corresponds with self.datatypes
        self.iData = 0
        self.pcount = 0
        self.active = False  # this is set once we reach the portion of the document that we want to parse
        self.description = ''
        self.example = ''
        self.emptyModeFlags = [] # when flags are in a sequence ( lable1, label2, label3 ), only the last flag has queryedit modes. we must gather them up and fill them when the last one ends
        HTMLParser.__init__(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.command)

    def startFlag(self, data):
        #_logger.debug(self, data)
        #assert data == self.currFlag
        self.iData = 0
        self.flags[self.currFlag] = {'longname': self.currFlag, 'shortname': None, 'args': None,
                                     'numArgs': None, 'docstring': '', 'modes': [] }

    def addFlagData(self, data):
        # encode our non-unicode 'data' string to unicode
        data = data.decode('utf-8')
        # now saftely encode it to non-unicode ascii, ignorning unknown characters
        data = data.encode('ascii', 'ignore')
        # Shortname
        if self.iData == 0:
            self.flags[self.currFlag]['shortname'] = data.lstrip('-\r\n')

        # Arguments
        elif self.iData == 1:
            typemap = {
             'string'  : unicode,
             'float'   : float,
             'double'  : float,
             'linear'  : float,
             'angle'   : float,
             'int'     : int,
             'uint'    : int,
             'int64'   : int,
             'index'   : int,
             'integer'  : int,
             'boolean'  : bool,
             'script'   : 'script',
             'name'     : 'PyNode',
             'select'   : 'PyNode',
             'time'     : 'time',
             'timerange': 'timerange',
             'floatrange':'floatrange',
             '...'      : '...' # means that there is a variable number of args. we don't do anything with this yet
            }
            args = [x.strip() for x in data.replace('[', '').replace(']', '').split(',') if x.strip()]
            for i, arg in enumerate(args):
                if arg not in typemap:
                    _logger.error("%s: %s: unknown arg type %r" % (self, self.currFlag, arg))
                else:
                    args[i] = typemap[arg]
            numArgs = len(args)
            if numArgs == 0:
                args = bool
                #numArgs = 1
                # numArgs will stay at 0, which is the number of mel arguments.
                # this flag should be renamed to numMelArgs
            elif numArgs == 1:
                args = args[0]

            self.flags[self.currFlag]['args'] = args
            self.flags[self.currFlag]['numArgs'] = numArgs

        # Docstring
        else:
            #self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).strip() + " "
            data = data.replace( 'In query mode, this flag needs a value.', '' )
            data = data.replace( 'Flag can appear in Create mode of command', '' )
            data = data.replace( 'Flag can appear in Edit mode of command', '' )
            data = data.replace( 'Flag can appear in Query mode of command', '' )
            data = data.replace( '\r\n', ' ' ).lstrip()
            data = data.replace( '\n', ' ' ).lstrip()
            data = data.strip('{}\t')
            data = data.replace('*', '\*') # for reStructuredText
            self.flags[self.currFlag]['docstring'] += data
        self.iData += 1

    def endFlag(self):
        # cleanup last flag
        #data = self.flags[self.currFlag]['docstring']

        #_logger.debug(("ASSERT", data.pop(0), self.currFlag))
        try:
            if not self.flags[self.currFlag]['modes']:
                self.emptyModeFlags.append(self.currFlag)
            elif self.emptyModeFlags:
                    #_logger.debug("past empty flags:", self.command, self.emptyModeFlags, self.currFlag)
                    basename = re.match( '([a-zA-Z]+)', self.currFlag ).groups()[0]
                    modes = self.flags[self.currFlag]['modes']
                    self.emptyModeFlags.reverse()
                    for flag in self.emptyModeFlags:
                        if re.match( '([a-zA-Z]+)', flag ).groups()[0] == basename:
                            self.flags[flag]['modes'] = modes
                        else:
                            break

                    self.emptyModeFlags = []
        except KeyError, msg:
            pass
            #_logger.debug(self.currFlag, msg)

    def handle_starttag(self, tag, attrs):
        #_logger.debug("begin: %s tag: %s" % (tag, attrs))
        attrmap = dict(attrs)
        if not self.active:
            if tag == 'a':
                name = attrmap.get('name', None)
                if name == 'hFlags':
                    #_logger.debug('ACTIVE')
                    self.active = 'flag'
                elif name == 'hExamples':
                    #_logger.debug("start examples")
                    self.active = 'examples'
        elif tag == 'a' and 'name' in attrmap:
            self.endFlag()
            newFlag = attrmap['name'][4:]
            newFlag = newFlag.lstrip('-')
            self.currFlag = newFlag
            self.iData = 0
            #_logger.debug("NEW FLAG", attrs)
            #self.currFlag = attrs[0][1][4:]

        elif tag == 'img':
            mode = attrmap.get('title', None)
            if mode in FLAGMODES:
                #_logger.debug("MODES", attrs[1][1])
                self.flags[self.currFlag]['modes'].append(mode)
        elif tag == 'h2':
            self.active = False

    def handle_endtag(self, tag):
        #if tag == 'p' and self.active == 'command': self.active = False
        #_logger.debug("end: %s" % tag)
        if not self.active:
            if tag == 'p':
                if self.pcount == 3:
                    self.active = 'command'
                else:
                    self.pcount += 1
        elif self.active == 'examples' and tag == 'pre':
            self.active = False

    def handle_entityref(self,name):
        if self.active == 'examples':
            self.example += r'"'

    def handle_data(self, data):
        if not self.active:
            return
        elif self.active == 'flag':
            if self.currFlag:
                stripped = data.strip()
                if stripped == 'Return value':
                    self.active=False
                    return

                if data and stripped and stripped not in ['(',')', '=', '], [']:
                    #_logger.debug("DATA", data)

                    if self.currFlag in self.flags:
                        self.addFlagData(data)
                    else:
                        self.startFlag(data)
        elif self.active == 'command':
            data = data.replace( '\r\n', ' ' )
            data = data.replace( '\n', ' ' )
            data = data.lstrip()
            data = data.strip('{}')
            data = data.replace('*', '\*') # for reStructuredText
            if '{' not in data and '}' not in data:
                self.description += data
            #_logger.debug(data)
            #self.active = False
        elif self.active == 'examples' and data != 'Python examples':
            #_logger.debug("Example\n")
            #_logger.debug(data)
            data = data.replace( '\r\n', '\n' )
            self.example += data
            #self.active = False


# class MayaDocsLoc(str) :
#    """ Path to the Maya docs, cached at pymel start """
#    __metaclass__ = util.Singleton

# TODO : cache doc location or it's evaluated for each getCmdInfo !
# MayaDocsLoc(mayaDocsLocation())

class NodeHierarchyDocParser(HTMLParser):

    def parse(self):
        docloc = mayaDocsLocation(self.version)
        if not os.path.isdir( docloc ):
            raise IOError, "Cannot find maya documentation. Expected to find it at %s" % docloc

        f = open( os.path.join( docloc , 'Nodes/index_hierarchy.html' ) )
        try:
            rawdata = f.read()
        finally:
            f.close()

        if versions.v2011 <= versions.current() < versions.v2012:
            # The maya 2011 doc doesn't parse correctly with HTMLParser - the
            # '< < <' lines get left out.  Use beautiful soup instead.
            soup = BeautifulSoup( rawdata, convertEntities='html' )
            for tag in soup.findAll(['tt', 'a']):
                # piggypack on current handle_starttag / handle_data
                self.handle_starttag(tag.name, tag.attrs)
                data = tag.string
                if data is not None:
                    self.handle_data(data)
        else:
            self.feed( rawdata )
        return self.tree

    def __init__(self, version=None):
        self.version = version
        self.currentTag = None
        self.depth = 0
        self.lastDepth = -1
        self.tree = None
        self.currentLeaves = []

        HTMLParser.__init__(self)
    def handle_starttag(self, tag, attrs):
        #_logger.debug("%s - %s" % (tag, attrs))
        self.currentTag = tag

    def handle_data(self, data):
        _logger.debug("data %r" % data)
        if self.currentTag == 'tt':
            self.depth = data.count('>')
            #_logger.debug("lastDepth: %s - depth: %s" % (self.lastDepth, self.depth))

        elif self.currentTag == 'a':
            data = data.lstrip()

            if self.depth == 0:
                if self.tree is None:
                    #_logger.debug("starting brand new tree: %s %s" % (self.depth, data))
                    self.tree = [data]
                else:
                    #_logger.debug("skipping %s", data)
                    return

            elif self.depth == self.lastDepth and self.depth > 0:
                #_logger.debug("adding to current level", self.depth, data)
                self.tree[ self.depth ].append( data )

            elif self.depth > self.lastDepth:
                #_logger.debug("starting new level: %s %s" % (self.depth, data))
                self.tree.append( [data] )

            elif self.depth < self.lastDepth:

                    for i in range(0, self.lastDepth-self.depth):
                        branch = self.tree.pop()
                        #_logger.debug("closing level %s - %s - %s" % (self.lastDepth, self.depth, self.tree[-1]))
                        currTree = self.tree[-1]
                        #if isinstance(currTree, list):
                        currTree.append( branch )
                        #else:
                        #    _logger.info("skipping", data)
                        #    self.close()
                        #    return

                    #_logger.debug("adding to level", self.depth, data)
                    self.tree[ self.depth ].append( data )
            else:
                return
            self.lastDepth = self.depth
            # with 2009 and the addition of the MPxNode, the hierarchy closes all the way out ( i.e. no  >'s )
            # this prevents the depth from getting set properly. as a workaround, we'll set it to 0 here,
            # then if we encounter '> >' we set the appropriate depth, otherwise it defaults to 0.
            self.depth = 0


def printTree( tree, depth=0 ):
    for branch in tree:
        if util.isIterable(branch):
            printTree( branch, depth+1)
        else:
            _logger.info('%s %s' % ('> '*depth,  branch))


class CommandModuleDocParser(HTMLParser):

    def parse(self):

        f = open( os.path.join( self.docloc , 'Commands/cat_' + self.category + '.html' ) )
        self.feed( f.read() )
        f.close()
        return self.cmdList

    def __init__(self, category, version=None ):
        self.cmdList = []
        self.category = category
        self.version = version

        docloc = mayaDocsLocation( '2009' if self.version=='2008' else self.version)
        self.docloc = docloc
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        try:
            attrs = attrs[0]
            #_logger.debug(attrs)
            if tag == 'a' and attrs[0]=='href':
                cmd = attrs[1].split("'")[1].split('.')[0]
                self.cmdList.append( cmd )
                #_logger.debug(cmd)
        except IndexError: return

class ApiDocParser(object):
    OBSOLETE_MSG = ['NO SCRIPT SUPPORT.', 'This method is not available in Python.']
    DEPRECATED_MSG = ['This method is obsolete.', 'Deprecated:']

    # in enums with multiple keys per int value, which (pymel) key name to use
    # as the default - ie, in MSpace, both object and preTransformed map to 2;
    # since 'object' is in PYMEL_ENUM_DEFAULTS['Space'], that is preferred
    PYMEL_ENUM_DEFAULTS = {'Space':('object',)}

    def __init__(self, apiModule, version=None, verbose=False, enumClass=tuple,
                 docLocation=None):
        self.version = versions.installName() if version is None else version
        self.apiModule = apiModule
        self.verbose = verbose
        if docLocation is None:
            docLocation = mayaDocsLocation('2009' if self.version=='2008' else self.version)
        self.docloc = docLocation
        self.enumClass = enumClass
        if not os.path.isdir(self.docloc):
            raise IOError, "Cannot find maya documentation. Expected to find it at %s" % self.docloc

        self.enums = {}
        self.pymelEnums = {}
        self.methods=util.defaultdict(list)
        self.currentMethod=None
        self.badEnums = []

    def formatMsg(self, *args):
        return self.apiClassName + '.' + self.currentMethod + ': ' + ' '.join( [ str(x) for x in args ] )

    def xprint(self, *args):
        if self.verbose:
            print self.formatMsg(*args)

    def getPymelMethodNames(self):


        setReg = re.compile('set([A-Z].*)')

        allFnMembers = self.methods.keys()
        pymelNames = {}
        pairs = {}
        pairsList = []

        def addSetGetPair(setmethod, getMethod):
            pairsList.append( (setMethod,getMethod) )
            # pair 'set' with 'is/get'
            pairs[setMethod] = getMethod
            for info in self.methods[setMethod]:
                info['inverse'] = (getMethod, True)

            # pair 'is/get' with 'set'
            pairs[getMethod] = setMethod
            for info in self.methods[getMethod]:
                info['inverse'] = (setMethod, False)

        for member in allFnMembers:
            m = setReg.match(member)
            if m:
                # MFn api naming convention usually uses setValue(), value() convention for its set and get methods, respectively
                # setSomething()  &  something()  becomes  setSomething() & getSomething()
                # setIsSomething() & isSomething() becomes setSomething() & isSomething()
                basename = m.group(1)
                origGetMethod = util.uncapitalize(basename)
                setMethod = member  # for name clarity
                if origGetMethod in allFnMembers:
                    # fix set
                    if re.match( 'is[A-Z].*', origGetMethod):
                        newSetMethod = 'set' + origGetMethod[2:] # remove 'is' #member[5:]
                        pymelNames[setMethod] = newSetMethod
                        for info in self.methods[setMethod]:
                            info['pymelName'] = newSetMethod
                        addSetGetPair( setMethod, origGetMethod)


                    # fix get
                    else:
                        newGetMethod = 'g' + setMethod[1:] # remove 's'
                        pymelNames[origGetMethod] = newGetMethod
                        for info in self.methods[origGetMethod]:
                            info['pymelName'] = newGetMethod
                        addSetGetPair( setMethod, origGetMethod)


                else:
                    getMethod = 'get' + basename
                    isMethod = 'is' + basename
                    if getMethod in allFnMembers:
                        addSetGetPair( setMethod, getMethod )
                    elif isMethod in allFnMembers:
                        addSetGetPair( setMethod, isMethod )

        return pymelNames, pairsList



    def getClassFilename(self):
        filename = 'class'
        for tok in re.split( '([A-Z][a-z]*)', self.apiClassName ):
            if tok:
                if tok[0].isupper():
                    filename += '_' + tok.lower()
                else:
                    filename += tok
        return filename

    _capitalizedRe = re.compile('([A-Z0-9][a-z0-9]*)')

    def _apiEnumNamesToPymelEnumNames(self, apiEnumNames):
        """remove all common prefixes from list of enum values"""
        if isinstance(apiEnumNames, util.Enum):
            apiEnumNames = apiEnumNames._keys.keys()
        if len(apiEnumNames) > 1:
            # We first aim to remove all similar 'camel-case-group' prefixes, ie:
            # if our enums look like:
            #    kFooBar
            #    kFooSomeThing
            #    kFooBunnies
            # we want to get Bar, SomeThing, Bunnies

            # {'kFooBar':0, 'kFooSomeThing':1}
            #     => [['k', 'Foo', 'Some', 'Thing'], ['k', 'Foo', 'Bar']]
            splitEnums = [ [ y for y in self._capitalizedRe.split( x ) if y ] for x in apiEnumNames ]

            # [['k', 'Invalid'], ['k', 'Pre', 'Transform']]
            #     => [('k', 'k'), ('Foo', 'Foo'), ('Some', 'Bar')]
            splitZip = zip( *splitEnums )
            for partList in splitZip:
                if  tuple([partList[0]]*len(partList)) == partList:
                    [ x.pop(0) for x in splitEnums ]
                else: break
            # splitEnums == [['Some', 'Thing'], ['Bar']]

            joinedEnums = [ util.uncapitalize(''.join(x), preserveAcronymns=True ) for x in splitEnums]
            for i, enum in enumerate(joinedEnums):
                if _iskeyword(enum):
                    joinedEnums[i] = enum+'_'
                    self.xprint( "bad enum", enum )
                elif enum[0].isdigit():
                    joinedEnums[i] = 'k' + enum
                    self.xprint( "bad enum", enum )

                    #print joinedEnums
                    #print enumList
                    #break

            return dict(zip(apiEnumNames, joinedEnums))
        else:
            # if only 1 name or less, name is unaltered
            return dict((name, name) for name in apiEnumNames)

    def _apiEnumToPymelEnum(self, apiEnum, apiToPymelNames=None):
        defaultsSet = self.PYMEL_ENUM_DEFAULTS.get(apiEnum.name, set())
        defaults = {}
        if apiToPymelNames is None:
            apiToPymelNames = self._apiEnumNamesToPymelEnumNames(apiEnum)
        pymelKeyDict = {}
        docs = dict(apiEnum._docs)
        for apiName, val in apiEnum._keys.iteritems():
            # want to include docs, so make dict (key, doc) => val
            pymelKeyDict[apiName] = val
            pymelName = apiToPymelNames[apiName]
            pymelKeyDict[pymelName] = val

            doc = apiEnum._docs.get(apiName)
            if doc:
                docs[pymelName] = doc

            # in the pymel dict, the pymel name should always be the default
            # key for a value... but the original dict may also have multiple
            # keys for a value... so:
            #   if there is an entry in PYMEL_ENUM_DEFAULTS for this
            #     class/pymelName, then use that as the default
            #   otherwise, use the pymel equivalent of whatever the original
            #     api default was
            if (pymelName in defaultsSet
                    # need to check val not in defaults, or else we can override
                    # a value set due to defaultsSet
                    or (val not in defaults and apiName == apiEnum.getKey(val))):
                defaults[val] = pymelName
        return util.Enum(apiEnum.name, pymelKeyDict, multiKeys=True,
                         defaultKeys=defaults)

    def handleEnums( self, type ):
        missingTypes = ['MUint64']
        otherTypes = ['void', 'char', 'uchar',
                    'double', 'double2', 'double3', 'double4',
                    'float', 'float2', 'float3', 'float4',
                    'bool',
                    'int', 'int2', 'int3', 'int4',
                    'uint', 'uint2', 'uint3', 'uint4',
                    'short', 'short2', 'short3', 'short4',
                    'long', 'long2', 'long3',
                    'MString', 'MStringArray', 'MStatus']
        notTypes = ['MCallbackId']

        if type is None: return type

        # the enum is on another class
        if '::' in type:
            type = self.enumClass( type.split( '::') )

        # the enum is on this class
        elif type in self.enums:
            type = self.enumClass( [self.apiClassName, type] )

        elif type[0].isupper() and 'Ptr' not in type and not hasattr( self.apiModule, type ) and type not in otherTypes+missingTypes+notTypes:
            type = self.enumClass( [self.apiClassName, type] )
            if type not in self.badEnums:
                self.badEnums.append(type)
                _logger.warn( "Suspected Bad Enum: %s", type )
        else:
            type = str(type)
        return type

    def handleEnumDefaults( self, default, type ):

        if default is None: return default

        if isinstance( type, self.enumClass ):

            # the enum is on another class
            if '::' in default:
                apiClass, enumConst = default.split( '::')
                assert apiClass == type[0]
            else:
                enumConst = default

            return self.enumClass([type[0], type[1], enumConst])

        return default

    def getOperatorName(self, methodName):
        op = methodName[8:]
        #print "operator", methodName, op
        if op == '=':
            methodName = None
        else:

            methodName = {
                '*=' : '__rmult__',
                '*'  : '__mul__',
                '+=' : '__radd__',
                '+'  : '__add__',
                '-=' : '__rsub__',
                '-'  : '__sub__',
                '/=' : '__rdiv__',
                '/'  : '__div__',
                '==' : '__eq__',
                '!=' : '__neq__',
                '[]' : '__getitem__'}.get( op, None )
        return methodName

    def isSetMethod(self):
        if re.match( 'set[A-Z]', self.currentMethod ):
            return True
        else:
            return False

    def isGetMethod(self):
        if re.match( 'get[A-Z]', self.currentMethod ):
            return True
        else:
            return False

    def parseTypes(self, proto):
        defaults={}
        names=[]
        types ={}
        typeQualifiers={}
        tmpTypes=[]
        # TYPES
        for paramtype in proto.findAll( 'td', **{'class':'paramtype'} ) :
            buf = []
            [ buf.extend(x.split()) for x in paramtype.findAll( text=True ) ] #if x.strip() not in ['', '*', '&', 'const', 'unsigned'] ]
            buf = [ x.strip().encode('ascii', 'ignore') for x in buf if x.strip() ]

            i=0
            for i, each in enumerate(buf):
                if each not in [ '*', '&', 'const', 'unsigned']:
                    argtype = buf.pop(i)
                    break
            else:
                # We didn't find any arg type - therefore everything
                # in buf is in the set('*', '&', 'const', 'unsigned')
                # ... so it's implicitly an unsigned int
                argtype = 'int'

            if 'unsigned' in buf and argtype in ('char','int', 'int2',
                                                 'int3', 'int4'):
                argtype = 'u' + argtype

            argtype = self.handleEnums(argtype)

            #print '\targtype', argtype, buf
            tmpTypes.append( (argtype, buf) )

        # ARGUMENT NAMES
        i = 0
        for paramname in  proto.findAll( 'td', **{'class':'paramname'} )  :
            buf = [ x.strip().encode('ascii', 'ignore') for x in paramname.findAll( text=True ) if x.strip() not in['',','] ]
            if not buf: continue
            argname = buf[0]
            data = buf[1:]

            type, qualifiers = tmpTypes[i]
            default=None
            joined = ''.join(data).strip()

            if joined:
                joined = joined.encode('ascii', 'ignore')
                # break apart into index and defaults :  '[3] = NULL'
                brackets, default = re.search( '([^=]*)(?:\s*=\s*(.*))?', joined ).groups()

                if brackets:
                    numbuf = re.split( r'\[|\]', brackets)
                    if len(numbuf) > 1:
                        # Note that these two args need to be cast differently:
                        #   int2 foo;
                        #   int bar[2];
                        # ... so, instead of storing the type of both as
                        # 'int2', we make the second one 'int__array2'
                        type = type + '__array' + numbuf[1]
                    else:
                        print "this is not a bracketed number", repr(brackets), joined

                if default is not None:
                    try:
                        # Constants
                        default = {
                            'true' : True,
                            'false': False,
                            'NULL' : None
                        }[default]
                    except KeyError:
                        try:
                            if type in ['int', 'uint','long', 'uchar']:
                                default = int(default)
                            elif type in ['float', 'double']:
                                # '1.0 / 24.0'
                                if '/' in default:
                                    default = eval(default)
                                # '1.0e-5F'  --> '1.0e-5'
                                elif default.endswith('F'):
                                    default = float(default[:-1])
                                else:
                                    default = float(default)
                            else:
                                default = self.handleEnumDefaults(default, type)
                        except ValueError:
                            default = self.handleEnumDefaults(default, type)
                    # default must be set here, because 'NULL' may be set to back to None, but this is in fact the value we want
                    self.xprint('DEFAULT', default)
                    defaults[argname] = default

            types[argname] = type
            typeQualifiers[argname] = qualifiers
            names.append(argname)
            i+=1
        assert sorted(names) == sorted(types.keys()), 'name-type mismatch %s %s' %  (sorted(names), sorted(types.keys()) )
        return names, types, typeQualifiers, defaults

    def parseEnums(self, proto):
        enumValues={}
        enumDocs={}
        for em in proto.findNextSiblings( 'div', limit=1)[0].findAll( 'em'):
            enumKey = str(em.contents[-1])
            try:
                enumVal = getattr(self.apiClass, enumKey)
            except:
                _logger.warn( "%s.%s of enum %s does not exist" % ( self.apiClassName, enumKey, self.currentMethod))
                enumVal = None
            enumValues[ enumKey ] = enumVal
            # TODO:
            # do we want to feed the docstrings to the Enum object itself
            # (which seems to have support for docstrings)? Currently, we're
            # not...
            docItem = em.next.next.next.next.next

            if isinstance( docItem, NavigableString ):
                enumDocs[enumKey] = str(docItem).strip()
            else:
                enumDocs[enumKey] = str(docItem.contents[0]).strip()

        apiEnum = util.Enum(self.currentMethod, enumValues, multiKeys=True)
        apiToPymelNames = self._apiEnumNamesToPymelEnumNames(apiEnum)
        pymelEnum = self._apiEnumToPymelEnum(apiEnum,
                                             apiToPymelNames=apiToPymelNames)
        for apiName, pymelName in apiToPymelNames.iteritems():
            apiDoc = enumDocs.get(apiName)
            if apiDoc is not None:
                enumDocs[pymelName] = apiDoc

        enumInfo = {'values' : apiEnum,
                    'valueDocs' : enumDocs,

                      #'doc' : methodDoc
                    }
        return enumInfo, pymelEnum

    def isObsolete(self, proto):
        # ARGUMENT DIRECTION AND DOCUMENTATION
        addendum = proto.findNextSiblings( 'div', limit=1)[0]
        #try: self.xprint( addendum.findAll(text=True ) )
        #except: pass

        #if addendum.findAll( text = re.compile( '(This method is obsolete.)|(Deprecated:)') ):

        if addendum.findAll( text=lambda x: x in self.OBSOLETE_MSG ):
            self.xprint( "OBSOLETE" )
            self.currentMethod = None
            return True
        return False

    def parseMethodArgs(self, proto, returnType, names, types, typeQualifiers):
        directions={}
        docs={}
        deprecated = False
        returnDoc = ''

        addendum = proto.findNextSiblings( 'div', limit=1)[0]
        #if self.currentMethod == 'createColorSet': raise NotImplementedError
        if addendum.findAll( text=lambda x: x in self.DEPRECATED_MSG ):
            self.xprint( "DEPRECATED" )
            #print self.apiClassName + '.' + self.currentMethod + ':' + ' DEPRECATED'
            deprecated = True


        methodDoc = ' '.join( addendum.p.findAll( text=True ) ).encode('ascii', 'ignore')

        tmpDirs = []
        tmpNames = []
        tmpDocs = []

        #extraInfo = addendum.dl.table
        if self.version and int(self.version.split('-')[0]) < 2013:
            extraInfos = addendum.findAll('table')
        else:
            #extraInfos = addendum.findAll(lambda tag: tag.name == 'table' and ('class', 'params') in tag.attrs)
            extraInfos = addendum.findAll(lambda tag: tag.name == 'dl' and ('class', 'return') not in tag.attrs and ('class', 'user') not in tag.attrs)
        if extraInfos:
            #print "NUMBER OF TABLES", len(extraInfos)
            if self.version and int(self.version.split('-')[0]) < 2013:
                extraInfo = extraInfos[0]
                tmpDirs += extraInfo.findAll( text=lambda text: text in ['[in]', '[out]'] )
                #tmpNames += [ em.findAll( text=True, limit=1 )[0] for em in extraInfo.findAll( 'em') ]
                for tr in extraInfo.findAll( 'tr'):
                    assert tr, "could not find name tr"
                    td = tr.findNext(lambda tag: tag.name == 'td' and ('class', 'paramname') in tag.attrs)
                    assert td, "could not find name t"
                    name = td.findAll( text=True, limit=1 )[0]
                    tmpNames.append(name)
                tds = extraInfo.findAll( lambda tag: tag.name == 'td' and not any([item for item in tag.attrs if 'class' in item]) )
                for doc in [td.findAll( text=lambda text: text.strip(), recursive=False) for td in tds]:
                    tmpDocs.append( ''.join(doc) )
                if not tmpDocs:
                    tmpDocs = [''] * len(tmpDirs)
            else:
                for extraInfo in extraInfos:
                    for tr in extraInfo.findAll( 'tr'):
                        assert tr, "could not find name tr"
                        tds = tr.findAll(lambda tag: tag.name == 'td')
                        assert tds, "could not find name td"
                        assert len(tds) == 3, "td list is unexpected length: %d" % len(tds)

                        tt = tds[0].findNext(lambda tag: tag.name == 'tt')
                        dir = tt.findAll( text=True, limit=1 )[0]
                        tmpDirs.append(dir.encode('ascii', 'ignore'))

                        name = tds[1].findAll( text=True, limit=1 )[0]
                        tmpNames.append(name.encode('ascii', 'ignore'))

                        doc = ''.join(tds[2].findAll( text=True))
                        tmpDocs.append(doc.encode('ascii', 'ignore'))

#                print "here2"
#                for tr in extraInfo.findAll( 'tr'):
#                    assert tr, "could not find name tr"
#                    tdName = tr.findNext(lambda tag: tag.name == 'td' and ('class', 'paramname') in tag.attrs)
#                    assert tdName, "could not find name td"
#                    name = tdName.findAll( text=True, limit=1 )[0]
#                    tmpNames.append(name)
#
#                    tdDir = tr.findNext(lambda tag: tag.name == 'td' and ('class', 'paramdir') in tag.attrs)
#                    assert tdDir, "could not find direction td"
#                    name = tdDir.findAll( text=True, limit=1 )[0]
#                    tmpDirs.append(name)

#                            for td in extraInfo.findAll( 'td' ):
#                                assert td, "could not find doc td"
#                                for doc in td.findAll( text=lambda text: text.strip(), recursive=False) :
#                                    if doc: tmpDocs.append( ''.join(doc) )

            assert len(tmpDirs) == len(tmpNames) == len(tmpDocs), \
                'names, types, and docs are of unequal lengths: %s vs. %s vs. %s' % (tmpDirs, tmpNames, tmpDocs)
            assert sorted(tmpNames) == sorted(typeQualifiers.keys()), 'name-typeQualifiers mismatch %s %s' %  (sorted(tmpNames), sorted(typeQualifiers.keys()) )
            #self.xprint(  sorted(tmpNames), sorted(typeQualifiers.keys()), sorted(typeQualifiers.keys()) )

            for name, dir, doc in zip(tmpNames, tmpDirs, tmpDocs) :
                if dir == '[in]':
                    # attempt to correct bad in/out docs
                    if re.search(r'\b([fF]ill|[sS]tor(age)|(ing))|([rR]esult)', doc ):
                        _logger.warn( "%s.%s(%s): Correcting suspected output argument '%s' based on doc '%s'" % (
                                                            self.apiClassName,self.currentMethod,', '.join(names), name, doc))
                        dir = 'out'
                    elif not re.match( 'set[A-Z]', self.currentMethod) and '&' in typeQualifiers[name] and types[name] in ['int', 'double', 'float', 'uint', 'uchar']:
                        _logger.warn( "%s.%s(%s): Correcting suspected output argument '%s' based on reference type '%s &' ('%s')'" % (
                                                            self.apiClassName,self.currentMethod,', '.join(names), name, types[name], doc))
                        dir = 'out'
                    else:
                        dir = 'in'
                elif dir == '[out]':
                    if types[name] == 'MAnimCurveChange':
                        _logger.warn( "%s.%s(%s): Setting MAnimCurveChange argument '%s' to an input arg (instead of output)" % (
                                                            self.apiClassName,self.currentMethod,', '.join(names), name))
                        dir = 'in'
                    else:
                        dir = 'out'
                elif dir == '[in,out]':
                    # it makes the most sense to treat these types as inputs
                    dir = 'in'
                else:
                    raise ValueError("direction must be either '[in]', '[out]', or '[in,out]'. got %r" % dir)

                assert name in names
                directions[name] = dir
                docs[name] = doc.replace('\n\r', ' ').replace('\n', ' ')


            # Documentation for Return Values
            if returnType:
                try:
                    returnDocBuf = addendum.findAll( 'dl', limit=1, **{'class':'return'} )[0].findAll( text=True )
                except IndexError:
                    pass
                else:
                    if returnDocBuf:
                        returnDoc = ''.join( returnDocBuf[1:] ).replace('\n\r', ' ').replace('\n', ' ').encode('ascii', 'ignore')
                    self.xprint(  'RETURN_DOC', repr(returnDoc)  )
        #assert len(names) == len(directions), "name lenght mismatch: %s %s" % (sorted(names), sorted(directions.keys()))
        return directions, docs, methodDoc, returnDoc, deprecated

    def getMethodNameAndOutput(self, proto):
        # NAME AND RETURN TYPE
        memb = proto.findAll( 'td', **{'class':'memname'} )[0]
        buf = [ x.strip().encode('ascii', 'ignore') for x in memb.findAll( text=True )]
        if len(buf) ==1:
            buf = [ x for x in buf[0].split() if x not in ['const', 'unsigned'] ]
            if len(buf)==1:
                returnType = None
                methodName = buf[0]
            else:
                returnType = ''.join(buf[:-1])
                methodName = buf[-1]
        else:
            returnType = buf[0]
            methodName = buf[1]
            buf = [ x for x in buf[0].split() if x not in ['const', 'unsigned'] ]
            if len(buf) > 1:
                returnType += buf[0]
                methodName = buf[1]

        methodName = methodName.split('::')[-1]

        # convert operators to python special methods
        if methodName.startswith('operator'):
            methodName = self.getOperatorName(methodName)
        else:
            #constructors and destructors
            if methodName.startswith('~') or methodName == self.apiClassName:
                methodName = None
        # no MStatus in python
        if returnType in ['MStatus', 'void']:
            returnType = None
        else:
            returnType = self.handleEnums(returnType)

        return methodName, returnType

    def iterProto(self, apiClassName):
        self.apiClassName = apiClassName
        self.apiClass = getattr(self.apiModule, self.apiClassName)
        self.docfile = self.getClassPath()

        _logger.info( "parsing file %s" , self.docfile )

        f = open( self.docfile )
        soup = BeautifulSoup( f.read(), convertEntities='html' )
        f.close()

        for proto in soup.body.findAll( 'div', **{'class':'memproto'} ):
            yield proto

    def getClassPath(self):
        filename = self.getClassFilename() + '.html'
        apiBase = os.path.join(self.docloc , 'API')
        path = os.path.join(apiBase, filename)
        if not os.path.isfile(path):
            path = os.path.join(apiBase, 'cpp_ref', filename)
        return path

    def parse(self, apiClassName):

        self.enums = {}
        self.pymelEnums = {}
        self.methods=util.defaultdict(list)
        self.currentMethod=None
        self.badEnums = []

        for proto in self.iterProto(apiClassName):

            methodName, returnType = self.getMethodNameAndOutput(proto)
            if methodName is None: continue
            # convert to unicode
            self.currentMethod = str(methodName)
            if self.currentMethod == 'void(*':
                continue
            # ENUMS
            if returnType == 'enum':
                self.xprint( "ENUM", returnType)
                #print returnType, methodName
                try:
                    #print enumList
                    enumData = self.parseEnums(proto)
                    self.enums[self.currentMethod] = enumData[0]
                    self.pymelEnums[self.currentMethod] = enumData[1]

                except AttributeError, msg:
                    _logger.error("FAILED ENUM: %s", msg)
                    import traceback
                    _logger.debug(traceback.format_exc())

            # ARGUMENTS
            else:
                self.xprint( "RETURN", returnType)

                # Static methods
                static = False
                try:
                    res = proto.findAll('code')
                    if res:
                        code = res[-1].string
                        if code and code.strip() == '[static]':
                            static = True
                except IndexError: pass

                if self.isObsolete(proto):
                    continue

                names, types, typeQualifiers, defaults = self.parseTypes(proto)

                try:
                    directions, docs, methodDoc, returnDoc, deprecated = self.parseMethodArgs(proto, returnType, names, types, typeQualifiers)
                except AssertionError, msg:
                    _logger.error(self.formatMsg("FAILED", str(msg)))
                    continue
                except AttributeError:
                    import traceback
                    _logger.error(self.formatMsg(traceback.format_exc()))
                    continue
                    #pass

#                print "names", names
#                print "types", types
#                print "defaults", defaults
#                print "directions", directions
#                print docs

                argInfo={}
                argList=[]
                inArgs=[]
                outArgs=[]

                for argname in names[:] :
                    type = types[argname]
                    if argname not in directions:
                        self.xprint("Warning: assuming direction is 'in'")
                        directions[argname] = 'in'
                    direction = directions[argname]
                    doc = docs.get( argname, '')

                    if type == 'MStatus':
                        types.pop(argname)
                        defaults.pop(argname,None)
                        directions.pop(argname,None)
                        docs.pop(argname,None)
                        idx = names.index(argname)
                        names.pop(idx)
                    else:
                        if direction == 'in':
                            inArgs.append(argname)
                        else:
                            outArgs.append(argname)
                        argInfo[ argname ] = {'type': type, 'doc': doc }

                # correct bad outputs
                if self.isGetMethod() and not returnType and not outArgs:
                    for argname in names:
                        if '&' in typeQualifiers[argname]:
                            doc = docs.get(argname, '')
                            directions[argname] = 'out'
                            idx = inArgs.index(argname)
                            inArgs.pop(idx)
                            outArgs.append(argname)

                            _logger.warn( "%s.%s(%s): Correcting suspected output argument '%s' because there are no outputs and the method is prefixed with 'get' ('%s')" % (
                                                                           self.apiClassName,self.currentMethod, ', '.join(names), argname, doc))

                # now that the directions are correct, make the argList
                for argname in names:
                    type = types[argname]
                    self.xprint( "DIRECTIONS", directions )
                    direction = directions[argname]
                    data = ( argname, type, direction)
                    self.xprint( "ARG", data )
                    argList.append(  data )

                methodInfo = { 'argInfo': argInfo,
                              'returnInfo' : { 'type' : returnType, 'doc' : returnDoc },
                              'args' : argList,
                              'returnType' : returnType,
                              'inArgs' : inArgs,
                              'outArgs' : outArgs,
                              'doc' : methodDoc,
                              'defaults' : defaults,
                              #'directions' : directions,
                              'types' : types,
                              'static' : static,
                              'typeQualifiers' : typeQualifiers,
                              'deprecated' : deprecated }
                self.methods[self.currentMethod].append(methodInfo)

                # reset
                self.currentMethod=None

        pymelNames, invertibles = self.getPymelMethodNames()


        return { 'methods' : dict(self.methods),
                 'enums' : self.enums,
                 'pymelEnums' : self.pymelEnums,
                 'pymelMethods' :  pymelNames,
                 'invertibles' : invertibles
                }
