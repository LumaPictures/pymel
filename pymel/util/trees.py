r"""

A tree module that can wrap either pure python tree implementation or the networkx library if present

########################################################################
WARNING: this module may be removed in the future, or radically altered.
We do NOT recommend using it in external code...
########################################################################

>>> # Create a tree from nested sequences:
>>> myTree = Tree('a', ('ab', 'aa', 'x', '_'))
>>> print(myTree)
('a', ('ab', 'aa', 'x', '_'))
>>> print(myTree.formatted())
+: a
|--: ab
|--: aa
|--: x
\--: _
>>> myTree.sort()
>>> print(myTree.formatted())
+: a
|--: _
|--: aa
|--: ab
\--: x
>>>
>>> # Forests
>>> # -------
>>> # We can make a forest by passing in multiple args to the constructor
>>> myForest = Tree(1, 2, 3)
>>> for top in myForest.tops():
...     print(top.value)
... 
1
2
3
>>> print(myForest.formatted())
-: 1
<BLANKLINE>
-: 2
<BLANKLINE>
-: 3
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Python implementation inspired from Gonzalo Rodrigues "Trees and more trees" in ASPN cookbook

# removed as it's 2.5 only
# import functools as ftools
from past.builtins import cmp
from builtins import next
from builtins import range
from builtins import object
from collections import *
import inspect
import warnings
import weakref as weak
from copy import *
from functools import reduce
from future.utils import PY2, with_metaclass

#import logging
#_logger = logging.getLogger(__name__)
useNetworkx = False
networkxLoad = False
# if useNetworkx :
#    try :
#        import networkx.tree as nt
#        networkxLoad = True
#    except :
#        _logger.info("Library 'networkx' not present")
#        networkxLoad = False
#
# if networkxLoad :
#    _logger.info("Trees module will use networkx library")
# else :
#    _logger.info("Trees module will use pure python implementation")

# Utility


def isSequence(x):
    return type(x) is list or type(x) is tuple


def isTree(x):
    return (type(type(x)) is MetaTree)


def isImmutableTree(x):
    if isTree(x):
        return x.__getattribute__('parent').fset is None
    else:
        return False


def isMutableTree(x):
    if isTree(x):
        return x.__getattribute__('parent').fset is not None
    else:
        return False


# decorator to identify mutable methods (that are only valid for mutable trees)
def mutabletree(f):
    f.mutabletree = True
    return f


# to create Tree classes
class MetaTree(type):

    """ This metaclass defines the type of all 'tree' classes """

    class PyTree(object):

        """Core methods for pure python trees implementation"""
        # these are the methods depending on implementation
        # a weak ref proxy of the parent/super (containing Tree) to allow faster parent lookup methods
        _pRef = None
        # the storage for value (top element of that tree)
        _value = None
        # the storage for subtrees, must be an iterable (and ordered if you want to have siblings order)
        # can be immutable or mutable
        _subtrees = None

        # Conversion to correct storage for subtrees
        def _toSubtree(cls, subtrees):
            """ Converts a list/tuple of subtrees to the appropriate date structure for that class
                Returns None for None or an empty list or tuple """
            if subtrees:
                return cls.TreeType(subtrees)
            else:
                return None
        _toSubtree = classmethod(_toSubtree)

        def __bool__(self):
            try:
                return (self._value is not None or self._subtrees is not None)
            except:
                return False

        def isElement(self):
            if self:
                return (self._value is not None and self._subtrees is None)
            else:
                return False

        def hasChilds(self):
            if self:
                return (self._subtrees is not None)
            else:
                return False
        # by default only define get methods, set will be defined if the data type is mutable
        # and properties than can be either read only or read-write will be (re)defined accordingly at class creation
        # we always return trees / elements which value an be read from the value property

        # to be bound to properties
        def _get_value(self):
            return self._value
        # only for mutable

        @mutabletree
        def _set_value(self, value):
            if value is not None:
                self._value = value

        def _get_parent(self):
            if self._pRef:
                # can remove
                if not self._pRef() is self:
                    return self._pRef()
                else:
                    raise RuntimeError("Loop detected in tree %r on parent "
                                       "of %s", (self, self._get_value()))
        # only for mutable

        @mutabletree
        def _set_parent(self, parent):
            if parent is None:
                # unparenting
                if self._pRef is None:
                    return
                else:
                    oldparent = self._pRef()
                    # FIXME : we more or less assume it's a list here using remove instead of more generic iterable methods
                    oldparent._subtrees.remove(self)
                    # clean old parent subtrees if it dropped to 0
                    l = len(tuple(oldparent._subtrees))
                    if l == 0:
                        oldparent._subtrees = None
                    elif l == 1:
                        # if old parent was a forest and now has only only child, get rid of the None root
                        if oldparent._get_value() is None:
                            c = tuple(oldparent._subtrees)[0]
                            oldparent._set_value(c._get_value())
                            oldparent._subtrees = c._subtrees
                    # remove reference from self to old parent
                    self._pRef = None
            elif isinstance(parent, self.__class__):
                if not parent is self:
                    # first unparent nicely if needed
                    if self._pRef is not None:
                        if self._pRef() is parent:
                            # what the fuss then ?
                            return
                        else:
                            # unparent
                            self._set_parent(None)
                    # then reparent as last child under 'parent'
                    # if self is actually a forest, we'll instead parent all childs of self
                    if self._get_value() is not None:
                        subs = [self]
                    elif self._subtrees is None:
                        subs = []
                    else:
                        subs = list(iter(self._subtrees))
                    for s in subs:
                        s._pRef = weak.ref(parent)
                        if parent._subtrees is None:
                            parent._subtrees = [s]
                        else:
                            # should not happen if the usual methods are used
                            for c in iter(parent._subtrees):
                                if c is s:          # not == of course
                                    raise RuntimeError("Self was already present in the childs of parent?")
                            parent._subtrees.append(s)
                    # now make self point to the new parent instead
                    if self._get_value() is None:
                        p = parent._get_parent()
                        self._pRef = weak.ref(p)
                        self._value = parent._value
                        self._subtrees = parent._subtrees
                else:
                    raise RuntimeError("Setting self parent to itself would create a loop in tree %r" % self)
            else:
                raise TypeError("Can only reparent self to same type '%s' than self, not to '%s'" % (type(self), type(parent)))

        def _get_next(self):
            try:
                return next(self.siblings())
            except StopIteration:
                return None

        @mutabletree
        def _set_next(self, next):
            parent = self._get_parent()
            if parent is not None:
                if parent._subtrees is not None:
                    l = len(tuple(parent._subtrees))
                    if l:
                        if next is None:
                            # nothing to do if self is unique child
                            if len(sseq) > 1:
                                # FIXME : we more or less assume it's a list here using remove instead of more generic iterable method
                                try:
                                    parent._subtrees.remove(self)
                                except ValueError:
                                    raise RuntimeError(u"Invalid tree, parent of self '%s' does not have self in its subtrees" % self.value)
                                parent._subtrees.append(self)
                        else:
                            if not isinstance(next, self.__class__):
                                next = self.__class__(next)
                            # nothing to do if self == next
                            if self != next:
                                it = iter(parent._subtrees)
                                for s in it:
                                    if s == self:
                                        try:
                                            n = next(it)
                                        except StopIteration:
                                            n = next(iter(parent._subtrees))
                                        # nothing to do is next is already self's next
                                        if n != next:
                                            # FIXME : we more or less assume it's a list here using remove and insert instead of more generic iterable methods
                                            parent._subtrees.remove(self)
                                            try:
                                                j = parent._subtrees.index(next)
                                            except ValueError:
                                                raise ValueError("Provided next element '%s' is not a sibling of self '%s'" % (next.value, self.value))
                                            parent._subtrees.insert(j, self)
                                # if self was not found, something is very wrong
                                raise RuntimeError(u"Invalid tree, parent of self '%s' does not have self in its subtrees" % self.value)
                    else:
                        raise RuntimeError(u"Invalid tree, parent of self '%s' has an empty subtrees list" % self.value)
                else:
                    raise RuntimeError(u"Invalid tree, parent of self '%s' has an empty subtrees list" % self.value)
            raise ValueError("Self has no parent, we can't change it's order in the list of its siblings, having none")
        # methods (for both mutable and immutable)

        def childs(self):
            """ Returns an iterator on all childs of self, or an empty iterator if self has no childs """
            if self._subtrees:
                return iter(self._subtrees)
            else:
                return iter(self.__class__.TreeType())

        def siblings(self):
            """ Returns an iterator on self siblings, not including self and starting with self next sibling,
                if self has no siblings (self has no parent or is unique child) then returns an empty iterator """
            parent = self._get_parent()
            if not parent:
                return iter(self.__class__.TreeType())
            else:
                cseq = tuple(parent.childs())
                for i in range(len(cseq)):
                    if cseq[i] is self:  # not ==
                        return iter(cseq[i + 1:] + cseq[:i])
                # self should be in it's parents subtrees
                raise RuntimeError(u"Invalid tree, parent of %s does not have this subtree in its 'childs'" % self.value)
        # Iterates as a nested tuple of values, the same format that can be passe back to init
        # that way if t is a Tree, Tree(list(t)) == Tree(tuple(t)) == t
        # use preorder, postorder, breadth for specific interations

        def __iter__(self):
            """Iterates first level of tree returning nested tuples for childs"""
            if self:
                if self.value:
                    yield self.value
                    childs = []
                    for subtree in self.childs():
                        childs += list(subtree.__iter__())
                    if childs:
                        yield tuple(childs)
                else:
                    for subtree in self.childs():
                        for tree in subtree.__iter__():
                            yield tree
        # To allow pickling (will leave weak refs out and rebuild the object on unpickling from the preorder list of elements)

        def __reduce__(self):
            return (self.__class__, tuple(self))
        # equivalence, __contains__
        # added equivalence test here

        def __eq__(self, other):
            """Checks for equality of two trees."""
            # Both trees not empty.
            if self and other:
                # Compare values.
                if self is other:
                    return True
                elif self.value != self.__class__(other).value:
                    return False
                elif len(self) != len(other):
                    return False
                else:
                    return reduce(lambda x, y: x and y, map(lambda c1, c2: c1 == c2, self.childs(), other.childs()), True)
            # Both trees empty.
            elif not self and not other:
                return True
            else:
                return False

        def __ne__(self, other):
            return not self.__eq__(other)
        # compare using only top value (if compare is defined for value type) or all values ?

        def __contains__(self, element):
            """Returns True if element is in the tree, False otherwise."""
            if isTree(element):
                for sub in self.breadth():
                    if element == sub:
                        return True
                return False
            else:
                for sub in self.breadth():
                    if element == sub.value:
                        return True
                return False
        # identity, not equivalence test

        def issubtree(self, other):
            if isinstance(other, self.__class__):
                parent = self
                while parent:
                    if parent is other:
                        return True
                    parent = parent.parent
            return False
        # get and __getitem
        # get the matching subtree to that subtree or element,
        # not that it can return a tuple if same element/subtree is present more than once in tree

        def __getitem__(self, value):
            """ Get a subtree from the Tree, given an element or value.
                Note that to be consistent with __getitem__ usual behavior, it will raise an exception
                it it doesn't find exactly one match (0 or more), method get will be more user friendly
                on non indexed trees.
                It's also possible to seek a path : a list of elements or values, it will limit the results
                to the subtrees that match the last item of the path, and whose parents match the path.
                A path can be relative, or absolute if starting with None as first item """
            result = self.get(value)
            l = len(result)
            if l == 1:
                return result[0]
            elif l == 0:
                raise KeyError("No  match for %s in Tree" % value)
            else:
                raise KeyError("More than one match for %s in Tree (%i found)" % (value, l))

        def get(self, value, default=tuple()):
            """ Identical to the __getitem__ method but will return a default value instead of raising KeyError
                if nor result is found """
            result = []
            # explore breadth first so that closest items are found faster
            if isTree(value):
                # do a faster check in case value is a subtree of self
                if value.issubtree(self):
                    return [value]
                # normal equivalence test
                for e in self.breadth():
                    if value == e:
                        result.append(e)
            elif isSequence(value):
                # we seek a path, a list of value that must be found in order,
                # if list starts with None it means it's an absolute path (starting at root)
                if value:
                    if value[0] is None:
                        result = [self]
                    else:
                        result += list(self.get(value[0]))
                    for p in value[1:]:
                        if result:
                            found = []
                            for t in result:
                                for c in t.childs():
                                    if c.value == self.__class__(p).value:
                                        found.append(c)
                            result = found
                        else:
                            break
            else:
                for e in self.breadth():
                    if value == e.value:
                        result.append(e)
            if not result:
                return default
            else:
                return tuple(result)
        # methods only for mutable : remove, __delitem__, add
        # remove

        @mutabletree
        def remove(self, element):
            """ Remove element from self, along with everything under it, will raise an exception if element is not in self """
            # TODO : only handle case where element is subtree of self here and let caller handle search for subtree from value
            self[element]._set_parent(None)
        # delete method

        @mutabletree
        def __delitem__(self, element):
            try:
                sub = self[element]
            except:
                raise ValueError("Tree does not contain element '%s'" % element)
            sub._set_parent(None)
            del sub

        # methods only for mutable
        @mutabletree
        def add(self, element, parent=None, next=None):
            """ Add an element to self. parent and next element can be specified.
                Element will be added as a child of parent, parent can be any element or subtree of self:
                if parent is specified as a value there must exactly one match in self or an exception will be raised
                if parent is None, element will be added as a sibling of self's top node(s)
                if next is not none, element will be added before next in the childs of parent, else as a last childs """
            if not isinstance(element, self.__class__):
                element = self.__class__(element)
            if parent is None:
                parent = self._get_parent()
                if parent is None:
                    value = self._get_value()
                    if value is not None:
                        # if self is not already a forest, make it one
                        subs = None
                        if self._subtrees is not None:
                            subs = list(iter(self._subtrees))
                        selfchild = self.__class__()
                        selfchild._pRef = weak.ref(self)
                        selfchild._set_value(value)
                        selfchild._subtrees = self.__class__._toSubtree(subs)
                        if subs:
                            for sub in subs:
                                sub._pRef = weak.ref(selfchild)
                        # must do manually
                        self._value = None
                        self._subtrees = self.__class__._toSubtree([selfchild])
                        # print self.debug()
                        # print selfchild.debug()
                    parent = self
            else:
                # parent must be actually a subtree of self, not a subtree of another tree that happens to be equal in value
                parent = self[parent]
            element._set_parent(parent)

        def __cmp__(self, other):
            return cmp(self.value, other.value)

        __le__ = lambda self, other: self.__cmp__(other) <= 0
        __lt__ = lambda self, other: self.__cmp__(other) < 0
        __ge__ = lambda self, other: self.__cmp__(other) >= 0
        __gt__ = lambda self, other: self.__cmp__(other) > 0

        @mutabletree
        def sort(self, *args):
            if self and self._subtrees:
                for subTree in self._subtrees:
                    subTree.sort(*args)
                self._subtrees.sort(*args)

        # set and __setitem__

        # Changed to not allow sequences to follow each other, as it was too
        # ambiguous/confusing, and ikely not what the user intended - ie, if
        # we do:
        # >>> myTree = Tree(list1, list2)
        # ...chances are, I'm not going to want to have to check what the values are of
        # list1 in order to know where in the tree list2 will be placed.
        #
        # For instance, old init will do this:
        # >>> list1 = (1,2)
        # >>> list2 = (3,4)
        # >>> tree1 = Tree(list1, list2)
        # >>> print tree1.formatted()
        # +
        # |--1
        # \-+2
        #   |--3
        #   \--4
        # >>> list1 = (1,('a', 'b'))
        # >>> tree2 = Tree(list1, list2)
        # >>> print tree2.formatted()
        # +
        # |-+1
        # | |--a
        # | \--b
        # |--3
        # \--4
        #
        # Thus, the depth at which list2 is placed is dependant on list1.
        # Likely not what we want... therefore, lists may now only follow
        # non-list values - entering the previous examples will now result in an
        # error.
        # To create the same structures, you would do:
        # >>> tree1 = Tree(1, 2, (3,4))
        # >>> print tree1.formatted()
        # >>> tree2 = Tree(1, ('a','b'), 3, 4)
        # >>> print tree2.formatted()

        # init, this can be overriden in class definition
        def __init__(self, *args, **kwargs):
            r"""
            Initializer - non-sequences are values, sequeneces are children of previous value.

            The args represent tree nodes, where a node is specified by either another tree
            object, or a non sequence representing the value of that node, optionally followed
            by a sequence representing the children of that node.

            Values cannot be None, and when specifying the elements in a child sequence, they
            must fit the same rules for valid tree nodes given above.

            Invalid arguments (ie, two sequences following each other) will raise a ValueError.

            If there is only one node (ie, only one non-sequence arg, optionally followed by
            a list of children), then a tree is returned, with the single node as it's
            single root.

            If there are multiple nodes, then a forest is returned, with each node
            representing a root.

            For speed and ease of use, if there is only a single argument, and it is a sequence,
            it is the same as though we had unpacked the sequence:

            >>> list = (1,('a','b'))
            >>> Tree(list) == Tree(*list)
            True

            Now, some examples:

            >>> myTree = Tree()  # makes an empty tree
            >>> print(myTree)
            ()
            >>> myTree = Tree(1)
            >>> print(repr(myTree)) # different ways of stringifying...
            Tree(1)
            >>> myTree = Tree(1,('a','b'))  # make a tree with children
            >>> print(myTree.formatted())
            +: 1
            |--: a
            \--: b
            >>> myTree = Tree(1,(2,'foo', ('bar',))) # tree with a subtree
            >>> myTree.view()
            +: 1
            |--: 2
            \-+: foo
              \--: bar
            >>> myForrest = Tree(1,2)   # make a forest
            >>> myForrest.view()        # view() is just shortcut for:
            ...                      # print treeInst.formatted()
            -: 1
            <BLANKLINE>
            -: 2
            >>> otherForrest = Tree('root1', myForrest, 'root4', ('kid1', 'kid2'))
            >>> otherForrest.view()
            -: root1
            <BLANKLINE>
            -: 1
            <BLANKLINE>
            -: 2
            <BLANKLINE>
            +: root4
            |--: kid1
            \--: kid2

            ...Note that a tree object, even if a forrest, will never be taken
            to represent the children of the previous arg - ie, the previous
            example did NOT result in:
            +: root1
            |--: 1
            \--: 2
            <BLANKLINE>
            +: root4
            |--: kid1
            \--: kid2

            This means that giving multiple forrest objects will effectively merge
            them into a larger forest:

            >>> forrest1 = Tree(1, 2)
            >>> forrest1.view()
            -: 1
            <BLANKLINE>
            -: 2
            >>> forrest2 = Tree('foo', 'bar')
            >>> forrest2.view()
            -: foo
            <BLANKLINE>
            -: bar
            >>> forrest3 = Tree(forrest1, forrest2)
            >>> forrest3.view()
            -: 1
            <BLANKLINE>
            -: 2
            <BLANKLINE>
            -: foo
            <BLANKLINE>
            -: bar

            Trying to give 2 sequences in a row results in a ValueError:

            >>> Tree('root1', (1,2), (3,4))
            Traceback (most recent call last):
              ...
            ValueError: Child sequence must immediately follow a non-sequence value when initializing a tree

            Similarly, trying to use 'None' as a tree value gives an error:
            >>> Tree(None, (1,2))
            Traceback (most recent call last):
              ...
            ValueError: None cannot be a tree element
            """
            # TODO: make it conform!
            parent = kwargs.get('parent', None)
            if parent is not None:
                pRef = weak.ref(parent)
            else:
                pRef = None

            if len(args) == 1 and isSequence(args[0]):
                args = args[0]

            roots = []
            previousWasValue = False
            for arg in args:
                isValue = False
                if isTree(arg):
                    # we need to do a shallow copy if it's not the same tree type, or not already a subtree of self
                    if isinstance(arg, self.__class__) and arg.parent is self:
                        avalue = arg.value
                        if avalue:
                            roots += [arg]                                        # one item in childs : the subtree
                        else:
                            roots += [c for c in arg.childs()]                    # all childs of subtree in childs
                    else:
                        avalue = arg.value
                        if avalue:
                            roots += [self.__class__(avalue, tuple(c for c in arg.childs()), parent=self)]     # one item in childs : the subtree
                        else:
                            roots += [self.__class__(c, parent=self) for c in arg.childs()]                    # all childs of subtree in childs
                elif isSequence(arg):
                    # we use sequences to encapsulate childs

                    # Check if the previous argument was a value,
                    # to see if this is a valid child list
                    if not previousWasValue:
                        raise ValueError('Child sequence must immediately follow a non-sequence value when initializing a tree')

                    childs = []
                    d = {'parent': self}
                    sub = self.__class__(*arg, **d)
                    if sub.value:
                        childs = [sub]
                    else:
                        childs = list(sub.childs())
                    # add resulting childs if any
                    if childs:
                        # parent to previous entry, childs are already self.__class__ copies
                        # coming from a sequence expansion
                        for c in childs:
                            c._pRef = weak.ref(roots[-1])
                        roots[-1]._subtrees = self.__class__._toSubtree(childs)
                elif arg is not None:
                    isValue = True
                    # argument at top level is a root
                    sub = self.__class__()
                    sub._pRef = pRef
                    sub._value = arg
                    roots.append(sub)

                else:
                    raise ValueError("None cannot be a tree element")
                previousWasValue = isValue

            if not roots:
                self._pRef = None
                self._value = None
                self._subtrees = None
            elif len(roots) == 1:
                # we don't need the None root if the tree is not a forest
                self._pRef = pRef
                self._value = roots[0]._value               # roots is filled with copies so not need to copy again
                self._subtrees = roots[0]._subtrees
            else:
                # more than one root, a None root as added on top
                self._pRef = pRef
                self._value = None
                self._subtrees = self.__class__._toSubtree(roots)
            # update the weak refs of childs to self
            for sub in self.childs():
                sub._pRef = weak.ref(self)

    class IndexedPyTree(object):

        """ Additionnal methods for pure python indexed trees implementation, elements must have unique values
            or Tree class must define a key method that provides a unique key for each element """
        # To the PyTree methods an index that for each of the subtree elements (as keys)
        # keeps a weak references to the subtree
        _index = weak.WeakValueDictionary()

        # unique key based on top element value, by default just return element value
        # but can be overriden. For instance use long name instead of just short name for a a node
        # will allow to store a hierarchy of Maya nodes with duplicate names
        def _get_key(self):
            return self._value
        # key of an element relative to self, returns a tuple of keys for the whole path self-> element

        def elementKey(self, element):
            pass

        # _set_parent must update the index of the parent
        @mutabletree
        def _set_parent(self, parent):
            oldparent = self.parent
            super(IndexedPyTree, self)._set_parent(parent)
            if parent != oldparent:
                oldparent._index.pop(self._get_key())
                for sub in self.preorder():
                    parent._index[sub._get_key()] = sub
        # indexing will allow more efficient ways for the following methods than with non indexed trees
        # equivalence, __contains__
        # added equivalence test here
#        def __eq__(self, other):
#            """Checks for equality of two trees."""
#            #Both trees not empty.
#            if self and other:
#                #Compare values.
#                if self is other :
#                    return True
#                elif self.value != self.__class__(other).value:
#                    return False
#                elif len(self) != len(other) :
#                    return False
#                else :
#                    return reduce(lambda x, y:x and y, map(lambda c1, c2:c1 == c2, self.childs(), other.childs()), True)
#            #Both trees empty.
#            elif not self and not other:
#                return True
#            else:
#                return False
#        def __ne__(self, other):
#            return not self.__eq__(other)
#        # compare using only top value (if compare is defined for value type) or all values ?
#        def __contains__(self, element):
#            """Returns True if element is in the tree, False otherwise."""
#            if self :
#                if not isinstance(element, self.__class__) :
#                    element = self.__class__(element)
#                return self._index.has_key(element._get_key())
#            else :
#                return False
#        # identity, not equivalence test
#        def issubtree(self, other) :
#            if isinstance(other, self.__class__) :
#                key = self._get_key()
#                if other._index.has_key(key) :
#                    return other._index[key] is self
#            return False
        # get and __getitem
        # get the matching subtree to that subtree or element, will be redefined in the case of an indexed tree
        # not that it can return a tuple if same element/subtree is present more than once in tree

        def __getitem__(self, value):
            """ Get a subtree from the Tree, given an element or value.
                Note that to be consistent with __getitem__ usual behavior, it will raise an exception
                it it doesn't find exactly one match (0 or more), method get will be more user friendly
                on non indexed trees.
                It's also possible to seek a path : a list of elements or values, it will limit the results
                to the subtrees that match the last item of the path, and whose parents match the path.
                A path can be relative, or absolute if starting with None as first item """
            result = self.get(value)
            l = len(result)
            if l == 1:
                return result[0]
            elif l == 0:
                raise KeyError("No  match for %s in Tree" % value)
            else:
                raise KeyError("More than one match for %s in Tree (%i found)" % (value, l))

        def get(self, value, default=tuple()):
            """ Identical to the __getitem__ method but will return a default value instead of raising KeyError
                if nor result is found """
            result = []
            # use index for faster find
            if isTree(value):
                # do a faster check in case value is a subtree of self
                if value.issubtree(self):
                    return [value]
                # normal equivalence test
                for e in self.breadth():
                    if value == e:
                        result.append(e)
            elif isSequence(value):
                # we seek a path, a list of value that must be found in order,
                # if list starts with None it means it's an absolute path (starting at root)
                if value:
                    if value[0] is None:
                        result = [self]
                    else:
                        result += list(self.get(value[0]))
                    for p in value[1:]:
                        if result:
                            found = []
                            for t in result:
                                for c in t.childs():
                                    if c.value == self.__class__(p).value:
                                        found.append(c)
                            result = found
                        else:
                            break
            else:
                for e in self.breadth():
                    if value == e.value:
                        result.append(e)
            if not result:
                return default
            else:
                return tuple(result)

    class NxTree(object):

        """ Core methods for trees based on the networkx library, these trees are indexed by implementation (name of an element must be unique) """

    # now the methods for an immutable tree, not depending on implementation
    class ImTree(object):

        """The methods for an immutable Tree class."""

        # Iterators all returns trees/elements, use the value property to get value
        # note: inorder traversal could be defined for binary trees
        def preorder(self):
            """The standard preorder traversal iterator."""
            if self:
                yield self
                for subtree in self.childs():
                    for tree in subtree.preorder():
                        yield tree

        def postorder(self):
            """Postorder traversal of a tree."""
            if self:
                for subtree in self.childs():
                    for tree in subtree.postorder():
                        yield tree
                yield self

        def breadth(self):
            """Breadth first traversal of a tree."""
            if self:
                yield self
                deq = deque(x for x in self.childs())
                while deq:
                    arg = deq.popleft()
                    yield arg
                    for a in arg.childs():
                        deq.append(a)

        def child(self, index=0):
            """ Returns nth child (by default first), is it exists """
            try:
                childs = [k for k in self.childs()]
                return childs[index]
            except:
                return None

        def parents(self):
            """Returns an iterator on path from element to top root, starting with first parent, empty iterator means self is root"""
            #parents = []
            #parent = self.parent
            # while parent :
            #    parents.append(parent)
            #    parent = parent.parent
            # return iter(parents)
            parent = self.parent
            while parent:
                yield parent
                parent = parent.parent

        def root(self):
            """ Root node of self, if self is a subtree, will travel up to top most node of containing tree """
            root = self
            parent = self.parent
            while parent:
                if parent.value:
                    root = parent
                parent = parent.parent
            return root

        def tops(self):
            """ Iterator on the top nodes of self, the subtrees that have no parent in self,
                will yield only self if self isn't a forest """
            if self.value:
                yield self
            else:
                for c in self.childs():
                    yield c

        def top(self, index=0):
            """ The nth top node of self (by default first) """
            try:
                tops = [k for k in self.tops()]
                return tops[index]
            except:
                return None

        def depth(self):
            """Depth of self, the distance to self's root"""
            parents = self.parents()
            depth = 0
            for p in parents:
                depth += 1
            return depth

        def leaves(self):
            """ Get an iterator on all leaves under self """
            for elem in self.preorder():
                if not elem.hasChilds():
                    yield elem

        def level(self, dist=0):
            """ Get an iterator on all elements at the specified distance of self, negative distance means up, positive means down """
            deq = deque((self, 0))
            while deq:
                arg, level = deq.popleft()
                if level == dist:
                    yield arg
                elif level > dist:
                    if arg.parent:
                        deq.append((arg.parent, level - 1))
                else:
                    for c in arg.childs():
                        deq.append((c, level + 1))

        # Comparison, contains, etc
        # Number of elements in the tree.
        def size(self):
            """Returns the number of elements (nodes) in the tree."""
            ret = 0
            for s in self.preorder():
                ret += 1
            return ret
        # use it for len(self)
        __len__ = size

        def height(self):
            """ Get maximum downward depth (distance from element to furthest leaf downwards of it) of the tree """
            max_depth = 0
            deq = deque((self, 0))
            while deq:
                arg, level = deq.popleft()
                if arg.value:
                    level += 1
                if not arg.isElement():
                    for a in arg.childs():
                        deq.append((a, level))
                else:
                    if level > max_depth:
                        max_depth = level
            return max_depth

        # this can be redefined for trees where the uniqueness of the elements can allow a more efficient search
        def _pathIter(self, element, depth=0, found=None, down=False, up=False):
            # test if we have a hit
            if self == element:
                return ((self,), 0)
            # abort if a path of length 'found' that is not more than depth+! has been found,
            # as we will explore parent or childs of self, shortest path we can still
            # hope to find in this branch is of length depth+1
            if found is not None and not abs(found) > abs(depth) + 1:
                return ((), None)
            # else keep searching
            seekup = None
            seekdown = None
            dirup = None
            dirdown = None
            if up and self.parent:
                p_path, dirup = self.parent._pathIter(element, up=True, depth=depth - 1, found=found)
                if dirup is not None:
                    seekup = (self,) + p_path
                    dirup -= 1
                    found = dirup + depth
            # means if a match is found upwards and downwards at equal distance, the upwards match will be preferred
            if down and (found is None or abs(found) > abs(depth) + 1):
                bestdirdown = None
                for c in self.childs():
                    c_path, dirdown = c._pathIter(element, down=True, depth=depth + 1, found=found)
                    if dirdown is not None:
                        c_path = (self,) + c_path
                        dirdown += 1
                        if not bestdirdown or dirdown < bestdirdown:
                            seekdown = c_path
                            bestdirdown = dirdown
                            found = dirdown + depth
                            # no need to check rest of childs now if found is just depth + 1
                            if not dirdown > 1:
                                break
                # finally down distance is the best down distance found amongst childs
                dirdown = bestdirdown

            # retain shortest path and direction
            if dirup is not None and dirdown is not None:
                # for equal distance, prefer up
                if abs(dirup) <= abs(dirdown):
                    path = seekup
                    direction = dirup
                else:
                    path = seekdown
                    direction = dirdown
            elif dirup is not None:
                # found only upwards
                path = seekup
                direction = dirup
            elif dirdown is not None:
                # found only downwards
                path = seekdown
                direction = dirdown
            else:
                # not found
                path = ()
                direction = None

            return (path, direction)

        # note it's not a true iterator as anyway we need to build handle lists to find shortest path first
        def path(self, element=None, **kwargs):
            """ Returns an iterator of the path to specified element if found, including starting element,
                empty iterator means no path found.
                For trees where duplicate values are allowed, shortest path to an element of this value is returned.
                element can be an ancestor or a descendant of self, if no element is specified, will return path from self's root to self
                up keyword set to True means it will search ascendants(parent and parents of parent) self for element, default is False
                down keyword set to True means it will search descendants(childs and childs of childs) of self for element, default is False
                If neither up nor down is specified, will search both directions
                order keyword defines in what order the path will be returned and can be set to 'top', 'bottom' or 'self', order by default is 'top'
                'top' means path will be returned from ancestor to descendant
                'bottom' means path will be returned from descendant to ancestor
                'self' means path will be returned from self to element """
            # By default returns path from self's root to self
            if element is None:
                path = (self,) + tuple(self.parents())
                direction = -len(path)
            else:
                if not isTree(element):
                    element = self.__class__(element)
                up = kwargs.get("up", False)
                down = kwargs.get("down", False)
                if not (up or down):
                    up = down = True
                path, direction = self._pathIter(element, depth=0, found=None, up=up, down=down)
            # in what order to return path
            # default : by hierarchy order, top to down, but can be returned start (self) to end (element)
            if direction is not None:
                order = kwargs.get("from", 'top')
                if order is 'top':
                    if direction < 0:
                        path = tuple(reversed(path))
                elif order is 'bottom':
                    if direction > 0:
                        path = tuple(reversed(path))
                elif order is 'self':
                    path = tuple(path)
                else:
                    raise ValueError("Unknown order '%s'" % order)
            return iter(path)

        def dist(self, element, **kwargs):
            """ Returns distance from self to element, 0 means self==element, None if no path exists
                up keyword set to True means it will search ascendants(parent and parents of parent) self for element, default is False
                down keyword set to True means it will search descendants(childs and childs of childs) of self for element, default is False
                If neither up nor down is specified, will search both directions
                signed keyword set to true means returns negative distance when element is upwards self, positive when it's downwards """
            up = kwargs.get("up", False)
            down = kwargs.get("down", False)
            signed = kwargs.get("signed", False)
            if not (up or down):
                up = down = True
            path, direction = self._pathIter(element, depth=0, found=None, down=down, up=up)
            if not signed:
                direction = abs(direction)
            return direction

         # TODO: make it match new __init__
        # - use [] for child lists, () for value/children pairs
        # make str, unicode, repr
        # str, unicode, represent
        def _strIter(self):
            res = ""
            value = self.value
            if value is not None:
                res = "'%s'" % str(value)
            temp = [sub._strIter() for sub in self.childs()]
            if temp:
                if res:
                    res += ", (%s)" % ", ".join(temp)
                else:
                    res = ", ".join(temp)
            return res

        # TODO: make it match new __init__
        # - use [] for child lists, () for value/children pairs
        def __str__(self):
            if self:
                return "(%s)" % (self._strIter())
            else:
                return "()"

        if PY2:
            def _unicodeIter(self):
                res = u""
                value = self.value
                if value:
                    res = u"'%s'" % unicode(value)
                temp = [sub._unicodeIter() for sub in self.childs()]
                if temp:
                    if res:
                        res += u", (%s)" % u", ".join(temp)
                    else:
                        res = u", ".join(temp)
                return res

            def __unicode__(self):
                if self:
                    return u"(%s)" % (self._unicodeIter())
                else:
                    return u"()"

        def _reprIter(self):
            res = ""
            value = self.value
            temp = [sub._strIter() for sub in self.childs()]
            if value:
                res = "%r" % value
            if temp:
                if res:
                    res += ", (%s)" % ", ".join(temp)
                else:
                    res = ", ".join(temp)
            return res

        def __repr__(self):
            if self:
                return "%s(%s)" % (self.__class__.__name__, self._reprIter())
            else:
                return "()"

        def formatted(self, returnList=False):
            """ Returns an indented string representation of the tree """
            # Changed print character from '>', so that doctest doesn't get
            # confused!
            # ...also made it a little prettier

            hasBranchChar = "|-"  # Ideally, would look like '+' with no left arm
            noBranchChar = "| "
            endBranchChar = r"\-"  # Ideally, would look ike '+' with no left or bottom arm
            emptyBranchChar = "  "
            hasChildrenChar = "+: "  # Ideally, would look like '+' with no top arm
            noChildrenChar = "-: "
            treeSep = ''
            lines = []
            if self:
                value = self.value

                children = tuple(self.childs())

                if value is not None:
                    if children:
                        valuePrefix = hasChildrenChar
                    else:
                        valuePrefix = noChildrenChar
                    lines.append(valuePrefix + str(value))

                for childNum, child in enumerate(children):
                    childLines = child.formatted(returnList=True)
                    if len(childLines) > 0:
                        if value is None:
                            # we've got a forest - print all children 'as is'
                            childPrefix = grandChildPrefix = ""
                        elif childNum < (len(children) - 1):
                            # We've got a "middle" child - use 'hasBranchChar' and 'noBranchChar'
                            childPrefix = hasBranchChar
                            grandChildPrefix = noBranchChar
                        else:
                            # We've got an "end" child - use 'endBranchChar' and 'emptyBranchChar'
                            childPrefix = endBranchChar
                            grandChildPrefix = emptyBranchChar
                        lines.append(childPrefix + childLines[0])
                        for grandChild in childLines[1:]:
                            lines.append(grandChildPrefix + grandChild)
                    if value is None and childNum < (len(children) - 1):
                        # if we have a forest, add a treeSep between trees
                        lines.append(treeSep)

            if returnList:
                return lines
            else:
                return "\n".join(lines)

        def view(self):
            """
            Shortcut for print(self.formatted())
            """
            print(self.formatted())

        def debug(self, depth=0):
            """ Returns an detailed representation of the tree fro debug purposes"""
            if self:
                parent = self.parent
                pvalue = None
                if parent:
                    pvalue = parent.value
                next = self.__next__
                nvalue = None
                if next:
                    nvalue = next.value
                result = u">" * depth + u"r:%r<%i>" % (self.value, id(self))
                if parent:
                    result += ", p:%r<%i>" % (pvalue, id(parent))
                else:
                    result += ", p:None"
                if next:
                    result += ", n:%r<%i>" % (nvalue, id(next))
                else:
                    result += ", n:None"
                result += "\n"
                for a in self.childs():
                    result += a.debug(depth + 1)
                return result

        def copy(self, cls=None):
            """ Shallow copy of a tree.
                An extra class argument can be given to copy with a different
                (tree) class. No checks are made on the class. """
            if cls is None:
                cls = self.__class__
            if self:
                if self.value:
                    subtrees = (self.value, tuple(self.childs()))
                else:
                    subtrees = tuple(self.childs())
                return cls(*subtrees)
            else:
                return cls()

        # TODO : isParent (tree, other), isChild(tree, other), inter, union, substraction ?

    # now the methods for an mutable tree, not depending on implementation
    class MuTree(object):

        """Additionnal methods for a Mutable Tree class."""

        # Edit methods that are defined for mutable trees
        def __setitem__(self, element, value):
            pass

        def graft(self, element, parent=None, next=None):
            """ Attach element to self.
                If parent is secified, will be grafted as last child of parent (or before child 'next'),
                if parent is not in self, will raise an exception,
                if parent is None will be grafted at top level of self, besides any existing root(s).
                If next is specified, self will be grafted before next in the list of parent's childs,
                if next is not in parent's childs, will raise an exception,
                if next is None, self will be grafted as last child under parent. """
            self.add(element, parent, next)

        def prune(self, element):
            """ Ungrafts element from self, with everything under it """
            element = self[element]
            self.remove(element)

        def pop(self, element):
            """ Delete top node of self and reparent all it's subtrees under it's current parent.
                If self was a root all it's subtrees become separate trees of a forest under the 'None' root.
                self will now have the new parent as top node """
            element = self[element]
            parent = element.parent
            for c in element.childs():
                self.graft(c, parent)
            self.remove(element)

        # TODO: reroot, in-place intersection, union, sub etc
        def reroot(self, element):
            """ Reroot self so that element is self new top node """
            pass

    # class creation using the method of the above class to populate a new class depending on
    # class creation options (mutable, indexed, etc)
    def __new__(mcl, classname, bases, classdict):
        # Build a Tree class deriving from a base iterable class, base class must have methods __init__,  __iter__ and __nonzero__
        # by default use list
        #        if not bases :
        #            bases = (list, )
        # check if base meets requirement, either we derive from another Tree class or from the type that will be used for internal storage
        mutable = None
        indexed = None
        # check for keywords
        if 'mutable' in classdict:
            mutable = (classdict['mutable'] == True)
            del classdict['mutable']
        if 'indexed' in classdict:
            indexed = (classdict['indexed'] == True)
            del classdict['indexed']
        treeType = None
        # default storage types depending on type of tree
        if mutable:
            treeType = list
        else:
            treeType = tuple
        # check base classes
        newbases = []
        for base in bases:
            if type(base) == MetaTree:
                mubase = hasattr(base, 'add')
                inbase = hasattr(base, 'key')
                # Tree type is most complete type of all base classes
                if treeType == None or (not mutable and mubase) or (not indexed and inbase):
                    treeType = base._TreeType
                    mutable = mubase
                    indexed = inbase
            # if we need to filter base classes ?
            newbases.append(base)

        # if we couldn't determine a tree type from keywords or base classes, raise an exception
        if not treeType:
            raise TypeError("Tree classes must derive from another Tree class, or an iterable type that defines __init__, __iter__ and __nonzero__ at least")
        # store the type of iterable used to represent the class subtrees
        newbases = tuple(newbases)

        # build dictionnary for that class
        newdict = {}
        # methods depending on implementations
        coredict = {}
        # if networkx not present
        BaseCoreClass = []
        if not indexed:
            BaseCoreClass = [MetaTree.PyTree]
        else:
            # for indexed trees use networkx if present
            if networkxLoad:
                BaseCoreClass = [MetaTree.NxTree]
            else:
                BaseCoreClass = [MetaTree.PyTree, MetaTree.IndexedPyTree]
        # build core directory form the core base class methods
        for c in BaseCoreClass:
            for k in list(c.__dict__.keys()):
                # drawback of organising methods in "fake" classes is we get an unneeded entries, like __module__
                if k not in ('__module__', '__dict__', '__weakref__'):
                    coredict[k] = c.__dict__[k]
        # use methods of core implementation that are relevant to this type of trees
        for k in coredict:
            m = coredict[k]
            if mutable or not hasattr(m, 'mutabletree'):
                newdict[k] = coredict[k]

        # set properties read only or read-write depending on the available methods
        newdict['value'] = property(newdict.get('_get_value', None), newdict.get('_set_value', None), None, """ Value of the top element of that tree """)
        newdict['parent'] = property(newdict.get('_get_parent', None), newdict.get('_set_parent', None), None, """ The parent tree of that tree, or None if tree isn't a subtree """)
        newdict['next'] = property(newdict.get('_get_next', None), newdict.get('_set_next', None), None, """ Next tree in the siblings order, or None is self doesn't have siblings """)
        if indexed:
            newdict['key'] = property(newdict.get('_get_key', None), newdict.get('_set_key', None), None, """ Unique key of the element for indexed trees """)

        # upper level methods, depending on type of tree
        # only restriction is you cannot override core methods
        basedict = dict(MetaTree.ImTree.__dict__)
        if mutable:
            # add the mutable methods
            mutabledict = dict(MetaTree.MuTree.__dict__)
            basedict.update(basedict, **mutabledict)

        # update with methods declared at class definition
        basedict.update(basedict, **classdict)
        # methods that must be defined here depending on the preceding

        # add  methods unless they clash with core methods
        for k in basedict:
            if k in newdict:
                if k == '__doc__':
                    newdict[k] = newdict[k] + "\n" + basedict[k]
                else:
                    warnings.warn("Can't override core method or property %s in Trees (trying to create class '%s')" % (k, classname))
            else:
                newdict[k] = basedict[k]

        # set class tree type
        newdict['_TreeType'] = treeType
        # delegate rest of the work to type.__new__
        return super(MetaTree, mcl).__new__(mcl, classname, newbases, newdict)

    # will get called after __new__
#    def __init__(cls, name, bases, classdict) :
#        print cls
#        print name
#        print bases
#        print classdict

    # To get info on the kind of tree class that was created
    def __get_TreeType(cls):
        return cls._TreeType
    TreeType = property(__get_TreeType, None, None, "The type used for internal tree storage for that tree class.")

    def __repr__(cls):
        return "%s<TreeType:%r>" % (cls.__name__, cls.TreeType)

    def __str__(cls):
        return "%s<TreeType:%r>" % (cls.__name__, cls.TreeType)

    if PY2:
        def __unicode__(cls):
            return u"%s<TreeType:%r>" % (cls.__name__, cls.TreeType)

# derive from one of these as needed


class FrozenTree(with_metaclass(MetaTree, object)):
    mutable = False
    indexed = False


class Tree(with_metaclass(MetaTree, object)):
    mutable = True
    indexed = False


class IndexedFrozenTree(with_metaclass(MetaTree, object)):
    mutable = False
    indexed = True


class IndexedTree(with_metaclass(MetaTree, object)):
    mutable = True
    indexed = True


def treeFromDict(childToParentDict):
    """
    This function will build a tree from the provided dictionnary of child:parent relations :
        where each key represent an element and each key value represent the parent of that element, allows to build Trees form
        cmp(a,b): returns True if a is a direct child of b, False else.
        All elements must be present in the dictionnary keys, with root elements having None as value/parent
    """
    if isinstance(childToParentDict, dict):
        def isChildFn(c, p):
            return childToParentDict.get(c, None) == p
        s = set(childToParentDict)
        s.update(iter(childToParentDict.values()))
        return treeFromChildLink(isChildFn, *s)
    else:
        raise ValueError("%r is not a dictionnary" % childToParentDict)


def treeFromChildLink(isExactChildFn, *args):
    r"""
    This function will build a tree from the provided sequence and a comparison function in the form:
        cmp(a,b): returns True if a is a direct child of b, False else

        >>> lst = ['aab', 'aba', 'aa', 'bbb', 'ba', 'b', 'a', 'bb', 'ab', 'bab', 'bba']
        >>> def isDirectChild(s1, s2) :
        ...     return s1.startswith(s2) and len(s1)==len(s2)+1
        >>> a = treeFromChildLink (isDirectChild, *lst)
        >>> a.sort()
        >>> print(a.formatted())
        +: a
        |-+: aa
        | \--: aab
        \-+: ab
          \--: aba
        <BLANKLINE>
        +: b
        |-+: ba
        | \--: bab
        \-+: bb
          |--: bba
          \--: bbb
        >>>
        >>> # A child cannot have more than one parent, if the isChild is ambiguous an exception will be raised
        >>>
        >>> def isChild(s1, s2) :
        ...     return s1.startswith(s2)
        >>> failedTree = treeFromChildLink (isChild, *lst)
        Traceback (most recent call last):
            ...
        ValueError: A child in Tree cannot have multiple parents, check the provided isChild(c, p) function: 'isChild' - child: aab - new parents: ['a'] - oldparent: aa
    """
    deq = deque()
    for arg in args:
        deq.append(Tree(arg))
    lst = []
    it = 0
    while deq:
        it += 1
        # print "iteration %i deq= %s, lst= %s"% (it, deq, lst)
        c = deq.popleft()
        hasParent = False
        for p in list(deq) + lst:
            pars = [x for x in p.preorder() if isExactChildFn(c.top().value, x.value)]
            for pr in pars:
                # print "%s is child of %s" % (c, pr)
                if not hasParent:
                    pr.graft(c, pr)
                    hasParent = True
                else:
                    print(pars)
                    # should only be one parent, break on first encountered

                    err = "A child in Tree cannot have multiple " \
                          "parents, check the provided isChild(c, p) " \
                          "function: '%s' - child: %s - new parents: %s - old" \
                          "parent: %s" % (isExactChildFn.__name__,
                                          c.value,
                                          [x.value for x in pars],
                                          c.parent.value)
                    raise ValueError(err)
        # If it's a root we move it to final list
        if not hasParent:
            # print "%s has not parent, it goes to the list as root" % str(c)
            lst.append(c)

    # print "final list %s" % str(lst)
    return Tree(*lst)


def treeFromIsChild(isChildFn, *elements):
    r"""
    This function will build a tree from the provided sequence and a comparison function in the form:
        isChildFn(c,p): returns True if c is a child of p (direct or indirect), False otherwise

    The comparison function must satisfy the following conditions for all a, b, and c in the tree:
        isChildFn(a,a) == False
            (an object is not a child of itself)
        if isChildFn(a,b) AND isChildFn(b,c), then isChildFn(a,c)
            (indirect children are inherited)
        if isChildFn(a,b) AND isChildFn(a,c), then isChildFn(b,c) OR isChildFn(c,b) OR b==c
            (if a child has two distinct parents, then one must be the parent of the other)

    If any member of elements is itself a Tree, then it will be treated as a subtree (or subtrees, in the
    case of a forest) to be merged into the returned tree structure; for every root in such a subtree,
    the structure below the root will be unaltered, though the entire subtree itself may be parented to
    some other member of elements.

    >>> lst = ['aab', 'aba', 'aa', 'ba', 'bbb', 'a', 'b', 'bb', 'ab', 'bab', 'bba']
    >>> def isChild(s1, s2) :
    ...     return s1.startswith(s2)
    >>> a = treeFromIsChild (isChild, *lst)
    >>> a.sort()
    >>> print(a.formatted())
    +: a
    |-+: aa
    | \--: aab
    \-+: ab
      \--: aba
    <BLANKLINE>
    +: b
    |-+: ba
    | \--: bab
    \-+: bb
      |--: bba
      \--: bbb
    """
    newTree = Tree()

    unordered = deque()

    # First, check for subtrees
    for element in elements:
        if isTree(element):
            for subTree in element.tops():
                newTree.add(subTree)
        else:
            unordered.append(element)

    # Then, go through unordered, making the subtrees rooted at each element
    while unordered:
        root = unordered.pop()
        children = deque()

        # iterate over a copy of unordered, since we're modifying it
        index = 0
        for val in deque(unordered):
            if isChildFn(val, root):
                children.append(val)
                del unordered[index]
            else:
                # Note that we only increment the index if we don't
                # delete an element... if we do delete an element,
                # our old index points at the next element already
                index += 1

        # Then check the subtrees, to see which are children of our root...
        for subTree in list(newTree.tops()):
            if isChildFn(subTree.value, root):
                children.append(subTree)
                newTree.remove(subTree)

        # ...then use recursion to make a new subTree with our new root
        newTree.add(root)
        newSubTree = newTree.top(-1)
        assert(newSubTree.value == root)
        #treeFromIsChild(isChildFn, *children).parent = newSubTree
        childForest = treeFromIsChild(isChildFn, *children)
        childForest.parent = newSubTree

    return newTree
#
# class DirTree(Tree):
#    """
#    A tree structure describing a directory hierarchy.
#    """
#    def __init__(self, dir=None):
#        """
#        Creates a DirTree rooted at the given directory
#
#        Can be initialized by passing in a single argument, which
#        if supplied, must be a path to a directory that exists
#        on the filesystem.
#
#        If the given directory does not exist on the filesystem,
#        a ValueError is raised.
#
#        >>> myDirTree = DirTree()
#        >>> myDirTree.value = 'root'
#        >>> myDirTree.add('foo')
#        >>> myDirTree.add('bar', parent='foo')
#        >>> myDirTree.add('other')
#        >>> myDirTree.view()
#        +: root
#        |-+: foo
#        | \--: bar
#        \--: other
#        """
#        if not os.path.isdir(dir):
#            raise ValueError("%s is not a valid directory" % dir)
#
#        super(DirTree, self).__init__()
#
#        if dir:
#            basename = ""
#            while not basename and dir:
#                dir, basename = os.path.split(dir)
#            self.value = basename
#            for entry in os.listdir(dir):
#                path = os.path.join(dir, entry)
#                if os.path.isdir(path):
#                    subTree = _pymelDirTree_recurse(path)
#                    self.add(subTree)
#
#    def dirPath(self, *args, **kwargs):
#        """
#        Returns a string representing the directory path from the root to this element.
#        """
#        dirs = [dir.value for dir in self.path()]
#        return os.path.join(dirs)


# unit test with doctest
if __name__ == '__main__':
    import doctest
    doctest.testmod()

