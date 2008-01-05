
"""
The io module contains functions relating to files and references.

In particular, the io module contains the functionality of maya.cmds.file. The file command should not be imported into
the default namespace because it conflicts with python's builtin file class. Since the file command has so many flags, 
I decided to kill two birds with one stone: by breaking the file command down into multiple functions -- one for each 
primary flag -- the resulting functions are more readable and allow the file command's functionality to be used directly
within the pymel namespace.   

for example, instead of this:
	
	>>> expFile = cmds.file( exportAll=1, preserveReferences=1 )
	
you can do this:

	>>> expFile = exportAll( preserveReferences=1)
	
some of the new commands were changed slightly from their flag name to avoid name clashes and to add to readability:

	>>> importFile( expFile )
	>>> createReference( expFile )

also note that the 'type' flag is set automatically for you when your path includes a '.mb' or '.ma' extension.
"""

try:
	import maya.cmds as cmds
except ImportError: pass

import path, sys
import core, util

def _getTypeFromExtension( path ):
	return {
		'.ma' : 'mayaAscii',
		'.mb' :	'mayaBinary'
	}[core.Path(path).ext]



		

def listNamespaces():
	"""Returns a list of the namespaces of referenced files.
	REMOVE In Favor of listReferences('dict') ?""" 
	try:
		return [ cmds.file( x, q=1, namespace=1) for x in cmds.file( q=1, reference=1)  ]
	except:
		return []





def listReferences(type='list'):
	"""file -q -reference
	By default returns a list of reference files as Reference classes. The optional type argument can be passed a 'dict'
	(or dict object) to return the references as a dictionary with namespaces as keys and References as values.
	
	Untested: multiple references with no namespace...
	"""
	
	# dict
	if type in ['dict', dict]:
		res = {}
		try:
			for x in cmds.file( q=1, reference=1):
				res[cmds.file( x, q=1, namespace=1)] = core.Reference(x)
		except: pass
		return res
	
	# list
	return map( core.Reference,cmds.file( q=1, reference=1) )

def getReferences(reference=None, recursive=False):
	res = {}	
	if reference is None:
		try:
			for x in cmds.file( q=1, reference=1):
				ref = core.Reference(x)
				res[cmds.file( x, q=1, namespace=1)] = ref
				if recursive:
					res.update( ref.subReferences() )
		except: pass
	else:
		try:
			for x in cmds.file( self, q=1, reference=1):
				res[cmds.file( x, q=1, namespace=1)] = core.Reference(x)
		except: pass
	return res	
	
def createReference( *args, **kwargs ):
	"""file -reference"""
	kwargs['reference'] = True
	return core.Reference(cmds.file(*args, **kwargs))

def loadReference( file, refNode, **kwargs ):
	"""file -loadReference"""
	kwargs['loadReference'] = refNode
	return core.Reference(cmds.file(file, **kwargs))
		
def exportAll( *args, **kwargs ):
	"""file -exportAll"""
	kwargs['exportAll'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	
	return core.Path(cmds.file(*args, **kwargs))

def exportAnim( *args, **kwargs ):
	"""file -exportAnim"""
	kwargs['exportAnim'] = True
	return core.Path(cmds.file(*args, **kwargs))

def exportAnimFromReference( *args, **kwargs ):
	"""file -exportAnimFromReference"""
	kwargs['exportAnimFromReference'] = True
	return core.Path(cmds.file(*args, **kwargs))

def exportAsReference( *args, **kwargs ):
	"""file -exportAsReference"""
	kwargs['exportAsReference'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	return core.Reference(cmds.file(*args, **kwargs))

def exportSelected( *args, **kwargs ):
	"""file -exportSelected"""
	kwargs['exportSelected'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	return core.Path(cmds.file(*args, **kwargs))
	
def exportSelectedAnim( *args, **kwargs ):
	"""file -exportSelectedAnim"""
	kwargs['exportSelectedAnim'] = True
	return core.Path(cmds.file(*args, **kwargs))
	
def exportSelectedAnimFromReference( *args, **kwargs ):
	"""file -exportSelectedAnimFromReference"""
	kwargs['exportSelectedAnimFromReference'] = True
	return core.Path(cmds.file(*args, **kwargs))

def importFile( *args, **kwargs ):
	"""file -import"""
	kwargs['import'] = True
	return core.Path(cmds.file(*args, **kwargs))

def newFile( *args, **kwargs ):
	"""file -newFile"""
	kwargs['newFile'] = True
	return core.Path(cmds.file(*args, **kwargs))

def openFile( *args, **kwargs ):
	"""file -open"""
	kwargs['open'] = True
	return core.Path(cmds.file(*args, **kwargs))	

def renameFile( *args, **kwargs ):
	"""file -rename"""
	kwargs['rename'] = True
	return core.Path(cmds.file(*args, **kwargs))
	
def saveAs(filepath, **kwargs):
	cmds.file( rename=filepath )
	kwargs['save']=True
	try:
		kwargs['type'] = _getTypeFromExtension(filepath)
	except KeyError: pass
	return core.Path(cmds.file(**kwargs) )
