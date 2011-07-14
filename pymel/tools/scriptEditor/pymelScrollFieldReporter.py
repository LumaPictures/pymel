
"""
to create a window:

window;
    paneLayout -configuration "single";
        pymelScrollFieldReporter;
showWindow;
"""


import sys, platform
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaUI as OpenMayaUI
import pymel.tools.mel2py as mel2py
from maya.cmds import encodeString

mparser = mel2py.melparse.MelParser()
mparser.build()

kPluginCmdName = "pymelScrollFieldReporter"

'''
# pass to scrollField
-clear(-clr)
-text(-t)    string

# can possibly be implemented
-saveSelection(-sv)    string
-saveSelectionToShelf(-svs)
-textLength(-tl)

# difficult or impossible to implement
-selectAll(-sla)
-select(-sl)    int int
-cutSelection(-ct)
-copySelection(-cp)
-pasteSelection(-pst)
-hasFocus(-hf)
-receiveFocusCommand(-rfc)    string

'''

kClear = ('clear', 'clr')
kText = ('text', 't')
kCmdReporter = ( 'cmdReporter', 'cr')

kMel = 'mel'
kPython = 'python'

filterFlags = {
    # filters
    'convertToPython'      : ( 'ctp', OpenMaya.MSyntax.kBoolean, False),
    'filterSourceType'     : ( 'fst', OpenMaya.MSyntax.kString, ''),
    'suppressPrintouts'    : ( 'spo', OpenMaya.MSyntax.kBoolean, False),
    'suppressInfo'         : ( 'si', OpenMaya.MSyntax.kBoolean, False),
    'suppressWarnings'     : ( 'sw', OpenMaya.MSyntax.kBoolean, False),
    'suppressErrors'       : ( 'se', OpenMaya.MSyntax.kBoolean, False),
    'suppressResults'      : ( 'sr', OpenMaya.MSyntax.kBoolean, False),
    'suppressStackTrace'   : ( 'sst', OpenMaya.MSyntax.kBoolean, False)
}

globalFilterFlags = {
    # global
    'echoAllCommands'    : ( 'eac', OpenMaya.MSyntax.kBoolean, False),
    'lineNumbers'        : ( 'ln', OpenMaya.MSyntax.kBoolean, False),
     'stackTrace'        : ( 'st', OpenMaya.MSyntax.kBoolean, False)
}

filterFlagNames = ['',
                'suppressPrintouts',    #1
                'suppressInfo',         #2
                'suppressWarnings',     #3
                'suppressErrors',       #4
                'suppressResults',      #5
                'suppressStackTrace' ]  #6

messageId = 0
messageIdSet = False
sourceType = kMel # 'mel' or 'python'

allHistory = []

callbackState = 'normal'

updateCmd = ''

# For XP x64 and Vista, system() returns 'Microsoft'
if platform.system() in ('Windows', 'Microsoft'):
    updateCmd = 'string $fWin=`window -q -frontWindow blah` + "|";string $x;for ($x in `lsUI -controlLayouts -long`) {if (startsWith( $x, $fWin ) ) {break;}};scrollField -e -insertionPosition %(len)d -insertText \"%(text)s\" "%(name)s";setFocus("%(name)s");setFocus($x);'
else:
    updateCmd = 'scrollField -e -insertionPosition %(len)d -insertText \"%(text)s\" "%(name)s";'

class Reporter(object):
    cmdReporter = None

    globalFilters = {
            'echoAllCommands'    : False,
            'lineNumbers'        : False,
             'stackTrace'        : False,
    }
    def __init__(self, *args, **kwargs):
        if not args:
            self.name = kPluginCmdName
        else:
            self.name = args[0]

        # set defaults
        self.filters = {
            # filters
            'convertToPython'     : False,
            'filterSourceType'    : '',
            'suppressPrintouts'   : False,
            'suppressInfo'        : False,
            'suppressWarnings'    : False,
            'suppressErrors'      : False,
            'suppressResults'     : False,
            'suppressStackTrace'  :  False
        }

        self.filters.update( kwargs )
        self.bufferLength = 0
        global allHistory
        self.history = allHistory[:]
        cmd = 'scrollField -wordWrap false -editable false "%s"' % self.name
        self.name = self.executeCommandResult( cmd )
        self.uiMessageID = OpenMayaUI.MUiMessage.addUiDeletedCallback( self.name, uiDeletedCallback, self.name )
        self.refreshHistory()



    def executeCommandOnIdle( self, cmd ):
        global callbackState
        if Reporter.globalFilters['echoAllCommands']:
            callbackState = 'ignoreCommand'
        OpenMaya.MGlobal.executeCommandOnIdle( cmd, False )

    def executeCommand( self, cmd ):
        global callbackState
        if Reporter.globalFilters['echoAllCommands']:
            callbackState = 'ignoreCommand'
        OpenMaya.MGlobal.executeCommand( cmd, False, False )

    def executeCommandResult( self, cmd ):
        global callbackState
        if Reporter.globalFilters['echoAllCommands']:
            callbackState = 'ignoreCommand'
        result = OpenMaya.MGlobal.executeCommandStringResult( cmd, False, False )
        return result

    def lineFilter( self, messageType, sourceType, nativeMsg, convertedMsg ):
        filterSourceType = self.filters['filterSourceType']

        if (not filterSourceType or filterSourceType != sourceType) and not self.filters.get( filterFlagNames[messageType], False ):
            if self.filters['convertToPython'] and convertedMsg is not None:
                return convertedMsg
            return nativeMsg

    def refreshHistory(self):
        output = ''
        for line in self.history:
            try:
                output += self.lineFilter( *line )
            except TypeError: pass
        self.bufferLength = len(output)
        cmd = 'scrollField -e -text \"%s\" "%s";' % ( output, self.name )
        self.executeCommand( cmd )

    def appendHistory(self, line ):
        self.history.append( line )
        output = self.lineFilter( *line )

        if output is not None:
            global callbackState

            cmd = updateCmd % { 'len' : self.bufferLength, 'text' : output, 'name' : self.name }

            #cmd =  % ( self.bufferLength, output, self.name )
            #cmd = 'scrollField -e -insertionPosition %d -insertText \"%s\" "%s";setFocus("%s")' % ( self.bufferLength, output, self.name, self.name )
            self.bufferLength += len(output)

            # f the line is a syntax error, we have to use OnIdle or maya will crash
            #if line[0] == OpenMaya.MCommandMessage.kError and line[1] == kMel and 'Syntax error' in line[2] : #line[2].endswith( 'Syntax error //\n'):
            if line[1] == kMel and ( callbackState == 'syntax_error' or line[0] in [OpenMaya.MCommandMessage.kError, OpenMaya.MCommandMessage.kWarning]  ):
                self.executeCommandOnIdle( cmd )
            else:
                self.executeCommand( cmd )

            return

    def setFilters( self, **filters ):
        self.filters.update( filters )
        self.refreshHistory()

    def setGlobalFilters( self, **filters ):
        global cmdReporter

        flags = ''
        for key, value in filters.items():
            if value: value = 1
            else: value = 0
            flags += '-%s %s ' % (key, value)

        cmd = 'cmdScrollFieldReporter -e %s "%s";' % ( flags, Reporter.cmdReporter )

        self.executeCommand( cmd )

        Reporter.globalFilters.update( filters )

    def getGlobalFilter(self, filter ):
        return Reporter.globalFilters[filter]


        cmd = 'cmdScrollFieldReporter -q -%s "%s";' % ( filter, Reporter.cmdReporter )


        #result = self.executeCommandResult( cmd )
        result = OpenMaya.MGlobal.executeCommandStringResult( cmd, False, False )


        return result

    def addCmdReporter( self, cmdReporter ):
        Reporter.cmdReporter = cmdReporter

    def clear(self):
        self.history = []
        cmd = 'scrollField -e -clear "%s";' % ( self.name )
        self.executeCommand( cmd )


    def text(self, text):
        cmd = 'scrollField -e -text "%s" "%s";' % ( text, self.name )
        self.executeCommand( cmd )

class ReporterDict(dict):
    def __getitem__(self, lookupName):
        lookupBuf = lookupName.split('|')
        for key, val in self.items():
            keyBuf = key.split('|')
            if keyBuf[-1*len(lookupBuf):] == lookupBuf:
                return val
        raise KeyError #, str(lookupName)

reporters = ReporterDict({})
#reporters = {}

def removeCallback(id):
    try:
        OpenMaya.MMessage.removeCallback( id )
    except:
        sys.stderr.write( "Failed to remove callback\n" )
        raise

def createCallback(stringData):
    # global declares module level variables that will be assigned
    global messageIdSet
    global messageId

    try:
        id = OpenMaya.MCommandMessage.addCommandOutputCallback( cmdCallback, stringData )
    except:
        sys.stderr.write( "Failed to install callback\n" )
        messageIdSet = False
    else:
        messageIdSet = True
    return id

def uiDeletedCallback( name ):
    #outputFile = open( '/var/tmp/commandOutput', 'a')
    #outputFile.write( 'before=%s\n' % reporters  )
    #outputFile.close()


    removeCallback( reporters[ name ].uiMessageID )
    reporters.pop( name )

    #outputFile = open( '/var/tmp/commandOutput', 'a')
    #outputFile.write( 'after=%s\n' % reporters  )
    #outputFile.close()

def cmdCallback( nativeMsg, messageType, data ):
    global callbackState

    #outputFile = open( '/var/tmp/commandOutput', 'a')
    #outputFile.write( '============\n%s\n%s %s, length %s \n' % (nativeMsg, messageType, callbackState, len(nativeMsg))  )
    #outputFile.close()


    if callbackState == 'ignoreCommand':
        callbackState = 'ignoreResult'
        return
    elif callbackState == 'ignoreResult':
        callbackState = 'normal'
        return

    global sourceType
    global allHistory

    syntaxError = False
    convertedMsg = None

    # Command History
    if messageType == OpenMaya.MCommandMessage.kHistory:
        callbackState = 'normal'
        #if nativeMsg.rfind(';') == len(nativeMsg)-2 : # and len(nativeMsg) >= 2:
        if nativeMsg.endswith(';\n') : # and len(nativeMsg) >= 2:
            sourceType = kMel
            try:
                #convertedMsg = mel2py.mel2pyStr( nativeMsg )
                convertedMsg = mparser.parse( nativeMsg )
            except Exception, msg:
                syntaxError = True
                pass
        else:
            sourceType = kPython

    # Display - unaltered strings, such as that printed by the print command
    elif messageType == OpenMaya.MCommandMessage.kDisplay and ( nativeMsg.endswith(';\n') or nativeMsg.startswith( '//' ) ):
        try:
            #convertedMsg = mel2py.mel2pyStr( nativeMsg )
            convertedMsg = mparser.parse( nativeMsg )
        except Exception, msg:
            pass
    else:
        try:
            nativeMsg = {
                    #OpenMaya.MCommandMessage.kDisplay: 'Output',
                    OpenMaya.MCommandMessage.kInfo: '',
                    OpenMaya.MCommandMessage.kWarning: 'Warning: ',
                    OpenMaya.MCommandMessage.kError: 'Error: ',
                    OpenMaya.MCommandMessage.kResult: 'Result: '
                }[ messageType ] + nativeMsg

            if sourceType == kMel:
                convertedMsg = '# %s #\n' % nativeMsg
                nativeMsg = '// %s //\n' % nativeMsg
            else:
                nativeMsg = '# %s #\n' % nativeMsg

        except KeyError:
            pass

    nativeMsg = encodeString( nativeMsg )
    if convertedMsg is not None:
        convertedMsg = encodeString( convertedMsg )

    #outputFile = open( '/var/tmp/commandOutput', 'a')
    #outputFile.write( '---------\n%s %s\n' % ( convertedMsg, sourceType ) )
    #outputFile.close()

    line = [ messageType, sourceType, nativeMsg, convertedMsg ]

    allHistory.append( line )

    #if messageType == OpenMaya.MCommandMessage.kError : # and 'Syntax error' in nativeMsg:
    #    return

    for reporter in reporters.values():
        reporter.appendHistory( line )

    if syntaxError:
        callbackState = 'syntax_error'

    #elif callbackState == 'syntax_error' and 'Syntax error' in nativeMsg:
    #    callbackState = 'normal'

    #global output
    #output += encodeString( message )

    #cmd = 'global string $gCommandReporter;cmdScrollFieldReporter -edit -text \"%s\" $gCommandReporter;' % output
    #cmd = 'scrollField -e -text \"%s\" %s;\n' % ( output, scrollFieldName )



    #OpenMaya.MGlobal.executeCommand( cmd, False, False )

# command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)



    def doIt(self, args):
        #global messageId

        try:
            argData = OpenMaya.MArgDatabase(self.syntax(), args)
        except:
            name = kPluginCmdName
            reporter = Reporter( name )
            reporters[reporter.name] = reporter
            return self.setResult( reporter.name )
        try:
            name = argData.commandArgumentString(0)
        except:
            name = kPluginCmdName


        # QUERY
        if argData.isQuery():
            reporter = reporters[name]
            for key,data in filterFlags.items():
                if argData.isFlagSet( key ):
                    self.setResult( reporter.filters[ key ] )
                    return

            for key,data in globalFilterFlags.items():
                if argData.isFlagSet( key ):
                    self.setResult( reporter.getGlobalFilter( key ) )
                    return

            if argData.isFlagSet( kCmdReporter[0] ):
                self.setResult( reporter.cmdReporter )

        else:
            filters = {}
            for key,data in filterFlags.items():
                if argData.isFlagSet( key ):
                    if data[1] == OpenMaya.MSyntax.kBoolean:
                        filters[key] = argData.flagArgumentBool( key, 0 )
                    elif data[1] == OpenMaya.MSyntax.kString:
                        filters[key] = argData.flagArgumentString( key, 0 )

            globalFilters = {}
            for key,data in globalFilterFlags.items():
                if argData.isFlagSet( key ):
                    if data[1] == OpenMaya.MSyntax.kBoolean:
                        globalFilters[key] = argData.flagArgumentBool( key, 0 )

            # EDIT
            if argData.isEdit():
                reporter = reporters[name]
                if filters:
                    reporter.setFilters( **filters )
                if globalFilters:
                    reporter.setGlobalFilters( **globalFilters )

                if argData.isFlagSet( kClear[0] ):
                    reporter.clear()
                elif argData.isFlagSet( kText[0] ):
                    reporter.text( argData.flagArgumentString( kText[0], 0 ) )
                elif argData.isFlagSet( kCmdReporter[0] ):
                    reporter.addCmdReporter( argData.flagArgumentString( kCmdReporter[0], 0 ) )
            # CREATE
            else:
                reporter = Reporter( name, **filters )
                reporters[reporter.name] = reporter

                #outputFile = open( '/var/tmp/commandOutput', 'a')
                #outputFile.write( 'create %s\n' % ( reporters ) )
                #outputFile.close()

                #reporters[name] = reporter
            self.setResult( reporter.name )



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

    for flag, data in globalFilterFlags.items():
        syntax.addFlag( data[0], flag, data[1] )

    syntax.addFlag( kClear[1], kClear[0] )
    syntax.addFlag( kText[1], kText[0], OpenMaya.MSyntax.kString )
    syntax.addFlag( kCmdReporter[1], kCmdReporter[0], OpenMaya.MSyntax.kString )

    return syntax

# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)

    if OpenMaya.MGlobal.mayaVersion() == '8.5':
        raise NotImplementedError, "pymelScrollFieldReporter is only supported in Maya 2008 and later."
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator, syntaxCreator )

        global messageIdSet
        global messageId
        if ( messageIdSet ):
            print "Message callback already installed"
        else:
            #print "Installing callback message"
            messageId = createCallback( '' )

    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    global messageIdSet
    global messageId
    # Remove the callback
    if ( messageIdSet ):
        removeCallback( messageId )
    # Remove the plug-in command
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )
        raise
