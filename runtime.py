"""
The runtime module contains all runtime commands.
"""

import factories

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createFunctions():
	for funcName, data in factories.cmdlist.items():
		if data['type'] == 'runtime':
			func = factories.functionFactory( funcName, None )
			if func:
				func.__module__ = __name__
				setattr( _thisModule, funcName, func )
_createFunctions()

#factories.createFunctions( _thisModule, None )