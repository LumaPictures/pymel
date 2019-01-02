import sys
import os
import unittest
import itertools
import re
import platform
import inspect
import math
import inspect
import pytest

import maya.cmds as cmds
import maya.OpenMaya as om
import pymel.core as pm
import pymel.api as api

THIS_FILE = os.path.abspath(inspect.getsourcefile(lambda: None))
THIS_DIR = os.path.dirname(THIS_FILE)
PARENT_DIR = os.path.dirname(THIS_DIR)
try:
    from maintenance.pymelControlPanel import getClassHierarchy
except ImportError:
    if PARENT_DIR not in sys.path:
        sys.path.append(PARENT_DIR)
        from maintenance.pymelControlPanel import getClassHierarchy
    else:
        raise

import pymel.internal.factories as factories
import pymel.internal.apicache as apicache
import pymel.util.arrays as arrays
import pymel.versions as versions

from pymel.util.testing import TestCaseExtended, setCompare

VERBOSE = False

class CrashError(Exception):
    """
    Raised to signal that doing something would have caused maya to crash.
    """
    pass


class testCase_attribs(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.sphere1, hist = pm.polySphere()

        class AttributeData(object):
            node = self.sphere1

            def __init__(self, name, **initArgs):
                self.name = name
                self.initArgs = initArgs

            def add(self):
                pm.addAttr(self.node, longName=self.name, **self.initArgs)

        self.newAttrs = [
                        AttributeData('angle', attributeType='doubleAngle'),
                        AttributeData('multiByte', multi=True, attributeType='byte'),
                        AttributeData('compound', attributeType='compound', numberOfChildren=3),
                        AttributeData('compound_multiFloat', attributeType='float', multi=True, parent='compound'),
                        AttributeData('compound_double', attributeType='double', parent='compound'),
                        AttributeData('compound_compound', attributeType='compound', numberOfChildren=2, parent='compound'),
                        AttributeData('compound_compound_matrix', attributeType='matrix', parent='compound_compound'),
                        AttributeData('compound_compound_long', attributeType='long', parent='compound_compound'),
                        AttributeData('multiCompound', attributeType='compound', multi=True, numberOfChildren=3),
                        AttributeData('multiCompound_string', dataType='string', parent='multiCompound'),
                        AttributeData('multiCompound_enum', attributeType='enum', parent='multiCompound'),
                        AttributeData('multiCompound_curve', dataType='nurbsCurve', parent='multiCompound'),
                        ]

        self.attrTypes = {}
        for attrData in self.newAttrs:
            attrType = attrData.initArgs.get('attributeType',attrData.initArgs.get('dataType'))
            if attrType == 'compound' or attrData.initArgs.get('multi'):
                attrType = 'TdataCompound'
            self.attrTypes[attrData.name] = attrType

        for attr in self.newAttrs:
            attr.add()

        self.newAttrs = dict([(newAttr.name, pm.Attribute(str(self.sphere1) + "." + newAttr.name)) for newAttr in self.newAttrs ])

        self.setIndices = (1, 3, 5, 12)
        for i in self.setIndices:
            self.newAttrs['multiByte'][i].set(1)

        self.setMultiElement = self.newAttrs['multiByte'][self.setIndices[0]]

        self.unsetMultiElement = self.newAttrs['multiByte'][200]

    def tearDown(self):
        pm.delete(self.sphere1)

    def test_newAttrsExists(self):
        for attrName, attr in self.newAttrs.iteritems():
#            print "Testing existence of:", attr.name()
            if attrName.startswith('multiCompound_'):
                self.assertFalse(attr.exists(), 'attr %r existed' % attr)
            else:
                self.assertTrue(attr.exists(), 'attr %r did not exist' % attr)

    def test_setMultiElementExists(self):
        attr = self.setMultiElement
        self.assertTrue(attr.exists(), '%s should exist' % attr)

    def test_unsetMultiElementExists(self):
        attr = self.unsetMultiElement
        self.assertFalse(attr.exists(), '%s should not exist' % attr)

    def test_setMultiCompoundElementExists(self):
        attr = self.newAttrs['multiCompound'][1].attr('multiCompound_string')
        attr.set('foo')
        self.assertTrue(attr.exists(), '%s should exist' % attr)

    def test_unsetMultiCompoundElementExists(self):
        attr = self.newAttrs['multiCompound'][1].attr('multiCompound_string')
        self.assertFalse(attr.exists())
        attr = self.newAttrs['multiCompound_string']
        self.assertFalse(attr.exists())

    def test_getParent(self):
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(), self.newAttrs['compound_compound'])

        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(0), self.newAttrs['compound_compound_long'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=1), self.newAttrs['compound_compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(2), self.newAttrs['compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=3), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-1), self.newAttrs['compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=-2), self.newAttrs['compound_compound'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-3), self.newAttrs['compound_compound_long'])
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=-4), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-5), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=4), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(-63), None)
        self.assertEqual(self.newAttrs['compound_compound_long'].getParent(generations=32), None)

        self.assertEqual(self.newAttrs['compound_compound_long'].getAllParents(),
                         [  self.newAttrs['compound_compound'],
                            self.newAttrs['compound'],
                         ])

        self.assertEqual(self.newAttrs['multiCompound_string'].getParent(generations=1).array(),
                         self.newAttrs['multiCompound'])
        self.assertEqual(self.newAttrs['multiCompound_string'].getParent(generations=2, arrays=True),
                         self.newAttrs['multiCompound'])
        self.assertEqual(self.newAttrs['multiCompound_string'].getParent(generations=-1, arrays=True),
                         self.newAttrs['multiCompound'])

        self.assertEqual(self.newAttrs['multiCompound_string'].getAllParents(),
                         [  self.newAttrs['multiCompound_string'].getParent(generations=1),
                         ])
        self.assertEqual(self.newAttrs['multiCompound_string'].getAllParents(arrays=True),
                         [  self.newAttrs['multiCompound_string'].getParent(generations=1),
                            self.newAttrs['multiCompound'],
                         ])

        self.assertEqual(self.newAttrs['multiByte'].getAllParents(), [])
        self.assertEqual(self.newAttrs['multiByte'].getAllParents(arrays=True), [])
        self.assertEqual(self.newAttrs['multiCompound'].getAllParents(), [])
        self.assertEqual(self.newAttrs['multiCompound'].getAllParents(arrays=True), [])
        self.assertEqual(self.newAttrs['multiCompound'].getAllParents(), [])
        self.assertEqual(self.newAttrs['multiCompound'].getAllParents(arrays=True), [])
        self.assertEqual(self.newAttrs['angle'].getAllParents(), [])
        self.assertEqual(self.newAttrs['angle'].getAllParents(arrays=True), [])

    def test_comparison(self):
        for attr in self.newAttrs.itervalues():
            self.assertEqual(attr, pm.PyNode(attr.name()))

    def test_comparisonOtherObject(self):
        self.assertNotEqual(self.newAttrs['compound'], self.sphere1)

    def test_add_delete(self):
        pm.PyNode('persp').addAttr('foo')
        self.assert_( pm.PyNode('persp').hasAttr('foo') )
        pm.PyNode('persp').deleteAttr('foo')
        self.assert_(  not pm.PyNode('persp').hasAttr('foo') )

    def test_elements(self):
        self.assertEqual(self.newAttrs['multiByte'].elements(), ['multiByte[%d]' % x for x in self.setIndices])
        self.assertEqual(self.newAttrs['multiCompound'].elements(), [])
        self.assertEqual(self.newAttrs['compound_multiFloat'].elements(), [])

    def test_iter(self):
        iterList = [x for x in self.newAttrs['multiByte']]
        expectedList = [self.newAttrs['multiByte'][i] for i in self.setIndices]
        self.assertEqual(iterList, expectedList)

    def test_iter_independence(self):
        iter1 = iter(self.newAttrs['multiByte'])
        iter2 = iter(self.newAttrs['multiByte'])
        zipped = zip(iter1, iter2)
        self.assertEqual(zipped, [ (self.newAttrs['multiByte'][i],
                                    self.newAttrs['multiByte'][i])
                                   for i in self.setIndices ])

    def test_settable(self):

        def testLockUnlock(attr, child=None):
            if child is None:
                attr.lock()
                self.assertFalse(attr.isSettable(), '%s was locked - should be unsettable' % attr)
                attr.unlock()
                self.assertTrue(attr.isSettable(), '%s was unlocked - should be settable' % attr)
            else:
                child.lock()
                self.assertFalse(child.isSettable(), '%s was locked - should be unsettable' % child)
                self.assertFalse(attr.isSettable(), '%s had locked child- should be unsettable' % attr)
                child.unlock()
                self.assertTrue(child.isSettable(), '%s was unlocked - should be settable' % attr)
                self.assertTrue(attr.isSettable(), '%s had unlocked child - should be settable' % attr)

        for attr in self.newAttrs.itervalues():
            if not attr.exists():
                continue

            testLockUnlock(attr)

            if attr.isMulti():
                child = attr[0]
                testLockUnlock(attr, child)
                if attr.isCompound():
                    multi_child = child.children()[0]
                    testLockUnlock(attr, child)
                    testLockUnlock(attr, multi_child)
            elif attr.isCompound():
                testLockUnlock(attr, attr.children()[0])

    def test_attr_type(self):
        for attrName, attrType in self.attrTypes.iteritems():
            self.assertEqual(self.newAttrs[attrName].type(), attrType)
        self.assertEqual(self.newAttrs['multiCompound'].numElements(), 0)
        self.assertEqual(self.newAttrs['multiByte'].numElements(), len(self.setIndices))

        # Try some non-dynamic attrs...
        self.assertEqual(self.sphere1.attr('translateX').type(), 'doubleLinear')
        self.assertEqual(self.sphere1.attr('translate').type(), 'double3')
        self.assertEqual(self.sphere1.attr('message').type(), 'message')

        # Try a more unusual attr type...
        circleMaker = pm.circle()[1]
        self.assertEqual(circleMaker.attr('outputCurve').type(), 'nurbsCurve')


class testCase_deleteAttr(unittest.TestCase):
    def setUp(self):
        self.node = pm.createNode('transform', name='daNode')
        self.assertFalse(self.node.hasAttr('foobar'))
        self.node.addAttr('foobar')
        self.attr = self.node.attr('foobar')

    def tearDown(self):
        pm.delete(self.node)

    def test_str(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        self.node.deleteAttr('foobar')
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_attr(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        self.node.deleteAttr(self.attr)
        self.assertFalse(self.node.hasAttr('foobar'))

    def test_attr_wrongNode(self):
        otherNode = pm.createNode('transform', name='otherNode')
        otherNode.addAttr('foobar')
        otherAttr = otherNode.attr('foobar')
        self.assertTrue(self.node.hasAttr('foobar'))
        self.assertTrue(otherNode.hasAttr('foobar'))
        self.assertRaises(pm.MayaAttributeError, self.node.deleteAttr,
                          otherAttr)
        self.assertRaises(pm.MayaAttributeError, otherNode.deleteAttr,
                          self.attr)
        self.assertTrue(self.node.hasAttr('foobar'))
        self.assertTrue(otherNode.hasAttr('foobar'))
        self.node.deleteAttr(self.attr)
        self.assertFalse(self.node.hasAttr('foobar'))
        self.assertTrue(otherNode.hasAttr('foobar'))

    def test_attrSpec(self):
        self.assertTrue(self.node.hasAttr('foobar'))
        self.node.deleteAttr(self.node.attrSpec('foobar'))
        self.assertFalse(self.node.hasAttr('foobar'))


class testCase_attrSpec(unittest.TestCase):
    def setUp(self):
        self.persp = pm.nt.Transform('persp')
    
    def assertObjectGroups(self, attrSpec):
        self.assertTrue(attrSpec.isConnectable())
        self.assertTrue(attrSpec.isStorable())
        self.assertTrue(attrSpec.isCached())
        self.assertTrue(attrSpec.isArray())
        self.assertEqual(attrSpec.name(), 'objectGroups')
        self.assertEqual(attrSpec.shortName(), 'og')
        parent = attrSpec.parent()
        self.assertIsInstance(parent, pm.AttributeSpec)
        self.assertEqual(parent.name(), 'instObjGroups')

    def test_str(self):
        attrSpec = self.persp.attrSpec('objectGroups')
        self.assertObjectGroups(attrSpec)

    def test_index(self):
        objGroups = None
        for i in xrange(self.persp.attributeCount()):
            # make sure we get a valid obj for all indices
            attrSpec = self.persp.attrSpec(i)
            self.assertIsInstance(attrSpec, pm.AttributeSpec)
            # make sure this doesn't error
            name = attrSpec.name()
            self.assertIsInstance(name, basestring)
            self.assertTrue(name)
            if name == 'objectGroups':
                objGroups = attrSpec
        self.assertIsNotNone(objGroups)
        self.assertObjectGroups(objGroups)

    def test_Attribute(self):
        attr = self.persp.attr('objectGroups')
        attrSpec = self.persp.attrSpec(attr)
        self.assertObjectGroups(attrSpec)

    def test_AttributeSpec(self):
        attrSpecOrig = self.persp.attrSpec('og')
        attrSpec = self.persp.attrSpec(attrSpecOrig)
        self.assertObjectGroups(attrSpec)

    def test_mplug(self):
        sel = om.MSelectionList()
        sel.add('persp.instObjGroups[0].objectGroups')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        attrSpec = self.persp.attrSpec(mplug)
        self.assertObjectGroups(attrSpec)

    def test_mobject(self):
        sel = om.MSelectionList()
        sel.add('persp.instObjGroups[0].objectGroups')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        mobj = mplug.attribute()
        attrSpec = self.persp.attrSpec(mobj)
        self.assertObjectGroups(attrSpec)

    def test_cls_str(self):
        attrSpec = pm.nt.Transform.attrSpec('objectGroups')
        self.assertObjectGroups(attrSpec)

    def test_cls_index(self):
        objGroups = None
        for i in xrange(om.MNodeClass('transform').attributeCount()):
            # make sure we get a valid obj for all indices
            attrSpec = pm.nt.Transform.attrSpec(i)
            self.assertIsInstance(attrSpec, pm.AttributeSpec)
            # make sure this doesn't error
            name = attrSpec.name()
            self.assertIsInstance(name, basestring)
            self.assertTrue(name)
            if name == 'objectGroups':
                objGroups = attrSpec
        self.assertIsNotNone(objGroups)
        self.assertObjectGroups(objGroups)

    def test_cls_Attribute(self):
        attr = self.persp.attr('objectGroups')
        attrSpec = pm.nt.Transform.attrSpec(attr)
        self.assertObjectGroups(attrSpec)

    def test_cls_AttributeSpec(self):
        attrSpecOrig = pm.nt.Transform.attrSpec('og')
        attrSpec = pm.nt.Transform.attrSpec(attrSpecOrig)
        self.assertObjectGroups(attrSpec)

    def test_cls_mplug(self):
        sel = om.MSelectionList()
        sel.add('persp.instObjGroups[0].objectGroups')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        attrSpec = pm.nt.Transform.attrSpec(mplug)
        self.assertObjectGroups(attrSpec)

    def test_cls_mobject(self):
        sel = om.MSelectionList()
        sel.add('persp.instObjGroups[0].objectGroups')
        mplug = om.MPlug()
        sel.getPlug(0, mplug)
        mobj = mplug.attribute()
        attrSpec = pm.nt.Transform.attrSpec(mobj)
        self.assertObjectGroups(attrSpec)

    def test_dynamic(self):
        # make sure that attrSpec doesn't improperly cache dynamic atributes
        # by re-creating an attr with the same name multiple times. We check
        # both by creating an attr with the same name on two different nodes
        # of the same type, and by recreating attrs with the exact same specs
        # multiple times, after doing a newFile
        for i in xrange(3):
            pm.newFile(f=1)
            persp = pm.PyNode('persp')
            top = pm.PyNode('top')
            self.assertFalse(persp.hasAttr('foobar'))
            self.assertFalse(persp.hasAttr('foo'))
            self.assertFalse(persp.hasAttr('foob'))
            self.assertFalse(top.hasAttr('foobar'))
            self.assertFalse(top.hasAttr('foo'))
            self.assertFalse(top.hasAttr('foob'))
            persp.addAttr(
                'foobar', shortName="foo", readable=True, writable=False,
                storable=False, multi=True, indexMatters=False)
            top.addAttr(
                'foobar', shortName="foob", readable=False, writable=True)
            self.assertTrue(persp.hasAttr('foobar'))
            self.assertTrue(persp.hasAttr('foo'))
            self.assertFalse(persp.hasAttr('foob'))
            self.assertTrue(top.hasAttr('foobar'))
            self.assertFalse(top.hasAttr('foo'))
            self.assertTrue(top.hasAttr('foob'))
            foo = persp.attrSpec('foobar')
            self.assertEqual(foo.name(), "foobar")
            self.assertEqual(foo.shortName(), "foo")
            self.assertTrue(foo.isReadable())
            self.assertFalse(foo.isWritable())
            self.assertFalse(foo.isStorable())
            self.assertTrue(foo.isArray())
            self.assertFalse(foo.getIndexMatters())
            foob = top.attrSpec('foobar')
            self.assertEqual(foob.name(), "foobar")
            self.assertEqual(foob.shortName(), "foob")
            self.assertFalse(foob.isReadable())
            self.assertTrue(foob.isWritable())
            self.assertTrue(foob.isStorable())
            self.assertFalse(foob.isArray())
            self.assertTrue(foob.getIndexMatters())


def pytest_generate_tests(metafunc):
    if hasattr(metafunc.cls, 'ARGS'):
        argnames = metafunc.cls.ARGS.split(', ')
        ids, argvalues = zip(*list(metafunc.cls.getParameters()))
        metafunc.parametrize(argnames, argvalues, ids=ids)


class TestInvertibles(object):
    ARGS = "pynode, apiClassName, setMethod, setter, getter, setArgTypes"
    EXCEPTIONS = [
                  'MotionPath',   # setUEnd causes maya to crash
                  'OldBlindDataBase',
                  'TextureToGeom'
                 ]

    GETTER_SKIPS = [
                    # calling setAbsoluteChannelSettings([1,2,3]) will
                    # effectively set the number of channels to three, and
                    # calling setAbsoluteChannelSettings([0]) does not set it
                    # back to 1... and there doesn't seem to be a way to set it
                    # back to 1 channel... forgiving this because I'm assuming
                    # that the number of channels isn't "supposed" to change
                    ('AnimClip', 'getAbsoluteChannelSettings'),

                    # calling setExpression seems to trigger some sort of mel
                    # callback - if you check cmds.undoInfo(q=1, printQueue=1),
                    # it shows a call like:
                    #   expression -e -ae 0  -o ""  -a ""  -s "" expression1;
                    # ...that happens after the apiUndo.cmdCount increment

                    # Could wrap the adding of the apiUndo item and actual
                    # execution of the cmd into a single undo chunk, but I'm
                    # worried about unforeseen consequences... going to forgive,
                    # since it will undo correctly, it just takes one more
                    # undo than expected (which is often the case with mel
                    # callbacks...)
                    ('Expression', 'isAnimated'),
                   ]

    class GetTypedArgError(Exception): pass

    @classmethod
    def getTypedArg(cls, type):
        typeMap = {
            'bool' : True,
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
            'MColorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0] ),
            'MVector' : [1,0,0],
            'MVectorArray': ( [1.0,0.0,0.0], [0.0,1.0,0.0], [0.0,0.0,1.0] ),
            'int' : 1,
            'MIntArray': [1,2,3],
            'MSpace.Space' : 'world'
        }
        if '.' in type:
            return 1 # take a dumb guess at an enum
        else:
            try:
                return typeMap[type]
            except KeyError:
                raise cls.GetTypedArgError(type)

    @classmethod
    def _getMethodAndArgTypes(cls, basePyClass, pyClassName, apiClassName,
                       classInfo, methodName):
        try:
            info = classInfo['methods'][methodName]
        except KeyError:
            return None
        methodName = classInfo.get('pymelMethods', {}).get(methodName, methodName)
        methodName, data, _ = factories._getApiOverrideNameAndData( pyClassName, methodName )
        try:
            overloadIndex = data.get('overloadIndex', 0)
            info = info[overloadIndex]
        except (KeyError, TypeError):
            return None
        # test if this invertible has been broken in pymelControlPanel
        if not info.get('inverse', True):
            return None
        try:
            method = getattr( basePyClass, methodName )
        except AttributeError:
            return None
        inArgs = [ arg for arg in info['inArgs'] if arg not in info['defaults'] ]
        argTypes = [ str(info['types'][arg]) for arg in inArgs ]
        return method, argTypes

    @classmethod
    def getParameters(cls):
        pyNodes = inspect.getmembers(pm.nodetypes,
                                     lambda x: inspect.isclass(x) and issubclass(x, pm.PyNode))

        realNodes = apicache._getRealMayaTypes(noPlugins=True)
        realPyNodes = [node for name, node in pyNodes if node.__melnode__ in realNodes]

        for pynode in realPyNodes:
            # for some reason, we sometimes return the same method twice...?
            # ensure we don't make 2 tests for it...
            methods = set()

            pynodeName = pynode.__name__
            if pynodeName in cls.EXCEPTIONS:
                continue

            for className, apiClassName in getClassHierarchy(pynodeName):
                if apiClassName not in factories.apiClassInfo:
                    continue

                #print className, apiClassName

                classInfo = factories.apiClassInfo[apiClassName]
                invertibles = classInfo.get('invertibles', [])
                #print invertibles

                for setMethod, getMethod in invertibles:
                    setMethodData = cls._getMethodAndArgTypes(pynode, className,
                                                              apiClassName,
                                                              classInfo,
                                                              setMethod)
                    if setMethodData is None:
                        continue
                    else:
                        setter, setArgTypes = setMethodData
                    if setter in methods:
                        continue
                    else:
                        methods.add(setter)

                    getter = None
                    if (pynodeName, getMethod) not in cls.GETTER_SKIPS:
                        getMethodData = cls._getMethodAndArgTypes(pynode, className,
                                                                  apiClassName,
                                                                  classInfo,
                                                                  getMethod)
                        if getMethodData:
                            getter, getArgTypes = getMethodData
                            if getArgTypes:
                                # if the getter requires args, don't bother testing
                                # it
                                getter = None

                    name = '%s_%s' % (pynode.__name__, setMethod)
                    yield name, (pynode, apiClassName, setMethod, setter,
                                 getter, setArgTypes)

    @pytest.mark.filterwarnings("ignore::pymel.internal.pwarnings.PymelBaseDeprecationWarning")
    def testInvert(self, pynode, apiClassName, setMethod, setter, getter, setArgTypes):
        import types

        print "testing %s.%s" % (pynode.__name__, setMethod)

        # if getter / setter are classmethods, we will get them as
        # bound args
        def isBoundMethod(obj):
            return isinstance(obj, types.MethodType) and obj.__self__ is not None

        if isBoundMethod(getter):
            # they should either BOTH be classmethods, or neither
            assert isBoundMethod(setter)
            isClassMethod = True
        else:
            assert not isBoundMethod(setter)
            isClassMethod = False

        sys.stdout.flush()
        sys.stdout.flush()
        melnodeName = pynode.__melnode__

        if not isClassMethod:
            if issubclass(pynode, pm.nt.GeometryShape):
                if pynode is pm.nt.Mesh :
                    obj = pm.polyCube()[0].getShape()
                    obj.createColorSet( 'thingie' )
                elif pynode is pm.nt.Subdiv:
                    obj = pm.polyToSubdiv( pm.polyCube()[0].getShape())[0].getShape()
                elif pynode is pm.nt.NurbsSurface:
                    obj = pm.sphere()[0].getShape()
                elif pynode is pm.nt.NurbsCurve:
                    obj = pm.circle()[0].getShape()
                else:
                    pytest.skip("incompatible node type")
            else:
                #print "creating: %s" % melnodeName
                obj = pm.createNode( melnodeName )

        try:
            try:
                if apiClassName == 'MFnMesh' and setMethod == 'setUVs':
                    setArgs = [ [.1]*obj.numUVs(), [.2]*obj.numUVs() ]
                elif apiClassName == 'MFnMesh' and setMethod == 'setColors':
                    setArgs = [ [ [.5,.5,.5] ]*obj.numColors() ]
                elif apiClassName == 'MFnMesh' and setMethod == 'setColor':
                    obj.setColors( [ [.5,.5,.5] ]*obj.numVertices() )
                    setArgs = [ 1, [1,0,0] ]
                elif apiClassName == 'MFnMesh' and setMethod in ['setFaceVertexColors', 'setVertexColors']:
                    obj.createColorSet(setMethod + '_ColorSet' )
                    setArgs = [ ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]), [1, 2, 3] ]

                elif apiClassName == 'MFnNurbsCurve' and setMethod == 'setKnot':
                    setArgs = [ 6, 4.5 ]
                elif setMethod == 'setIcon':
                    setArgs = [ 'polyCylinder.png' ]
                else:
                    setArgs = [ self.getTypedArg(typ) for typ in setArgTypes ]
                #descr =  '%s.%s(%s)' % ( pynodeName, setMethod, ', '.join( [ repr(x) for x in setArgs] ) )

                if isClassMethod:
                    getArgs = []
                else:
                    getArgs = [obj]
                    setArgs = [obj] + setArgs

                if getter:
                    oldVal = getter(*getArgs)
                setter( *setArgs )
                cmds.undo()
                if getter:
                    newVal = getter(*getArgs)

                    if isinstance(newVal, float):
                        assert oldVal == pytest.approx(newVal, abs=1e-12)
                    elif isinstance(newVal, (tuple, list, arrays.Array)):
                        assert len(newVal) == len(oldVal)
                        # self.fail('oldVal %r != to newVal %r - unequal lengths' % (oldVal, newVal))
                        for i in xrange(len(newVal)):
                            # msg = 'index %d of oldVal %r not equal to newVal %r' % (i, oldVal, newVal)
                            if isinstance(newVal[i], float):
                                assert oldVal[i] == pytest.approx(newVal[i], abs=1e-12)
                            else:
                                assert oldVal[i] == newVal[i]
                    else:
                        assert oldVal == newVal
            except self.GetTypedArgError:
                pass
        finally:
            try:
                pm.delete( obj )
            except:
                pass


# TODO: add tests for slices
# test tricky / extended slices: ie, [:3], [:-1], [-3:-1], [5:1:-2], etc
# test multi-index slices, ie: [1:2, 5:9:2]
# Add tests for ranges of float parameters: ie, 'nurbsSphere1.v[5.657][3.1:4.2]'
# Add tests for double-indexed nurbs suface: 'nurbsSphere1.v[1.1:2.2][3.3:4.4]'
# check that indexing uses mel-style ranges (ie, inclusive)
# Continuous components with negative indices - ie, nurbsSurf[-3.3][-2]

class ComponentData(object):
    """
    Stores data handy for creating / testing a component.
    """
    def __init__(self, pymelType, nodeName, compName, indices, ranges,
                 melCompName=None,
                 pythonIndices=None, melIndices=None, neverUnindexed=False):
        self.pymelType = pymelType
        self.nodeName = nodeName
        self.compName = compName
        if melCompName is None:
            melCompName = compName
        self.melCompName = melCompName
        self.indices = indices
        self.ranges = ranges
        if isinstance(self.indices, (int, float, basestring)):
            self.indices = (self.indices,)
        if pythonIndices is None:
            pythonIndices = []
        if isinstance(pythonIndices, (int, float, basestring)):
            pythonIndices = [pythonIndices]
        self.pythonIndices = pythonIndices
        if melIndices is None:
            melIndices = []
        if isinstance(melIndices, (int, float, basestring)):
            melIndices = [melIndices]
        self.melIndices = melIndices
        self.neverUnindexed = neverUnindexed

        if indices:
            # just want the first one, since all we need in a component
            # mobject of the right type
            for x in self.melIndexedComps():
                compObjStr = x
                break
        else:
            compObjStr = self.melUnindexedComp()
        self._compObj = api.toApiObject(compObjStr)[1]


    def pyUnindexedComp(self):
        return self.nodeName + "." + self.compName

    def melUnindexedComp(self):
        return self.nodeName + "." + self.melCompName

    def _makeIndicesString(self, indexObj):
        return ''.join([('[%s]' % x) for x in indexObj.index])

    def pyIndexedComps(self):
        if not self.hasPyIndices():
            raise ValueError("no indices stored - %s" % self.pyUnindexedComp())
        else:
            # yield partial indices as well...
            for index in itertools.chain(self.indices, self.pythonIndices):
                if len(index.index):
                    for partialIndexLen in xrange(1, len(index.index)):
                        yield self.pyUnindexedComp() + self._makeIndicesString(IndexData(*index.index[:partialIndexLen]))
                yield self.pyUnindexedComp() + self._makeIndicesString(index)

    def melIndexedComps(self):
        if not self.hasMelIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in itertools.chain(self.indices, self.melIndices):
                yield self.melUnindexedComp() + self._makeIndicesString(index)

    def bothIndexedComps(self):
        """
        For indices which are same for mel/pymel, returns a pair (melComp, pyComp)
        if not self.hasMelIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in itertools.chain(self.indices, self.melIndices):
                yield self.melUnindexedComp() + self._makeIndicesString(index)
        """
        if not self.hasBothIndices():
            raise ValueError("no indices stored - %s" % self.melUnindexedComp())
        else:
            for index in self.indices:
                indiceString = self._makeIndicesString(index)
                yield (self.melUnindexedComp() + indiceString,
                       self.pyUnindexedComp() + indiceString)

    def hasPyIndices(self):
        return self.indices or self.pythonIndices

    def hasMelIndices(self):
        return self.indices or self.melIndices

    def hasBothIndices(self):
        return bool(self.indices)

    def typeEnum(self):
        return self._compObj.apiType()

    def typeName(self):
        return self._compObj.apiTypeStr()

class IndexData(object):
    def __init__(self, *index):
        self.index = index


def makeComponentCreationTests(evalStringCreator, funcName=None):
    """
    Outputs a function suitable for use as a unittest test that tests creation of components.

    For every ComponentData item in in self.compData, it will call
        'evalStringCreator(self, componentData)'
    evalStringCreator should output
        evalStrings
    where evalStrings is a list of strings, each of which when called like:
        eval(anEvalString)
    evaluates to a component.

    The function returns
        (successfulComps, failedComps)
    where each item of successfulComps is a successfully created component
    object, and each item of failedComps is the evalString that was not made.

    If any component cannot be created, the test will fail, and output a list of the components that
    could not be made in the fail message.
    """

    def test_makeComponents(self):
        successfulComps = []
        failedComps = []
        for componentData in self.compData.itervalues():
            evalStrings = evalStringCreator(self, componentData)
            for evalString in evalStrings:
                if VERBOSE:
                    print "trying to create:", evalString, "...",
                try:
                    self._pyCompFromString(evalString)
                except Exception:
                    if VERBOSE:
                        print "FAILED"
                    failedComps.append(evalString)
                else:
                    if VERBOSE:
                        print "ok"
                    successfulComps.append(evalString)
        if failedComps:
            self.fail('Could not create following components:\n   ' + '\n   '.join(failedComps))
    if funcName:
        test_makeComponents.__name__ = funcName
    return test_makeComponents

class MakeEvalStringCreator(object):
    """
    Used to transform a 'compString evalString creator' function to a
    a 'compData evalString creator' function.

    The generated 'compData evalString creator' is a function of the form:
       compDataEvalStringCreator(testCase, compDataObject)
    It takes a testCase_components object and a ComponentData object,
    and returns a list of strings, each of which can be fed as an argument
    to eval to generate a component.

    The input function, the 'compString evalString creator', is of the form:
        compStringEvalStringCreator(testCase, compString)
    It takes a testCase_components object and a component string, such as
       'myCube.vtx[1]'
    and returns a single string, which may be fed to eval to generate a
    component.

    melOrPymel determines whether mel-style or pymel-style syntax will be used.
    (in general, pymel-style indices are similar to mel-style, but can allow
    things such as [:-1].  Also, different component names may be used - for
    instance, the mel-syntax 'myNurbsSphere.v' will result in a v-isoparm,
    whereas PyNode('myNurbsSphere').v will give you the visibility attribute,
    so PyNode('myNurbsSphere').vIsoparm must be used. )

    If indexed is True, then the returned components will have an index. In this
    case, only compData which have associated index data (of the correct mel-or-
    pymel syntax type) will generate evalStrings.

    If indexed is False, then returned components will not have an index.
    In this case, alwaysMakeUnindexed will control whether given compData
    objects generate an evalString - if alwaysMakeUnindexed, all compData will
    be used, whereas as if it is false, only compData which have no index data
    for the given synatx will generate evalStrings.
    In addtion, if a ComponentData object has it's neverUnindexed property set
    to True, then no unindexed comp will be returned.
    """
    def __init__(self, melOrPymel, indexed=True, alwaysMakeUnindexed=False):
        self.melOrPymel = melOrPymel
        self.indexed = indexed
        self.alwaysMakeUnindexed = alwaysMakeUnindexed

    def __call__(self, evalStringCreator):
        def wrappedEvalStringCreator(testCase, compData):
            strings = []
            compDataStringFunc = None
            if self.indexed:
                if self.melOrPymel == 'mel':
                    if compData.hasMelIndices():
                        compDataStringFunc = compData.melIndexedComps
                elif self.melOrPymel == 'pymel':
                    if compData.hasPyIndices():
                        compDataStringFunc = compData.pyIndexedComps
                elif self.melOrPymel == 'both':
                    if compData.hasBothIndices():
                        compDataStringFunc = compData.bothIndexedComps
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, x)
                               for x in compDataStringFunc()]
            elif not compData.neverUnindexed:
                if self.melOrPymel == 'mel':
                    if self.alwaysMakeUnindexed or not compData.hasMelIndices():
                        compDataStringFunc = compData.melUnindexedComp
                elif self.melOrPymel == 'pymel':
                    if self.alwaysMakeUnindexed or not compData.hasPyIndices():
                        compDataStringFunc = compData.pyUnindexedComp
                if compDataStringFunc:
                    strings = [evalStringCreator(testCase, compDataStringFunc())]
            # get rid of any empty strings
            return [x for x in strings if x]
        return wrappedEvalStringCreator

def getEvalStringFunctions(theObj):
    returnDict = {}
    for propName in dir(theObj):
        evalStringId = '_evalStrings'
        if propName.endswith(evalStringId):
            returnDict[propName] = getattr(theObj, propName)
    return returnDict

class testCase_components(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)

        self.nodes = {}
        self.compData= {}


        self.nodes['cube'] = cmds.polyCube()[0]
        self.compData['meshVtx'] = ComponentData(pm.MeshVertex,
                                                 self.nodes['cube'], "vtx",
                                            [IndexData(2), IndexData('2:4')],
                                            [(0,7)],
                                            pythonIndices = [IndexData(':-1')])
        self.compData['meshEdge'] = ComponentData(pm.MeshEdge,
                                                  self.nodes['cube'], "e",
                                                  [IndexData(1)],
                                                  [(0,11)])
        #self.compData['meshEdge'] = ComponentData(self.nodes['cube'], "edge", 1)   # This just gets the plug, not a kEdgeComponent
        self.compData['meshFace'] = ComponentData(pm.MeshFace,
                                                  self.nodes['cube'], "f",
                                                  [IndexData(4)],
                                                  [(0,5)])
        self.compData['meshUV'] = ComponentData(pm.MeshUV,
                                                self.nodes['cube'], "map",
                                                [IndexData(3)],
                                                [(0,13)])
        self.compData['meshVtxFace'] = ComponentData(pm.MeshVertexFace,
                                                     self.nodes['cube'], "vtxFace",
                                                     [IndexData(3,0)],
                                                     [(0,7),(0,5)])
        self.compData['rotatePivot'] = ComponentData(pm.Pivot,
                                                     self.nodes['cube'],
                                                     "rotatePivot", [], [])

        self.nodes['subdBase'] = cmds.polyCube()[0]
        self.nodes['subd'] = cmds.polyToSubdiv(self.nodes['subdBase'])[0]
        self.compData['subdCV'] = ComponentData(pm.SubdVertex,
                                                self.nodes['subd'], "smp",
                                                [IndexData(0,2)], [])
        self.compData['subdEdge'] = ComponentData(pm.SubdEdge,
                                                  self.nodes['subd'], "sme",
                                                  [IndexData(256,1)], [])
        self.compData['subdFace'] = ComponentData(pm.SubdFace,
                                                  self.nodes['subd'], "smf",
                                                  [IndexData(256,0)], [])
        self.compData['subdUV'] = ComponentData(pm.SubdUV,
                                                self.nodes['subd'], "smm",
                                                [IndexData(10)], [])
        self.compData['scalePivot'] = ComponentData(pm.Pivot,
                                                    self.nodes['subd'],
                                                    "scalePivot", [], [])

        self.nodes['curve'] = cmds.circle()[0]
        self.compData['curveCV'] = ComponentData(pm.NurbsCurveCV,
                                                 self.nodes['curve'], "cv",
                                                 [IndexData(6)],
                                                 [(0,7)])
        self.compData['curvePt'] = ComponentData(pm.NurbsCurveParameter,
                                                 self.nodes['curve'], "u",
                                                 [IndexData(7.26580365007639)],
                                                 [(0,8)])
        self.compData['curveEP'] = ComponentData(pm.NurbsCurveEP,
                                                 self.nodes['curve'], "ep",
                                                 [IndexData(7)],
                                                 [(0,7)])
        self.compData['curveKnot'] = ComponentData(pm.NurbsCurveKnot,
                                                   self.nodes['curve'], "knot",
                                                   [IndexData(1)],
                                                   [(0,12)])

        self.nodes['sphere'] = cmds.sphere()[0]
        self.compData['nurbsCV'] = ComponentData(pm.NurbsSurfaceCV,
                                                 self.nodes['sphere'], "cv",
                                                 [IndexData(2,1)],
                                                 [(0,6),(0,7)],
                                                 pythonIndices = [IndexData('0:5:2', '1:4:3')])
        self.compData['nurbsIsoU'] = ComponentData(pm.NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "u",
                                                   [IndexData(4),
                                                    IndexData(2.1,1.8)],
                                                   [(0,4),(0,8)],
                                                   neverUnindexed=True)
        self.compData['nurbsIsoV'] = ComponentData(pm.NurbsSurfaceIsoparm,
                                                   self.nodes['sphere'], "vIsoparm",
                                                   [IndexData(5.27974050577565),
                                                    IndexData(3,1.3)],
                                                   # Indice range given in u, v order,
                                                   # because comparison func will
                                                   # automatically flip indice
                                                   # order before using range
                                                   # info for 'v' isoparms
                                                   [(0,4),(0,8)],
                                                   melCompName="v",
                                                   neverUnindexed=True)
        self.compData['nurbsIsoUV'] = ComponentData(pm.NurbsSurfaceIsoparm,
                                                    self.nodes['sphere'], "uv",
                                                    [IndexData(1, 4.8)],
                                                   [(0,4),(0,8)],
                                                    neverUnindexed=True)
        self.compData['nurbsPatch'] = ComponentData(pm.NurbsSurfaceFace,
                                                    self.nodes['sphere'], "sf",
                                                    [IndexData(1,1)],
                                                    [(0,3),(0,7)])
        self.compData['nurbsEP'] = ComponentData(pm.NurbsSurfaceEP,
                                                 self.nodes['sphere'], "ep",
                                                 [IndexData(1,5)],
                                                 [(0,4),(0,7)])
        self.compData['nurbsKnot'] = ComponentData(pm.NurbsSurfaceKnot,
                                                   self.nodes['sphere'], "knot",
                                                   [IndexData(1,5)],
                                                   [(0,8),(0,12)])
        self.compData['nurbsRange'] = ComponentData(pm.NurbsSurfaceRange,
                                                    self.nodes['sphere'], "u",
                                                    [IndexData('2:3')],
                                                    [(0,4),(0,8)])

        self.latticeSize = (3,5,4)
        self.nodes['lattice'] = cmds.lattice(self.nodes['cube'],
                                             divisions=self.latticeSize)[1]
        self.compData['lattice'] = ComponentData(pm.LatticePoint,
                                                 self.nodes['lattice'], "pt",
                                                 [IndexData(0,1,0)],
                                                 [(0,2),(0,4),(0,3)])
        self.nodes['polySphere'] = cmds.polySphere()[0]

        self.nodes['negUSurf'] = cmds.surface(name='periodicSurf', du=3, dv=1,
                                              fu='periodic', fv='open',
                                              ku=range(-13, 0, 1), kv=(0, 1),
                                              pw=[(4, -4, 0, 1), (4, -4, -2.5, 1),
                                                  (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                                  (4, 4, 0, 1), (4, 4, -2.5, 1),
                                                  (0, 5.5, 0, 1), (0, 5.5, -2.5, 1),
                                                  (-4, 4, 0, 1), (-4, 4, -2.5, 1),
                                                  (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1),
                                                  (-4, -4, 0, 1), (-4, -4, -2.5, 1),
                                                  (0, -5.5, 0, 1), (0, -5.5, -2.5, 1),
                                                  (4, -4, 0, 1), (4, -4, -2.5, 1),
                                                  (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                                  (4, 4, 0, 1), (4, 4, -2.5, 1)] )
        self.compData['negNurbsIso'] = ComponentData(pm.NurbsSurfaceIsoparm,
                                                     self.nodes['negUSurf'], "uv",
                                                     [IndexData(-3.4, .5)],
                                                     [(-11,-3),(0,1)],
                                                     neverUnindexed=True)

        # Done in effort to prevent crash which happens after making a subd,
        # then adding any subd edges to an MSelectionList
        # see http://groups.google.com/group/python_inside_maya/browse_thread/thread/9415d03bac9e712b/0b94edb468fbe6bd
        cmds.refresh()
        import maya.utils
        maya.utils.processIdleEvents()
        # While the above works to prevent the crash in GUI mode,
        # unfortunately, I can't find anything that works in batch mode...
        # the following are various things I've tried...
        # Unfortunately, nothing is working so far...
#        cmds.refresh()
#        subdPyNode = pm.PyNode(self.nodes['subd']).getShape()
#        subdPyNode.__apimfn__().updateSubdSurface()

#        cmds.createNode('mesh')
#        cmds.undo()
#        edgeIt = api.MItSubdEdge(subdPyNode.__apimobject__())
#        while not edgeIt.isDone():
#            edgeIt.index()
#            edgeIt.next()

    def tearDown(self):
        for node in self.nodes.itervalues():
            if cmds.objExists(node):
                cmds.delete(node)
                #pass

    def test_allCompsRepresented(self):
        unableToCreate = ('kEdgeComponent',
                          'kDecayRegionCapComponent',
                          'kSetGroupComponent',
                          'kDynParticleSetComponent',
                          )
        compTypesDict = factories.getComponentTypes()
        flatCompTypes = set()
        for typesList in compTypesDict.itervalues():
            flatCompTypes.update(typesList)
        flatCompTypes = flatCompTypes - set([factories.apiTypesToApiEnums[x] for x in unableToCreate])

        notFoundCompTypes = set(flatCompTypes)
        for compDatum in self.compData.itervalues():
            testedType = compDatum.typeEnum()
            self.assert_(testedType in flatCompTypes)
            notFoundCompTypes.discard(testedType)

        if notFoundCompTypes:
            failMsg = "component types not tested:\n"
            for x in notFoundCompTypes:
                failMsg += "    " + factories.apiEnumsToApiTypes[x] + "\n"
            self.fail(failMsg)

    _indicesRe = re.compile( r'\[([^]]*)\]')

    @classmethod
    def _compStrSplit(cls, compStr):
        """
        Returns a tuple (nodeName, compName, indices).

        Indices will itself be a list.

        Example:
        >> testCase_components._compStrSplit('mySurf.uv[4][*]') # doctest: +SKIP
        ('mySurf', 'uv', ['4', '*'])
        """
        if '.' not in compStr:
            raise ValueError("compStr must be in 'nodeName.comp' form")
        nodeName, rest = compStr.split('.', 1)
        if not rest:
            compName = ''
            indices = []
        else:
            indices = cls._indicesRe.findall(rest)
            if not indices:
                compName = rest
            else:
                compName = rest.split('[', 1)[0]
        return nodeName, compName, indices

    @classmethod
    def _compStrJoin(cls, nodeName, compName, indices):
        """
        Inverse of _compStrSplit

        Given three items, nodeName, compName, indices, will
        return a component string representing that comp.

        Example:
        >> testCase_components._joinCompStr('mySurf', 'uv', ['4', '*']) # doctest: +SKIP
        'mySurf.uv[4][*]'
        """
        indicesStr = ''
        for indice in indices:
            indicesStr += '[%s]' % indice
        return '%s.%s%s' % (nodeName, compName, indicesStr)

    def _compStringsEqual(self, comp1, comp2, compData):
        # We assume that these comps have a '.' in them,
        # and that they've already been fed through
        # filterExpand, so myCube.vtx / myCubeShape.vtx
        # have been standardized
        if comp1==comp2:
            return True

        node1, comp1Name, indices1 = self._compStrSplit(comp1)
        node2, comp2Name, indices2 = self._compStrSplit(comp2)

        if node1 != node2:
            return False

        if not (comp1Name and comp2Name and
                indices1 and indices2):
            return False

        if comp1Name != comp2Name:
            # If the component names are not equal,
            # they're different components, unless
            # they're u/v/uv variants of each other...
            uvNames = ('u', 'v', 'uv')
            if (comp1Name not in uvNames or
                comp2Name not in uvNames):
                return False

        if comp1Name in ('vtxFace', 'smp', 'sme', 'smf'):
            # these types (really, any discrete component)
            # should be found
            # equal before we get here, by
            # filterExpand/setCompare -
            # so just fail these, as
            # the range information is hard to get
            return False

        # If one of them is v, we need to
        # flip the indices...
        if comp1Name == 'v':
            if len(indices1) == 0:
                pass
            elif len(indices1) == 1:
                indices1 = ['*', indices1[0]]
            elif len(indices1) == 2:
                indices1 = [indices1[1], indices1[0]]
            else:
                raise ValueError(comp1)
        if comp2Name == 'v':
            if len(indices2) == 0:
                pass
            elif len(indices2) == 1:
                indices2 = ['*', indices2[0]]
            elif len(indices2) == 2:
                indices2 = [indices2[1], indices2[0]]
            else:
                return ValueError(comp2)

        if len(indices1) < len(indices2):
            indices1 += (['*'] * (len(indices2) - len(indices1)))
        elif len(indices1) > len(indices2):
            indices2 += (['*'] * (len(indices1) - len(indices2)))

        if len(indices1) > len(compData.ranges):
            return False
        # it's ok if we have less indices than possible dimensions...

        for indice1, indice2, range in zip(indices1, indices2, compData.ranges):
            if indice1 == indice2:
                continue
            if (not self._isCompleteIndiceString(indice1, range) or
                not self._isCompleteIndiceString(indice2, range)):
                return False
        return True

    def _isCompleteIndiceString(self, indice, range):
        """
        Returns true if the given mel indice string would
        represent a 'complete' dimension for the given range.
        """
        if indice == '*':
            return True
        if indice.count(':') != 1:
            return False
        start, stop = indice.split(':')
        return float(start) == range[0] and float(stop) == range[1]

    def compsEqual(self, comp1, comp2, compData, failOnEmpty=True):
        """
        Compares two components for equality.

        The two args should either be pymel components objects, strings
        which can be selected, or a tuple or list of such objects.

        It will also return False if either component is empty, if failOnEmpty
        is True (default).
        """
        # First, make sure comp1, comp2 are both lists
        bothComps = [comp1, comp2]
        for i, comp in enumerate(bothComps):
            if isinstance(comp, (pm.Component, basestring)):
                bothComps[i] = [comp]
            else:
                # ensure it's a list, so we can modify it
                bothComps[i] = list(comp)

        # there's a bug where a comp such as:
        #   myNurbSurf.u[2]
        # will get converted to
        #   myNurbSurf.u[2][0:1]
        # when it should be
        #   myNurbSurf.u[2][0:8]
        # ...to get around it, use
        #  myNurbSurf.u[2][*]
        # See test_mayaBugs.TestSurfaceRangeDomain
        # for complete info on what will go wrong...
        if compData.pymelType in (pm.NurbsSurfaceRange, pm.NurbsSurfaceIsoparm):
            for compIterable in bothComps:
                for i, comp in enumerate(compIterable):
                    # Just worry about strings - the PyNodes
                    # are supposed to handle this bug themselves!
                    if isinstance(comp, basestring):
                        nodePart, compName, indices = self._compStrSplit(comp)
                        if compName == 'uv':
                            compPart = 'u'
                        if compName in ('u', 'v'):
                            if len(indices) < 2:
                                indices.append('*')
                        comp = self._compStrJoin(nodePart, compName, indices)
                    compIterable[i] = comp

        comp1, comp2 = bothComps



#        Comps are compared through first converting to strings
#        by selecting and using filterExpand, then by comparing the
#        the strings through string parsing.
#        This seems to be the only way to get comps such as
#        myNurbShape.v[3][0:4] and myNurb.v[3] (when the u range is 0-4,
#        and myNurbShape is the first shape of myNurb) to compare equal.


        # First, filter the results through filterExpand...
        if failOnEmpty:
            if not comp1: return False
            if not comp2: return False
        pm.select(comp1)
        comp1 = cmds.filterExpand(sm=tuple(x for x in xrange(74)))
        pm.select(comp2)
        comp2 = cmds.filterExpand(sm=tuple(x for x in xrange(74)))

        # first, filter out components whose strings are identical
        only1, both, only2 = setCompare(comp1, comp2)
        # Then, do pairwise comparison...
        # Make a copy of only1, as we'll be modifying it as we iterate
        # through...
        for comp1 in list(only1):
            for comp2 in only2:
                if self._compStringsEqual(comp1, comp2, compData):
                    only1.remove(comp1)
                    only2.remove(comp2)
                    break
            else:
                # we couldn't find a match for comp1 - fail!
                return False
        assert(not only1)
        # If only2 is now empty as well, success!
        return not only2

    def _pyCompFromString(self, compString):
        self._failIfWillMakeMayaCrash(compString)
        return eval(compString)

    # Need separate tests for PyNode / Component, b/c was bug where
    # Component('pCube1.vtx[3]') would actually return a Component
    # object, instead of a MeshVertex object, and fail, while
    # PyNode('pCube1.vtx[3]') would succeed

    def pyNodeMaker(self, compString):
        return 'pm.PyNode(%r)' % compString

    # cubeShape1.vtx[1] => PyNode('cubeShape1.vtx[1]')
    indexed_PyNode_evalStrings = MakeEvalStringCreator('mel', indexed=True)(pyNodeMaker)
    # cubeShape1.vtx[1] => PyNode('cubeShape1.vtx')
    unindexedComp_PyNode_evalStrings = MakeEvalStringCreator('mel', indexed=False)(pyNodeMaker)

    def componentMaker(self, compString):
        return 'pm.Component(%r)' % compString

    # cubeShape1.vtx[1] => Component('cubeShape1.vtx[1]')
    indexed_Component_evalStrings = MakeEvalStringCreator('mel', indexed=True)(componentMaker)
    # cubeShape1.vtx[1] => Component('cubeShape1.vtx')
    unindexedComp_Component_evalStrings = MakeEvalStringCreator('mel', indexed=False)(componentMaker)

    def object_evalStrings(self, compData):
        """
        ie, MeshVertexComponent('pCube1')
        """
        # Can't do Pivot('pCube1'), as we don't know whether we want scalePivot or rotatePivot
        if compData.pymelType == pm.Pivot:
            return []
        pymelClass = compData.pymelType
        return ['pm.%s(%r)' % (pymelClass.__name__, compData.nodeName)]

    def node_dot_comptypeMaker(self, compString):
        # node.scalePivot / node.rotatePivot returns the ATTRIBUTE,
        # so skip these.
        # (we can get the component by doing node.comp('scalePivot')
        if compString.endswith('Pivot'):
            return ''
        nodeName, compName = compString.split('.', 1)
        return 'pm.PyNode(%r).%s' % (nodeName, compName)

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    node_dot_comptypeIndex_evalStrings = MakeEvalStringCreator('pymel', indexed=True)(node_dot_comptypeMaker)
    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx
    node_dot_comptype_evalStrings = MakeEvalStringCreator('pymel', indexed=False, alwaysMakeUnindexed=True)(node_dot_comptypeMaker)

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx
    @MakeEvalStringCreator('pymel', indexed=False, alwaysMakeUnindexed=True)
    def node_dot_compFunc_evalStrings(self, compString):
        nodeName, compName = compString.split('.', 1)
        return 'pm.PyNode(%r).comp(%r)' % (nodeName, compName)

    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    @MakeEvalStringCreator('pymel', indexed=True)
    def node_dot_compFuncIndex_evalStrings(self, compString):
        nodeName, compNameAndIndex = compString.split('.', 1)
        indexSplit = compNameAndIndex.find('[')
        compName = compNameAndIndex[:indexSplit]
        indexString = compNameAndIndex[indexSplit:]
        return 'pm.PyNode(%r).comp(%r)%s' % (nodeName, compName, indexString)

    def test_objectComponentsClassEqual(self):
        successfulComps = []
        crashAvoidComps = []
        failedComps = []
        for componentData in self.compData.itervalues():
            for compString in self.object_evalStrings(componentData):
                try:
                    pymelObj = self._pyCompFromString(compString)
                except (CrashError, unittest.case._ExpectedFailure):
                    crashAvoidComps.append(compString)
                except Exception:
                    failedComps.append(compString)
                else:
                    className = compString.split('(')[0]
                    pymelClass = eval(className)
                    if pymelObj.__class__ == pymelClass:
                        successfulComps.append(compString)
                    else:
                        failedComps.append(compString)
        if failedComps:
            self.fail('Following components wrong class (or not created):\n   ' + '\n   '.join(failedComps))
        if crashAvoidComps:
            msg = 'Following components not created to avoid crash:\n   ' + '\n   '.join(failedComps)
            try:
                raise CrashError(msg)
            except:
                raise unittest.case._ExpectedFailure(sys.exc_info())


    def getComponentStrings(self, returnCompData=False, evalStringFuncs=None):
        """
        Return a list of all component strings made using this object's
        component data.

        If evalStringFuncs is given, it should be an iterable which returns
        evalString functions.

        Otherwise, the eval string function returned by
        getEvalStringFunctions(self.__class__).itervalues()
        will be used.

        If returnCompData is True, the returned list will be of tuples
            (evalString, compData)
        """
        if evalStringFuncs is None:
            evalStringFuncs = getEvalStringFunctions(self.__class__).values()
        componentStrings = set()
        for componentData in self.compData.itervalues():
            for evalStringFunc in evalStringFuncs:
                newStrings = evalStringFunc(self, componentData)
                if returnCompData:
                    newStrings = [(x, componentData) for x in newStrings]
                componentStrings.update(newStrings)
        return list(componentStrings)

    def test_componentSelection(self):
        failedCreation  = []
        failedSelections = []
        for compString in self.getComponentStrings():
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "selecting...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
                    pm.select(pymelObj, r=1)
                except Exception:
#                        import traceback
#                        traceback.print_exc()
                    failedSelections.append(compString)
                if VERBOSE:
                    print "done!"
                    printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"

        if failedCreation or failedSelections:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedSelections:
                failMsgs.append('Following components unselectable:\n   ' + '\n   '.join(failedSelections))
            self.fail('\n\n'.join(failMsgs))

    def test_component_repr(self):
        failedCreation  = []
        failedRepr = []

        for compString in self.getComponentStrings():
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if VERBOSE:
                    print "getting repr...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
                    repr(pymelObj)
                except Exception:
                    failedRepr.append(compString)
                else:
                    if VERBOSE:
                        print "done!"
                        printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"

        if failedCreation or failedRepr:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedRepr:
                failMsgs.append('Following components un-repr-able:\n   ' + '\n   '.join(failedRepr))
            self.fail('\n\n'.join(failMsgs))

    def test_componentIteration(self):
        failedCreation  = []
        failedIterations = []
        failedSelections = []
        iterationUnequal = []

        for compString,compData in self.getComponentStrings(returnCompData=True):
            printedDone = False
            if VERBOSE:
                print compString, "-", "creating...",
            try:
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                # only test iteration for discrete components!
                if not isinstance(pymelObj, pm.DiscreteComponent):
                    continue

                if VERBOSE:
                    print "iterating...",
                try:
                    self._failIfWillMakeMayaCrash(pymelObj)
                    iteration = [x for x in pymelObj]
                    iterationString = repr(iteration)
                except Exception:
#                        import traceback
#                        traceback.print_exc()
                    failedIterations.append(compString)
                else:
                    if VERBOSE:
                        print "comparing (using selection)...",
                    try:
                        pm.select(iteration)
                    except Exception:
                        failedSelections.append(iterationString)
                    else:
                        iterSel = pm.filterExpand(sm=(x for x in xrange(74)))
                        try:
                            pm.select(pymelObj)
                        except Exception:
                            failedSelections.append(compString)
                        else:
                            compSel = pm.filterExpand(sm=(x for x in xrange(74)))
                            if not self.compsEqual(iterSel, compSel, compData):
                                iterationUnequal.append(compString)
                            if VERBOSE:
                                print "done!"
                                printedDone = True
            if VERBOSE and not printedDone:
                print "FAIL!!!"

        if failedCreation or failedIterations or failedSelections or iterationUnequal:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedIterations:
                failMsgs.append('Following components uniterable:\n   ' + '\n   '.join(failedIterations))
            if failedSelections:
                failMsgs.append('Following components unselectable:\n   ' + '\n   '.join(failedSelections))
            if iterationUnequal:
                failMsgs.append('Following components iteration not equal to orignal:\n   ' + '\n   '.join(iterationUnequal))
            self.fail('\n\n'.join(failMsgs))

    def test_componentTypes(self):
        def getCompAttrName(compString):
            dotSplit = compString.split('.')
            if len(dotSplit) > 1:
                return re.split(r'\W+', dotSplit[1])[0]

        failedCreation  = []
        failedComparisons = []
        for compString, compData in self.getComponentStrings(returnCompData=True):
            try:
                pymelObj = self._pyCompFromString(compString)
            except Exception:
                failedCreation.append(compString)
            else:
                if pymelObj.__class__ != compData.pymelType:
                        failedComparisons.append(compString +
                            ' - expected: %s got: %s' % (compData.pymelType,
                                                         pymelObj.__class__))

        if failedCreation or failedComparisons:
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedComparisons:
                failMsgs.append('Following components type wrong:\n   ' + '\n   '.join(failedComparisons))
            self.fail('\n\n'.join(failMsgs))

    # There's a bug - if you add x.sme[*][*] to an
    # MSelectionList immediately
    # after creating the component, without any idle events
    # run in between, Maya crashes...
    # In gui mode, we process idle events after creation,
    # but we can't do that in batch... so if we're
    # in batch, just fail x.sme[*][*]...

    # Even more fun - on osx, any comp such as x.sm*[256][*] crashes as well...
    def _failIfWillMakeMayaCrash(self, comp):
        # As of Maya 2018 (and possibly before??), the tests in
        # test_nodetypes seem to no longer make maya crash... even though
        # test_mayaBugs.TestSubdivSelectCrash still DOES crash maya...
        # In any case, we no longer auto-fail these tests... though leaving the
        # code here in case it starts crashing things again
        return
        try:
            if isinstance(comp, basestring):
#                if versions.current() >= versions.v2011:
#                    # In 2011, MFnNurbsSurface.getKnotDomain will make maya crash,
#                    # meaning any surf.u/v/uv.__getindex__ will crash
#                    nodeName, compName, indices = self._compStrSplit(comp)
#                    if re.match(r'''(?:(u|v|uv)(Isoparm)?|comp\(u?['"](u|v|uv)(Isoparm)?['"]\))$''', compName):
#                        raise CrashError
                if (platform.system() == 'Darwin' or
                    api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                              api.MGlobal.kLibraryApp)):
                    if ((comp.startswith('pm.SubdEdge') or
                         comp.endswith("comp(u'sme')") or
                         comp.endswith('.sme'))
                        and api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                                        api.MGlobal.kLibraryApp)):
                        raise CrashError
                    elif platform.system() == 'Darwin':
                        crashRe = re.compile(r".sm[pef]('\))?\[[0-9]+\]$")
                        if crashRe.search(comp):
                            raise CrashError
            elif isinstance(comp, pm.Component):
                # Check if we're in batch - in gui, we processed idle events after subd
                # creation, which for some reason, prevents the crash
                if api.MGlobal.mayaState() in (api.MGlobal.kBatch,
                                              api.MGlobal.kLibraryApp):
                    # In windows + linux, just selections of type .sme[*][*] - on OSX,
                    # it seems any .sm*[256][*] will crash it...
                    if platform.system() == 'Darwin':
                        if (isinstance(comp, (pm.SubdEdge, pm.SubdVertex, pm.SubdFace)) and
                            comp.currentDimension() in (0, 1)):
                            raise CrashError
                    elif (isinstance(comp, pm.SubdEdge) and
                          comp.currentDimension() == 0):
                        raise CrashError
        except CrashError, e:
            print "Auto-failing %r to avoid crash..." % comp
            raise unittest.case._ExpectedFailure(sys.exc_info())

    def test_multiComponentName(self):
        compMobj = api.MFnSingleIndexedComponent().create(api.MFn.kMeshVertComponent)
        mfnComp = api.MFnSingleIndexedComponent(compMobj)
        mfnComp.addElement(0)
        mfnComp.addElement(1)
        mfnComp.addElement(2)
        mfnComp.addElement(5)
        mfnComp.addElement(7)
        mfnComp.addElement(9)
        mfnComp.addElement(11)
        myVerts = pm.MeshVertex(self.nodes['polySphere'], compMobj)
        self.assertEqual(str(myVerts), 'pSphere1.vtx[0:2,5:11:2]')

    def test_mixedPivot(self):
        pm.select(self.nodes['cube'] + '.rotatePivot', r=1)
        pm.select(self.nodes['cube'] + '.scalePivot', add=1)
        cubeName = self.nodes['cube']
        self.assertEqual(set(cmds.ls(sl=1)),
                         set(['%s.%s' % (cubeName, pivot) for pivot in ('rotatePivot', 'scalePivot')]))

    def test_mixedIsoparm(self):
        pm.select(self.nodes['sphere'] + '.u[1]', r=1)
        pm.select(self.nodes['sphere'] + '.v[0]', add=1)
        pm.select(self.nodes['sphere'] + '.uv[2][1]', add=1)
        nameAliases = set(x % self.nodes['sphere'] for x in [
                           # aliases for .u[1]
                           '%s.u[1]',
                           '%s.u[1][*]',
                           '%s.u[1][0:8]',
                           '%s.uv[1]',
                           '%s.uv[1][*]',
                           '%s.uv[1][0:8]',
                           # aliases for .v[0]
                           '%s.v[0]',
                           '%s.v[0][*]',
                           '%s.v[0][0:4]',
                           '%s.uv[*][0]',
                           '%s.uv[0:4][0]',
                           # aliases for .uv[2][1]
                           '%s.u[2][1]',
                           '%s.v[1][2]',
                           '%s.uv[2][1]'])
        selected = set(cmds.ls(sl=1))
        self.assertTrue(selected.issubset(nameAliases))

    def test_nurbsIsoPrintedRange(self):
        # Maya has a bug -running:
        #
        # import maya.cmds as cmds
        # cmds.sphere()
        # cmds.select('nurbsSphere1.uv[*][*]')
        # print cmds.ls(sl=1)
        # cmds.select('nurbsSphere1.u[*][*]')
        # print cmds.ls(sl=1)
        #
        # Gives two different results:
        # [u'nurbsSphere1.u[0:4][0:1]']
        # [u'nurbsSphere1.u[0:4][0:8]']
        sphereShape = pm.PyNode(self.nodes['sphere']).getShape().name()
        nameAliases = [x % sphereShape for x in [
                           '%s.u[*]',
                           '%s.u[*][*]',
                           '%s.u[0:4][0:8]',
                           '%s.uv[*]',
                           '%s.uv[*][*]',
                           '%s.uv[0:4][0:8]',
                           '%s.v[*]',
                           '%s.v[*][*]',
                           '%s.v[0:8][0:4]']]
        pynodeStr = str(pm.PyNode(self.nodes['sphere']).uv)
        self.assertTrue(pynodeStr in nameAliases,
                        '%s not equivalent to %s.uv[0:4][0:8]' % (pynodeStr,sphereShape))

    def test_meshVertConnnectedFaces(self):
        # For a standard cube, vert 3 should be connected to
        # faces 0,1,4
        desiredFaceStrings = ['%s.f[%d]' % (self.nodes['cube'], x) for x in (0,1,4)]
        connectedFaces = pm.PyNode(self.nodes['cube']).vtx[3].connectedFaces()
        self.assertTrue(self.compsEqual(desiredFaceStrings, connectedFaces, self.compData['meshFace']))

    def test_indiceChecking(self):
        # Check for a DiscreteComponent...
        cube = pm.PyNode(self.nodes['cube'])
        cube.vtx[2]
        cube.vtx[7]
        cube.vtx[-8]
        cube.vtx[-8:7]
        self.assertRaises(IndexError, cube.vtx.__getitem__, 8)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(0,8))
        self.assertRaises(IndexError, cube.vtx.__getitem__, -9)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(-9,7))
        self.assertRaises(IndexError, cube.vtx.__getitem__, 'foo')
        self.assertRaises(IndexError, cube.vtx.__getitem__, 5.2)
        self.assertRaises(IndexError, cube.vtx.__getitem__, slice(0,5.2))

        # Check for a ContinuousComponent...
        sphere = pm.PyNode(self.nodes['sphere'])
        self._failIfWillMakeMayaCrash('%s.u[2]' % sphere.name())
        sphere.u[2]
        sphere.u[4]
        sphere.u[0]
        sphere.u[0:4]
        self.assertRaises(IndexError, sphere.u.__getitem__, 4.1)
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(0,5))
        self.assertRaises(IndexError, sphere.u.__getitem__, -2)
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(-.1,4))
        self.assertRaises(IndexError, sphere.u.__getitem__, 'foo')
        self.assertRaises(IndexError, sphere.u.__getitem__, slice(0,'foo'))

    def test_melIndexing(self):
        melString = '%s.vtx[1:4]' % self.nodes['cube']
        self.assertTrue(self.compsEqual(melString, pm.PyNode(melString), self.compData['meshVtx']))


    # cubeShape1.vtx[1] => PyNode('cubeShape1').vtx[1]
    node_dot_comptypeIndex_evalStrings = MakeEvalStringCreator('pymel', indexed=True)(node_dot_comptypeMaker)

    def test_melPyMelCompsEqual(self):
        def pairedStrings(self, compStringPair):
            # The mel compString we don't need to alter...
            # For the PyNode, use PyNode('cubeShape1').vtx[1] syntax
            return (compStringPair[0], self.node_dot_comptypeMaker(compStringPair[1]))

        unindexedPairedStrings = MakeEvalStringCreator('both', indexed=False)(pairedStrings)
        indexedPairedStrings = MakeEvalStringCreator('both', indexed=True)(pairedStrings)
        failedCreation  = []
        failedDuringCompare = []
        failedComparison = []
        for componentData in self.compData.itervalues():
            evalStringPairs = itertools.chain(unindexedPairedStrings(self, componentData),
                                              indexedPairedStrings(self, componentData))
            for melString, pyString in evalStringPairs:
                printedDone = False
                if VERBOSE:
                    print melString, "/", pyString, "-", "creating...",
                try:
                    pymelObj = self._pyCompFromString(pyString)
                except Exception:
                    failedCreation.append(pyString)
                else:
                    if VERBOSE:
                        print "comparing...",
                    try:
                        areEqual = self.compsEqual(melString, pymelObj, componentData)
                    except Exception:
                        #raise
                        failedDuringCompare.append(str( (melString, pyString) ))
                    else:
                        if not areEqual:
                            failedComparison.append(str( (melString, pyString) ))
                        else:
                            if VERBOSE:
                                print "done!"
                            printedDone = True
                if not printedDone and VERBOSE:
                    print "FAIL!!!"

        if any( (failedCreation, failedDuringCompare, failedComparison) ):
            failMsgs = []
            if failedCreation:
                failMsgs.append('Following components not created:\n   ' + '\n   '.join(failedCreation))
            if failedDuringCompare:
                failMsgs.append('Following components had error during compare:\n   ' + '\n   '.join(failedDuringCompare))
            if failedComparison:
                failMsgs.append('Following components unequal:\n   ' + '\n   '.join(failedComparison))
            self.fail('\n\n'.join(failMsgs))

    def test_extendedSlices(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        pyCube = pm.PyNode('pCube1')
        check(pyCube.e[2:11:3],
              ('pCubeShape1.e[11]', 'pCubeShape1.e[8]',
               'pCubeShape1.e[5]', 'pCubeShape1.e[2]'),
              self.compData['meshEdge'])
        pySphere = pm.PyNode('nurbsSphere1')
        check(pySphere.cv[1:5:2][1:4:3],
              ('nurbsSphereShape1.cv[1][4]', 'nurbsSphereShape1.cv[1][1]',
               'nurbsSphereShape1.cv[3][4]', 'nurbsSphereShape1.cv[3][1]',
               'nurbsSphereShape1.cv[5][4]', 'nurbsSphereShape1.cv[5][1]'),
              self.compData['nurbsCV'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))

    def test_continuousCompRanges(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        check(self._pyCompFromString("pm.PyNode('nurbsSphere1').vIsoparm[5.54][1.1:3.4]"),
              'nurbsSphereShape1.u[1.1:3.4][5.54]',
              self.compData['nurbsIsoUV'])
        check(self._pyCompFromString("pm.PyNode('nurbsCircle1').u[2.8:6]"),
              'nurbsCircleShape1.u[2.8:6]',
              self.compData['curvePt'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))

    def test_negativeDiscreteIndices(self):
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        pyCurve = pm.PyNode('nurbsCircle1')
        # Breaking into extra lines here just to make debugging easier
        pyCurveShape = pyCurve.getShape()
        knot = pyCurveShape.knot
        knotNeg3 = knot[-3]
        check(knotNeg3,
              'nurbsCircleShape1.knot[10]',
              self.compData['curveKnot'])
        pyLattice = pm.PyNode('ffd1Lattice')
        check(pyLattice.pt[-1][-5:-2][-2],
              ('ffd1LatticeShape.pt[2][0][2]',
               'ffd1LatticeShape.pt[2][1][2]',
               'ffd1LatticeShape.pt[2][2][2]'),
              self.compData['lattice'])
        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))

    def test_negativeContinuousIndices(self):
        # For continous comps, these should behave just like positive ones...
        failedComps = []
        def check(pynode, expectedStrings, compData):
            if not self.compsEqual(pynode, expectedStrings, compData):
                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))

        surf = pm.PyNode('surfaceShape1')
        check(surf.uv[-3.3][.5],
              'surfaceShape1.u[-3.3][.5]',
              self.compData['negNurbsIso'])
        check(surf.uv[-8:-5.1][0],
              'surfaceShape1.u[-8:-5.1][0]',
              self.compData['negNurbsIso'])

        if failedComps:
            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))

    def test_multipleIterations(self):
        """
        Make sure that, on repeated iterations through a component, we get the same result.
        """
        comp = pm.PyNode(self.nodes['cube']).e[3:10]
        iter1 = [x for x in comp]
        iter2 = [x for x in comp]
        self.assertEqual(iter1, iter2)

    # Disabling this for now - such indicing wasn't possible in 0.9.x, either,
    # so while I'd like to get this working at some point, it's not necessary for now...
#    def test_multipleNoncontiguousIndices(self):
#        """
#        test things like .vtx[1,2,5:7]
#        """
#        failedComps = []
#        def check(pynode, expectedStrings, compData):
#            if not self.compsEqual(pynode, expectedStrings, compData):
#                failedComps.append(repr(pynode) + '\n      not equal to:\n   ' + str(expectedStrings))
#
#        cube = pm.PyNode('pCube1')
#        vtx = cube.vtx
#        check(vtx[1,2,5:7],
#              ('pCubeShape1.vtx[1]',
#               'pCubeShape1.vtx[2]',
#               'pCubeShape1.vtx[5]',
#               'pCubeShape1.vtx[6]',
#               'pCubeShape1.vtx[7]'),
#              self.compData['meshVtx'])
#
#        ffd = pm.PyNode('ffd1LatticeShape')
#        pt = ffd.pt
#        check(pt[0,1][1,2,4,][0,2],
#              ('ffd1LatticeShape.pt[0][1][0]',
#               'ffd1LatticeShape.pt[0][1][2]',
#               'ffd1LatticeShape.pt[0][2][0]',
#               'ffd1LatticeShape.pt[0][2][2]',
#               'ffd1LatticeShape.pt[0][4][0]',
#               'ffd1LatticeShape.pt[0][4][2]',
#               'ffd1LatticeShape.pt[1][1][0]',
#               'ffd1LatticeShape.pt[1][1][2]',
#               'ffd1LatticeShape.pt[1][2][0]',
#               'ffd1LatticeShape.pt[1][2][2]',
#               'ffd1LatticeShape.pt[1][4][0]',
#               'ffd1LatticeShape.pt[1][4][2]',
#               ),
#               self.compData['lattice'])
#
#        if failedComps:
#            self.fail('Following components did not yield expected components:\n   ' + '\n   '.join(failedComps))

    def test_totalSize_meshVtx(self):
        self.assertEqual(pm.PyNode(self.nodes['cube']).vtx.totalSize(), 8)
    def test_totalSize_meshEdge(self):
        self.assertEqual(pm.PyNode(self.nodes['cube']).edges.totalSize(), 12)
    def test_totalSize_meshFace(self):
        self.assertEqual(pm.PyNode(self.nodes['cube']).faces.totalSize(), 6)
    def test_totalSize_meshUV(self):
        # default cube uv layout is "t-shape" - so 14 uvs
        self.assertEqual(pm.PyNode(self.nodes['cube']).uvs.totalSize(), 14)
    def test_totalSize_meshVtxFace(self):
        self.assertEqual(pm.PyNode(self.nodes['cube']).vtxFace.totalSize(), 24)
    def test_totalSize_curveCV(self):
        self.assertEqual(pm.PyNode(self.nodes['curve']).cv.totalSize(), 8)
    def test_totalSize_curveEP(self):
        self.assertEqual(pm.PyNode(self.nodes['curve']).ep.totalSize(), 8)
    def test_totalSize_curveKnot(self):
        self.assertEqual(pm.PyNode(self.nodes['curve']).knots.totalSize(), 13)
    def test_totalSize_nurbsCV(self):
        self.assertEqual(pm.PyNode(self.nodes['sphere']).cv.totalSize(), 56)
    def test_totalSize_nurbsPatch(self):
        self.assertEqual(pm.PyNode(self.nodes['sphere']).faces.totalSize(), 32)
    def test_totalSize_nurbsEP(self):
        self.assertEqual(pm.PyNode(self.nodes['sphere']).ep.totalSize(), 40)
    def test_totalSize_nurbsKnot(self):
        self.assertEqual(pm.PyNode(self.nodes['sphere']).knots.totalSize(), 117)
    def test_totalSize_lattice(self):
        self.assertEqual(pm.PyNode(self.nodes['lattice']).pt.totalSize(),
                         self.latticeSize[0] * self.latticeSize[1] * self.latticeSize[2])

    def test_stringComp_indexing(self):
        comp = pm.PyNode('%s.vtx[*]' % self.nodes['cube'])
        compIndex = comp[2];
        self.assertEqual(compIndex.getPosition(), pm.dt.Point(-0.5, 0.5, 0.5))

    def test_listComp(self):
        nodeTypes = {'cube':pm.nt.Mesh,
                     'subd':pm.nt.Subdiv,
                     'curve':pm.nt.NurbsCurve,
                     'sphere':pm.nt.NurbsSurface,
                     'lattice':pm.nt.Lattice,
                    }

        def assertListCompForNodeClass(node, nodeClass):
            compNames = sorted(nodeClass._componentAttributes)
            compTypes = set()
            uniqueNames = []
            for compName in compNames:
                compType = nodeClass._componentAttributes[compName]
                if compType not in compTypes:
                    compTypes.add(compType)
                    uniqueNames.append(compName)
            self.assertEqual(node.listComp(names=True), compNames)
            comps = []
            for name in uniqueNames:
                comps.append(node.comp(name))
            self.assertEqual(node.listComp(), comps)


        for typeName, nodeClass in nodeTypes.iteritems():
            print typeName, nodeClass
            trans = pm.PyNode(self.nodes[typeName])
            assertListCompForNodeClass(trans, pm.nt.Transform)
            shape = trans.getShape()
            assertListCompForNodeClass(shape, nodeClass)

    def test_list_and_slice_getitem(self):
        cube = self.nodes['cube']
        faces = pm.PyNode(cube).f[0:2, 4]
        self.assertEqual(faces.indices(), [0, 1, 2, 4])
        pm.select(faces)
        selStrs = [
            '{cube}.f[0:2]',
            '{cube}.f[4]'
        ]
        selStrs = list(x.format(cube=cube) for x in selStrs)
        self.assertEqual(cmds.ls(sl=1), selStrs)

    def test_tuple_getitem(self):
        cube = self.nodes['cube']
        faces = pm.PyNode(cube).f[0, 1, 2, 4]
        self.assertEqual(faces.indices(), [0, 1, 2, 4])
        pm.select(faces)
        selStrs = [
            '{cube}.f[0:2]',
            '{cube}.f[4]'
        ]
        selStrs = list(x.format(cube=cube) for x in selStrs)
        self.assertEqual(cmds.ls(sl=1), selStrs)

    def test_list_getitem(self):
        cube = self.nodes['cube']
        indices = [0, 1, 2, 4]
        faces = pm.PyNode(cube).f[indices]
        self.assertEqual(faces.indices(), [0, 1, 2, 4])
        pm.select(faces)
        selStrs = [
            '{cube}.f[0:2]',
            '{cube}.f[4]'
        ]
        selStrs = list(x.format(cube=cube) for x in selStrs)
        self.assertEqual(cmds.ls(sl=1), selStrs)

    def test_iterable_getitem(self):
        cube = self.nodes['cube']
        indices = iter([0, 1, 2, 4])
        faces = pm.PyNode(cube).f[indices]
        self.assertEqual(faces.indices(), [0, 1, 2, 4])
        pm.select(faces)
        selStrs = [
            '{cube}.f[0:2]',
            '{cube}.f[4]'
        ]
        selStrs = list(x.format(cube=cube) for x in selStrs)
        self.assertEqual(cmds.ls(sl=1), selStrs)

    def test_add(self):
        cube = self.nodes['cube']
        verts0str = '{cube}.vtx[0:2]'.format(cube=cube)
        verts1str = '{cube}.vtx[6:7]'.format(cube=cube)
        verts0 = pm.PyNode(verts0str)
        verts1 = pm.PyNode(verts1str)
        pm.select(verts0)
        self.assertEqual(cmds.ls(sl=1), [verts0str])
        pm.select(verts1)
        self.assertEqual(cmds.ls(sl=1), [verts1str])
        verts01 = verts0 + verts1
        pm.select(verts0)
        self.assertEqual(cmds.ls(sl=1), [verts0str])
        pm.select(verts1)
        self.assertEqual(cmds.ls(sl=1), [verts1str])
        pm.select(verts01)
        self.assertEqual(cmds.ls(sl=1), [verts0str, verts1str])
        verts0 += verts1
        pm.select(verts0)
        self.assertEqual(cmds.ls(sl=1), [verts0str, verts1str])
        pm.select(verts1)
        self.assertEqual(cmds.ls(sl=1), [verts1str])


for propName, evalStringFunc in \
        getEvalStringFunctions(testCase_components).iteritems():
    evalStringId = '_evalStrings'
    if propName.endswith(evalStringId):
        baseName = propName[:-len(evalStringId)].capitalize()
        newFuncName = 'test_' + baseName + '_ComponentCreation'
        setattr(testCase_components, newFuncName,
            makeComponentCreationTests(evalStringFunc, funcName=newFuncName))

class testCase_DagNode(TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)

    def test_getParent(self):
        tg1     = pm.createNode('transform', name='topGroup1')
        tg1c1   = pm.createNode('transform',    name='tg1_child1', parent='topGroup1')
        tg1c1g1 = pm.createNode('transform',        name='tg1_c1_grandkid1', parent='tg1_child1')
        tg1c1g2 = pm.createNode('transform',        name='tg1_c1_grandkid2', parent='tg1_child1')
        tg1c2   = pm.createNode('transform',    name='tg1_child2', parent='topGroup1')
        tg2     = pm.createNode('transform', name='topGroup2')
        tg2c2   = pm.createNode('transform',    name='tg2_child1', parent='topGroup2')
        # try some non-unique names
        tg3     = pm.createNode('transform', name='topGroup3')
        tg3c1   = pm.createNode('transform',    name='child1', parent='topGroup3')
        tg3c1c1 = pm.createNode('transform',        name='child1', parent='topGroup3|child1')
        tg4     = pm.createNode('transform', name='topGroup4')
        tg4c1   = pm.createNode('transform',    name='child1', parent='topGroup4')

        self.assertEqual(tg1c1g1.getParent(), tg1c1)

        self.assertEqual(tg1c1g1.getParent(0), tg1c1g1)
        self.assertEqual(tg1c1g1.getParent(generations=1), tg1c1)
        self.assertEqual(tg1c1g1.getParent(2), tg1)
        self.assertEqual(tg1c1g1.getParent(generations=3), None)
        self.assertEqual(tg1c1g1.getParent(-1), tg1)
        self.assertEqual(tg1c1g1.getParent(generations=-2), tg1c1)
        self.assertEqual(tg1c1g1.getParent(-3), tg1c1g1)
        self.assertEqual(tg1c1g1.getParent(generations=-4), None)
        self.assertEqual(tg1c1g1.getParent(-5), None)
        self.assertEqual(tg1c1g1.getParent(generations=4), None)
        self.assertEqual(tg1c1g1.getParent(-63), None)
        self.assertEqual(tg1c1g1.getParent(generations=32), None)

        self.assertEqual(tg1c1g1.getAllParents(), [tg1c1, tg1])

        self.assertEqual(tg3c1.getParent(generations=1), tg3)
        self.assertEqual(tg3c1c1.getParent(generations=2), tg3)
        self.assertEqual(tg3c1.getParent(generations=-1), tg3)

        self.assertEqual(tg3c1c1.getAllParents(), [tg3c1, tg3])
        self.assertEqual(tg3c1.getAllParents(), [tg3])
        self.assertEqual(tg3.getAllParents(), [])

    def test_isVisible(self):
        setA = []
        setB = []
        vis = [1,1,0,0,1,0,0,1]
        z = 0
        for x in range(8):
            setA.append(pm.createNode('transform', name='setA%d' % x))
            setB.append(pm.createNode('transform', name='setB%d' % x))

        for x in range(4):
            setA[x+4].setParent(setA[x])
            setB[x+4].setParent(setB[x])

        for x in range(8):
            setA[x].visibility.set(vis[x])
            setB[x].visibility.set(vis[x])

        for x in range(8):
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible())
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=True))
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=False))

        for x in range(8):
            setB[x].overrideEnabled.set(1)
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible())
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=True))
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=False))

        for x in range(8):
            setB[x].overrideVisibility.set(1)
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible())
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=True))
            self.assertEqual(setA[x].isVisible(), setB[x].isVisible(checkOverride=False))

        for x in range(8):
            setB[x].overrideVisibility.set(0)
            self.assertFalse(setB[x].isVisible())

class testCase_Shape(TestCaseExtended):
    def setUp(self):
        self.trans, self.polySphere = pm.polySphere()
        self.shape = self.trans.getShape()

    def test_getTransform(self):
        self.assertEqual(self.shape.getTransform(), self.trans)

    def tearDown(self):
        pm.delete(self.trans)

class testCase_transform(TestCaseExtended):
    def setUp(self):
        self.trans = pm.createNode('transform')
        self.trans.setRotationOrder('XYZ', False)

    def tearDown(self):
        pm.delete(self.trans)

    def test_setRotation(self):
        #Check dt.EulerRotation when angle unit differs
        oldUnit = pm.currentUnit(q=1, angle=1)
        try:
            pm.currentUnit(angle='degree')

            # Check dt.EulerRotation input
            euler = pm.dt.EulerRotation(10, 20, 30)
            self.trans.setRotation(euler)
            self.assertRotationsEqual(euler, self.trans.attr('rotate').get())

            # Check dt.Quaternion input
            euler = pm.dt.EulerRotation(5, 15, -16)
            quat = pm.dt.Quaternion(euler.asQuaternion())
            self.trans.setRotation(quat)
            self.assertRotationsEqual(euler, self.trans.attr('rotate').get())

            # Check api.MEulerRotation input
            angles = (10, 20, 30)
            euler = pm.api.MEulerRotation(*[math.radians(x) for x in angles])
            self.trans.setRotation(euler)
            self.assertRotationsEqual(angles, self.trans.attr('rotate').get())

            # Check api.MQuaternion input
            angles = (5, 15, -16)
            euler = pm.api.MEulerRotation(*[math.radians(x) for x in angles])
            quat = euler.asQuaternion()
            self.trans.setRotation(quat)
            self.assertRotationsEqual(angles, self.trans.attr('rotate').get())

            # Check list of size 3 input
            angles = (10, 20, 30)
            self.trans.setRotation(angles)
            self.assertRotationsEqual(angles, self.trans.attr('rotate').get())

            # Check list of size 4 input
            angles = (5, 15, -16)
            euler = pm.api.MEulerRotation(*[math.radians(x) for x in angles])
            quat = pm.dt.Quaternion(euler.asQuaternion())
            quatVals = list(quat)
            self.trans.setRotation(quatVals)
            self.assertRotationsEqual(angles, self.trans.attr('rotate').get())

            #Check dt.EulerRotation when euler rotation order non-standard
            origAngles = (10, 20, 30, 'YXZ')
            euler = pm.dt.EulerRotation(*origAngles)
            self.trans.setRotation(euler)
            euler.reorderIt('XYZ')
            self.assertRotationsEqual(euler, self.trans.attr('rotate').get())
            self.trans.setRotationOrder('YXZ', True)
            try:
                self.assertRotationsEqual(origAngles[:3], self.trans.attr('rotate').get())
            finally:
                self.trans.setRotationOrder('XYZ', False)

            #Check dt.EulerRotation when trans rotation order non-standard
            origAngles = (10, 20, 30, 'XYZ')
            euler = pm.dt.EulerRotation(*origAngles)
            self.trans.setRotationOrder('ZYX', False)
            try:
                self.trans.setRotation(euler)
                euler.reorderIt('ZYX')
                self.assertRotationsEqual(euler, self.trans.attr('rotate').get())
            finally:
                self.trans.setRotationOrder('XYZ', True)
            self.assertRotationsEqual(origAngles[:3], self.trans.attr('rotate').get())

            # Check dt.EulerRotation input with radian angles
            degAngles = (5, 15, -16)
            radAngles = [math.radians(x) for x in degAngles]
            euler = pm.dt.EulerRotation(*radAngles, unit='radians')
            self.trans.setRotation(euler)
            self.assertRotationsEqual(degAngles, self.trans.attr('rotate').get())
        finally:
            pm.currentUnit(angle=oldUnit)

    def test_rotateByQuaternion(self):
        # Check dt.Quaternion input
        euler = pm.dt.EulerRotation(5, 15, -16)
        quat = pm.dt.Quaternion(euler.asQuaternion())
        self.trans.rotateByQuaternion(quat)
        self.assertRotationsEqual(euler, self.trans.attr('rotate').get())
        self.trans.rotateByQuaternion(quat)
        eulerSquared = (quat * quat).asEulerRotation()
        eulerSquared.unit = pm.dt.Angle.getUIUnit()
        self.assertRotationsEqual(eulerSquared, self.trans.attr('rotate').get())

    def assertRotationsEqual(self, rot1, rot2):
        if not len(rot1) == len(rot2):
            raise ValueError("rotation values must have same length: %r, %r" % (rot1, rot2))
        for i, (aVal, bVal) in enumerate(zip(rot1, rot2)):
            self.assertAlmostEqual(aVal, bVal,
                                   msg="component %i of rotations not equal (%s != %s)"
                                        % (i, aVal, bVal))

    def test_rotateOrientation(self):
        # test that getRotateOrientation / setRotateOrientation work
        noRot = pm.dt.Quaternion.identity
        self.assertRotationsEqual(noRot, self.trans.getRotateOrientation())
        rot1 = pm.dt.Quaternion(pm.dt.Vector(1, 0, 0), pm.dt.Vector(1,2,3))
        rot2 = pm.dt.Quaternion(pm.dt.Vector(1, 0, 0), .5)
        self.trans.setRotateOrientation(rot1, balance=False)
        self.assertRotationsEqual(rot1, self.trans.getRotateOrientation())
        self.trans.setRotateOrientation(rot2, balance=False)
        self.assertRotationsEqual(rot2, self.trans.getRotateOrientation())
        pm.undo()
        self.assertRotationsEqual(rot1, self.trans.getRotateOrientation())
        pm.undo()
        self.assertRotationsEqual(noRot, self.trans.getRotateOrientation())
        pm.redo()
        self.assertRotationsEqual(rot1, self.trans.getRotateOrientation())
        pm.redo()
        self.assertRotationsEqual(rot2, self.trans.getRotateOrientation())


class testCase_nurbsSurface(TestCaseExtended):
    def setUp(self):
        self.negUSurf = pm.PyNode(pm.surface(name='periodicSurf', du=3, dv=1,
                                       fu='periodic', fv='open',
                                       ku=range(-13, 0, 1), kv=(0, 1),
                                       pw=[(4, -4, 0, 1), (4, -4, -2.5, 1),
                                           (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                           (4, 4, 0, 1), (4, 4, -2.5, 1),
                                           (0, 5.5, 0, 1), (0, 5.5, -2.5, 1),
                                           (-4, 4, 0, 1), (-4, 4, -2.5, 1),
                                           (-5.5, 0, 0, 1), (-5.5, 0, -2.5, 1),
                                           (-4, -4, 0, 1), (-4, -4, -2.5, 1),
                                           (0, -5.5, 0, 1), (0, -5.5, -2.5, 1),
                                           (4, -4, 0, 1), (4, -4, -2.5, 1),
                                           (5.5, 0, 0, 1), (5.5, 0, -2.5, 1),
                                           (4, 4, 0, 1), (4, 4, -2.5, 1)] ))

    def tearDown(self):
        pm.delete(self.negUSurf)

    def test_knotDomain(self):
        # Was a bug with this, due to automatic wrapping of api 'unsigned int &' args
        self.assertEqual(self.negUSurf.getKnotDomain(), (-11.0, -3.0, 0.0, 1.0))


class testCase_camera(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)

    def test_failedSetNear_noUndoCreated(self):
        # api-wrapped commands that error should not create an api undo item!
        cam = pm.createNode('camera')
        cam.setNearClippingPlane(.01)
        pm.flushUndo()
        self.assertEqual(cam.getNearClippingPlane(), .01)
        cam.setNearClippingPlane(.02)
        self.assertEqual(cam.getNearClippingPlane(), .02)
        self.assertRaises(RuntimeError, cam.setNearClipPlane, -5)
        self.assertEqual(cam.getNearClippingPlane(), .02)
        # this undo shouldn't undo our failed attemp tto set the near clip
        # plane... instead, it should undo the last successful thng we did,
        # which was change it from .01 to .02
        pm.undo()
        self.assertEqual(cam.getNearClippingPlane(), .01)

    def test_setNearFarClippingPlanes(self):
        cam = pm.createNode('camera')
        near = cam.attr('nearClipPlane')
        far = cam.attr('farClipPlane')
        near.set(.1)
        far.set(1000)
        pm.flushUndo()
        self.assertEqual(cam.getNearClipPlane(), .1)
        self.assertEqual(cam.getFarClipPlane(), 1000)
        cam.setNearFarClippingPlanes(.2, 2000)
        self.assertEqual(cam.getNearClipPlane(), .2)
        self.assertEqual(cam.getFarClipPlane(), 2000)
        cam.setNearFarClippingPlanes(.3, 3000)
        self.assertEqual(cam.getNearClipPlane(), .3)
        self.assertEqual(cam.getFarClipPlane(), 3000)
        pm.undo()
        self.assertEqual(cam.getNearClipPlane(), .2)
        self.assertEqual(cam.getFarClipPlane(), 2000)
        pm.undo()
        self.assertEqual(cam.getNearClipPlane(), .1)
        self.assertEqual(cam.getFarClipPlane(), 1000)
        pm.redo()
        self.assertEqual(cam.getNearClipPlane(), .2)
        self.assertEqual(cam.getFarClipPlane(), 2000)
        cam.setNearFarClippingPlanes(.4, 4000)
        self.assertEqual(cam.getNearClipPlane(), .4)
        self.assertEqual(cam.getFarClipPlane(), 4000)
        pm.undo()
        self.assertEqual(cam.getNearClipPlane(), .2)
        self.assertEqual(cam.getFarClipPlane(), 2000)
        pm.undo()
        self.assertEqual(cam.getNearClipPlane(), .1)
        self.assertEqual(cam.getFarClipPlane(), 1000)
        pm.redo()
        self.assertEqual(cam.getNearClipPlane(), .2)
        self.assertEqual(cam.getFarClipPlane(), 2000)
        pm.redo()
        self.assertEqual(cam.getNearClipPlane(), .4)
        self.assertEqual(cam.getFarClipPlane(), 4000)


class testCase_joint(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)

#    def test_getAbsolute(self):
#        # Was a bug with this, due to handling of methods which needed casting AND unpacking
#        self.assertEqual(self.j.getAbsolute(), (4,5,6))

    def test_angleX(self):
        joint = pm.nt.Joint(angleX=31.5)
        self.assertEqual(joint.getAngleX(), 31.5)
        joint.setAngleX(20.2)
        self.assertEqual(joint.getAngleX(), 20.2)
        pm.delete(joint)

    def test_angleY(self):
        joint = pm.nt.Joint(angleY=31.5)
        self.assertEqual(joint.getAngleY(), 31.5)
        joint.setAngleY(20.2)
        self.assertEqual(joint.getAngleY(), 20.2)
        pm.delete(joint)

    def test_angleZ(self):
        joint = pm.nt.Joint(angleZ=31.5)
        self.assertEqual(joint.getAngleZ(), 31.5)
        joint.setAngleZ(20.2)
        self.assertEqual(joint.getAngleZ(), 20.2)
        pm.delete(joint)

    def test_radius(self):
        # Was a bug with this, due to handling of methods which needed unpacking (but not casting)
        joint = pm.nt.Joint(radius=31.5)
        self.assertEqual(joint.getRadius(), 31.5)
        joint.setRadius(20.2)
        self.assertEqual(joint.getRadius(), 20.2)
        pm.delete(joint)

    def test_stiffnessX(self):
        joint = pm.nt.Joint(stiffnessX=31.5)
        self.assertEqual(joint.getStiffnessX(), 31.5)
        joint.setStiffnessX(20.2)
        self.assertEqual(joint.getStiffnessX(), 20.2)
        pm.delete(joint)

    def test_stiffnessY(self):
        joint = pm.nt.Joint(stiffnessY=31.5)
        self.assertEqual(joint.getStiffnessY(), 31.5)
        joint.setStiffnessY(20.2)
        self.assertEqual(joint.getStiffnessY(), 20.2)
        pm.delete(joint)

    def test_stiffnessZ(self):
        joint = pm.nt.Joint(stiffnessZ=31.5)
        self.assertEqual(joint.getStiffnessZ(), 31.5)
        joint.setStiffnessZ(20.2)
        self.assertEqual(joint.getStiffnessZ(), 20.2)
        pm.delete(joint)


class testCase_sets(TestCaseExtended):
    def setUp(self):
        cmds.file(new=1, f=1)
        self.cube = pm.polyCube()[0]
        self.sphere = pm.sphere()[0]
        self.set = pm.sets()
    def assertSetSelect(self, setClass, *items):
        """
        Generator function which tests the given set type.
        It first selects the items, saves the list of the selected items, and makes a set
        from the selected items. Then it
            - selects the items in the set
            - calls set.members()
        and compares each of the results to the initial selection.
        """
        pm.select(items)
        initialSel = cmds.ls(sl=1)
        if issubclass(setClass, pm.nt.ObjectSet):
            mySet = pm.sets(initialSel)
        else:
            mySet = pm.nt.SelectionSet(initialSel)
        self.assertNoError(pm.select, mySet)
        self.assertIteration(initialSel, cmds.ls(sl=1),
                             orderMatters=False)
        if issubclass(setClass, pm.nt.ObjectSet):
            myList = mySet.members()
        else:
            myList = list(mySet)
        pm.select(myList)
        newSel = cmds.ls(sl=1)
        self.assertIteration(initialSel, newSel, orderMatters=False)

    def test_ObjectSet_singleObject(self):
        self.assertSetSelect(pm.nt.ObjectSet, self.cube)

    def test_ObjectSet_multiObject(self):
        self.assertSetSelect(pm.nt.ObjectSet, self.cube, self.sphere)

    def test_ObjectSet_vertices(self):
        self.assertSetSelect(pm.nt.ObjectSet, self.cube.vtx[1:3])

    def test_ObjectSet_mixedObjectsComponents(self):
        self.assertSetSelect(pm.nt.ObjectSet, self.cube.edges[4:6], self.sphere)

    def test_SelectionSet_singleObject(self):
        self.assertSetSelect(pm.nt.SelectionSet, self.cube)

    def test_SelectionSet_multiObject(self):
        self.assertSetSelect(pm.nt.SelectionSet, self.cube, self.sphere)

    def test_SelectionSet_vertices(self):
        self.assertSetSelect(pm.nt.SelectionSet, self.cube.vtx[1:3])

    def test_SelectionSet_mixedObjectsComponents(self):
        self.assertSetSelect(pm.nt.SelectionSet, self.cube.edges[4:6], self.sphere)

    def test_SelectionSet_nestedSets(self):
        self.assertSetSelect(pm.nt.SelectionSet, self.set)

    def test_ObjectSet_len(self):
        mySet = pm.sets(name='mySet', empty=True)
        self.assertEqual(len(mySet), 0)
        mySet.add('persp')
        self.assertEqual(len(mySet), 1)
        mySet.add('perspShape')
        self.assertEqual(len(mySet), 2)

    def test_SelectionSet_len(self):
        mySet = pm.nt.SelectionSet([])
        self.assertEqual(len(mySet), 0)
        mySet.add('persp')
        self.assertEqual(len(mySet), 1)
        mySet.add('perspShape')
        self.assertEqual(len(mySet), 2)



#class testCase_0_7_compatabilityMode(unittest.TestCase):
#    # Just used to define a value that we know won't be stored in
#    # 0_7_compatability mode...
#    class NOT_SET(object): pass
#
#    def setUp(self):
#        self.stored_0_7_compatability_mode = factories.pymel_options.get( '0_7_compatibility_mode', False)
#        factories.pymel_options['0_7_compatibility_mode'] = True
#
#    def tearDown(self):
#        if self.stored_0_7_compatability_mode == NOT_SET:
#            del factories.pymel_options['0_7_compatibility_mode']
#        else:
#            factories.pymel_options['0_7_compatibility_mode'] = self.stored_0_7_compatability_mode
#
#    def test_nonexistantPyNode(self):
#        # Will raise an error if not in 0_7_compatability_mode
#        pm.PyNode('I_Dont_Exist_3142341324')
#

class testCase_apiArgConversion(unittest.TestCase):
    def test_unsignedIntRef_out_args(self):
        # the MFnLattice.getDivisions uses
        # multiple unsigned int & 'out' arguments ... make sure
        # that we can call them / they were translated correctly!
        res = (3,4,5)
        latticeObj = pm.lattice(cmds.polyCube()[0], divisions=res)[1]
        self.assertEqual(latticeObj.getDivisions(), res)

    def test_float2Ref_out_arg(self):
        """
        Test api functions that have an output arg of type float2 &
        MFnMesh.getUvAtPoint's uvPoint arg is one such arg.
        """
        mesh = pm.polyCube()[0].getShape()
        self.assertEqual(mesh.getUVAtPoint([0,0,0], space='world'),
                         [0.49666666984558105, 0.125])

    def test_int2Ref_out_arg(self):
        """
        Test api functions that have an output arg of type int2 &
        MFnMesh.getEdgeVertices's vertexList arg is one such arg.
        """
        mesh = pm.polyCube()[0].getShape()
        self.assertEqual(mesh.getEdgeVertices(2), [4,5])

class testCase_Mesh(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        self.trans = pm.polyCube()[0]
        self.cube = self.trans.getShape()
        self.mesh = pm.createNode('mesh')

    def test_emptyMeshOps(self):
        mesh = self.mesh
        for comp in (mesh.vtx, mesh.faces, mesh.edges):
            self.assertEqual(len(comp), 0)
            self.assertEqual(bool(comp), False)
        self.assertEqual(mesh.numColorSets(), 0)
        self.assertEqual(mesh.numFaceVertices(), 0)
        self.assertEqual(mesh.numNormals(), 0)
        self.assertEqual(mesh.numUVSets(), 0)
        self.assertEqual(mesh.numUVs(), 0)
        self.assertEqual(mesh.numFaces(), 0)
        self.assertEqual(mesh.numVertices(), 0)
        self.assertEqual(mesh.numEdges(), 0)

    def test_setVertexColor(self):
        for i in range(8):
            color = pm.dt.Color(1.0* i/8.0,0.5,0.5,1)
            self.cube.setVertexColor(color, i)
        for i in range(8):
            color = pm.dt.Color(1.0* i/8.0,0.5,0.5,1)
            self.assertEqual(self.trans.vtx[i].getColor(), color)

class MeshComponentTesterMixin(object):
    def setUp(self):
        pm.newFile(f=1)

    def makeCube(self):
        self.cubeTrans = pm.polyCube()[0]
        self.cube = self.cubeTrans.getShape()

    def makeDegenerate(self):
        # for testing an unconnected vert - don't know of a way to have an
        # unconnected edge...
        import maya.OpenMaya as om
        pts = om.MFloatPointArray()
        pts.append(0, 0, 0)
        pts.append(1, 0, 0)
        pts.append(0, 0, 1)
        pts.append(1, 0, 1)
        counts = om.MIntArray(1, 3)
        indices = om.MIntArray()
        indices.append(0)
        indices.append(1)
        indices.append(2)
        self.degenTrans = pm.PyNode(om.MFnMesh().create(4, 1, pts, counts, indices))
        self.degen = self.degenTrans.getShape()

class testCase_MeshVert(unittest.TestCase, MeshComponentTesterMixin):
    def test_setVertexColor(self):
        self.makeCube()
        for i in range(8):
            color = pm.dt.Color(1.0* i/8.0,0.5,0.5,1)
            self.cubeTrans.vtx[i].setColor(color)
        for i in range(8):
            color = pm.dt.Color(1.0* i/8.0,0.5,0.5,1)
            self.assertEqual(self.cube.vtx[i].getColor(), color)

    def test_connections(self):
        self.makeCube()
        self.assertTrue(self.cube.vtx[2].isConnectedTo(self.cube.vtx[3]))
        self.assertFalse(self.cube.vtx[2].isConnectedTo(self.cube.vtx[7]))

        self.assertTrue(self.cube.vtx[5].isConnectedTo(self.cube.e[7]))
        self.assertFalse(self.cube.vtx[5].isConnectedTo(self.cube.e[5]))

        self.assertTrue(self.cube.vtx[6].isConnectedTo(self.cube.f[5]))
        self.assertFalse(self.cube.vtx[6].isConnectedTo(self.cube.f[0]))

    def test_connectedVertices_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.vtx[0].connectedVertices())
        expected = [1, 2, 6]
        self.assertEqual(result, expected)

    def test_connectedVertices_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.vtx[3].connectedVertices())
        expected = []
        self.assertEqual(result, expected)

    def test_connectedEdges_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.vtx[0].connectedEdges())
        expected = [0, 4, 10]
        self.assertEqual(result, expected)

    def test_connectedEdges_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.vtx[3].connectedEdges())
        expected = []
        self.assertEqual(result, expected)

    def test_connectedFaces_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.vtx[0].connectedFaces())
        expected = [0, 3, 5]
        self.assertEqual(result, expected)

    def test_connectedFaces_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.vtx[3].connectedFaces())
        expected = []
        self.assertEqual(result, expected)


class testCase_MeshEdge(unittest.TestCase, MeshComponentTesterMixin):
    def test_connections(self):
        self.makeCube()
        self.assertTrue(self.cube.e[7].isConnectedTo(self.cube.vtx[5]))
        self.assertFalse(self.cube.e[5].isConnectedTo(self.cube.vtx[5]))

        self.assertTrue(self.cube.e[2].isConnectedTo(self.cube.e[8]))
        self.assertFalse(self.cube.e[2].isConnectedTo(self.cube.e[5]))

        self.assertTrue(self.cube.e[1].isConnectedTo(self.cube.f[0]))
        self.assertFalse(self.cube.e[6].isConnectedTo(self.cube.f[2]))

    # no degenerate tests, because don't know how to make an unconnected edge!

    def test_connectedVertices_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.e[0].connectedVertices())
        expected = [0, 1]
        self.assertEqual(result, expected)

    def test_connectedEdges_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.e[0].connectedEdges())
        expected = [4, 5, 10, 11]
        self.assertEqual(result, expected)

    def test_connectedFaces_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.e[0].connectedFaces())
        expected = [0, 3]
        self.assertEqual(result, expected)


class testCase_MeshFace(unittest.TestCase, MeshComponentTesterMixin):
    def test_connections(self):
        self.makeCube()
        # Oddly enough, in a cube, all the verts 'connected' to the face
        # are the ones NOT contained in it, and all the ones that are
        # contained are considered not connected...
        self.assertTrue(self.cube.f[5].isConnectedTo(self.cube.vtx[7]))
        self.assertTrue(self.cube.f[0].isConnectedTo(self.cube.vtx[3]))

        self.assertTrue(self.cube.f[3].isConnectedTo(self.cube.e[5]))
        self.assertFalse(self.cube.f[4].isConnectedTo(self.cube.e[4]))

        self.assertTrue(self.cube.f[2].isConnectedTo(self.cube.f[1]))
        self.assertFalse(self.cube.f[5].isConnectedTo(self.cube.f[4]))

    def test_connectedVertices_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.f[0].connectedVertices())
        expected = [4, 5, 6, 7]
        self.assertEqual(result, expected)

    def test_connectedVertices_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.f[0].connectedVertices())
        expected = []
        self.assertEqual(result, expected)

    def test_connectedEdges_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.f[0].connectedEdges())
        expected = [6, 7, 10, 11]
        self.assertEqual(result, expected)

    def test_connectedEdges_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.f[0].connectedEdges())
        expected = []
        self.assertEqual(result, expected)

    def test_connectedFaces_norm(self):
        self.makeCube()
        result = sorted(x.index() for x in self.cube.f[0].connectedFaces())
        expected = [1, 3, 4, 5]
        self.assertEqual(result, expected)

    def test_connectedFaces_degenerate(self):
        self.makeDegenerate()
        result = sorted(x.index() for x in self.degen.f[0].connectedFaces())
        expected = []
        self.assertEqual(result, expected)


class testCase_Locator(unittest.TestCase):
    def setUp(self):
        cmds.file(f=1, new=1)

    def test_createFromClass(self):
        self.assertFalse(cmds.ls(type='locator'))
        locNode = pm.nt.Locator()
        self.assertIsInstance(locNode, pm.nt.Locator)
        self.assertEqual(cmds.ls(type='locator'), [locNode.name()])


class testCase_ConstraintAngleOffsetQuery(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)

    def runTest(self):
        for cmdName in ('aimConstraint', 'orientConstraint'):
            cube1 = pm.polyCube()[0]
            cube2 = pm.polyCube()[0]
            cube2.translate.set( (2,0,0) )
            cmd = getattr(pm, cmdName)
            constraint = cmd(cube1, cube2)

            setVals = (12, 8, 7)
            cmd(constraint, e=1, offset=setVals)
            getVals = tuple(cmd(constraint, q=1, offset=1))
            self.assertVectorsEqual(setVals, getVals)

class testCase_Container(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)

    def testPublishedAttribute(self):
        c=pm.container( current=1 )
        g=pm.group( em=True )
        pm.container( c, e=True, publishAsParent=(g, 'yippee') )
        fromPyNode = pm.PyNode('container1.yippee')
        self.assertTrue( isinstance(fromPyNode, pm.Attribute))
        self.assertEqual( fromPyNode.name(), 'container1.canBeParent[0]' )
        fromAttr = c.attr('yippee')
        self.assertTrue( isinstance(fromAttr, pm.Attribute))
        self.assertEqual( fromAttr.name(), 'container1.canBeParent[0]' )
        self.assertEqual( fromPyNode, fromAttr )

    def testGetParentContainer(self):
        c1 = pm.container()
        self.assertEqual(c1.getParentContainer(), None)
        c2 = pm.container(addNode=c1)
        self.assertEqual(c2.getParentContainer(), None)
        self.assertEqual(c1.getParentContainer(), c2)

    def testGetRootTransform(self):
        t = pm.createNode('transform')
        c = pm.container(addNode=t)
        self.assertEqual(c.getRootTransform(), None)
        self.assertEqual(c.getPublishAsRoot(), None)
        c.setPublishAsRoot((t, True))
        self.assertEqual(c.getRootTransform(), t)
        self.assertEqual(c.getPublishAsRoot(), t)


class testCase_AnimCurve(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)

    def testAddKeys(self):
        import maya.OpenMayaAnim as omAn
        import maya.OpenMaya as om

        # Test thanks to Mark Therrell, from issue 234

        pm.sphere()

        nodeAttr = 'nurbsSphere1.tx'
        times = [1, 2, 4, 7]
        values = [-1.444, 2.461, 7.544, 11.655]

        ## get the the MPlug of the node.attr using pymel (could use api, this way just to see it work)
        mplug = pm.PyNode(nodeAttr).__apimplug__()

        ## instantiate the MFnAnimaCurve function, get the curve type needed
        crvFnc = omAn.MFnAnimCurve()
        crvtype = crvFnc.timedAnimCurveTypeForPlug(mplug)

        ## make a curve on the attr using API
        ## how do i create the curve with pymel?? no docs on this??
        crv = crvFnc.create(mplug,crvtype)

        ## try to add keyframes to the curve using .addKeys function in Pymel
        name = om.MFnDependencyNode(crv).name()
        pyAnimCurve = pm.PyNode(name)
        pyAnimCurve.addKeys(times,values,'step','step',False)

        for time, val in zip(times, values):
            pm.currentTime(time)
            self.assertEqual(pm.getAttr(nodeAttr), val)

    def assertAddKey(self, curveType):
        if curveType.startswith('animCurve'):
            inType = curveType[-2]
            outType = curveType[-1]
        elif curveType.startswith('resultCurveTimeTo'):
            inType = 'T'
            if curveType.endswith('Angular'):
                outType = 'A'
            elif curveType.endswith('Linear'):
                outType = 'L'
            elif curveType.endswith('Time'):
                outType = 'T'
            elif curveType.endswith('Unitless'):
                outType = 'T'
            else:
                raise ValueError('unknown result curve type')
        else:
            raise ValueError('unknown curve type')
        curve = pm.createNode(curveType)
        self.assertEqual(curve.numKeys(), 0)
        if inType == 'T':
            inputs = (-1, 1, pm.dt.Time(3), pm.dt.Time(100))
        else:
            inputs = (-1, 1, 3, 100)
        if outType == 'T':
            outputs = (pm.dt.Time(-5), .25, pm.dt.Time(20), 45)
        else:
            outputs = (-5, .25, 20, 45)

        inTangents = []
        outTangents = []
        origGlobalIn = cmds.keyTangent(q=1, g=1, inTangentType=1)[0]
        origGlobalOut = cmds.keyTangent(q=1, g=1, outTangentType=1)[0]

        pm.flushUndo()

        try:
            # Add key 0
            cmds.keyTangent(g=1, inTangentType='auto')
            cmds.keyTangent(g=1, outTangentType='plateau')

            curve.addKey(inputs[0], outputs[0], 'flat',
                         pm.nt.AnimCurve.TangentType.clamped)
            inTangents.append('flat')
            outTangents.append(pm.nt.AnimCurve.TangentType.clamped)

            # Add key 1
            curve.addKey(inputs[1], outputs[1])
            inTangents.append(pm.nt.AnimCurve.TangentType.auto.index)
            outTangents.append('plateau')

            # Add key 2
            cmds.keyTangent(g=1, inTangentType='linear')
            cmds.keyTangent(g=1, outTangentType='step')
            curve.addKey(inputs[2], outputs[2],
                         tangentOutType=pm.nt.AnimCurve.TangentType.smooth)
            inTangents.append(pm.nt.AnimCurve.TangentType.linear)
            outTangents.append('smooth')

            # Add key 3
            cmds.keyTangent(g=1, inTangentType='slow')
            cmds.keyTangent(g=1, outTangentType='fast')
            curve.addKey(inputs[3], outputs[3],
                         tangentInType=pm.nt.AnimCurve.TangentType.clamped.index)
            inTangents.append(pm.nt.AnimCurve.TangentType.clamped)
            outTangents.append(pm.nt.AnimCurve.TangentType.fast.index)

            def assertKeys(numKeys):
                self.assertEqual(curve.numKeys(), numKeys)
                for i, (inVal, outVal, inTan, outTan) in enumerate(zip(
                        inputs, outputs, inTangents, outTangents)):
                    if i >= numKeys:
                        break

                    if inType =='T':
                        keyInput = curve.getTime(i)
                    else:
                        keyInput = curve.getUnitlessInput(i)
                    self.assertEqual(keyInput, inVal)

                    if outType != 'T':
                        self.assertEqual(curve.getValue(i), outVal)
                    self.assertEqual(curve.evaluate(keyInput), outVal)
                    self.assertEqual(curve.getInTangentType(i), inTan)
                    self.assertEqual(curve.getOutTangentType(i), outTan)

            assertKeys(4)

            # test undo/redo
            cmds.undo() # undo 4th addKey
            assertKeys(3)
            cmds.undo() # undo outTangentType='fast'
            cmds.undo() # undo inTangentType='slow'
            cmds.undo() # undo 3rd addKey
            assertKeys(2)
            cmds.undo() # undo outTangentType='step'
            cmds.undo() # undo inTangentType='linear'
            cmds.undo() # undo 2nd addKey
            assertKeys(1)
            cmds.undo() # undo 1st addKey
            assertKeys(0)
            cmds.redo() # redo 1st addKey
            assertKeys(1)
            cmds.redo() # redo 2nd addKey
            cmds.redo() # redo inTangentType='linear'
            cmds.redo() # redo outTangentType='step'
            assertKeys(2)
            cmds.redo() # redo 3rd addKey
            cmds.redo() # redo inTangentType='slow'
            cmds.redo() # redo outTangentType='fast'
            assertKeys(3)
            cmds.redo()  # redo 4th addKey
            assertKeys(4)
        finally:
            cmds.keyTangent(g=1, inTangentType=origGlobalIn)
            cmds.keyTangent(g=1, outTangentType=origGlobalOut)

        # test findClosest... I'm lazy, I didn't want to make a separate test
        # for findClosest...

        # first, make sure we find the right value if we're exactly on it...
        for i, inVal in enumerate(inputs):
            self.assertEqual(curve.findClosest(inVal), i)
        # Now try some more intermediate values...
        # inputs = (-1, 1, 3, 100)
        self.assertEqual(curve.findClosest(-1e10), 0)
        self.assertEqual(curve.findClosest(-1.1), 0)
        self.assertEqual(curve.findClosest(-.01), 0)
        self.assertEqual(curve.findClosest(.00002), 1)
        self.assertEqual(curve.findClosest(.09), 1)
        self.assertEqual(curve.findClosest(1.5), 1)
        self.assertEqual(curve.findClosest(2.5), 2)
        self.assertEqual(curve.findClosest(50), 2)
        self.assertEqual(curve.findClosest(51.6), 3)
        self.assertEqual(curve.findClosest(99.0), 3)
        self.assertEqual(curve.findClosest(3.8743e10), 3)

    def test_addKeyTA(self):
        self.assertAddKey("animCurveTA")

    def test_addKeyTL(self):
        self.assertAddKey("animCurveTL")

    def test_addKeyTT(self):
        self.assertAddKey("animCurveTT")

    def test_addKeyTU(self):
        self.assertAddKey("animCurveTU")

    def test_addKeyUA(self):
        self.assertAddKey("animCurveUA")

    def test_addKeyUL(self):
        self.assertAddKey("animCurveUL")

    def test_addKeyUT(self):
        self.assertAddKey("animCurveUT")

    def test_addKeyUU(self):
        self.assertAddKey("animCurveUU")

    def test_addKeyResultTA(self):
        self.assertAddKey("resultCurveTimeToAngular")

    def test_addKeyResultTL(self):
        self.assertAddKey("resultCurveTimeToLinear")

    def test_addKeyResultTT(self):
        self.assertAddKey("resultCurveTimeToTime")

    def test_addKeyResultTU(self):
        self.assertAddKey("resultCurveTimeToUnitless")

    def test_timedAnimCurveTypeForPlug(self):
        time = pm.PyNode('time1')
        persp = pm.PyNode('persp')
        self.assertEqual(pm.nt.AnimCurve.timedAnimCurveTypeForPlug(persp.tx),
                         pm.nt.AnimCurve.AnimCurveType.TL)
        self.assertEqual(pm.nt.AnimCurve.timedAnimCurveTypeForPlug(persp.rx),
                         pm.nt.AnimCurve.AnimCurveType.TA)
        self.assertEqual(pm.nt.AnimCurve.timedAnimCurveTypeForPlug(time.outTime),
                         pm.nt.AnimCurve.AnimCurveType.TT)
        self.assertEqual(pm.nt.AnimCurve.timedAnimCurveTypeForPlug(persp.displayLocalAxis),
                         pm.nt.AnimCurve.AnimCurveType.TU)

    def test_unitlessAnimCurveTypeForPlug(self):
        time = pm.PyNode('time1')
        persp = pm.PyNode('persp')
        self.assertEqual(pm.nt.AnimCurve.unitlessAnimCurveTypeForPlug(persp.tx),
                         pm.nt.AnimCurve.AnimCurveType.UL)
        self.assertEqual(pm.nt.AnimCurve.unitlessAnimCurveTypeForPlug(persp.rx),
                         pm.nt.AnimCurve.AnimCurveType.UA)
        self.assertEqual(pm.nt.AnimCurve.unitlessAnimCurveTypeForPlug(time.outTime),
                         pm.nt.AnimCurve.AnimCurveType.UT)
        self.assertEqual(pm.nt.AnimCurve.unitlessAnimCurveTypeForPlug(persp.displayLocalAxis),
                         pm.nt.AnimCurve.AnimCurveType.UU)

    def test_undo(self):
        curve = pm.nt.AnimCurveTL()

        def assertKeys(expectedTimes, expectedVals):
            numKeys = len(expectedTimes)
            self.assertEqual(numKeys, len(expectedVals))
            self.assertEqual(numKeys, curve.numKeys())
            times = []
            vals = []
            for i in xrange(numKeys):
                times.append(curve.getTime(i))
                vals.append(curve.getValue(i))
            self.assertEqual(times, expectedTimes)
            self.assertEqual(vals, expectedVals)

        assertKeys([], [])

        origTimes = [0, 10, 20, 30, 40]
        origVals = [0, 1, 2, 3, 4]
        curve.addKeys(origTimes, origVals)
        assertKeys(origTimes, origVals)

        pm.undo()
        assertKeys([], [])
        pm.redo()
        assertKeys(origTimes, origVals)

        curve.remove(2)
        newTimes1 = [0, 10, 30, 40]
        newVals1 = [0, 1, 3, 4]
        assertKeys(newTimes1, newVals1)

        curve.setTime(1, 8)
        newTimes2 = [0, 8, 30, 40]
        newVals2 = [0, 1, 3, 4]
        assertKeys(newTimes2, newVals2)

        curve.setValue(0, 82)
        newTimes3 = [0, 8, 30, 40]
        newVals3 = [82, 1, 3, 4]
        assertKeys(newTimes3, newVals3)

        pm.undo()
        assertKeys(newTimes2, newVals2)
        pm.undo()
        assertKeys(newTimes1, newVals1)
        pm.undo()
        assertKeys(origTimes, origVals)

        # we don't undo the addKeys, because there's a maya bug that makes
        # the other MAnimCurveChanges (or at least the setTime one?) not work
        # See here for reproduction details:
        #    https://gist.github.com/elrond79/9ca6750b1c7f5b748d7f19cf62405b2e
        #pm.undo()
        #assertKeys([], [])
        #pm.redo()
        #assertKeys(origTimes, origVals)

        pm.redo()
        assertKeys(newTimes1, newVals1)
        pm.redo()
        assertKeys(newTimes2, newVals2)
        pm.redo()
        assertKeys(newTimes3, newVals3)

        pm.undo()
        assertKeys(newTimes2, newVals2)
        pm.redo()
        assertKeys(newTimes3, newVals3)
        pm.undo()
        assertKeys(newTimes2, newVals2)
        pm.redo()
        assertKeys(newTimes3, newVals3)


class testCase_rename(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)

    def testBasicRename(self):
        sphere = pm.polySphere()[0]
        sphere.rename('firstName')
        self.assertEqual('firstName', sphere.nodeName())
        sphere.rename('newName')
        self.assertEqual('newName', sphere.nodeName())

    def testPreserveNamespace(self):
        sphere1 = pm.polySphere()[0]
        sphere2 = pm.polySphere()[0]
        pm.namespace(add="myNS")


        pm.namespace(set=":")
        # set to sphere1, myNS:sphere2
        sphere1.rename(':sphere1')
        sphere2.rename(':myNS:sphere2')
        self.assertEqual('sphere1', sphere1.nodeName())
        self.assertEqual('myNS:sphere2', sphere2.nodeName())
        # test w/o preserveNamespace, current NS == :
        sphere1.rename('sphere3', preserveNamespace=False)
        sphere2.rename('sphere4', preserveNamespace=False)
        self.assertEqual('sphere3', sphere1.nodeName())
        self.assertEqual('sphere4', sphere2.nodeName())

        pm.namespace(set=":myNS")
        # set to sphere1, myNS:sphere2
        sphere1.rename(':sphere1')
        sphere2.rename(':myNS:sphere2')
        self.assertEqual('sphere1', sphere1.nodeName())
        self.assertEqual('myNS:sphere2', sphere2.nodeName())
        # test w/o preserveNamespace, current NS == :myNS
        sphere1.rename('sphere3', preserveNamespace=False)
        sphere2.rename('sphere4', preserveNamespace=False)
        self.assertEqual('myNS:sphere3', sphere1.nodeName())
        self.assertEqual('myNS:sphere4', sphere2.nodeName())

        pm.namespace(set=":")
        # set to sphere1, myNS:sphere2
        sphere1.rename(':sphere1')
        sphere2.rename(':myNS:sphere2')
        self.assertEqual('sphere1', sphere1.nodeName())
        self.assertEqual('myNS:sphere2', sphere2.nodeName())
        # test w/ preserveNamespace, current NS == :
        sphere1.rename('sphere3', preserveNamespace=True)
        sphere2.rename('sphere4', preserveNamespace=True)
        self.assertEqual('sphere3', sphere1.nodeName())
        self.assertEqual('myNS:sphere4', sphere2.nodeName())

        pm.namespace(set=":myNS")
        # set to sphere1, myNS:sphere2
        sphere1.rename(':sphere1')
        sphere2.rename(':myNS:sphere2')
        self.assertEqual('sphere1', sphere1.nodeName())
        self.assertEqual('myNS:sphere2', sphere2.nodeName())
        # test w/ preserveNamespace, current NS == :myNS
        sphere1.rename('sphere3', preserveNamespace=True)
        sphere2.rename('sphere4', preserveNamespace=True)
        self.assertEqual('sphere3', sphere1.nodeName())
        self.assertEqual('myNS:sphere4', sphere2.nodeName())

class testCase_RenderLayer(TestCaseExtended):
    def setUp(self):
        pm.newFile(f=1)
        self.cube = pm.polyCube()[0]
        self.sphere = pm.polySphere()[0]
        pm.select(None)
        self.layer = pm.createRenderLayer(name="diffuse")

    def test_add_single(self):
        self.assertEqual(self.layer.listMembers(), [])
        self.layer.addMembers(self.cube)
        self.assertEqual(self.layer.listMembers(), [self.cube])
        self.layer.addMembers(self.sphere)
        self.assertEqual(set(self.layer.listMembers()),
                         set([self.cube, self.sphere]))

    def test_add_multi(self):
        self.assertEqual(self.layer.listMembers(), [])
        self.layer.addMembers([self.cube, self.sphere])
        self.assertEqual(set(self.layer.listMembers()),
                         set([self.cube, self.sphere]))

    def test_remove_single(self):
        self.layer.addMembers([self.cube, self.sphere])
        self.assertEqual(set(self.layer.listMembers()),
                         set([self.cube, self.sphere]))
        self.layer.removeMembers(self.sphere)
        self.assertEqual(self.layer.listMembers(), [self.cube])
        self.layer.removeMembers(self.cube)
        self.assertEqual(self.layer.listMembers(), [])

    def test_remove_multi(self):
        self.layer.addMembers([self.cube, self.sphere])
        self.assertEqual(set(self.layer.listMembers()),
                         set([self.cube, self.sphere]))
        self.layer.removeMembers([self.sphere, self.cube])
        self.assertEqual(self.layer.listMembers(), [])

    # can't use unittest.skipIf, because nose doesn't seem to recognize it...
    if versions.current() < versions.v2018:
        def test_setCurrent(self):
            self.assertEqual(pm.nt.RenderLayer.defaultRenderLayer(),
                             pm.nt.RenderLayer.currentLayer())
            self.layer.setCurrent()
            self.assertEqual(self.layer, pm.nt.RenderLayer.currentLayer())

        def test_adjustments(self):
            widthAttr = pm.PyNode("defaultResolution.width")
            self.assertEqual(self.layer.listAdjustments(), [])
            self.layer.addAdjustments(widthAttr)
            self.assertEqual(self.layer.listAdjustments(), ["defaultResolution.width"])

            origVal = widthAttr.get()
            adjVal = origVal + 5

            self.layer.setCurrent()
            widthAttr.set(adjVal)
            self.assertEqual(widthAttr.get(), adjVal)
            pm.nt.RenderLayer.defaultRenderLayer().setCurrent()
            self.assertEqual(widthAttr.get(), origVal)
            self.layer.setCurrent()
            self.assertEqual(widthAttr.get(), adjVal)

            self.layer.removeAdjustments(widthAttr)
            self.assertEqual(self.layer.listAdjustments(), [])
            self.assertEqual(widthAttr.get(), origVal)
            pm.nt.RenderLayer.defaultRenderLayer().setCurrent()
            self.assertEqual(widthAttr.get(), origVal)

    def test_create_addedToManager(self):
        layer = pm.nt.RenderLayer(name='myLayer')
        otherLayer = pm.createNode('renderLayer', name='otherLayer')
        managedLayers = pm.Attribute('renderLayerManager.renderLayerId').outputs()
        self.assertIn(layer, managedLayers)
        self.assertNotIn(otherLayer, managedLayers)

    def test_create_selected(self):
        A = pm.createNode('transform', name='A')
        self.assertEqual(pm.ls(selection=1), [A])
        layerEmpty1 = pm.nt.RenderLayer()
        self.assertFalse(layerEmpty1.listMembers())

        pm.select(A)
        layerSel = pm.nt.RenderLayer(empty=False)
        self.assertEqual(layerSel.listMembers(), [A])

        pm.select(A)
        layerEmpty2 = pm.nt.RenderLayer(empty=True)
        self.assertFalse(layerEmpty2.listMembers())


class testCase_DisplayLayer(unittest.TestCase):
    def setUp(self):
        cmds.file(f=1, new=1)

    def test_create_addedToManager(self):
        layer = pm.nt.DisplayLayer(name='myLayer')
        otherLayer = pm.createNode('displayLayer', name='otherLayer')
        managedLayers = pm.Attribute('layerManager.displayLayerId').outputs()
        self.assertIn(layer, managedLayers)
        self.assertNotIn(otherLayer, managedLayers)

    def test_create_selected(self):
        A = pm.createNode('transform', name='A')
        self.assertEqual(pm.ls(selection=1), [A])
        layerEmpty1 = pm.nt.DisplayLayer()
        self.assertFalse(layerEmpty1.listMembers())

        pm.select(A)
        layerSel = pm.nt.DisplayLayer(empty=False)
        self.assertEqual(layerSel.listMembers(), [A])

        pm.select(A)
        layerEmpty2 = pm.nt.DisplayLayer(empty=True)
        self.assertFalse(layerEmpty2.listMembers())

    def test_addRemove(self):
        A = pm.createNode('transform', name='A')
        B = pm.createNode('transform', name='B')
        C = pm.createNode('transform', name='C')
        D = pm.createNode('transform', name='D')
        E = pm.createNode('transform', name='E')

        layer = pm.nt.DisplayLayer(name='myLayer')
        self.assertFalse(layer.listMembers())
        layer.addMembers(A)
        self.assertEqual(set(layer.listMembers()), {A})
        layer.addMembers([B, C, D])
        self.assertEqual(set(layer.listMembers()), {A, B, C, D})
        layer.removeMembers(C)
        self.assertEqual(set(layer.listMembers()), {A, B, D})
        layer.removeMembers([A, D])
        self.assertEqual(set(layer.listMembers()), {B})


class testCase_Character(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)
        # First, create a character to hold the clips. The character will be
        # a 3-bone skeleton named "arm".
        #
        cmds.select(d=True)
        cmds.joint(p=(0, 0, 0))
        cmds.joint(p=(0, 4, 0))
        cmds.joint('joint1', e=True, zso=True, oj='xyz')
        cmds.joint(p=(0, 8, -1))
        cmds.joint('joint2', e=True, zso=True, oj='xyz')
        cmds.joint(p=(0, 9, -2))
        cmds.joint('joint3', e=True, zso=True, oj='xyz')
        cmds.select('joint1', 'joint2', 'joint3', r=True)
        self.char = pm.character(name='arm')

    def test_getClipScheduler(self):
        self.assertEqual(self.char.getClipScheduler(), None)

        # Create some animation for the character. For this example the animation will
        # be quite trivial.
        #
        cmds.select('joint3', r=True)
        cmds.currentTime(0)
        cmds.setKeyframe('joint3.rx')
        cmds.currentTime(10)
        cmds.setKeyframe('joint3.rx', v=90)
        cmds.currentTime(20)
        cmds.setKeyframe('joint3.rx', v=0)
        # Create a clip for the current animation named "handWave"
        #
        cmds.clip('arm', startTime=0, endTime=20, name='handWave')

        self.assertEqual(self.char.getClipScheduler(), 'armScheduler1')

class testCase_listAttr(unittest.TestCase):
    # FIXME: to prevent this test from changing over time it might be a good idea to create
    # custom MPxNode type with known attributes
    # See also: test_general.test_Attribute_iterDescendants
    def setUp(self):
        pm.newFile(f=1)
        self.cube1 = pm.polyCube(ch=0)[0]
        self.cube2 = pm.polyCube(ch=0)[0]
        self.cube3 = pm.polyCube(ch=0)[0]
        self.blend = pm.blendShape(self.cube2, self.cube3, self.cube1)[0]

    def test_standard(self):
        results = set(x.name() for x in self.blend.listAttr())
        expected = {
            u'blendShape1.attributeAliasList',
            u'blendShape1.baseOrigin',
            u'blendShape1.baseOriginX',
            u'blendShape1.baseOriginY',
            u'blendShape1.baseOriginZ',
            u'blendShape1.binMembership',
            u'blendShape1.caching',
            u'blendShape1.envelope',
            u'blendShape1.fchild1',
            u'blendShape1.fchild2',
            u'blendShape1.fchild3',
            u'blendShape1.frozen',
            u'blendShape1.function',
            u'blendShape1.icon',
            u'blendShape1.input',
            u'blendShape1.inputTarget',
            u'blendShape1.inputTarget[-1].baseWeights',
            u'blendShape1.inputTarget[-1].controlPoints',
            u'blendShape1.inputTarget[-1].controlPoints[-1].xValue',
            u'blendShape1.inputTarget[-1].controlPoints[-1].yValue',
            u'blendShape1.inputTarget[-1].controlPoints[-1].zValue',
            u'blendShape1.inputTarget[-1].inputTargetGroup',
            u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem',
            u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget',
            u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputPointsTarget',
            u'blendShape1.inputTarget[-1].inputTargetGroup[-1].normalizationId',
            u'blendShape1.inputTarget[-1].inputTargetGroup[-1].targetWeights',
            u'blendShape1.inputTarget[-1].normalizationGroup',
            u'blendShape1.inputTarget[-1].normalizationGroup[-1].normalizationUseWeights',
            u'blendShape1.inputTarget[-1].normalizationGroup[-1].normalizationWeights',
            u'blendShape1.inputTarget[-1].paintTargetIndex',
            u'blendShape1.inputTarget[-1].paintTargetWeights',
            u'blendShape1.inputTarget[-1].sculptTargetIndex',
            u'blendShape1.inputTarget[-1].sculptTargetTweaks',
            u'blendShape1.inputTarget[-1].vertex',
            u'blendShape1.inputTarget[-1].vertex[-1].xVertex',
            u'blendShape1.inputTarget[-1].vertex[-1].yVertex',
            u'blendShape1.inputTarget[-1].vertex[-1].zVertex',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[0].inputGeomTarget',
            u'blendShape1.input[0].groupId',
            u'blendShape1.input[0].inputGeometry',
            u'blendShape1.isHistoricallyInteresting',
            u'blendShape1.map64BitIndices',
            u'blendShape1.message',
            u'blendShape1.nodeState',
            u'blendShape1.origin',
            u'blendShape1.outputGeometry',
            u'blendShape1.paintWeights',
            u'blendShape1.parallelBlender',
            u'blendShape1.supportNegativeWeights',
            u'blendShape1.targetOrigin',
            u'blendShape1.targetOriginX',
            u'blendShape1.targetOriginY',
            u'blendShape1.targetOriginZ',
            u'blendShape1.topologyCheck',
            u'blendShape1.useTargetCompWeights',
            u'blendShape1.weight',
        }
        self.assertTrue(results.issuperset(expected))
        self.assertIn(u'blendShape1.attributeAliasList', results)
        self.assertIn(u'blendShape1.inputTarget[-1].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].baseWeights', results)
        self.assertIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget', results)

    def test_topLevel(self):
        results = set(x.name() for x in self.blend.listAttr(topLevel=True))
        expected = {
            u'blendShape1.attributeAliasList',
            u'blendShape1.baseOrigin',
            u'blendShape1.binMembership',
            u'blendShape1.caching',
            u'blendShape1.envelope',
            u'blendShape1.frozen',
            u'blendShape1.function',
            u'blendShape1.icon',
            u'blendShape1.input',
            u'blendShape1.inputTarget',
            u'blendShape1.isHistoricallyInteresting',
            u'blendShape1.map64BitIndices',
            u'blendShape1.message',
            u'blendShape1.nodeState',
            u'blendShape1.origin',
            u'blendShape1.outputGeometry',
            u'blendShape1.paintWeights',
            u'blendShape1.parallelBlender',
            u'blendShape1.supportNegativeWeights',
            u'blendShape1.targetOrigin',
            u'blendShape1.topologyCheck',
            u'blendShape1.useTargetCompWeights',
            u'blendShape1.weight',
        }
        self.assertTrue(results.issuperset(expected))
        self.assertIn(u'blendShape1.attributeAliasList', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget', results)
        self.assertNotIn(u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget', results)

    def test_descendants(self):
        results = set(x.name() for x in self.blend.listAttr(descendants=True))
        expected = {
            u'blendShape1.attributeAliasList',
            u'blendShape1.baseOrigin',
            u'blendShape1.baseOriginX',
            u'blendShape1.baseOriginY',
            u'blendShape1.baseOriginZ',
            u'blendShape1.binMembership',
            u'blendShape1.caching',
            u'blendShape1.envelope',
            u'blendShape1.fchild1',
            u'blendShape1.fchild2',
            u'blendShape1.fchild3',
            u'blendShape1.frozen',
            u'blendShape1.function',
            u'blendShape1.icon',
            u'blendShape1.input',
            u'blendShape1.inputTarget',
            u'blendShape1.inputTarget[0]',
            u'blendShape1.inputTarget[0].baseWeights',
            u'blendShape1.inputTarget[0].controlPoints',
            u'blendShape1.inputTarget[0].inputTargetGroup',
            u'blendShape1.inputTarget[0].inputTargetGroup[0]',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000]',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputGeomTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputPointsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].normalizationId',
            u'blendShape1.inputTarget[0].inputTargetGroup[0].targetWeights',
            u'blendShape1.inputTarget[0].inputTargetGroup[1]',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000]',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputComponentsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputGeomTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].inputTargetItem[6000].inputPointsTarget',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].normalizationId',
            u'blendShape1.inputTarget[0].inputTargetGroup[1].targetWeights',
            u'blendShape1.inputTarget[0].normalizationGroup',
            u'blendShape1.inputTarget[0].paintTargetIndex',
            u'blendShape1.inputTarget[0].paintTargetWeights',
            u'blendShape1.inputTarget[0].sculptTargetIndex',
            u'blendShape1.inputTarget[0].sculptTargetTweaks',
            u'blendShape1.inputTarget[0].vertex',
            u'blendShape1.input[0]',
            u'blendShape1.input[0].groupId',
            u'blendShape1.input[0].inputGeometry',
            u'blendShape1.isHistoricallyInteresting',
            u'blendShape1.map64BitIndices',
            u'blendShape1.message',
            u'blendShape1.nodeState',
            u'blendShape1.origin',
            u'blendShape1.outputGeometry',
            u'blendShape1.outputGeometry[0]',
            u'blendShape1.paintWeights',
            u'blendShape1.parallelBlender',
            u'blendShape1.supportNegativeWeights',
            u'blendShape1.targetOrigin',
            u'blendShape1.targetOriginX',
            u'blendShape1.targetOriginY',
            u'blendShape1.targetOriginZ',
            u'blendShape1.topologyCheck',
            u'blendShape1.useTargetCompWeights',
            u'blendShape1.weight',
            u'blendShape1.weight[0]',
            u'blendShape1.weight[1]',
        }
        self.assertTrue(results.issuperset(expected))
        self.assertIn(u'blendShape1.attributeAliasList', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].baseWeights', results)
        self.assertIn(u'blendShape1.inputTarget[0].baseWeights', results)
        self.assertNotIn(u'blendShape1.inputTarget[-1].inputTargetGroup[-1].inputTargetItem[-1].inputComponentsTarget', results)
        self.assertIn(u'blendShape1.inputTarget[0].inputTargetGroup[0].inputTargetItem[6000].inputComponentsTarget', results)


# current behavior is that using invalid nodes only raises a warning - may want
# to make this an error at some point, but for now, need to preserve this
# behavior

class testCase_invalidNode(unittest.TestCase):
    def setUp(self):
        pm.newFile(f=1)

    def test_invalidNodeName(self):
        import warnings
        oldNode = pm.group(name='foo')
        self.assertEqual(oldNode.name(), 'foo')
        pm.delete(oldNode)
        # this will raise a Future warning - disable that for now, in case
        # we have --warnings-as-errors set
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            self.assertEqual(oldNode.name(), 'foo')


#def test_units():
#    startLinear = currentUnit( q=1, linear=1)
#
#    #cam = pm.PyNode('persp')
#    # change units from default
#    currentUnit(linear='meter')
#
#    light = directionalLight()
#
#    testPairs = [ ('persp.translate', 'getTranslation', 'setTranslation', datatypes.Vector([3.0,2.0,1.0]) ),  # Distance datatypes.Vector
#                  ('persp.shutterAngle' , 'getShutterAngle', 'setShutterAngle', 144.0 ),  # Angle
#                  ('persp.verticalShake' , 'getVerticalShake', 'setVerticalShake', 1.0 ),  # Unitless
#                  ('persp.focusDistance', 'getFocusDistance', 'setFocusDistance', 5.0 ),  # Distance
#                  ('%s.penumbraAngle' % light, 'getPenumbra', 'setPenumbra', 5.0 ),  # Angle with renamed api method ( getPenumbraAngle --> getPenumbra )
#
#                 ]
#
#    for attrName, getMethodName, setMethodName, realValue in testPairs:
#        at = pm.PyNode(attrName)
#        node = at.node()
#        getter = getattr( node, getMethodName )
#        setter = getattr( node, setMethodName )
#
#
#        descr =  '%s / %s / %s' % ( attrName, getMethodName, setMethodName )
#
#        def checkUnits( *args ):
#            print repr(at)
#            print "Real Value:", repr(realValue)
#            # set attribute using "safe" method
#            at.set( realValue )
#            # get attribute using wrapped api method
#            gotValue = getter()
#            print "Got Value:", repr(gotValue)
#            # compare
#            self.assertEqual( realValue, gotValue )
#
#            # set using wrapped api method
#            setter( realValue )
#            # get attribute using "safe" method
#            gotValue = at.get()
#            # compare
#            self.assertEqual( realValue, gotValue )
#        checkUnits.description = descr
#        yield checkUnits
#
#    # reset units
#    currentUnit(linear=startLinear)
#    pm.delete( light )
#                    #print types

class testCase_classification(unittest.TestCase):
    def setUp(self):
        self.tr, _ = pm.polySphere()

    def testClassification(self):
        self.assertIn('drawdb/geometry/transform', self.tr.classification())

    def testSatisfies(self):
        self.assertFalse(self.tr.classification(satisfies='blah'))
        self.assertTrue(self.tr.classification(satisfies='drawdb/geometry'))

    def tearDown(self):
        pm.delete(self.tr)

class testCase_parentTests(unittest.TestCase):
    def setUp(self):
        self.cam = pm.createNode('camera')
        self.camTrans = self.cam.getParent()
        self.ipTrans, self.ip = pm.imagePlane(camera=self.cam)

    def tearDown(self):
        pm.delete(self.camTrans)

    def test_hasParent(self):
        self.assertFalse(self.camTrans.hasParent(self.camTrans))
        self.assertFalse(self.camTrans.hasParent(self.cam))
        self.assertFalse(self.camTrans.hasParent(self.ipTrans))
        self.assertFalse(self.camTrans.hasParent(self.ip))

        self.assertTrue(self.cam.hasParent(self.camTrans))
        self.assertFalse(self.cam.hasParent(self.cam))
        self.assertFalse(self.cam.hasParent(self.ipTrans))
        self.assertFalse(self.cam.hasParent(self.ip))

        self.assertFalse(self.ipTrans.hasParent(self.camTrans))
        self.assertTrue(self.ipTrans.hasParent(self.cam))
        self.assertFalse(self.ipTrans.hasParent(self.ipTrans))
        self.assertFalse(self.ipTrans.hasParent(self.ip))

        self.assertFalse(self.ip.hasParent(self.camTrans))
        self.assertFalse(self.ip.hasParent(self.cam))
        self.assertTrue(self.ip.hasParent(self.ipTrans))
        self.assertFalse(self.ip.hasParent(self.ip))

    def test_hasChild(self):
        self.assertFalse(self.camTrans.hasChild(self.camTrans))
        self.assertTrue(self.camTrans.hasChild(self.cam))
        self.assertFalse(self.camTrans.hasChild(self.ipTrans))
        self.assertFalse(self.camTrans.hasChild(self.ip))

        self.assertFalse(self.cam.hasChild(self.camTrans))
        self.assertFalse(self.cam.hasChild(self.cam))
        self.assertTrue(self.cam.hasChild(self.ipTrans))
        self.assertFalse(self.cam.hasChild(self.ip))

        self.assertFalse(self.ipTrans.hasChild(self.camTrans))
        self.assertFalse(self.ipTrans.hasChild(self.cam))
        self.assertFalse(self.ipTrans.hasChild(self.ipTrans))
        self.assertTrue(self.ipTrans.hasChild(self.ip))

        self.assertFalse(self.ip.hasChild(self.camTrans))
        self.assertFalse(self.ip.hasChild(self.cam))
        self.assertFalse(self.ip.hasChild(self.ipTrans))
        self.assertFalse(self.ip.hasChild(self.ip))

    def test_isParentOf(self):
        self.assertFalse(self.camTrans.isParentOf(self.camTrans))
        self.assertTrue(self.camTrans.isParentOf(self.cam))
        self.assertTrue(self.camTrans.isParentOf(self.ipTrans))
        self.assertTrue(self.camTrans.isParentOf(self.ip))

        self.assertFalse(self.cam.isParentOf(self.camTrans))
        self.assertFalse(self.cam.isParentOf(self.cam))
        self.assertTrue(self.cam.isParentOf(self.ipTrans))
        self.assertTrue(self.cam.isParentOf(self.ip))

        self.assertFalse(self.ipTrans.isParentOf(self.camTrans))
        self.assertFalse(self.ipTrans.isParentOf(self.cam))
        self.assertFalse(self.ipTrans.isParentOf(self.ipTrans))
        self.assertTrue(self.ipTrans.isParentOf(self.ip))

        self.assertFalse(self.ip.isParentOf(self.camTrans))
        self.assertFalse(self.ip.isParentOf(self.cam))
        self.assertFalse(self.ip.isParentOf(self.ipTrans))
        self.assertFalse(self.ip.isParentOf(self.ip))

    def test_isChildOf(self):
        self.assertFalse(self.camTrans.isChildOf(self.camTrans))
        self.assertFalse(self.camTrans.isChildOf(self.cam))
        self.assertFalse(self.camTrans.isChildOf(self.ipTrans))
        self.assertFalse(self.camTrans.isChildOf(self.ip))

        self.assertTrue(self.cam.isChildOf(self.camTrans))
        self.assertFalse(self.cam.isChildOf(self.cam))
        self.assertFalse(self.cam.isChildOf(self.ipTrans))
        self.assertFalse(self.cam.isChildOf(self.ip))

        self.assertTrue(self.ipTrans.isChildOf(self.camTrans))
        self.assertTrue(self.ipTrans.isChildOf(self.cam))
        self.assertFalse(self.ipTrans.isChildOf(self.ipTrans))
        self.assertFalse(self.ipTrans.isChildOf(self.ip))

        self.assertTrue(self.ip.isChildOf(self.camTrans))
        self.assertTrue(self.ip.isChildOf(self.cam))
        self.assertTrue(self.ip.isChildOf(self.ipTrans))
        self.assertFalse(self.ip.isChildOf(self.ip))
