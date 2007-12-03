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
#import functools as ftools
from collections import *
import util

__version__ = 1.2
__author__ = "G. Rodrigues"

# several modifications for pymel, so if it breaks its probably my fult, not the author's

#Auxiliary class to tackle default args.
class _undef_arg(object):
    pass


##The abstract BTree class, where most of the methods reside.
#class BaseBTree(object):
#    """The binary tree "interface" class.
#
#    It has three properties: cargo, and the left and right subtrees.
#    A terminal node (= atomic tree) is one where the left and right
#    subtrees are the empty tree."""
#
#    def isatom(self):
#        """Returns 1 if the tree has no nonempty subtrees, 0 otherwise."""
#        if self:
#            if self.left or self.right:
#                return 0
#            else:
#                return 1
#        else:
#            return 1
#
#    #The simplest print possible.
#    def __str__(self):
#        if not self:
#            return "()"
#        else:
#            return "(%s, %s, %s)" % (str(self.cargo), str(self.left), str(self.right))
#
#    #pymel addition for repre.
#    def __repr__(self):
#        if self:
#            return "%s(%r, %r, %r)" % (self.__class__.__name__, self.cargo, self.left, self.right)
#        else:
#            return "%s()" % self.__class__.__name__
#
#    #The BTree iterators.
#    def __iter__(self):
#        """The standard preorder traversal of a binary tree."""
#        if self:
#            yield self.cargo
#            for elem in self.left:
#                yield elem
#            for elem in self.right:
#                yield elem
#
#    def postorder(self):
#        """Postorder traversal of a binary tree."""
#        if self:
#            for elem in self.left.postorder():
#                yield elem
#            for elem in self.right.postorder():
#                yield elem
#            yield self.cargo
#        
#    def inorder(self):
#        """Inorder traversal of a binary tree."""
#        if self:
#            for elem in self.left.inorder():
#                yield elem
#            yield self.cargo
#            for elem in self.right.inorder():
#                yield elem
#
#    #"Inplace" iterators.
#    def subtree(self):
#        """Preorder iterator over the (nonempty) subtrees.
#
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""
#
#        if self:
#            yield self
#            for tree in self.left.subtree():
#                yield tree
#            for tree in self.right.subtree():
#                yield tree
#
#    def postsubtree(self):
#        """Postorder iterator over the (nonempty) subtrees.
#
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""        
#
#        if self:
#            for tree in self.left.postsubtree():
#                yield tree
#            for tree in self.right.postsubtree():
#                yield tree
#            yield self
#
#    def insubtree(self):
#        """Inorder iterator over the (nonempty) subtrees.
#
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""        
#
#        if self:
#            for tree in self.left.postsubtree():
#                yield tree
#            yield self
#            for tree in self.right.postsubtree():
#                yield tree
#
#    #Binary comparisons.
#    def __eq__(self, other):
#        """Checks for equality of two binary trees."""
#        #Both trees not empty.
#        if self and other:
#            #Compare cargos.
#            if self.cargo != other.cargo:
#                return 0
#            else:
#                #Recursive calls.
#                if self.left.__eq__(other.left):
#                    return self.right.__eq__(other.right)
#                else:
#                    return 0
#        #Both trees empty.
#        elif not self and not other:
#            return 1
#        else:
#            return 0
#
#    def __ne__(self, other):
#        return not self.__eq__(other)
#
#    def __contains__(self, elem):
#        """Returns 1 if elem is in some node of the tree, 0 otherwise."""
#        for element in self:
#            if elem == element:
#                return 1
#        return 0
#
#    def __len__(self):
#        """Returns the number of nodes (elements) in the tree."""
#        ret = 0
#        for elem in self:
#            ret += 1
#        return ret
#
#    def copy(self):
#        """Shallow copy of a BTree object."""
#        if self:
#            return self.__class__(self.cargo, self.left.copy(), self.right.copy())
#        else:
#            return self.__class__()
#
#
##The two implementations of BTree class.
#class BTree(BaseBTree):
#    """A mutable implementation of the binary tree BTree class."""
#
#    def __init__(self, cargo = _undef_arg, left = None, right = None):
#        """The initializer."""
#        if cargo is not _undef_arg:
#            self.__cargo = cargo
#
#            if left is not None:
#                if isinstance(left, BTree):
#                    self.__left = left
#                else:
#                    raise TypeError, "Object %s is not a BTree binary tree." % repr(left)
#            else:
#                self.__left = BTree()
#
#            if right is not None:
#                if isinstance(right, BTree):
#                    self.__right = right
#                else:
#                    raise TypeError, "Object %s is not a BTree binary tree." % repr(right)
#            else:
#                self.__right = BTree()
#
#    def __nonzero__(self):
#        """Returns 1 if the tree is nonempty, 0 otherwise."""
#        try:
#            self.__cargo
#            return 1
#        except AttributeError:
#            return 0
#
#    #Properties.
#    def __get_cargo(self):
#        if self:
#            return self.__cargo
#        else:
#            raise AttributeError, "An empty tree has no cargo."
#
#    def __set_cargo(self, cargo):
#        if not self:
#            self.__left = BTree()
#            self.__right = BTree()            
#        self.__cargo = cargo
#
#    def __del_cargo(self):
#        if self:
#            #Turn tree into an empty tree => delete all attributes.
#            del self.__cargo
#            del self.__left
#            del self.__right
#        else:
#            raise AttributeError, "Cannot delete the cargo of an empty tree."
#
#    cargo = property(__get_cargo, __set_cargo, __del_cargo, "The root element of the tree.")
#
#    def __get_left(self):
#        if self:
#            return self.__left
#        else:
#            raise AttributeError, "An empty tree has no left subtree."
#
#    def __set_left(self, tree):
#        if self:
#            if isinstance(tree, BTree):
#                self.__left = tree
#            else:
#                raise TypeError, "Object %s is not a BTree." % repr(tree)
#        else:
#            raise AttributeError, "Cannot set the left subtree of an empty tree."
#
#    def __del_left(self):
#        if self:
#            self.__left = BTree()
#        else:
#            raise AttributeError, "Cannot delete the left subtree of an empty tree."
#
#    left = property(__get_left, __set_left, __del_left, "The left subtree.")
#
#    def __get_right(self):
#        if self:
#            return self.__right
#        else:
#            raise AttributeError, "An empty tree has no right subtree."
#
#    def __set_right(self, tree):
#        if self:
#            if isinstance(tree, BTree):
#                self.__right = tree
#            else:
#                raise TypeError, "Object %s is not a BTree." % repr(tree)
#        else:
#            raise AttributeError, "Cannot set the right subtree of an empty tree."
#
#    def __del_right(self):
#        if self:
#            self.__right = BTree()
#        else:
#            raise AttributeError, "Cannot delete the right subtree of an empty tree."
#
#    right = property(__get_right, __set_right, __del_right, "The right subtree.")
#
#    #General inplace transformations of mutable binary trees.
#    def map(self, func):
#        """Inplace map transformation of a binary tree."""
#        for tree in self.subtree():
#            tree.cargo = func(tree.cargo)
#
#    def toFrozenBTree(self):
#        """Returns an FrozenBTree copy."""
#        if self:
#            return toFrozenBTree(self.cargo, self.left.toFrozenBTree(), self.right.toFrozenBTree())
#        else:
#            return toFrozenBTree()
#
#
#class InsertionBTree(BTree):
#    """Class implementing insertion binary trees.
#
#    The cargo, left and right properties are read-only. To add elements use the
#    insert method.
#
#    It is up to the client to ensure that the elements in the tree have meaningful
#    order methods."""
#
#    def __init__(self, cargo = _undef_arg):
#        if cargo is _undef_arg:
#            BTree.__init__(self)
#        else:
#            BTree.__init__(self, cargo)
#            BTree.left.__set__(self, InsertionBTree())
#            BTree.right.__set__(self, InsertionBTree())            
#
#    #Redefinition of cargo, left/right properties to be read only.
#    cargo = property(BTree.cargo.__get__, None, None, "The root element of the tree.")
#    left = property(BTree.left.__get__, None, None, "The left subtree.")
#    right = property(BTree.right.__get__, None, None, "The right subtree.")
#
#    #Redefinition of basic iterators.
#    def __iter__(self):
#        """Iterator over the tree elements in min-max order."""
#        return BTree.inorder(self)
#
#    def subtree(self):
#        """Traversal through the (nonempty) subtrees in min-max order.
#        
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""
#
#        return BTree.insubtree(self)
#
#    #Iterating in max-min order.
#    def inrevorder(self):
#        """Iterator over the tree elements in max-min order."""
#        if self:
#            for elem in self.right.inrevorder():
#                yield elem
#            yield self.cargo
#            for elem in self.left.inrevorder():
#                yield elem
#
#    def inrevsubtree(self):
#        """Traversal through the (nonempty) subtrees in max-min order.
#        
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""
#
#        if self:
#            for tree in self.right.inrevsubtree():
#                yield tree
#            yield self
#            for tree in self.left.inrevsubtree():
#                yield tree
#
#    #The in protocol.
#    def __contains__(self, elem):
#        if self:
#            if elem == self.cargo:
#                return 1
#            elif elem > self.cargo:
#                return self.right.__contains__(elem)
#            else:
#                return self.left.__contains__(elem)
#        else:
#            return 0
#
#    def find(self, elem):
#        """Returns the subtree which has elem as cargo.
#
#        If elem is not in tree it raises an exception."""
#
#        if self:
#            if elem == self.cargo:
#                return self
#            elif elem > self.cargo:
#                return self.right.find(elem)
#            else:
#                return self.left.find(elem)
#        else:
#            raise ValueError, "%s is not in tree." % str(elem)
#
#    def insert(self, elem):
#        """Inserts an element in the tree if it is not there already."""
#        if not self:
#            #Insert elem in empty tree.
#            BTree.cargo.__set__(self, elem)
#            BTree.left.__set__(self, InsertionBTree())
#            BTree.right.__set__(self, InsertionBTree())
#        #Recursive calls.
#        elif elem < self.cargo:
#            self.left.insert(elem)
#        elif elem > self.cargo:
#            self.right.insert(elem)
#            
#    def delete(self, elem):
#        """Deletes an elem from the tree.
#
#        Raises an exception if elem is not in tree."""
#
#        if self:
#            if elem == self.cargo:
#                if self.isatom():
#                    BTree.cargo.__del__(self)
#                #Both trees not empty
#                elif self.left and self.right:
#                    #Get min element subtree and connect it to self.left.
#                    minsubtree = self.right.subtree().next()
#                    BTree.left.__set__(minsubtree, self.left)
#                    #root -> root.right.
#                    BTree.cargo.__set__(self, self.right.cargo)
#                    BTree.left.__set__(self, self.right.left)
#                    BTree.right.__set__(self, self.right.right)                    
#                #Right subtree is empty.
#                elif not self.right:
#                    #root -> root.left
#                    BTree.cargo.__set__(self, self.left.cargo)
#                    BTree.left.__set__(self, self.left.left)
#                    BTree.right.__set__(self, self.left.right)
#                #Left subtree is empty.
#                else:
#                    #root -> root.right
#                    BTree.cargo.__set__(self, self.right.cargo)
#                    BTree.left.__set__(self, self.right.left)
#                    BTree.right.__set__(self, self.right.right)
#            #Recursive calls.
#            elif elem < self.cargo:
#                self.left.delete(elem)
#            else:
#                self.right.delete(elem)
#        else:
#            raise ValueError, "%s is not an element of the tree." % str(elem)
#
#
#class FrozenBTree(BaseBTree):
#    """An implementation of an immutable binary tree using tuples."""
#
#    def __init__(self, cargo = _undef_arg, left = None, right = None):
#        """The initializer."""
#        if cargo is not _undef_arg:
#            if left is not None:
#                if not isinstance(left, FrozenBTree):
#                    raise TypeError, "Object %s is not an FrozenBTree." % repr(left)
#            else:
#                left = FrozenBTree()
#
#            if right is not None:
#                if not isinstance(right, FrozenBTree):
#                    raise TypeError, "Object %s is not an FrozenBTree." % repr(right)
#            else:
#                right = FrozenBTree()
#
#            self.__head = (cargo, left, right)            
#        else:
#            self.__head = None
#
#    def __nonzero__(self):
#        """Returns 1 if the tree is nonempty, 0 otherwise."""
#        return self.__head is not None
#
#    #Properties.
#    def __get_cargo(self):
#        if self:
#            return self.__head[0]
#        else:
#            raise AttributeError, "An empty tree has no cargo."
#
#    cargo = property(__get_cargo, None, None, "The root element of the tree.")
#
#    def __get_left(self):
#        if self:
#            return self.__head[1]
#        else:
#            raise AttributeError, "An empty tree has no left subtree."
#
#    left = property(__get_left, None, None, "The left subtree.")
#
#    def __get_right(self):
#        if self:
#            return self.__head[2]
#        else:
#            raise AttributeError, "An empty tree has no right subtree."
#
#    right = property(__get_right, None, None, "The right subtree.")
#
#    #Conversion method.
#    def toBTree(self):
#        """Returns a BTree copy."""
#        if self:
#            return BTree(self.cargo, self.left.toBTree(), self.right.toBTree())
#        else:
#            return BTree()
#
#
##Making FrozenBTree hashable.
#class HashBTree(FrozenBTree):
#    """Class implementing a hashable immutable binary tree. It can contain only hashables."""
#
#    def __init__(self, cargo = _undef_arg, left = None, right = None):
#        try:
#            if cargo is not _undef_arg:
#                cargo.__hash__
#            FrozenBTree.__init__(self, cargo, left, right)
#        except AttributeError:
#            raise TypeError, "Object %s is not hashable." % repr(cargo)
#
#    #HashBTrees can be keys in dictionaries (rhyme not intended).
#    def __hash__(self):
#        return hash(tuple(self))


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
                return "(%s)" % repr(self.cargo)
            else:
                temp = [subtree.__str__() for subtree in self.childs]
                return "(%s, %s)" % (repr(self.cargo), ", ".join(temp))
        else:
            return "()"

    #The simplest print possible.
    def __unicode__(self):
        if self:
            if self.isatom():
                return u"(%s)" % repr(self.cargo)
            else:
                temp = [subtree.__unicode__() for subtree in self.childs]
                return u"(%s, %s)" % (self.cargo, u", ".join(temp))
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
                arg = tuple(args[0])
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
    deq = deque(map(Tree, args))
    lst = []
    it = 0
    while deq:
        it+=1
        # print "iteration %i deq= %s, lst= %s"% (it, deq, lst)
        c = deq.popleft()
        hasParent = False        
        for p in list(deq)+lst :
            for pr in filterIter(ftools.partial(applyOnCargo(isExactChildFn), c), p.subtree()) :
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
