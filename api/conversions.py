""" Imports Maya API methods in the 'api' namespace, and defines various utilities for Python<->API communication """

# They will be imported / redefined later in Pymel, but we temporarily need them here

import pymel.mayahook as mayahook
from allapi import *
from maya.cmds import ls as _ls
#import pymel.factories as _factories

import sys, inspect, warnings, timeit, time, re
from pymel.util import Singleton, metaStatic, expandArgs, Tree, FrozenTree, IndexedFrozenTree, treeFromDict
import pymel.util as util
import pickle, os.path
import pymel.util.nameparse as nameparse
import pymel.mayahook as mayahook
from HTMLParser import HTMLParser

# TODO : would need this shared as a Singleton class, but importing from pymel.mayahook.factories anywhere 
# except form core seems to be a problem
#from pymel.mayahook.factories import NodeHierarchy

print "module name", __name__
_thisModule = sys.modules[__name__]
#_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

Enum = util.namedtuple( 'Enum', ['parent', 'enum'] )

class Enum(tuple):
    def __str__(self): return '.'.join( [str(x) for x in self] )

class ApiDocParser(HTMLParser):

    def getClassFilename(self):
        # Need to check the name format for versions other than 2008 and
        # 2009... I'm just assuming for now that they're more likely to be the
        # 2008 format than the 2009 format
        if self.version in ('7.0', '8.0', '8.5', '2008'):
            filename = self.functionSet
        else:
            filename = 'class'
            for tok in re.split( '([A-Z][a-z]+)', self.functionSet ):
                if tok:
                    if tok[0].isupper():
                        filename += '_' + tok.lower()
                    else:
                        filename += tok
        return filename
        
    def parse(self):
        docloc = mayahook.mayaDocsLocation(self.version)
        if not os.path.isdir(docloc):
            raise TypeError, "Cannot find maya documentation. Expected to find it at %s" % docloc
        f = open( os.path.join( docloc , 'API', self.getClassFilename() + '.html' ) )
        self.feed( f.read() )
        f.close()
        
        self.processData()
        #for method, methodInfo in self.methods.items():
        #    print method
        #    for methodOption in methodInfo:
        #        print methodOption
        
        # convert from defaultdict
        
        pymelEnums = {}     
        # remove common prefixes. convert from:
        # ['kTangentGlobal', 'kTangentFixed', 'kTangentLinear', 'kTangentFlat', 'kTangentSmooth', 'kTangentStep', 'kTangentSlow', 'kTangentFast', 'kTangentClamped', 'kTangentPlateau', 'kTangentStepNext']
        # to:
        # ['Global', 'Fixed', 'Linear', 'Flat', 'Smooth', 'Step', 'Slow', 'Fast', 'Clamped', 'Plateau', 'StepNext']
        from keyword import iskeyword as _iskeyword
        for enumName, enumList in self.enums.items():
            if len(enumList) > 1:
                splitEnums = [ [ y for y in re.split( '([A-Z][a-z0-9]*)', x ) if y ] for x in enumList ]
                splitEnumsCopy = splitEnums[:]
                for partList in zip( *splitEnumsCopy ):
                    if  tuple([partList[0]]*len(partList)) == partList:
                        [ x.pop(0) for x in splitEnums ]
                    else: break
                joinedEnums = [ util.uncapitalize(''.join(x)) for x in splitEnums]
                for i, enum in enumerate(joinedEnums):
                    if _iskeyword(enum):
                        joinedEnums[i] = enum+'_'
                        print "enums", enumName
                        print joinedEnums
                        print enumList
                        break
                    
                #joinedEnums = [ ''.join(x) for x in splitEnums]
#                for enum in joinedEnums:
#                    if enum in ['None' , 'True', 'False']:
#                        print "enums", enumName
#                        print joinedEnums
#                        print enumList
#                        break
                
                pymelEnums[enumName] = joinedEnums
            else:
                pymelEnums[enumName] = enumList
        # add the "pymelName" : 
        # api retrieval names are often named something like fooBar, while pymel retreival methods are getFooBar.
        allFnMembers = self.methods.keys()
        pymelNames = {}
        for member in allFnMembers:
            if len(member) > 4 and member.startswith('set') and member[3].isupper():
                # MFn api naming convention usually uses setValue(), value() convention for its set and get methods, respectively
                # 'setSomething'  -->  'something'
                origGetMethod = member[3].lower() + member[4:]
                if origGetMethod in allFnMembers:
                    newGetMethod = 'get' + member[3:]
                    pymelNames[origGetMethod] = newGetMethod
                    for info in self.methods[origGetMethod]:
                        info['pymelName'] = newGetMethod 
                        
        return { 'methods' : dict(self.methods), 
                 'enums' : dict(self.enums),
                 'pymelEnums' : pymelEnums,
                 'pymelMethods' :  pymelNames
                }
              
    def __init__(self, functionSet, version=None, verbose=False ):
        self.cmdList = []
        self.functionSet = functionSet

        if version is None:
            version = mayahook.getMayaVersion()
        self.version = version
        
        self.methods = util.defaultdict(list)
        self.currentMethod = None
        
        self.mode = None
        self.grouping = None
        self.data = []
        self.parameters = []
        self.returnType = []
        self.defaults = {}
           
        self.enums = util.defaultdict(list)
        self.currentEnum = None
        self.badEnums = []
        
        self.verbose = verbose
        HTMLParser.__init__(self)
        
    def handle_data(self, data):
        data = data.lstrip().rstrip()
        #data = data.replace( '&amp;', '&' )
        
        if data in [ 'Protected Member Functions', 
                      'Member Enumeration Documentation', 
                      'Constructor Destructor Documentation', 
                      'Member Function Documentation',
                      'Public Types',
                      'Member Enumeration Documentation' ]:
            #print self.currentMethod, data
            self.grouping = data
            
        elif self.currentMethod is not None and data:
            #print self.grouping, self.mode
            if data in ['Reimplemented from', 'Parameters:', 'Returns:' ]:
                self.mode = data
                
            elif self.mode == 'Parameters:':
                if data in ['[in]', '[out]']:
                    self.parameters.append( [data[1:-1], None, ''] ) # direction
                elif self.parameters[-1][1] == None:
                    self.parameters[-1][1] = data
                else:
                    self.parameters[-1][2] += data
                    
                    
            elif self.mode == 'Returns:':
                self.returnType.append( data )
                
            elif self.mode == 'Reimplemented from':
                pass
            
            elif self.grouping == 'Member Function Documentation':
                #print data
                #print self.currentMethod, "adding data", data
                if data.startswith('()'):
                    buf = data.split()
                    self.data.extend( ['(', ')'] + buf[1:] )
                elif data.endswith( ')' ):
                    self.data.append( data[:-1] )
                    self.data.append( ')')
                else:
                    self.data.append(data)
            
        elif self.grouping == 'Public Types':
            #print data
            # the enum name
            if re.match( '[A-Z]+[a-zA-Z0-9]*', data ):
                self.currentEnum = data
            # enum entry
            elif re.match( 'k[a-zA-Z]+[a-zA-Z0-9]*', data ):
                if self.currentEnum:
                    self.enums[self.currentEnum].append( data )
            
                #print data
            #elif 'Protected' in data:
            #    print "data1", data
    def processData(self):
        def handleEnums( type ):
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
            # the enum is on another class
            if '::' in type:
                type = Enum( type.split( '::') )
                
            # the enum is on this class
            elif type in self.enums:
                type = Enum( [self.functionSet, type] )
                
            elif type[0].isupper() and 'Ptr' not in type and not hasattr( _thisModule, type ) and type not in otherTypes+missingTypes+notTypes:
                type = Enum( [self.functionSet, type] )
                if type not in self.badEnums:
                    self.badEnums.append(type)
                    if self.verbose: print "Suspected Bad Enum:", type
                
            return type
        if self.currentMethod is not None:
            if self.verbose: print self.currentMethod
            
            #print self.data
            try:
                start = self.data.index( '(' )
                end = self.data.index( ')' )
            except ValueError:
                raise ValueError, '%s: could not find parentheses: %s, %r' % ( self.functionSet, self.currentMethod, self.data )
            buf = ' '.join( self.data[:start] ).split()[:-1] # remove last element, the method name          
            returnType = None
            
            if len(buf) and 'no script support.' not in [ x.lower() for x in self.data[end+1:]] :

                #-----------------
                # Return Type
                #-----------------
                if len(buf)>1:
                    #if buf[0] == self.functionSet: print self.currentMethod, "returnBuf", buf
                    # unsigned int
                    if buf[0] in ['const', 'unsigned']:
                        buf.pop(0)
                    
                    if len(buf)==1:    
                        returnType = buf[0]
                    elif len(buf)==2 and buf[1]=='*':
                        returnType = buf[0] + 'Ptr'
                    #else:  print "%s: could not determine %s return value: got list: %s" % ( self.functionSet, self.currentMethod, buf)
                else:
                    returnType = handleEnums(buf[0])
                        
                if returnType == 'MStatus':
                    returnType = None
                    
                #-----------------
                # Static
                #-----------------
                static = False
                try:
                    if self.data[end+1:][0] == '[static]':
                        static = True
                except IndexError: pass
                
                
                
                #print tempargs
                argList = []
                argInfo = util.defaultdict(dict)
                inArgs = []
                outArgs = []
                
                # Find Direction and Docs
                direction = None
                argName = None
                doc = ''
                

                #print self.currentMethod, buf, self.parameters #, self.defaults

                #---------------------
                # Docs and Direction
                #---------------------
                
                # self.parameters looks like:
                # [  ['[in]', 'node', 'node to check'],  ['[out]', 'ReturnStatus', 'Status Code (see below)']  ]
                
                if self.verbose: print "parameters",self.parameters
                
                for direction, argName, doc in self.parameters: 
                    # A better way would be if we knew the type already, but we don't
                    if argName not in ['ReturnStatus', 'status', 'retStatus', 'ret', 'stat', 'ResultStatus']:
                        argInfo[ argName ]['doc'] = doc
                        if direction == 'in': inArgs.append(argName)
                        elif direction == 'out': outArgs.append(argName)
                                           
                
                
                #------------------------
                # Arg Type and Defaults
                #------------------------
                tempargs = ' '.join( self.data[start+1:end] )
                
                methodDoc = ''
                defaults = {}
                for argGrp in tempargs.split(','):
                    
                    argGrp = [ y for y in argGrp.split() if y not in [ '*', 'const', '=', 'unsigned'] ]
                    
                    
                    if len(argGrp):
                        

                        type = argGrp[0]
                        if type in 'MStatus':
                            continue
                        
                        try:
                            keyword = argGrp[1]
                            
                        except IndexError:
                            # void
                            #print "something wrong with argGrp", argGrp
                            continue
                        else:

                            #----------------
                            #    TYPE
                            #----------------
                            try:
                                # move array length from keyword to type:
                                # keyword[3] ---> keyword
                                # type       ---> type3 
                                tmp = argGrp[2]
                                
                                buf = re.split( r'\[|\]', tmp)
                                if len(buf) > 1:
                                    
                                    type = type + buf[1]
                                    default = None
                                else:     
                                            
                                    default = {
                                        'true' : True,
                                        'false': False
                                    }.get( tmp, tmp )
                                    
                            except IndexError:
                                default = None
                              
                            # Enum Types
                            type = handleEnums( type )
                                
                            argInfo[ keyword ]['type'] = type
                            argInfo[ 'types' ][keyword] = type
                            
                            #----------------
                            #    DEFAULT
                            #----------------
                            if default is not None:
                                
                                # Enums
                                if isinstance( default, basestring ) and '::' in default:
                                    default = default.split('::')[-1]
                                    
                                #argInfo[ keyword ]['default'] = default
                                #argInfo[ 'defaults' ][keyword] = default
                                defaults[keyword] = default
                                
                            if keyword in inArgs:
                                #try:
                                #    typeName = returnCast[type].__name__
                                #except KeyError:
                                #    typeName = type
                                direction = 'in'
                                methodDoc += ':param %s: %s\n' % ( keyword, argInfo[keyword].get('doc', '') )
                                methodDoc += ':type %s: %s\n' % ( keyword, type )
                                argInfo[keyword]['doc'] = doc
                            else: 
                                direction = 'out'
                            
                            #print self.currentMethod, [keyword, type, default, direction]
                            argList.append( ( keyword, type, default, direction)  )
                                
                    elif len(argGrp)==1:
                        print "arg group lenght is 1:", argGrp
                
                # return type documentation
                allReturnTypes = []
                if returnType:
                    allReturnTypes.append( returnType )
                if outArgs:
                    allReturnTypes += [  argInfo[ 'types' ][x] for x in outArgs ]
                    
                if allReturnTypes:
                    methodDoc += ':rtype: %s' % ','.join( [ str(x) for x in allReturnTypes] )
                #elif self.currentMethod.startswith( 'get' ) and len(self.currentMethod) > 3:
                #    print "no outputs", self.functionSet, self.currentMethod, len(self.methods[self.currentMethod])
                
                #print argList, argInfo
                methodInfo = { 'argInfo': argInfo, 
                              'args' : argList, 
                              'returnType' : returnType, 
                              'inArgs' : inArgs, 
                              'outArgs' : outArgs, 
                              'doc' : methodDoc, 
                              'defaults' : defaults,
                              'static' : static } 
                self.methods[self.currentMethod].append(methodInfo)
            
            self.mode = None
            self.data = []
            self.parameters = []
            self.returnType = []
    
    def handle_comment(self, comment ):
                                
        comment = comment.lstrip().rstrip()
        comment = comment.replace( '&amp;', '' ) # does not affect how we pass
        self.processData()
        #print comment    
        try:     
            clsname, methodname, op, tempargs  = re.search( r'doxytag: member="([a-zA-Z0-9]+)::([a-zA-Z0-9]+\s*([=!*/\-+\[\]])*)" ref="[0-9a-f]+" args="\((.*)\)', comment ).groups()
        except AttributeError:
            pass
            if self.verbose: print "failed regex: ", comment
        else:
            #if methodname == self.functionSet:
            #    return
            
            #print "METHOD", methodname
            if self.grouping != 'Member Function Documentation':
                if self.verbose: print "not a member function: %s (%s)" % ( methodname, self.grouping )
                self.currentMethod = None
                return
            
            if op: #methodname.startswith('operator'):
                #op = methodname[8:]
                #print op
                if op == '=':
                    self.currentMethod = None
                else:
                    
                    self.currentMethod = { 
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
#                    if pymelName:
#                        for info in self.methods[self.currentMethod]:
#                            info['pymelName'] = pymelName 
#                    else:
#                        print "could not determine pymelName for operator %s" % op
            if self.verbose: print "new method", methodname
            self.currentMethod = methodname
            
            
def getMFnInfo( functionSet ):
    parser = ApiDocParser(functionSet )
    try:
        classInfo = parser.parse()
    except IOError: pass  
    else:

        
#        for methodName, methodInfoList in classInfo['methods'].items():
#              for i, methodInfo in enumerate( methodInfoList ):
#                  #try: print methodInfo['pymelName'], methodName
#                  #except: pass
#                  newMethodName = methodInfo.get('pymelName', methodName)
#                  if newMethodName.startswith('get') and len(newMethodName)>3:              
#                      outputs = []
#                      returnType = methodInfo['returnType']
#                      if returnType:
#                          outputs.append( returnType )
#                      outputs += methodInfo['outArgs']
#                      if not outputs:
#                           print "no outputs", functionSet, methodName, i 
        return classInfo




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



class ApiTypesToApiEnums(Singleton, dict) :
    """Lookup of Maya API types to corresponding MFn::Types enum"""
    
class ApiEnumsToApiTypes(Singleton, dict) :
    """Lookup of MFn::Types enum to corresponding Maya API types"""

class ApiTypesToApiClasses(Singleton, dict) :
    """Lookup of Maya API types to corresponding MFnBase Function sets"""
    
# Reserved Maya types and API types that need a special treatment (abstract types)
# TODO : parse docs to get these ? Pity there is no kDeformableShape to pair with 'deformableShape'
# strangely createNode ('cluster') works but dgMod.createNode('cluster') doesn't

# added : filters them to weed out those not present in current version

#class ReservedMayaTypes(dict) :
#    __metaclass__ =  metaStatic
## Inverse lookup
#class ReservedApiTypes(dict) :
#   

class ReservedMayaTypes(Singleton, dict) : pass
class ReservedApiTypes(Singleton, dict) : pass
    
def _buildMayaReservedTypes():
    """ Build a list of Maya reserved types.
        These cannot be created directly from the API, thus the dgMod trick to find the corresonding Maya type won't work """
        
    reservedTypes = { 'invalid':'kInvalid', 'base':'kBase', 'object':'kNamedObject', 'dependNode':'kDependencyNode', 'dagNode':'kDagNode', \
                'constraint':'kConstraint', 'field':'kField', \
                'geometryShape':'kGeometric', 'shape':'kShape', 'deformFunc':'kDeformFunc', 'cluster':'kClusterFilter', \
                'dimensionShape':'kDimension', \
                'abstractBaseCreate':'kCreate', 'polyCreator':'kPolyCreator', \
                'polyModifier':'kMidModifier', 'subdModifier':'kSubdModifier', \
                'curveInfo':'kCurveInfo', 'curveFromSurface':'kCurveFromSurface', \
                'surfaceShape': 'kSurface', 'revolvedPrimitive':'kRevolvedPrimitive', 'plane':'kPlane', 'curveShape':'kCurve', \
                'animCurve': 'kAnimCurve', 'resultCurve':'kResultCurve', 'cacheBase':'kCacheBase', 'filter':'kFilter',
                'blend':'kBlend', 'ikSolver':'kIkSolver', \
                'light':'kLight', 'nonAmbientLightShapeNode':'kNonAmbientLight', 'nonExtendedLightShapeNode':'kNonExtendedLight', \
                'texture2d':'kTexture2d', 'texture3d':'kTexture3d', 'textureEnv':'kTextureEnv', \
                'plugin':'kPlugin', 'pluginNode':'kPluginDependNode', 'pluginLocator':'kPluginLocatorNode', 'pluginData':'kPluginData', \
                'pluginDeformer':'kPluginDeformerNode', 'pluginConstraint':'kPluginConstraintNode', \
                'unknown':'kUnknown', 'unknownDag':'kUnknownDag', 'unknownTransform':'kUnknownTransform',\
                'xformManip':'kXformManip', 'moveVertexManip':'kMoveVertexManip' }      # creating these 2 crash Maya      

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
                   
class MayaTypesToApiTypes(Singleton, dict) :
    """ Lookup of currently existing Maya types as keys with their corresponding API type as values.
    Not a read only (static) dict as these can change (if you load a plugin)"""


class ApiTypesToMayaTypes(Singleton, dict) :
    """ Lookup of currently existing Maya API types as keys with their corresponding Maya type as values.
    Not a read only (static) dict as these can change (if you load a plugin)
    In the case of a plugin a single API 'kPlugin' type corresponds to a tuple of types )"""

#: lookup tables for a direct conversion between Maya type to their MFn::Types enum
class MayaTypesToApiEnums(Singleton, dict) :
    """Lookup from Maya types to API MFn::Types enums """

#: lookup tables for a direct conversion between API type to their MFn::Types enum 
class ApiEnumsToMayaTypes(Singleton, dict) :
    """Lookup from API MFn::Types enums to Maya types """

 
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
    except:
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
            try :
                parent = dagMod.createNode ( 'transform', MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
             
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
    
    
    
def updateMayaTypesList() :
    """Updates the cached MayaTypes lists. Not currently used. """
    start = time.time()
    # use dict of empty keys just for faster random access
    # the nodes returned by ls will be added by createPyNodes and pluginLoadedCB
    typeList = dict( ReservedMayaTypes().items() + [(k, None) for k in _ls(nodeTypes=True)] )
    # remove types that no longuer exist
    for k in MayaTypesToApiTypes().keys() :
        if not typeList.has_key(k) :
            # this could happen when a plugin is unloaded and some types become unregistered
            api = MayaTypesToApiTypes()[k]
            mtypes = ApiTypesToMayaTypes()[api]
            mtypes.pop(k)
            MayaTypesToApiTypes().pop(k)
    # add new types
    for k in typeList.keys() :
         if not MayaTypesToApiTypes().has_key(k) :
            # this will happen for initial building and when a plugin is loaded that registers new types
            api = typeList[k]
            if not api :
                api = mayaTypeToApiType(k)
            MayaTypesToApiTypes()[k] = api
            # can have more than one Maya type associated with an API type (yeah..)
            # we mark one as "default" if it's a member of the reserved type by associating it with a True value in dict
            defType = ReservedMayaTypes().has_key(k)
            if not ApiTypesToMayaTypes().has_key(api) :
                ApiTypesToMayaTypes()[api] = { k : defType } #originally: dict( ((k, defType),) )
            else :
                ApiTypesToMayaTypes()[api][k] = defType
    elapsed = time.time() - start
    print "Updated Maya types list in %.2f sec" % elapsed

            
# initial update  
#updateMayaTypesList()
       

def _getMObject(nodeType, dagMod, dgMod) :
    """ Returns a queryable MObject form a give apiType """
    
    if type(dagMod) is not MDagModifier or type(dgMod) is not MDGModifier :
        raise ValueError, "Need a valid MDagModifier and MDGModifier or cannot return a valid MObject"
    # cant create these nodes, some would crahs MAya also
    if ReservedApiTypes().has_key(nodeType) or ReservedMayaTypes().has_key(nodeType) :
        return None   
    obj = MObject()
    if ApiTypesToMayaTypes().has_key(nodeType) :
        mayaType = ApiTypesToMayaTypes()[nodeType].keys()[0]
        apiType = nodeType
    elif MayaTypesToApiTypes().has_key(nodeType) :
        mayaType = nodeType
        apiType = MayaTypesToApiTypes()[nodeType]
    else :
        return None    
      
    try :
        parent = dagMod.createNode ( 'transform', MObject())
        obj = dagMod.createNode ( mayaType, parent )
    except :
        try :
            obj = dgMod.createNode ( mayaType )
        except :
            pass
    if isValidMObject(obj) :
        return obj
    else :
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
    # we create a dummy object of this type in a dgModifier
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
    obj = _getMObject(apiType, dagMod, dgMod, parentType) 
    if isValidMObject(obj) :
        return obj.hasFn(typeInt)
    else :
        return False
 

# Filter the given API type list to retain those that are parent of apiType
# can pass a list of types to check for being possible parents of apiType
# or a dictionnary of types:node to speed up testing
def _parentFn (apiType, dagMod=None, dgMod=None, *args, **kwargs) :
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
    # we create a dummy object of this type in a dgModifier
    # as the dgModifier.doIt() method is never called, the object
    # is never actually created in the scene
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
    for mayaType in args :
#        mayaType = apiType = None
#        if ApiTypesToMayaTypes().has_key(k) :
#            mayaType = ApiTypesToMayaTypes()[k].keys()[0]
#            apiType = k
#        elif MayaTypesToApiTypes().has_key(k) :
#            mayaType = k
#            apiType = MayaTypesToApiTypes()[k]
#        else :
#            continue
#        print mayaType, apiType
        if ReservedMayaTypes().has_key(mayaType) :
            apiType = ReservedMayaTypes()[mayaType]
            print "reserved", mayaType, apiType
            mayaResult[mayaType] = apiType
            result[apiType] = None
      
        else :
            obj = MObject()          
            try :
                # DagNode
                parent = dagMod.createNode ( 'transform', MObject())
                obj = dagMod.createNode ( mayaType, parent )
            except :
                # DependNode
                try :
                    obj = dgMod.createNode ( mayaType )
                except :
                    pass
            if isValidMObject(obj) :
                apiType = obj.apiTypeStr()
                mayaResult[mayaType] = apiType
                result[apiType] = obj
    #            else :
    #                result[apiType] = None
    return result, mayaResult

# child:parent lookup of the Maya API classes hierarchy (based on the existing MFn class hierarchy)
# TODO : fix that, doesn't accept the Singleton base it seems
# class ApiTypeHierarchy(Singleton, FrozenTree) :
#    """ Hierarchy Tree of all API Types """

def _buildApiTypesList():
    """the list of api types is static.  even when a plugin registers a new maya type, it will be associated with 
    an existing api type"""
    
    global ApiTypesToApiEnums, ApiEnumsToApiTypes
    
    ApiTypesToApiEnums( dict( inspect.getmembers(MFn, lambda x:type(x) is int)) )
    ApiEnumsToApiTypes( dict( (ApiTypesToApiEnums()[k], k) for k in ApiTypesToApiEnums().keys()) )

    #apiTypesToApiEnums = dict( inspect.getmembers(MFn, lambda x:type(x) is int)) 
    #apiEnumsToApiTypes = dict( (ApiTypesToApiEnums()[k], k) for k in ApiTypesToApiEnums().keys()) 
    #return apiTypesToApiEnums, apiEnumsToApiTypes
    
# Initialises MayaTypes for a faster later access
def _buildMayaTypesList() :
    """Updates the cached MayaTypes lists """
    start = time.time()

    # api types/enums dicts must be created before reserved type bc they are used for filtering
    _buildMayaReservedTypes()
    
    # use dict of empty keys just for faster random access
    # the nodes returned by ls will be added by createPyNodes and pluginLoadedCB
    # add new types
    print "reserved types", ReservedMayaTypes()
    for mayaType, apiType in ReservedMayaTypes().items() + [(k, None) for k in _ls(nodeTypes=True)]:
         #if not MayaTypesToApiTypes().has_key(mayaType) :
         addMayaType( mayaType, apiType )
    elapsed = time.time() - start
    print "Updated Maya types list in %.2f sec" % elapsed


# Build a dictionnary of api types and parents to represent the MFn class hierarchy
def _buildApiTypeHierarchy () :
    def _MFnType(x) :
        if x == MFnBase :
            return ApiEnumsToApiTypes()[ 1 ]
        else :
            try :
                return ApiEnumsToApiTypes()[ x().type() ]
            except :
                return ApiEnumsToApiTypes()[ 0 ]
    
    #global apiTypeHierarchy, ApiTypesToApiClasses
    _buildMayaReservedTypes()
    
    allMayaTypes = ReservedMayaTypes().keys() + _ls(nodeTypes=True)
    
    apiTypesToApiClasses = {}
    
    # all of maya OpenMaya api is now imported in module api's namespace
    MFnClasses = inspect.getmembers(_thisModule, lambda x: inspect.isclass(x) and issubclass(x, MFnBase))
    MFnTree = inspect.getclasstree( [x[1] for x in MFnClasses] )
    MFnDict = {}
    
    for x in expandArgs(MFnTree, type='list') :
        try :
            MFnClass = x[0]
            ct = _MFnType(MFnClass)
            pt = _MFnType(x[1][0])
            if ct and pt :
                apiTypesToApiClasses[ ct ] = MFnClass
                #ApiTypesToApiClasses()[ ct ] = x[0]
                MFnDict[ ct ] = pt

        except IndexError:
            pass
    
    apiClassInfo = {}
    for name, obj in inspect.getmembers( _thisModule, lambda x: type(x) == type and x.__name__.startswith('M') ):
        if not name.startswith( 'MPx' ):
            try:
                info = getMFnInfo( name )
                if info is not None:
                    #print "succeeded", name
                    apiClassInfo[ name ] = info
            except (ValueError,IndexError), msg:
                print "failed", name, msg
                    
    # print MFnDict.keys()
    # Fixes for types that don't have a MFn by faking a node creation and testing it
    # Make it faster by pre-creating the nodes used to test
    dagMod = MDagModifier()
    dgMod = MDGModifier()      
    #nodeDict = _createNodes(dagMod, dgMod, *ApiTypesToApiEnums().keys())
    nodeDict, mayaDict = _createNodes( dagMod, dgMod, *allMayaTypes )
    
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

def _buildApiCache():
    #print ApiTypesToApiEnums()
    #print ApiTypesToApiClasses()
    #global ReservedMayaTypes, ReservedApiTypes, ApiTypesToApiEnums, ApiEnumsToApiTypes, ApiTypesToApiClasses, apiTypeHierarchy
    
    #global ReservedMayaTypes, ReservedApiTypes, ApiTypesToApiEnums, ApiEnumsToApiTypes, ApiTypesToApiClasses#, apiTypeHierarchy
         
    ver = mayahook.getMayaVersion(extension=False)

    cacheFileName = os.path.join( util.moduleDir(),  'mayaApi'+ver+'.bin'  )
    try :
        file = open(cacheFileName, mode='rb')
        #try :
        #ReservedMayaTypes, ReservedApiTypes
        #ApiTypesToApiEnums, ApiEnumsToApiTypes, ApiTypesToApiClasses, apiTypeHierarchy = pickle.load(file)
        data = pickle.load(file)
        #ReservedMayaTypes, ReservedApiTypes, ApiTypesToApiEnums, ApiEnumsToApiTypes, ApiTypesToApiClasses, apiTypeHierarchy = data
        #print "unpickled", ApiTypesToApiClasses
        #return data
        #print data
        ReservedMayaTypes(data[0])
        ReservedApiTypes(data[1])
        ApiTypesToApiEnums(data[2])
        ApiEnumsToApiTypes(data[3])
        MayaTypesToApiTypes(data[4])
        apiTypesToApiClasses = data[5]
        ApiTypesToApiClasses(data[5])
        apiTypeHierarchy = data[6]
        apiClassInfo = data[7]
        return apiTypeHierarchy, apiClassInfo
            
        #except:
        #    print "Unable to load the Maya API Hierarchy from '"+file.name+"'"       
        file.close()
    except (IOError, OSError, IndexError):
        print "Unable to open '"+cacheFileName+"' for reading the Maya API Hierarchy"
    
    print "Rebuilding the API Caches..."
    
    # fill out the data structures
    _buildApiTypesList()
    #apiTypesToApiEnums, apiEnumsToApiTypes = _buildApiTypesList()
    #_buildMayaTypesList()
    apiTypeHierarchy, apiTypesToApiClasses, apiClassInfo = _buildApiTypeHierarchy()
    #_buildApiTypeHierarchy()
    
    
    
    #ApiTypesToApiClasses( apiTypesToApiClasses )

    try :
        file = open(cacheFileName, mode='wb')
        try :
            #print "about to pickle", apiTypesToApiClasses
            #print "about to pickle", ApiEnumsToApiTypes()
            pickle.dump( (ReservedMayaTypes(), ReservedApiTypes(), ApiTypesToApiEnums(), ApiEnumsToApiTypes(), MayaTypesToApiTypes(), 
                          apiTypesToApiClasses, apiTypeHierarchy, apiClassInfo),
                            file, 2)
            print "done"
        except:
            print "Unable to write the Maya API Cache to '"+file.name+"'"
        file.close()
    except :
        print "Unable to open '"+cacheFileName+"' for writing"
    
    return apiTypeHierarchy, apiClassInfo   
    #return ReservedMayaTypes, ReservedApiTypes, ApiTypesToApiEnums, ApiEnumsToApiTypes, apiTypesToApiClasses, apiTypeHierarchy

# Initialize the API tree
# ApiTypeHierarchy(_buildApiTypeHierarchy())
# initial update  
start = time.time()
# ApiTypeHierarchy(_buildApiTypeHierarchy())
#_buildApiCache()
apiTypeHierarchy, apiClassInfo = _buildApiCache()
#apiTypesToApiClasses, apiTypeHierarchy = _buildApiCache()
#ReservedMayaTypes, ReservedApiTypes, ApiTypesToApiEnums, ApiEnumsToApiTypes, apiTypesToApiClasses, apiTypeHierarchy = _buildApiCache()
# quick fix until we can get a Singleton ApiTypeHierarchy() up

elapsed = time.time() - start
print "Initialized API Cache in in %.2f sec" % elapsed

# TODO : to represent plugin registered types we might want to create an updatable (dynamic, not static) MayaTypesHierarchy ?

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
    return ApiTypesToApiEnums().get(apiType, None)

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
#            >>> obj = api.toMObject ('pCubeShape1')
#            >>> api.objType (obj, api=True, inherited=True)
#            >>> # Result: ['kBase', 'kDependencyNode', 'kDagNode', 'kMesh'] #
#            >>> api.objType (obj, api=False, inherited=True)
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
#            fn = api.MFnDagNode(dag)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, api.MPlug ):
#                        result = result.child( fn.attribute( token ) )
#                    else:
#                        try:
#                            result = fn.findPlug( token )
#                        except TypeError:
#                            for i in range(fn.childCount()):
#                                try:
#                                    result = api.MFnDagNode( fn.child(i) ).findPlug( token )
#                                except TypeError:
#                                    pass
#                                else:
#                                    break
#                if isinstance( token, nameparse.NameIndex ):
#                    result = result.elementByLogicalIndex( token.value )
#            if dagMatters:
#                result = (dag, result)
#        else:
#            fn = api.MFnDependencyNode(obj)
#            for token in nameTokens[1:]: # skip the first, bc it's the node, which we already have
#                if isinstance( token, nameparse.MayaName ):
#                    if isinstance( result, api.MPlug ):
#                        result = result.child( fn.attribute( token ) )
#                    else:
#                        result = fn.findPlug( token )
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
    
    
