
"""
The file command is the most important of the commands that should not be imported into the default namespace because
it conflicts with python's builtin file class.  Since the file command has so many flags, I decided to kill two birds with
one stone: by breaking the file command down into multiple functions -- one for each primary flag -- the command becomes
more readable and also allows its functionality to be found directly within the pymel namespace.   

for example, instead of this:
	
	>>> expFile = cmds.file( exportAll=1, preserveReferences=1 )
	
you can do this:

	>>> expFile = exportAll( preserveReferences=1)
	
some of the new commands were changed slightly from their flag name to avoid name clashes and to add to readability:

	>>> importFile( expFile )
	>>> createReference( expFile )

also note that the 'type' flag is set automatically for you when your path includes a '.mb' or '.ma' extension.
"""

import maya.cmds as cmds
import path, sys
import pymel.core, util

def _getTypeFromExtension( path ):
	return {
		'.ma' : 'mayaAscii',
		'.mb' :	'mayaBinary'
	}[pymel.core.MPath(path).ext]



		

def listNamespaces():
	"""Returns a list of the namespaces of referenced files.
	REMOVE In Favor of listReferences('dict') ?""" 
	try:
		return [ cmds.file( x, q=1, namespace=1) for x in cmds.file( q=1, reference=1)  ]
	except:
		return []





def listReferences(type='list'):
	"""file -q -reference
	By default returns a list of reference files as MReference classes. The optional type argument can be passed a 'dict'
	(or dict object) to return the references as a dictionary with namespaces as keys and MReferences as values.
	
	Untested: multiple references with no namespace...
	"""
	
	# dict
	if type in ['dict', dict]:
		res = {}
		try:
			for x in cmds.file( q=1, reference=1):
				res[cmds.file( x, q=1, namespace=1)] = pymel.core.MReference(x)
		except: pass
		return res
	
	# list
	return map( pymel.core.MReference,cmds.file( q=1, reference=1) )

def getReferences(reference=None, recursive=False):
	res = {}	
	if reference is None:
		try:
			for x in cmds.file( q=1, reference=1):
				ref = pymel.core.MReference(x)
				res[cmds.file( x, q=1, namespace=1)] = ref
				if recursive:
					res.update( ref.subReferences() )
		except: pass
	else:
		try:
			for x in cmds.file( self, q=1, reference=1):
				res[cmds.file( x, q=1, namespace=1)] = pymel.core.MReference(x)
		except: pass
	return res	
	
def createReference( *args, **kwargs ):
	"""file -reference"""
	kwargs['reference'] = True
	return pymel.core.MReference(cmds.file(*args, **kwargs))

def loadReference( file, refNode, **kwargs ):
	"""file -loadReference"""
	kwargs['loadReference'] = refNode
	return pymel.core.MReference(cmds.file(file, **kwargs))
		
def exportAll( *args, **kwargs ):
	"""file -exportAll"""
	kwargs['exportAll'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def exportAnim( *args, **kwargs ):
	"""file -exportAnim"""
	kwargs['exportAnim'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def exportAnimFromReference( *args, **kwargs ):
	"""file -exportAnimFromReference"""
	kwargs['exportAnimFromReference'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def exportAsReference( *args, **kwargs ):
	"""file -exportAsReference"""
	kwargs['exportAsReference'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	return pymel.core.MReference(cmds.file(*args, **kwargs))

def exportSelected( *args, **kwargs ):
	"""file -exportSelected"""
	kwargs['exportSelected'] = True
	try:
		kwargs['type'] = _getTypeFromExtension(args[0])
	except KeyError: pass
	return pymel.core.MPath(cmds.file(*args, **kwargs))
	
def exportSelectedAnim( *args, **kwargs ):
	"""file -exportSelectedAnim"""
	kwargs['exportSelectedAnim'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))
	
def exportSelectedAnimFromReference( *args, **kwargs ):
	"""file -exportSelectedAnimFromReference"""
	kwargs['exportSelectedAnimFromReference'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def importFile( *args, **kwargs ):
	"""file -import"""
	kwargs['import'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def newFile( *args, **kwargs ):
	"""file -newFile"""
	kwargs['newFile'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))

def openFile( *args, **kwargs ):
	"""file -open"""
	kwargs['open'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))	

def renameFile( *args, **kwargs ):
	"""file -rename"""
	kwargs['rename'] = True
	return pymel.core.MPath(cmds.file(*args, **kwargs))
	
def saveAs(filepath, **kwargs):
	cmds.file( rename=filepath )
	kwargs['save']=True
	return pymel.core.MPath(cmds.file(**kwargs) )
