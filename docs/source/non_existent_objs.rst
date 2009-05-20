.. currentmodule:: pymel

=======================================
Non-Existent Objects
=======================================

Previous versions of PyMEL allowed you to instantiate classes for non-existent objects.  This was common practice for testing 
object existence using PyNode.exists and could also be useful in circumstances where
you wished to use name formatting methods.

Starting with this version, an exception will be raised if the passed name does not represent an object in the scene. This has 
several advantages:

    1. you will never unknowingingly attempt to use a node or attribute that does not exist, either due to a typo or unexpected context
    2. it brings PyMEL's attribute handling more in line with pythonic rules, where attributes must exist before accessing them
    3. it prevents the awkward situation of having a python object for which only a handful of methods will actually work
    
The side-effect, however, is that certain conventions for existence testing are no longer supported, while new ones have also been added.


---------------------------------------
Compatibility Mode
---------------------------------------

We realize this is a big change so we have provided an option in the new ``pymel.cfg`` file ( found in the root of the pymel directory )
called '0_7_compatibility_mode'. When enabled, this option causes PyMEL to treat non-existent objects in a similar fashion to version 0.7.x:

    >>> x = PyNode( 'nonExistentNodeName' ) # doctest: +SKIP
    >>> x # doctest: +SKIP
    DependNodeName('nonExistentNodeName') 
    >>> x.exists() # doctest: +SKIP
    False

When the Maya node or attribute does not exists, the python object returned is not a subclass of PyNode, but rather of `other.NameParser`.  
For more information see `Manipulating Names of Non-Existent Objects`_.  Also, keep in mind that the behavior of "compatibility mode" 
is deprecated and will not be supported in PyMEL 1.0 ( unless, of course, there is strong public support to keep it ).

---------------------------------------
New Exceptions
---------------------------------------

We've added three new exceptions which can be used to test for existence errors when creating new PyNodes: `MayaObjectError`, 
`MayaNodeError`, and `MayaAttributeError`. 
    
    >>> for x in [ 'fooBar.spangle', 'superMonk' ] :
    ...     try:
    ...         PyNode( x )
    ...         print "It Exists"
    ...     except MayaNodeError:
    ...         print "The Node Doesn't Exist:", x
    ...     except MayaAttributeError:
    ...         print "The Attribute Doesn't Exist:", x
    ...
    The Attribute Doesn't Exist: fooBar.spangle
    The Node Doesn't Exist: superMonk

Both exceptions can be caught by using the parent exception `MayaObjectError`. In addition `MayaAttributeError` can also be caught
with the builtin exception `AttributeError`.

Note that you will get different exceptions depending on how you access the attribute. This is because the shorthand notation can also
be used to access functions, in which case the `MayaAttributeError` does not make sense to raise.  As mentioned above, you can always
use AttributeError to catch both.


Explicit notation:
    >>> x = polySphere(name='earth')[0]
    >>> x.attr('myAttr')
    Traceback (most recent call last):
        ...
    MayaAttributeError: Maya Attribute does not exist: u'earth.myAttr'
    
Shorthand notation:
    >>> x = polySphere(name='moon')[0]
    >>> x.myAttr
    Traceback (most recent call last):
        ...
    AttributeError: Transform(u'moon') has no attribute or method named 'myAttr'
    
---------------------------------------
Testing Node Existence
---------------------------------------

No longer supported:
    >>> if PyNode( 'fooBar' ).exists(): #doctest: +SKIP
    ...     print "It Exists"
    ... else:
    ...     print "It Doesn't Exist"
    It Doesn't Exist
        
Still supported:
    >>> if objExists( 'fooBar' ): 
    ...     print "It Exists"
    ... else:
    ...     print "It Doesn't Exist"
    It Doesn't Exist
    
New construct:
    >>> try:
    ...     PyNode( 'fooBar' )
    ...     print "It Exists"
    ... except MayaObjectError:
    ...     print "It Doesn't Exist"
    It Doesn't Exist
    
---------------------------------------
Testing Attribute Existence
---------------------------------------

No longer supported:
    >>> if PyNode( 'persp.spangle' ).exists(): #doctest: +SKIP
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
    
No longer supported:
    >>> x = PyNode('persp') 
    >>> if x.spangle.exists(): #doctest: +SKIP
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

Still supported:
    >>> if objExists( 'persp.spangle' ):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
            
New construct:    
    >>> x = PyNode('persp') 
    >>> if x.hasAttr('spangle'):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

New construct:
    >>> try:
    ...     PyNode( 'persp.spangle' )
    ...     print "Attribute Exists"
    ... except MayaAttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

New construct:
    >>> x = PyNode('persp') 
    >>> try:
    ...     x.spangle
    ...     print "Attribute Exists"
    ... except AttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
    
---------------------------------------
Other PyMEL Idioms
---------------------------------------
Two other PyMEL idioms have been removed as a result of this change. `Attribute.add` has been removed because the attribute has to exist
in order to successfully get an Attribute instance.  Instead, you should use the ``addAttr`` method on the node:


No longer supported:
    
    >>> PyNode('persp').myNewFloatAttr.add( at=float ) #doctest: +SKIP
    
Still supported:

    >>> PyNode('persp').addAttr( 'myNewFloatAttr', at=float )

Similarly, the ``force`` flag for setAttr functions, which creates the attribute before setting if it does not exist, can only be safely used from the node class
and not the attribute class:

No longer supported:
  
    >>> PyNode('persp').myNewIntAttr.set( 2, force=1 ) #doctest: +SKIP

Still supported:

    >>> PyNode('persp').setAttr( 'myNewIntAttr', 2, force=1 )

New construct:
 
    >>> PyNode('persp').setDynamicAttr( 'myNewIntAttr', 2 )
      
--------------------------------------------
Manipulating Names of Non-Existent Objects
--------------------------------------------

One advantage of the old way of dealing with non-existent objects was that you could use the name parsing methods of the PyNode
classes to manipulate the object's name until you found what you were looking for.  To allow for this, we've added
several classes which operate on non-existent nodes and contain only methods for string parsing and existence testing.
These nodes can be found in the `other` module and are named `other.NameParser`, `other.AttributeName`, `other.DependNodeName`, 
and `other.DagNodeName`.


--------------------------------------------
Asserting Proper Type
--------------------------------------------

While `PyNode` serves to easily cast any string to its proper class in the node hierarchy, other nodes in the hierarchy can achieve the 
same effect:

    >>> PyNode('lambert1')
    Lambert(u'lambert1')
    >>> DependNode('lambert1')
    Lambert(u'lambert1')

If the determined type does not match the requested type, an error will be raised.  For example, a lambert node is not
a DAG node:

    >>> DagNode( 'lambert1' )
    Traceback (most recent call last):
    ...
    TypeError: Determined type is Lambert, which is not a subclass of desired type DagNode

This is useful because it can be used as a quick way to assert that a given node is of the desire type.

    >>> select( 'lambert1' ) # this line represents user action
    >>> try:
    ...    DagNode( selected()[0] )
    ... except TypeError:
    ...    print "Please select a DAG node"
    Please select a DAG node
 