from pymel import *
from pymel.tools.pymelControlPanel import getApiClassName, getClassHierarchy

def getFundamentalTypes():
    classList = sorted( list( set( [ key[0] for key in api.apiToMelData.keys()] ) ) )
    leaves = [ util.capitalize(x.key) for x in factories.nodeHierarchy.leaves() ]
    return sorted( set(classList).intersection(leaves) )

EXCEPTIONS = ['MotionPath']
  
def testInvertibles():
    classList = getFundamentalTypes()
    print classList
    for pynodeName in classList:
        try:
            pynode = getattr( core.nodetypes, pynodeName )
        except AttributeError:
            print "could not find", pynodeName
            continue
        if not issubclass( pynode, PyNode ) or pynodeName in EXCEPTIONS:
            continue
        
        for pymelClassName, apiClassName in getClassHierarchy(pynodeName):
            if apiClassName not in api.apiClassInfo:
                continue
            classInfo = api.apiClassInfo[apiClassName]
            invertibles = classInfo['invertibles']

            obj = createNode( util.uncapitalize(pynodeName) )
            print repr(obj)
                            
            for setMethod, getMethod in invertibles:
                info = classInfo['methods'][setMethod]
                try:
                    setMethod = info[0]['pymelName']
                except KeyError: pass
                setMethod, data = factories._getApiOverrideNameAndData( pynodeName, setMethod )
                try:
                    overloadIndex = data['overloadIndex']
                    info = info[overloadIndex]
                except (KeyError, TypeError): pass
                else:
                    try:
                        setter = getattr( pynode, setMethod )                      
                    except AttributeError: pass
                    else:
                        typeMap = {   'bool' : True,
                            'double' : 0.5,
                            'float': 0.5,
                            'MFloatArray': [1.1, 2.2, 3.3],
                            'MString': 'thingie',
                            'float2': (.1, .2),
                            'MPoint' : [1,2,3],
                            'short': 1,
                            'MColor' : [1,0,0],
                            'MColorArray': ( [1,0,0], [0,1,0] ),
                            'MVector' : [1,0,0],
                            'MVectorArray': ( [1,0,0], [0,1,0] ),
                            'int' : 1,
                            'MIntArray': [1,2,3],
                            'MSpace.Space' : 'world'
                        }
                        
                        inArgs = [ arg for arg in info['inArgs'] if arg not in info['defaults'] ]
                        types = [ info['types'][arg] for arg in inArgs ]
                        try:
                            args = [ typeMap[typ] for typ in types ]
                            print pynodeName, setMethod, getMethod, args
                            try:
                                setter( obj, *args )
                            except Exception, e:
                                print str(e)
                        except KeyError, msg:
                            print str(msg)
            
            delete( obj )

                    #print types
