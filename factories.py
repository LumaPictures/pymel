import sys, path
import pymel
import pymel.ctx
import pymel.core
import pymel.ui
import maya.cmds as cmds
#import maya.cmds
import util, helpDocs

"This module is used by pymel to automatically generate many of its functions and classes"

#-----------------------
# Function Factory
#-----------------------

def functionFactory( inFunc, returnFunc, moduleName='pymel' ):
	def newFunc( *args, **kwargs):
		res = apply( inFunc, args, kwargs )
		if 'query' not in kwargs and 'q' not in kwargs: # and 'edit' not in kwargs and 'e' not in kwargs:
			if isinstance(res, list):
				
				try:
					res = map( returnFunc, res )
				except: pass
				
				"""
				try:
					res = pymel.core.PyNode( res[0] )
				except: pass
				"""
			elif res:
				try:
					res = returnFunc( res )
				except: pass
		return res
	newFunc.__name__ = inFunc.__name__
	try:
		newFunc.__doc__ = helpDocs.commandHelp[inFunc.__name__]['help']
	except:
		print "could not find help docs for", newFunc.__name__
	newFunc.__module__ = moduleName
	return newFunc

def functionFactory2( inFunc, returnClass ):
	def newFunc( *args, **kwargs):
		res = apply( inFunc, args, kwargs )
		if len(res) == 1:
			res[0] = pymel.Transform(res[0])
		elif len(res) == 2:
			res[0] = pymel.Transform(res[0])
			res[1] = returnClass(res[1])
		return res
	newFunc.__name__ = inFunc.__name__
	newFunc.__module__ = 'pymel'
	return newFunc
				
#-----------------------
# Class Factory
#-----------------------
	
def makeCreateFlagCmd( cls, inFunc, flag, docstring='' ):
	def f(self): return inFunc( self,  **{'edit':True, flag:True} )
	f.__name__ = flag
	if docstring:
		f.__doc__ = docstring
	setattr( cls, flag, f )

def makeQueryFlagCmd( cls, name, inFunc, flag, docstring='' ):
	#name = 'get' + flag[0].upper() + flag[1:]
	def f(self, **kwargs):
		kwargs['query']=True
		kwargs[flag]=True 
		return inFunc( self, **kwargs )
	
	f.__name__ = name
	if docstring:
		f.__doc__ = docstring
	setattr( cls, name, f )

def makeEditFlagCmd( cls, name, inFunc, flag, docstring='' ):
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
		cmdFlags = helpDocs.commandHelp[inFunc.__name__]['flagDocs']
		for flag, flagInfo in cmdFlags.items():			
			if flag in ['query', 'edit']:
				continue
			modes = flagInfo['modes']
			if 'query' in modes:
				methodName = 'get' + util.capitalize(flag)
				if not hasattr( baseCls, methodName ):
					makeQueryFlagCmd( cls, methodName, inFunc, 
							flag, flagInfo['docstring'] )
	
			# edit command, if there is a corresponding query we use the 'set' prefix. otherwise, not.			
			if 'edit' in modes and 'query' in modes:
				methodName = 'set' + util.capitalize(flag)
				if not hasattr( baseCls, methodName ):
					makeEditFlagCmd( cls, methodName, inFunc, 
							flag, flagInfo['docstring'] )
				
			elif 'edit' in modes:
				if not hasattr( baseCls, flag ):
					makeEditFlagCmd( cls, flag, inFunc, flag, flagInfo['docstring'] )
			
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
		try:
			func = getattr(pymel.core, funcName)
		except AttributeError:
			func = getattr(cmds,funcName)
					
		if len(buf) > 1:
			# create a new class based on this function and wrapped the function function 
			
			baseClsName = buf[1]
			# base Class
			try:
				baseCls = getattr(module, baseClsName)
			except IndexError: 
				baseCls = unicode
			except AttributeError:
				print "could not find %s.%s" % (moduleName, baseClsName)
				baseCls = unicode
		
			# alternate node name
			# use this when the name of the command and name of the node created differ
			# this is the name that PyNode will look for when casting node types to classes
			try:
				nodeName = buf[2]
			except: 
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
		
		else:
			# just create a wrapped function, no new class
			module.__dict__[funcName] = functionFactory( func, pymel.core.PyNode, moduleName )
		
		#except NameError:
		#	print 'could not create class', funcName
	return creationReturnMap	

'''	
def primitiveCommands():
	
	commands = util.moduleDir() / 'commandsPrimitives'
	file = commands.open( 'r' )
	for funcName in file:
		buf = funcName.split()
		funcName = buf[0]		
		try:
			returnCls = getattr(pymel, buf[1])
		except: 
			returnCls = pymel.Transform
				
		def newFunc( *args, **kwargs):
			res = apply( cmds.__dict__[funcName], *args, **kwargs )
			if len(res) == 1:
				res[0] = pymel.Transform(res[0])
			elif len(res) == 2:
				res[0] = pymel.Transform(res[0])
				res[1] = returnCls(res[1])
			return res
		
		newFunc.__name__ = funcName
		try:
			newFunc.__doc__ = helpDocs.commandHelp[funcName]['help']
		except:
			print "could not find help docs for", funcName
		newFunc.__module__ = 'pymel'
		setattr(pymel, funcName, newFunc)
'''
	
def ctxCommands():
	commands = util.moduleDir() / 'commandsCtx'
	file = commands.open( 'r' )
	for funcName in file:
		buf = funcName.split()
		funcName = buf[0]		

		"""
		# direct copy doesn't work bc docs are ready-only
		newFunc = cmds.__dict__[funcName]
		"""
		
		# wrapper
		def newFunc(*args, **kwargs): return apply(cmds.__dict__[funcName], *args, **kwargs)
		newFunc.__name__ = funcName
		try:
			newFunc.__doc__ = helpDocs.commandHelp[funcName]['help']
		except:
			print "could not find help docs for", funcName
		newFunc.__module__ = 'pymel.ctx'
		setattr(pymel.ctx, funcName, newFunc)

#del maya.cmds
		