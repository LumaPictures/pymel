from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import range
from builtins import str
import sys, os, inspect, unittest
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as om

class test_PMTypes(unittest.TestCase):

    def setUp(self):
        self.eu = pm.datatypes.Vector(1,2,3)
        self.r = pm.datatypes.Point([0.25, 0.5, 1.0, 0.5])
        self.u = pm.datatypes.Vector()
        self.v = pm.datatypes.Vector()
        self.n = pm.datatypes.Vector()
        self.w = pm.datatypes.Vector()
        self.p = pm.datatypes.Point()
        self.q = pm.datatypes.Quaternion()
        self.m = pm.datatypes.Matrix()
        self.M = pm.api.MTransformationMatrix()
        self.V = pm.datatypes.VectorN()
        self.t = pm.api.MTransformationMatrix()


    def tearDown(self):
        pass

#############################################################
## MVector tests

    #def testMVector_dir(self):
    #    self.assertEqual(dir(self.u), dir(datatypes.Vector)) # currently errors - 'this' is not present in Vector

    def testMVector_attrs(self):
        self.assertEqual(self.u.shape, pm.datatypes.Vector.shape)
        self.assertEqual(self.u.ndim, pm.datatypes.Vector.ndim)
        self.assertEqual(self.u.size, pm.datatypes.Vector.size)
        self.u.assign(pm.datatypes.Vector(1, 2, 3))
        self.assertEqual(self.u.x, 1.0)
        self.assertEqual(self.u.y, 2.0)
        self.assertEqual(self.u.z, 3.0)

    def testMVector_instance(self):
        # The default class constructor. Creates a null vector.
        self.u = pm.datatypes.Vector()
        self.assertEqual(self.u, pm.datatypes.Vector())

        # The copy constructor. Create a new vector and initialize it to the same values as the given vector.
        self.u.assign(pm.datatypes.Vector(4, 5, 6))
        self.assertEqual(self.u, pm.datatypes.Vector([4.0, 5.0, 6.0]))

        # The copy constructor. Create a new vector and initialize it to the same values as the given vector.
        self.u = pm.datatypes.Vector(1, 2, 3)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # Class constructor. Initializes the vector with the explicit x, y and z values provided as arguments.
        self.u = pm.datatypes.Vector(x=1, y=2, z=3)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # Class constructor. Initializes the vector with the explicit x, y and z values provided in the given double array.
        self.u = pm.datatypes.Vector([1, 2], z=3)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # Class constructor. Initializes the vector with the explicit x, y and z values provided in the given double array.
        self.u[0:2] = [1,1]
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 1.0, 3.0]))

        # The index operator. If its argument is 0 it will return the x component of the vector. If its argument is 1 it will return the y component of the vector. Otherwise it will return the z component of the vector.
    def testMVector_indexOperatorAccess(self):
        self.assertEqual(self.eu(0), 1)
        self.assertEqual(self.eu(1), 2)
        self.assertEqual(self.eu(2), 3)
        self.assertEqual(self.eu(21), 3)

        self.assertEqual(self.eu[0], 1)
        self.assertEqual(self.eu[1], 2)
        self.assertEqual(self.eu[2], 3)

        # Vector from Point
    def testMVector_instanceFromPoint(self):
        self.u = pm.datatypes.Vector(pm.datatypes.Point(1, 2, 3))
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # vector from API point
    def testMVector_instanceMPoint(self):
        self.u = pm.datatypes.Vector(pm.api.MPoint(1, 2, 3))
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # Vector from VectorN
    def testMVector_instanceVectorN(self):
        self.u = pm.datatypes.Vector(pm.datatypes.VectorN(1, 2, 3))
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        # Vector from Single Float
    def testMVector_instance_from_singleFloat(self):
        self.u = pm.datatypes.Vector(1)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 1.0, 1.0]))

        #
    def testMVector_instance_from_VectorOfLengthTwo(self):
        # Z defaults to 0.0
        self.u = pm.datatypes.Vector(1,2)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 0.0]))

    def testMVector_instanceVectorN2(self):
        self.u = pm.datatypes.Vector(pm.datatypes.VectorN(1, shape=(2,)))
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 1.0, 0.0]))

        # construct from Point, overriding individual axis values
    def testMVector_instancePoint2(self):
        self.u = pm.datatypes.Vector(pm.datatypes.Point(1, 2, 3, 1), y=20, z=30)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 20.0, 30.0]))

        # assign value through index access
    def testMVector_indexAssign(self):
        self.u = pm.datatypes.Vector(1, 20, 30)
        self.u[0] = 10
        self.assertEqual(self.u, pm.datatypes.Vector([10.0, 20.0, 30.0]))

    def testMVector_IOBAssign(self):
        def IOBtest():
            self.u = pm.datatypes.Vector(pm.datatypes.VectorN(1, 2, 3, 4))
        self.assertRaises(TypeError,IOBtest)  # fails with TypeError, was expecting ValueError

    def testMVector_in(self):
        self.assertTrue(1.0 in self.eu)

    def testMVector_list(self):
        self.assertEqual(list(self.eu),[1.0, 2.0, 3.0] )

    def testMVector_len(self):
        self.assertEqual(len(self.eu), 3)

    # Ensure that isInstance recognizes u, tests inheritance
    def testMVector_isInstances(self):
        self.assertTrue( isinstance(self.eu, pm.datatypes.VectorN))
        self.assertTrue( isinstance(self.u, pm.datatypes.Array))
        self.assertTrue( isinstance(self.u, pm.api.MVector))

    # Create Vector from api.MPoint
    def testMVector_instanceAPI(self):
        self.u = pm.datatypes.Vector(pm.api.MPoint(1, 2, 3))
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))

#    def testMVector_translateAPI(self):
#        self.u = datatypes.Vector(api.MPoint(1, 2, 3))
#        #self.M.setTranslation ( self.u, api.MSpace.kWorld )
#        self.u = Vector(self.M.getTranslation ( api.MSpace.kWorld ))
#        self.assertEqual(self.u, Vector([1.0, 2.0, 3.0]))

    def testMVector_Axis(self):
        self.u = pm.datatypes.Vector.xAxis
        self.v = pm.datatypes.Vector.yAxis
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 0.0, 0.0]))
        self.assertEqual(self.v, pm.datatypes.Vector([0.0, 1.0, 0.0]))

    def testMVector_crossProduct(self):
        self.u = pm.datatypes.Vector.xAxis
        self.v = pm.datatypes.Vector.yAxis
        self.n = self.u ^ self.v
        self.assertEqual(self.n, pm.datatypes.Vector([0.0, 0.0, 1.0]))
        self.n = self.u ^ pm.datatypes.VectorN(self.v)
        self.assertEqual(self.n, pm.datatypes.Vector([0.0, 0.0, 1.0]))
        self.n = self.u ^ [0, 1, 0]
        self.assertEqual(self.n, pm.datatypes.Vector([0.0, 0.0, 1.0]))

    def testMVector_dotProduct(self):
        self.n = pm.datatypes.Vector([1.0, 1.0, 1.0])
        self.n = self.n * 2
        self.assertEqual(self.n, pm.datatypes.Vector([2.0, 2.0, 2.0]))
        self.n = self.n * [0.5, 1.0, 2.0]
        self.assertEqual(self.n, pm.datatypes.Vector([1.0, 2.0, 4.0]))
        self.n = self.n * self.n
        self.assertEqual(self.n, 21)

    def testMVector_clamp(self):
        self.n = pm.datatypes.Vector([1.0, 3.0, 4.0])
        self.assertEqual((self.n.clamp(1.0, 2.0)),pm.datatypes.Vector([1.0, 2.0, 2.0]))

    def testMVector_neg(self):
        self.n = pm.datatypes.Vector([1.0, 3.0, 4.0])
        self.assertEqual(-self.n,pm.datatypes.Vector([-1.0, -3.0, -4.0]))

    def testMVector_add(self):
        self.u = pm.datatypes.Vector.xAxis
        self.v = pm.datatypes.Vector.yAxis
        self.w = self.u + self.v
        self.assertEqual(self.w,pm.datatypes.Vector([1.0, 1.0, 0.0]))

        self.u = pm.datatypes.Vector.xAxis
        self.assertEqual(self.u + 2,pm.datatypes.Vector([3.0, 2.0, 2.0]))
        self.assertEqual(2 + self.u,pm.datatypes.Vector([3.0, 2.0, 2.0]))
        self.assertEqual((self.u + [0.01, 0.01, 0.01]), pm.datatypes.Vector([1.01, 0.01, 0.01]))

    def testMVectorPoint_add(self):
        self.u = pm.datatypes.Vector.xAxis
        self.p = pm.datatypes.Point(1, 2, 3)

        self.q = self.u + self.p
        self.assertEqual(self.q, pm.datatypes.Point([2.0, 2.0, 3.0]))
        self.q = self.p + self.u
        self.assertEqual(self.q, pm.datatypes.Point([2.0, 2.0, 3.0]))

        self.assertEqual((self.q + self.p), pm.datatypes.Point([3.0, 4.0, 6.0]))
        self.assertEqual((self.p + self.q), pm.datatypes.Point([3.0, 4.0, 6.0]))
        self.assertEqual((self.p + self.u), pm.datatypes.Point([2.0, 2.0, 3.0]))

        self.assertEqual(pm.datatypes.VectorN(1, 2, 3, 4) + self.u, pm.datatypes.VectorN([2.0, 2.0, 3.0, 4])) # TODO want Point returned, rather than VectorN
        self.assertEqual([1, 2, 3] + self.u, pm.datatypes.Vector([2.0, 2.0, 3.0])) # TODO want Point returned, rather than Vector

    def testMVector_and_VectorN(self):
        self.u = pm.datatypes.Vector.xAxis
        self.w = self.u + pm.datatypes.VectorN(1, 2, 3, 4)
        self.assertEqual(self.w, pm.datatypes.VectorN([2.0, 2.0, 3.0, 4]))

    def testMVector_length(self):
        self.u = pm.datatypes.Vector(1, 2, 3)
        self.assertEqual(self.u, pm.datatypes.Vector([1.0, 2.0, 3.0]))
        self.assertAlmostEquals(self.u.length(), 3.74165738677 )
        self.assertAlmostEquals(pm.datatypes.Vector.length(self.u), 3.74165738677 )
        #self.assertAlmostEquals(datatypes.Vector.length([1,2,3]), 3.74165738677 )  # TODO :: TypeError: unbound method length() must be called with Vector instance as first argument (got list instance instead)
        self.assertAlmostEquals(pm.datatypes.length(pm.datatypes.VectorN(1,2,3)), 3.74165738677)
        self.assertAlmostEquals(pm.datatypes.VectorN(1,2,3).length(), 3.74165738677)
        self.assertAlmostEquals(pm.datatypes.VectorN.length(pm.datatypes.VectorN(1,2,3,4)), 5.47722557505)
        self.assertAlmostEquals(pm.datatypes.VectorN(1, 2, 3, 4).length(), 5.47722557505)
        self.assertEqual(pm.datatypes.length(1), 1.0)
        self.assertAlmostEquals(pm.datatypes.length([1,2]),2.2360679775)
        self.assertAlmostEquals(pm.datatypes.length([1,2,3]), 3.74165738677)
        self.assertAlmostEquals(pm.datatypes.length([1,2,3,4]), 5.47722557505)
        self.assertAlmostEquals(pm.datatypes.length([1,2,3,4], 0), 5.47722557505)
        self.assertAlmostEquals(pm.datatypes.length([1,2,3,4], (0,)), 5.47722557505)

        def AxisValTest(): # Axis must be value '0' for all Vectors
            pm.datatypes.length([1, 2, 3, 4], 1)
        self.assertRaises(ValueError,AxisValTest)  # ValueError: axis 0 is the only valid axis for a VectorN, 1 invalid

    def testMVector_sqlength(self):
        self.u = pm.datatypes.Vector(1,2,3)
        self.assertEqual(self.u.sqlength(), 14.0)

    def testMVector_axis(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)
        self.assertEqual(pm.datatypes.axis(self.u, self.v), pm.datatypes.Vector([-0.0, 0.707, 0.0]))
        self.assertEqual(self.u.axis(self.v), pm.datatypes.Vector([-0.0, 0.707, 0.0]))
        self.assertEqual(pm.datatypes.axis(pm.datatypes.VectorN(self.u), pm.datatypes.VectorN(self.v)), pm.datatypes.VectorN([-0.0, 0.707, 0.0]))
        self.assertEqual(pm.datatypes.axis(pm.datatypes.VectorN(self.u), pm.datatypes.VectorN(self.v)), pm.datatypes.VectorN([-0.0, 0.707, 0.0]))
        first = pm.datatypes.axis(self.u, self.v, normalize=True)
        last = pm.datatypes.Vector([-0.0, 1.0, -0.0])
        self.assertTrue(first.isEquivalent(last))

        first = self.v.axis(self.u, normalize=True)
        last = pm.datatypes.Vector([-0.0, -1.0, 0.0])
        self.assertTrue(first.isEquivalent(last))

        first = pm.datatypes.axis(pm.datatypes.VectorN(self.u), pm.datatypes.VectorN(self.v), normalize=True)
        last = pm.datatypes.VectorN([-0.0, 1.0, 0.0])
        self.assertTrue(first.isEquivalent(last))

    def testMVector_angle(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)
        self.assertAlmostEquals(pm.datatypes.angle(self.u,self.v), 0.785398163397 )
        self.assertAlmostEquals(self.v.angle(self.u), 0.785398163397 )
        self.assertAlmostEquals(pm.datatypes.angle(pm.datatypes.VectorN(self.u),pm.datatypes.VectorN(self.v)),0.785398163397 )
        self.assertEqual(pm.datatypes.cotan(self.u, self.v), 1.0)

    def testMVector_angleRotateTo(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)

        first = self.u.rotateTo(self.v)
        last = pm.datatypes.Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
        self.assertTrue(first.isEquivalent(last))

    def testMVector_angleRotateBy(self):
        u = pm.datatypes.Vector(1, 0, 0)
        v = pm.datatypes.Vector(0.707, 0, -0.707)

        first = u.rotateBy(u.axis(v), u.angle(v))
        last = pm.datatypes.Vector([0.707106781187, 0.0, -0.707106781187])

        self.assertTrue(first.isEquivalent(last))

        q = pm.datatypes.Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])

        first = u.rotateBy(q)
        last = pm.datatypes.Vector([0.707106781187, 0.0, -0.707106781187])
        self.assertTrue(first.isEquivalent(last))


    def testMVector_angleDistanceTo(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)
        self.assertAlmostEquals(self.u.distanceTo(self.v),0.765309087885)

    def testMVector_angleParallel(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)
        self.assertFalse(self.u.isParallel(self.v))
        self.assertTrue(self.u.isParallel(2*self.u))

    def testMVector_normal(self):
        self.u = pm.datatypes.Vector(1,2,3)
        first = self.u.normal()
        last = pm.datatypes.Vector([0.267261241912, 0.534522483825, 0.801783725737])
        self.assertTrue(first.isEquivalent(last))

    def testMVector_normalize(self):
        self.u = pm.datatypes.Vector(1,2,3)
        self.u.normalize()
        last = pm.datatypes.Vector([0.267261241912, 0.534522483825, 0.801783725737])
        self.assertTrue(self.u.isEquivalent(last))

    def testMVector_equality(self):
        self.u = pm.datatypes.Vector(1,2,3)
        self.w = self.u + pm.datatypes.VectorN(1, 2, 3, 4)
        self.assertTrue(self.u == self.u)
        self.assertTrue(self.u != self.w)
        self.assertTrue(self.u == pm.datatypes.Vector(1.0, 2.0, 3.0))
        #self.failIfEqual(self.u == [1.0, 2.0, 3.0])
        self.assertTrue(self.u != [1.0, 2.0, 3.0])
        self.assertTrue(self.u != pm.datatypes.Point(1.0, 2.0, 3.0))
        self.assertTrue(self.u.isEquivalent([1.0, 2.0, 3.0]))
        self.assertTrue(self.u.isEquivalent(pm.datatypes.Vector(1.0, 2.0, 3.0)))
        self.assertTrue(self.u.isEquivalent(pm.datatypes.Point(1.0, 2.0, 3.0)))
        #self.assertFalse(self.u.isEquivalent(self.w)) # TODO :: TypeError: super(type, obj): obj must be an instance or subtype of type
        #self.assertTrue(self.u.isEquivalent(self.w, 0.1)) # TODO :: TypeError: super(type, obj): obj must be an instance or subtype of type

    def testMVector_angleBlend(self):
        self.u = pm.datatypes.Vector(1, 0, 0)
        self.v = pm.datatypes.Vector(0.707, 0, -0.707)
        goop = pm.datatypes.Vector([0.8535, 0.0, -0.3535])
        self.assertTrue(self.u.blend(self.v).data.isEquivalent(goop.data))

#############################################################
## MPoint tests

    def testMPoint_hasAttr(self):
        self.assertTrue(hasattr(pm.datatypes.Point,'data'))

    def testMPoint_list(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(list(self.p),[1.0, 2.0, 3.0] )

    def testMPoint_len(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(len(self.p),3)

    def testMPoint_size(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(self.p.size,4)

    def testMPoint_indiceAccess(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(self.p.x, 1.0)
        self.assertEqual(self.p.y, 2.0)
        self.assertEqual(self.p.z, 3.0)
        self.assertEqual(self.p.w, 1.0)

        self.assertEqual(self.p[0], 1.0)
        self.assertEqual(self.p[1], 2.0)
        self.assertEqual(self.p[2], 3.0)
        self.assertEqual(self.p[3], 1.0)

    def testMPoint_get(self):
        self.p = pm.datatypes.Point(1,2,3)
        got = self.p.get()
        self.assertTrue(got == (1.0, 2.0, 3.0, 1.0))

    def testMPoint_distanceTo(self):
        self.q = pm.api.MPoint()
        self.p = pm.datatypes.Point(1,2,3)
        self.assertAlmostEquals(self.q.distanceTo(self.p), 3.74165738677)


    def testMPoint_NonCartesion_instance(self):
        # support for non cartesian points still there
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0, 2.0]))

        self.v = pm.datatypes.Vector(self.p)
        self.assertEqual(self.v, pm.datatypes.Vector([0.5, 1.0, 1.5]))

        self.V = pm.datatypes.VectorN(self.p)
        self.assertEqual(self.V,pm.datatypes.VectorN([1.0, 2.0, 3.0, 2.0]))

    def testMPoint_NonCartesion_list(self):
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        self.assertEqual(list(self.p), [1.0, 2.0, 3.0, 2.0])

    def testMPoint_NonCartesion_len(self):
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        self.assertEqual(len(self.p),4)

    def testMPoint_NonCartesion_size(self):
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        self.assertEqual(self.p.size,4)

    def testMPoint_NonCartesion_indexLetterAccess(self):
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        self.assertEqual(self.p.x, 1.0)
        self.assertEqual(self.p.y, 2.0)
        self.assertEqual(self.p.z, 3.0)
        self.assertEqual(self.p.w, 2.0)

        self.assertEqual(self.p[0], 1.0)
        self.assertEqual(self.p[1], 2.0)
        self.assertEqual(self.p[2], 3.0)
        self.assertEqual(self.p[3], 2.0)

    def testMPoint_NonCartesion_Get(self):
        got = ""
        self.p = pm.datatypes.Point(1, 2, 3, 2)
        got = self.p.get()
        self.assertTrue(got == (1.0, 2.0, 3.0, 2.0))


##############################################################

#        self.q = api.MPoint()
#        self.assertEqual(self.q.distanceTo(self.p), 1.87082869339)

##############################################################


        self.p = pm.datatypes.Point (pm.api.MPoint())
        self.assertEqual(self.p, pm.datatypes.Point([0.0, 0.0, 0.0]))

        self.p = pm.datatypes.Point(1)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 1.0, 1.0]))

        self.p = pm.datatypes.Point(1, 2)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 0.0]))

        self.p = pm.datatypes.Point(1, 2, 3)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

        self.p = pm.datatypes.Point(pm.api.MPoint(1, 2, 3))
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

        self.p = pm.datatypes.Point(pm.datatypes.VectorN(1,2))
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 0.0]))

        self.p = pm.datatypes.Point(pm.datatypes.VectorN(1, 2, 3))
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

    def testMPoint_instance(self):
        self.p = pm.datatypes.Point()
        self.assertEqual(self.p, pm.datatypes.Point([0.0, 0.0, 0.0]))
        self.assertTrue("<maya.OpenMaya.MPoint; proxy of <Swig Object of type 'MPoint *' at" in repr(self.p.data))

        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

        self.v = pm.datatypes.Vector(self.p)
        self.assertNotEqual(self.p, self.v)
        self.assertTrue(self.p.isEquivalent(self.v))
        self.assertTrue(self.v.isEquivalent(self.p))
        self.assertEqual(self.v, pm.datatypes.Vector([1.0, 2.0, 3.0]))

        self.V = pm.datatypes.VectorN(self.p)
        self.assertEqual(self.V, pm.datatypes.VectorN([1.0, 2.0, 3.0, 1.0]))

        # Point from MVector
        self.p = pm.datatypes.Point(pm.api.MVector(1, 2, 3))
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

        # Point from datatypes.VectorN
        self.p = pm.datatypes.Point(pm.datatypes.VectorN(1, 2, 3, 4))
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0, 4.0]))

        # Point from datatypes.Vector from Point
        self.p = pm.datatypes.Point(pm.datatypes.Vector(self.p))
        self.assertEqual(self.p, pm.datatypes.Point([0.25, 0.5, 0.75]))

        # VectorN from Point from VectorN
        self.p = pm.datatypes.Point(pm.datatypes.VectorN(1, 2, 3, 4))
            # notice the last minute, sneak conversion to VectorN.
        self.assertEqual(pm.datatypes.VectorN(self.p), pm.datatypes.VectorN([1.0, 2.0, 3.0, 4.0]))

        # Copy Constructor
        self.p = pm.datatypes.Point(self.p, w=1)
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 2.0, 3.0]))

        # datatypes.Vector from Point
        self.assertEqual(pm.datatypes.Vector(self.p), pm.datatypes.Vector([1.0, 2.0, 3.0])) # test Vector from Point

        # datatypes.VectorN from Point
        self.assertEqual(pm.datatypes.VectorN(self.p), pm.datatypes.VectorN([1.0, 2.0, 3.0, 1.0]))

        # origin test
        self.p = pm.datatypes.Point.origin
        self.assertEqual(self.p, pm.datatypes.Point([0.0, 0.0, 0.0]))

        # xAxis test
        self.p = pm.datatypes.Point.xAxis
        self.assertEqual(self.p, pm.datatypes.Point([1.0, 0.0, 0.0]))

        # yAxis test
        self.p = pm.datatypes.Point.yAxis
        self.assertEqual(self.p, pm.datatypes.Point([0.0, 1.0, 0.0]))

        # zAxis test
        self.p = pm.datatypes.Point.zAxis
        self.assertEqual(self.p, pm.datatypes.Point([0.0, 0.0, 1.0]))


    def testMPoint_add(self):
        self.p = pm.datatypes.Point(1, 2, 3, 1)
        self.assertEqual(self.p + 2, pm.datatypes.Point([3.0, 4.0, 5.0, 1.0]))
        self.assertEqual(2 + self.p, pm.datatypes.Point([3.0, 4.0, 5.0, 1.0]))

        #reset vals
        self.p = pm.datatypes.Point(1, 2, 3)

        # Point and Vector :: returns Point
        self.assertEqual(self.p + pm.datatypes.Vector([1, 2, 3]), pm.datatypes.Point([2.0, 4.0, 6.0]))

        # Point and Point :: returns Point
        self.assertEqual(self.p + pm.datatypes.Point([1, 2, 3]), pm.datatypes.Point([2.0, 4.0, 6.0]))

        # Point and list(3,) :: returns Point
        self.assertEqual(self.p + [1, 2, 3], pm.datatypes.Point([2.0, 4.0, 6.0]))

        # Point(3,) and Point(4,) :: returns Point
        self.assertEqual(self.p + pm.datatypes.Point([1, 2, 3, 1]), pm.datatypes.Point([2.0, 4.0, 6.0]))
        self.assertEqual(self.p + pm.datatypes.Point([1, 2, 3, 2]), pm.datatypes.Point([1.5, 3.0, 4.5]))

        # Vector and Point :: returns Point
        self.assertEqual((pm.datatypes.Vector([1, 2, 3]) + self.p), pm.datatypes.Point([2.0, 4.0, 6.0]))

        # Point and List(4,) :: returns Point
        self.assertEqual(self.p + [1, 2, 3, 2], pm.datatypes.Point([2.0, 4.0, 6.0, 3.0]))

        # Point(3,) and Point :: returns Point
        self.assertEqual((pm.datatypes.Point([1, 2, 3]) + self.p), pm.datatypes.Point([2.0, 4.0, 6.0]))

        # List and Point :: returns Point
        self.assertEqual(([1, 2, 3] + self.p), pm.datatypes.Point([2.0, 4.0, 6.0]))

        # TODO : returns Vector - expected Point([2.0, 4.0, 6.0])) :: if w=1, it returns type Vector,otherwise returns Point
        self.assertEqual(([1, 2, 3, 1] + self.p), pm.datatypes.Vector([2.0, 4.0, 6.0]))

        # not sure what ths chunk is testing for?
        #self.p = datatypes.Point(1, 2, 3)  # reset for all
        #self.assertEquasls((datatypes.Point([1,2,3]) + self.p), datatypes.Point([2.0, 4.0, 6.0]))
        #self.assertEqual([1,2,3,2] + self.p, datatypes.Point([2.0, 4.0, 6.0, 3.0]))
        #self.assertEqual((datatypes.Point([1, 2, 3, 2]) + self.p), datatypes.Point([1.5, 3.0, 4.5]))

    def testMPoint_operations(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.25, 0.5, 1.0)

        # divide point by scalar
        self.assertEqual((self.p / 2),pm.datatypes.Point([0.5, 1.0, 1.5]))

        # multiply point by scalar
        self.assertEqual((self.p * 2),pm.datatypes.Point([2.0, 4.0, 6.0]))

        # add point by scalar
        self.assertEqual(self.q + 2,pm.datatypes.Point([2.25, 2.5, 3.0]))

        # divide point by scalar
        self.assertEqual(self.q / 2,pm.datatypes.Point([0.125, 0.25, 0.5]))

        # add point to point
        #self.assertEqual(self.p + self.q, datatypes.Point([1.25, 2.5, 4.0]))

        # subtract point from point :: successfully returns Vector instance
        self.assertEqual(self.p - self.q, pm.datatypes.Vector([0.75, 1.5, 2.0]))
        self.assertEqual(self.q - self.p, pm.datatypes.Vector([-0.75, -1.5, -2.0]))

        # subtract point from (point subtracted from point) :: nested/transitive subtraction
        self.assertEqual(self.p-(self.p - self.q), pm.datatypes.Point([0.25, 0.5, 1.0]))

        # Multiply Vectors from Points
        self.assertEqual(pm.datatypes.Vector(self.p) * pm.datatypes.Vector(self.q), 4.25)

        # Point multiplication
        self.assertEqual(self.p*self.q, 4.25)

        # divide point by point
        self.assertEqual(self.p / self.q, pm.datatypes.Vector([4.0, 4.0, 3.0])) # TODO : Original expected Point([4.0, 4.0, 3.0])

        # divide point by scalar
        self.assertEqual(self.p / 2, pm.datatypes.Point([0.5, 1.0, 1.5]))

        # multiply point by scalar
        self.assertEqual(self.p * 2, pm.datatypes.Point([2.0, 4.0, 6.0]))

    def testMPoint_cartesianize(self):
        locCop = pm.datatypes.Point(self.r)
        self.assertEqual(locCop.cartesian(),pm.datatypes.Point([0.5, 1.0, 2.0]))
        self.assertEqual(locCop.cartesianize(),pm.datatypes.Point([0.5, 1.0, 2.0]))

#    def testMPoint_deepcopy(self):
#        self.assertEqual(self.r, datatypes.Point([0.25, 0.5, 1.0, 0.5]))
#        self.assertEqual(self.r, self.qc)

    def testMPoint_rationalize(self):
        locCop = pm.datatypes.Point(self.r)
        self.assertEqual(locCop.rational(), pm.datatypes.Point([0.5, 1.0, 2.0, 0.5]))
        self.assertEqual(locCop.rationalize(), pm.datatypes.Point([0.5, 1.0, 2.0, 0.5])) # TODO :: currently returns Point([1.0, 2.0, 4.0, 0.5]

    def testMPoint_homegenize(self):
        locCop = pm.datatypes.Point(self.r)
        self.assertEqual(locCop.homogen(), pm.datatypes.Point([0.125, 0.25, 0.5, 0.5]))
        self.assertEqual(locCop.homogenize(), pm.datatypes.Point([0.125, 0.25, 0.5, 0.5])) # TODO :: homogen leaves self.r intact, returns homogenized

    def testMPoint_VectorFromCartesianizedPoint(self):
        locCop = pm.datatypes.Point(self.r)
        self.assertEqual(pm.datatypes.Vector(locCop.cartesian()), pm.datatypes.Vector([0.5, 1.0, 2.0])) #ignores 'w'

    def testMPoint_dividePointByScalar(self):
        self.assertEqual(self.r / 2, pm.datatypes.Point([0.125, 0.25, 0.5, 0.5]))

    def testMPoint_multPointByScalar(self):
        self.assertEqual(self.r * 2, pm.datatypes.Point([0.5, 1.0, 2.0, 0.5]))

    def testMPoint_addPointToScalar(self):
        self.assertEqual(self.r + 2, pm.datatypes.Point([2.5, 3.0, 4.0]))  # cartesianize is done by datatypes.Vector's add

    def testMPoint_VectorInst_addition(self):
        self.p = pm.datatypes.Point(1,2,3)
        #self.q = datatypes.Point(0.25, 0.5, 1.0)
        self.assertEqual((self.p + pm.datatypes.Vector(1, 2, 3)), pm.datatypes.Point([2.0, 4.0, 6.0]))
        self.assertEqual((self.r + pm.datatypes.Vector(1, 2, 3)), pm.datatypes.Point([1.5, 3.0, 5.0]))

    def testMPoint_cartesion_VectorInst_addition(self):
        self.assertEqual((self.r.cartesian() + pm.datatypes.Vector(1,2,3)), pm.datatypes.Point([1.5, 3.0, 5.0]))

    def testMPoint_subtractPointFromPoint(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.25, 0.5, 1.0)
        self.assertEqual((self.p - self.r), pm.datatypes.Vector([0.5, 1.0, 1.0]))
        self.assertEqual((self.r - self.p), pm.datatypes.Vector([-0.5, -1.0, -1.0]))
        self.assertEqual(self.p - (self.p - self.r), pm.datatypes.Point([0.5, 1.0, 2.0]))

    def testMPoint_cartesian_subtraction(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual((self.p-self.r.cartesian()), pm.datatypes.Vector([0.5, 1.0, 1.0]))

    def testMPoint_VectorMultiply_from_Points(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(pm.datatypes.Vector(self.p) * pm.datatypes.Vector(self.r), 8.5)

    def testMPoint_mult(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertEqual(self.p * self.r, 8.5)

 #   def testMPoint_dividePoints(self):  # TODO : need explicit homogenize as division not handled by api
 #       homoP = self.p.homogenize()
 #       homoQ = self.q.homogenize()
 #       self.assertEqual(homoP / homoQ, datatypes.Vector([2.0, 2.0, 1.5])) # used to be Point([4.0, 4.0, 3.0, 2.0])
        #  TODO : what do we want here ?

    def testMPoint_length(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.assertAlmostEquals(self.p.length(),3.74165738677)
        self.assertEqual(self.p[:1].length(), 1.0)
        self.assertEqual(pm.datatypes.length(self.p[:1]), 1.0)
        self.assertAlmostEquals(self.p[:2].length(), 2.2360679775)
        self.assertAlmostEquals(self.p[:3].length(), self.p.length())
        self.assertAlmostEquals(pm.datatypes.length(self.p),3.74165738677)


    def testMPoint_axis(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.707, 0.0, -0.707)
        # returns Vector(- + -)
        self.assertEqual(pm.datatypes.axis(pm.datatypes.Point.origin, self.p, self.q), pm.datatypes.Vector([-1.414, 2.828, -1.414]))
        # returns Vector(- + -)
        self.assertEqual(pm.datatypes.Point.origin.axis(self.p, self.q), pm.datatypes.Vector([-1.414, 2.828, -1.414]))
        # returns Vector(+ - +)
        self.assertEqual(pm.datatypes.Point.origin.axis(self.q, self.p), pm.datatypes.Vector([1.414, -2.828, 1.414]))

    def testMPoint_angle(self): # TODO :: WONKY ass vals returned - do the math again
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.707, 0.0, -0.707)
        self.assertAlmostEquals(pm.datatypes.angle(pm.datatypes.Point.origin, self.p, self.q), 1.9583930134500773)
        self.assertAlmostEquals(pm.datatypes.angle(pm.datatypes.Point.origin, self.q, self.p), 1.9583930134500773)

        self.assertAlmostEquals(pm.datatypes.angle(pm.datatypes.Point.origin, self.p, self.r), 0.13078263384791716)
        self.assertAlmostEquals(pm.datatypes.angle(pm.datatypes.Point.origin, self.r, self.p), 0.13078263384791716)

        self.assertAlmostEquals(pm.datatypes.Point.origin.angle(self.p, self.q), 1.9583930134500773)
        self.assertAlmostEquals(pm.datatypes.Point.origin.angle(self.p, self.r), 0.13078263384791716)
        # self.assertEqual(datatypes.cotan(datatypes.Point.origin, self.p, self.q), 1.0)

    def testMPoint_distance(self):
        self.q = pm.datatypes.Point(0.707, 0.0, -0.707)
        self.p = pm.datatypes.Point(1,2,3)
        self.assertAlmostEquals(self.p.distanceTo(self.q), 4.2222858737892199)

    def testMPoint_differenceLengthForDistance(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.707, 0.0, -0.707)
        self.assertAlmostEquals((self.q-self.p).length(), 4.2222858737892199)

    def testMPoint_planar(self):
        self.p = pm.datatypes.Point(1,2,3)
        self.q = pm.datatypes.Point(0.707, 0.0, -0.707)
        self.assertTrue( pm.datatypes.planar( pm.datatypes.Point.origin, self.p, self.q ))
        #self.assertTrue( datatypes.planar( datatypes.Point.origin, self.p, self.q, self.r )) # TODO :: currently evaluates to false whenever you pass in mor than three args
        #self.assertFalse(datatypes.planar( datatypes.Point.origin, self.p, self.q, self.r + datatypes.Vector(0.0, 0.1, 0.0)))

    def testMPoint_center(self):
        locP = pm.datatypes.Point([1.0, 2.0, 3.0])
        locQ = pm.datatypes.Point([1.0, 2.0, 3.0, 1.0])
        first = pm.datatypes.center(pm.datatypes.Point.origin, locP, locP)
        last = pm.datatypes.Point([0.666666666667, 1.33333333333, 2.0])
        self.assertTrue(first, last) #TODO # Point([0.569, 0.0, -0.235666666667, 1.0])

    def testMPoint_bWeights(self):
        locP = pm.datatypes.Point([1.0, 2.0, 3.0])
        locQ = pm.datatypes.Point([1.0, 2.0, 3.0, 1.0])

        self.assertEqual(pm.datatypes.bWeights(self.r, pm.datatypes.Point.origin, locP, locQ), (0.0, 0.5, 0.5))
        self.assertEqual(pm.datatypes.bWeights((.5,0,0), (0,0,0),(1,0,0),(1,1,0),(0,1,0)), (.5, .5, 0, 0))

    def testMPoint_round(self):
        self.p = pm.datatypes.Point([0.33333, 0.66666, 1.333333, 0.33333])
        self.assertEqual(pm.datatypes.round(self.p, 3), pm.datatypes.Point([0.333, 0.667, 1.333, 0.333]) )


##################################################################
## MColor tests

    def testMColor_hasattr(self):
        self.assertTrue(hasattr(pm.datatypes.Color, 'data'))

    def testMColor_instance_hasattr(self):
        self.c = pm.datatypes.Color()
        self.assertTrue(hasattr(self.c, 'data'))

    def testMColor_instance(self):
        self.c = pm.datatypes.Color()
        self.assertEqual(self.c, pm.datatypes.Color([0.0, 0.0, 0.0, 1.0]))

        self.c = pm.datatypes.Color(pm.api.MColor())
        self.assertEqual(self.c, pm.datatypes.Color([0.0, 0.0, 0.0, 1.0])) # TODO - using api convention of single value would mean alpha
        # instead of datatypes.VectorN convention of filling all with value
        # which would yield # Color([0.5, 0.5, 0.5, 0.5]) instead
        # This would break coerce behavior for Color

        self.c = pm.datatypes.Color(0.5)
        self.assertEqual(self.c ,pm.datatypes.Color([0.5, 0.5, 0.5, 0.5]))

        self.c = pm.datatypes.Color(1, 1, 1)
        self.assertEqual(self.c , pm.datatypes.Color([1.0, 1.0, 1.0, 1.0]))

        self.c = pm.datatypes.Color(1, 0.5, 2, 0.5)
        self.assertEqual(self.c,pm.datatypes.Color([1.0, 0.5, 2.0, 0.5]))

        self.c = pm.datatypes.Color(128, quantize=255)
        self.assertEqual(self.c , pm.datatypes.Color([0.501960813999, 0.501960813999, 0.501960813999, 0.501960813999]))

        self.c = pm.datatypes.Color(255, 128, b=64, a=32, quantize=255)
        self.assertEqual(self.c , pm.datatypes.Color([1.0, 0.501960813999, 0.250980407, 0.1254902035]))

        self.c = pm.datatypes.Color(0, 65535, 65535, quantize=65535, mode='hsv')
        self.assertEqual(self.c , pm.datatypes.Color([1.0, 0.0, 0.0, 1.0]))

        self.c = pm.datatypes.Color(self.c, v=0.5, mode='hsv')
        self.assertEqual(self.c , pm.datatypes.Color([0.5, 0.0, 0.0, 1.0]))

    def testMColor_CopyConstructor(self):
        self.c = pm.datatypes.Color(pm.datatypes.Color.blue, v=0.5)
        self.assertEqual(self.c , pm.datatypes.Color([0.0, 0.0, 0.5, 1.0]))

    def testMColor_round(self):
        self.c = pm.datatypes.round(pm.datatypes.Color(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)
        self.assertEqual(self.c , pm.datatypes.Color([1.0, 0.5, 1.0, 1.0]))

        self.c = pm.datatypes.round(pm.datatypes.Color(255, b=128, quantize=255, mode='rgb'), 2)
        self.assertEqual(self.c , pm.datatypes.Color([1.0, 1.0, 0.5, 1.0]))

    def testMColor_rgb(self):
        self.c = pm.datatypes.Color(0, 65535, 65535, quantize=65535, mode='hsv')
        self.assertEqual(self.c.rgb, (1.0, 0.0, 0.0))

    def testMColor_hsv(self):
        self.c = pm.datatypes.Color(0, 65535, 65535, quantize=65535, mode='hsv')
        self.assertEqual(self.c.hsv, (0.0, 1.0, 1.0))

        self.d = pm.datatypes.Color(self.c, v=0.5, mode='hsv')
        self.assertEqual(self.d.hsv,(0.0, 1.0, 0.5))

        self.c = pm.datatypes.Color(pm.datatypes.Color.blue, v=0.5)
        self.assertEqual(self.c.hsv,(0.66666666666666663, 1.0, 0.5))

    def testMColor_rgbIndex_access(self):
        self.c = pm.datatypes.Color(pm.datatypes.Color.blue, v=0.5)
        self.c.r = 1.0
        self.c.g = 2.0
        self.c.b = 3.0
        self.c.a = 0.5

        self.assertEqual(self.c , pm.datatypes.Color([1.0, 2.0, 3.0, 0.5]))
        self.assertEqual(self.c.hsv, (0.0, 0.0, 1.0))

    def testMColor_RGB_Constructor_Clamp(self):
        self.c = pm.datatypes.Color(1, 0.5, 2, 0.5).clamp()
        self.assertEqual(self.c, pm.datatypes.Color([1.0, 0.5, 1.0, 0.5]) )
        self.assertEqual(self.c.hsv, (0.83333333333333337, 0.5, 1.0))

    def testMColor_Copy_Constructor(self):
        self.c = pm.datatypes.Color(1, 0.5, 2, 0.5).clamp()
        self.d = pm.datatypes.Color(self.c,v=0.5)
        self.assertEqual(self.d, pm.datatypes.Color([0.5, 0.25, 0.5, 0.5]))
        self.assertEqual(self.d.hsv, (0.83333333333333337, 0.5, 0.5))

    def testMColor_RGB_Constructor(self):
        self.c = pm.datatypes.Color(0.0, 0.5, 1.0, 0.5)
        self.assertEqual(self.c, pm.datatypes.Color(0.0, 0.5, 1.0, 0.5))

    def testMColor_Gamma(self):
        self.c = pm.datatypes.Color(0.0, 0.5, 1.0, 0.5)
        self.d = self.c.gamma(2.0)
        self.assertEqual(self.d, pm.datatypes.Color([0.0, 0.25, 1.0, 0.5]))

    def testMColor_Blend(self):
        self.c = pm.datatypes.Color.red.blend(pm.datatypes.Color.blue, 0.5)
        self.assertEqual(self.c.hsv, (0.83333333333333337, 1.0, 0.5))

    def testMColor_HsvBlend(self):
        self.c = pm.datatypes.Color.red.hsvblend(pm.datatypes.Color.blue, 0.5)
        self.assertEqual(self.c.hsv, (0.83333333333333337, 1.0, 1.0))

    def testMColor_Over(self):
        self.c = pm.datatypes.Color(0.25, 0.5, 0.75, 0.5)
        self.d = pm.datatypes.Color.black
        self.assertEqual(self.c.over(self.d), pm.datatypes.Color([0.125, 0.25, 0.375, 1.0]) )
        self.assertEqual(self.d.over(self.c), pm.datatypes.Color([0.0, 0.0, 0.0, 0.5]))

    def testMColor_RGB_Constructor_Premult(self):
        self.c = pm.datatypes.Color(0.25, 0.5, 0.75, 0.5)
        self.assertEqual(self.c.premult(), pm.datatypes.Color([0.125, 0.25, 0.375, 1.0]))

    def testMColor_VectorInheritance(self):
        self.c = pm.datatypes.Color(0.25, 0.5, 1.0, 1.0)
        self.d = pm.datatypes.Color(2.0, 1.0, 0.5, 0.25)
        self.assertEqual(self.c, pm.datatypes.Color([0.25, 0.5, 1.0, 1.0]))
        self.assertEqual(self.d, pm.datatypes.Color([2.0, 1.0, 0.5, 0.25]))

        # Negative assignment
        self.assertEqual(-(self.c), pm.datatypes.Color([-0.25, -0.5, -1.0, 1.0]))

        # Multiply two colors
        self.e = self.c * self.d
        self.assertEqual(self.e, pm.datatypes.Color([0.5, 0.5, 0.5, 0.25]))

        # Addition with constant
        self.assertEqual((self.e + 2), pm.datatypes.Color([2.5, 2.5, 2.5, 0.25]))

        # Multiply by scalar float
        # (defined in api for colors and also multiplies alpha)
        self.assertEqual((self.e * 2.0), pm.datatypes.Color([1.0, 1.0, 1.0, 0.5]))

        # Divide by scalar float
        # TODO as is divide, that ignores alpha now for some reason
        self.assertEqual((self.e/2.0), pm.datatypes.Color([0.25, 0.25, 0.25, 0.25]))

        # Addition with Vector Instance
        self.assertEqual(self.e + pm.datatypes.Vector(1,2,3), pm.datatypes.Color([1.5, 2.5, 3.5, 0.25]))
        # TODO Come correct? Here, behaves like API.

        # Addition with self
        self.assertEqual((self.c + self.c), pm.datatypes.Color([0.5, 1.0, 2.0, 1.0]))
        # Addition with Color
        self.assertEqual((self.c + self.d), pm.datatypes.Color([2.25, 1.5, 1.5, 1.0]))
        # Subtraction with Color
        self.assertEqual((self.d - self.c), pm.datatypes.Color([1.75, 0.5, -0.5, 0.25]))
        #print "end tests Color" - TODO go through classes and make sure all methods are represented

#===============================================================================
# Euler Tests
#===============================================================================
    def testEuler_units(self):
        oldUnit = pm.datatypes.Angle.getUIUnit()
        try:
            pm.datatypes.Angle.setUIUnit('degrees')
            inDegrees = [10,20,30]
            eDeg = pm.datatypes.EulerRotation(inDegrees)
            self.assertEqual(eDeg, pm.datatypes.EulerRotation(inDegrees, unit='degrees'))
            eRad = pm.datatypes.EulerRotation(eDeg)
            eRad.unit = 'radians'
            self.assertEqual(eDeg, eRad)
            inRadians = [pm.datatypes.Angle(x, unit='degrees').asRadians() for x in inDegrees]
            eRad2 = pm.datatypes.EulerRotation(inRadians, unit='radians')
            self.assertEqual(eRad2, eDeg)
            self.assertNotEqual(eRad2.x, eDeg.x)
            self.assertEqual(list(eDeg), [pm.datatypes.Angle(x, unit='radians').asDegrees() for x in eRad2])
        finally:
            pm.datatypes.Angle.setUIUnit(oldUnit)

    def testEuler_rotationOrder(self):
        rot = pm.datatypes.EulerRotation(10,20,30, 'XYZ')
        self.assertEqual(rot.order, 'XYZ')
        rot.order = 'ZYX'
        self.assertEqual(rot.order, 'ZYX')
        other = pm.datatypes.EulerRotation(10,20,30, 'ZYX')
        self.assertEqual(other.order, 'ZYX')
        self.assertEqual(rot, pm.datatypes.EulerRotation(10,20,30, 'ZYX'))
        rot.assign( (6,7,8) )
        self.assertEqual(rot.order, 'ZYX')

    def testEuler_setItem(self):
        rot = pm.datatypes.EulerRotation(10,20,30, 'XYZ')
        self.assertAlmostEqual(rot.y, 20)
        rot.y = 50
        self.assertAlmostEqual(rot.y, 50)
        self.assertAlmostEqual(rot.z, 30)
        rot['z'] = 60
        self.assertAlmostEqual(rot.z, 60)
        self.assertAlmostEqual(rot.x, 10)
        rot[0] = 70
        self.assertAlmostEqual(rot.x, 70)

    ##################################################################
    ## MMatrix tests

    def testMatrix_Instance(self) :
        self.m = pm.datatypes.Matrix()
        self.assertEqual(self.m.shape, pm.datatypes.Matrix.shape)
        self.assertEqual(self.m.ndim,  pm.datatypes.Matrix.ndim)
        self.assertEqual(self.m.size,  pm.datatypes.Matrix.size)

    def testIdentityMatrix_IsInstance(self) :
        self.m = pm.datatypes.Matrix.identity
        self.assertTrue(isinstance(self.m, pm.datatypes.MatrixN))
        self.assertTrue(isinstance(self.m, pm.datatypes.Array))
        self.assertTrue(isinstance(self.m, pm.api.MMatrix))

    def testMatrix_False_Instances(self) :
        def Matrix_fromRange_Test():
            self.m = pm.datatypes.Matrix(list(range(20))) # TODO should fail
            self.m.formated()
        #   cannot initialize a Matrix of shape (4, 4) from list of 20,
        #   would cause truncation errors, use an explicit resize or trim"
        self.assertRaises(TypeError, Matrix_fromRange_Test)

#        self.m = datatypes.Matrix()
#        def MatrixSetTest1():
#            self.m.shape = (4,4) # TODO should fail
#        def MatrixSetTest2():
#            self.m.shape = 2
#
#        self.assertRaises(ValueError, MatrixSetTest1)
#        self.assertRaises(ValueError, MatrixSetTest2)

    def testMatrix_formated(self) :
        self.m = pm.datatypes.Matrix()
        self.assertEqual(self.m.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

    def testMatrix_IndexAccess(self) :
        self.m = pm.datatypes.Matrix()


        # Single Index
        self.assertEqual(self.m[0][0], 1.0)
        #self.assertEqual(self.m[0:0][0:2],[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]) ## TODO :: WTF?
        # Multi Index
        self.assertEqual(self.m[1:2][0:1], pm.datatypes.MatrixN([[0.0, 1.0, 0.0, 0.0]]))

        # paren indice access
        self.assertEqual(self.m(0,0), 1.0)

    def testMMatrix_API_Calls(self) :
        # should be accepted directly by API methods
        self.n = pm.api.MMatrix()

        # SetToProduct # TODO returns MMatrix() ?
        self.m = self.n.setToProduct(self.m,self.m)
        self.assertTrue("<maya.OpenMaya.MMatrix; proxy of <Swig Object of type 'MMatrix *' at" in repr(self.m)) #TODO -

        # Make MAtrix instance from range()
        self.m = pm.datatypes.Matrix(list(range(16)))
        self.assertEqual(self.m.formated(), '[[0.0, 1.0, 2.0, 3.0],\n [4.0, 5.0, 6.0, 7.0],\n [8.0, 9.0, 10.0, 11.0],\n [12.0, 13.0, 14.0, 15.0]]')

        # Make Matrix instance from Array from range()
        self.M = pm.datatypes.Array(list(range(16)), shape=(8, 2))
        self.m = pm.datatypes.Matrix(self.M)
        self.assertEqual(self.m.formated(), '[[0.0, 1.0, 2.0, 3.0],\n [4.0, 5.0, 6.0, 7.0],\n [8.0, 9.0, 10.0, 11.0],\n [12.0, 13.0, 14.0, 15.0]]')

        # Make Matrix instance from MatrixN from range()
        self.M = pm.datatypes.MatrixN(list(range(9)), shape=(3, 3))
        self.m = pm.datatypes.Matrix(self.M)
        self.assertEqual(self.m.formated(),'[[0.0, 1.0, 2.0, 0.0],\n [3.0, 4.0, 5.0, 0.0],\n [6.0, 7.0, 8.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

        # inherits from Array and MatrixN
        self.assertTrue(isinstance(self.m, pm.datatypes.MatrixN))
        self.assertTrue(isinstance(self.m, pm.datatypes.Array))

        # as well as _api_Matrix
        self.assertTrue(isinstance(self.m, pm.api.MMatrix))

        # create transformationmatrix and translate, yo :: TODO
        self.n = pm.api.MMatrix()
        self.m = self.n.setToProduct(self.m, self.m)
        self.t = pm.api.MTransformationMatrix()
        self.t.setTranslation(pm.datatypes.Vector(1,2,3), pm.api.MSpace.kWorld)
        self.m = pm.datatypes.Matrix(self.t)
        self.assertEqual(self.m.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [1.0, 2.0, 3.0, 1.0]]')

        self.m = pm.datatypes.Matrix(self.m, a30=10)
        self.assertEqual(self.m.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [10.0, 2.0, 3.0, 1.0]]')


    def testMatrix_Trimmed(self):
        self.m = pm.datatypes.Matrix.identity
        self.M = self.m.trimmed(shape=(3, 3))
        self.assertEqual(self.M.formated(),'[[1.0, 0.0, 0.0],\n [0.0, 1.0, 0.0],\n [0.0, 0.0, 1.0]]') # TODO goto the docs, tool

    def testMatrix_issingular(self):
        self.M = pm.datatypes.Matrix.identity
        self.M = self.m.trimmed(shape=(3,3))
        self.assertEqual(self.M, pm.datatypes.MatrixN([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]))

        def Matrix_badTrim_Test():
            self.m.trim(shape=(3,3)) # TODO should fail
        self.assertRaises(TypeError, Matrix_badTrim_Test) # new shape (3, 3) should not be compatible with class Matrix

    def testMatrix_columnAccess(self):
        self.m = pm.datatypes.Matrix.identity
        self.assertEqual(self.m.ncol, 4)

        def Matrix_badRow():
            self.m.nrow = 3
        self.assertRaises(TypeError, Matrix_badRow)

    def testMatrix_rowAccess(self):
        self.assertEqual(self.m.nrow, 4)

# for i in range(0,4):print m.col[i]

    def testMatrix_list(self):
        self.assertEqual(list(self.m.row), [pm.datatypes.Array([1.0, 0.0, 0.0, 0.0]), pm.datatypes.Array([0.0, 1.0, 0.0, 0.0]), pm.datatypes.Array([0.0, 0.0, 1.0, 0.0]), pm.datatypes.Array([0.0, 0.0, 0.0, 1.0])] )

        self.assertEqual(list(self.m.col), [pm.datatypes.Array([1.0, 0.0, 0.0, 0.0]), pm.datatypes.Array([0.0, 1.0, 0.0, 0.0]), pm.datatypes.Array([0.0, 0.0, 1.0, 0.0]), pm.datatypes.Array([0.0, 0.0, 0.0, 1.0])] )

    def testMMatrix_fromTrimmedMatrixN(self):
        self.m  = pm.datatypes.Matrix(pm.datatypes.MatrixN(list(range(9)), shape=(3,3)).trimmed(shape=(4,4), value=10))
        self.assertEqual(self.m.formated(), '[[0.0, 1.0, 2.0, 10.0],\n [3.0, 4.0, 5.0, 10.0],\n [6.0, 7.0, 8.0, 10.0],\n [10.0, 10.0, 10.0, 10.0]]')

    def testMMatrix_getAccess(self):
        self.m = pm.datatypes.Matrix(pm.datatypes.MatrixN(list(range(9)), shape=(3,3)).trimmed(shape=(4,4), value=10))
        self.assertEqual(self.m.get(), ((0.0, 1.0, 2.0, 10.0), (3.0, 4.0, 5.0, 10.0), (6.0, 7.0, 8.0, 10.0), (10.0, 10.0, 10.0, 10.0)))

    def testMMatrix_indexAccess(self):
        self.m = pm.datatypes.Matrix(pm.datatypes.MatrixN(list(range(9)), shape=(3,3)).trimmed(shape=(4,4), value=10))
        self.assertEqual(self.m[0], pm.datatypes.Array([0.0, 1.0, 2.0, 10.0]))

        self.m[0] = 10
        self.assertEqual(self.m.formated(), '[[10.0, 10.0, 10.0, 10.0],\n [3.0, 4.0, 5.0, 10.0],\n [6.0, 7.0, 8.0, 10.0],\n [10.0, 10.0, 10.0, 10.0]]')

        # list
        self.assertTrue(10 in self.m)
        self.assertEqual(list(self.m), [pm.datatypes.Array([10.0, 10.0, 10.0, 10.0]), pm.datatypes.Array([3.0, 4.0, 5.0, 10.0]), pm.datatypes.Array([6.0, 7.0, 8.0, 10.0]), pm.datatypes.Array([10.0, 10.0, 10.0, 10.0])])

        # list flat
        self.assertEqual(list(self.m.flat), [10.0, 10.0, 10.0, 10.0, 3.0, 4.0, 5.0, 10.0, 6.0, 7.0, 8.0, 10.0, 10.0, 10.0, 10.0, 10.0])

    def testMMatrix_AxisAccess(self):
        self.u = pm.datatypes.Vector.xAxis
        self.v = pm.datatypes.Vector.yAxis
        self.assertEqual(self.v, pm.datatypes.Vector.yAxis)
        self.assertEqual(self.u, pm.datatypes.Vector.xAxis)

    def testMMatrix_rounded(self):
        ## TODO round(m, 2) returns
            #Traceback (most recent call last):
            #  File "<stdin>", line 1, in <module>
            #  File "/Volumes/luma/_globalSoft/python/thirdParty/pymel/util/mathutils.py", line 43, in round
            #    return _round(value, ndigits)
            #TypeError: a float is required

        # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
        #self.m = datatypes.Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
        #(round(self.m, 2).formated(),'[[0.0, 0.0, -0.5, 0.0],\n [0.26, 0.97, 0.0, 0.0],\n [1.93, -0.52, 0.0, 0.0],\n [1.0, 2.0, 3.0, 1.0]]' )
        pass

    def testMMatrix_operations(self):
        self.m = pm.datatypes.Matrix([[0.0, 4.16333634234e-17, -0.5, 0.0], [0.258819045103, 0.965925826289, 1.38777878078e-16, 0.0], [1.93185165258, -0.517638090205, 0.0, 0.0], [1.0, 2.0, 3.0, 1.0]])
        self.x = pm.datatypes.Vector.xAxis
        self.y = pm.datatypes.Vector.yAxis
        self.z = pm.datatypes.Vector.zAxis
        self.u = pm.datatypes.Vector(1, 2, 3)

        # start check
        self.assertEqual(self.u, pm.datatypes.Vector([1, 2, 3]))

        # multiply Matrix by Vector
        first = self.u * self.m
        last = pm.datatypes.Vector([6.31319304795, 0.378937381963, -0.5])
        self.assertTrue(first.isEquivalent(last))

        first = self.m * self.u
        last = pm.datatypes.Vector([-1.5, 2.19067069768, 0.896575472168])
        self.assertTrue(first.isEquivalent(last))

        #  multiply Matrix by Point
        self.p = pm.datatypes.Point(1,10,100,1)

        first = self.p * self.m
        last = pm.datatypes.Point([196.773355709, -40.1045507576, 2.5, 1.0])
        self.assertTrue(first.isEquivalent(last))

        first = self.m * self.p
        last = pm.datatypes.Point([-50.0, 9.91807730799, -3.24452924947, 321.0])
        self.assertTrue(first.isEquivalent(last))

        # multiplication by datatypes.VectorN:3
        first = pm.datatypes.VectorN([1, 2, 3])* self.m
        last = pm.datatypes.VectorN([6.31319304795, 0.378937381963, -0.5])
        #self.assertTrue(self.v.isEquivalent(last)) # AssertionError
        #self.assertEqual(first, last) # AssertionError: VectorN([6.31319304795, 0.378937381963, -0.5]) != VectorN([6.31319304795, 0.378937381963, -0.5])

        fd = first.data
        ld = last.data
        for i in range(0,2): # used assertAlmostEquals since we were getting some rounding errors for the list items after the eighth decimal
            self.assertAlmostEquals(fd[i], ld[i])

        # multiplication by datatypes.VectorN:5 Should fail, because
        # datatypes.Vector:5 and matrix:shape(4,4) are not able to conform for a 'VectorN * MatrixN' multiplication
        def VectorN_test():
            self.v = pm.datatypes.VectorN([1, 2, 3, 4, 5])* self.m
        self.assertRaises(ValueError, VectorN_test)

        # element wise multiplication
        self.m = pm.datatypes.Matrix(list(range(1, 17)))
        self.assertEqual(self.m.formated(), '[[1.0, 2.0, 3.0, 4.0],\n [5.0, 6.0, 7.0, 8.0],\n [9.0, 10.0, 11.0, 12.0],\n [13.0, 14.0, 15.0, 16.0]]')
        self.assertEqual(([1, 10, 100] * self.m), pm.datatypes.Matrix([[1.0, 20.0, 300.0, 0.0], [5.0, 60.0, 700.0, 0.0], [9.0, 100.0, 1100.0, 0.0], [13.0, 140.0, 1500.0, 0.0]]) )

        self.M = pm.datatypes.MatrixN(list(range(1, 21)), shape=(4, 5))
        self.assertEqual(self.M.formated(), '[[1, 2, 3, 4, 5],\n [6, 7, 8, 9, 10],\n [11, 12, 13, 14, 15],\n [16, 17, 18, 19, 20]]')

        self.n = self.m * self.M
        self.assertEqual(self.n.formated(),'[[110.0, 120.0, 130.0, 140.0, 150.0],\n [246.0, 272.0, 298.0, 324.0, 350.0],\n [382.0, 424.0, 466.0, 508.0, 550.0],\n [518.0, 576.0, 634.0, 692.0, 750.0]]')

        # check class name
        self.assertEqual(pm.util.clsname(self.n), 'MatrixN')

        # multiply by integer - should return a Matrix
        self.n = (self.m * 2)
        self.assertEqual(self.n.formated(), '[[2.0, 4.0, 6.0, 8.0],\n [10.0, 12.0, 14.0, 16.0],\n [18.0, 20.0, 22.0, 24.0],\n [26.0, 28.0, 30.0, 32.0]]')
        # and then double-check class
        self.assertEqual(pm.util.clsname(self.n), 'Matrix')

        # multiply integer by matrix - should return a Matrix
        self.n = (2 * self.m)
        self.assertEqual(self.n.formated(), '[[2.0, 4.0, 6.0, 8.0],\n [10.0, 12.0, 14.0, 16.0],\n [18.0, 20.0, 22.0, 24.0],\n [26.0, 28.0, 30.0, 32.0]]')
        self.assertEqual(pm.util.clsname(self.n), 'Matrix')

        # add matrix to integer - should return a Matrix
        self.n = self.m + 2
        self.assertEqual(self.n.formated(),'[[3.0, 4.0, 5.0, 6.0],\n [7.0, 8.0, 9.0, 10.0],\n [11.0, 12.0, 13.0, 14.0],\n [15.0, 16.0, 17.0, 18.0]]')
        self.assertEqual(pm.util.clsname(self.n), 'Matrix')

         # add integer to matrix
        self.n = 2 + self.m
        self.assertEqual(self.n.formated(),'[[3.0, 4.0, 5.0, 6.0],\n [7.0, 8.0, 9.0, 10.0],\n [11.0, 12.0, 13.0, 14.0],\n [15.0, 16.0, 17.0, 18.0]]')
        self.assertEqual(pm.util.clsname(self.n), 'Matrix')

        def setToProduct_test():
            self.m.setToProduct(self.m, self.M)
        # cannot initialize a Matrix of shape (4, 4) from shape (4, 5) - truncation errors
        self.assertRaises(TypeError, setToProduct_test)

        # isEquivalent() should evaluate as false
        self.assertFalse(self.m.isEquivalent(self.m * self.M))

        # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
        self.m = pm.datatypes.Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])

        # round() matrix values # TODO round from chad
        #self.assertEqual(round(self.m, 2).formated(), '[[0.0, 0.0, -0.5, 0.0],\n [0.26, 0.97, 0.0, 0.0],\n [1.93, -0.52, 0.0, 0.0],\n [1.0, 2.0, 3.0, 1.0]]')

        # round() the transposed() the matrix # TODO round from chad
        #self.assertEqual(round(self.m.transpose(),2).formated(), '[[0.0, 0.26, 1.93, 1.0],\n [0.0, 0.97, -0.52, 2.0],\n [-0.5, 0.0, 0.0, 3.0],\n [0.0, 0.0, 0.0, 1.0]]')

        # issingular() - make sure (not) no inverse - yay, assertFalse!
        self.assertFalse(self.m.isSingular())

        # so lets check that inverse matrix# TODO round from chad
        #self.assertEqual(round(self.m.inverse(),2).formated(), '[[0.0, 0.26, 0.48, 0.0],\n [0.0, 0.97, -0.13, 0.0],\n [-2.0, 0.0, 0.0, 0.0],\n [6.0, -2.19, -0.22, 1.0]]')

        # adjoint() - should be the same as the inverse, as they are *almost the same thing # TODO round from chad
        #self.assertEqual(round(self.m.adjoint(),2).formated(), '[[0.0, 0.26, 0.48, 0.0],\n [0.0, 0.97, -0.13, 0.0],\n [-2.0, 0.0, -0.0, 0.0],\n [6.0, -2.19, -0.22, 1.0]]')

        # adjugate() - should be identical to the adoint matrix# TODO round from chad
        #self.assertEqual(round(self.m.adjugate(),2).formated(), '[[0.0, 0.26, 0.48, 0.0],\n [0.0, 0.97, -0.13, 0.0],\n [-2.0, 0.0, -0.0, 0.0],\n [6.0, -2.19, -0.22, 1.0]]')

        # homogenize()# TODO round from chad
        #self.assertEqual(round(self.m.homogenize(),2).formated(), '[[0.0, 0.0, -1.0, 0.0],\n [0.26, 0.97, 0.0, 0.0],\n [0.97, -0.26, -0.0, 0.0],\n [1.0, 2.0, 3.0, 1.0]]')

        # determinant()
        self.assertEqual(self.m.det(), 1.0)

        # determinant for this matrix:4x4
        self.assertEqual(self.m.det4x4(), 1.0)

        # determinant of the upper left 3x3 submatrix of this matrix instance
        self.assertEqual(self.m.det3x3(), 1.0)

        # TODO round from chad
        #self.assertEqual(round(m.weighted(0.5),2).formated(), '[[0.53, 0.0, -0.53, 0.0],\n [0.09, 0.99, 0.09, 0.0],\n [1.05, -0.2, 1.05, 0.0],\n [0.5, 1.0, 1.5, 1.0]]')

        # blend() # TODO round from chad
        #self.assertEqual(round(m.blend(Matrix.identity, 0.5),2).formated(), '[[0.53, 0.0, -0.53, 0.0],\n [0.09, 0.99, 0.09, 0.0],\n [1.05, -0.2, 1.05, 0.0],\n [0.5, 1.0, 1.5, 1.0]]')


##################################################################
## MTransformationMatrix tests


    def testMTransformationMatrix_QuatInstance(self) :
        q = pm.datatypes.Quaternion()
        self.assertEqual(q, pm.datatypes.Quaternion([0.0, 0.0, 0.0, 1.0]))

        q = pm.datatypes.Quaternion(1, 2, 3, 0.5)
        last = pm.datatypes.Quaternion([1.0, 2.0, 3.0, 0.5])
        self.assertTrue(q.isEquivalent(last))

        q = pm.datatypes.Quaternion(0.785, 0.785, 0.785, "XYZ", unit='radians')
        last = pm.datatypes.Quaternion([0.191357439088, 0.461717715523, 0.191357439088, 0.844737481223])
        self.assertTrue(q.isEquivalent(last))

    def testMTransformationMatrix_rotate(self):
        self.m = pm.datatypes.Matrix()
        self.q = pm.datatypes.Quaternion(1, 2, 3, 0.5)
        self.m.rotate = self.q
        last = pm.datatypes.Matrix([[-0.824561403509, 0.491228070175, 0.280701754386, 0.0], [0.0701754385965, -0.40350877193, 0.912280701754, 0.0], [0.561403508772, 0.771929824561, 0.298245614035, 0.0], [0.0, 0.0, 0.0, 1.0]])
        self.assertTrue(self.m.isEquivalent(last))

        self.t = pm.datatypes.Matrix()
        self.q = pm.datatypes.Quaternion(1, 2, 3, 0.5)
        self.t.rotate = self.q
        last = pm.datatypes.Matrix([[-0.824561403509, 0.491228070175, 0.280701754386, 0.0], [0.0701754385965, -0.40350877193, 0.912280701754, 0.0], [0.561403508772, 0.771929824561, 0.298245614035, 0.0], [0.0, 0.0, 0.0, 1.0]])
        self.assertTrue(self.t.isEquivalent(last))

    def testMTransformationMatrix_rotation(self):
        tm = pm.datatypes.TransformationMatrix()
        self.assertEqual(tm.getRotation(), pm.datatypes.EulerRotation(0,0,0) )
        tm.setRotation(90,0,0, 'XYZ')
        last = pm.datatypes.Matrix([[1,0,0,0], [0,0,1,0], [0,-1,0,0], [0,0,0,1]])
        self.assertTrue(tm.isEquivalent(last))
        self.assertEqual(tm.getRotation(), pm.datatypes.EulerRotation(90,0,0, 'XYZ'))
        tm.setRotation(10,20,30, 'XYZ')
        last = pm.dt.Matrix([[0.81379768134937369, 0.46984631039295421, -0.34202014332566871, 0.0,],
                   [-0.44096961052988248, 0.8825641192593856, 0.16317591116653482, 0.0,],
                   [0.37852230636979256, 0.018028311236297268, 0.92541657839832336, 0.0,],
                   [0.0, 0.0, 0.0, 1.0]])
        self.assertTrue(tm.isEquivalent(last))
        tm.setRotation(10,20,30, 'YZX')
        last = pm.dt.Matrix([0.81379768134937369,
                         0.52209946381304628,
                         -0.25523613325019773,
                         0.0,
                         -0.49999999999999994,
                         0.85286853195244317,
                         0.15038373318043533,
                         0.0,
                         0.29619813272602386,
                         0.0052361332501977423,
                         0.95511216570526569,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         1.0])
        self.assertTrue(tm.isEquivalent(last))
        tm.setRotation(10,20,30, 'ZYX')
        last = pm.dt.Matrix([0.81379768134937369,
                         0.54383814248232565,
                         -0.2048741287028622,
                         0.0,
                         -0.46984631039295427,
                         0.82317294464550095,
                         0.31879577759716787,
                         0.0,
                         0.34202014332566871,
                         -0.16317591116653482,
                         0.92541657839832336,
                         0.0,
                         0.0,
                         0.0,
                         0.0,
                         1.0])
        self.assertTrue(tm.isEquivalent(last))

    def testMTransformationMatrix_rotateTo(self):
        self.t = pm.datatypes.TransformationMatrix()
        self.t.rotateTo([1, 2, 3, 0.5])
        last = pm.datatypes.Matrix([[-0.824561403509, 0.491228070175, 0.280701754386, 0.0], [0.0701754385965, -0.40350877193, 0.912280701754, 0.0], [0.561403508772, 0.771929824561, 0.298245614035, 0.0], [0.0, 0.0, 0.0, 1.0]])
        self.assertTrue(self.t.isEquivalent(last))

    def testMTransformationMatrix_formatted(self):
        self.m = pm.datatypes.TransformationMatrix()
        self.assertEqual(self.m.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

    def testMTransformationMatrix_indiceAccess(self):
        self.m = pm.datatypes.TransformationMatrix()
        self.assertEqual(self.m[0, 0], 1.0)
        self.assertEqual(self.m[0:2, 0:3], pm.datatypes.MatrixN([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))

    def testMTransformationMatrix_instanceEquality(self):
        self.m = pm.datatypes.TransformationMatrix()
        self.assertEqual(pm.datatypes.TransformationMatrix.shape, self.m.shape)
        self.assertEqual(pm.datatypes.TransformationMatrix.ndim, self.m.ndim)
        self.assertEqual(pm.datatypes.TransformationMatrix.size, self.m.size)

    def testMTransformationMatrix_inheritance(self):
        self.m = pm.datatypes.TransformationMatrix.identity
        self.assertTrue(isinstance(self.m, pm.datatypes.MatrixN))
        self.assertTrue(isinstance(self.m, pm.datatypes.Array)) # inherits from MatrixN --> Array

    def testMTransformationMatrix_API_instances(self):
        # as well as api.TransformationMatrix and api.Matrix
        self.m = pm.datatypes.TransformationMatrix.identity
        self.assertTrue(isinstance(self.m, pm.api.MTransformationMatrix))
        self.assertTrue(isinstance(self.m, pm.api.MMatrix))

    def testMTransformationMatrix_isEquivalent(self):
        self.n = pm.datatypes.TransformationMatrix.identity
        self.m = pm.datatypes.TransformationMatrix.identity

        self.assertTrue(self.m.isEquivalent(self.n))

        # Should Fail TODO :: does not currently fail
        def setShape_test1():
            self.m.shape = (4,4)
        def setShape_test2():
            self.m.shape = 2
        # these currently don't error out the way they should. TODO
        self.assertRaises(TypeError, setShape_test1())
        self.assertRaises(TypeError, setShape_test2())

        # setToProduct # TODO :: File "<stdin>", line 1, in <module> TypeError: in method 'MMatrix_setToProduct', argument 2 of type 'MMatrix const &'
        self.n = pm.api.MMatrix()
        #self.n = self.n.setToProduct(self.m, self.m)
        #self.assertTrue("<maya.OpenMaya.MMatrix; proxy of <Swig Object of type 'MMatrix *" in repr(self.n))

        # assign
        self.n = pm.api.MTransformationMatrix()
        self.n = self.n.assign(self.m)
        self.assertTrue("<maya.OpenMaya.MTransformationMatrix; proxy of <Swig Object of type 'MTransformationMatrix *" in repr(self.n))

        # rotation
        self.m = pm.datatypes.TransformationMatrix.identity
        self.m.rotation = pm.datatypes.Quaternion()
        self.assertEqual(self.m.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

        # translations
        self.n = pm.datatypes.TransformationMatrix.identity
        self.n.translation = pm.datatypes.Vector(1, 2, 3)
        self.assertEqual(self.n.formated(), '[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

        # identity multiplied by identity
        self.o = self.m * self.n
        self.assertEqual(self.o.formated(),'[[1.0, 0.0, 0.0, 0.0],\n [0.0, 1.0, 0.0, 0.0],\n [0.0, 0.0, 1.0, 0.0],\n [0.0, 0.0, 0.0, 1.0]]')

    def test_constants(self):
        # TODO : come up with a programatic way of finding constants
        s = """
        Vector.xAxis
        Vector.one
        Vector.zero
        Vector.yNegAxis
        Vector.zNegAxis
        Vector.xNegAxis
        Vector.zAxis
        Vector.yAxis
        FloatVector.xAxis
        FloatVector.one
        FloatVector.zero
        FloatVector.yNegAxis
        FloatVector.zNegAxis
        FloatVector.xNegAxis
        FloatVector.zAxis
        FloatVector.yAxis
        Point.origin
        Point.xAxis
        Point.yNegAxis
        Point.zero
        Point.zNegAxis
        Point.yAxis
        Point.zAxis
        Point.one
        Point.xNegAxis
        FloatPoint.origin
        FloatPoint.yNegAxis
        FloatPoint.yAxis
        FloatPoint.zNegAxis
        FloatPoint.xNegAxis
        FloatPoint.zAxis
        FloatPoint.xAxis
        FloatPoint.one
        FloatPoint.zero
        Color.xAxis
        Color.yNegAxis
        Color.zero
        Color.zNegAxis
        Color.yAxis
        Color.zAxis
        Color.one
        Color.xNegAxis
        FloatMatrix.identity
        TransformationMatrix.identity
        EulerRotation.identity
        Quaternion.identity
        """

        for x in s.split('\n'):
            x = x.strip()
            if x:
                c, at = x.split('.')
                val  = getattr( getattr( pm.datatypes, c ), at )


class test_Quaternion(unittest.TestCase):
    def testQuaternion_init_identity(self):
        mIdentity = om.MQuaternion()
        identity = pm.dt.Quaternion()
        self.assertEqual(identity, pm.dt.Quaternion(0, 0, 0, 1))
        self.assertEqual(identity, pm.dt.Quaternion(0, 0, 0, 1))
        self.assertEqual(identity, mIdentity)
        self.assertNotEqual(identity, om.MQuaternion(1,2,3,1))

    def testQuaternion_init_4floats(self):
        m1231float = om.MQuaternion(1.1, 2.2, 3.3, 1.0)
        quat = pm.dt.Quaternion(1.1, 2.2, 3.3, 1.0)
        self.assertEqual(quat, pm.dt.Quaternion(1.1, 2.2, 3.3, 1.0))
        self.assertEqual(quat, m1231float)
        self.assertNotEqual(quat, pm.dt.Quaternion())

    def testQuaternion_init_4ints(self):
        m1231int = om.MQuaternion(1, 2, 3, 1)
        quat = pm.dt.Quaternion(1, 2, 3, 1)
        self.assertEqual(quat, pm.dt.Quaternion(1, 2, 3, 1))
        self.assertEqual(quat, m1231int)

    def testQuaternion_init_otherQuat(self):
        m1231int = om.MQuaternion(1, 2, 3, 1)
        origQuat = pm.dt.Quaternion(1, 2, 3, 1)
        quat = pm.dt.Quaternion(origQuat)
        self.assertEqual(quat, origQuat)
        self.assertEqual(quat, m1231int)

    def testQuaternion_init_otherMQuat(self):
        m1231int = om.MQuaternion(1, 2, 3, 1)
        quat = pm.dt.Quaternion(m1231int)
        self.assertEqual(quat, m1231int)

    def testQuaternion_init_rotateVecToVec(self):
        m100to123 = om.MQuaternion(om.MVector(1,0,0), om.MVector(1,2,3))
        quat = pm.dt.Quaternion(pm.dt.Vector(1,0,0), pm.dt.Vector(1,2,3))
        self.assertEqual(quat, m100to123)

        quat = pm.dt.Quaternion(om.MVector(1,0,0), om.MVector(1,2,3))
        self.assertEqual(quat, m100to123)

        quat = pm.dt.Quaternion((1,0,0), (1,2,3))
        self.assertEqual(quat, m100to123)

        quat = pm.dt.Quaternion([1,0,0], [1,2,3])
        self.assertEqual(quat, m100to123)

        quat = pm.dt.Quaternion((1,0,0), [1,2,3])
        self.assertEqual(quat, m100to123)

        quat = pm.dt.Quaternion(pm.dt.Vector(1,0,0), [1,2,3])
        self.assertEqual(quat, m100to123)

    def testQuaternion_init_rotateVecToVec_factor(self):
        m100to123_25 = om.MQuaternion(om.MVector(1,0,0), om.MVector(1,2,3), .25)
        quat = pm.dt.Quaternion(pm.dt.Vector(1,0,0), pm.dt.Vector(1,2,3), .25)
        self.assertEqual(quat, m100to123_25)

        quat = pm.dt.Quaternion(om.MVector(1,0,0), om.MVector(1,2,3), .25)
        self.assertEqual(quat, m100to123_25)

        quat = pm.dt.Quaternion((1,0,0), (1,2,3), .25)
        self.assertEqual(quat, m100to123_25)

        quat = pm.dt.Quaternion([1,0,0], [1,2,3], .25)
        self.assertEqual(quat, m100to123_25)

        quat = pm.dt.Quaternion((1,0,0), om.MVector(1,2,3), .25)
        self.assertEqual(quat, m100to123_25)

        quat = pm.dt.Quaternion([1,0,0], (1,2,3), .25)
        self.assertEqual(quat, m100to123_25)

    def testQuaternion_init_axisAngle(self):
        m32x = om.MQuaternion(32, om.MVector(1,0,0))
        quat = pm.dt.Quaternion(pm.dt.Vector(1, 0, 0), 32.0)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(pm.dt.Vector(1, 0, 0), 32)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32.0, pm.dt.Vector(1, 0, 0))
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32, pm.dt.Vector(1, 0, 0))
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion((1, 0, 0), 32.0)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion((1, 0, 0), 32)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32.0, (1, 0, 0))
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32, (1, 0, 0))
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion([1, 0, 0], 32.0)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion([1, 0, 0], 32)
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32.0, [1, 0, 0])
        self.assertEqual(quat, m32x)

        quat = pm.dt.Quaternion(32, [1, 0, 0])
        self.assertEqual(quat, m32x)


class test_Units(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pm.newFile(f=1)
        cls.transform = pm.createNode('transform', name='testTrans')
        cls.time = pm.createNode('time', name='testTime')
        cls.linearUnit = cmds.currentUnit(query=True, linear=True)
        cls.angleUnit = cmds.currentUnit(query=True, angle=True)
        cls.timeUnit = cmds.currentUnit(query=True, time=True)

    @classmethod
    def tearDownClass(cls):
        pm.newFile(f=1)
        cmds.currentUnit(linear=cls.linearUnit)
        cmds.currentUnit(angle=cls.angleUnit)
        cmds.currentUnit(time=cls.timeUnit)

    def testDistancePlug(self):
        pm.dt.Distance.setUIUnit('centimeters')
        self.assertEqual(pm.dt.Distance.getUIUnit(), 'centimeters')

        tx = self.transform.attr('tx')
        tx.set(10)

        self.assertEqual(tx.get(), 10)
        txDist = pm.dt.getPlugValue(tx.__apimplug__())
        self.assertIsInstance(txDist, pm.dt.Distance)
        self.assertEqual(txDist.unit, 'centimeters')
        self.assertEqual(float(txDist), 10)

        pm.dt.Distance.setUIUnit('meters')
        self.assertEqual(pm.dt.Distance.getUIUnit(), 'meters')

        self.assertEqual(tx.get(), .1)
        txDist = pm.dt.getPlugValue(tx.__apimplug__())
        self.assertIsInstance(txDist, pm.dt.Distance)
        self.assertEqual(txDist.unit, 'meters')
        self.assertEqual(float(txDist), .1)

    def testAnglePlug(self):
        from math import pi
        pm.dt.Angle.setUIUnit('degrees')
        self.assertEqual(pm.dt.Angle.getUIUnit(), 'degrees')

        rx = self.transform.attr('rx')
        rx.set(90)

        self.assertEqual(rx.get(), 90)
        rxAngle = pm.dt.getPlugValue(rx.__apimplug__())
        self.assertIsInstance(rxAngle, pm.dt.Angle)
        self.assertEqual(rxAngle.unit, 'degrees')
        self.assertEqual(float(rxAngle), 90)

        pm.dt.Angle.setUIUnit('radians')
        self.assertEqual(pm.dt.Angle.getUIUnit(), 'radians')

        self.assertAlmostEqual(rx.get(), pi / 2)
        rxAngle = pm.dt.getPlugValue(rx.__apimplug__())
        self.assertIsInstance(rxAngle, pm.dt.Angle)
        self.assertEqual(rxAngle.unit, 'radians')
        self.assertAlmostEqual(float(rxAngle), pi / 2)

    def testTimePlug(self):
        pm.dt.Time.setUIUnit('film')
        self.assertEqual(pm.dt.Time.getUIUnit(), 'film')

        out = self.time.attr('outTime')
        out.set(24)

        self.assertEqual(out.get(), 24)
        outTime = pm.dt.getPlugValue(out.__apimplug__())
        self.assertIsInstance(outTime, pm.dt.Time)
        self.assertEqual(outTime.unit, 'film')
        self.assertEqual(float(outTime), 24)

        pm.dt.Time.setUIUnit('k48FPS')
        self.assertEqual(pm.dt.Time.getUIUnit(), 'k48FPS')

        self.assertEqual(out.get(), 48)
        outTime = pm.dt.getPlugValue(out.__apimplug__())
        self.assertIsInstance(outTime, pm.dt.Time)
        self.assertEqual(outTime.unit, 'k48FPS')
        self.assertEqual(float(outTime), 48)




def _testMVector():

    print("Vector class:", dir(Vector))
    u = Vector()
    print(u)
    print("Vector instance:", dir(u))
    print(repr(u))
    print(Vector.__readonly__)
    print(Vector.__slots__)
    print(Vector.shape)
    print(Vector.ndim)
    print(Vector.size)
    print(u.shape)
    print(u.ndim)
    print(u.size)
    # should fail
    u.shape = 2

    u.assign(Vector(4, 5, 6))
    print(repr(u))
    #Vector([4.0, 5.0, 6.0])
    u = Vector(1, 2, 3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    print(len(u))
    # 3
    # inherits from VectorN --> Array
    print(isinstance(u, VectorN))
    # True
    print(isinstance(u, Array))
    # True
    # as well as _api.Vector
    print(isinstance(u, _api.MVector))
    # True
    # accepted directly by API methods
    M = _api.MTransformationMatrix()
    M.setTranslation(u, _api.MSpace.kWorld)
    # need conversion on the way back though
    u = Vector(M.getTranslation(_api.MSpace.kWorld))
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])

    u = Vector(x=1, y=2, z=3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    u = Vector([1, 2], z=3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    u = Vector(_api.MPoint(1, 2, 3))
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    print("u = Vector(VectorN(1, 2, 3))")
    u = Vector(VectorN(1, 2, 3))
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    u = Vector(1)
    print(repr(u))
    # Vector([1.0, 1.0, 1.0])
    u = Vector(1, 2)
    print(repr(u))
    # Vector([1.0, 2.0, 0.0])
    u = Vector(VectorN(1, shape=(2,)))
    print(repr(u))
    # Vector([1.0, 1.0, 0.0])
    u = Vector(Point(1, 2, 3))
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    u = Vector(Point(1, 2, 3, 1), y=20, z=30)
    print(repr(u))
    # Vector([1.0, 20.0, 30.0])
    # should fail
    print("Vector(VectorN(1, 2, 3, 4))")
    try:
        u = Vector(VectorN(1, 2, 3, 4))
    except:
        print("will raise ValueError: could not cast [1, 2, 3, 4] to Vector of size 3, some data would be lost")

    print(u.get())
    # (1.0, 20.0, 30.0)
    print(u[0])
    1.0
    u[0] = 10
    print(repr(u))
    # Vector([10.0, 20.0, 30.0])
    print((10 in u))
    # True
    print(list(u))
    # [10.0, 20.0, 30.0]

    u = Vector.xAxis
    v = Vector.yAxis
    print(Vector.xAxis)
    print(str(Vector.xAxis))
    print(str(Vector.xAxis))
    print(repr(Vector.xAxis))

    print("u = Vector.xAxis:")
    print(repr(u))
    # Vector([1.0, 0.0, 0.0])
    print("v = Vector.yAxis:")
    print(repr(v))
    # Vector([0.0, 1.0, 0.0])
    n = u ^ v
    print("n = u ^ v:")
    print(repr(n))
    # Vector([0.0, 0.0, 1.0])
    print("n.x=%s, n.y=%s, n.z=%s" % (n.x, n.y, n.z))
    # n.x=0.0, n.y=0.0, n.z=1.0
    n = u ^ VectorN(v)
    print("n = u ^ VectorN(v):")
    print(repr(n))
    # Vector([0.0, 0.0, 1.0])
    n = u ^ [0, 1, 0]
    print("n = u ^ [0, 1, 0]:")
    print(repr(n))
    # Vector([0.0, 0.0, 1.0])
    n[0:2] = [1, 1]
    print("n[0:2] = [1, 1]:")
    print(repr(n))
    # Vector([1.0, 1.0, 1.0])
    print("n = n * 2 :")
    n = n * 2
    print(repr(n))
    # Vector([2.0, 2.0, 2.0])
    print("n = n * [0.5, 1.0, 2.0]:")
    n = n * [0.5, 1.0, 2.0]
    print(repr(n))
    # Vector([1.0, 2.0, 4.0])
    print("n * n :")
    print(n * n)
    # 21.0
    print(repr(n.clamp(1.0, 2.0)))
    # Vector([1.0, 2.0, 2.0])
    print(repr(-n))
    # Vector([-1.0, -2.0, -4.0])
    w = u + v
    print(repr(w))
    # Vector([1.0, 1.0, 0.0])
    p = Point(1, 2, 3)
    q = u + p
    print(repr(q))
    # Point([2.0, 2.0, 3.0, 1.0])
    q = p + u
    print(repr(q))
    # Point([2.0, 2.0, 3.0, 1.0])
    print(repr(p + q))
    # Point([3.0, 4.0, 6.0, 1.0])
    w = u + VectorN(1, 2, 3, 4)
    print(repr(w))
    # VectorN([2.0, 2.0, 3.0, 4])
    print(repr(u + 2))
    # Vector([3.0, 2.0, 2.0])
    print(repr(2 + u))
    # Vector([3.0, 2.0, 2.0])
    print(repr(p + 2))
    # Point([3.0, 4.0, 5.0, 1.0])
    print(repr(2 + p))
    # Point([3.0, 4.0, 5.0, 1.0])
    print(repr(p + u))
    # Point([2.0, 2.0, 3.0, 1.0])
    print(repr(VectorN(1, 2, 3, 4) + u))
    # VectorN([2.0, 2.0, 3.0, 4])
    print(repr([1, 2, 3] + u))
    # Vector([2.0, 2.0, 3.0])

    u = Vector(1, 2, 3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    print(u.length())
    # 3.74165738677
    print(length(u))
    # 3.74165738677
    print(length([1, 2, 3]))
    # 3.74165738677
    print(length(VectorN(1, 2, 3)))
    # 3.74165738677
    print(VectorN(1, 2, 3).length())
    # 3.74165738677
    print(length(VectorN(1, 2, 3, 4)))
    # 5.47722557505
    print(VectorN(1, 2, 3, 4).length())
    # 5.47722557505
    print(length(1))
    # 1.0
    print(length([1, 2]))
    # 2.2360679775
    print(length([1, 2, 3]))
    # 3.74165738677
    print(length([1, 2, 3, 4]))
    # 5.47722557505
    print(length([1, 2, 3, 4], 0))
    # 5.47722557505
    print(length([1, 2, 3, 4], (0,)))
    # 5.47722557505
    print(length([[1, 2], [3, 4]], 1))
    # [3.16227766017, 4.472135955]
    # should fail
    try:
        print(length([1, 2, 3, 4], 1))
    except:
        print("Will raise ValueError, \"axis 0 is the only valid axis for a Vector, 1 invalid\"")

    u = Vector(1, 2, 3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    print(u.sqlength())
    # 14
    print(repr(u.normal()))
    # Vector([0.267261241912, 0.534522483825, 0.801783725737])
    u.normalize()
    print(repr(u))
    # Vector([0.267261241912, 0.534522483825, 0.801783725737])

    u = Vector(1, 2, 3)
    print(repr(u))
    # Vector([1.0, 2.0, 3.0])
    w = u + [0.01, 0.01, 0.01]
    print(repr(w))
    # Vector([1.01, 2.01, 3.01])
    print((u == u))
    # True
    print((u == w))
    # False
    print((u == Vector(1.0, 2.0, 3.0)))
    # True
    print((u == [1.0, 2.0, 3.0]))
    # False
    print((u == Point(1.0, 2.0, 3.0)))
    # False
    print(u.isEquivalent([1.0, 2.0, 3.0]))
    # True
    print(u.isEquivalent(Vector(1.0, 2.0, 3.0)))
    # True
    print(u.isEquivalent(Point(1.0, 2.0, 3.0)))
    # True
    print(u.isEquivalent(w))
    # False
    print(u.isEquivalent(w, 0.1))
    # True

    u = Vector(1, 0, 0)
    print(repr(u))
    # Vector([1.0, 0.0, 0.0])
    v = Vector(0.707, 0, -0.707)
    print(repr(v))
    # Vector([0.707, 0.0, -0.707])
    print(repr(axis(u, v)))
    # Vector([-0.0, 0.707, 0.0])
    print(repr(u.axis(v)))
    # Vector([-0.0, 0.707, 0.0])
    print(repr(axis(VectorN(u), VectorN(v))))
    # VectorN([-0.0, 0.707, 0.0])
    print(repr(axis(u, v, normalize=True)))
    # Vector([-0.0, 1.0, 0.0])
    print(repr(v.axis(u, normalize=True)))
    # Vector([-0.0, -1.0, 0.0])
    print(repr(axis(VectorN(u), VectorN(v), normalize=True)))
    # VectorN([-0.0, 1.0, 0.0])
    print(angle(u, v))
    # 0.785398163397
    print(v.angle(u))
    # 0.785398163397
    print(angle(VectorN(u), VectorN(v)))
    # 0.785398163397
    print(cotan(u, v))
    # 1.0
    print(repr(u.rotateTo(v)))
    # Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print(repr(u.rotateBy(u.axis(v), u.angle(v))))
    # Vector([0.707106781187, 0.0, -0.707106781187])
    q = Quaternion([-0.0, 0.382683432365, 0.0, 0.923879532511])
    print(repr(u.rotateBy(q)))
    # Vector([0.707106781187, 0.0, -0.707106781187])
    print(u.distanceTo(v))
    # 0.765309087885
    print(u.isParallel(v))
    # False
    print(u.isParallel(2 * u))
    # True
    print(repr(u.blend(v)))
    # Vector([0.8535, 0.0, -0.3535])

    print("end tests Vector")


def _testMPoint():

    print("Point class", dir(Point))
    print(hasattr(Point, 'data'))
    p = Point()
    print(repr(p))
    # Point([0.0, 0.0, 0.0])
    print("Point instance", dir(p))
    print(hasattr(p, 'data'))
    print(repr(p.data))
    # <maya.OpenMaya.Point; proxy of <Swig Object of type 'Point *' at 0x84a1270> >

    p = Point(1, 2, 3)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    v = Vector(p)
    print(repr(v))
    # Vector([1.0, 2.0, 3.0])
    V = VectorN(p)
    print(repr(V))
    # VectorN([1.0, 2.0, 3.0, 1.0])
    print(list(p))
    # [1.0, 2.0, 3.0]
    print(len(p))
    # 3
    print(p.size)
    # 4
    print(p.x, p.y, p.z, p.w)
    # 1.0 2.0 3.0 1.0
    print(p[0], p[1], p[2], p[3])
    # 1.0 2.0 3.0 1.0
    p.get()
    # 1.0 2.0 3.0 1.0

    # accepted by api
    q = _api.MPoint()
    print(q.distanceTo(p))
    # 3.74165738677

    # support for non cartesian points still there

    p = Point(1, 2, 3, 2)
    print(repr(p))
    # Point([1.0, 2.0, 3.0, 2.0])
    v = Vector(p)
    print(repr(v))
    # Vector([0.5, 1.0, 1.5])
    V = VectorN(p)
    print(repr(V))
    # VectorN([1.0, 2.0, 3.0, 2.0])
    print(list(p))
    # [1.0, 2.0, 3.0, 2.0]
    print(len(p))
    # 4
    print(p.size)
    # 4
    print(p.x, p.y, p.z, p.w)
    # 1.0 2.0 3.0 2.0
    print(p[0], p[1], p[2], p[3])
    # 1.0 2.0 3.0 2.0
    p.get()
    # 1.0 2.0 3.0 2.0

    # accepted by api
    q = _api.MPoint()
    print(q.distanceTo(p))
    # 1.87082869339

    p = Point(_api.MPoint())
    print(repr(p))
    # Point([0.0, 0.0, 0.0])
    p = Point(1)
    print(repr(p))
    # Point([1.0, 1.0, 1.0])
    p = Point(1, 2)
    print(repr(p))
    # Point([1.0, 2.0, 0.0])
    p = Point(1, 2, 3)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    p = Point(_api.MPoint(1, 2, 3))
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    p = Point(VectorN(1, 2))
    print(repr(p))
    # Point([1.0, 2.0, 0.0])
    p = Point(Vector(1, 2, 3))
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    p = Point(_api.MVector(1, 2, 3))
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    p = Point(VectorN(1, 2, 3, 4))
    print(repr(p))
    # Point([1.0, 2.0, 3.0, 4.0])
    print(repr(Vector(p)))
    # Vector([0.25, 0.5, 0.75])
    print(repr(VectorN(p)))
    # VectorN([1.0, 2.0, 3.0, 4.0])
    p = Point(p, w=1)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    print(repr(Vector(p)))
    # Vector([1.0, 2.0, 3.0])
    print(repr(VectorN(p)))
    # VectorN([1.0, 2.0, 3.0, 1.0])

    p = Point.origin
    print(repr(p))
    # Point([0.0, 0.0, 0.0])
    p = Point.xAxis
    print(repr(p))
    # Point([1.0, 0.0, 0.0])

    p = Point(1, 2, 3)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    print(repr(p + Vector([1, 2, 3])))
    # Point([2.0, 4.0, 6.0])
    print(repr(p + Point([1, 2, 3])))
    # Point([2.0, 4.0, 6.0])
    print(repr(p + [1, 2, 3]))
    # Point([2.0, 4.0, 6.0])
    print(repr(p + [1, 2, 3, 1]))
    # Point([2.0, 4.0, 6.0])
    print(repr(p + Point([1, 2, 3, 1])))
    # Point([2.0, 4.0, 6.0])
    print(repr(p + [1, 2, 3, 2]))
    # Point([2.0, 4.0, 6.0, 3.0])    TODO : convert to Point always?
    print(repr(p + Point([1, 2, 3, 2])))
    # Point([1.5, 3.0, 4.5])

    print(repr(Vector([1, 2, 3]) + p))
    # Point([2.0, 4.0, 6.0])
    print(repr(Point([1, 2, 3]) + p))
    # Point([2.0, 4.0, 6.0])
    print(repr([1, 2, 3] + p))
    # Point([2.0, 4.0, 6.0])
    print(repr([1, 2, 3, 1] + p))
    # Point([2.0, 4.0, 6.0])
    print(repr(Point([1, 2, 3, 1]) + p))
    # Point([2.0, 4.0, 6.0])
    print(repr([1, 2, 3, 2] + p))
    # Point([2.0, 4.0, 6.0, 3.0])
    print(repr(Point([1, 2, 3, 2]) + p))
    # Point([1.5, 3.0, 4.5])

    # various operation, on cartesian and non cartesian points

    print("p = Point(1, 2, 3)")
    p = Point(1, 2, 3)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    print("p/2")
    print(repr(p / 2))
    # Point([0.5, 1.0, 1.5])
    print("p*2")
    print(repr(p * 2))
    # Point([2.0, 4.0, 6.0])
    print("q = Point(0.25, 0.5, 1.0)")
    q = Point(0.25, 0.5, 1.0)
    print(repr(q))
    # Point([0.25, 0.5, 1.0])
    print(repr(q + 2))
    # Point([2.25, 2.5, 3.0])
    print(repr(q / 2))
    # Point([0.125, 0.25, 0.5])
    print(repr(p + q))
    # Point([1.25, 2.5, 4.0])
    print(repr(p - q))
    # Vector([0.75, 1.5, 2.0])
    print(repr(q - p))
    # Vector([-0.75, -1.5, -2.0])
    print(repr(p - (p - q)))
    # Point([0.25, 0.5, 1.0])
    print(repr(Vector(p) * Vector(q)))
    # 4.25
    print(repr(p * q))
    # 4.25
    print(repr(p / q))
    # Point([4.0, 4.0, 3.0])

    print("p = Point(1, 2, 3)")
    p = Point(1, 2, 3)
    print(repr(p))
    # Point([1.0, 2.0, 3.0])
    print("p/2")
    print(repr(p / 2))
    # Point([0.5, 1.0, 1.5])
    print("p*2")
    print(repr(p * 2))
    # Point([2.0, 4.0, 6.0])
    print("q = Point(0.25, 0.5, 1.0, 0.5)")
    q = Point(0.25, 0.5, 1.0, 0.5)
    print(repr(q))
    # Point([0.25, 0.5, 1.0, 0.5])
    r = q.deepcopy()
    print(repr(r))
    # Point([0.25, 0.5, 1.0, 0.5])
    print(repr(r.cartesianize()))
    # Point([0.5, 1.0, 2.0])
    print(repr(r))
    # Point([0.5, 1.0, 2.0])
    print(repr(q))
    # Point([0.25, 0.5, 1.0, 0.5])
    print(repr(q.cartesian()))
    # Point([0.5, 1.0, 2.0])
    r = q.deepcopy()
    print(repr(r))
    # Point([0.25, 0.5, 1.0, 0.5])
    print(repr(r.rationalize()))
    # Point([0.5, 1.0, 2.0, 0.5])
    print(repr(r))
    # Point([0.5, 1.0, 2.0, 0.5])
    print(repr(q.rational()))
    # Point([0.5, 1.0, 2.0, 0.5])
    r = q.deepcopy()
    print(repr(r.homogenize()))
    # Point([0.125, 0.25, 0.5, 0.5])
    print(repr(r))
    # Point([0.125, 0.25, 0.5, 0.5])
    print(repr(q.homogen()))
    # Point([0.125, 0.25, 0.5, 0.5])
    print(repr(q))
    # Point([0.25, 0.5, 1.0, 0.5])
    print(Vector(q))
    # [0.5, 1.0, 2.0]
    print(Vector(q.cartesian()))
    # [0.5, 1.0, 2.0]
    # ignore w
    print("q/2")
    print(repr(q / 2))
    # Point([0.125, 0.25, 0.5, 0.5])
    print("q*2")
    print(repr(q * 2))
    # Point([0.5, 1.0, 2.0, 0.5])
    print(repr(q + 2))             # cartesianize is done by Vector add
    # Point([2.5, 3.0, 4.0])

    print(repr(q))
    # Point([0.25, 0.5, 1.0, 0.5])
    print(repr(p + Vector(1, 2, 3)))
    # Point([2.0, 4.0, 6.0])
    print(repr(q + Vector(1, 2, 3)))
    # Point([1.5, 3.0, 5.0])
    print(repr(q.cartesian() + Vector(1, 2, 3)))
    # Point([1.5, 3.0, 5.0])

    print(repr(p - q))
    # Vector([0.5, 1.0, 1.0])
    print(repr(p - q.cartesian()))
    # Vector([0.5, 1.0, 1.0])
    print(repr(q - p))
    # Vector([-0.5, -1.0, -1.0])
    print(repr(p - (p - q)))
    # Point([0.5, 1.0, 2.0])
    print(repr(Vector(p) * Vector(q)))
    # 4.25
    print(repr(p * q))
    # 4.25
    print(repr(p / q))             # need explicit homogenize as division not handled by api
    # Point([4.0, 4.0, 3.0, 2.0])    TODO : what do we want here ?
    # Vector([2.0, 2.0, 1.5])
    # additionnal methods

    print("p = Point(x=1, y=2, z=3)")
    p = Point(x=1, y=2, z=3)
    print(p.length())
    # 3.74165738677
    print(p[:1].length())
    # 1.0
    print(p[:2].length())
    # 2.2360679775
    print(p[:3].length())
    # 3.74165738677

    p = Point(1.0, 0.0, 0.0)
    q = Point(0.707, 0.0, -0.707)
    print(repr(p))
    # Point([1.0, 0.0, 0.0, 1.0])
    print(repr(q))
    # Point([0.707, 0.0, -0.707, 1.0])
    print(repr(q - p))
    # Vector([-0.293, 0.0, -0.707])
    print(repr(axis(Point.origin, p, q)))
    # Vector([-0.0, 0.707, 0.0])
    print(repr(Point.origin.axis(p, q)))
    # Vector([-0.0, 0.707, 0.0])
    print(repr(Point.origin.axis(q, p)))
    # Vector([0.0, -0.707, 0.0])
    print(angle(Point.origin, p, q))
    # 0.785398163397
    print(angle(Point.origin, q, p))
    # 0.785398163397
    print(Point.origin.angle(p, q))
    # 0.785398163397
    print(p.distanceTo(q))
    # 0.765309087885
    print((q - p).length())
    # 0.765309087885
    print(cotan(Point.origin, p, q))
    # 1.0
    # obviously True
    print(planar(Point.origin, p, q))
    # True
    r = center(Point.origin, p, q)
    print(repr(r))
    # Point([0.569, 0.0, -0.235666666667, 1.0])
    print(planar(Point.origin, p, q, r))
    # True
    print(planar(Point.origin, p, q, r + Vector(0.0, 0.1, 0.0)))
    # False
    print(bWeights(r, Point.origin, p, q))
    # (0.33333333333333337, 0.33333333333333331, 0.33333333333333343)

    p = Point([0.33333, 0.66666, 1.333333, 0.33333])
    print(repr(round(p, 3)))
    # Point([0.333, 0.667, 1.333, 0.333])

    print("end tests Point")


def _testMColor():

    print("Color class", dir(Color))
    print(hasattr(Color, 'data'))
    c = Color()
    print(repr(c))
    # Color([0.0, 0.0, 0.0, 1.0])
    print("Color instance", dir(c))
    print(hasattr(c, 'data'))
    print(repr(c.data))
    # Color([0.0, 0.0, 0.0, 1.0])
    c = Color(_api.MColor())
    print(repr(c))
    # Color([0.0, 0.0, 0.0, 1.0])
    # using api convetion of single value would mean alpha
    # instead of VectorN convention of filling all with value
    # which would yield # Color([0.5, 0.5, 0.5, 0.5]) instead
    # This would break coerce behavior for Color
    print("c = Color(0.5)")
    c = Color(0.5)
    print(repr(c))
    # Color([0.5, 0.5, 0.5, 0.5])
    print("c = round(Color(128, quantize=255), 2)")
    c = Color(128, quantize=255)
    print(repr(c))
    # Color([0.501999974251, 0.501999974251, 0.501999974251, 0.501999974251])
    c = Color(255, 128, b=64, a=32, quantize=255)
    print(repr(c))
    # Color([1.0 0.501999974251 0.250999987125 0.125490196078])

    print("c = Color(1, 1, 1)")
    c = Color(1, 1, 1)
    print(repr(c))
    # Color([1.0, 1.0, 1.0, 1.0])
    print("c = round(Color(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)")
    c = round(Color(255, 0, 255, g=128, quantize=255, mode='rgb'), 2)
    print(repr(c))
    # Color([1.0, 0.5, 1.0, 1.0])

    print("c = round(Color(255, b=128, quantize=255, mode='rgb'), 2)")
    c = round(Color(255, b=128, quantize=255, mode='rgb'), 2)
    print(repr(c))
    # Color([1.0, 1.0, 0.5, 1.0])
    print("c = Color(1, 0.5, 2, 0.5)")
    c = Color(1, 0.5, 2, 0.5)
    print(repr(c))
    # Color([1.0, 0.5, 2.0, 0.5])
    print("c = Color(0, 65535, 65535, quantize=65535, mode='hsv')")
    c = Color(0, 65535, 65535, quantize=65535, mode='hsv')
    print(repr(c))
    # Color([1.0, 0.0, 0.0, 1.0])
    print("c.rgb")
    print(repr(c.rgb))
    # (1.0, 0.0, 0.0)
    print("c.hsv")
    print(repr(c.hsv))
    # (0.0, 1.0, 1.0)
    d = Color(c, v=0.5, mode='hsv')
    print(repr(d))
    # Color([0.5, 0.0, 0.0, 1.0])
    print(repr(d.hsv))
    # (0.0, 1.0, 0.5)
    print("c = Color(Color.blue, v=0.5)")
    c = Color(Color.blue, v=0.5)
    print(repr(c))
    # Color([0.0, 0.0, 0.5, 1.0])
    print("c.hsv")
    print(c.hsv)
    # (0.66666666666666663, 1.0, 0.5)
    c.r = 1.0
    print(repr(c))
    # Color([1.0, 0.0, 0.5, 1.0])
    print("c.hsv")
    print(c.hsv)
    # (0.91666666666666663, 1.0, 1.0)

    print("c = Color(1, 0.5, 2, 0.5).clamp()")
    c = Color(1, 0.5, 2, 0.5).clamp()
    print(repr(c))
    # Color([1.0, 0.5, 1.0, 0.5])
    print(c.hsv)
    # (0.83333333333333337, 0.5, 1.0)

    print("Color(c, v=0.5)")
    d = Color(c, v=0.5)
    print(repr(d))
    # Color([0.5, 0.25, 0.5, 0.5])
    print("d.hsv")
    print(d.hsv)
    # (0.83333333333333337, 0.5, 0.5)

    print("c = Color(0.0, 0.5, 1.0, 0.5)")
    c = Color(0.0, 0.5, 1.0, 0.5)
    print(repr(c))
    # Color(0.0, 0.5, 1.0, 0.5)
    print("d = c.gamma(2.0)")
    d = c.gamma(2.0)
    print(repr(d))
    # Color([0.0, 0.25, 1.0, 0.5])

    print("c = Color.red.blend(Color.blue, 0.5)")
    c = Color.red.blend(Color.blue, 0.5)
    print(repr(c))
    # Color([0.5, 0.0, 0.5, 1.0])
    print(c.hsv)
    # (0.83333333333333337, 1.0, 0.5)
    c = Color.red.hsvblend(Color.blue, 0.5)
    print(repr(c))
    # Color([1.0, 0.0, 1.0, 1.0])
    print(c.hsv)
    # (0.83333333333333337, 1.0, 1.0)

    print("c = Color(0.25, 0.5, 0.75, 0.5)")
    c = Color(0.25, 0.5, 0.75, 0.5)
    print(repr(c))
    # Color([0.25, 0.5, 0.75, 0.5])
    print("d = Color.black")
    d = Color.black
    print(repr(d))
    # Color([0.0, 0.0, 0.0, 1.0])
    print("c.over(d)")
    print(repr(c.over(d)))
    # Color([0.125, 0.25, 0.375, 1.0])
    print("d.over(c)")
    print(repr(d.over(c)))
    # Color([0.0, 0.0, 0.0, 0.5])
    print("c.premult()")
    print(repr(c.premult()))
    # Color([0.125, 0.25, 0.375, 1.0])

    # herited from Vector

    print("c = Color(0.25, 0.5, 1.0, 1.0)")
    c = Color(0.25, 0.5, 1.0, 1.0)
    print(repr(c))
    # Color([0.25, 0.5, 1.0, 1.0])
    print("d = Color(2.0, 1.0, 0.5, 0.25)")
    d = Color(2.0, 1.0, 0.5, 0.25)
    print(repr(d))
    # Color([2.0, 1.0, 0.5, 0.25])
    print("-c")
    print(repr(-c))
    # Color([-0.25, -0.5, -1.0, 1.0])
    print("e = c*d")
    e = c * d
    print(repr(e))
    # Color([0.5, 0.5, 0.5, 0.25])
    print("e + 2")
    print(repr(e + 2))
    # Color([2.5, 2.5, 2.5, 0.25])
    print("e * 2.0")               # mult by scalar float is defined in api for colors and also multiplies alpha
    print(repr(e * 2.0))
    # Color([1.0, 1.0, 1.0, 0.5])
    print("e / 2.0")               # as is divide, that ignores alpha now for some reason
    print(repr(e / 2.0))
    # Color([0.25, 0.25, 0.25, 0.25])
    print("e+Vector(1, 2, 3)")
    print(repr(e + Vector(1, 2, 3)))
    # Color([1.5, 2.5, 3.5, 0.25])
    # how to handle operations on colors ?
    # here behaves like api but does it make any sense
    # for colors as it is now ?
    print("c+c")
    print(repr(c + c))
    # Color([0.5, 1.0, 2.0, 1.0])
    print("c+d")
    print(repr(c + d))
    # Color([2.25, 1.5, 1.5, 1.0])
    print("d-c")
    print(repr(d - c))
    # Color([1.75, 0.5, -0.5, 0.25])

    print("end tests Color")


def _testMMatrix():

    print("Matrix class", dir(Matrix))
    m = Matrix()
    print(m.formated())
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print(m[0, 0])
    # 1.0
    print(repr(m[0:2, 0:3]))
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print(m(0, 0))
    # 1.0
    print("Matrix instance:", dir(m))
    print(Matrix.__readonly__)
    print(Matrix.__slots__)
    print(Matrix.shape)
    print(Matrix.ndim)
    print(Matrix.size)
    print(m.shape)
    print(m.ndim)
    print(m.size)
    # should fail
    m.shape = (4, 4)
    m.shape = 2

    print(dir(Space))

    m = Matrix.identity
    # inherits from MatrixN --> Array
    print(isinstance(m, MatrixN))
    # True
    print(isinstance(m, Array))
    # True
    # as well as _api.Matrix
    print(isinstance(m, _api.MMatrix))
    # True
    # accepted directly by API methods
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print(repr(m))
    print(repr(n))

    # inits
    m = Matrix(list(range(16)))
    print(m.formated())
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]
    M = Array(list(range(16)), shape=(8, 2))
    m = Matrix(M)
    print(m.formated())
    #[[0.0, 1.0, 2.0, 3.0],
    # [4.0, 5.0, 6.0, 7.0],
    # [8.0, 9.0, 10.0, 11.0],
    # [12.0, 13.0, 14.0, 15.0]]
    M = MatrixN(list(range(9)), shape=(3, 3))
    m = Matrix(M)
    print(m.formated())
    #[[0.0, 1.0, 2.0, 0.0],
    # [3.0, 4.0, 5.0, 0.0],
    # [6.0, 7.0, 8.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    # inherits from MatrixN --> Array
    print(isinstance(m, MatrixN))
    # True
    print(isinstance(m, Array))
    # True
    # as well as _api.Matrix
    print(isinstance(m, _api.MMatrix))
    # True
    # accepted directly by API methods
    n = _api.MMatrix()
    m = n.setToProduct(m, m)
    print(repr(m))
    print(repr(n))
    t = _api.MTransformationMatrix()
    t.setTranslation(Vector(1, 2, 3), _api.MSpace.kWorld)
    m = Matrix(t)
    print(m.formated())
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    m = Matrix(m, a30=10)
    print(m.formated())
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [10.0, 2.0, 3.0, 1.0]]
    # should fail
    print("Matrix(range(20)")
    try:
        m = Matrix(list(range(20)))
        print(m.formated())
    except:
        print("will raise ValueError: cannot initialize a Matrix of shape (4, 4) from (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19), some information would be lost, use an explicit resize or trim")

    m = Matrix.identity
    M = m.trimmed(shape=(3, 3))
    print(repr(M))
    # MatrixN([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    print(M.formated())
    #[[1.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0],
    # [0.0, 0.0, 1.0]]
    try:
        m.trim(shape=(3, 3))
    except:
        print("will raise TypeError: new shape (3, 3) is not compatible with class Matrix")

    print(m.nrow)
    # 4
    print(m.ncol)
    # 4
    # should fail
    try:
        m.nrow = 3
    except:
        print("will raise TypeError: new shape (3, 4) is not compatible with class Matrix")
    print(list(m.row))
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]
    print(list(m.col))
    # [Array([1.0, 0.0, 0.0, 0.0]), Array([0.0, 1.0, 0.0, 0.0]), Array([0.0, 0.0, 1.0, 0.0]), Array([0.0, 0.0, 0.0, 1.0])]

    m = Matrix(MatrixN(list(range(9)), shape=(3, 3)).trimmed(shape=(4, 4), value=10))
    print(m.formated())
    #[[0.0, 1.0, 2.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]

    print(m.get())
    # ((0.0, 1.0, 2.0, 10.0), (3.0, 4.0, 5.0, 10.0), (6.0, 7.0, 8.0, 10.0), (10.0, 10.0, 10.0, 10.0))
    print(repr(m[0]))
    # [0.0, 1.0, 2.0, 10.0]
    m[0] = 10
    print(m.formated())
    #[[10.0, 10.0, 10.0, 10.0],
    # [3.0, 4.0, 5.0, 10.0],
    # [6.0, 7.0, 8.0, 10.0],
    # [10.0, 10.0, 10.0, 10.0]]
    print((10 in m))
    # True
    print(list(m))
    # [Array([10.0, 10.0, 10.0, 10.0]), Array([3.0, 4.0, 5.0, 10.0]), Array([6.0, 7.0, 8.0, 10.0]), Array([10.0, 10.0, 10.0, 10.0])]
    print(list(m.flat))
    # [10.0, 10.0, 10.0, 10.0, 3.0, 4.0, 5.0, 10.0, 6.0, 7.0, 8.0, 10.0, 10.0, 10.0, 10.0, 10.0]

    u = Vector.xAxis
    v = Vector.yAxis
    print(Vector.xAxis)
    print(str(Vector.xAxis))
    print(str(Vector.xAxis))
    print(repr(Vector.xAxis))

    print("u = Vector.xAxis:")
    print(repr(u))

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print("m:")
    print(round(m, 2))
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]

    x = Vector.xAxis
    y = Vector.yAxis
    z = Vector.zAxis
    u = Vector(1, 2, 3)
    print("u:")
    print(repr(u))
    # Vector([1, 2, 3])
    print("u*m")
    print(repr(u * m))
    # Vector([6.31319304794, 0.378937381963, -0.5])
    print("m*u")
    print(repr(m * u))
    # Vector([-1.5, 2.19067069768, 0.896575472168])

    p = Point(1, 10, 100, 1)
    print("p:")
    print(repr(p))
    # Point([1.0, 10.0, 100.0, 1.0])
    print("p*m")
    print(repr(p * m))
    # Point([196.773355709, -40.1045507576, 2.5, 1.0])
    print("m*p")
    print(repr(m * p))
    # Point([-50.0, 9.91807730799, -3.24452924947, 322.0])

    print("v = [1, 2, 3]*m")
    v = VectorN([1, 2, 3]) * m
    print(repr(v))
    # VectorN([6.31319304794, 0.378937381963, -0.5])
    print("v = [1, 2, 3, 1]*m")
    v = VectorN([1, 2, 3, 1]) * m
    print(repr(v))
    # VectorN([7.31319304794, 2.37893738196, 2.5, 1.0])
    # should fail
    print("VectorN([1, 2, 3, 4, 5])*m")
    try:
        v = VectorN([1, 2, 3, 4, 5]) * m
    except:
        print("Will raise ValueError: vector of size 5 and matrix of shape (4, 4) are not conformable for a VectorN * MatrixN multiplication")

    # herited

    print("m = Matrix(range(1, 17))")
    m = Matrix(list(range(1, 17)))
    print(m.formated())
    #[[1.0, 2.0, 3.0, 4.0],
    # [5.0, 6.0, 7.0, 8.0],
    # [9.0, 10.0, 11.0, 12.0],
    # [13.0, 14.0, 15.0, 16.0]]
    # element wise
    print("[1, 10, 100]*m")
    print(repr([1, 10, 100] * m))
    # Matrix([[1.0, 20.0, 300.0, 0.0], [5.0, 60.0, 700.0, 0.0], [9.0, 100.0, 1100.0, 0.0], [13.0, 140.0, 1500.0, 0.0]])
    print("M = MatrixN(range(20), shape=(4, 5))")
    M = MatrixN(list(range(1, 21)), shape=(4, 5))
    print(M.formated())
    #[[1, 2, 3, 4, 5],
    # [6, 7, 8, 9, 10],
    # [11, 12, 13, 14, 15],
    # [16, 17, 18, 19, 20]]
    print("m*M")
    n = m * M
    print((n).formated())
    #[[110.0, 120.0, 130.0, 140.0, 150.0],
    # [246.0, 272.0, 298.0, 324.0, 350.0],
    # [382.0, 424.0, 466.0, 508.0, 550.0],
    # [518.0, 576.0, 634.0, 692.0, 750.0]]
    print(util.clsname(n))
    # MatrixN
    print("m*2")
    n = m * 2
    print((n).formated())
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]
    print(util.clsname(n))
    # Matrix
    print("2*m")
    n = 2 * m
    print((n).formated())
    #[[2.0, 4.0, 6.0, 8.0],
    # [10.0, 12.0, 14.0, 16.0],
    # [18.0, 20.0, 22.0, 24.0],
    # [26.0, 28.0, 30.0, 32.0]]
    print(util.clsname(n))
    # Matrix
    print("m+2")
    n = m + 2
    print((n).formated())
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]
    print(util.clsname(n))
    # Matrix
    print("2+m")
    n = 2 + m
    print((n).formated())
    #[[3.0, 4.0, 5.0, 6.0],
    # [7.0, 8.0, 9.0, 10.0],
    # [11.0, 12.0, 13.0, 14.0],
    # [15.0, 16.0, 17.0, 18.0]]
    print(util.clsname(n))
    # Matrix
    try:
        m.setToProduct(m, M)
    except:
        print("""Will raise TypeError:  cannot initialize a Matrix of shape (4, 4) from (Array([0, 1, 2, 3, 4]), Array([5, 6, 7, 8, 9]), Array([10, 11, 12, 13, 14]), Array([15, 16, 17, 18, 19])) of shape (4, 5),
                                        as it would truncate data or reduce the number of dimensions""")

    print(m.isEquivalent(m * M))
    # False

    # trans matrix : t: 1, 2, 3, r: 45, 90, 30, s: 0.5, 1.0, 2.0
    m = Matrix([0.0, 4.1633363423443383e-17, -0.5, 0.0, 0.25881904510252079, 0.96592582628906831, 1.3877787807814459e-16, 0.0, 1.9318516525781366, -0.51763809020504159, 0.0, 0.0, 1.0, 2.0, 3.0, 1.0])
    print("m:")
    print(round(m, 2))
    #[[0.0, 0.0, -0.5, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [1.93, -0.52, 0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    print("m.transpose():")
    print(round(m.transpose(), 2))
    #[[0.0, 0.26, 1.93, 1.0],
    # [0.0, 0.97, -0.52, 2.0],
    # [-0.5, 0.0, 0.0, 3.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print("m.isSingular():")
    print(m.isSingular())
    # False
    print("m.inverse():")
    print(round(m.inverse(), 2))
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, 0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print("m.adjoint():")
    print(round(m.adjoint(), 2))
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print("m.adjugate():")
    print(round(m.adjugate(), 2))
    #[[0.0, 0.26, 0.48, 0.0],
    # [0.0, 0.97, -0.13, 0.0],
    # [-2.0, 0.0, -0.0, 0.0],
    # [6.0, -2.19, -0.22, 1.0]]
    print("m.homogenize():")
    print(round(m.homogenize(), 2))
    #[[0.0, 0.0, -1.0, 0.0],
    # [0.26, 0.97, 0.0, 0.0],
    # [0.97, -0.26, -0.0, 0.0],
    # [1.0, 2.0, 3.0, 1.0]]
    print("m.det():")
    print(m.det())
    # 1.0
    print("m.det4x4():")
    print(m.det4x4())
    # 1.0
    print("m.det3x3():")
    print(m.det3x3())
    # 1.0
    print("m.weighted(0.5):")
    print(round(m.weighted(0.5), 2))
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]
    print("m.blend(Matrix.identity, 0.5):")
    print(round(m.blend(Matrix.identity, 0.5), 2))
    #[[0.53, 0.0, -0.53, 0.0],
    # [0.09, 0.99, 0.09, 0.0],
    # [1.05, -0.2, 1.05, 0.0],
    # [0.5, 1.0, 1.5, 1.0]]

    print("end tests Matrix")


def _testMTransformationMatrix():

    q = Quaternion()
    print(repr(q))
    # Quaternion([0.0, 0.0, 0.0, 1.0])
    q = Quaternion(1, 2, 3, 0.5)
    print(repr(q))
    # Quaternion([1.0, 2.0, 3.0, 0.5])
    q = Quaternion(0.785, 0.785, 0.785, "xyz")
    print(repr(q))
    # Quaternion([0.191357439088, 0.461717715523, 0.191357439088, 0.844737481223])

    m = Matrix()
    m.rotate = q
    print(repr(m))
    # Matrix([[0.500398163355, 0.499999841466, -0.706825181105, 0.0], [-0.146587362969, 0.853529322022, 0.499999841466, 0.0], [0.853295859083, -0.146587362969, 0.500398163355, 0.0], [0.0, 0.0, 0.0, 1.0]])

    print("TransformationMatrix class", dir(TransformationMatrix))
    m = TransformationMatrix()
    print(m.formated())
    #[[1.0, 0.0, 0.0, 0.0],
    # [0.0, 1.0, 0.0, 0.0],
    # [0.0, 0.0, 1.0, 0.0],
    # [0.0, 0.0, 0.0, 1.0]]
    print(m[0, 0])
    # 1.0
    print(m[0:2, 0:3])
    # [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    print("TransformationMatrix instance:", dir(m))
    print(TransformationMatrix.__readonly__)
    print(TransformationMatrix.__slots__)
    print(TransformationMatrix.shape)
    print(TransformationMatrix.ndim)
    print(TransformationMatrix.size)
    print(m.shape)
    print(m.ndim)
    print(m.size)
    # should fail
    m.shape = (4, 4)
    m.shape = 2

    print(dir(Space))

    m = TransformationMatrix.identity
    # inherits from MatrixN --> Array
    print(isinstance(m, MatrixN))
    # True
    print(isinstance(m, Array))
    # True
    # as well as _api.TransformationMatrix and _api.Matrix
    print(isinstance(m, _api.MTransformationMatrix))
    # True
    print(isinstance(m, _api.MMatrix))
    # True

    # accepted directly by API methods
    n = _api.MMatrix()
    n = n.setToProduct(m, m)
    print(repr(n))

    n = _api.MTransformationMatrix()
    n = n.assign(m)
    print(repr(n))

    m = TransformationMatrix.identity
    m.rotation = Quaternion()
    print(repr(m))
    print(m.formated())

    n = TransformationMatrix.identity
    n.translation = Vector(1, 2, 3)
    print(n.formated())
    print(repr(n))

    o = m * n
    print(repr(o))
    print(o.formated())

    print("end tests TransformationMatrix")


if __name__ == '__main__':
    unittest.main()