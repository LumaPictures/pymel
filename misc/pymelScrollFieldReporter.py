
"""
to create a window:

window;
    paneLayout -configuration "single";
        pymelScrollFieldReporter;
showWindow;
"""


import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from pymel.mel2py import mel2pyStr
from maya.cmds import encodeString


kPluginCmdName = "pymelScrollFieldReporter"

'''
-saveSelection(-sv)	string	
-saveSelectionToShelf(-svs)		
-selectAll(-sla)		
-select(-sl)	int int	
-clear(-clr)		
-text(-t)	string	
-textLength(-tl)		
-cutSelection(-ct)		
-copySelection(-cp)		
-pasteSelection(-pst)		
-hasFocus(-hf)	
-receiveFocusCommand(-rfc)	string
'''

filterFlags = {
	# global
	'echoAllCommands': ( 'eac', OpenMaya.MSyntax.kBoolean),	
	'lineNumbers': ( 'ln', OpenMaya.MSyntax.kBoolean),
 	'stackTrace': ( 'st', OpenMaya.MSyntax.kBoolean),
	# filters
	'convertToPython' : ( 'ctp', OpenMaya.MSyntax.kBoolean),
	'filterSourceType' : ( 'fst', OpenMaya.MSyntax.kString),
	'suppressPrintouts': ( 'spo', OpenMaya.MSyntax.kBoolean),
	'suppressInfo': ( 'si', OpenMaya.MSyntax.kBoolean),
	'suppressWarnings': ( 'sw', OpenMaya.MSyntax.kBoolean),	
	'suppressErrors': ( 'se', OpenMaya.MSyntax.kBoolean),
	'suppressResults': ( 'sr', OpenMaya.MSyntax.kBoolean),	
	'suppressStackTrace': ( 'sst', OpenMaya.MSyntax.kBoolean)
}

filterFlagNames = ['', 'suppressPrintouts','suppressInfo', 'suppressWarnings', 'suppressErrors', 'suppressResults', 'suppressStackTrace' ]

messageId = 0
messageIdSet = False
reporters = {}
output = ''
sourceType = None # 'mel' or 'python'

kMel = 'mel'
kPython = 'python'

callbackState = True

class Reporter(object):
	def __init__(self, *args, **kwargs):
		if not args:
			self.name = kPluginCmdName
		else:
			self.name = args[0]
		
		self.flags = kwargs
		self.history = []	
		cmd = 'scrollField -wordWrap false -editable false "%s"' % self.name
		self.name = self.executeCommandResult( cmd )

	def executeCommand( self, cmd ):
		global callbackState
		callbackState = False
		OpenMaya.MGlobal.executeCommand( cmd, False, False )
		callbackState = True

	def executeCommandResult( self, cmd ):
		global callbackState
		callbackState = False
		result = OpenMaya.MGlobal.executeCommandStringResult( cmd, False, False )
		callbackState = True
		return result
				
	def lineFilter( self, messageType, sourceType, nativeMsg, convertedMsg ):
		filterSourceType = self.flags.get('filterSourceType', '' )

		#outputFile = open( '/var/tmp/commandOutput', 'a')
		#outputFile.write( '%s %s %s %s\n' % (nativeMsg, messageType, filterFlagNames[messageType], self.flags)  )
		#outputFile.close()
				
		if (not filterSourceType or filterSourceType == sourceType) and not self.flags.get( filterFlagNames[messageType], False ): 
			if self.flags.get( 'convertToPython', False) and convertedMsg is not None:
				return convertedMsg
			return nativeMsg
		
	def refreshHistory(self):
		output = ''
		for line in self.history:
			try:
				output += self.lineFilter( *line )
			except TypeError: pass
		
		cmd = 'scrollField -e -text \"%s\" "%s";' % ( output, self.name )
		self.executeCommand( cmd )
		
	def appendHistory(self, line ):
		self.history.append( line )
		output = self.lineFilter( *line )
	
		if output is not None:
			cmd = 'scrollField -e -insertText \"%s\" "%s";' % ( output, self.name )
		
			#outputFile = open( '/var/tmp/commandOutput', 'a')
			#outputFile.write( cmd + '\n' )
			#outputFile.close()
		
			self.executeCommand( cmd )
		
	def setFilters( self, **filters ):			
		self.flags.update( filters )	
		self.refreshHistory()
			


def removeCallback(id):
	try:
		OpenMaya.MMessage.removeCallback( id )
	except:
		sys.stderr.write( "Failed to remove callback\n" )
		raise

def cmdCallback( nativeMsg, messageType, data ):
	outputFile = open( '/var/tmp/commandOutput', 'a')
	outputFile.write( '%s %s\n' % (nativeMsg, messageType)  )
	outputFile.close()
	
	global callbackState
	if not callbackState:
		return
		
	global sourceType
	
	convertedMsg = None
	if messageType == OpenMaya.MCommandMessage.kHistory:
		if nativeMsg.rfind(';') == len(nativeMsg)-2:
			sourceType = kMel
			try:
				convertedMsg = mel2pyStr( nativeMsg )
			except: pass
		else:
			sourceType = kPython
	else:
		try:
			nativeMsg = '%s: %s' % ( {
					#OpenMaya.MCommandMessage.kDisplay: 'Output',
					OpenMaya.MCommandMessage.kInfo: 'Info',
					OpenMaya.MCommandMessage.kWarning: 'Warning',
					OpenMaya.MCommandMessage.kError: 'Error',				
					OpenMaya.MCommandMessage.kResult: 'Result'
				}[ messageType ], nativeMsg )
				
			if sourceType == kMel:
				convertedMsg = '# %s #\n' % nativeMsg 
				nativeMsg = '// %s //\n' % nativeMsg 				
			else:
				nativeMsg = '# %s #\n' % nativeMsg
				
		except KeyError:
			pass
			'''
			outputFile = open( '/var/tmp/commandOutput', 'a')
			outputFile.write( '%s %s %s\n' % (nativeMsg, messageType, sourceType)  )
			outputFile.close()
			return
			'''
	nativeMsg = encodeString( nativeMsg )
	if convertedMsg is not None:
		convertedMsg = encodeString( convertedMsg )
		
	line = [ messageType, sourceType, nativeMsg, convertedMsg ]
	
	for reporter in reporters.values():
		reporter.appendHistory( line )


	return
			
	#global output
	#output += encodeString( message )
	
	#cmd = 'global string $gCommandReporter;cmdScrollFieldReporter -edit -text \"%s\" $gCommandReporter;' % output
	#cmd = 'scrollField -e -text \"%s\" %s;\n' % ( output, scrollFieldName )
	

	
	#OpenMaya.MGlobal.executeCommand( cmd, False, False )
	
# command
class scriptedCommand(OpenMayaMPx.MPxCommand):
	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)
		
	def createCallback(self, stringData):
		# global declares module level variables that will be assigned
		global messageIdSet
	
		try:
			id = OpenMaya.MCommandMessage.addCommandOutputCallback( cmdCallback, stringData )
		except:
			sys.stderr.write( "Failed to install callback\n" )
			messageIdSet = False
		else:
			messageIdSet = True
		return id
	
	def doIt(self, args):
		global messageId
	
		argData = OpenMaya.MArgDatabase(self.syntax(), args)
		name = argData.commandArgumentString(0)
		flags = {}
		for key,data in filterFlags.items():
			if argData.isFlagSet( key ):
				if data[1] == OpenMaya.MSyntax.kBoolean:
					flags[key] = argData.flagArgumentBool( key, 0 )
				elif data[1] == OpenMaya.MSyntax.kString:
					flags[key] = argData.flagArgumentString( key, 0 )
		
		if argData.isQuery():
			self.setResult( reporters[name].flags.get( flags.keys()[0], False ) )
		elif argData.isEdit():
			reporters[name].setFilters( **flags )			
		else:
			reporter = Reporter( name, **flags )
			#reporters[reporter.name] = reporter
			reporters[name] = reporter
			
		if ( messageIdSet ):
			pass
			#print "Message callaback already installed"
		else:
			#print "Installing callback message"
			messageId = self.createCallback( '' )
						
		#result = OpenMaya.MGlobal.executeCommandStringResult( cmd, False, False )
		#self.setResult( result )
		#
			
# Creator
def cmdCreator():
	return OpenMayaMPx.asMPxPtr( scriptedCommand() )

# Syntax creator
def syntaxCreator():
	syntax = OpenMaya.MSyntax()
	syntax.addArg(OpenMaya.MSyntax.kString)
	syntax.enableQuery(True)
	syntax.enableEdit(True)
	for flag, data in filterFlags.items():
		syntax.addFlag( data[0], flag, data[1] )

	return syntax

# Initialize the script plug-in
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.registerCommand( kPluginCmdName, cmdCreator, syntaxCreator )
	except:
		sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
		raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
	# Remove the callback
	if ( messageIdSet ):
		removeCallback( messageId )
	# Remove the plug-in command
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterCommand( kPluginCmdName )
		#outputFile.close()
	except:
		sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )
		raise
