""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here

import pymel.mayahook as mayahook
_logger = mayahook.getLogger(__name__)

from allapi import *

#import pymel.factories as _factories

import sys, inspect, timeit, time, re
from pymel.util import Singleton, metaStatic, expandArgs, Tree, FrozenTree, IndexedFrozenTree, treeFromDict, warn
from pymel.mayahook import ExecutionWarning
import pymel.util as util
import pickle, os.path
#import pymel.mayahook as mayahook
from HTMLParser import HTMLParser
try:
    from pymel.util.external.BeautifulSoup import BeautifulSoup, NavigableString
except ImportError:
    from BeautifulSoup import BeautifulSoup, NavigableString

from keyword import iskeyword as _iskeyword


VERBOSE = 0

# TODO : would need this shared as a Singleton class, but importing from pymel.mayahook.factories anywhere 
# except form core seems to be a problem
#from pymel.mayahook.factories import NodeHierarchy

_thisModule = sys.modules[__name__]
#_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

#Enum = util.namedtuple( 'Enum', ['parent', 'enum'] )

class Enum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )
    def __repr__(self): return repr(str(self))
    def pymelName(self, forceType=None):
        parts = list(self)
        if forceType:
            parts[0] = forceType
        else:
            mfn = getattr( _thisModule, self[0] )
            mayaTypeDict = ApiEnumsToMayaTypes()[ mfn().type() ]
            parts[0] = util.capitalize( mayaTypeDict.keys()[0] )

        return '.'.join( [str(x) for x in parts] )

class ApiDocParser(object):
    OBSOLETE_MSG = ['NO SCRIPT SUPPORT.', 'This method is not available in Python.']
    DEPRECATED_MSG = ['This method is obsolete.', 'Deprecated:']
    def __init__(self, version=None, verbose=False):

        self.verbose = verbose
        self.docloc = mayahook.mayaDocsLocation(version)
        if not os.path.isdir(self.docloc):
            docloc09 = mayahook.mayaDocsLocation('2009')
            if not os.path.isdir(self.docloc):
                raise IOError, "Cannot find maya documentation. Expected to find it at %s" % self.docloc

            _logger.warn( "could not find maya documentation for this version of Maya. Using 2009 documentation" )
            self.docloc = docloc09
        
    def xprint(self, *args): 
        if self.verbose or VERBOSE:
            print self.apiClassName + '.' + self.currentMethod + ':', ' '.join( [ str(x) for x in args ] ) 
           
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
    
    def getPymelEnums(self, enumDict):
        """remove all common prefixes from list of enum values"""
        if len(enumDict) > 1:
            enumList = enumDict.keys()
            splitEnums = [ [ y for y in re.split( '([A-Z0-9][a-z0-9]*)', x ) if y ] for x in enumList ]
            splitEnumsCopy = splitEnums[:]
            for partList in zip( *splitEnumsCopy ):
                if  tuple([partList[0]]*len(partList)) == partList:
                    [ x.pop(0) for x in splitEnums ]
                else: break
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
            
            pymelEnumDict = dict( [ (k2,enumDict[k1]) for k1, k2 in zip( enumList, joinedEnums ) ] )
                
            #print "enums", joinedEnums
            return pymelEnumDict
        
        return enumDict
                           
    def handleEnums( self, type ):
        missingTypes = ['MUint64']
        otherTypes = ['void', 'char',
                    'double', 'double2', 'double3', 'double4',
                    'float', 'float2', 'float3', 'float4',
                    'bool',
                    'int', 'int2', 'int3', 'int4', 'uint',
                    'short', 'short2', 'short3', 'short4',
                    'long', 'long2', 'long3',
                    'MString', 'MStringArray']
        notTypes = ['MCallbackId']
        
        if type is None: return type
        
        # the enum is on another class
        if '::' in type:
            type = Enum( type.split( '::') )
            
        # the enum is on this class
        elif type in self.enums:
            type = Enum( [self.apiClassName, type] )
            
        elif type[0].isupper() and 'Ptr' not in type and not hasattr( _thisModule, type ) and type not in otherTypes+missingTypes+notTypes:
            type = Enum( [self.apiClassName, type] )
            if type not in self.badEnums:
                self.badEnums.append(type)
                _logger.warn( "Suspected Bad Enum: %s", type )
        else:
            type = str(type)
        return type
    
    def handleEnumDefaults( self, default, type ):

        if default is None: return default
        
        if isinstance( type, Enum ):
            
            # the enum is on another class
            if '::' in default:
                apiClass, enumConst = default.split( '::')
                assert apiClass == type[0]
            else:
                enumConst = default
                  
            return Enum([type[0], type[1], enumConst])
                
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
                                
    def parse(self, apiClassName):

        self.enums = {}
        self.pymelEnums = {}
        self.methods=util.defaultdict(list)
        self.currentMethod=None
        self.badEnums = []
        
        self.apiClassName = apiClassName          
        self.apiClass = getattr(_thisModule, self.apiClassName)
        
        
        self.docfile = os.path.join( self.docloc , 'API', self.getClassFilename() + '.html' )

        _logger.info( "parsing file %s" , self.docfile )
        
        f = open( self.docfile )
    
        soup = BeautifulSoup( f.read(), convertEntities='html' )
        f.close()
          

        for proto in soup.body.findAll( 'div', **{'class':'memproto'} ): 

            returnDoc = ''
            
            # NAME AND RETURN TYPE
            memb = proto.findAll( 'td', **{'class':'memname'} )[0]
            buf = [ x.strip() for x in memb.findAll( text=True )]
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
                
                if methodName is None: continue
            
            # no MStatus in python
            if returnType in ['MStatus', 'void']:
                returnType = None
            else:
                returnType = self.handleEnums(returnType)
            
            # convert to unicode
            self.currentMethod = str(methodName)
            
            #constructors and destructors
            if self.currentMethod.startswith('~') or self.currentMethod == self.apiClassName:
                continue
            
            # ENUMS
            if returnType == 'enum':
                self.xprint( "ENUM", returnType)
                #print returnType, methodName    
                try:
                    enumValues={}
                    enumDocs={}
                    for em in proto.findNextSiblings( 'div', limit=1)[0].findAll( 'em'):
                        enumKey = str(em.contents[-1])
                        try:
                            enumVal = getattr(self.apiClass, enumKey)
                        except:
                            warn( "%s.%s of enum %s does not exist" % ( self.apiClassName, enumKey, self.currentMethod), ExecutionWarning)
                            enumVal = None
                        enumValues[ enumKey ] = enumVal
                        
                        docItem = em.next.next.next.next.next
                        
                        if isinstance( docItem, NavigableString ):
                            enumDocs[enumKey] = str(docItem).strip()
                        else:
                            enumDocs[enumKey] = str(docItem.contents[0]).strip()
    
                    #self.enums[self.currentMethod] = dict( [ (x,i) for i, x in enumerate(enumList) ] )
                    #self.pymelEnums[self.currentMethod] = dict( [ (x,i) for i, x in enumerate(pymelEnumList) ] )      
                    pymelEnumList = self.getPymelEnums( enumValues )
                    for val, pyval in zip(enumValues,pymelEnumList):
                        enumDocs[pyval] = enumDocs[val]
                    
                    enumInfo = {'values' : util.Enum(self.currentMethod, enumValues), 
                                'valueDocs' : enumDocs,
                                  
                                  #'doc' : methodDoc
                                } 
                    
                    #print enumList
                    
                    self.enums[self.currentMethod] = enumInfo
                    self.pymelEnums[self.currentMethod] = util.Enum(self.currentMethod, pymelEnumList)
                    
                except AttributeError, msg:
                    _logger.error( "FAILED ENUM: %s", msg )
                    
            # ARGUMENTS
            else:
                self.xprint( "RETURN", returnType)
                
                argInfo={}
                argList=[]
                defaults={}
                names=[]
                directions={}
                docs={}
                inArgs=[]
                outArgs=[]
                types ={}
                typeQualifiers={}
                methodDoc = ''
                deprecated = False
                
                # Static methods
                static = False
                try:
                    code = proto.findAll('code')[-1].string
                    if code and code.strip() == '[static]': 
                        static = True
                except IndexError: pass    
                
                tmpTypes=[]
                # TYPES
                for paramtype in proto.findAll( 'td', **{'class':'paramtype'} ) :
                    buf = []
                    [ buf.extend(x.split()) for x in paramtype.findAll( text=True ) ] #if x.strip() not in ['', '*', '&', 'const', 'unsigned'] ]
                    buf = [ str(x.strip()) for x in buf if x.strip() ]

                    i=0
                    for i, each in enumerate(buf):
                        if each not in [ '*', '&', 'const', 'unsigned']:
                            break
                    argtype = buf.pop(i)
                    
                    argtype = self.handleEnums(argtype)
                    
                    #print '\targtype', argtype, buf
                    tmpTypes.append( (argtype, buf) )
                
                # ARGUMENT NAMES 
                i = 0
                for paramname in  proto.findAll( 'td', **{'class':'paramname'} )  :
                    buf = [ x.strip() for x in paramname.findAll( text=True ) if x.strip() not in['',','] ]
                    if buf:
                        argname = buf[0]
                        data = buf[1:]
                        
                        type, qualifiers = tmpTypes[i]
                        default=None
                        joined = ''.join(data).strip()
                        
                        if joined:
                            # break apart into index and defaults :  '[3] = NULL'
                            brackets, default = re.search( '([^=]*)(?:\s*=\s*(.*))?', joined ).groups()
                            
                            if brackets:                         
                                numbuf = re.split( r'\[|\]', brackets)
                                if len(numbuf) > 1:
                                    type = type + numbuf[1]
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
                                        if type in ['int', 'uint','long']:
                                            default = int(default)
                                        elif type in ['float', 'double']:
                                            # '1.0 / 24.0'
                                            if '/' in default:
                                                default = eval(default.encode('ascii', 'ignore'))
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
                        
                try:
                    # ARGUMENT DIRECTION AND DOCUMENTATION
                    addendum = proto.findNextSiblings( 'div', limit=1)[0]
                    #try: self.xprint( addendum.findAll(text=True ) )
                    #except: pass
                    
                    #if addendum.findAll( text = re.compile( '(This method is obsolete.)|(Deprecated:)') ):
                    
                    if addendum.findAll( text=lambda x: x in self.OBSOLETE_MSG ):
                        self.xprint( "OBSOLETE" )
                        self.currentMethod = None
                        continue
                    
                    #if self.currentMethod == 'createColorSet': raise NotImplementedError
                    if addendum.findAll( text=lambda x: x in self.DEPRECATED_MSG ):
                        self.xprint( "DEPRECATED" )
                        #print self.apiClassName + '.' + self.currentMethod + ':' + ' DEPRECATED'
                        deprecated = True
                    
                    
                    methodDoc = ' '.join( addendum.p.findAll( text=True ) )
                    
                    tmpDirs = []
                    tmpNames = []
                    tmpDocs = []
                    
                    #extraInfo = addendum.dl.table
                    extraInfos = addendum.findAll('table')
                    
                    if extraInfos:
                        #print "NUMBER OF TABLES", len(extraInfos)
                        for extraInfo in extraInfos:
                            tmpDirs += extraInfo.findAll( text=lambda text: text in ['[in]', '[out]'] )
            
                            #tmpNames += [ em.findAll( text=True, limit=1 )[0] for em in extraInfo.findAll( 'em') ]
                            tmpNames = []
                            for tr in extraInfo.findAll( 'tr'):
                                assert tr, "could not find name tr"
                                em = tr.findNext( 'em' )
                                assert tr, "could not find name em"
                                name = em.findAll( text=True, limit=1 )[0]
                                tmpNames.append(name)
                            
#                            for td in extraInfo.findAll( 'td' ):
#                                assert td, "could not find doc td"
#                                for doc in td.findAll( text=lambda text: text.strip(), recursive=False) :
#                                    if doc: tmpDocs.append( ''.join(doc) )
                                    
                            for doc in [td.findAll( text=lambda text: text.strip(), recursive=False) for td in extraInfo.findAll( 'td' )]:
                                if doc: tmpDocs.append( ''.join(doc) )
                            
                                  
                        assert len(tmpDirs) == len(tmpNames) == len(tmpDocs), 'names and types lists are of unequal lengths: %s vs. %s vs. %s' % (tmpDirs, tmpNames, tmpDocs) 
                        assert sorted(tmpNames) == sorted(typeQualifiers.keys()), 'name list mismatch %s %s' %  (sorted(tmpNames), sorted(typeQualifiers.keys()) )
                        
                        #self.xprint(  sorted(tmpNames), sorted(typeQualifiers.keys()), sorted(typeQualifiers.keys()) )
                        
                        for name, dir, doc in zip(tmpNames, tmpDirs, tmpDocs) :
                            if dir == '[in]': 
                                # attempt to correct bad in/out docs
                                if re.search(r'\b([fF]ill|[sS]tor(age)|(ing))|([rR]esult)', doc ):
                                    warn( "%s.%s(%s): Correcting suspected output argument '%s' based on doc '%s'" % (
                                                                        self.apiClassName,self.currentMethod,', '.join(names), name, doc), ExecutionWarning)
                                    dir = 'out'
                                elif not re.match( 'set[A-Z]', self.currentMethod) and '&' in typeQualifiers[name] and types[name] in ['int', 'double', 'float']:
                                    warn( "%s.%s(%s): Correcting suspected output argument '%s' based on reference type '%s &' ('%s')'" % (
                                                                        self.apiClassName,self.currentMethod,', '.join(names), name, types[name], doc), ExecutionWarning)                                                                                        
                                    dir = 'out'
                                else:
                                    dir = 'in'
                            elif dir == '[out]': 
                                dir = 'out'
                            else: raise
                            
                            assert name in names
                            directions[name] = dir
                            docs[name] = doc
                        
                        
                        # Documentation for Return Values
                        if returnType:
                            try:   
                                returnDocBuf = addendum.findAll( 'dl', limit=1, **{'class':'return'} )[0].findAll( text=True )
                            except IndexError:
                                pass
                            else:
                                if returnDocBuf:
                                    returnDoc = ''.join( returnDocBuf[1:] ).strip('\n')
                                self.xprint(  'RETURN_DOC', repr(returnDoc)  )         

                        
                except (AttributeError, AssertionError), msg:
                    self.xprint( "FAILED", str(msg) )
                    pass

                 
#                print names
#                print types
#                print defaults
#                print directions
#                print docs

                for argname in names[:] :
                    type = types[argname]
                    direction = directions.get(argname, 'in')
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

                            warn( "%s.%s(%s): Correcting suspected output argument '%s' because there are no outputs and the method is prefixed with 'get' ('%s')" % (               
                                                                           self.apiClassName,self.currentMethod, ', '.join(names), argname, doc), ExecutionWarning) 
                
                # now that the directions are correct, make the argList
                for argname in names:
                    type = types[argname]
                    direction = directions.get(argname, 'in')
                    data = ( argname, type, direction)
                    if self.verbose: self.xprint( "ARG", data )       
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

                          
# fast convenience tests on API objects
def isValidMObjectHandle (obj):
    if isinstance(obj, MObjectHandle) :
        return obj.isValid() and obj.isAlive()
    else :
        return False

def isValidMObject (obj):
    if isinstance(obj, MObject) :
        return not obj.isNull()
    else :
        return False
    
def isValidMPlug (obj):
    if isinstance(obj, MPlug) :
        return not obj.isNull()
    else :
        return False

def isValidMDagPath (obj):
    if isinstance(obj, MDagPath) : 
        # when the underlying MObject is no longer valid, dag.isValid() will still return true,
        # but obj.fullPathName() will be an empty string
        return obj.isValid() and obj.fullPathName() 
    else :
        return False

def isValidMNode (obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDependencyNode)
    else :
        return False

def isValidMDagNode (obj):
    if isValidMObject(obj) :
        return obj.hasFn(MFn.kDagNode)
    else :
        return False
    
def isValidMNodeOrPlug (obj):
    return isValidMPlug (obj) or isValidMNode (obj)

# Maya static info :
# Initializes various static look-ups to speed up Maya types conversions



class ApiTypesToApiEnums(dict) :
    """Lookup of Maya API types to corresponding MFn::Types enum"""
    __metaclass__ = Singleton   
class ApiEnumsToApiTypes(dict) :
    """Lookup of MFn::Types enum to corresponding Maya API types"""
    __metaclass__ = Singleton
class ApiTypesToApiClasses(dict) :
    """Lookup of Maya API types to corresponding MFnBase Function sets"""
    __metaclass__ = Singleton
    
# Reserved Maya types and API types that need a special treatment (abstract types)
# TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
# strangely createNode ('cluster') works but dgMod.createNode('cluster') doesn't

# added : filters them to weed out those not present in current version

#class ReservedMayaTypes(dict) :
#    __metaclass__ =  metaStatic
## Inverse lookup
#class ReservedApiTypes(dict) :
#   

class ReservedMayaTypes(dict) :
    __metaclass__ = Singleton
class ReservedApiTypes(dict) :
    __metaclass__ = Singleton
    
def _buildMayaReservedTypes():
    """ Build a list of Maya reserved types.
        These cannot be created directly from the API, thus the dgMod trick to find the corresonding Maya type won't work """

    ReservedMayaTypes().clear()
    ReservedApiTypes().clear()
    
    reservedTypes = { 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
                'entity':'kDependencyNode', \
                'constraint':'kConstraint', 'field':'kField', \
                'geometryShape':'kGeometric', 'shape':'kShape', 'deformFunc':'kDeformFunc', 'cluster':'kClusterFilter', \
                'dimensionShape':'kDimension', \
                'abstractBaseCreate':'kCreate', 'polyCreator':'kPolyCreator', \
                'polyModifier':'kMidModifier', 'subdModifier':'kSubdModifier', \
                'curveInfo':'kCurveInfo', 'curveFromSurface':'kCurveFromSurface', \
                'surfaceShape': 'kSurface', 'revolvedPrimitive':'kRevolvedPrimitive', 'plane':'kPlane', 'curveShape':'kCurve', \
                'animCurve': 'kAnimCurve', 'resultCurve':'kResultCurve', 'cacheBase':'kCacheBase', 'filter':'kFilter',
                'blend':'kBlend', 'ikSolver':'kIkSolver', \
                'light':'kLight', 'renderLight':'kLight', 'nonAmbientLightShapeNode':'kNonAmbientLight', 'nonExtendedLightShapeNode':'kNonExtendedLight', \
                'texture2d':'kTexture2d', 'texture3d':'kTexture3d', 'textureEnv':'kTextureEnv', \
                'primitive':'kPrimitive', 'reflect':'kReflect', 'smear':'kSmear', \
                'plugin':'kPlugin', 'THdependNode':'kPluginDependNode', 'THlocatorShape':'kPluginLocatorNode', 'pluginData':'kPluginData', \
                'THdeformer':'kPluginDeformerNode', 'pluginConstraint':'kPluginConstraintNode', \
                'unknown':'kUnknown', 'unknownDag':'kUnknownDag', 'unknownTransform':'kUnknownTransform',\
                'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip', # creating these 2 crash Maya 
                'dynBase': 'kDynBase', 'polyPrimitive': 'kPolyPrimitive','nParticle': 'kNParticle', 'birailSrf': 'kBirailSrf', 'pfxGeometry': 'kPfxGeometry', } # Reserved types that crash when            

    # filter to make sure all these types exist in current version (some are Maya2008 only)
    ReservedMayaTypes ( dict( (item[0], item[1]) for item in filter(lambda i:i[1] in ApiTypesToApiEnums(), reservedTypes.iteritems()) ) )
    # build reverse dict
    ReservedApiTypes ( dict( (item[1], item[0]) for item in ReservedMayaTypes().iteritems() ) )
    
    return ReservedMayaTypes(), ReservedApiTypes()

# some handy aliases / shortcuts easier to remember and use than actual Maya type name
class ShortMayaTypes(dict) :
    __metaclass__ =  metaStatic
    
ShortMayaTypes({'all':'base', 'valid':'base', 'any':'base', 'node':'dependNode', 'dag':'dagNode', \
                'deformer':'geometryFilter', 'weightedDeformer':'weightGeometryFilter', 'geometry':'geometryShape', \
                'surface':'surfaceShape', 'revolved':'revolvedPrimitive', 'deformable':'deformableShape', \
                'curve':'curveShape' })                
                   
class MayaTypesToApiTypes(dict) :
    """ Lookup of currently existing Maya types as keys with their corresponding API type as values.
    Not a read only (static) dict as these can change (if you load a plugin)"""
    __metaclass__ = Singleton

class ApiTypesToMayaTypes(dict) :
    """ Lookup of currently existing Maya API types as keys with their corresponding Maya type as values.
    Not a read only (static) dict as these can change (if you load a plugin)
    In the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )"""
    __metaclass__ = Singleton
    
#: lookup tables for a direct conversion between Maya type to their MFn::Types enum
class MayaTypesToApiEnums(dict) :
    """Lookup from Maya types to API MFn::Types enums """
    __metaclass__ = Singleton
    
#: lookup tables for a direct conversion between API type to their MFn::Types enum 
class ApiEnumsToMayaTypes(dict) :
    """Lookup from API MFn::Types enums to Maya types """
    __metaclass__ = Singleton
 
# Cache API types hierarchy, using MFn classes hierarchy and additionnal trials
# TODO : do the same for Maya types, but no clue how to inspect them apart from parsing docs


#: Reserved API type hierarchy, for virtual types where we can not use the 'create trick'
#: to query inheritance, as of 2008 types and API types seem a bit out of sync as API types
#: didn't follow latest Maya types additions...
class ReservedApiHierarchy(dict) :
    __metaclass__ =  metaStatic
ReservedApiHierarchy({ 'kNamedObject':'kBase', 'kDependencyNode':'kNamedObject', 'kDagNode':'kDependencyNode', \
                    'kConstraint':'kTransform', 'kField':'kTransform', \
                    'kShape':'kDagNode', 'kGeometric':'kShape', 'kDeformFunc':'kShape', 'kClusterFilter':'kWeightGeometryFilt', \
                    'kDimension':'kShape', \
                    'kCreate':'kDependencyNode', 'kPolyCreator':'kDependencyNode', \
                    'kMidModifier':'kDependencyNode', 'kSubdModifier':'kDependencyNode', \
                    'kCurveInfo':'kCreate', 'kCurveFromSurface':'kCreate', \
                    'kSurface':'kGeometric', 'kRevolvedPrimitive':'kGeometric', 'kPlane':'kGeometric', 'kCurve':'kGeometric', \
                    'kAnimCurve':'kDependencyNode', 'kResultCurve':'kAnimCurve', 'kCacheBase':'kDependencyNode' ,'kFilter':'kDependencyNode', \
                    'kBlend':'kDependencyNode', 'kIkSolver':'kDependencyNode', \
                    'kLight':'kShape', 'kNonAmbientLight':'kLight', 'kNonExtendedLight':'kNonAmbientLight', \
                    'kTexture2d':'kDependencyNode', 'kTexture3d':'kDependencyNode', 'kTextureEnv':'kDependencyNode', \
                    'kPlugin':'kBase', 'kPluginDependNode':'kDependencyNode', 'kPluginLocatorNode':'kLocator', \
                    'kPluginDeformerNode':'kGeometryFilt', 'kPluginConstraintNode':'kConstraint', 'kPluginData':'kData', \
                    'kUnknown':'kDependencyNode', 'kUnknownDag':'kDagNode', 'kUnknownTransform':'kTransform',\
                    'kXformManip':'kTransform', 'kMoveVertexManip':'kXformManip' })  

apiTypeHierarchy = {}

def ApiTypeHierarchy() :
    return apiTypeHierarchy

# get the API type from a maya type
def mayaTypeToApiType (mayaType) :
    """ Get the Maya API type from the name of a Maya type """
    try:
        return MayaTypesToApiTypes()[mayaType]
    except KeyError:
        apiType = 'kInvalid'
        # Reserved types must be treated specially
        if ReservedMayaTypes().has_key(mayaType) :
            # It's an abstract type            
            apiType = ReservedMayaTypes()[mayaType]
        else :
            # we create a dummy object of this type in a dgModifier
            # as the dgModifier.doIt() method is never called, the object
            # is never actually created in the scene
            obj = MObject() 
            dagMod = MDagModifier()
            dgMod = MDGModifier()
            #if mayaType == 'directionalLight': print "MayaTypesToApiTypes", "directionalLight" in MayaTypesToApiTypes().keys(), len(MayaTypesToApiTypes().keys())
            obj = _makeDgModGhostObject(mayaType, dagMod, dgMod)
            if isValidMObject(obj):
                apiType = obj.apiTypeStr()
        return apiType


def addMayaType(mayaType, apiType=None ) :
    """ Add a type to the MayaTypes lists. Fill as many dictionary caches as we have info for. 
    
        - MayaTypesToApiTypes
        - ApiTypesToMayaTypes
        - ApiTypesToApiEnums
        - ApiEnumsToApiTypes
        - MayaTypesToApiEnums
        - ApiEnumsToMayaTypes
    """


    if apiType is None:
        apiType = mayaTypeToApiType(mayaType)    
    if apiType is not 'kInvalid' :
        
        apiEnum = getattr( MFn, apiType )
        
        defType = ReservedMayaTypes().has_key(mayaType)
        
        MayaTypesToApiTypes()[mayaType] = apiType
        if not ApiTypesToMayaTypes().has_key(apiType) :
            ApiTypesToMayaTypes()[apiType] = { mayaType : defType }
        else :
            ApiTypesToMayaTypes()[apiType][mayaType] = defType
        
        # these are static and are build elsewhere
        #ApiTypesToApiEnums()[apiType] = apiEnum
        #ApiEnumsToApiTypes()[apiEnum] = apiType
        
        MayaTypesToApiEnums()[mayaType] = apiEnum
        if not ApiEnumsToMayaTypes().has_key(apiEnum) :
            ApiEnumsToMayaTypes()[apiEnum] = { mayaType : None }
        else:
            ApiEnumsToMayaTypes()[apiEnum][mayaType] = None 

def removeMayaType( mayaType ):
    """ Remove a type from the MayaTypes lists. 
    
        - MayaTypesToApiTypes
        - ApiTypesToMayaTypes
        - ApiTypesToApiEnums
        - ApiEnumsToApiTypes
        - MayaTypesToApiEnums
        - ApiEnumsToMayaTypes
    """
    try:
        apiEnum = MayaTypesToApiEnums().pop( mayaType )
    except KeyError: pass
    else:
        enums = ApiEnumsToMayaTypes()[apiEnum]
        enums.pop( mayaType, None )
        if not enums:
            ApiEnumsToMayaTypes().pop(apiEnum)
            ApiEnumsToApiTypes().pop(apiEnum)
    try:
        apiType = MayaTypesToApiTypes().pop( mayaType, None )
    except KeyError: pass
    else:
        types = ApiTypesToMayaTypes()[apiType]
        types.pop( mayaType, None )
        if not types:
            ApiTypesToMayaTypes().pop(apiType)
            ApiTypesToApiEnums().pop(apiType)
    
       

def _getMObject(nodeType, dagMod, dgMod) :
    """ Returns a queryable MObject from a given apiType or mayaType"""
    
    # cant create these nodes, some would crahs MAya also
    if ReservedApiTypes().has_key(nodeType) or ReservedMayaTypes().has_key(nodeType) :
        return None   

    if ApiTypesToMayaTypes().has_key(nodeType) :
        mayaType = ApiTypesToMayaTypes()[nodeType].keys()[0]
        #apiType = nodeType
    elif MayaTypesToApiTypes().has_key(nodeType) :
        mayaType = nodeType
        #apiType = MayaTypesToApiTypes()[nodeType]
    else :
        return None    
    
    return _makeDgModGhostObject(mayaType, dagMod, dgMod)


def _makeDgModGhostObject(mayaType, dagMod, dgMod):
    # we create a dummy object of this type in a dgModifier (or dagModifier)
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    
    # Note that you need to call the dgMod/dagMod.deleteNode method as well - if we don't,
    # and we call this function while loading a scene (for instance, if the scene requires
    # a plugin that isn't loaded, and defines custom node types), then the nodes are still
    # somehow created, despite never explicitly calling doIt()
    if type(dagMod) is not MDagModifier or type(dgMod) is not MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"

    # Regardless of whether we're making a DG or DAG node, make a parent first - 
    # for some reason, this ensures good cleanup (don't ask me why...??)
    parent = dagMod.createNode ( 'transform', MObject())
    
    try:
        try :
            # Try making it with dgMod FIRST - this way, we can avoid making an
            # unneccessary transform if it is a DG node
            obj = dgMod.createNode ( mayaType )
        except RuntimeError:
            # DagNode
            obj = dagMod.createNode ( mayaType, parent )
            _logger.debug( "Made ghost DAG node of type '%s'" % mayaType )
        else:
            # DependNode
            _logger.debug( "Made ghost DG node of type '%s'" % mayaType )
            dgMod.deleteNode(obj)
    except:
        obj = MObject()

    dagMod.deleteNode(parent)

    if isValidMObject(obj) :
        return obj
    else :
        _logger.debug("Error trying to create ghost node for '%s'" %  mayaType)
        return None


# check if a an API type herits from another
# it can't b e done for "virtual" types (in ReservedApiTypes)
def _hasFn (apiType, dagMod, dgMod, parentType=None) :
    """ Get the Maya API type from the name of a Maya type """
    if parentType is None :
        parentType = 'kBase'
    # Reserved we can't determine it as we can't create the node, all we can do is check if it's
    # in the ReservedApiHierarchy
    if ReservedApiTypes().has_key(apiType) :
        return ReservedApiHierarchy().get(apiType, None) == parentType
    # Need the MFn::Types enum for the parentType
    if ApiTypesToApiEnums().has_key(parentType) :
        typeInt = ApiTypesToApiEnums()[parentType]
    else :
        return False
    # print "need creation for %s" % apiType
    obj = _getMObject(apiType, dagMod, dgMod, parentType) 
    if isValidMObject(obj) :
        return obj.hasFn(typeInt)
    else :
        return False
 

# Filter the given API type list to retain those that are parent of apiType
# can pass a list of types to check for being possible parents of apiType
# or a dictionnary of types:node to speed up testing
def _parentFn (apiType, dagMod, dgMod, *args, **kwargs) :
    """ Checks the given API type list, or API type:MObject dictionnary to return the first parent of apiType """
    if not kwargs :
        if not args :
            args = ('kBase', )
        kwargs = dict( (args[k], None) for k in args )
    else :
        for k in args :
            if not kwargs.has_key(k) :
                kwargs[k] = None
    # Reserved we can't determine it as we can't create the node, all we can do is check if it's
    # in the ReservedApiHierarchy
    if ReservedApiTypes().has_key(apiType) :
        p = ReservedApiHierarchy().get(apiType, None)
        if p is not None :
            for t in kwargs.keys() :
                if p == t :
                    return t
        return None

    result = None           
    obj = kwargs.get(apiType, None)        
    if not isValidMObject(obj) :
        # print "need creation for %s" % apiType
        obj = _getMObject(apiType, dagMod, dgMod)
    if isValidMObject(obj) :
        if not kwargs.get(apiType, None) :
            kwargs[apiType] = obj          # update it if we had to create
        parents = []
        for t in kwargs.keys() :
            # Need the MFn::Types enum for the parentType
            if t != apiType :
                if ApiTypesToApiEnums().has_key(t) :
                    ti = ApiTypesToApiEnums()[t]
                    if obj.hasFn(ti) :
                        parents.append(t)
        # problem is the MObject.hasFn method returns True for all ancestors, not only first one
        if len(parents) :
            if len(parents) > 1 :
                for p in parents :
                    if ApiTypesToApiEnums().has_key(p) :
                        ip = ApiTypesToApiEnums()[p]
                        isFirst = True
                        for q in parents :
                            if q != p :
                                stored = kwargs.get(q, None)
                                if not stored :
                                    if ReservedApiTypes().has_key(q) :
                                        isFirst = not ReservedApiHierarchy().get(q, None) == p
                                    else :                                    
                                        stored = _getMObject(q, dagMod, dgMod)
                                        if not kwargs.get(q, None) :
                                            kwargs[q] = stored          # update it if we had to create                                        
                                if stored :
                                    isFirst = not stored.hasFn(ip)
                            if not isFirst :
                                break
                        if isFirst :
                            result = p
                            break
            else :
                result = parents[0]
                                 
    return result

def _createNodes(dagMod, dgMod, *args) :
    """pre-build a apiType:MObject, and mayaType:apiType lookup for all provided types, be careful that these MObject
        can be used only as long as dagMod and dgMod are not deleted"""

    result = {}
    mayaResult = {}
    unableToCreate = set()
    
        
    for mayaType in args :
        if ReservedMayaTypes().has_key(mayaType) :
            apiType = ReservedMayaTypes()[mayaType]
            #print "reserved", mayaType, apiType
            mayaResult[mayaType] = apiType
            result[apiType] = None
      
        else :
            obj = _makeDgModGhostObject(mayaType, dagMod, dgMod)
            if obj :
                apiType = obj.apiTypeStr()
                mayaResult[mayaType] = apiType
                result[apiType] = obj
            else:
                unableToCreate.add(mayaType)
    return result, mayaResult, unableToCreate

# child:parent lookup of the Maya API classes hierarchy (based on the existing MFn class hierarchy)
# TODO : fix that, doesn't accept the Singleton base it seems
# class ApiTypeHierarchy(FrozenTree) :
#    """ Hierarchy Tree of all API Types """
#    __metaclass__ = Singleton

def _buildApiTypesList():
    """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with 
    an existing api type"""
    
    ApiTypesToApiEnums().clear()
    ApiEnumsToApiTypes().clear()
    
    ApiTypesToApiEnums( dict( inspect.getmembers(MFn, lambda x:type(x) is int)) )
    ApiEnumsToApiTypes( dict( (ApiTypesToApiEnums()[k], k) for k in ApiTypesToApiEnums().keys()) )

    #apiTypesToApiEnums = dict( inspect.getmembers(MFn, lambda x:type(x) is int)) 
    #apiEnumsToApiTypes = dict( (ApiTypesToApiEnums()[k], k) for k in ApiTypesToApiEnums().keys()) 
    #return apiTypesToApiEnums, apiEnumsToApiTypes
    
## Initialises MayaTypes for a faster later access
#def _buildMayaTypesList() :
#    """Updates the cached MayaTypes lists """
#    start = time.time()
#    from maya.cmds import ls as _ls
#    # api types/enums dicts must be created before reserved type bc they are used for filtering
#    _buildMayaReservedTypes()
#    
#    # use dict of empty keys just for faster random access
#    # the nodes returned by ls will be added by createPyNodes and pluginLoadedCB
#    # add new types
#    print "reserved types", ReservedMayaTypes()
#    for mayaType, apiType in ReservedMayaTypes().items() + [(k, None) for k in _ls(nodeTypes=True)]:
#         #if not MayaTypesToApiTypes().has_key(mayaType) :
#         addMayaType( mayaType, apiType )
#    elapsed = time.time() - start
#    print "Updated Maya types list in %.2f sec" % elapsed


# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def _buildApiTypeHierarchy (apiClassInfo=None) :
    """
    Used to rebuild api info from scratch.
    
    Set 'apiClassInfo' to a valid apiClassInfo structure to disable rebuilding of apiClassInfo
    - this is useful for versions < 2009, as these versions cannot parse the api docs; by passing
    in an apiClassInfo, you can rebuild all other api information.  If left at the default value
    of 'None', then it will be rebuilt using the apiDocParser.
    """
    def _MFnType(x) :
        if x == MFnBase :
            return ApiEnumsToApiTypes()[ 1 ]  # 'kBase'
        else :
            try :
                return ApiEnumsToApiTypes()[ x().type() ]
            except :
                return ApiEnumsToApiTypes()[ 0 ] # 'kInvalid'
    
    #global apiTypeHierarchy, ApiTypesToApiClasses
    _buildMayaReservedTypes()
    
    if not mayahook.mayaIsRunning():
        mayahook.mayaInit()
    import maya.cmds
    
    # load all maya plugins
    mayaLoc = mayahook.getMayaLocation()
    # need to set to os.path.realpath to get a 'canonical' path for string comparison...
    pluginPaths = [os.path.realpath(x) for x in os.environ['MAYA_PLUG_IN_PATH'].split(os.path.pathsep)]
    for pluginPath in [x for x in pluginPaths if x.startswith( mayaLoc ) and os.path.isdir(x) ]:
        for x in os.listdir( pluginPath ):
            if os.path.isfile( os.path.join(pluginPath,x)):
                maya.cmds.loadPlugin( x )

    allMayaTypes = ReservedMayaTypes().keys() + maya.cmds.ls(nodeTypes=True)
    
    apiTypesToApiClasses = {}
    
    # all of maya OpenMaya api is now imported in module api's namespace
    MFnClasses = inspect.getmembers(_thisModule, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
    MFnTree = inspect.getclasstree( [x[1] for x in MFnClasses] )
    MFnDict = {}
    
    for x in expandArgs(MFnTree, type='list') :
        MFnClass = x[0]
        current = _MFnType(MFnClass)
        if current and current != 'kInvalid' and len(x[1]) > 0:
            #Check that len(x[1]) > 0 because base python 'object' will have no parents...
            parent = _MFnType(x[1][0])
            if parent:
                apiTypesToApiClasses[ current ] = MFnClass
                #ApiTypesToApiClasses()[ current ] = x[0]
                MFnDict[ current ] = parent
    
    if apiClassInfo is None:
        apiClassInfo = {}
#        try:
        parser = ApiDocParser()
#        except IOError, msg: 
#            _logger.warn( "failed to find docs for current version: %s", name )
            
        for name, obj in inspect.getmembers( _thisModule, lambda x: type(x) == type and x.__name__.startswith('M') ):
            if not name.startswith( 'MPx' ):
                
                try:
                    try:
                        info = parser.parse(name)
                        apiClassInfo[ name ] = info
                    except IOError:
                        _logger.warn( "failed to parse docs: %s", name )

                except (ValueError,IndexError), msg: 
                    _logger.warn( "failed %s %s" % ( name, msg ) )
                    
    # print MFnDict.keys()
    # Fixes for types that don't have a MFn by faking a node creation and testing it
    # Make it faster by pre-creating the nodes used to test
    dagMod = MDagModifier()
    dgMod = MDGModifier()      
    #nodeDict = _createNodes(dagMod, dgMod, *ApiTypesToApiEnums().keys())
    nodeDict, mayaDict, unableToCreate = _createNodes( dagMod, dgMod, *allMayaTypes )
    if len(unableToCreate) > 0:
        _logger.warn("Unable to create the following nodes: %s" % ", ".join(unableToCreate))
    
    for mayaType, apiType in mayaDict.items() :
        MayaTypesToApiTypes()[mayaType] = apiType
        addMayaType( mayaType, apiType )
    
    # Fix? some MFn results are not coherent with the hierarchy presented in the docs :
    MFnDict.pop('kWire', None)
    MFnDict.pop('kBlendShape', None)
    MFnDict.pop('kFFD', None)
    for k in ApiTypesToApiEnums().keys() :
        if k not in MFnDict.keys() :
            #print "%s not in MFnDict, looking for parents" % k
            #startParent = time.time()
            p = _parentFn(k, dagMod, dgMod, **nodeDict)
            #endParent = time.time()
            if p :
                #print "Found parent: %s in %.2f sec" % (p, endParent-startParent)
                MFnDict[k] = p
            else :
                #print "Found none in %.2f sec" % (endParent-startParent)     
                pass         
                                       
    # print MFnDict.keys()
    # make a Tree from that child:parent dictionnary

    # assign the hierarchy to the module-level variable
    apiTypeHierarchy = IndexedFrozenTree(treeFromDict(MFnDict))
    return apiTypeHierarchy, apiTypesToApiClasses, apiClassInfo

def _buildApiCache(rebuildAllButClassInfo=False):
    """
    Used to rebuild api cache, either by loading from a cache file, or rebuilding from scratch.
    
    Set 'rebuildAllButClassInfo' to True to force rebuilding of all info BUT apiClassInfo -
    this is useful for versions < 2009, as these versions cannot parse the api docs; by setting
    this to False, you can rebuild all other api information.
    """        

    apiToMelData, apiClassOverrides = loadApiToMelBridge()
    
    # Need to initialize this to possibly pass into _buildApiTypeHierarchy, if rebuildAllButClassInfo
    apiClassInfo = None
    
    data = mayahook.loadCache( 'mayaApi', 'the API cache' )
    if data is not None:
        
        ReservedMayaTypes(data[0])
        ReservedApiTypes(data[1])
        ApiTypesToApiEnums(data[2])
        ApiEnumsToApiTypes(data[3])
        MayaTypesToApiTypes(data[4])
        ApiTypesToApiClasses(data[5])
        apiTypeHierarchy = data[6]
        apiClassInfo = data[7]
        
        
        if not rebuildAllButClassInfo:
            # Note that even if rebuildAllButClassInfo, we still want to load
            # the cache file, in order to grab apiClassInfo
            return apiTypeHierarchy, apiClassInfo, apiToMelData, apiClassOverrides
            
    
    _logger.info( "Rebuilding the API Caches..." )
    
    # fill out the data structures
    _buildApiTypesList()
    #apiTypesToApiEnums, apiEnumsToApiTypes = _buildApiTypesList()
    #_buildMayaTypesList()
    
    if not rebuildAllButClassInfo:
        apiClassInfo = None
    apiTypeHierarchy, apiTypesToApiClasses, apiClassInfo = _buildApiTypeHierarchy(apiClassInfo=apiClassInfo)

    # merge in the manual overrides: we only do this when we're rebuilding or in the pymelControlPanel
    _logger.info( 'merging in dictionary of manual api overrides')
    util.mergeCascadingDicts( apiClassOverrides, apiClassInfo, allowDictToListMerging=True )

    mayahook.writeCache( ( dict(ReservedMayaTypes()), dict(ReservedApiTypes()), 
                           dict(ApiTypesToApiEnums()), dict(ApiEnumsToApiTypes()), 
                           dict(MayaTypesToApiTypes()), 
                           apiTypesToApiClasses, apiTypeHierarchy, apiClassInfo 
                          )
                         , 'mayaApi', 'the API cache' )
    
    return apiTypeHierarchy, apiClassInfo, apiToMelData, apiClassOverrides

# TODO : to represent plugin registered types we might want to create an updatable (dynamic, not static) MayaTypesHierarchy ?

def saveApiCache():
    mayahook.writeCache( ( dict(ReservedMayaTypes()), dict(ReservedApiTypes()), 
                           dict(ApiTypesToApiEnums()), dict(ApiEnumsToApiTypes()), 
                           dict(MayaTypesToApiTypes()), 
                           dict(ApiTypesToApiClasses()), apiTypeHierarchy, apiClassInfo 
                          )
                         , 'mayaApi', 'the API cache' )

def loadApiToMelBridge():

    data = mayahook.loadCache( 'mayaApiMelBridge', 'the api-mel bridge', useVersion=False )
    if data is not None:
        # maya 8.5 fix: convert dict to defaultdict
        bridge, overrides = data
        bridge = util.defaultdict(dict, bridge)
        return bridge, overrides
    
    # no bridge cache exists. create default
    bridge = util.defaultdict(dict)
    
    # no api overrides exist. create default
    overrides = {}
    
    return bridge, overrides

def saveApiToMelBridge():
    # maya 8.5 fix: convert defaultdict to dict
    bridge = dict(apiToMelData)
    mayahook.writeCache( (bridge,apiClassOverrides ), 'mayaApiMelBridge', 'the api-mel bridge', useVersion=False )


#-------------------------------------------------------------------------------------

_start = time.time()
apiTypeHierarchy, apiClassInfo, apiToMelData, apiClassOverrides = _buildApiCache(rebuildAllButClassInfo=False)

    
_elapsed = time.time() - _start
_logger.debug( "Initialized API Cache in in %.2f sec" % _elapsed )

#-------------------------------------------------------------------------------------


def toApiTypeStr( obj ):
    if isinstance( obj, int ):
        return ApiEnumsToApiTypes().get( obj, None )
    elif isinstance( obj, basestring ):
        return MayaTypesToApiTypes().get( obj, None)
    
def toApiTypeEnum( obj ):
    try:
        return ApiTypesToApiEnums()[obj]
    except KeyError:
        return MayaTypesToApiEnums().get(obj,None)

def toMayaType( obj ):
    if isinstance( obj, int ):
        return ApiEnumsToMayaTypes().get( obj, None )
    elif isinstance( obj, basestring ):
        return ApiTypesToMayaTypes().get( obj, None)
    
def toApiFunctionSet( obj ):
    if isinstance( obj, basestring ):
        try:
            return ApiTypesToApiClasses()[ obj ]
        except KeyError:
            return ApiTypesToApiClasses().get( MayaTypesToApiTypes().get( obj, None ) )
         
    elif isinstance( obj, int ):
        try:
            return ApiTypesToApiClasses()[ ApiEnumsToApiTypes()[ obj ] ]
        except KeyError:
            return

#-----------------------------------
# All Below Here are Deprecated
#-----------------------------------
# conversion API enum int to API type string and back
def apiEnumToType (apiEnum) :
    """ Given an API type enum int, returns the corresponding Maya API type string,
        as in MObject.apiType() to MObject.apiTypeStr() """    
    return ApiEnumsToApiTypes().get(apiEnum, None)

def apiTypeToEnum (apiType) :
    """ Given an API type string, returns the corresponding Maya API type enum (int),
        as in MObject.apiTypeStr() to MObject.apiType()"""
    # Is there ever a time that our dictionary would not have an entry and MFn would? I changed this
    # because after reload of certain pymel modules, these dictionaries can go empty.
    #return ApiTypesToApiEnums().get(apiType, None)
    try:
        return getattr( MFn, apiType )
    except AttributeError:
        pass

# get the maya type from an API type
def apiEnumToNodeType (apiTypeEnum) :
    """ Given an API type enum int, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return ApiEnumsToMayaTypes().get(apiTypeEnum, None)

def apiTypeToNodeType (apiType) :
    """ Given an API type name, returns the corresponding Maya node type,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return ApiTypesToMayaTypes().get(apiType, None)

def nodeTypeToAPIType (nodeType) :
    """ Given an Maya node type name, returns the corresponding Maya API type name,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    return MayaTypesToApiTypes().get(nodeType, None)


def apiToNodeType (*args) :
    """ Given a list of API type or API type int, return the corresponding Maya node types,
        note that there isn't an exact 1:1 equivalence, in the case no corresponding node type
        can be found, will return the corresponding type for the first parent in the types hierarchy
        that can be matched """
    result = []
    for a in args :
        if type(a) is int :         
            result.append(_apiEnumToNodeType(a))
        else :
            result.append(_apiTypeToNodeType(a))
    if len(result) == 1 :
        return result[0]
    else :
        return tuple(result)

#-----------------------------------
# All Above Here are Deprecated
#-----------------------------------

# Converting API MObjects and more

## type for a MObject with nodeType / objectType like options
#def objType (obj, api=True, inherited=True):
#    """ Returns the API or Node type name of MObject obj, and optionnally
#        the list of types it inherits from.
#            >>> obj = toMObject ('pCubeShape1')
#            >>> objType (obj, api=True, inherited=True)
#            >>> # Result: ['kBase', 'kDependencyNode', 'kDagNode', 'kMesh'] #
#            >>> objType (obj, api=False, inherited=True)
#            >>> # Result: ['dependNode', 'entity', 'dagNode', 'shape', 'geometryShape', 'deformableShape', 'controlPoint', 'surfaceShape', 'mesh'] # 
#        Note that unfortunatly API and Node types do not exactly match in their hierarchy in Maya
#    """
#    result = obj.apiType()
#    if api :
#        result = apiEnumToType (result)
#        if inherited :
#            result = [k.value for k in ApiTypeHierarchy().path(result)]    
#    else :
#        result = apiEnumToNodeType (result)
#        if inherited :
#            result =  [k.value for k in NodeHierarchy().path(result)]   
#    return result
            
# returns a MObject for an existing node
def toMObject (nodeName):
    """ Get the API MObject given the name of an existing node """ 
    sel = MSelectionList()
    obj = MObject()
    result = None
    try :
        sel.add( nodeName )
        sel.getDependNode( 0, obj )
        if isValidMObject(obj) :
            result = obj 
    except :
        pass
    return result

def toApiObject (nodeName, dagPlugs=True):
    """ Get the API MPlug, MObject or (MObject, MComponent) tuple given the name of an existing node, attribute, components selection
    
    if dagPlugs is True, plug result will be a tuple of type (MDagPath, MPlug)
    
    """ 
    sel = MSelectionList()
    try:
        sel.add( nodeName )
    except:
        if "." in nodeName :
            # Compound Attributes
            #  sometimes the index might be left off somewhere in a compound attribute 
            # (ex 'Nexus.auxiliary.input' instead of 'Nexus.auxiliary[0].input' )
            #  but we can still get a representative plug. this will return the equivalent of 'Nexus.auxiliary[-1].input'
            try:
                buf = nodeName.split('.')
                obj = toApiObject( buf[0] )
                if isinstance(obj,MDagPath):
                    mfn = MFnDagNode(obj)
                else:
                    mfn = MFnDependencyNode(obj)
                plug = mfn.findPlug( buf[-1], False )
                
                if dagPlugs: # and isValidMDagPath(obj) : 
                    return (obj, plug)
                return plug
            except (RuntimeError,ValueError):
                return
    else:
        if "." in nodeName :
            try:
                # Plugs
                plug = MPlug()
                sel.getPlug( 0, plug )
                if dagPlugs:
                    try:
                        # Plugs with DagPaths
                        sel.add( nodeName.split('.')[0] )
                        dag = MDagPath()
                        sel.getDagPath( 1, dag )
                        #if isValidMDagPath(dag) :
                        return (dag, plug)
                    except RuntimeError: pass
                return plug
            
            except RuntimeError:
                # Components
                dag = MDagPath()
                comp = MObject()
                sel.getDagPath( 0, dag, comp )
                #if not isValidMDagPath(dag) :   return
                return (dag, comp)
        else:
            try:
                # DagPaths
                dag = MDagPath()
                sel.getDagPath( 0, dag )
                #if not isValidMDagPath(dag) : return
                return dag
         
            except RuntimeError:
                # Objects
                obj = MObject()
                sel.getDependNode( 0, obj )          
                #if not isValidMObject(obj) : return     
                return obj
        
#    # TODO : components
#    if "." in nodeName :
#        # build up to the final MPlug
#        nameTokens = nameparse.getBasicPartList( nodeName )
#        if dag.isValid():
#            fn = MFnDagNode(dag)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, MPlug ):
#                        result = result.child( fn.attribute( unicode(token) ) )
#                    else:
#                        try:
#                            result = fn.findPlug( unicode(token) )
#                        except TypeError:
#                            for i in range(fn.childCount()):
#                                try:
#                                    result = MFnDagNode( fn.child(i) ).findPlug( unicode(token) )
#                                except TypeError:
#                                    pass
#                                else:
#                                    break
#                if isinstance( token, nameparse.NameIndex ):
#                    result = result.elementByLogicalIndex( token.value )
#            if dagMatters:
#                result = (dag, result)
#        else:
#            fn = MFnDependencyNode(obj)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, MPlug ):
#                        result = result.child( fn.attribute( unicode(token) ) )
#                    else:
#                        result = fn.findPlug( unicode(token) )
#                            
#                if isinstance( token, nameparse.NameIndex ):
#                    result = result.elementByLogicalIndex( token.value )
#        
#
#    return result

def toMDagPath (nodeName):
    """ Get an API MDagPAth to the node, given the name of an existing dag node """ 
    obj = toMObject (nodeName)
    if obj :
        dagFn = MFnDagNode (obj)
        dagPath = MDagPath()
        dagFn.getPath ( dagPath )
        return dagPath

# returns a MPlug for an existing plug
def toMPlug (plugName):
    """ Get the API MObject given the name of an existing plug (node.attribute) """
    nodeAndAttr = plugName.split('.', 1)
    obj = toMObject (nodeAndAttr[0])
    plug = None
    if obj :
        depNodeFn = MFnDependencyNode(obj)
        attr = depNodeFn.attribute(nodeAndAttr[1])
        plug = MPlug ( obj, attr )
        if plug.isNull() :
            plug = None
    return plug

def toComponentMObject( dagPath ):
    """
    get an MObject representing all components of the passed dagPath
    
    The component type that will be returned depends on the exact type of
    object passed in - for instance, a poly mesh will return a component
    representing all the kMeshVertComponents.
    
    The exact choice of component type is determined by MItGeometry.
    """
    
    component = MObject()
    sel = MSelectionList()
    mit = MItGeometry( dagPath )
    while not mit.isDone():
        # MItGeometry.component is deprecated
        comp = mit.currentItem()
        # merge is True
        sel.add( dagPath, comp, True )
        mit.next()
    sel.getDagPath( 0, dagPath, component )
    return component
      
# MDagPath, MPlug or MObject to name
# Note there is a kNamedObject API type but not corresponding MFn, thus
# I see no way of querying the name of something that isn't a kDependency node or a MPlug
# TODO : add components support, short/ long name support where applies
def MObjectName( obj ):
    """ Get the name of an existing MPlug, MDagPath or MObject representing a dependency node""" 
    if isValidMPlug (obj) :
        return obj.name()
    elif isValidMNode (obj) :
        depNodeFn = MFnDependencyNode(obj)
        return depNodeFn.name()
    elif isValidMDagPath (obj):
        # return obj.fullPathName()
        return obj.partialPathName()
    else :
        return unicode(obj)


# names to MObjects function (expected to be faster to share one selectionList)
def nameToMObject( *args ):
    """ Get the API MObjects given names of existing nodes """ 
    sel = MSelectionList() 
    for name in args :
        sel.add( name )
    result = []            
    obj = MObject()            
    for i in range(sel.length()) :
        try :
            sel.getDependNode( i, obj )
        except :
            result.append(None)
        if isValidMObject(obj) :
            result.append(obj)
        else :
            result.append(None)
    if len(result) == 1:
        return result[0]
    else :
        return tuple(result)

def getComponentTypes():
    # WTF is kMeshFaceVertComponent?? it doesn't inherit from MFnComponent,
    # and there's also a kMeshVtxFaceComponent (which does)??
    mfnCompBase = MFnComponent()
    mfnCompTypes = (MFnSingleIndexedComponent(),
                    MFnDoubleIndexedComponent(),
                    MFnTripleIndexedComponent())
    # Maya 2008 and before didn't haveMFnUint64SingleIndexedComponent
    if hasattr(MFn, 'kUint64SingleIndexedComponent'):
        mfnCompTypes += (MFnUint64SingleIndexedComponent(),)
    
    componentTypes = {}
    for compType in mfnCompTypes + (mfnCompBase,):
        componentTypes[compType.type()] = []

    for apiEnum in ApiEnumsToApiTypes():
        if mfnCompBase.hasObj(apiEnum):
            for compType in mfnCompTypes:
                if compType.hasObj(apiEnum):
                    break
            else:
                compType = mfnCompBase
            componentTypes[compType.type()].append(apiEnum)
                
    return componentTypes

    
# wrap of api iterators

def MItNodes( *args, **kwargs ):
    """ Iterator on MObjects of nodes of the specified types in the Maya scene,
        if a list of tyes is passed as args, then all nodes of a type included in the list will be iterated on,
        if no types are specified, all nodes of the scene will be iterated on
        the types are specified as Maya API types """
    typeFilter = MIteratorType()
    if args : 
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we will iterate on dependancy nodes, not dagPaths or plugs
        typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) typeFilter
    iterObj = MItDependencyNodes ( typeFilter )     
    while not iterObj.isDone() :
        yield (iterObj.thisNode())
        iterObj.next()   


# Iterators on nodes connections using MItDependencyGraph (ie listConnections/ listHistory)
def MItGraph (nodeOrPlug, *args, **kwargs):
    """ Iterate over MObjects of Dependency Graph (DG) Nodes or Plugs starting at a specified root Node or Plug,
        If a list of types is provided, then only nodes of these types will be returned,
        if no type is provided all connected nodes will be iterated on.
        Types are specified as Maya API types.
        The following keywords will affect order and behavior of traversal:
        upstream: if True connections will be followed from destination to source,
                  if False from source to destination
                  default is False (downstream)
        breadth: if True nodes will be returned as a breadth first traversal of the connection graph,
                 if False as a preorder (depth first)
                 default is False (depth first)
        plug: if True traversal will be at plug level (no plug will be traversed more than once),
              if False at node level (no node will be traversed more than once),
              default is False (node level)
        prune : if True will stop the iteration on nodes than do not fit the types list,
                if False these nodes will be traversed but not returned
                default is False (do not prune) """
#    startObj = MObject() 
#    startPlug = MPlug()
    startObj = None
    startPlug = None   
    if isValidMPlug(nodeOrPlug):
        startPlug = nodeOrPlug
    elif isValidMNode(nodeOrPlug) :
        startObj = nodeOrPlug
    else :
        raise ValueError, "'%s' is not a valid Node or Plug" % toMObjectName(nodeOrPlug)
    upstream = kwargs.get('upstream', False)
    breadth = kwargs.get('breadth', False)
    plug = kwargs.get('plug', False)
    prune = kwargs.get('prune', False)
    if args : 
        typeFilter = MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a node or a plug
        if startPlug is not None :
            typeFilter.setObjectType ( MIteratorType.kMPlugObject )
        else :
            typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if upstream :
        direction = MItDependencyGraph.kUpstream
    else :
        direction = MItDependencyGraph.kDownstream
    if breadth :
        traversal = MItDependencyGraph.kBreadthFirst 
    else :
        traversal =  MItDependencyGraph.kDepthFirst
    if plug :
        level = MItDependencyGraph.kPlugLevel
    else :
        level = MItDependencyGraph.kNodeLevel
    iterObj = MItDependencyGraph ( startObj, startPlug, typeFilter, direction, traversal, level )
    if prune :
        iterObj.enablePruningOnFilter()
    else :
        iterObj.disablePruningOnFilter() 
    # iterates and yields MObjects
    while not iterObj.isDone() :
        yield (iterObj.thisNode())
        iterObj.next()

# Iterators on dag nodes hierarchies using MItDag (ie listRelatives)
def MItDag (root = None, *args, **kwargs) :
    """ Iterate over the hierarchy under a root dag node, if root is None, will iterate on whole Maya scene
        If a list of types is provided, then only nodes of these types will be returned,
        if no type is provided all dag nodes under the root will be iterated on.
        Types are specified as Maya API types.
        The following keywords will affect order and behavior of traversal:
        breadth: if True nodes Mobjects will be returned as a breadth first traversal of the hierarchy tree,
                 if False as a preorder (depth first)
                 default is False (depth first)
        underworld: if True traversal will include a shape's underworld (dag object parented to the shape),
              if False underworld will not be traversed,
              default is False (do not traverse underworld )
        depth : if True will return depth of each node.
        prune : if True will stop the iteration on nodes than do not fit the types list,
                if False these nodes will be traversed but not returned
                default is False (do not prune) """
    # startObj = MObject()
    # startPath = MDagPath()
    startObj = startPath = None  
    if isValidMDagPath (root) :
        startPath = root
    elif isValidMDagNode (root) :
        startObj = root
    else :
        raise ValueError, "'%s' is not a valid Dag Node" % toMObjectName(root)
    breadth = kwargs.get('breadth', False)
    underworld = kwargs.get('underworld', False)
    prune = kwargs.get('prune', False)
    path = kwargs.get('path', False)
    allPaths = kwargs.get('allPaths', False)
    if args : 
        typeFilter = MIteratorType()
        if len(args) == 1 :
            typeFilter.setFilterType ( args[0] ) 
        else :
            # annoying argument conversion for Maya API non standard C types
            scriptUtil = MScriptUtil()
            typeIntM = MIntArray()
            scriptUtil.createIntArrayFromList ( args,  typeIntM )
            typeFilter.setFilterList ( typeIntM )
        # we start on a MDagPath or a Mobject
        if startPath is not None :
            typeFilter.setObjectType ( MIteratorType.kMDagPathObject )
        else :
            typeFilter.setObjectType ( MIteratorType.kMObject )
    # create iterator with (possibly empty) filter list and flags
    if breadth :
        traversal = MItDag.kBreadthFirst 
    else :
        traversal =  MItDag.kDepthFirst
    iterObj = MItDag ( typeFilter, traversal )
    if root is not None :
        iterObj.reset ( typeFilter, startObj, startPath, traversal )
 
    if underworld :
        iterObj.traverseUnderWorld (True)
    else :
        iterObj.traverseUnderWorld (False) 
    # iterates and yields MObject or MDagPath
    # handle prune ?

    # Must define dPath in loop or the iterator will yield
    # them as several references to the same object (thus with the same value each time)
    # instances must not be returned multiple times
    # could use a dict but it requires "obj1 is obj2" and not only "obj1 == obj2" to return true to
    # dic = {}
    # dic[obj1]=True
    # dic.has_key(obj2) 
    instance = []
    # code doesn't look nice but Im putting the tests out of the iter loops to loose as little speed as possible,
    # will certainly define functions for each case
    if allPaths :
        dPathArray = MDagPathArray()
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    iterObj.getAllPaths(dPathArray)
                    nbDagPath = dPathArray.length()
                    for i in range(nbDagPath) :
                        dPath = MDagPath(dPathArray[i])
                        yield dPath
                    instance.append(obj)
            else :
                iterObj.getAllPaths(dPathArray)
                nbDagPath = dPathArray.length()
                for i in range(nbDagPath) :
                    dPath = MDagPath(dPathArray[i])
                    yield dPath
            iterObj.next()
    elif path :
        while not iterObj.isDone() :
            if iterObj.isInstanced ( True ) :
                obj = iterObj.currentItem()
                if not obj in instance :
                    dPath = MDagPath()
                    iterObj.getPath(dPath)
                    yield dPath
                    instance.append(obj)
            else :
                dPath = MDagPath()
                iterObj.getPath(dPath)
                yield dPath
            iterObj.next()                           
    else :
        while not iterObj.isDone() :
            obj = iterObj.currentItem()
            if iterObj.isInstanced ( True ) :
                if not obj in instance :
                    yield obj
                    instance.append(obj)
            else :
                yield obj
            iterObj.next()
    
           
def getPlugValue( plug ):
    """given an MPlug, get its value"""

    #if plug.isArray():
    #    raise TypeError, "array plugs of this type are not supported"
    
    obj = plug.attribute()
    apiType = obj.apiType()

    if apiType in [ MFn.kAttribute2Double, MFn.kAttribute2Float, MFn.kAttribute2Short, MFn.kAttribute2Int,
                    MFn.kAttribute3Double, MFn.kAttribute3Float, MFn.kAttribute3Short, MFn.kAttribute3Int,
                    MFn.kAttribute4Double,
                    MFn.kCompoundAttribute ] :
        res = []
        for i in range(plug.numChildren()):
            res.append( getPlugValue( plug.child(i) ) )
        return tuple(res)

    elif apiType in [ MFn.kDoubleLinearAttribute, MFn.kFloatLinearAttribute ] :
        return plug.asMDistance()

    elif apiType in [ MFn.kDoubleAngleAttribute, MFn.kFloatAngleAttribute ] :
        return plug.asMAngle()

    elif apiType == MFn.kTimeAttribute:
        return plug.asMTime()

    elif apiType == MFn.kNumericAttribute:
        #return getNumericPlugValue(plug)
        nAttr = MFnNumericAttribute(obj)
        dataType = nAttr.unitType()
        if dataType == MFnNumericData.kBoolean:
            return plug.asBool()
        
        elif dataType in [ MFnNumericData.kShort, MFnNumericData.kInt, MFnNumericData.kLong, MFnNumericData.kByte] :
            return plug.asInt()
        
        elif dataType in [ MFnNumericData.kFloat, MFnNumericData.kDouble, MFnNumericData.kAddr] :
            return plug.asDouble()
        raise "%s: unknown numeric attribute type: %s" % (plug.partialName(True, True, True, False, True, True), dataType)
    
    elif apiType == MFn.kEnumAttribute:
        return plug.asInt()
    
    elif apiType == MFn.kTypedAttribute:
        tAttr = MFnTypedAttribute( obj )
        dataType = tAttr.attrType()
        
        
        if dataType == MFnData.kInvalid:
            return None
        
        elif dataType == MFnData.kString:
            return plug.asString()
        
        elif dataType == MFnData.kNumeric:
            
            # all of the dynamic mental ray attributes fail here, but i have no idea why they are numeric attrs and not message attrs.
            # cmds.getAttr returns None, so we will too.
            try:
                dataObj = plug.asMObject()
            except:
                return
            
            try:
                numFn = MFnNumericData( dataObj )
            except RuntimeError:
                if plug.isArray():
                    raise TypeError, "%s: numeric arrays are not supported" % plug.partialName(True, True, True, False, True, True)
                else:
                    raise TypeError, "%s: attribute type is numeric, but its data cannot be interpreted numerically" % plug.partialName(True, True, True, False, True, True)
            dataType = numFn.numericType()
                    
            if dataType == MFnNumericData.kBoolean:
                return plug.asBool()
            
            elif dataType in [ MFnNumericData.kShort, MFnNumericData.kInt, MFnNumericData.kLong, MFnNumericData.kByte] :
                return plug.asInt()
            
            elif dataType in [ MFnNumericData.kFloat, MFnNumericData.kDouble, MFnNumericData.kAddr] :
                return plug.asDouble()
            
            elif dataType == MFnNumericData.k2Short :
                su1 = MScriptUtil()
                ptr1 = su1.asShortPtr()
                su2= MScriptUtil()
                ptr2 = su2.asShortPtr()
                
                numFn.getData2Short(ptr1,ptr2)
                return ( MScriptUtil(ptr1).asShort(), MScriptUtil(ptr2).asShort() )
            
            elif dataType in [ MFnNumericData.k2Int, MFnNumericData.k2Long ]:
                su1 = MScriptUtil()
                ptr1 = su1.asIntPtr()
                su2= MScriptUtil()
                ptr2 = su2.asIntPtr()
                
                numFn.getData2Int(ptr1,ptr2)
                return ( MScriptUtil(ptr1).asInt(), MScriptUtil(ptr2).asInt() )
        
            elif dataType == MFnNumericData.k2Float :
                su1 = MScriptUtil()
                ptr1 = su1.asFloatPtr()
                su2= MScriptUtil()
                ptr2 = su2.asFloatPtr()
                
                numFn.getData2Float(ptr1,ptr2)
                return ( MScriptUtil(ptr1).asFloat(), MScriptUtil(ptr2).asFloat() )
             
            elif dataType == MFnNumericData.k2Double :
                su1 = MScriptUtil()
                ptr1 = su1.asDoublePtr()
                su2= MScriptUtil()
                ptr2 = su2.asDoublePtr()
                
                numFn.getData2Double(ptr1,ptr2)
                return ( MScriptUtil(ptr1).asDouble(), MScriptUtil(ptr2).asDouble() )
        
            elif dataType == MFnNumericData.k3Float:
                su1 = MScriptUtil()
                ptr1 = su1.asFloatPtr()
                su2= MScriptUtil()
                ptr2 = su2.asFloatPtr()
                su3= MScriptUtil()
                ptr3 = su2.asFloatPtr()
                 
                numFn.getData3Float(ptr1,ptr2,ptr3)
                return ( MScriptUtil(ptr1).asFloat(), MScriptUtil(ptr2).asFloat(), MScriptUtil(ptr3).asFloat() )
            
            elif dataType ==  MFnNumericData.k3Double:
                su1 = MScriptUtil()
                ptr1 = su1.asDoublePtr()
                su2= MScriptUtil()
                ptr2 = su2.asDoublePtr()
                su3= MScriptUtil()
                ptr3 = su2.asDoublePtr()
                  
                numFn.getData3Double(ptr1,ptr2,ptr3)
                return ( MScriptUtil(ptr1).asDouble(), MScriptUtil(ptr2).asDouble(), MScriptUtil(ptr3).asDouble() )
            
        
            
            elif dataType == MFnNumericData.kChar :
                return plug.asChar()
            
            raise TypeError, "%s: Unsupported numeric attribute: %s" % (plug.partialName(True, True, True, False, True, True),dataType)
        
        elif dataType == MFnData.kMatrix :
            return MFnMatrixData( plug.asMObject() ).matrix()
        
        elif dataType == MFnData.kDoubleArray :
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnDoubleArrayData( dataObj ).array()
        
        elif dataType == MFnData.kIntArray :
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnIntArrayData( dataObj ).array()
        
        elif dataType == MFnData.kPointArray :
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnPointArrayData( dataObj ).array()
        
        elif dataType == MFnData.kVectorArray :
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnVectorArrayData( dataObj ).array()
        
        elif dataType == MFnData.kStringArray :
            try:
                dataObj = plug.asMObject()
            except RuntimeError:
                return []
            return MFnStringArrayData( dataObj ).array()
        raise TypeError, "%s: Unsupported typed attribute: %s" % (plug.partialName(True, True, True, False, True, True),dataType)
    
    raise TypeError, "%s: Unsupported Type: %s" % (plug.partialName(True, True, True, False, True, True), ApiEnumsToApiTypes().get( apiType, '' ))

        