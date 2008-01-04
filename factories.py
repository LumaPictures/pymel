import path, util, sys, os, inspect, pickle, re, types
from examples.trees import *
#from networkx.tree import *
from HTMLParser import HTMLParser
try:
	import maya.cmds as cmds
except ImportError: pass

moduleName = 'pymel'
module = __import__(moduleName, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

#---------------------------------------------------------------
#		Doc Parser
#---------------------------------------------------------------
	
class CommandDocParser(HTMLParser):
	def __init__(self):
		self.flags = {}  # shortname, argtype, docstring, and a list of modes (i.e. edit, create, query)
		self.currFlag = ''
		# iData is used to track which type of data we are putting into flags, and corresponds with self.datatypes
		self.iData = 0
		self.pcount = 0
		self.active = False  # this is set once we reach the portion of the document that we want to parse
		self.description = ''
		
		HTMLParser.__init__(self)
	
	def startFlag(self, data):
		#print self, data
		#assert data == self.currFlag
		self.iData = 0
		self.flags[self.currFlag] = {'longname': self.currFlag, 'shortname': None, 'argtype': None, 'docstring': '', 'modes': [] }
	
	def addFlagData(self, data):
		# shortname, argtype
		if self.iData == 0:
			self.flags[self.currFlag]['shortname'] = data
		elif self.iData == 1:
			self.flags[self.currFlag]['argtype'] = data	
		else:
			#self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).strip() + " "
			
			
			data = data.replace( 'In query mode, this flag needs a value.', '' )
			data = data.replace( 'Flag can appear in Create mode of command', '' )
			data = data.replace( 'Flag can appear in Edit mode of command', '' )
			data = data.replace( 'Flag can appear in Query mode of command', '' )
			data = data.replace( '\r\n', ' ' ).lstrip()
			
			self.flags[self.currFlag]['docstring'] += data
		self.iData += 1
		
	def endFlag(self):
		# cleanup last flag
		#data = self.flags[self.currFlag]['docstring']
		
		#print "ASSERT", data.pop(0), self.currFlag
		#self.flags[self.currFlag]['shortname'] = data.pop(0)
		self.iData = 0
		
	def handle_starttag(self, tag, attrs):
		#print "begin: %s tag: %s" % (tag, attrs)
		if not self.active:
			if tag == 'a' and attrs[0][1] == 'hFlags':
				#print 'ACTIVE'
				self.active = 'flag'
					
		elif tag == 'a' and attrs[0][0] == 'name':
			self.endFlag()
			#print "NEW FLAG", self.currFlag
			self.currFlag = attrs[0][1][4:]
			
	
		elif tag == 'img' and len(attrs) > 4:
			#print "MODES", attrs[1][1]
			self.flags[self.currFlag]['modes'].append(attrs[1][1])
		elif tag == 'h2':
			self.active = False
			
	def handle_endtag(self, tag):
		#if tag == 'p' and self.active == 'command': self.active = False
		#print "end: %s" % tag
		if not self.active:
			if tag == 'p':
				if self.pcount == 3:
					self.active = 'command'
				else:
					self.pcount += 1
		
	def handle_data(self, data):
		if not self.active:
			return
		elif self.active == 'flag':	
			if self.currFlag:
				stripped = data.strip()
				if stripped == 'Return value':
					self.active=False
					return
					
				if data and stripped and stripped not in ['(',')', '=', '], [']:
					#print "DATA", data
			
					if self.currFlag in self.flags:				
						self.addFlagData(data)
					else:
						self.startFlag(data)
		elif self.active == 'command':
			self.description += data.replace( '\r\n', ' ' ).lstrip()
			#print data
			#self.active = False

def _mayaDocsLocation( version ):
	docLocation = path.path( os.environ.get("MAYA_LOCATION", '/Applications/Autodesk/maya%s/Maya.app/Contents' % version) )
	import platform
	if platform.system() == 'Darwin':
		docLocation = docLocation.parent.parent
	docLocation = path.path( docLocation / 'docs/Maya%s/en_US' % version )
	return docLocation
	
def getCmdInfo( command, version='8.5' ):
	"""Since many maya Python commands are builtins we can't get use getargspec on them.
	besides most use keyword args that we need the precise meaning of ( if they can be be used with 
	edit or query flags, the shortnames of flags, etc) so we have to parse the maya docs"""
	
	try:
		f = open( _mayaDocsLocation(version) / 'CommandsPython/%s.html' % (command) )	
		parser = CommandDocParser()
		parser.feed( f.read() )
		f.close()
		return parser.description, parser.flags
	except IOError:
		#print "could not find docs for %s" % command
		return ('',{})
		#raise IOError, "cannot find maya documentation directory"

class NodeHierarchyDocParser(HTMLParser):
				
	def __init__(self):
		self.currentTag = None
		self.depth = 0
		self.lastDepth = -1
		self.tree = None
		self.currentLeaves = []
		
		HTMLParser.__init__(self)
	def handle_starttag(self, tag, attrs):
		self.currentTag = tag
	
	def handle_data(self, data):
		if self.currentTag == 'tt':
			self.lastDepth = self.depth
			self.depth = data.count('>')
		if self.currentTag == 'a':
			data = data.lstrip()
			
			if self.depth == self.lastDepth:				
				#print "adding to level", self.depth, data
				self.tree[ self.depth ].append( data )
				
			elif self.depth > self.lastDepth:
				#print "starting new level", self.depth, data
				try:
					self.tree.append( [data] )
				except AttributeError:
					self.tree = [data]
					
			elif self.depth < self.lastDepth:
				for i in range(0, self.lastDepth-self.depth):
					branch = self.tree.pop()
					#print "closing level", self.lastDepth
					self.tree[-1].append( branch )
				
				#print "adding to level", self.depth, data
				self.tree[ self.depth ].append( data )
	'''		
	def handle_data(self, data):
		if self.currentTag == 'tt':
			self.lastDepth = self.depth
			self.depth = data.count('>')
			
		if self.currentTag == 'a':
			data = data.lstrip()
			
			if self.depth == self.lastDepth:				
				#print "adding to level", self.depth, data
				self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )
				self.currentLeaves[ self.depth ] = data
				
			elif self.depth > self.lastDepth:
				#print "starting new level", self.depth, data
				try:
					self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )
					
				except AttributeError:
					self.tree = RootedTree(data)
					#self.tree = DirectedTree()	
					#self.tree.add_node( data )				
				self.currentLeaves.append( data )
					
			elif self.depth < self.lastDepth:
				for i in range(0, self.lastDepth-self.depth):
					self.currentLeaves.pop()
					#print "closing level", self.lastDepth
					#self.tree[-1].append( branch )
				
				#print "adding to level", self.depth, data
				self.tree.add_leaf( self.currentLeaves[ self.depth-1 ], data )		
				self.currentLeaves[ self.depth ] = data
	'''
		
def printTree( tree, depth=0 ):
	for branch in tree:
		if util.isIterable(branch):
			printTree( branch, depth+1)
		else:
			print '> '*depth, branch
			
def _getNodeHierarchy( version='8.5' ):
	f = open( _mayaDocsLocation(version) / 'Nodes/index_hierarchy.html' )	
	parser = NodeHierarchyDocParser()
	parser.feed( f.read() )
	f.close()
	return parser.tree
	
#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------

# creation commands whose names do not match the type of node they return require this dict
# to resolve which command the class should wrap 
nodeTypeToCommandMap = {
	#'failed' : 'clip',
	#'failed' : 'clipSchedule',
	'airField' : 'air',
	'dragField' : 'drag',
	'emitter' : 'emitter',
	'turbulenceField' : 'turbulence',
	#'failed' : 'effector',
	'volumeAxisField' : 'volumeAxis',
	'uniformField' : 'uniform',
	'gravityField' : 'gravity',
	#'failed' : 'event',
	#'failed' : 'pointCurveConstraint',
	#'failed' : 'deformer',
	#'failed' : 'constrain',
	'locator' : 'spaceLocator',
	'vortexField' : 'vortex',
	'makeNurbTorus' : 'torus',
	'makeNurbCone' : 'cone',
	'makeNurbCylinder' : 'cylinder',
	#'failed' : 'curve',
	'makeNurbSphere' : 'sphere',
	'makeNurbCircle' : 'circle',
	'makeNurbPlane' : 'nurbsPlane',
	'makeNurbsSquare' : 'nurbsSquare',
	'makeNurbCube' : 'nurbsCube'
}

def _getUICommands():
	f = open(util.moduleDir() / 'misc/commandsUI', 'r')
	cmds = f.read().split('\n')
	f.close()
	return cmds
				
def buildMayaCmdsArgList() :
	"""Build and save to disk the list of Maya Python commands and their arguments"""
	try:
		# removes extra version info which should not affect the list of commands ( x64, Service Pack 1, P04 )
		try:
			ver = re.match( "([\d.]+)", cmds.about( version=1 )).group(1)#@UndefinedVariable
		except AttributeError:
			ver = cmds.about(version=True).split()[0] 
		
	except (AttributeError, NameError):
		return []
		
	newPath = util.moduleDir() / 'mayaCmdsList'+ver+'.bin'
	cmdlist = {}
	try :
		file = newPath.open(mode='rb')
		try :
			cmdlist,nodeHierarchy,uiClassList = pickle.load(file)
			nodeHierarchyTree = IndexedTree(nodeHierarchy)
		except :
			print "Unable to load the list of Maya commands from '"+file.name+"'"
		
		file.close()
	except :
		print "Unable to open '"+newPath+"' for reading the list of Maya commands"
	
	if not len(cmdlist): # or not isinstance(cmdlist,list):		
		
		print "Rebuilding the list of Maya commands..."
		
		nodeHierarchy = _getNodeHierarchy(ver)
		nodeHierarchyTree = IndexedTree(nodeHierarchy)
		uiClassList = _getUICommands()
		cmdlist = dict( inspect.getmembers(cmds, callable) )
		for funcName in cmdlist :	

			description, args = getCmdInfo(funcName, ver)
			
			# determine to which module this function belongs
			if funcName in ['eval',	'file', 'filter', 'help', 'quit']:
				module = None
			elif funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
				module = 'ctx'
			elif funcName in uiClassList:
				module = 'ui'
			elif funcName in nodeHierarchyTree or funcName in nodeTypeToCommandMap.values():
				module = 'node'
			else:
				module = 'core'
				
			cmdlist[funcName] = { 'type': module, 'flags': args, 'description' : description }
			
			'''
			# func, args, (usePyNode, baseClsName, nodeName)
			# args = dictionary of command flags and their data
			# usePyNode = determines whether the class returns its 'nodeName' or uses PyNode to dynamically return
			# baseClsName = for commands which should generate a class, this is the name of the superclass to inherit
			# nodeName = most creation commands return a node of the same name, this option is provided for the exceptions
			try:
				cmdlist[funcName] = args, pymelCmdsList[funcName] )		
			except KeyError:
				# context commands generate a class based on unicode (which is triggered by passing 'None' to baseClsName)
				if funcName.startswith('ctx') or funcName.endswith('Ctx') or funcName.endswith('Context'):
		 			cmdlist[funcName] = (funcName, args, (False, None, None) )
				else:
					cmdlist[funcName] = (funcName, args, () )
			'''
		
		uiClassList = map( util.capitalize, uiClassList )
				
		try :
			file = newPath.open(mode='wb')
			try :
				pickle.dump( (cmdlist,nodeHierarchy,uiClassList),  file, 2)
				print "done"
			except:
				print "Unable to write the list of Maya commands to '"+file.name+"'"
			file.close()
		except :
			print "Unable to open '"+newPath+"' for writing"

	
	return (cmdlist,nodeHierarchyTree,uiClassList)
					
#---------------------------------------------------------------


		
cmdlist, nodeHierarchy, uiClassList = buildMayaCmdsArgList()

#-----------------------
# Function Factory
#-----------------------

def _addDocs(inObj, newObj, cmdInfo ):
	try:
		docstring = cmdInfo['description'] + '\n\n'
		flagDocs = cmdInfo['flags']
		docstring += 'Flags:\n'
		for flag in sorted(flagDocs.keys()):
			docs = flagDocs[flag]

			label = '    - %s (%s)' % (flag, docs['shortname'])
			docstring += label + '\n'
			#docstring += '~'*len(label) + '\n'
			if docs['modes']:
				docstring += '        - %s\n' % (', '.join(docs['modes']))
			docstring += '        - %s\n' %  docs['docstring']
	
		if inObj.__doc__:
			docstring = inObj.__doc__ + '\n' + docstring
		newObj.__doc__ = docstring
			
	except KeyError:
		print "could not find help docs for", inObj

def _getCommandFlags(flagDocs):
	commandFlags = []
	for flag, data in flagDocs.items():
		if 'command' in flag.lower():
			commandFlags += [flag, data['shortname']]
	return commandFlags

_thisModule = __import__('pymel.core', globals(), locals(), [''])		
	
def functionFactory( funcName, returnFunc ):
	"""create a new function, apply the given returnFunc to the results (if any), 
	and add to the module given by 'moduleName'.  Use pre-parsed command documentation
	to add to __doc__ strings for the command."""
	
	try:
		inFunc = getattr(_thisModule, funcName)			
	except AttributeError:
		try:
			inFunc = getattr(cmds,funcName)
		except AttributeError:
			return

	cmdInfo = cmdlist[funcName]

	# if the function is not a builtin and there's no return command to map, just add docs
	if type(inFunc) == types.FunctionType and returnFunc is None:
		_addDocs( inFunc, inFunc, cmdInfo )
		return inFunc
	
	elif type(inFunc) == types.BuiltinFunctionType or ( type(inFunc) == types.FunctionType and returnFunc ):					
	
		commandFlags = _getCommandFlags(cmdInfo['flags'])
		if commandFlags:
			#print inFunc.__name__, commandFlags		
			def newFunc( *args, **kwargs):
				# wrap ui callback commands to ensure that the booleans True and False are returned instead of strings u'true', and u'false'
				for key in commandFlags:
					try:
						cb = kwargs[ key ]
						if hasattr(cb, '__call__'):
							def callback(*args):
								newargs = []
								for arg in args:
									if arg == 'false': arg = False
									elif arg == 'true': arg = True
									newargs.append(arg)
								newargs = tuple(newargs)
								return cb( *newargs )
							kwargs[ key ] = callback
					except KeyError: pass
				
				res = apply( inFunc, args, kwargs )
				if not kwargs.get('query', kwargs.get('q',False)): # and 'edit' not in kwargs and 'e' not in kwargs:
					if isinstance(res, list):				
						try:
							res = map( returnFunc, res )
						except: pass
				
					elif res:
						try:
							res = returnFunc( res )
						except: pass
				return res
	
		elif returnFunc:
			def newFunc( *args, **kwargs):
				res = apply( inFunc, args, kwargs )
				if not kwargs.get('query', kwargs.get('q',False)): # and 'edit' not in kwargs and 'e' not in kwargs:
					if isinstance(res, list):				
						try:
							res = map( returnFunc, res )
						except: pass
				
					elif res:
						try:
							res = returnFunc( res )
						except: pass
				return res
		else:
			def newFunc(*args, **kwargs): return apply(inFunc, args, kwargs)
	
		_addDocs( inFunc, newFunc, cmdInfo )
		newFunc.__name__ = inFunc.__name__

		return newFunc
	#else:
	#	print "function %s is of incorrect type: %s" % (funcName, type(inFunc) )
			
def makeCreateFlagCmd( inFunc, flag, docstring='' ):
	def f(self): return inFunc( self,  **{'edit':True, flag:True} )
	f.__name__ = flag
	if docstring:
		f.__doc__ = docstring
	return f

def makeQueryFlagCmd( name, inFunc, flag, docstring='' ):
	#name = 'get' + flag[0].upper() + flag[1:]
	def f(self, **kwargs):
		kwargs['query']=True
		kwargs[flag]=True 
		return inFunc( self, **kwargs )
	
	f.__name__ = name
	if docstring:
		f.__doc__ = docstring
	return f

def makeEditFlagCmd( name, inFunc, flag, docstring='' ):
	#name = 'set' + flag[0].upper() + flag[1:]	
	def f(self, val, **kwargs): 
		kwargs['edit']=True
		kwargs[flag]=val 
		try:
			return inFunc( self, **kwargs )
		except TypeError:
			kwargs.pop('edit')
			return inFunc( self, **kwargs )
			
	f.__name__ = name
	if docstring:
		f.__doc__ = docstring
	return f


		
class metaNode(type) :
	"""
	A metaclass for creating classes based on node type.  If no bases are passed, the superclass is determined
	from the node hierarchy parsed from the maya docs.  All non-existent superclasses will be created prior to
	creating the new class.  Methods will be added to the new classes based on info parsed from the docs on
	their command counterparts.

	"""

	
	def __new__(cls, classname, bases, classdict):
		
		nodeType = util.uncapitalize(classname)
		
		try:
			nodeType = nodeTypeToCommandMap.get( nodeType, nodeType )
			#if nodeHierarchy.children( nodeType ):
			#	print nodeType, nodeHierarchy.children( nodeType )
			cmdInfo = cmdlist[nodeType]
			
			try:	
				func = getattr(_thisModule, nodeType)

			except AttributeError:
				func = getattr(cmds,nodeType)
			
			# add documentation
			classdict['__doc__'] = 'class counterpart of function L{%s}\n\n%s\n\n' % (nodeType, cmdInfo['description'])
			
			for flag, flagInfo in cmdInfo['flags'].items():
 		
				if flag in ['query', 'edit']:
					continue
				modes = flagInfo['modes']
				if 'query' in modes:
					methodName = 'get' + util.capitalize(flag)
					if methodName not in classdict:
						classdict[methodName] = makeQueryFlagCmd( methodName, func, 
								flag, flagInfo['docstring'] )

				# edit command: if there is a corresponding query we use the 'set' prefix. 		
				if 'edit' in modes and 'query' in modes:
					methodName = 'set' + util.capitalize(flag)
					if methodName not in classdict:
						classdict[methodName] = makeEditFlagCmd( methodName, func, 
								flag, flagInfo['docstring'] )
				
				# edit command: if there is not a matching 'set' and 'get' pair, we use the flag name as the method name
				elif 'edit' in modes:
					methodName = flag
					if methodName not in classdict:
						classdict[methodName] = makeEditFlagCmd( methodName, func,
						 		flag, flagInfo['docstring'] )
					
		except KeyError: # on cmdlist[nodeType]
			pass
			
		return super(metaNode, cls).__new__(cls, classname, bases, classdict)
				
def makeDocs( mayaVersion='8.5' ):
	"internal use only"
	
	import re
	import epydoc.cli
	
	pymeldir = util.moduleDir()
	
	# generate epydocs
	os.chdir( pymeldir )
	sys.argv = [pymeldir, '--debug',  '--config=%s' % os.path.join( pymeldir, 'epydoc.cfg') ]
	epydoc.cli.cli(useLogger=False)
	
	return
	
	#---------------------------------------------------------------
	# skipping all this for now
	#---------------------------------------------------------------
	'''
	# copy over maya doc pages and link to them from the epydoc pages	
	docdir = pymeldir / 'docs'
	
	try:
		(docdir / 'CommandsPython').mkdir()
	except OSError:
		pass
	
	htmlFile = 'pymel-module.html'
	f = open( os.path.join( docdir, htmlFile), 'r'  )
	lines = f.readlines()
	f.close()
	
	reg = re.compile("(pymel-module.html#)([a-zA-Z0-9_]+)")
	for i, line in enumerate(lines):
		buf = reg.split( line )
		try:
			command = buf[2]
			localHelpFile = path( 'CommandsPython/' + command + '.html' )
			line = buf[0] + localHelpFile + buf[3]
			localHelpFile = docdir / localHelpFile
			if not localHelpFile.exists():				
				globalHelpFile = path( _mayaCommandHelpFile( command, mayaVersion ) )
				print "copying", globalHelpFile, localHelpFile
				globalHelpFile.copy( localHelpFile.parent )
				
		except: pass
		lines[i] = line 
	
	f = open( os.path.join(pymeldir, 'docs', htmlFile), 'w' ) 
	f.writelines(lines)
	f.close()
	'''
