import unittest

import pymel.core.language as lang

# do this after pymel.core, so maya has initialized
from maya.mel import eval as meval


class testCase_pythonToMelCmd(unittest.TestCase):
    def test_bool_arg(self):
        self.assertEqual(lang.pythonToMelCmd('xform', rao=1).strip(),
                         'xform -rao')

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
    
