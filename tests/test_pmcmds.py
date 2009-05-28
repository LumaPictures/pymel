#import unittest, sys
#
#import maya.cmds
#from testingutils import TestCaseExtended, setupUnittestModule
#import pymel.core.pmcmds as pmcmds
#
#class Mylist(object):
#    def __init__(self, list):
#        self.theList = list
#    def __iter__(self):
#        return self.theList.__iter__()
#    def __repr__(self):
#        return "Mylist(%s)" % repr(self.theList)
#    
##class Mystring(object):
##    def __init__(self, inputString):
##        self.theString = str(inputString)
##    def __str__(self):
##        return self.theString
##    def __repr__(self):
##        return "Mystring(%s)" % repr(self.theString)
#    
#
## If this is true, we will test that the maya cmds (not just the pymel commands!)
## fail / succeed when we expect them to... really, this is just informational
#testMayaCmds = False
#
## If this is true, (and testMayaCmd is True), then we will run tests
## to make sure that maya commands FAIL when we expect them to...
#testMayaFailures = True
#
#
#mayaTests_shouldPass = []
#mayaTests_shouldFail = []
#wrappedTests = []
#
#class TestWrappedCmds(TestCaseExtended):
#    def setUp(self):
#        import pymel
#        maya.cmds.file(f=True,new=True)
#        self.cubeTrans1, cubeShaper = pymel.polyCube()
#        self.cubeTrans2, cubeShaper = pymel.polyCube()
#        self.lists = {}
#        self.lists['transform'] = [self.cubeTrans1, self.cubeTrans2]
#        self.lists['attribute'] = [self.cubeTrans1.translateX, self.cubeTrans2.translateZ]
#        maya.cmds.connectAttr(str(self.cubeTrans1.scaleY), str(self.cubeTrans2.scaleZ))
#        self.lists['attribute2'] = [self.cubeTrans1.scaleY, self.cubeTrans2.scaleZ]
#
#        
#    @classmethod
#    def addTestsForCmd(cls, cmdName, typeOfArgs,  \
#                       mayaFailsOnCustomStrings=False, mayaFailsOnCustomLists=False, \
#                       mayaFailsOnCustomStringsInNormalLists=False, \
#                       numOfArgs=None, canTakeListArg=False, extraArgs=None, extraKwArgs=None):
#        '''
#        cmdName - name of the command to test (ie, we will be testing maya.cmds.cmdName and pymel.cmdName)
#        typeOfArgs - the type of the non-keyword arguments for the command (ie, transform, attribute, etc)
#        args - extra non-keyword args to pass to the command
#        
#        mayaFailsOnCustomStrings - if true, then maya.cmds.cmdName should fail when called with non-string objects,
#            and pymel.cmdName should handle it - test this
#        mayaFailsOnCustomLists -  if true, then maya.cmds.cmdName should fail when called with non-list sequences,
#            and pymel.cmdName should handle it - test this
#            Note - if BOTH mayaFailsOnCustomStrings and mayaFailsOnCustomLists are true, it will also test when
#            the command is fed a non-list sequence filled with non-string objects
#        mayaFailsOnCustomStringsInNormalLists - even if mayaFailsOnCustomStrings==True, then for some
#            reason, maya will generally SUCCEED on a customString in a normal list... change this to check that
#            maya FAILS in this case
#        canTakeListArg - if false, then the command will be fed multiple non-keyword args,
#            where each argument is a single object; if true, the command will ALSO be tested
#            with a single non-keyword argument, which is a sequence of objects (note that if
#            this is false, then the value of mayaFailsOnCustomLists is ignored)
#        numOfArgs - if numOfArgs is not None, then only feed in this many objects of the requested type
#            as non-keyword args to the command
#        extraArgs - other non-keyword args that will be passed into cmdName
#        extraKwArgs - other keyword args that will be passed into cmdName
#        '''
#
#        if extraArgs==None: extraArgs = []
#        if extraKwArgs==None: extraKwArgs = {}
##         print extraArgs
##         print extraKwArgs
#        
#        mayaCmd = getattr(maya.cmds, cmdName)
#        wrappedCmd = getattr(pmcmds, cmdName)
#
#        # possible arg formats:
#        # 1. cmdName(arg1String, arg2String)
#        # 2. cmdName(arg1PyNode, arg2Pynode)
#        # 3. cmdName([arg1String, arg2String])
#        # 4. cmdname([arg1PyNode, arg2Pynode])
#        # 5. cmdname(Mylist([arg1String, arg2String]))
#        # 6. cmdname(Mylist([arg1PyNode, arg2Pynode]))
#        
#        def addTestPair(mayaCmdWillFail=True, testPyNodes=False, useListArg=False, testCustomLists=False):
#            nameSuffixList = [typeOfArgs]
#            if testPyNodes:
#                nameSuffixList.append("PyNodes")
#            else:
#                nameSuffixList.append("normalStrings")
#            if useListArg:
#                nameSuffixList.append("in")
#                if testCustomLists:
#                    nameSuffixList.append("customList")
#                else:
#                    nameSuffixList.append("normalList")
#
#            def feedArgs(function):
#                '''Decorator used to feed in the appropriate args to the test function.'''
#                def methodWithAutomaticArgs(self):
#                    args = self.getArgs(typeOfArgs,
#                                        numOfArgs,
#                                        testPyNodes,
#                                        useListArg,
#                                        testCustomLists,
#                                        *extraArgs)
##                    print "self: %s" % self
##                    print "args: %s" % args
##                    print "kwargs: %s" % extraKwArgs
#                    return function(self, *args, **extraKwArgs)
#                
#                methodWithAutomaticArgs.__name__ = function.__name__
#                methodWithAutomaticArgs.__doc__ = function.__doc__
#                return methodWithAutomaticArgs
#                        
#            if mayaCmdWillFail:
#                @feedArgs
#                def mayaTest(self, *args, **kwargs):
#                    '''maya.cmds.%s fails on %s'''
#                    self.assertRaises(TypeError, mayaCmd, *args, **kwargs)
#            else:
#                # if the maya command succeeds, no need to test the wrapped
#                @feedArgs 
#                def mayaTest(self, *args, **kwargs):
#                    '''maya.cmds.%s handles %s'''
##                    print "%s(" % mayaCmd.__name__,
##                    print ", ".join([unicode(x) for x in args]),
##                    for key, val in kwargs: print "%s=%s," % (key,val),
##                    print ")"
#                    self.assertNoError(mayaCmd, *args, **kwargs)
#
#            @feedArgs
#            def wrappedTest(self, *args, **kwargs):
#                '''pymel.%s handles %s'''
##                print "%s(" % wrappedCmd.__name__,
##                print ", ".join([unicode(x) for x in args]),
##                for key, val in kwargs: print "%s=%s," % (key,val),
##                print ")"
#                self.assertNoError(wrappedCmd, *args, **kwargs)
#
#            for testMethod in (mayaTest, wrappedTest):
#                testMethod.__name__ = "_".join(["test", cmdName, testMethod.__name__, "on"] + nameSuffixList) 
#                testMethod.__doc__ = testMethod.__doc__ % (cmdName, " ".join(nameSuffixList))
#                while(hasattr(cls, testMethod.__name__)):
#                    testMethod.__name__ += '1'
#                setattr(cls, testMethod.__name__, testMethod)
#                
#            if mayaCmdWillFail:
#                mayaTests_shouldFail.append(mayaTest.__name__)
#            else:
#                mayaTests_shouldPass.append(mayaTest.__name__)
#            wrappedTests.append(wrappedTest.__name__)
#        
#        # 1. cmdName(arg1String, arg2String)
#        addTestPair(mayaCmdWillFail=False)
#
#        # 2. cmdName(arg1PyNode, arg2Pynode)
#        addTestPair(mayaCmdWillFail=mayaFailsOnCustomStrings, testPyNodes=True)
#            
#        if canTakeListArg:
#            # 3. cmdName([arg1String, arg2String])
#            addTestPair(mayaCmdWillFail=False, useListArg=True)
#            
#            # 4. cmdname([arg1PyNode, arg2Pynode])
#            addTestPair(mayaCmdWillFail=mayaFailsOnCustomStringsInNormalLists,
#                        useListArg=True, testPyNodes=True)
#
#            # 5. cmdname(Mylist([arg1String, arg2String]))
#            addTestPair(mayaCmdWillFail=mayaFailsOnCustomLists,
#                        useListArg=True, testCustomLists=True)
#                
#            # 6. cmdname(Mylist([arg1PyNode, arg2Pynode]))
#            addTestPair(mayaCmdWillFail=mayaFailsOnCustomLists,
#                        useListArg=True, testPyNodes=True, testCustomLists=True),
#
#
#    # Need to put this in separate method, b/c addTestsForCmd is a classmethod, and can't access
#    # self.lists directly
#    def getArgs(self, typeOfArgs, numOfArgs, testPyNodes, useListArg, testCustomLists, *args):
#        pynodeArgs =  self.lists[typeOfArgs]
#        if numOfArgs is not None:
#            while numOfArgs > len(pynodeArgs):
#                pynodeArgs = pynodeArgs + pynodeArgs
#            pynodeArgs = pynodeArgs[:numOfArgs]
#        stringArgs = [unicode(x) for x in pynodeArgs]
#
#        if testPyNodes:
#            testedArgs = pynodeArgs
#        else:
#            testedArgs = stringArgs
#
#        if useListArg:
#            if testCustomLists:
#                testedArgs = [Mylist(testedArgs)]
#            else:
#                testedArgs = [testedArgs] 
#                
##        print "testedArgs: %s" % testedArgs
#        return testedArgs + list(args)
#
## Reference:
##TestWrappedCmds.addTestsForCmd(cmdName, typeOfArgs,  
##                       failsOnCustomStrings=False, failsOnCustomLists=False, \
##                       numOfArgs=None, canTakeListArg=False, *args, **kwargs)
#
## I don't really need the "absolute" here, was really just making sure extraKwArgs worked...
#TestWrappedCmds.addTestsForCmd('group', 'transform', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True, extraKwArgs={'absolute':1})
#TestWrappedCmds.addTestsForCmd('select', 'transform', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True)
#TestWrappedCmds.addTestsForCmd('connectAttr', 'attribute', mayaFailsOnCustomStrings=True, extraKwArgs={'force':1})
#TestWrappedCmds.addTestsForCmd('disconnectAttr', 'attribute2', mayaFailsOnCustomStrings=True)
#TestWrappedCmds.addTestsForCmd('listConnections', 'attribute2', mayaFailsOnCustomStrings=True,
#                               mayaFailsOnCustomLists=True, canTakeListArg=True)
#TestWrappedCmds.addTestsForCmd('getAttr', 'attribute', mayaFailsOnCustomStrings=True, numOfArgs=1)
#TestWrappedCmds.addTestsForCmd('setAttr', 'attribute', mayaFailsOnCustomStrings=True, numOfArgs=1, extraArgs=[3])
#TestWrappedCmds.addTestsForCmd('listAttr', 'transform', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True)
#TestWrappedCmds.addTestsForCmd('listAttr', 'attribute', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True)
#TestWrappedCmds.addTestsForCmd('attributeInfo', 'attribute', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True,
#                               extraKwArgs={'allAttributes':True})
#TestWrappedCmds.addTestsForCmd('listRelatives', 'transform', mayaFailsOnCustomStrings=True, mayaFailsOnCustomLists=True, canTakeListArg=True)
##TestWrappedCmds.addTestsForCmd('connectAttr', 'attribute', failsOnCustomStrings=True, failsOnCustomLists=True, canTakeListArg=True)
#
#mayaCmdsSuite_shouldPass = unittest.TestSuite()
#mayaCmdsSuite_shouldFail = unittest.TestSuite()
#wrappedCmdsSuite = unittest.TestSuite()
#
#for suite, testList in ( (mayaCmdsSuite_shouldPass, mayaTests_shouldPass),
#                         (mayaCmdsSuite_shouldFail, mayaTests_shouldFail),
#                         (wrappedCmdsSuite, wrappedTests) ):
#    for test in testList:
#        suite.addTest(TestWrappedCmds(test))
#
#mayaCmdsSuite = unittest.TestSuite()
#mayaCmdsSuite.addTests(mayaCmdsSuite_shouldPass)
#if testMayaFailures:
#    mayaCmdsSuite.addTests(mayaCmdsSuite_shouldFail) 
#
#allSuite = unittest.TestSuite()
#allSuite.addTests( (mayaCmdsSuite, wrappedCmdsSuite) )
#
#def suite():
#    if testMayaCmds:
#        return allSuite
#    else:
#        return wrappedCmdsSuite
#
#def main():
#    unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite())
#    
#setupUnittestModule(__name__)
