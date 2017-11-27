
Python in Maya Done Right
=========================

PyMEL makes python scripting with Maya work the way it should.

Maya's command module is a direct translation of mel commands into python commands. The result is a very awkward and unpythonic syntax which does not take advantage of python's strengths -- particulary, a flexible, object-oriented design. PyMEL builds on the `maya.cmds` module by organizing its commands into a class hierarchy, and by customizing them to operate in a more succinct and intuitive way.

Project Goals
-------------

- Create an open-source python module for Maya that is intuitive to MEL users and python users alike
- Fix bugs and design limitations in Maya's python modues, maya.cmds and maya.mel
- Keep code concise and readable
- Add organization through class hierarchy and sub-modules
- Provide documentation accessible via html and the builtin `help() function
- Make it "just work"

Production Proven
-----------------

Since its release in 2008, PyMEL has accumulated an impressive resume in both feature films and games, and is now bundled with every release of Maya.

Here's what Seth Gibson of Bungie Studios, makers of *Halo*, has to say:

> Having done production python code myself for many years, wrapping my head around Maya's native implementation took a little bit of time. With PyMel, I can think and write the python code and syntax I'm already used to, which speeds up my development time considerably. It's also going to help our other Technical Artists with their Python learning curve, since PyMEL's syntax is consistent with most other python packages. Kudos to the PyMel team for such a well thought out project!

BSD License
-----------

PyMEL is released under the BSD license, which is as open as open source gets. Your studio can freely use, contribute to, and modify this module with no strings attached.

Features
--------

### API Hybridization

PyMEL harnesses the API to create a name-independent representation of your object. This means that the annoying inconsistencies of string comparisons are over: no more worrying about short names versus long names, DAG paths, unique paths, instance paths... it's all handled intelligently for you. And what's more, if anything causes the name of your object to change it will automatically be reflected in your python object.

PyMEL node classes now include hundreds of new methods derived from the API, but with the same intuitive and unified design as before. With PyMEL you get the benefits of API speed and versatility without the advanced learning curve.

### Improved Batch / Standalone Support

Ever wonder why python scripts that work in the Maya UI or in Maya batch don't work in Maya's python interpreter?  Here's a possible explanation: in both GUI and batch modes Maya sources all of its lowest-level MEL scripts, like those that load user plugins, whereas mayapy and `maya.initialize` does not.

PyMEL ensures that Maya is properly initialized when used from Maya's python interpreter, which makes runtime environments more consistent and your scripts more portable, which adds up to fewer bugs.

### Tighter MEL Integration

Executing a MEL script with arguments can be an unsightly mess when done the default way:

**default**
```python
values = ['one', 'two', 'three', 'four']
maya.mel.eval('stringArrayRemoveDuplicates({"'+'","'.join(values)+'"})')
```

So PyMEL provides a handy interface which makes calling MEL procedures just like calling a python function:

**PyMEL**
```python
values = ['one', 'two', 'three', 'four']
pm.mel.stringArrayRemoveDuplicates(values)
```

Also, unlike `maya.mel.eval`, PyMEL will give you the specific MEL error message in a python traceback, along with line numbers:

```python
>>> mel.myScript('foo', [])
Traceback (most recent call last):
    ...
MelConversionError: Error occurred during execution of MEL script: line 2: Cannot convert data of type string[] to type float.
```

Also, getting and setting MEL global variables is as easy as working with a dictionary:

```python
print pm.melGlobals['gMainFileMenu']
pm.melGlobals['gGridDisplayGridLinesDefault'] = 2
```

### Powerful Classes

#### Nodes

```python
camTrans, cam = pm.camera()  # create a new camera
cam.setFocalLength(100)
fov = cam.getHorizontalFieldOfView()
cam.dolly(-3)
cam.track(left=10)
cam.addBookmark('new')
```

#### Attributes

```python
s = pm.polySphere()[0]
if s.visibility.isKeyable() and not s.visibility.isLocked():
    s.visibility.set(True)
    s.visibility.lock()
    print s.visibility.type()
```

#### File paths

backup all mb files in the current scene's directory

```python
basedir = pm.sceneName().parent
backupDir = basedir / "backup" #slash op joins paths
if not backupDir.exists:
    backupDir.mkdir()
for path in basedir.files('*.mb'):
    print "backing up: ", path.name
    path.copy(backupDir / (path.namebase + ".old"))
```

#### Shape components and vectors/matrices

select all faces that point up in world space

```python
s = pm.polySphere()[0]
for face in s.faces:
    if face.getNormal('world').y > 0.0:
       pm.select(face, add=1)
```

#### optionVars dictionary

```python
if 'numbers' not in pm.optionVar:
    pm.optionVar['numbers'] = [1, 24, 47]
pm.optionVar['numbers'].append(9)
numArray = pm.optionVar.pop('numbers')
```

Who is PyMEL for?
-----------------

### For the Novice

Object-oriented programming, like that provided by PyMEL, is more intuitive to learn because the functionality of an object is directly associated with the object itself.

For an artist starting to program in Maya, the first question you might ask is "what can I do with this node?" Using a procedural approach, like that offered by MEL or maya.cmds, you'll have to dig through the thousands of MEL commands looking for the one that you want. For a camera node, the `camera` MEL command is easy to find, but did you find `orbit`, `track`, `dolly`, and `tumble`, which also work on cameras?  What about the API methods?

In PyMEL, all you have to do is type `help(nt.Camera)` in the python script editor to find out all the things a camera node can do, or just look up the Camera class in the PyMEL docs.

### For the MEL Scripter

When we say PyMEL is concise and easy to read, we mean it.

***MEL***

```mel
string $sel[] = `ls -sl`;
string $shapes[] = `listRelatives -s $sel[0]`;
string $conn[] = `listConnections -s 1 -d 0 $shapes[0]`;
setAttr ( $conn[0] + ".radius") 3;
```

***PyMEL***

```python
pm.selected()[0].getShape().inputs()[0].radius.set(3)
```

### For the Technical Director

For those looking to master python in a production environment, PyMEL is more than a module for Maya scripting, it is a repository of example python code -- a self-contained pipeline demonstrating advanced python concepts like function factories, metaclasses, and decorators, as well as essential production practices such as parsing, pickling, logging, and unit testing.

For those who are already masters of python and who naturally expect more out of a python package, PyMEL is for you, too. It was written for use in production by experiened programmers with a vision for how to add object-oriented design to Maya.

Code Comparison
---------------

**with Mel**

```mel
string $objs[] = `ls -type transform`;
for ($x in $objs) {
    print (longNameOf($x)); print "\n";

    // make and break some connections
    connectAttr( $x + ".sx") ($x + ".sy");
    connectAttr( $x + ".sx") ($x + ".sz");

    // disconnect all connections to .sx
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
        $elements += """ + $elem + "" ";
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

    // call a mel procedure
    myMelScript( `nodeType $x`, $trans );
}
```

**with default Python**

```python
import maya.cmds as cmds
objs = cmds.ls(type='transform')
# returns None when it finds no matches
if objs is not None:
    for x in objs:
        print mm.eval('longNameOf("%s")' % x)

        # make and break some connections
        cmds.connectAttr('%s.sx' % x,  '%s.sy' % x)
        cmds.connectAttr('%s.sx' % x,  '%s.sz' % x)

        # disconnect all connections to .sx
        conn = cmds.listConnections(x + ".sx", s=0, d=1, p=1)
        # returns None when it finds no match:
        if conn is not None:
            for inputPlug in conn:
                cmds.disconnectAttr(x + ".sx", inputPlug)

        # add and set a string array attribute with the history of this transform's shape
        if not mm.eval('attributeExists "newAt" "%s"' % x):
            cmds.addAttr(x, ln='newAt', dataType='stringArray')
        shape = cmds.listRelatives(x, s=1 )
        if shape is not None:
            history = cmds.listHistory( shape[0] )
        else:
            history = []
        args = tuple(['%s.newAt' % x, len(history)] + history)
        cmds.setAttr(*args,  type='stringArray' )

        # get and set some attributes
        cmds.setAttr('%s.rotate' % x, 1, 1, 1)
        scale = cmds.getAttr('%s.scale' % x)
        # maya packs the previous result in a list for no apparent reason:
        scale = scale[0]
        # the tuple must be converted to a list for item assignment:
        trans = list(cmds.getAttr('%s.translate' % x )[0])  
        trans[0] *= scale[0]
        trans[1] *= scale[1]
        trans[2] *= scale[2]
        cmds.setAttr('%s.scale' % x, trans[0], trans[1], trans[2])
        # call a mel procedure
        mm.eval('myMelScript("%s",{%s,%s,%s})' % (cmds.nodeType(x), trans[0], trans[1], trans[2]))
```

**with Pymel**

```python
# safe to import into main namespace (but only recommended when scripting interactively)
from pymel import *
for x in ls( type='transform'):
    # object oriented design
    print x.longName()

    # make and break some connections
    x.sx.connect(x.sy)
    x.sx.connect(x.sz)
    # disconnect all connections to .sx
    x.sx.disconnect()

    # add and set a string array attribute with the history of this transform's shape
    x.setAttr('newAt', x.getShape().history(), force=1)

    # get and set some attributes
    x.rotate.set([1, 1, 1])
    trans = x.translate.get()
    # vector math:
    trans *= x.scale.get()
    # ability to pass list/vector args
    x.translate.set(trans)
    # call a mel procedure
    mel.myMelScript(x.type(), trans)
```

there's a reason why python is rapidly becoming the industry stanadard. with pymel, python and maya finally play well together.

---

Pymel is developed and maintained by [Luma Pictures](http://www.lumapictures.com).
