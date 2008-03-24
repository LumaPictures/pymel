import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import re,copy,types

class pluginRegister(object):
	def __init__(self, pluginName, pluginClass, syntax):
		self.pluginName = pluginName
		self.pluginClass = pluginClass
		self.syntax = syntax
		
	def initialize( self, mplugin ):
		try:		
			mplugin.registerCommand( self.pluginName, 
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
			
def pluginFactory( wrappedClass, pluginName, commandArgParser=None ):
	
	usedShortNames = []
	_syntax=OpenMaya.MSyntax()
	
	def getArgList():
		" get the class arguments, which become the plugin command arguments "
		argList = []
		try:
			argList=wrappedClass.__init__.func_code.co_varnames[1:wrappedClass.__init__.func_code.co_argcount]
		except AttributeError:
			try:
				argList=wrappedClass.__new__.func_code.co_varnames[1:wrappedClass.__new__.func_code.co_argcount]
			except AttributeError:
				pass
				
		return argList
	
	def getMethodsList():
		" get the methods of the class, which become the command flags"
		
		
		def shortname( methodName, method ):
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
				if hasattr( method, "__doc__") and method.__doc__:				
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
			if not shortname or shortname in usedShortNames:
				shortname = byConvention()
				if shortname in usedShortNames:				
					shortname=methodName[0]
					count = 1
					for each in methodName[1:]:
						shortname+=each.lower()
						count+=1
						if shortname not in usedShortNames or count==3:
							break
			#if len(shortname) < 2:
			#	shortname = methodName[:3]
			usedShortNames.append(shortname)
			return "-%s" % shortname
		
		def longname( method ):
			return "-%s" % method
		
		methodList = filter( lambda x: not x.startswith('_'), dir(wrappedClass))

		method_args = []
		for methodName in methodList:
			
			
			methodName = methodName.encode()
			method = getattr(wrappedClass,methodName)
			nArg = 0
			
			methodType = type(method)
			
			
			if methodType is types.MethodType:
				#print method.func_code.co_varnames, method.func_code.co_argcount
				fargs=method.func_code.co_varnames[1:method.func_code.co_argcount]
				nArg = len(fargs)
				#argType = 
			elif methodType is property:
				if type( methodType.fget) != types.NoneType and type( methodType.fset) != types.NoneType:
					#print "enabling query"
					_syntax.enableQuery(True)
				nArg = 1
			#else:
				#print "skipping %s '%s'" % (methodType, methodName) # add this to the filter above
			
			if len(methodName) > 3:			
				method_args.append( [methodName, nArg,  shortname(methodName, method), longname(methodName), methodType] )
		return method_args
		
	
	argNames = getArgList()
	methodNames = []
	longNames = []
	shortNames = []
	methodTypes = []
	nArgs = []
	
	
	#syntax.addArg(OpenMaya.MSyntax.kString)
	
	# convert class arguments to plugin arguments
	for arg in argNames:
		#print arg
		_syntax.addArg(OpenMaya.MSyntax.kString)
	
	# convert methods/properties to plugin flags
	for method, nArg, shortname, longname, attrType in getMethodsList():
		
		methodNames.append( method )
		shortNames.append( shortname )
		longNames.append( longname )
		nArgs.append( nArg )
		methodTypes.append( attrType ) # instancemethod, property, etc
		#print method, nArg, shortname, longname
		
		{ 
			0: lambda: _syntax.addFlag( shortname,longname ),
			1: lambda: _syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString),
			2: lambda: _syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString),
			3: lambda: _syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString),
			4: lambda: _syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString),
			5: lambda: _syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString, OpenMaya.MSyntax.kString)
		}[nArg]()
		
		
		'''
		if nArg:
			#args = (OpenMaya.MSyntax.kString,)*nArgs
			#syntax.addFlag( shortname,longname, *args)
			_syntax.addFlag( shortname,longname, OpenMaya.MSyntax.kString)
		else:
			_syntax.addFlag( shortname, longname, OpenMaya.MSyntax.kNoArg )	'''
	
	
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
				
		def parseCommandArgs(self, args):
			#print "parsing command args"
			# command/class arguments
			#argData= OpenMaya.MArgParser(self.syntax(),args)
			argValues = []
			for i in range( len(argNames) ):
				try:
					argValues.append( argData.commandArgumentString(i).encode() )
				except RuntimeError:
					print "could not get command arg"
					argValues.append( None )
			return argValues
				
		def parseArgs(self, args):

			argData= OpenMaya.MArgParser(self.syntax(),args)
			classArgs = self.parseCommandArgs(argData)
			
			# ---- test -------
			# python friendly version
			
			method = None
			methodType = None
			for i, flag in enumerate(shortNames):
				if argData.isFlagSet( flag ):
					flagArgs = []
					j = 0
					
					while(1):
						try:
							flagArgs.append( argData.flagArgumentString(flag,j) )
							
						except: break
						
						j+=1
					
					
					#print "Flag New:",  methodNames[i], flagArgs, classArgs, methodTypes[i] 
					return ( methodNames[i], flagArgs, classArgs, methodTypes[i]  )
					
			# -------------------

			print "parsing flag args", args.length()
			# flag/method arguments
			method = None
			i = 0
			for i in range(args.length()):			
				arg = args.asString(i)
				if arg.startswith('-') and arg not in ['-q', '-e', '-query', '-edit']:
					#print "parsing %s" % arg
					try:
						index = longNames.index(arg)
					except:
						index = shortNames.index(arg) 
						
					values = []
					if not argData.isQuery():							
						values = [args.asString(j).encode() for j in range(i+1, i+nArgs[ index ]+1) ] 						
					
					#print "Flag Curr:",  methodNames[index], values, classArgs, methodTypes[index] 
					return ( methodNames[index], values, classArgs, methodTypes[index] )
					
					#OpenMaya.MGlobal.displayError( ": Unsupported Flag")
			
			
		def doIt(self,args):

			(method, methodArgs, classArgs, methodType) = self.parseArgs( args )

			#print method, methodArgs, classArgs, methodType

			obj=apply( wrappedClass, classArgs )
		
			# if the attribute is a property:
			#  getattr -->   myClassCmd -q -attr
			#  setattr -->   myClassCmd -attr "value"
			if methodType == property:
				if methodArgs:
					setattr( obj, method, methodArgs[0] )
					return
				else:
					return self.setResult( getattr(obj, method) )
			else:
				func = getattr( obj, method)
				return self.setResult( apply( func, methodArgs ) )
			
			
		
		def syntaxCreator():
			return _syntax	
		
		def cmdCreator(self):
			return OpenMayaMPx.asMPxPtr( self )
		#pluginName = pluginName
	pluginProxy.__name__ = pluginName
	
	if commandArgParser:
		pluginProxy.parseCommandArgs = commandArgParser
	
	return pluginRegister(pluginName, pluginProxy, _syntax)		
	#return (pluginProxy, _syntax)
			
			
	
