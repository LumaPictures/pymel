
import maya.cmds
import sys, os.path

# Locations of commandList file by OS type as returned by maya.cmds.about( os=True )
commandListLocations = {
    'nt' : 'bin',
    'win64' : 'bin',
    'mac' : 'MacOS',
    'linux' : 'lib',
    'linux64' : 'lib'
}

def __makeStubFunc( command, library ):
    def stubFunc( *args, **keywords ):
        """ Dynamic library stub function """
        maya.cmds.dynamicLoad( library )
        # call the real function which has replaced us
        return maya.cmds.__dict__[command]( *args, **keywords )
    return stubFunc

def processCommandList():
    """
    Process the "commandList" file that contains the mappings between command names and the
    libraries in which they are found.  This function will install stub functions in maya.cmds
    for all commands that are not yet loaded.  The stub functions will load the required library
    and then execute the command.
    """

    try:
        # Assume that maya.cmds.about and maya.cmds.internalVar are already registered
        #
        commandListPath = os.path.realpath( os.environ[ 'MAYA_LOCATION' ] )
        platform = maya.cmds.about( os=True )
        commandListPath = os.path.join( commandListPath, commandListLocations[platform], 'commandList' )

        file = open( commandListPath, 'r' )
        for line in file:
            commandName, library = line.split()
            if not commandName in maya.cmds.__dict__:
                maya.cmds.__dict__[commandName] = __makeStubFunc( commandName, library )
    except:
        sys.stderr.write("Unable to process commandList %s" % commandListPath)
        raise

# Copyright (C) 1997-2011 Autodesk, Inc., and/or its licensors.
# All rights reserved.
#
# The coded instructions, statements, computer programs, and/or related
# material (collectively the "Data") in these files contain unpublished
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its licensors,
# which is protected by U.S. and Canadian federal copyright law and by
# international treaties.
#
# The Data is provided for use exclusively by You. You have the right to use,
# modify, and incorporate this Data into other products for purposes authorized 
# by the Autodesk software license agreement, without fee.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. AUTODESK
# DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTIES
# INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF NON-INFRINGEMENT,
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR ARISING FROM A COURSE 
# OF DEALING, USAGE, OR TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS
# LICENSORS BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK AND/OR ITS
# LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY OR PROBABILITY OF SUCH DAMAGES.

