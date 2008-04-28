
import pymel
import pymel.util.factories as _factories
import maya.cmds as cmds

def testNodeCmds(verbose=False):

    emptyFunctions = []
    
    for funcName in _factories.nodeCommandList:
        print funcName.center( 50, '=')
        
        if funcName in [ 'character', 'lattice', 'boneLattice', 'sculpt', 'wire' ]:
            print "skipping"
            continue
            
        try:
            func = getattr(pymel, funcName)
        except AttributeError:
            continue
            
        try:
            cmds.select(cl=1)
            
            if funcName.endswith( 'onstraint'):
                s = cmds.polySphere()[0]
                c = cmds.polyCube()[0]
                obj = func(s,c)
            else:
                obj = func()
                if obj is None:
                    emptyFunctions.append( funcName )
                    raise ValueError, "Returned object is None"
            
        except (TypeError,RuntimeError, ValueError), msg:
            print "ERROR: failed creation:", msg

        else:
            #(func, args, data) = cmdList[funcName]    
            #(usePyNode, baseClsName, nodeName)
            args = _factories.cmdlist[funcName]['flags']

            if isinstance(obj, list):
                print "returns list"
                obj = obj[-1]

            for flag, flagInfo in args.items():            
                if flag in ['query', 'edit']:
                    continue
                
                
                try:
                    modes = flagInfo['modes']
                    testModes = False
                except KeyError, msg:
                    #raise KeyError, '%s: %s' % (flag, msg)
                    print flag, "Testing modes"
                    modes = []
                    testModes = True
                
                # QUERY
                val = None
                if 'query' in modes or testModes == True:
                    cmd = "%s('%s', query=True, %s=True)" % (func.__name__, obj,  flag)
                    try:
                        val = func( obj, **{'query':True, flag:True} )
                        #print val
                        if verbose:
                            print cmd
                            print "\tsucceeded: %s" % val
                    except TypeError, msg:                            
                        if str(msg).startswith( 'Invalid flag' ):
                            _factories.cmdlist[funcName]['flags'].pop(flag,None)
                        #else:
                        print cmd
                        print "\t", msg
                        val = None
                    except RuntimeError, msg:
                        print cmd
                        print "\t", msg    
                        val = None
                    else:
                         modes.append('query')
                # EDIT
                if 'edit' in modes or testModes == True:
                    argtype = flagInfo['args']
                    print "Args:", argtype
                    try:    
                        if val is None:

                            if isinstance( argtype, list ):
                                val = []
                                for typ in argtype:
                                    if type == str:
                                        val.append('persp')
                                    else:
                                        val.append( argtype(0) )
                            else:
                                if argtype == str:
                                    val = 'persp'
                                else:
                                    val = argtype(0)    
                                        
                        cmd =  "%s('%s', edit=True, %s=%s)" % (func.__name__, obj,  flag, val)
                        val = func( obj, **{'edit':True, flag:val} )
                        if verbose:
                            print cmd
                            print "\tsucceeded: %s" % val
                        #print "SKIPPING %s: need arg of type %s" % (flag, flagInfo['argtype'])
                    except TypeError, msg:                                                        
                        if str(msg).startswith( 'Invalid flag' ):
                            _factories.cmdlist[funcName]['flags'].pop(flag,None)
                        #else:
                        print cmd
                        print "\t", msg 
                    except RuntimeError, msg:
                        print cmd
                        print "\t", msg    
                    except KeyError:
                        print "UNKNOWN ARG:", argtype
                    else:
                        modes.append('edit')
    
    print "done"
    print emptyFunctions
