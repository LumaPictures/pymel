from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest

import pymel.util.arrays
from pymel.util.arrays import Array

class TestArray(unittest.TestCase):
    def test_truediv(self):
        a = Array(1, 2, 3)
        res = a.__truediv__(2)
        expected = Array(.5, 1, 1.5)
        self.assertEqual(res, expected)
        res = a / 2
        self.assertEqual(res, expected)

    def test_rtruediv(self):
        a = Array(1, 2, 4)
        res = a.__rtruediv__(2)
        expected = Array(2, 1, .5)
        self.assertEqual(res, expected)
        res = 2 / a
        self.assertEqual(res, expected)

    def test_itruediv(self):
        a = Array(1, 2, 3)
        res = a.__itruediv__(2)
        expected = Array(.5, 1, 1.5)
        self.assertEqual(res, expected)
        a = Array(1, 2, 3)
        a /= 2
        self.assertEqual(a, expected)

    def test_floordiv(self):
        a = Array(1, 2, 3)
        res = a.__floordiv__(2)
        expected = Array(0, 1, 1)
        self.assertEqual(res, expected)
        res = a // 2
        self.assertEqual(res, expected)

    def test_rfloordiv(self):
        a = Array(1, 2, 4)
        res = a.__rfloordiv__(2)
        expected = Array(2, 1, 0)
        self.assertEqual(res, expected)
        res = 2 // a
        self.assertEqual(res, expected)

    def test_ifloordiv(self):
        a = Array(1, 2, 3)
        res = a.__ifloordiv__(2)
        expected = Array(0, 1, 1)
        self.assertEqual(res, expected)
        a = Array(1, 2, 3)
        a //= 2
        self.assertEqual(a, expected)

    def test_mod(self):
        a = Array(1, 2, 3)
        res = a.__mod__(2)
        expected = Array(1, 0, 1)
        self.assertEqual(res, expected)
        res = a % 2
        self.assertEqual(res, expected)

    def test_rmod(self):
        a = Array(1, 2, 4)
        res = a.__rmod__(2)
        expected = Array(0, 0, 2)
        self.assertEqual(res, expected)
        res = 2 % a
        self.assertEqual(res, expected)

    def test_imod(self):
        a = Array(1, 2, 3)
        res = a.__imod__(2)
        expected = Array(1, 0, 1)
        self.assertEqual(res, expected)
        a = Array(1, 2, 3)
        a %= 2
        self.assertEqual(a, expected)
