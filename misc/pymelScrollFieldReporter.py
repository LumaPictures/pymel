
import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
from pymel.mel2py import mel2pyStr
from maya.cmds import encodeString


kPluginCmdName = "pymelScrollFieldReporter"

messageId = 0
messageIdSet = False

output = ''

def removeCallback(id):
	try:
		OpenMaya.MMessage.removeCallback( id )
	except:
		sys.stderr.write( "Failed to remove callback\n" )
		raise

def cmdCallback( message, messageType, scrollFieldName ):
	#global outputFile
	
	if messageType == OpenMaya.MCommandMessage.kHistory and message.rfind(';') == len(message)-2:
		#outputFile = open( '/var/tmp/commandOutput', 'a')
		message = mel2pyStr( message )
		#outputFile.write( message )
		#outputFile.close()
	else:
		try:
			message = '# %s: %s #\n' % ( {
					OpenMaya.MCommandMessage.kWarning: 'Warning',
					OpenMaya.MCommandMessage.kError: 'Error',
					OpenMaya.MCommandMessage.kResult: 'Result'
				}[ messageType ], message )
			
		except KeyError:pass	
	
	global output
	output += encodeString( message )
	
	#cmd = 'global string $gCommandReporter;cmdScrollFieldReporter -edit -text \"%s\" $gCommandReporter;' % output
	cmd = 'scrollField -e -text \"%s\" %s;\n' % ( output, scrollFieldName )
	
	#outputFile = open( '/var/tmp/commandOutput', 'a')
	#outputFile.write( 'scrollField -e -text \"%s\" %s;\n' % ( encodeString( message ), scrollFieldName )  )
	#outputFile.close()
	
	OpenMaya.MGlobal.executeCommand( cmd, False, False )
	
# command
class scriptedCommand(OpenMayaMPx.MPxCommand):
	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)
		#self.output = open( '/var/tmp/commandOutput', 'w')
		#global outputFile
		outputFile = open( outputFileName, 'a' )
		
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
		if ( messageIdSet ):
			print "Message callaback already installed"
		else:
			print "Installing callback message"
			#argData = OpenMaya.MArgDatabase(self.syntax(), args)
			#name = argData.getCommandArgument(0, name2)
			#print name, name2
			name = kPluginCmdName
			result = OpenMaya.MGlobal.executeCommandStringResult( 'scrollField -wordWrap false -editable false ' + name, False, False )
			sys.stdout.write( result )
			messageId = self.createCallback( result )
			
# Creator
def cmdCreator():
	return OpenMayaMPx.asMPxPtr( scriptedCommand() )

# Syntax creator
def syntaxCreator():
	syntax = OpenMaya.MSyntax()
	syntax.addArg(OpenMaya.MSyntax.kString)
	return syntax

# Initialize the script plug-in
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.registerCommand( kPluginCmdName, cmdCreator )
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
