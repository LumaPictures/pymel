
import sys, os, os.path, re
from exceptions import *
from path import path
import envparse


#from maya.cmds import encodeString

# Singleton classes can be derived from this class
# You can derive from other classes as long as Singleton comes first (and class doesn't override __new__
# >>> class uniqueImmutableDict(Singleton, dict) :
# >>> 	def __init__(self, value) :
# >>>		# will only be initialied once
# >>>		if not len(self):
# >>>			super(uniqueDict, self).update(value)
# >>>    	else :
# >>>    		raise TypeError, "'"+self.__class__.__name__+"' object does not support redefinition"
# >>>   # You'll want to override or get rid of dict herited set item methods
class Singleton(object) :
	def __new__(cls, *p, **k):
		if not '_the_instance' in cls.__dict__:
			cls._the_instance = super(Singleton, cls).__new__(cls)
		return cls._the_instance

class psuedoUnicode(object):
	"""to reduce the chance of clashes between methods and attributes, _BaseObj could inherit this class, which
	behaves exactly like a unicode and yet has none of its public methods."""
	
	def __init__( self, name ):
		self.__name = unicode(name)
	def __unicode__( self ):
		return self.__name
	def __repr__(self):
		return "%s('%s')" % (self.__class__.__name__, self)
	def __str__( self ):
		return unicode.__str__(self.__name)
	def __hash__(self):
		return unicode.__hash__( self.__name )
	def __lt__(self, other):
		return unicode.__lt__(self.__name, other)		
	def __le__(self, other):
		return unicode.__le__(self.__name, other)	
	def __eq__(self, other):
		return unicode.__eq__(self.__name, other)	
	def __ne__(self, other):
		return unicode.__ne__(self.__name, other)	
	def __gt__(self, other):
		return unicode.__gt__(self.__name, other)	
	def __ge__(self, other):
		return unicode.__ge__(self.__name, other)
	def __nonzero__(self):
		return unicode.__nonzero__(self.__name)

#-----------------------------------------------
#  Pymel Internals
#-----------------------------------------------
def pythonToMel(arg):
	if isinstance(arg,basestring):
		return '"%s"' % cmds.encodeString(arg)
	elif isIterable(arg):
		return '{%s}' % ','.join( map( pythonToMel, arg) ) 
	return unicode(arg)
			
def capitalize(s):
	return s[0].upper() + s[1:]
					
def isIterable( obj ):
	return hasattr(obj,'__iter__') and not isinstance(obj,basestring)

def convertListArgs( args ):
	if len(args) == 1 and isIterable(args[0]):
		return tuple(args[0])
	return args	

# Completely flatten a multi-list argument so that in can be passed as
# a list of arguments to a command.
# TODO : flatten hierarchy trees the same way, depth first or breadth first           
def expandListArgs( *args, **kwargs ) :
    """ \'Flattens\' the arguments list: recursively replaces any iterable argument in *args by a tuple of its
    elements that will be inserted at its place in the returned arguments. A depth limit can be specified.
        >>> expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'], limit=2 )
        >>> ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'] )
        >>> ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        Note that on a pymel tree it's the equivalent of doing a preorder traversal : [k for k in iter(theTree)]"""
    
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
        >>> expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'], limit=2 )
        >>> ('a', 'b', ['c', 'd'], 'e', 'f', 'g')
        >>> expandListArgs( ['a', ['b', ['c', 'd']]], 'e', ['f', 'g'] )
        >>> ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        Note that on a pymel tree it's the equivalent the default preorder traversal iterator: iter(theTree)"""
    
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

# A source commande that will search for the Python script "file" in the specified path
# (using the system path if none is provided) path and tries to call execfile() on it
def source (file, searchPath=None, recurse=False) :
    """Looks for a python script in the specified path (uses system path if no path is specified)
        and executes it if it's found """
    filepath = os.path(file)
    filename = filepath.basename()
    if searchPath is None :
        searchPath=sys.path
    if not util.isIterable(searchPath) :
        searchPath = list((searchPath,))
    itpath = iter(searchPath)
    #print "looking for file as: "+filepath
    while not filepath.exists() :
        try :
            p = os.path(itpath.next()).realpath().abspath()
            filepath = filepath.joinpath(p, filename)
            #print 'looking for file as: '+filepath
            if recurse and not filepath.exists() :
                itsub = os.walk(p)
                while not filepath.exists() :
                    try :
                        root, dirs, files = itsub.next()
                        itdirs = iter(dirs)
                        while not filepath.exists() :
                            try :
                                filepath = filepath.joinpath(Path(root), os.path(itdirs.next()), filename)
                                #print 'looking for file as: '+filepath
                            except :
                                pass
                    except :
                        pass
        except :
            raise ValueError, "File '"+filename+"' not found in path"
            # In case the raise exception is replaced by a warning don't forget to return here
            return
    # print "Executing: "+filepath
    return execfile(filepath)

# parse the Maya.env file and set the environement variablas and python path accordingly
def parseMayaenv(envLocation=None, version=None) :
	""" parse the Maya.env file and set the environement variablas and python path accordingly.
		You can specify a location for the Maya.env file or the Maya version"""
	name = 'Maya.env'
	if os.name == 'nt' :
		maya = 'maya.exe'
		sep = ';'
	else :
		maya = 'maya.bin'
		sep = ':'
	envPath = None
	if envLocation :
		envPath = envLocation
		if not os.path.isfile(envPath) :
			envPath = os.path.join(envPath, name)
			
	# no Maya.env specified, we look for it in MAYA_APP_DIR
	if not envPath or not envPath.isfile() :
		if not os.environ.has_key('MAYA_APP_DIR') :
			home = os.environ.get('HOME', None)
			if not home :
				warnings.warn("Neither HOME nor MAYA_APP_DIR is set, unable to find location of Maya.env", ExecutionWarning)
				return False
			else :
				maya_app_dir = os.path.join(home, 'maya')
		else :
			maya_app_dir = os.environ['MAYA_APP_DIR']
		# try to find which version of Maya should be initialized
		if not version :
			# try to query version, will only work if reparsing env from a working Maya
			try :
				from maya.cmds import about        
				version = eval("about(version=True)");
			except :
				# get version from MAYA_LOCATION then
				try :
					version = re.search( 'maya([\d.]+)', os.environ['MAYA_LOCATION']).group(1)		
				except :
					# if run from Maya provided mayapy / python interpreter, can guess version
					startPath = os.path.dirname(sys.executable)
					if os.path.isfile(os.path.join(startPath, maya)) :
						version = os.path.basename(startPath)
					else :
						print "Unable to determine which verson of Maya should be initialized, trying for Maya.env in %s" % maya_app_dir
		# look first for Maya.env in 'version' subdir of MAYA_APP_DIR, then directly in MAYA_APP_DIR
		if version and os.path.isfile(os.path.join(maya_app_dir, version, name)) :
			envPath = os.path.join(maya_app_dir, version, name)
		else :
			envPath = os.path.join(maya_app_dir, name)

	# finally if we have a possible Maya.env, parse it
	if os.path.isfile(envPath) :
		try :
			envFile = open(envPath)
		except :
			warnings.warn ("Unable to open Maya.env file %s" % envPath, ExecutionWarning)
			return False
		success = False
		try :
			envTxt = envFile.read()
			envVars = envparse.parse(envTxt)
			# update env vars
			for v in envVars :
				#print "%s was set or modified" % v
				os.environ[v] = envVars[v]
			# add to syspath
			if envVars.has_key('PYTHONPATH') :
				#print "sys.path will be updated"
				plist = os.environ['PYTHONPATH'].split(sep)
				for p in plist :
					if not p in sys.path :
						sys.path.append(p)
			success = True
		finally :
			envFile.close()
			return success
	else :
		if version :
			print"Found no suitable Maya.env file for Maya version %s" % version
		else :
			print"Found no suitable Maya.env file"
		return False
				
# Will test initialize maya standalone if necessary (like if scripts are run from an exernal interpeter)
# returns True if Maya is available, False either
def mayaInit(forversion=None) :
	""" Try to init Maya standalone module, use when running pymel from an external Python inerpreter,
	it is possible to pass the desired Maya version number to define which Maya to initialize """

	# test that Maya actually is loaded and that commands have been initialized,for the requested version		
	try :
		from maya.cmds import about        
		version = eval("about(version=True)");
	except :
		version = None

	if forversion :
		if version == forversion :
			return True
		else :
			print "Maya is already initialized as version %s, initializing it for a different version %s" % (version, forversion)
	elif version :
			return True
				
	# reload env vars, define MAYA_ENV_VERSION in the Maya.env to avoid unneeded reloads
	envVersion = os.environ.get('MAYA_ENV_VERSION', None)
	
	if (forversion and envVersion!=forversion) or not envVersion :
		if not parseMayaenv(version=forversion) :
			print "Could not read or parse Maya.env file"
	if not sys.modules.has_key('maya.standalone') or version != forversion:
		try :
			import maya.standalone #@UnresolvedImport
			maya.standalone.initialize(name="python")
		except :
			pass
	try :
		from maya.cmds import about    
		reload(maya.cmds) #@UnresolvedImport
		version = eval("about(version=True)")
		return (forversion and version==forversion) or version
	except :
		return False

def timer( command='pass', number=10, setup='import pymel' ):
	import timeit
	t = timeit.Timer(command, setup)
	time = t.timeit(number=number)
	print "command took %.2f sec to execute" % time
	return time
	
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
	import ply.lex as lex
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