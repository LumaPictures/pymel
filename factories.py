import sys, path
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

def functionFactory( inFunc, returnFunc=None, moduleName='pymel' ):
	"""create a new function, apply the given returnFunc to the results (if any), 
	and add to the module given by 'moduleName'.  Use pre-parsed command documentation
	to add to __doc__ strings for the command."""
	if returnFunc:
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
		def newFunc(*args, **kwargs): return apply(inFunc, *args, **kwargs)
	
	newFunc.__name__ = inFunc.__name__
	try:
		flagDocs = helpDocs.commandHelp[inFunc.__name__]
		docstring = 'Flags:\n'
		for flag in sorted(flagDocs.keys()):
			docs = flagDocs[flag]

			docstring += '%s (%s)\n' % (flag, docs['shortname'])
			if docs['modes']:
				docstring += '    [%s]\n' % (', '.join(docs['modes']))
			docstring += '    %s\n' %  docs['docstring']
		
			newFunc.__doc__ = inFunc.__doc__ + '\n' + docstring
	except KeyError:
		print "could not find help docs for", newFunc.__name__
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


def classFactory( inFunc, clsName, moduleName='pymel', baseCls=object ):
	
	if baseCls.__name__.endswith('_'):
		cls = baseCls
		cls.__name__ = clsName
	else:
		cls = type( clsName, (baseCls,), {} )
	#cmdFile = path.path( util.moduleDir() / 'commands' / inFunc.__name__ )
	try:
		cmdFlags = helpDocs.commandHelp[inFunc.__name__]

		for flag, flagInfo in cmdFlags.items():			
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
	

def createClasses( cmdFile, moduleName='pymel', returnGeneratedClass=True, runTest=False ):
	creationCmdsList =  util.moduleDir() / cmdFile
	
	module = __import__(moduleName)
	
	file = creationCmdsList.open( 'r' )
	creationReturnMap = {}
	for funcName in file:
		buf = funcName.split()
		
		# get the function object
		funcName = buf[0]
		
		# if the function has already been overloaded in pymel.core, use this one instead of the one in maya.cmds
		try:
			func = getattr(pymel.core, funcName)
		except AttributeError:
			try:
				func = getattr(cmds,funcName)
			except NameError:
				return {}
		
		# create a new class based on this function and wrap the function  			
		try:						
			baseClsName = buf[1]
			# base Class
			try:
				baseCls = getattr(module, baseClsName)
			except AttributeError:
				print "could not find %s.%s" % (moduleName, baseClsName)
				baseCls = unicode
		
			# alternate node name
			# use this when the name of the command and name of the node created differ
			# this is the name that PyNode will look for when casting node types to classes
			try:
				nodeName = buf[2]
			except IndexError: 
				nodeName = funcName
		
			
			clsName = util.capitalize( funcName )
			cls = classFactory( func, clsName, moduleName, baseCls)
	
				
			module.__dict__[clsName] = cls
			if returnGeneratedClass:
				module.__dict__[funcName] = functionFactory( func, cls, moduleName )
			else:
				module.__dict__[funcName] = functionFactory( func, pymel.core.PyNode, moduleName )
		
			creationReturnMap[nodeName] = cls
			pymel.core.returnMap[nodeName] = cls
		
		except IndexError:
			# just create a wrapped function, no new class
			module.__dict__[funcName] = functionFactory( func, pymel.core.PyNode, moduleName )
		
		#except NameError:
		#	print 'could not create class', funcName
	return creationReturnMap	

	
def ctxCommands():
	moduleName = 'pymel.ctx'
	commands = util.moduleDir() / 'commandsCtx'
	file = commands.open( 'r' )
	module = __import__(moduleName)
	for funcName in file:
		buf = funcName.split()
		funcName = buf[0]	
		try:
			func = getattr(cmds,funcName)
		except NameError:
			return
		module.__dict__[funcName] = functionFactory( func, None, moduleName )


#del maya.cmds
		