from pymel import *
from pymel.tools.pymelControlPanel import getApiClassName, getClassHierarchy

def getFundamentalTypes():
    classList = sorted( list( set( [ key[0] for key in api.apiToMelData.keys()] ) ) )
    leaves = [ util.capitalize(x.key) for x in factories.nodeHierarchy.leaves() ]
    return sorted( set(classList).intersection(leaves) )

EXCEPTIONS = ['MotionPath','OldBlindDataBase', 'TextureToGeom']
 

     
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

        if issubclass(pynode, GeometryShape):
            if pynode == Mesh :
                obj = polyCube()[0].getShape()
            elif pynode == Subdiv:
                obj = polyToSubdiv( polyCube()[0].getShape())[0].getShape()
            elif pynode == NurbsSurface:
                obj = sphere()[0].getShape()
            elif pynode == NurbsCurve:
                obj = circle()[0].getShape()
            else:
                print "skipping shape", pynode
                continue
        else:
            obj = createNode( util.uncapitalize(pynodeName) )
        
        print repr(obj)
    
        for className, apiClassName in getClassHierarchy(pynodeName):
            
            if apiClassName not in api.apiClassInfo:
                continue
            
            #print className, apiClassName
            
            classInfo = api.apiClassInfo[apiClassName]
            invertibles = classInfo['invertibles']
            #print invertibles
    
                            
            for setMethod, getMethod in invertibles:
                info = classInfo['methods'][setMethod]
                try:
                    setMethod = info[0]['pymelName']
                except KeyError: pass
                
                setMethod, data = factories._getApiOverrideNameAndData( className, setMethod )
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
                            'double' : 2.5, # min required for setFocalLength
                            'double3' : ( 1.0, 2.0, 3.0),
                            'MEulerRotation' : ( 1.0, 2.0, 3.0),
                            'float': 2.5,
                            'MFloatArray': [1.1, 2.2, 3.3],
                            'MString': 'thingie',
                            'float2': (.1, .2),
                            'MPoint' : [1,2,3],
                            'short': 1,
                            'MColor' : [1,0,0],
                            'MColorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0] ),
                            'MVector' : [1,0,0],
                            'MVectorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0] ),
                            'int' : 1,
                            'MIntArray': [1,2,3],
                            'MSpace.Space' : 'world'
                        }
                        
                        inArgs = [ arg for arg in info['inArgs'] if arg not in info['defaults'] ]
                        types = [ str(info['types'][arg]) for arg in inArgs ]
                        try:
                            args = [ typeMap[typ] for typ in types ]
                            descr =  '%s.%s(%s)' % ( pynodeName, setMethod, ', '.join( [ repr(x) for x in args] ) )
    #                            try:
    #                                setter( obj, *args )
    #                            except Exception, e:
    #                                print str(e)
                            args = [obj] + args
                            def checkSetter( setter, args ):
                                setter( *args )
                                mel.undo()
                            checkSetter.description = descr
                            yield checkSetter, setter, args
                        except KeyError, msg:
                            print str(msg)
        try: 
            delete( obj )
        except:
            pass
             


                    #print types
