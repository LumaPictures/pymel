"""
This module implements binary and generalized trees.

History of changes:
version 1.1:
- Changed cargo, left/right props of InsertionBTree to be read-only.
- find and delete methods for InsertionBTree.
- Introduced empty trees (trees with no nodes).
- Deleted not implemented's from abstract classes.
- Deleted some if redundant checks.

ToDo:
 - Make empty tree a cached "static" value?
 - Move graft/ungraft to be methods of childs prop, now returning a
   set-like object?
"""


#Import generators.
from __future__ import generators
#Pymel add
# removed as it's 2.5 only
# import functools as ftools
from collections import *
import util

__version__ = 1.2
__author__ = "G. Rodrigues"
s

#Auxiliary class to tackle default args.
class _undef_arg(object):
    pass


#The abstract generalized tree class where most of the methods reside.
class BaseTree(object):
    """The generalized "interface" tree class.

    It has two properties: the cargo and a childs iterator giving the child subtrees.

    The childs property returns a new (reset) iterator each time it is called.
    There is no order of iteration through the nodes (implementation is free to
    swap them around). """

    def isatom(self):
        """A tree is atomic if it has no subtrees."""
        try:
            self.childs.next()
        except StopIteration:
            return 1
        except AttributeError:
            return 1
        return 0

    #The simplest print possible.
    def __str__(self):
        if self:
            if self.isatom():
                return "('%s')" % str(self.cargo)
            else:
                temp = [subtree.__str__() for subtree in self.childs]
                return "('%s', %s)" % (str(self.cargo), ", ".join(temp))
        else:
            return "()"

    #The simplest print possible as unicode.
    def __unicode__(self):
        if self:
            if self.isatom():
                return u"('%s')" % unicode(self.cargo)
            else:
                temp = [subtree.__unicode__() for subtree in self.childs]
                return u"('%s', %s)" % (unicode(self.cargo), u", ".join(temp))
        else:
            return u"()"

    #pymel addition for represent.
    def __repr__(self):
        if self:
            if self.isatom():
                return u"%s(%r)" % (self.__class__.__name__, self.cargo)
            else:
                temp = [subtree.__repr__() for subtree in self.childs]
                return u"%s(%r, %s)" % (self.__class__.__name__, self.cargo, u", ".join(temp))
        else:
            return u"%s()" % self.__class__.__name__

    #The Tree iterators.
    def __iter__(self):
        """The standard preorder traversal iterator."""
        if self:
            yield self.cargo
            for subtree in self.childs:
                for elem in subtree:
                    yield elem

    def postorder(self):
        """Postorder traversal of a tree."""
        if self:
            for subtree in self.childs:
                for elem in subtree.postorder():
                    yield elem
            yield self.cargo

    #The "inplace" iterators.
    def subtree(self):
        """Preorder iterator over the subtrees.

        Warning: As always, do not use this iterator in a for loop while altering
        the structure of the tree."""

        if self:
            yield self
            for subtree in self.childs:
                for tree in subtree.subtree():
                    yield tree

    def postsubtree(self):
        """Postorder iterator over the subtrees.

        Warning: As always, do not use this iterator in a for loop while altering
        the structure of the tree."""

        if self:
            for subtree in self.childs:
                for tree in subtree.postsubtree():
                    yield tree
            yield self

    #The in protocol.
    # Modified to test inclusion of subtrees 
    def __contains__(self, elem):
        """Returns 1 if elem is in the tree, 0 otherwise."""
        if isinstance (elem, BaseTree) :
            for sub in self.subtree():
                if elem == sub:
                    return 1
            return 0           
        else :
            for element in self:
                if elem == element:
                    return 1
            return 0

    #Number of elements in the tree.
    def __len__(self):
        """Returns the number of elements (nodes) in the tree."""
        ret = 0
        for elem in self:
            ret += 1
        return ret
    
    # added equivalence test here
    def __eq__(self, other):
        """Checks for equality of two trees."""
        #Both trees not empty.
        if self and other:
            #Compare cargos.
            if self.cargo != other.cargo:
                return False
            else:
                if len(self) != len(other) :
                    return False
                else :
                    #Recursive calls.
                    return reduce(lambda x, y:x and y, map(lambda c1, c2:c1 == c2, self.childs, other.childs), True)
        #Both trees empty.
        elif not self and not other:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        """Shallow copy of a Tree object."""
        if self:
            if self.isatom():
                return self.__class__(self.cargo)
            else:
                temp = tuple([subtree.copy() for subtree in self.childs])
                return self.__class__(self.cargo, *temp)
        else:
            return self.__class__()


#Tree implementations.
class Tree(BaseTree):
    """
    Class implementing an immutable generalized tree type.
        You can initialize explicitely or directly from a nested sequence:
    >>> theTree = Tree(1, Tree(2, Tree(20), Tree(21, Tree(210), Tree(211))), Tree(3, Tree(30), Tree(31)))
    >>> theOtherTree = Tree(1, (2, (20), (21, (210), (211))), (3, (30), (31)))
    >>> print theTree == theOtherTree
    To build a tree of sequences:
    >>> seqTree = Tree((1, 2, 3), Tree((4, 5, 6)), Tree((7, 8, 9)))
    >>> seqOtherTree = Tree( (1,2,3), ((4, 5, 6),), ((7, 8, 9),), )
    >>> seqTree == seqOtherTree
    >>> [k for k in seqTree]
    >>> [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
            """

    def __init__(self, *args):
        """The initializer."""
        if args:
            # modified to allow initialisation from nested lists or tuples
            if len(args)==1 and util.isIterable(args[0]) :
                args = tuple(args[0])
            self.__head = [args[0]]
            for arg in args[1:] :
                if not isinstance(arg, BaseTree) :
                    if util.isIterable(arg) :
                        self.__head.append(Tree(*arg))
                    else :
                        self.__head.append(Tree(arg))
                elif isinstance(arg, FrozenTree) :
                    self.__head.append(arg.copy().toTree())
                else :
                    self.__head.append(arg)
        else:
            self.__head = None

    def __nonzero__(self):
        return self.__head is not None

    #Properties.
    def __get_cargo(self):
        if self:
            return self.__head[0]
        else:
            raise AttributeError, "An empty tree has no cargo."

    def __set_cargo(self, cargo):
        if self:
            self.__head[0] = cargo
        else:
            self.__head = [cargo]

    def __del_cargo(self):
        if self:
            self.__head = None
        else:
            raise ValueError, "Cannot delete the cargo of an empty tree."

    cargo = property(__get_cargo, __set_cargo, __del_cargo, "The root element of the tree.")

    def __get_childs(self):
        def it(lst):
            for i in xrange(1, len(lst)):
                yield lst[i]

        if self:
            return it(self.__head)
        #Return empty iterator.
        else:
            return iter([])

    childs = property(__get_childs, None, None, "The iterator over the child subtrees.")

    #Add or delete trees to the root of the tree.
    def graft(self, t):
        """Graft a tree to the root node."""
        if self:
            if isinstance(t, Tree):
                self.__head.append(t)
            else:
                raise TypeError, "%r is not a tree instance." % t
        else:
            raise AttributeError, "Cannot graft a tree in an empty tree."

    def ungraft(self, t):
        """Ungrafts a subtree from the current node.

        The argument is the subtree to ungraft itself."""

        if self:
            for pair in zip(self.childs, range(1, len(self.__head))):
                if t is pair[0]:
                    del self.__head[pair[1]]
                    return None
            raise AttributeError, "tree %r is not grafted to the root node of this tree." % t
        else:
            raise AttributeError, "Cannot ungraft a tree from an empty tree."

    #General inplace transformations of trees.
    def map(self, func):
        """Inplace map transformation of a tree."""
        for tree in self.subtree():
            tree.cargo = func(tree.cargo)

    #Conversion methods.
    def toFrozenTree(self):
        """Convert tree into an immutable tree."""
        if self:
            if self.isatom():
                return FrozenTree(self.cargo)
            else:
                args = (self.cargo,)
                args = args + tuple([subtree.toFrozenTree() for subtree in self.childs])
                return FrozenTree(*args)
        else:
            return FrozenTree()

# Immutable tree
class FrozenTree(BaseTree):
    """
    Class implementing an immutable generalized tree type.
        You can initialize explicitely or directly from a nested sequence:
    >>> theFrozenTree = FrozenTree(1, Tree(2, Tree(20), Tree(21, Tree(210), Tree(211))), Tree(3, Tree(30), Tree(31)))
    >>> theOtherFrozenTree = FrozenTree(1, (2, (20), (21, (210), (211))), (3, (30), (31)))
    >>> print theFrozenTree == theOtherFrozenTree
            """
    def __init__(self, *args):
        """The initializer"""
        if args:
            # modified to allow initialisation from a nested list call on *args with args = theList            
            if len(args)==1 and util.isIterable(args[0]) :
                arg = tuple(args[0])
            self.__head = (args[0],)
            for arg in args[1:] :
                if not isinstance(arg, BaseTree) :
                    if util.isIterable(arg) :
                        self.__head = self.__head + (FrozenTree(*arg),)
                    else :
                        self.__head = self.__head + (FrozenTree(arg),)
                elif isinstance(arg, Tree) :
                    self.__head = self.__head + (arg.copy().toFrozenTree(),)
                else :
                    self.__head = self.__head + (arg,)

    def __nonzero__(self):
        return self.__head is not None

    #Properties.
    def __get_cargo(self):
        if self:
            return self.__head[0]
        else:
            raise AttributeError, "An empty tree has no cargo."

    cargo = property(__get_cargo, None, None, "The root element of the tree")

    def __get_childs(self):
        def it(lst):
            for i in xrange(1, len(lst)):
                yield lst[i]

        if self:
            return it(self.__head)
        else:
            #Return empty iterator.
            return iter(())

    childs = property(__get_childs, None, None, "The iterator over the child subtrees.")

    def toTree(self):
        """Convert tree into a mutable tree."""
        if self:
            if self.isatom():
                return Tree(self.cargo)
            else:
                args = (self.cargo,)
                args = args + tuple([subtree.toTree() for subtree in self.childs])
                return Tree(*args)
        else:
            return Tree()
        
# pymel additions

# Similar to filter but using an iterator insead of returning a list
def filterIter(filterFn, value):
    for v in value :
        if filterFn(v) :
            yield v

# apply a function on the cargo of it's arguments instead of directly if they are Trees
def applyOnCargo (inFunc) :
    def newFunc(*args, **kwargs) :
        nargs = []
        for arg in args :
            if isinstance(arg, BaseTree) :
                nargs.append(arg.cargo)
            else :
                nargs.append(arg)
        return apply(inFunc, nargs, kwargs)        
    newFunc.__name__ = inFunc.__name__+'OnCargo'
    return newFunc

# Checks all elements of a list against eah other with a 'paternity test' :
# Will build a tree from a list and a "isChild" comparison fonction
# such as isChild(c, p) returns true if c is a direct child of p
def treeFromChildLink (isExactChildFn, *args):
    """
    This function will build a tree from the provided sequence and a comparison function in the form:
        cmp(a,b): returns True if a is a direct child of b, False else
    >>> lst = ['aab', 'aba', 'aa', 'bbb', 'ba', 'a', 'b', 'bb', 'ab', 'bab', 'bba']
    >>> def isChild(s1, s2) :
    >>>     return s1.startswith(s2) and len(s1)==len(s2)+1
    >>> forest = treeFromChildLink (isChild, lst)
    >>> for tree in forest :
    >>>     print tree
    A child cannot have more than one parent, if the isChild is ambiguous an exception will be raised
    >>> def isChild(s1, s2) :
    >>>     return s1.startswith(s2) 
    >>> forest = treeFromChildLink (isChild, lst)    
    """
    deq = deque(Tree(arg) for arg in args)
    lst = []
    it = 0
    while deq:
        it+=1
        # print "iteration %i deq= %s, lst= %s"% (it, deq, lst)
        c = deq.popleft()
        hasParent = False        
        for p in list(deq)+lst :
            for pr in filterIter(lambda x:applyOnCargo(isExactChildFn)(c, x), p.subtree()) :
                # print "%s is child of %s" % (c, pr)                        
                if not hasParent :
                    pr.graft(c)
                    hasParent = True
                else :
                    # should only be one parent, break on first encountered
                    raise ValueError, "A child in Tree cannot have multiple parents, check the provided isChild(c, p) function: '%s'" % isExactChildFn.__name__
        # If it's a root we move it to final list
        if not hasParent :
            # print "%s has not parent, it goes to the list as root" % str(c)
            lst.append(c)
    
    # print "final list %s" % str(lst)
    if len(lst) == 1 :
        return lst[0]
    else :
        return tuple(lst)
