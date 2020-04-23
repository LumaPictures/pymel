.. currentmodule:: pymel.core.general

=======================================
Non-Existent Objects
=======================================

You cannot instantiate a `PyNode` for an object which does not exist.  An exception will be raised if the passed name does not represent an object in the scene. This has several advantages:

    1. you will never unwittingly attempt to use a node or attribute that does not exist, either due to a typo or unexpected context
    2. it brings PyMEL's attribute handling more in line with pythonic rules, where attributes must exist before accessing them
    3. it prevents the awkward situation of having a python object for which only a handful of methods will actually work


---------------------------------------
PyMEL Exceptions
---------------------------------------

PyMEL has three exceptions which can be used to test for existence errors when creating new PyNodes: `MayaObjectError`, 
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
use `AttributeError` to catch both.


Explicit notation::

    >>> x = polySphere(name='earth')[0]
    >>> x.attr('myAttr')
    Traceback (most recent call last):
        ...
    MayaAttributeError: Maya Attribute does not exist: u'earth.myAttr'
    
Shorthand notation::

    >>> x = polySphere(name='moon')[0]
    >>> x.myAttr
    Traceback (most recent call last):
        ...
    AttributeError: Transform(u'moon') has no attribute or method named 'myAttr'
    
---------------------------------------
Testing Node Existence
---------------------------------------
        
Still supported::

    >>> if objExists('fooBar'): 
    ...     print "It Exists"
    ... else:
    ...     print "It Doesn't Exist"
    It Doesn't Exist
    
PyMEL construct::

    >>> try:
    ...     PyNode('fooBar')
    ...     print "It Exists"
    ... except MayaObjectError:
    ...     print "It Doesn't Exist"
    It Doesn't Exist
    
---------------------------------------
Testing Attribute Existence
---------------------------------------

Still supported::

    >>> if objExists('persp.spangle'):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
            
PyMEL construct::

    >>> x = PyNode('persp') 
    >>> if x.hasAttr('spangle'):
    ...     print "Attribute Exists"
    ... else:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

PyMEL construct::

    >>> try:
    ...     PyNode( 'persp.spangle' )
    ...     print "Attribute Exists"
    ... except MayaAttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist

PyMEL construct::

    >>> x = PyNode('persp') 
    >>> try:
    ...     x.spangle
    ...     print "Attribute Exists"
    ... except AttributeError:
    ...     print "Attribute Doesn't Exist"
    Attribute Doesn't Exist
      
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
same effect::

    >>> PyNode('lambert1')
    nt.Lambert('lambert1')
    >>> DependNode('lambert1')
    nt.Lambert('lambert1')

If the determined type does not match the requested type, an error will be raised.  For example, a lambert node is not
a DAG node::

    >>> nt.DagNode('lambert1')
    Traceback (most recent call last):
    ...
    TypeError: Determined type is Lambert, which is not a subclass of desired type DagNode

This is useful because it can be used as a quick way to assert that a given node is of the desire type. ::

    >>> select('lambert1') # this line represents user action
    >>> try:
    ...    nt.DagNode( selected()[0] )
    ... except TypeError:
    ...    print "Please select a DAG node"
    Please select a DAG node
 