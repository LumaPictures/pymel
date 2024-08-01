from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest

import maya.OpenMaya as om

import pymel.internal.factories as factories


class TestApiEnums(unittest.TestCase):
    def test_apiTypesToApiEnums(self):
        for enumName, enumNum  in factories.apiTypesToApiEnums.items():
            self.assertIsInstance(enumNum, int)
            self.assertIsInstance(enumName, str)
            self.assertEqual(getattr(om.MFn, enumName), enumNum)

    def test_apiEnumsToApiTypes(self):
        for enumNum, enumName in factories.apiEnumsToApiTypes.items():
            self.assertIsInstance(enumNum, int)
            self.assertIsInstance(enumName, str)
            self.assertEqual(getattr(om.MFn, enumName), enumNum)

    def test_consistency(self):
        # apiEnumsToApiTypes should be the inverse of apiTypesToApiEnums,
        # except that multiple names may map to the same number
        rebuilt_apiEnumsToApiTypes = {}
        multipleNames = {}
        for enumName, enumNum  in factories.apiTypesToApiEnums.items():
            if enumNum in multipleNames:
                multipleNames[enumNum].append(enumName)
            else:
                existingName = rebuilt_apiEnumsToApiTypes.pop(enumNum, None)
                if existingName is None:
                    rebuilt_apiEnumsToApiTypes[enumNum] = enumName
                else:
                    multipleNames[enumNum] = [existingName, enumName]

        # ensure that for all nums that had multiple names, it exists in
        # apiEnumsToApiTypes, and the value is one of the expected ones
        for enumNum, possibleNames in multipleNames.items():
            chosenName = factories.apiEnumsToApiTypes[enumNum]
            self.assertIn(chosenName, possibleNames)
            rebuilt_apiEnumsToApiTypes[enumNum] = chosenName
        self.assertDictEqual(factories.apiEnumsToApiTypes,
                             rebuilt_apiEnumsToApiTypes)


class TestUtils(unittest.TestCase):
    def test_maybeConvert(self):
        self.assertEqual(
            factories.maybeConvert(1, bool),
            True)

        self.assertEqual(
            factories.maybeConvert(0, bool),
            False)

        self.assertEqual(
            factories.maybeConvert('0', int),
            0)

        self.assertEqual(
            factories.maybeConvert('foo', int),
            'foo')

        self.assertEqual(
            factories.maybeConvert([0, 1, 2], bool),
            [False, True, True])

        self.assertEqual(
            factories.maybeConvert([], bool),
            [])
