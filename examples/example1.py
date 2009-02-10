"""

PyMEL makes python within Maya the way it should be-- readable, concise, and object-oriented. PyMEL integrates the python API with the maya.cmds
module by organizing many of its commands into a class hierarchy, and by customizing them to operate in a more succinct and intuitive way.

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
Production Proven
======================

Since its release over a year ago PyMEL, has accumulated an impressive resume, in both feature films and games: 

    - DreamWorks: *Fung Fu Panda*, *Shrek 4*, *Monsters Vs Aliens*, and *How to Train Your Dragon*
    - Luma Pictures: *Pirates of the Carribean: At World's End*, *Harry Potter 6*, and *Wolverine*
    - ImageMovers Digital: Robert Zemeckis' upcoming *A Christman Carol*
   
Here's what Seth Gibson of Bungie Studios, makers of the hit game *Halo*, has to say:

    "Having done production python code myself for many years, wrapping my head around Maya's native 
    implementation took a little bit of time.  With PyMel, I can think and write the python code and 
    syntax I'm already used to, which speeds up my development time considerably.  It's also
    going to help our other Technical Artists with their Python learning curve, since PyMEL's syntax
    is consistent with most other python packages.  Kudos to the PyMel team for such a well 
    thought out project!"

======================
What's New
======================

----------------------
API Hybridization
----------------------

PyMEL 0.9 is a dramatic leap forward in the evolution of python in Maya.  The node and attribute classes have been rewritten 
from the ground up to use the python API as their foundation, increasing the speed and fidelity of PyMEL's object-oriented design.  

PyMEL harnesses the API to create a name-independent
representation of your object.  With this in hand, PyMEL can operate on the object itself, not just the string representing the object.
And if anything causes the name of your object to change it will automatically be reflected in your node variable.

Let's take a common example: testing if two nodes or attributes are the
same. In MEL or maya.cmds, to accomplish this the typical solution is to perform a string comparison 
of two object names, but there are many ways that this seemingly simple operation can go wrong. For instance, forgetting to compare the
full paths of dag node objects, or comparing the long name of an attribute to the short name of an attribute.  
And what if someone renames the node or its name becomes non-unique?  With PyMEL, the nightmares
of string comparisons are over.

Below, we make a camera, rename it, and then group and instance it, to demonstrate how the name changes are constantly reflected. Keep in mind
that the changes could have just as easily been performed by the user interacting with objects through the GUI.

    >>> cam, shape = camera()
    >>> print cam
    camera1
    >>> cam.rename('renderCam')
    >>> print cam
    renderCam
    >>> grp = group(cam)
    >>> instance(grp)
    >>> print cam
    group1|renderCam
    >>> cam.getInstances()
    [Transform(u'group1|renderCam'), Transform(u'group2|renderCam')]

Comparing attributes is just as easy.  

    >>> # long and short names retrieve the same attribute
    >>> cam.t == cam.translate    
    True
    >>> cam.tx == cam.translate.translateX
    True

Like MEL, PyMEL will also look up shape attributes from a transform:

    >>> cam  # confirm that cam is a transform
    Transform(u'group1|renderCam')
    >>> cam.focalLength  # get the focalLength of the shape
    Attribute(u'group1|renderCam|renderCamShape.focalLength')
    >>> cam.focalLength == cam.getShape().focalLength
    True
    
Beyond this new purity of behavior, PyMEL node classes now include hundreds of new methods derived from the API, but with the same intuitive and unified design as before.
With PyMEL you get the benefits of API speed and versatility without the advanced learning curve.

--------------------
BSD License
--------------------
    
PyMEL is released under the BSD license, which is as open as open source gets.  Your studio can freely use, contribute to, and 
modify this module with no strings attached.


------------------------------
Improved Standalone Support
------------------------------

Unlike the maya module, PyMEL behaves the same in a standalone interpreter as it does in an GUI session.
When pymel detects that it is being imported in a standalone
interpreter it performs these operations:

    1. initializes maya.standalone
    2. parses your Maya.env and adds variables to your environment
    3. sources userSetup.mel

This will save you a lot of time and headache when using Maya in a standalone environment.

--------------------------------
Tighter MEL Integration
--------------------------------

Calling MEL from python is still an unfortunate necessity, so PyMEL makes it as easy as possible.  This release builds on PyMEL's already
vastly improved method, which allows you to call a mel procedure as if it was a python function:

.. python::

    values = ['one', 'two', 'three', 'four']
    
    # default
    maya.mel.eval( 'stringArrayRemoveDuplicates( {"'+'","'.join(values)+'"})')
    
    # PyMEL
    mel.stringArrayRemoveDuplicates( values )
    
In the new release, when a MEL script called from PyMEL raises an error, you will get the specific mel error message in the python traceback, along with line numbers!
    
For example, here's a procedure "myScript" with a line that will result in an error:

    >>> mel.eval( '''global proc myScript( string $stringArg, float $floatArray[] ){ 
    ...     float $donuts = `ls -type camera`;}''')
    
When we call it, we can quickly determine the problem:

    >>> mel.myScript( 'foo', [] )
    Traceback (most recent call last):
        ...
    MelConversionError: Error occurred during execution of MEL script: line 2: Cannot convert data of type string[] to type float.

Also, getting and setting MEL global variables is accomplished via a special dictionary-like object:

    >>> melGlobals['$gMainFileMenu']
    mainFileMenu
    >>> melGlobals['$gGridDisplayGridLinesDefault'] = 2    
        
--------------------------------
Other Improvements
--------------------------------

    - New and improved math classes
    - Expanded documentation
    - Loads of useful utilities



==========================
Who is PyMEL for?
==========================

--------------------------
For the Novice
--------------------------

Object-oriented programming, like that provided by PyMEL, is more intuitive to learn because the functionality of an object is directly
associated with the object itself.  For an artist starting to program in Maya, the first question you might ask is "what can I do with this node?"  
Using a procedural approach, like that offered by MEL or maya.cmds, you'll have to dig through the hundreds of MEL commands looking for the one that you want. 
For a camera node, the ``camera`` MEL command is easy to find, but did you find ``orbit``, ``track``,
``dolly``, and ``tumble``, which also work on cameras?  In PyMEL, all you have to do is type ``help(Camera)`` in the python script editor 
to find out all the things a camera node can do, or just look up the Camera class in the PyMEL docs.


--------------------------
For the MEL Scripter
--------------------------

When we say PyMEL is concise and easy to read, we mean it.

MEL:

.. python::

    string $sel[] = `ls -sl`;
    string $shapes[] = `listRelatives -s $sel[0]`;
    string $conn[] = `listConnections -s 1 -d 0 $shapes[0]`;
    setAttr ( $conn[0] + ".radius") 3;

PyMEL

.. python::
    
    selected()[0].getShape().inputs()[0].radius.set(3)      


-----------------------------
For the Technical Director
-----------------------------

For those looking to master python in a production environment, PyMEL is more than a module for Maya scripting, 
it is a repository of example python code -- a self-contained pipeline demonstrating 
advanced python concepts like function factories, metaclasses, and decorators, as well as essential production practices such as parsing, pickling, logging, and unit testing.

For those who are already masters of python and who naturally expect more out of a python package, PyMEL is for you, too.  It was written in real production environments by 
programmers with a vision for how to seamlessly integrate the API and MEL.


======================
Core Features
======================

----------------------
Powerful Classes
----------------------

**Node classes** for every node type

.. python::

    camTrans, cam = camera()
    cam.setFocalLength(100) 
    fov = cam.getHorizontalFieldOfView()
    cam.dolly( -3 )
    cam.track(left=10)
    cam.addBookmark('new')



An **Attribute class** organizes all the attribute commands in one place

.. python::
    
    s = polySphere()[0]
    if s.visibility.isKeyable() and not s.visibility.isLocked():
        s.visibility.set( True )
        s.visibility.lock()
        print s.visibility.type()


Manipulate **file paths** with ease

.. python::

    #backup all mb files in the current scene's directory
    basedir = sceneName().parent
    backupDir = basedir / "backup" #slash op joins paths
    if not backupDir.exists:
        backupDir.mkdir()
    for file in basedir.files( '*.mb' ):
        print "backing up: ", file.name
        file.copy( backupDir / (file.namebase + ".old") )

Work with shape **components**, perform **vector math**, and easily set object attributes with the results

.. python::

    #select all faces that point up in world space
    s = polySphere()[0]
    for face in s.faces:
        if face.getNormal('world').y > 0.0:
           select( face, add=1)

Manage optionVars as a python dictionary 

.. python::

    if 'numbers' not in optionVar:
        optionVar['numbers'] = [1,24,47]
    optionVar['numbers'].append(9)
    numArray = optionVar.pop('numbers')

---------------------------
Do More with Less Code
---------------------------

If you've tried working with the default maya.cmds and maya.mel modules, you know that they add a lot of awkward syntax that can slow you down. PyMEL streamlines
this syntax in many ways.

Unlike maya.cmds, PyMEL is safe to import into the main namespace, so you don't have to prefix all your commands:

.. python::

    # default
    cmds.select( cmds.ls() )
    
    # PyMEL
    select( ls() )

PyMEL provides customized **operators** for succinct scripting:

.. python::
        
    cam = camera()[0]
    sphere = polySphere()[0]
    sphere | cam  # parent the camera to the sphere
    
    cam.tx >> cam.ty  # connect operator
    cam.tx // cam.ty  # disconnect operator




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
            cmds.setAttr( *args ,  type= 'stringArray' )
    
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
PyMEL
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
        x.setAttr( 'newAt', x.getShape().history(), force=1 )
        
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


cmds.file( newFile=1, force=1)
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
        shape = cmds.listRelatives( x, s=1, f=1 )
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
newFile( force=1 )
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
