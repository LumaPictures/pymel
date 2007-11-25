
import sys, os, os.path
from path import *
#from maya.cmds import encodeString

# Singleton classes can be derived from this class
class Singleton(object):
	def __new__(cls, *p, **k):
		if not '_the_instance' in cls.__dict__:
			cls._the_instance = object.__new__(cls)
		return cls._the_instance
		
#-----------------------------------------------
#  Pymel Internals
#-----------------------------------------------
def pythonToMel(arg):
	if isinstance(arg,basestring):
		return '"%s"' % cmds.encodeString(arg)
	elif util.isIterable(arg):
		return '{%s}' % ','.join( map( pythonToMel, arg) ) 
	return unicode(arg)
			
def capitalize(s):
	return s[0].upper() + s[1:]
					
def isIterable( obj ):
	return hasattr(obj,'__iter__') and not isinstance(obj,basestring)

def convertListArgs( args ):
	if len(args) == 1 and _isIterable(args[0]):
		return tuple(args[0])
	return args	

# Completely flatten a multi-list argument so that in can be passed as
# a list of arguments to a command.
# TODO : flatten hierarchy trees the same way, depth first or breadth first           
def expandListArgs( *args, **kwargs ) :
    """ \'Flattens\' the arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments. A depth limit can be specified.
        ex: expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'], limit=2 )
        Result: ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'] )
        Result: ('a', 'b', 'c', 'd', 'e', 'f', 'g') """
    
    cargs = tuple()
    l = kwargs.get('limit', None)
    try :
        l -= 1
    except :
        pass
    cont = (l is None or l>=0)
    for arg in args :
        if isIterable(arg) and cont :
            nargs = tuple(arg)
            nkw = {'limit':l}
            cargs += expandListArgs( *nargs, **nkw )
        else :
            cargs += (arg,)
    return cargs

# Same behavior as expandListArg but implemented as an Python iterator, for huge lists
# it would be more memory efficient            
def iterateListArgs( *args, **kwargs ) :
    """ Iterates through all arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments. A depth limit can be specified.
        ex: expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'], limit=2 )
        Result: ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'] )
        Result: ('a', 'b', 'c', 'd', 'e', 'f', 'g') """
    
    l = kwargs.get('limit', None)
    try :
        l -= 1
    except :
        pass
    cont = (l is None or l>=0)
    for arg in args :
        if isIterable(arg) and cont :
            nargs = tuple(arg)
            nkw = {'limit':l}
            for a in iterateListArgs( *nargs, **nkw ) :
                yield a
        else :
            yield arg

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

# Will test initialize maya standalone if necessary (like if scripts are run from an exernal interpeter)
# returns True if Maya is available, False either
def mayaInit () :
    result = False
    if not os.environ.has_key('MAYA_ENV_VERSION') :
        print "Maya environement variables not (yet) set"        
        # envMaya.setMayaEnv ()
        # print "Maya environement variables reset"

    # test that Maya actually is loaded
    if sys.modules.has_key('maya.cmds') :
        result = True
    else :
        try :
            import maya.cmds as cmds #@UnresolvedImport
            result = sys.modules.has_key('maya.cmds')
        except :
            if not sys.modules.has_key('maya.standalone') :
                try :
                    import maya.standalone #@UnresolvedImport
                    maya.standalone.initialize(name="python")
                    result = True
                except :
                    result = False

    return result

def toZip( directory, zipFile ):
	"""Sample for storing directory to a ZipFile"""
	import zipfile

	zipFile = path(zipFile)
	if zipFile.exists(): zipFile.remove()
	
	z = zipfile.ZipFile(
		zipFile, 'w', compression=zipfile.ZIP_DEFLATED
	)
	if not directory.endswith(os.sep):
		directory += os.sep
		
	directory = path(directory)
	
	for subdir in directory.dirs('[a-z]*') + [directory]: 
		for fname in subdir.files('[a-z]*'):
			archiveName = fname.replace( directory, '' )
			print "adding ", archiveName
			z.write( fname, archiveName, zipfile.ZIP_DEFLATED )
	z.close()
	return zipFile

def release( username=None, password = None):
	import pymel.examples.example1
	import pymel.examples.example2
	import googlecode
	
	baseDir = moduleDir()
	for d in baseDir.dirs():
		for f in d.files('*.pyc') + baseDir.files('*.pyc'):
			print "removing", f
			f.remove()
		for f in d.files('.*') + baseDir.files('.*'):
			print "removing", f
			f.remove()
	
	ver = str(pymel.__version__)
	zipFile = baseDir.parent / 'pymel-%s.zip' % ver
	print "zipping up %s into %s" % (baseDir, zipFile)
	toZip( 	baseDir, zipFile )
	
	if username and password:
		print "uploading to googlecode"
		googlecode.upload(zipFile, 'pymel', username, password, 'pymel ' + str(pymel.__version__), 'Featured')
		print "done"