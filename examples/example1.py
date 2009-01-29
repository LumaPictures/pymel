"""

Pymel makes python within Maya the way it should be-- readable, concise, and object-oriented. Pymel builds on the maya.cmds module by organizing many of its commands into a class hierarchy, and by customizing them to operate in a more succinct and intuitive way.
Compatible with both maya8.5 and maya2008

======================
Project Goals
======================

    - Create an open-source python module for Maya that is intuitive to MEL users and python users alike
    - Fix bugs and design limitations in Maya's python modues, maya.cmds and maya.mel
    - Keep code concise and readable
    - Add organization through class hierarchy and sub-modules
    - Provide documentation accessible via html and the builtin help() function
    - Make it "just work"

======================
What's New
======================

Pymel 0.9 is a dramatic leap forward in the evolution of python in Maya.  The node and attribute classes have been rewritten 
to use the python API as their foundation, increasing speed and flexibility of the object-oriented design.  

For those looking to master python in a production environment, pymel is more than a module for Maya scripting, 
it is a wealth of knowledge -- a self-contained pipeline demonstrating advanced python concepts like function factories, 
metaclasses, and decorators, as well as essential practices such as html-parsing, pickling, logging, and unit testing.

======================
Powerful new classes
======================

**Node classes** for every node type

>>> camTrans, cam = camera()
>>> cam.setFocalLength(100) 
>>> cam.getHorizontalFieldOfView()
20.4079476169
>>> cam.dolly( -3 )
>>> cam.track(left=10)
>>> cam.addBookmark('new')
>>> isinstance( cam, Shape )
True


An **Attribute class** organizes all the attribute commands in one place

.. python::
    
    if s.visibility.isKeyable() and not s.visibility.isLocked():
        s.visibility = True
        s.visibility.lock()
        print s.visibility.type()


Manipulate **file paths** with ease

.. python::

    #backup all mb files in the current scene's directory
    basedir = sceneName().parent
    backupDir = basedir / "backup" #slash op joins paths
    backupDir.mkdir()
    for file in basedir.files( '*.mb' ):
        print "backing up: ", file.name
        file.copy( backupDir / (file.namebase + ".old") )

Work with shape **components**, perform **vector math**, and easily set object attributes with the results

.. python::

    #select all faces that point up in world space
    s = polySphere()[0]
    for face in s.faces:
        if face.normal.objectToWorld(s).y > 0.0:
           select( face, add=1)

Manage optionVars as a python dictionary 

.. python::

    if 'numbers' not in optionVar:
        optionVar['numbers'] = [1,24,47]
    optionVar['numbers'].append(9)
    numArray = optionVar.pop('numbers')

==========================
Do More with Less Code
==========================

If you've tried working with the default maya.cmds and maya.mel modules, you know that they add a lot of awkward syntax that can slow you down. Pymel streamlines this syntax in many ways.

Safe to import into the main namespace, so you don't have to prefix all your commands

.. python::

    # default
    cmds.select( cmds.ls() )
    
    # pymel
    select( ls() )

Customized **operators** for succinct scripting

.. python::

    for source, dest in s.connections( connections=1, sourceFirst=1):
        source // dest # disconnection operator

Call Mel procedures as if they were python commands: no more annoying string formatting

.. python::

    values = ['one', 'two', 'three', 'four']
    
    # default
    maya.mel.eval( 'stringArrayRemoveDuplicates( {"'+'","'.join(values)+'"})')
    
    # pymel
    mel.stringArrayRemoveDuplicates( values )

Enhanced Commands with intelligent defaults and new flags

.. python::

    # force flag: set the attribute; if it does not exist, create it.
    # (attr. type is auto-determined based on the input type)
    s.inputList.set( s.inputs(), force=1)


==========================
Code Comparison
==========================

--------------------------
maya.cmds
--------------------------

.. python::
    
    objs = cmds.ls( type= 'transform') 
    if objs is not None:                    # returns None when it finds no matches
        for x in objs:
            print mm.eval('longNameOf("%s")' % x)
            
            # make and break some connections
            cmds.connectAttr(   '%s.sx' % x,  '%s.sy' % x )
            cmds.connectAttr(   '%s.sx' % x,  '%s.sz' % x )
            cmds.disconnectAttr( '%s.sx' % x,  '%s.sy' % x)
    
            conn = cmds.listConnections( x + ".sx", s=0, d=1, p=1)
            # returns None when it finds no matches
            if conn is not None:                
                for inputPlug in conn:
                    cmds.disconnectAttr( x + ".sx", inputPlug )
            
            # add and set a string array attribute with the history of this transform's shape
            if not mm.eval( 'attributeExists "newAt" "%s"' % x): 
                cmds.addAttr(  x, ln='newAt', dataType='stringArray')
            shape = cmds.listRelatives( x, s=1 )
            if shape is not None:
                history = cmds.listHistory( shape[0] )
            else:
                history = []
            args = tuple( ['%s.newAt' % x, len(history)] + history )
            cmds.setAttr( *args ,  **{ 'type' : 'stringArray' } )
    
            # get and set some attributes
            cmds.setAttr ( '%s.rotate' % x, 1,  1, 1 )
            scale = cmds.getAttr ( '%s.scale' % x )
            scale = scale[0] # maya packs the previous result in a list for no apparent reason
            trans = list( cmds.getAttr ( '%s.translate' % x )[0] )  # the tuple must be converted to a list for item assignment
            trans[0] *= scale[0]
            trans[1] *= scale[1]
            trans[2] *= scale[2]
            cmds.setAttr ( '%s.scale' % x, trans[0], trans[1], trans[2] )
            mm.eval('myMelScript("%s",{%s,%s,%s})' % (cmds.nodeType(x), trans[0], trans[1], trans[2]) )
            
--------------------------
MEL
--------------------------

.. python::

    string $objs[] = `ls -type transform`;
    for ($x in $objs) {
        print (longNameOf($x)); print "\\n";    
        
        // make and break some connections
        connectAttr( $x + ".sx") ($x + ".sy");
        connectAttr( $x + ".sx") ($x + ".sz");
        disconnectAttr( $x + ".sx") ($x + ".sy");
        string $conn[] = `listConnections -s 0 -d 1 -p 1 ($x + ".sx")`;
        for ($inputPlug in $conn)
            disconnectAttr ($x + ".sx") $inputPlug;
        
        // add and set a string array attribute with the history of this transform's shape
        if ( !`attributeExists "newAt" $x`)
            addAttr -ln newAt -dataType stringArray $x;
        string $shape[] = `listRelatives -s $x`;
        string $history[] = `listHistory $shape[0]`;
        string $elements = "";
        for ($elem in $history) 
            $elements += "\"" + $elem + "\" ";
        eval ("setAttr -type stringArray " + $x + ".newAt " + `size $history` + $elements);
        print `getAttr ( $x + ".newAt" )`;
        
        // get and set some attributes
        setAttr ($x + ".rotate") 1 1 1;
        float $trans[] = `getAttr ($x + ".translate")`;
        float $scale[] = `getAttr ($x + ".scale")`;
        $trans[0] *= $scale[0];
        $trans[1] *= $scale[1];
        $trans[2] *= $scale[2];
        setAttr ($x + ".scale") $trans[0] $trans[1] $trans[2];    
        
        // call some other scripts    
        myMelScript( `nodeType $x`, $trans );
    }
    

--------------------------
pymel
--------------------------

.. python::

    from pymel import *                   # safe to import into main namespace
    for x in ls( type='transform'):
        print x.longName()                # object oriented design
        
        # make and break some connections
        x.sx >> x.sy                      # connection operator    
        x.sx >> x.sz    
        x.sx // x.sy                      # disconnection operator
        x.sx.disconnect()                 # smarter methods -- (automatically disconnects all inputs and outputs when no arg is passed)
        
        # add and set a string array attribute with the history of this transform's shape
        if not x.hasAttr('newAt'):
            x.addAttr( 'newAt', dataType='stringArray')
        x.newAt.set( x.getShape().history() )
        
        # get and set some attributes
        x.rotate.set( [1,1,1] )    
        trans = x.translate.get()
        trans *= x.scale.get()           # vector math
        x.translate.set( trans )         # ability to pass list/vector args
        mel.myMelScript(x.type(), trans) # automatic handling of mel procedures
        
"""


#---------------------------------------------------------------------
#        Default Python
#---------------------------------------------------------------------


import maya.mel as mm
import maya.cmds as cmds

mm.eval("""
global proc myMelScript( string $type, float $val[] )
{     print ("the value is:" + $val[0] + " " + $val[1] + " " + $val[2] );
    print "\\n"; 
}
""")



objs = cmds.ls( type= 'transform') 
if objs is not None:                    # returns None when it finds no matches
    for x in objs:
        print mm.eval('longNameOf("%s")' % x)
        
        # make and break some connections
        cmds.connectAttr(   '%s.sx' % x,  '%s.sy' % x )
        cmds.connectAttr(   '%s.sx' % x,  '%s.sz' % x )
        cmds.disconnectAttr( '%s.sx' % x,  '%s.sy' % x)

        conn = cmds.listConnections( x + ".sx", s=0, d=1, p=1)
        # returns None when it finds no matches
        if conn is not None:                
            for inputPlug in conn:
                cmds.disconnectAttr( x + ".sx", inputPlug )
        
        # add and set a string array attribute with the history of this transform's shape
        if not mm.eval( 'attributeExists "newAt" "%s"' % x): 
            cmds.addAttr(  x, ln='newAt', dataType='stringArray')
        shape = cmds.listRelatives( x, s=1 )
        if shape is not None:
            history = cmds.listHistory( shape[0] )
        else:
            history = []
        args = tuple( ['%s.newAt' % x, len(history)] + history )
        cmds.setAttr( *args ,  **{ 'type' : 'stringArray' } )

        # get and set some attributes
        cmds.setAttr ( '%s.rotate' % x, 1,  1, 1 )
        scale = cmds.getAttr ( '%s.scale' % x )
        scale = scale[0] # maya packs the previous result in a list for no apparent reason
        trans = list( cmds.getAttr ( '%s.translate' % x )[0] )  # the tuple must be converted to a list for item assignment
        trans[0] *= scale[0]
        trans[1] *= scale[1]
        trans[2] *= scale[2]
        cmds.setAttr ( '%s.scale' % x, trans[0], trans[1], trans[2] )
        mm.eval('myMelScript("%s",{%s,%s,%s})' % (cmds.nodeType(x), trans[0], trans[1], trans[2]) )
            


#---------------------------------------------------------------------
#        Default Python
#---------------------------------------------------------------------


from pymel import *                   # safe to import into main namespace
for x in ls( type='transform'):
    print x.longName()                # object oriented design
    
    # make and break some connections
    x.sx >> x.sy                      # connection operator    
    x.sx >> x.sz    
    x.sx // x.sy                      # disconnection operator
    x.sx.disconnect()                 # smarter methods -- (automatically disconnects all inputs and outputs when no arg is passed)
    
    # add and set a string array attribute with the history of this transform's shape
    if not x.hasAttr('newAt'):
        x.addAttr( 'newAt', dataType='stringArray')
    x.newAt.set( x.getShape().history() )
    
    # get and set some attributes
    x.rotate.set( [1,1,1] )    
    trans = x.translate.get()
    trans *= x.scale.get()           # vector math
    x.translate.set( trans )         # ability to pass list/vector args
    mel.myMelScript(x.type(), trans) # automatic handling of mel procedures
