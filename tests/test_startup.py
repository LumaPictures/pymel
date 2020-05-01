from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import shutil
import tempfile
import unittest

import pymel.internal.startup as startup

class TestCacheFormats(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_dumpLoad(self):
        smiley = u'\U0001F600'
        DATAS = {
            'unicode': {'foo': smiley},
            'ascii': {'foo': 7}
        }

        filebase = os.path.join(self.tmpdir, 'test_bin')
        for name, data in DATAS.items():
            for fmt in startup.PymelCache.FORMATS:
                filename = '{}_{}{}'.format(filebase, name, fmt.ext)
                #print("testing: {} - {} - {}".format(name, data, fmt[0]))
                fmt.writer(data, filename)
                read_data = fmt.reader(filename)
                assert read_data == data
                assert type(read_data) is type(data)