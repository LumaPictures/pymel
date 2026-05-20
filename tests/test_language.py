import unittest

import pymel.core.language as lang

# do this after pymel.core, so maya has initialized
from maya.mel import eval as meval
import maya.cmds as cmds


class testCase_pythonToMelCmd(unittest.TestCase):
    def test_bool_flag(self):
        self.assertEqual(lang.pythonToMelCmd('xform', rao=1).strip(),
                         'xform -rao')
        self.assertEqual(lang.pythonToMelCmd('connectAttr', force=1).strip(),
                         'connectAttr -force')

    def test_bool_arg(self):
        self.assertEqual(lang.pythonToMelCmd('connectAttr', lock=1).strip(),
                         'connectAttr -lock 1')

    def test_multi_arg(self):
        self.assertEqual(lang.pythonToMelCmd('xform', translation=(1,2,3)).strip(),
                         'xform -translation 1 2 3')

class testCase_MelGlobals(unittest.TestCase):
    def setUp(self):
        meval('''global proc int melGlobals_test_int_getter(int $inValue)
                {
                    return $inValue;
                }''')

        meval('''global proc string melGlobals_test_str_getter(string $inValue)
                {
                    return $inValue;
                }''')

        meval('''global proc int[] melGlobals_test_int_arr_getter(int $inValue[])
                {
                    return $inValue;
                }''')

        meval('''global proc string[] melGlobals_test_str_arr_getter(string $inValue[])
                {
                    return $inValue;
                }''')


    def test_set_int(self):
        meval('global int $melGlobals_test_set_int1')

        lang.melGlobals.set('melGlobals_test_set_int1', 37)
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_set_int1)'),
                         37)
        lang.melGlobals.set('$melGlobals_test_set_int1', 47)
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_set_int1)'),
                         47)
        lang.MelGlobals.set('melGlobals_test_set_int1', 57)
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_set_int1)'),
                         57)
        lang.MelGlobals.set('$melGlobals_test_set_int1', 67)
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_set_int1)'),
                         67)

    def test_set_int_arr(self):
        meval('global int $melGlobals_test_set_int_arr1[]')

        lang.melGlobals.set('melGlobals_test_set_int_arr1', [3, 4])
        self.assertEqual(meval('melGlobals_test_int_arr_getter($melGlobals_test_set_int_arr1)'),
                         [3, 4])
        lang.melGlobals.set('$melGlobals_test_set_int_arr1', [5, 6])
        self.assertEqual(meval('melGlobals_test_int_arr_getter($melGlobals_test_set_int_arr1)'),
                         [5, 6])
        lang.MelGlobals.set('melGlobals_test_set_int_arr1', [7, 8])
        self.assertEqual(meval('melGlobals_test_int_arr_getter($melGlobals_test_set_int_arr1)'),
                         [7, 8])
        lang.MelGlobals.set('$melGlobals_test_set_int_arr1', [9, 10])
        self.assertEqual(meval('melGlobals_test_int_arr_getter($melGlobals_test_set_int_arr1)'),
                         [9, 10])

    def test_set_str(self):
        meval('global string $melGlobals_test_set_str1')

        lang.melGlobals.set('melGlobals_test_set_str1', 'albatross')
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_set_str1)'),
                         'albatross')
        lang.melGlobals.set('$melGlobals_test_set_str1', 'dinosaur')
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_set_str1)'),
                         'dinosaur')

        lang.MelGlobals.set('melGlobals_test_set_str1', 'iguana')
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_set_str1)'),
                         'iguana')
        lang.MelGlobals.set('$melGlobals_test_set_str1', 'parakeet')
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_set_str1)'),
                         'parakeet')

    def test_set_str_arr(self):
        meval('global string $melGlobals_test_set_str_arr1[]')

        lang.melGlobals.set('melGlobals_test_set_str_arr1', ['albatross', 'macaroni'])
        self.assertEqual(meval('melGlobals_test_str_arr_getter($melGlobals_test_set_str_arr1)'),
                         ['albatross', 'macaroni'])
        lang.melGlobals.set('$melGlobals_test_set_str_arr1', ['dinosaur', 'pizza'])
        self.assertEqual(meval('melGlobals_test_str_arr_getter($melGlobals_test_set_str_arr1)'),
                         ['dinosaur', 'pizza'])

        lang.MelGlobals.set('melGlobals_test_set_str_arr1', ['iguana', 'lasagna'])
        self.assertEqual(meval('melGlobals_test_str_arr_getter($melGlobals_test_set_str_arr1)'),
                         ['iguana', 'lasagna'])
        lang.MelGlobals.set('$melGlobals_test_set_str_arr1', ['parakeet', 'dougnuts'])
        self.assertEqual(meval('melGlobals_test_str_arr_getter($melGlobals_test_set_str_arr1)'),
                         ['parakeet', 'dougnuts'])

    def test_setitem_int(self):
        meval('int $melGlobals_test_setitem_int1')

        lang.melGlobals['melGlobals_test_setitem_int1'] = 37
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_setitem_int1)'),
                         37)
        lang.melGlobals['$melGlobals_test_setitem_int1'] = 47
        self.assertEqual(meval('melGlobals_test_int_getter($melGlobals_test_setitem_int1)'),
                         47)

    def test_setitem_str(self):
        meval('global string $melGlobals_test_setitem_str1')

        lang.melGlobals['melGlobals_test_setitem_str1'] = 'monkey'
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_setitem_str1)'),
                         'monkey')
        lang.melGlobals['$melGlobals_test_setitem_str1'] = 'apple'
        self.assertEqual(meval('melGlobals_test_str_getter($melGlobals_test_setitem_str1)'),
                         'apple')

    def test_get_int(self):
        meval('global int $melGlobals_test_get_int1')

        meval('$melGlobals_test_get_int1 = 37')
        self.assertEqual(lang.melGlobals.get('melGlobals_test_get_int1'), 37)

        meval('$melGlobals_test_get_int1 = 47')
        self.assertEqual(lang.melGlobals.get('$melGlobals_test_get_int1'), 47)

        meval('$melGlobals_test_get_int1 = 57')
        self.assertEqual(lang.MelGlobals.get('melGlobals_test_get_int1'), 57)

        meval('$melGlobals_test_get_int1 = 67')
        self.assertEqual(lang.MelGlobals.get('$melGlobals_test_get_int1'), 67)

    def test_get_int_arr(self):
        meval('global int $melGlobals_test_get_int_arr1[]')

        meval('$melGlobals_test_get_int_arr1 = {1, 2}')
        self.assertEqual(lang.melGlobals.get('melGlobals_test_get_int_arr1'), [1, 2])

        meval('$melGlobals_test_get_int_arr1 = {3, 4}')
        self.assertEqual(lang.melGlobals.get('$melGlobals_test_get_int_arr1'), [3, 4])

        meval('$melGlobals_test_get_int_arr1 = {5, 6}')
        self.assertEqual(lang.MelGlobals.get('melGlobals_test_get_int_arr1'), [5, 6])

        meval('$melGlobals_test_get_int_arr1 = {7, 8}')
        self.assertEqual(lang.MelGlobals.get('$melGlobals_test_get_int_arr1'), [7, 8])

    def test_get_str(self):
        meval('global string $melGlobals_test_get_str1')

        meval('$melGlobals_test_get_str1 = "waldo"')
        self.assertEqual(lang.melGlobals.get('melGlobals_test_get_str1'), 'waldo')

        meval('$melGlobals_test_get_str1 = "marcy"')
        self.assertEqual(lang.melGlobals.get('$melGlobals_test_get_str1'), 'marcy')

        meval('$melGlobals_test_get_str1 = "may"')
        self.assertEqual(lang.MelGlobals.get('melGlobals_test_get_str1'), 'may')

        meval('$melGlobals_test_get_str1 = "marlene"')
        self.assertEqual(lang.MelGlobals.get('$melGlobals_test_get_str1'), 'marlene')

    def test_get_str_arr(self):
        meval('global string $melGlobals_test_get_str_arr1[]')

        meval('$melGlobals_test_get_str_arr1 = {"waldo", "funk"}')
        self.assertEqual(lang.melGlobals.get('melGlobals_test_get_str_arr1'), ["waldo", "funk"])

        meval('$melGlobals_test_get_str_arr1 = {"marcy", "jazz"}')
        self.assertEqual(lang.melGlobals.get('$melGlobals_test_get_str_arr1'), ["marcy", "jazz"])

        meval('$melGlobals_test_get_str_arr1 = {"may", "rock"}')
        self.assertEqual(lang.MelGlobals.get('melGlobals_test_get_str_arr1'), ["may", "rock"])

        meval('$melGlobals_test_get_str_arr1 = {"marlene", "trip-hop"}')
        self.assertEqual(lang.MelGlobals.get('$melGlobals_test_get_str_arr1'), ["marlene", "trip-hop"])

    def test_getitem_int(self):
        meval('global int $melGlobals_test_getitem_int1')

        meval('$melGlobals_test_getitem_int1 = 37')
        self.assertEqual(lang.melGlobals['melGlobals_test_getitem_int1'], 37)

        meval('$melGlobals_test_getitem_int1 = 47')
        self.assertEqual(lang.melGlobals['$melGlobals_test_getitem_int1'], 47)

    def test_getitem_str(self):
        meval('global string $melGlobals_test_getitem_str1')

        meval('$melGlobals_test_getitem_str1 = "waldo"')
        self.assertEqual(lang.melGlobals.get('melGlobals_test_getitem_str1'), 'waldo')

        meval('$melGlobals_test_getitem_str1 = "marcy"')
        self.assertEqual(lang.melGlobals.get('$melGlobals_test_getitem_str1'), 'marcy')

        meval('$melGlobals_test_getitem_str1 = "may"')
        self.assertEqual(lang.MelGlobals.get('melGlobals_test_getitem_str1'), 'may')

        meval('$melGlobals_test_getitem_str1 = "marlene"')
        self.assertEqual(lang.MelGlobals.get('$melGlobals_test_getitem_str1'), 'marlene')

    def test_initVar_int(self):
        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_int1')
        lang.melGlobals.initVar('int', 'melGlobals_test_initVar_int1')
        meval('print $melGlobals_test_initVar_int1')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_int2')
        lang.melGlobals.initVar('int', '$melGlobals_test_initVar_int2')
        meval('print $melGlobals_test_initVar_int2')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_int3')
        lang.MelGlobals.initVar('int', 'melGlobals_test_initVar_int3')
        meval('print $melGlobals_test_initVar_int3')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_int4')
        lang.MelGlobals.initVar('int', '$melGlobals_test_initVar_int4')
        meval('print $melGlobals_test_initVar_int4')

    def test_initVar_str(self):
        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_str1')
        lang.melGlobals.initVar('string', 'melGlobals_test_initVar_str1')
        meval('print $melGlobals_test_initVar_str1')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_str2')
        lang.melGlobals.initVar('string', '$melGlobals_test_initVar_str2')
        meval('print $melGlobals_test_initVar_str2')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_str3')
        lang.MelGlobals.initVar('string', 'melGlobals_test_initVar_str3')
        meval('print $melGlobals_test_initVar_str3')

        self.assertRaises(RuntimeError, meval, 'print $melGlobals_test_initVar_str4')
        lang.MelGlobals.initVar('string', '$melGlobals_test_initVar_str4')
        meval('print $melGlobals_test_initVar_str4')

    def test_getType_int(self):
        meval('global int $melGlobals_test_getType_int1')
        self.assertEqual(lang.melGlobals.getType('melGlobals_test_getType_int1'),
                         'int')

        meval('global int $melGlobals_test_getType_int2')
        self.assertEqual(lang.melGlobals.getType('$melGlobals_test_getType_int2'),
                         'int')

        meval('global int $melGlobals_test_getType_int3')
        self.assertEqual(lang.MelGlobals.getType('melGlobals_test_getType_int3'),
                         'int')

        meval('global int $melGlobals_test_getType_int4')
        self.assertEqual(lang.MelGlobals.getType('$melGlobals_test_getType_int4'),
                         'int')

    def test_getType_str(self):
        meval('global string $melGlobals_test_getType_str1')
        self.assertEqual(lang.melGlobals.getType('melGlobals_test_getType_str1'),
                         'string')

        meval('global string $melGlobals_test_getType_str2')
        self.assertEqual(lang.melGlobals.getType('$melGlobals_test_getType_str2'),
                         'string')

        meval('global string $melGlobals_test_getType_str3')
        self.assertEqual(lang.MelGlobals.getType('melGlobals_test_getType_str3'),
                         'string')

        meval('global string $melGlobals_test_getType_str4')
        self.assertEqual(lang.MelGlobals.getType('$melGlobals_test_getType_str4'),
                         'string')

    def test_keys(self):
        self.assertFalse('$melGlobals_test_keys_int1' in lang.melGlobals.keys())
        meval('global int $melGlobals_test_keys_int1')
        self.assertTrue('$melGlobals_test_keys_int1' in lang.melGlobals.keys())
        self.assertFalse('melGlobals_test_keys_int1' in lang.melGlobals.keys())

        self.assertFalse('$melGlobals_test_keys_int2' in lang.MelGlobals.keys())
        meval('global int $melGlobals_test_keys_int2')
        self.assertTrue('$melGlobals_test_keys_int2' in lang.MelGlobals.keys())
        self.assertFalse('melGlobals_test_keys_int2' in lang.MelGlobals.keys())

        self.assertFalse('$melGlobals_test_keys_str1' in lang.melGlobals.keys())
        meval('global string $melGlobals_test_keys_str1')
        self.assertTrue('$melGlobals_test_keys_str1' in lang.melGlobals.keys())
        self.assertFalse('melGlobals_test_keys_str1' in lang.melGlobals.keys())

        self.assertFalse('$melGlobals_test_keys_str2' in lang.MelGlobals.keys())
        meval('global string $melGlobals_test_keys_str2')
        self.assertTrue('$melGlobals_test_keys_str2' in lang.MelGlobals.keys())
        self.assertFalse('melGlobals_test_keys_str2' in lang.MelGlobals.keys())

    def test_contains(self):
        self.assertFalse('$melGlobals_test_contains_int1' in lang.melGlobals)
        self.assertFalse('melGlobals_test_contains_int1' in lang.melGlobals)
        meval('global int $melGlobals_test_contains_int1')
        self.assertTrue('$melGlobals_test_contains_int1' in lang.melGlobals)
        self.assertTrue('melGlobals_test_contains_int1' in lang.melGlobals)

        self.assertFalse('$melGlobals_test_contains_int2' in lang.melGlobals)
        self.assertFalse('melGlobals_test_contains_int2' in lang.melGlobals)
        meval('global int $melGlobals_test_contains_int2')
        self.assertTrue('$melGlobals_test_contains_int2' in lang.melGlobals)
        self.assertTrue('melGlobals_test_contains_int2' in lang.melGlobals)

        self.assertFalse('$melGlobals_test_contains_str1' in lang.melGlobals)
        self.assertFalse('melGlobals_test_contains_str1' in lang.melGlobals)
        meval('global string $melGlobals_test_contains_str1')
        self.assertTrue('$melGlobals_test_contains_str1' in lang.melGlobals)
        self.assertTrue('melGlobals_test_contains_str1' in lang.melGlobals)

        self.assertFalse('$melGlobals_test_contains_str2' in lang.melGlobals)
        self.assertFalse('melGlobals_test_contains_str2' in lang.melGlobals)
        meval('global string $melGlobals_test_contains_str2')
        self.assertTrue('$melGlobals_test_contains_str2' in lang.melGlobals)
        self.assertTrue('melGlobals_test_contains_str2' in lang.melGlobals)

    def test_get_dict(self):
        self.assertEqual(lang.melGlobals.get_dict('melGlobals_test_get_dict'),
                         None)
        self.assertEqual(lang.melGlobals.get_dict('melGlobals_test_get_dict',
                                                  'foo'),
                         'foo')
        meval('global int $melGlobals_test_get_dict = 3')
        self.assertEqual(lang.melGlobals.get_dict('melGlobals_test_get_dict'),
                         3)
        self.assertEqual(lang.melGlobals.get_dict('melGlobals_test_get_dict',
                                                  'foo'),
                         3)

    def test_noInit_set(self):
        self.assertRaises(TypeError, lang.melGlobals.set, 'melGlobals_test_nonexistant1', 37)
        self.assertRaises(TypeError, lang.melGlobals.set, 'melGlobals_test_nonexistant2', 'foo')

    def test_noInit_setitem(self):
        self.assertRaises(TypeError, lang.melGlobals.__setitem__, 'melGlobals_test_nonexistant3', 37)
        self.assertRaises(TypeError, lang.melGlobals.__setitem__, 'melGlobals_test_nonexistant4', 'foo')

    def test_noInit_get(self):
        self.assertRaises(KeyError, lang.melGlobals.get, 'melGlobals_test_nonexistant5')

    def test_noInit_getitem(self):
        self.assertRaises(KeyError, lang.melGlobals.__getitem__, 'melGlobals_test_nonexistant6')

    def test_noInit_getType(self):
        self.assertRaises(TypeError, lang.melGlobals.getType, 'melGlobals_test_nonexistant7')


class testCase_env(unittest.TestCase):
    def setUp(self):
        cmds.playbackOptions(animationStartTime=1)
        cmds.playbackOptions(minTime=4)
        cmds.playbackOptions(maxTime=10)
        cmds.playbackOptions(animationEndTime=24)

    def test_animStartTime_property(self):
        self.assertEqual(1, lang.env.animStartTime)
        lang.env.animStartTime = 2
        self.assertEqual(2, lang.env.animStartTime)

    def test_animStartTime_methods(self):
        self.assertEqual(1, lang.env.getAnimStartTime())
        lang.env.setAnimStartTime(3)
        self.assertEqual(3, lang.env.getAnimStartTime())

    def test_minTime_property(self):
        self.assertEqual(4, lang.env.minTime)
        lang.env.minTime = 5
        self.assertEqual(5, lang.env.minTime)

    def test_minTime_methods(self):
        self.assertEqual(4, lang.env.getMinTime())
        lang.env.setMinTime(6)
        self.assertEqual(6, lang.env.getMinTime())

    def test_maxTime_property(self):
        self.assertEqual(10, lang.env.maxTime)
        lang.env.maxTime = 11
        self.assertEqual(11, lang.env.maxTime)

    def test_maxTime_methods(self):
        self.assertEqual(10, lang.env.getMaxTime())
        lang.env.setMaxTime(12)
        self.assertEqual(12, lang.env.getMaxTime())

    def test_animEndTime_property(self):
        self.assertEqual(24, lang.env.animEndTime)
        lang.env.animEndTime = 22
        self.assertEqual(22, lang.env.animEndTime)

    def test_animEndTime_methods(self):
        self.assertEqual(24, lang.env.getAnimEndTime())
        lang.env.setAnimEndTime(23)
        self.assertEqual(23, lang.env.getAnimEndTime())

    def test_playbackTimes_property(self):
        self.assertEqual((1, 4, 10, 24), lang.env.playbackTimes)
        lang.env.playbackTimes = (2, 5, 11, 22)
        self.assertEqual((2, 5, 11, 22), lang.env.playbackTimes)

    def test_playbackTimes_methods(self):
        self.assertEqual((1, 4, 10, 24), lang.env.getPlaybackTimes())
        lang.env.setPlaybackTimes((3, 6, 12, 23))
        self.assertEqual((3, 6, 12, 23), lang.env.getPlaybackTimes())


class testCase_Mel(unittest.TestCase):
    def setUp(self):
        meval('''global proc int Mel_test_int_getter(int $inValue)
                {
                    return $inValue;
                }''')

        meval('''global proc string Mel_test_str_getter(string $inValue)
                {
                    return $inValue;
                }''')

        meval('''global proc int[] Mel_test_int_arr_getter(int $inValue[])
                {
                    return $inValue;
                }''')

        meval('''global proc string[] Mel_test_str_arr_getter(string $inValue[])
                {
                    return $inValue;
                }''')

        meval('''global proc int Mel_test(int $inValue)
                {
                    return $inValue;
                }''')

        meval('''global proc float Mel_test.NumUtils.add(float $inValue1, float $inValue2)
                {
                    return $inValue1 + $inValue2;
                }''')

        meval('''global proc float Mel_test.NumUtils.sub(float $inValue1, float $inValue2)
                {
                    return $inValue1 - $inValue2;
                }''')

        meval('''global proc float Mel_test.NumUtils.Constants.getPi()
                {
                    return 3.141;
                }''')

    def test_MelProcCalls(self):
        self.assertEqual(lang.mel.Mel_test_int_getter(12), 12)
        self.assertEqual(lang.mel.Mel_test_str_getter("Test!"), "Test!")
        self.assertEqual(lang.mel.Mel_test_int_arr_getter([1, 2, 3]), [1, 2, 3])
        self.assertEqual(lang.mel.Mel_test_str_arr_getter(['A', 'B', 'C']), ['A', 'B', 'C'])
        self.assertRaises(lang.MelConversionError, lang.mel.Mel_test_int_getter, ["A", "B"])
        self.assertRaises(lang.MelArgumentError, lang.mel.Mel_test_int_getter, 12, 13)

    def test_MelNamespacedProcCalls(self):
        self.assertEqual(lang.mel.Mel_test(32), 32)
        self.assertEqual(lang.mel.Mel_test.NumUtils.add(1.5, 2.2), 3.7)
        self.assertEqual(lang.mel.Mel_test.NumUtils.sub(2.5, 1.2), 1.3)
        self.assertEqual(lang.mel.Mel_test.NumUtils.Constants.getPi(), 3.141)
        self.assertRaises(lang.MelConversionError, lang.mel.Mel_test.NumUtils.add, ["A"], ["B"])
        self.assertRaises(lang.MelArgumentError, lang.mel.Mel_test.NumUtils.add, 12, 13, 14)
        self.assertRaises(lang.MelUnknownProcedureError, lang.mel.Mel_test.poop)
