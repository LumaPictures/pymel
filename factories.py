import sys, path, types
import pymel
import pymel.ctx
import pymel.core
import pymel.ui
try:
	import maya.cmds as cmds
except ImportError: pass
import util, helpDocs

"This module is used by pymel to automatically generate many of its functions and classes"

#-----------------------
# Function Factory
#-----------------------

def _addDocs(inObj, newObj, flagDocs):
	try:
		docstring = 'Flags:\n'
		for flag in sorted(flagDocs.keys()):
			docs = flagDocs[flag]

			docstring += '%s (%s)\n' % (flag, docs['shortname'])
			if docs['modes']:
				docstring += '    [%s]\n' % (', '.join(docs['modes']))
			docstring += '    %s\n' %  docs['docstring']
	
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
		
def functionFactory( inFunc, returnFunc, moduleName='pymel', flagDocs=None ):
	"""create a new function, apply the given returnFunc to the results (if any), 
	and add to the module given by 'moduleName'.  Use pre-parsed command documentation
	to add to __doc__ strings for the command."""
	
	
	commandFlags = _getCommandFlags(flagDocs)
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
			if 'query' not in kwargs and 'q' not in kwargs: # and 'edit' not in kwargs and 'e' not in kwargs:
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
			if 'query' not in kwargs and 'q' not in kwargs: # and 'edit' not in kwargs and 'e' not in kwargs:
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
	
	_addDocs( inFunc, newFunc, flagDocs )
	newFunc.__name__ = inFunc.__name__

	newFunc.__module__ = moduleName
	return newFunc

				
#-----------------------
# Class Factory
#-----------------------
	
def _makeCreateFlagCmd( cls, inFunc, flag, docstring='' ):
	def f(self): return inFunc( self,  **{'edit':True, flag:True} )
	f.__name__ = flag
	if docstring:
		f.__doc__ = docstring
	setattr( cls, flag, f )

def _makeQueryFlagCmd( cls, name, inFunc, flag, docstring='' ):
	#name = 'get' + flag[0].upper() + flag[1:]
	def f(self, **kwargs):
		kwargs['query']=True
		kwargs[flag]=True 
		return inFunc( self, **kwargs )
	
	f.__name__ = name
	if docstring:
		f.__doc__ = docstring
	setattr( cls, name, f )

def _makeEditFlagCmd( cls, name, inFunc, flag, docstring='' ):
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
	setattr( cls, name, f )


def classFactory( inFunc, clsName, moduleName='pymel', baseCls=object, flagDocs=None ):
	
	# use existing class
	if baseCls.__name__.endswith('_'):
		cls = baseCls
		cls.__name__ = clsName
	# create a new class
	else:
		cls = type( clsName, (baseCls,), {} )
	#cmdFile = path.path( util.moduleDir() / 'commands' / inFunc.__name__ )
	try:
		for flag, flagInfo in flagDocs.items():
			#if 'command' in flag.lower():
			#	print inFunc.__name__, flag
				 		
			if flag in ['query', 'edit']:
				continue
			modes = flagInfo['modes']
			if 'query' in modes:
				methodName = 'get' + util.capitalize(flag)
				if not hasattr( baseCls, methodName ):
					_makeQueryFlagCmd( cls, methodName, inFunc, 
							flag, flagInfo['docstring'] )
	
			# edit command, if there is a corresponding query we use the 'set' prefix. otherwise, not.			
			if 'edit' in modes and 'query' in modes:
				methodName = 'set' + util.capitalize(flag)
				if not hasattr( baseCls, methodName ):
					_makeEditFlagCmd( cls, methodName, inFunc, 
							flag, flagInfo['docstring'] )
				
			elif 'edit' in modes:
				if not hasattr( baseCls, flag ):
					_makeEditFlagCmd( cls, flag, inFunc, flag, flagInfo['docstring'] )
			
	except KeyError:
		print "command docs don't exist for '%s'" % inFunc.__name__
		
	cls.__module__ = moduleName
	return cls
	
def createPymelObjects():
	
	moduleName = 'pymel'
	module = __import__(moduleName)
	returnMap = {}
	#for funcName, v in helpDocs.commandHelp.items():
	#for funcName, v in helpDocs.buildMayaCmdsArgList().items():
	for funcName, args, classData in helpDocs.buildMayaCmdsArgList():
		
		if funcName in ['eval',	'file', 'filter', 'help', 'quit']:
			continue
	

			
		# func, args, (usePyNode, baseClsName, nodeName)
		# args = dictionary of command flags and their data
		# usePyNode = determines whether the class returns its 'nodeName' or uses PyNode to dynamically return
		# baseClsName = for commands which should generate a class, this is the name of the superclass to inherit
		# nodeName = most creation commands return a node of the same name, this option is provided for the exceptions
			
		try:
			func = getattr(pymel.core, funcName)
			
		except AttributeError:
			try:
				func = getattr(cmds,funcName)
				
				# if the function is not a builtin, add it to the pymel module.
				# docstrings will be added below
				if type(func) == types.FunctionType:
					module.__dict__[funcName] = func
			except NameError:
				return {}
			except AttributeError:
				print "could not find maya command:", funcName
				
		try:
			usePyNode, baseClsName, nodeName = classData
			try:
				baseCls = getattr(module, baseClsName)
			except (AttributeError, TypeError):
				#print "could not find %s.%s" % (moduleName, baseClsName)
				baseCls = unicode
			#except TypeError, msg:
			#	print "%s: %s.%s: %s" % (funcName, moduleName, baseClsName, msg)
			
			# create the new class
			clsName = util.capitalize( funcName )
			cls = classFactory( func, clsName, moduleName, baseCls, args)
					
			module.__dict__[clsName] = cls

			if usePyNode:
				#print funcName, "PyNode wrapping"
				module.__dict__[funcName] = functionFactory( func, pymel.core.PyNode, moduleName, args )
			else:
				#print funcName, "wrapping to return newly generated class"		
				module.__dict__[funcName] = functionFactory( func, cls, moduleName, args )
			
			if nodeName:		
				returnMap[nodeName] = cls
			
		# do not create a new class
		except ValueError:

			# create a wrapped function
			if type(func) == types.BuiltinFunctionType:
				#if usePyNode:
				#	module.__dict__[funcName] = functionFactory( func, pymel.core.PyNode, moduleName, args )
				#else:
				#print funcName, "lightly wrapping builtin function"
				module.__dict__[funcName] = functionFactory( func, None, moduleName, args )
					
			# add documentation string to existing function	
			elif type(func) == types.FunctionType:
				#print funcName, "adding Docs to core function"
				_addDocs( func, func, args )
					
	pymel.core.returnMap.update(returnMap)
	return returnMap


#del maya.cmds
		