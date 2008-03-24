"""
The ctx module contains all context commands.
"""

import pymel.util.factories

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createFunctions():
	for funcName in pymel.util.factories.moduleCmds['ctx']:
		func = pymel.util.factories.functionFactory( funcName, None )
		if func:
			func.__module__ = __name__
			setattr( _thisModule, funcName, func )
		#else:
		#	print "could not create ctx function", funcName	
							
#_createFunctions()
pymel.util.factories.createFunctions( __name__ )