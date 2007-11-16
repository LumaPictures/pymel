import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import re,copy,types,sys,inspect

"""
The plugin factory creates maya mel commands out of python classes.  This is the yin to pymel's yang (or is it the other
way around?). Pymel helps to integrate mel into python, whereas this factory helps to integrate python into mel.  It was created
in order to ease our transition to an entirely python-based pipeline.  we had many custom maya commands which were written in c++,
and i wanted to keep all the syntax of these commands exactly the same, but change the guts over to use the python classes we had
developed for use outside of maya.



"""
 
class pluginRegister(object):
	def __init__(self, pluginName, pluginClass, syntax):
		self.pluginName = pluginName
		self.pluginClass = pluginClass
		self.syntax = syntax
		
	def initialize( self, mplugin ):
		try:		
			mplugin.registerCommand( 
					self.pluginName, 
					lambda: OpenMayaMPx.asMPxPtr(  self.pluginClass() ), 
					lambda: self.syntax )
		except:
			sys.stderr.write( "Failed to register command: %s\n" % self.pluginName )
			raise
		
	def uninitialize( self, mplugin ):
		try:
			mplugin.deregisterCommand( self.pluginName )
		except:
			sys.stderr.write( "Failed to unregister command: %s\n" % self.pluginName )
			raise

class Parser(object):
	def __init__(self):
		self.usedShortNames = []
		

	def getShortname( self, methodName, method ):
		"""uses several different methods to generate a shortname flag from the long name"""
		def byDoc():
			""" a shortname can be explicitly set by adding the keyword shortname followed by a colon followed by the shortname
		
					ex.
				
					class foo():
						def bar():
							'shortname: b'
							# do some things
							return
					
			"""
			if method and hasattr( method, "__doc__") and method.__doc__:				
				m = re.search( '.*shortname: (\w+)', method.__doc__)
				if m:
					return m.group(1)
	
		def byCaps():
			""" uses hungarian notation (aka camelCaps) to generate a shortname, with a maximum of 3 letters
				ex.  
				
					myProc --> mp
					fooBar --> fb
					superCrazyLongProc --> scl
			"""
				
			shortname=methodName[0]
			count = 1
			for each in methodName[1:]:
				if each.isupper():
					shortname+=each.lower()
					count+=1
					if count==3:
						break
			return shortname
		
		def byUnderscores():
			""" for python methods that use underscores instead of camelCaps"""
		
			buf = methodName.split('_')
			shortname = ''
			for i, token in enumerate(buf):
				shortname += token[0].lower()
				if i==2:
					break
			return shortname
		
		def byConvention():
			""" chooses between bUnderscores and byCaps"""
		
			if '_' in methodName:
				return byUnderscores()
			return byCaps()
	
		# try byDoc first		
		shortname = byDoc()
		if not shortname or shortname in self.usedShortNames:
			shortname = byConvention()
			if shortname in self.usedShortNames:				
				shortname=methodName[0]
				count = 1
				for each in methodName[1:]:
					shortname+=each.lower()
					count+=1
					if shortname not in self.usedShortNames or count==3:
						break
		#if len(shortname) < 2:
		#	shortname = methodName[:3]
		self.usedShortNames.append(shortname)
		return "-%s" % shortname

	def getLongname( self, method ):
		return "-%s" % method



class funcParser(Parser):
	def __init__(self, funcToWrap):
		Parser.__init__(self)
		self.funcToWrap = funcToWrap	

		"""
		from inspect docs:
		A tuple of four things is returned: (args, varargs, varkw, defaults).
		'args' is a list of the argument names (it may contain nested lists).
		'varargs' and 'varkw' are the names of the * and ** arguments or None.
		'defaults' is an n-tuple of the default values of the last n arguments."""

		# therefore, 
		self.args, varargs, varkw, self.defaults = inspect.getargspec( funcToWrap )
		
		
	def getArgList(self):
		"get the arguments of the function, which become the plugin command arguments."
		
		# since defaults is a tuple of the last n arguments, then args without keywords
		# are the list of args from 0 up to n from the end, or [:-n]
		return self.args[:-1*len(self.defaults)]

		
	def getFlagsList(self):
		" get the keyword arguments of the function, which become the command flags"		
		pass
		# this is not yet finished
		
		for kwarg in self.args[ len(self.args) - len(self.defaults) ]:
			print kwarg
		
			methodType = 'func'
			
			
			if len(kwarg) > 3:			
				method_args.append( [kwarg, nArg,  shortname(kwarg, None), longname(kwarg), methodType] )
						
class ClassParser(Parser):

	def __init__(self, clsToWrap):
		Parser.__init__(self)
		self.clsToWrap = clsToWrap
		self.methodTypes = {}
		self._syntax=OpenMaya.MSyntax()


	def getSyntax(self):
		return self._syntax
				
	def getArgList(self):
		"get the class arguments, which become the plugin command arguments."
		
		argList = []
		# __init__ function
		try:		
			argList=self.clsToWrap.__init__.func_code.co_varnames[1:self.clsToWrap.__init__.func_code.co_argcount]
		
		# __new__ function	
		except AttributeError:
			try:
				argList=self.clsToWrap.__new__.func_code.co_varnames[1:self.clsToWrap.__init__.func_code.co_argcount]
			except AttributeError:
				pass
		
		# convert class arguments to plugin arguments
		for arg in argList:
			#print arg
			self._syntax.addArg(OpenMaya.MSyntax.kString)	
				
		return argList

	
	def getFlagsList(self):
		" get the methods of the class, which become the command flags"
			
		methodList = filter( lambda x: not x.startswith('_'), dir(self.clsToWrap))

		method_args = []
		for methodName in methodList:
					
			methodName = methodName.encode()
			method = getattr(self.clsToWrap,methodName)
			nArg = 0
			
			methodType = type(method)
			
			# regular method
			if methodType is types.MethodType:
				#print method.func_code.co_varnames, method.func_code.co_argcount
				fargs=method.func_code.co_varnames[1:method.func_code.co_argcount]
				nArg = len(fargs)
			
			# special case for properties
			elif methodType is property:
				if type( methodType.fget) != types.NoneType and type( methodType.fset) != types.NoneType:
					#print "enabling query"
					self._syntax.enableQuery(True)
				nArg = 1
			#else:
				#print "skipping %s '%s'" % (methodType, methodName) # add this to the filter above
			
			shortname = self.getShortname(methodName, method)
			longname = self.getLongname(methodName)
			
			# methodnames must be greater than 3 chars long (TODO: print a warning....)
			if len(methodName) > 3:			
				self.methodTypes[methodName] = methodType
				method_args.append( [methodName, nArg, shortname, longname ] )
				
				try:				
					#add to syntax
					{ 
						0: lambda: self._syntax.addFlag( shortname,longname ),
						1: lambda: self._syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString),
						2: lambda: self._syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, 
							OpenMaya.MSyntax.kString),
						3: lambda: self._syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, 
							OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString),
						4: lambda: self._syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, 
							OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString),
						5: lambda: self._syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, 
							OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString)
					}[nArg]()
				except KeyError:
					print "%s is too many arguments for flag %s on %s" % (nArg, methodName, self.clsToWrap )
		
		
		return method_args
			
def pluginFactory( clsToWrap, pluginName=None, commandArgParser=None ):
	
	"""The plugin factory takes a python class and wraps it into a maya MPxCommand.  If no command name is passed then
	the name of passed class is used.  The optional commandArgParser is a function for overriding the default
	handling of the maya argument data and should accept one arg, the command's MArgParser (or is it MArgDatabase? can't remember.)"""
		
	if not pluginName:
		pluginName = clsToWrap.__name__

	parser = None
	if isinstance( clsToWrap, object ):
		parser = ClassParser( clsToWrap )
	
	argNames = parser.getArgList()
	methodNames, nArgs, shortnames, longnames = zip( *parser.getFlagsList() ) 	

	
	
	class pluginProxy(OpenMayaMPx.MPxCommand):
		
		def setResult(self, result):
			if result is None: return
			
			if isinstance(result, dict):
				#convert a dictionary into a 2d list
				newResult = []
				for key, value in result.items():
					newResult.append(key)
					newResult.append(value)
				OpenMayaMPx.MPxCommand.setResult(newResult)
			else:
				#try:
				OpenMayaMPx.MPxCommand.setResult(result)
				#except NotImplementedError:
				#	print "Unsupported return type: %s" % type(result).__name__
				
		def parseCommandArgs(self, argData):
			argValues = []
			for i in range( len(argNames) ):
				try:
					argValues.append( argData.commandArgumentString(i).encode() )
				except RuntimeError:
					print "could not get command arg"
					argValues.append( None )
			return argValues
				
		def parseFlagArgs(self, argData):

			for i, flag in enumerate(shortNames):
				if argData.isFlagSet( flag ):
					flagArgs = []
					j = 0
					
					while(1):
						try:
							flagArgs.append( argData.flagArgumentString(flag,j) )
							
						except: break
						
						j+=1
					
					return ( methodNames[i], flagArgs )
					
			
		def doIt(self,args):
			
			argData= OpenMaya.MArgParser(self.syntax(),args)
			
			commandArgs = self.parseCommandArgs(argData)
			(methodName, methodArgs) = self.parseFlagArgs( argData )

			obj=apply( clsToWrap, commandArgs )
	
			print obj, methodName, methodArgs
			# if the attribute is a property:
			#  getattr -->   myClassCmd -q -attr
			#  setattr -->   myClassCmd -attr "value"
			
			if parser.methodType[methodName] == property:
				if methodArgs:
					setattr( obj, methodName, methodArgs[0] )
					return
				else:
					return self.setResult( getattr(obj, methodName) )
			else:
				func = getattr( obj, methodName )
				return self.setResult( apply( func, methodArgs ) )


	pluginProxy.__name__ = pluginName
	
	if commandArgParser:
		pluginProxy.parseCommandArgs = commandArgParser
	
	return pluginRegister(pluginName, pluginProxy, parser.getSyntax())		
	#return (pluginProxy, _syntax)
			
			
	
