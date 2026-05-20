'''
Created on Oct 16, 2012

@author: paulm
'''
import os
import unittest
import logging

import pymel.internal.plogging as plogging
import pymel.core

class testCase_raiseLog(unittest.TestCase):
    DEFAULT_LOGGER = pymel.core._logger

    @classmethod
    def _makeTest(cls, logLvlName, errorLvlName, logger=None):
        logLvl = getattr(logging, logLvlName)
        errorLvl = getattr(logging, errorLvlName)

        if logger:
            funcType = 'method'
            func = logger.raiseLog
            args = []
        else:
            funcType = 'function'
            func =  plogging.raiseLog
            args = [cls.DEFAULT_LOGGER]
        msg = "attempting %s raiseLog %s (ERRORLEVEL set to %s):" % (logLvlName, funcType, errorLvlName)
        args.extend([logLvl, msg])

        def raiseLogTest(self):
            oldLvl = plogging.ERRORLEVEL
            plogging.ERRORLEVEL = errorLvl
            try:
                kwargs = {'errorClass':TypeError}
                if errorLvl <= logLvl:
                    # the errorLevel is lower than the level we're emitting, it should
                    # raise an error
                    self.assertRaises(RuntimeError, func, *args)
                    self.assertRaises(TypeError, func, *args, **kwargs)
                else:
                    # we should be able to run this without an error...
                    func(*args)
                    func(*args, **kwargs)
            finally:
                plogging.ERRORLEVEL = oldLvl
        raiseLogTest.__name__ = 'test_raiseLog_%s_emit_%s_err_%s' % (funcType, logLvlName, errorLvlName)
        return raiseLogTest


    @classmethod
    def addTests(cls):
        logLevelNames = ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        for logLvlName in logLevelNames:
            for errorLvlName in logLevelNames:
                for logger in (None, cls.DEFAULT_LOGGER):
                    test = cls._makeTest(logLvlName, errorLvlName, logger=logger)
                    setattr(cls, test.__name__, test)
testCase_raiseLog.addTests()