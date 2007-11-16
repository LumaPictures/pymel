
import sys, os, os.path
from path import *
#from maya.cmds import encodeString

#-----------------------------------------------
#  Pymel Internals
#-----------------------------------------------
def pythonToMel(arg):
	if isinstance(arg,basestring):
		return '"%s"' % cmds.encodeString(arg)
	elif util.isIterable(arg):
		return '{%s}' % ','.join( map( pythonToMel, arg) ) 
	return unicode(arg)
	
def mayaCommandHelpFile( command, version ):
	return '/Applications/Autodesk/maya%s/docs/Maya%s/en_US/CommandsPython/%s.html' % (version, version, command)
	
def release():
	import pymel.examples.example1
	import pymel.examples.example2
	
	baseDir = moduleDir()
	for d in baseDir.dirs():
		for f in d.files('*.pyc') + baseDir.files('*.pyc'):
			print "removing", f
			f.remove()
		for f in d.files('._*') + baseDir.files('._*'):
			print "removing", f
			f.remove()
			
			
def capitalize(s):
	return s[0].upper() + s[1:]
					
def isIterable( obj ):
	return hasattr(obj,'__iter__') and not isinstance(obj,basestring)

def convertListArgs( args ):
	if len(args) == 1 and _isIterable(args[0]):
		return tuple(args[0])
	return args	

def listForNone( res ):
	if res is None:
		return []
	return res

def cacheProperty(getter, attr_name, fdel=None, doc=None):
	"""a property type for getattr functions that only need to be called once per instance.
		future calls to getattr for this property will return the previous non-null value.
		attr_name is the name of an attribute in which to store the cached values"""
	def fget(obj):
		val = None
	
		if hasattr(obj,attr_name):			
			val = getattr(obj, attr_name)
			#print "cacheProperty: retrieving cache: %s.%s = %s" % (obj, attr_name, val)
			
		if val is None:
			#print "cacheProperty: running getter: %s.%s" %  (obj, attr_name)
			val = getter(obj)
			#print "cacheProperty: caching: %s.%s = %s" % (obj, attr_name, val)
			setattr(obj, attr_name, val )
		return val
				
	def fset(obj, val):
		#print "cacheProperty: setting attr %s.%s=%s" % (obj, attr_name, val)
		setattr(obj, attr_name, val)

	return property( fget, fset, fdel, doc)

def moduleDir():
	return path( sys.modules[__name__].__file__ ).parent

				