"""
The runtime module contains all runtime commands.
"""

import pymel.util.factories

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createFunctions():
	for funcName in pymel.util.factories.moduleCmds['runtime']:
		func = pymel.util.factories.functionFactory( funcName, None )
		if func:
			func.__module__ = __name__
			setattr( _thisModule, funcName, func )
#_createFunctions()

pymel.util.factories.createFunctions( __name__ )