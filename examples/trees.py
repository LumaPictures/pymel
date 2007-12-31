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
from weakref import *
from copy import *
from pymel import *

__version__ = 1.2
__author__ = "G. Rodrigues"


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
            return True
        except AttributeError:
            return True
        return False

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

    def formated (self) :
        """ returns an indented formated string for display """
        stack = [(self,0)]
        result = ""
        while stack :
            arg, level = stack.pop()
            if not arg.isatom() :
                stack.append( (Tree(arg.cargo), level) )
                stack += [(x,level+1) for x in arg.childs]
            else :
                result = ">"*level+str(arg.cargo)+"\n"+result
        
        return result

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

    def breadth(self):
        """breadth first traversal of a tree."""
        if self:
            yield self.cargo        
            deq = deque(x for x in self.childs)
            while deq :
                arg = deq.popleft()
                if not arg.isatom() :
                    for a in arg.childs :
                        deq.append (a)
                else :
                    yield arg.cargo

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

    def breadthsubtree(self):
        """breadth first traversal of a tree."""
        if self:
            yield self        
            deq = deque(x for x in self.childs)
            while deq :
                arg = deq.popleft()
                if not arg.isatom() :
                    for a in arg.childs :
                        deq.append (a)
                else :
                    yield arg

    def find(self, cargo):
        """Returns the subtree whose root cargo is elem, if found"""
        result = None
        for t in self.subtree() :
            if t.cargo == cargo :
                result = t
                break
        return result

    def __get_parentElement(self, elem):
        for sub in self.childs :
            if sub.cargo == elem :
                return self.cargo
        # if nothing found check childs
        for sub in self.childs :
            found = sub.__get_parentElement(elem)
            if found :
                return found
             
    def __get_parentSubtree(self, subt):
        for sub in self.childs :
            if sub == subt :
                return self
        # if nothing found check childs
        for sub in self.childs :
            found = sub.__get_parentSubtree(subt)
            if found :
                return found
                                
    def parent(self, elem) :
        """ Returns the parent element or subtree of a given element or subtree """
        if isinstance (elem, BaseTree) :
            return self.__get_parentSubtree(elem)
        else :
            return self.__get_parentElement(elem)     

    def parents(self, elem) :
        """ Iterates one all parents element or subtree of a given element or subtree up to root"""
        parents = []
        if isinstance (elem, BaseTree) :
            parent =  self.__get_parentSubtree(elem)
            while parent :
                yield parent
                parent = self.__get_parentSubtree(parent)
        else :
            parent = self.__get_parentElement(elem) 
            while parent :
                yield parent
                parent = self.__get_parentElement(parent)
                
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
            
class TripleIndex(object):
    """ A triple parent, child, next index for IndexedTrees """
    __storage = [None, None, None]
    def __get_parent(self):
        return self.__storage[0]
    def __set_parent(self, parent):
        self.__storage[0] = parent
    parent = property(__get_parent, __set_parent, None, "The parent index.")             
    def __get_child(self):
        return self.__storage[1]
    def __set_child(self, child):
        self.__storage[1] = child
    child = property(__get_child, __set_child, None, "The first child index.")      
    def __get_next(self):
        return self.__storage[2]
    def __set_next(self, next):
        self.__storage[2]= next
    next = property(__get_next, __set_next, None, "The next sibling index.")                  
    def __init__(self, value=(None, None, None)) :
        try :
            self.__storage = list(value)
        except :
            raise TypeError, "TripleIndex can only be initialized with a list or tuple of exactly 3 values: 'parent', 'child', 'next'"    
    def __eq__(self, other):
        if self :
            if other.isinstance(TripleIndex) :
                return self.parent==other.parent and self.child==other.child and self.next==other.next
            else :
                return False
        else :
            return other == None
    def isNull(self):
        if self :
            return self.parent==None and self.child==None and self.next==None
        else :
            return True

class TreeElement(object) :
    """ Elements of IndexedTrees """                      
    # weak reference proxy to the tree containing this element
    __tree = None
    # weak ref to index stored in tree
    #        __index = None
    #        # own storage for index (remove?)
    #          __ownIndex = TripleIndex()
    
    __index = None
    # value and key it is stored under in tree
    __key = None
    __value = None

    # ref to tree should only be readable from outside
    def __get_tree(self):
        return self.__tree
    tree = property(__get_tree, None, None, "The reference to the tree containing that element.")  
    def __get_value(self):
        return self.__value
    value = property(__get_value, None, None, "The element contained value.")  
    def __get_key(self):
        return self.__key
    key = property(__get_key, None, None, "The key the element is stored under in tree.")  
                    
    # Index properties, (private)
#        def __get_index(self):
#            if self.__index :
#                return self.__index
#            else :
#                return self.__ownIndex
#        def __set_index(self, value):
#            if self.__index :
#                self.__index = copy(value)
#            else :
#                self.__ownIndex = copy(value)
#        index = property(__get_index, __set_index, None, "The tree index to parent, child, next elements.")                  

    
    # Element properties and methods (public)               
    
    def __init__(self, value, tree=None ):
        """ Init an Element with (tree, value=key), can update an exsiting Element with value/key only """
        if isinstance(tree, IndexedTree):
            key = value
            # a weak ref to container tree
            self.__tree = proxy(tree)
            self.__value = value
            self.__key = self.tree.key(value)
            # element is "nowhere" until parented somehwere    
            self.__index = TripleIndex()               
            #if tree.has_key(key) :
            #    self.__index = proxy(dict.__getitem__(tree, key).__ownIndex)
        elif tree is None :
            self.__tree = None
            self.__index = None
            self.__value = value
            self.__key = None                
        else :
            raise ValueError, "Can instanciate an IndexedTree.Element on an empty (None) or valid IndexedTree "                      
                    
                # self.key = hash(self.value) or a custom hash function to allow multiple identical values

    def __repr__(self):
        return "%s(%r, %r)"  % (self.__class__.__name__, self.value, self.tree)
    def __str__(self):
        return str(self.value)
    def __unicode__(self):
        return unicode(self.value)
  
    # Element must be associated with a valide tree or these properties can't be used
    def __get_parent(self):
        if self.tree and self.__index.parent:
            return self.tree[self.__index.parent]
    def __set_parent(self, parent):
        if self.tree :
            if not parent :
                # Parent=None means at top, under fake root
                if not self.tree.has_key(None) :
                    self.tree[None] = None
                parent = self.tree[None]            
            if self.tree.has(parent) :
                # unparent nicely from old parent if element index exists
                if not self.__index.isNull() :
                    del(self.parent)
                # initialize index
                self.__index = TripleIndex()
                # reparent
                self.__index.parent = parent.key
                # if first child of the new parent
                if not parent.__index.child :
                    parent.__index.child = self.key
                # add at the end of current childs list
                previous = parent.lastchild()
                previous.__index.next = self.key
                # added at the end so points to first child
                self.__index.next = parent.__index.child
            else :
                raise ValueError, "Parent must be in same tree as Element, use 'add' or 'graft' to attach to another tree instead"
        else :
            raise RuntimeError, "Element must be part of a tree to set parent, child or next properties"
    def __del_parent(self):
        if self.tree :            
            last = self.last()
            first = self.first()
            # remove from list of siblings
            if last != self :
                last.__index.next = self.__index.next
            # if first child, relink parent
            if self == first :
                # this will return even fake root whereas normal "parent" property doesn't
                parent = self.tree[self.__index.parent]
                if last == self :
                    parent.__index.child = None
                else :
                    parent.__index.child = self.__index.next
            # element isn't attached to anywhere, reset __index to reflect that    
            self.__index = TripleIndex()    
        else :
            raise RuntimeError, "Element must be part of a tree to set parent, child or next properties"                           
    parent = property(__get_parent, __set_parent, __del_parent, """ The parent element of that element in the tree """)
    def __get_child(self):
        if self.tree and self.__index.child :
            return self.tree[self.__index.child] 
    child = property(__get_child, None, None, """ The first child element of that element in the tree """)
    def __get_next(self):
        if self.tree and self.__index.next :
            return self.tree[self.__index.next] 
    def __set_next(self, next):
        if self.tree :
            if next :
                parent = self.parent
                if self.tree.has(next) and next.parent == parent :
                    first = self.first()
                    previous = self.last()
                    last = next.last()
                    previous.__index.next = self.__index.next
                    last.__index.next = self.key
                    self.__index.next = next.key
                    # if next was first child, we take it's place
                    if first == next :
                        parent.__index.child = self                        
                else :
                    raise ValueError, "Next must have same parent as element, use 'parent' to move to another parent"
            else :
                self.__index.next = self.first().key
        else :
            raise RuntimeError, "Element must be part of a tree to set parent, child or next properties"                   
    next = property(__get_next, __set_next, None, """ The next sibling element of that element in the tree """)
    
    # def __get_last(self):
    def last(self):
        last = self
        next = self.next
        while next and next != self :
            last = next
            next = next.next
        return last
    # last = property(__get_last, None, None, """ The last sibling element before looping back to that element in the tree """)
    def first(self):
        return self.tree[self.__index.parent].child
    # first = property(__get_first, None, None, """ The first sibling element (the one parent is pointing to) of that element in the tree """)     
       
    def parents(self):
        parent = self.parent
        while parent :
            yield parent
            parent = parent.parent
    #parents = property(__iter_parents, None, None, """ Iterator on all parents, starting with but not including element, until root is reached """)
        
    def root(self):
        root = self
        parent = root.parent
        while parent :
            root = parent
            parent = root.parent
        return root
    #root = property(__get_root, None, None, """ Root of the subtree containing this element """)

    def depth(self):
        depth = 0
        parent = self.parent
        while parent :
            depth += 1
            parent = parent.parent
        return depth
    #depth = property(__get_depth, None, None, """ Depth (distance from root) of this element """)

    def childs(self):
        child = self.child
        if child :
            yield child
            for c in child.siblings() :
                yield c 
    #childs = property(__iter_childs, None, None, """ Iterator on all children of this element """)

    def lastchild(self):
        childs = [k for k in self.childs()]
        if childs :
            return childs[-1]

    def siblings(self):
        next = self.next
        while next and next != self :
            yield next
            next = next.next
    #siblings = property(__iter_siblings, None, None, """ Iterator on all siblings of the element, starting with but not including the element """)            

    def subtree(self):
        sub = IndexedTree(self)
        parent = sub[self]
        for child in self.childs() :
            sub.graft(child.subtree(), parent)
        return sub
    #subtree = property(__get_subtree, None, None, """ Subtree of the tree with the element as root """)

    # define __iter__ as __iter_below ?
    def below(self):
        for e in self.subtree().preorder() :
            yield e
    #below = property(__iter_below, None, None, """ Preorder iterator on all elements in tree below the element """)
    
    def postorder(self):
         for e in self.subtree().postorder() :
            yield e           
    #post = property(__iter_post, None, None, """ Postorder iterator on all elements in tree below the element """)

    def breadth(self):
         for e in self.subtree.breadth() :
            yield e           
    #breadth = property(__iter_breadth, None, None, """ Breadth iterator on all elements in tree below the element """)
    
    def leaves(self):
        for e in self.subtree().leaves() :
            yield e
    #leaves = property(__iter_leaves, None, None, """ Iterator on the leaves of the branch below the element """)

    def subtrees(self):
        for e in self.subtree().subtrees() :
            yield e
    #subtrees = property(__iter_subtrees, None, None, """ Preorder iterator on all subtrees of the element """)
              
    def postsubtrees(self):
        for e in self.subtree().postsubtrees() :
            yield e
    #postsubtrees = property(__iter_postsubtrees, None, None, """ Postorder iterator on all subtrees of the element """)
           
    def breadthsubtrees(self):
        for e in self.subtree().breadthsubtrees() :
            yield e
    #breadthsubtrees = property(__iter_breadthsubtrees, None, None, """ Breadth iterator on all subtrees of the element """)
   
    # TODO: Methods that need two elements as arguments       
    def dist(self, other):
        pass
   
    def path(self, other):
        pass
    
    def level(self, level): 
        """ Iterator on elements at a given level above or below that element in the tree """
        pass     
            
# Tree of unique elements, built on a dictionnary
# it's a triple parent, child, next indexed tree, takes more space but faster for parent method
# than a double child, next index tree
class IndexedTree(dict) :
    """ Dictionnary based tree (actually, forest) of unique hashable elements
            >>> IndexedTree ('a', ('aa', 'ab'), 'b', ('ba', 'bb'), 'c', ('ca', 'cb'))
            >>> {'a': [None, None, 'b'], 'aa': ['a', None, 'ab'], 'c': [None, None, 'a'], 'ab': ['a', None, 'aa'], 'ba': ['b', None, 'bb'], 'bb': ['b', None, 'ba'], 'cb': ['c', None, 'ca'], 'ca': ['c', None, 'cb'], 'b': [None, None, 'c']}
        Can be displayed in idented format with the display() method """
          

    # Tree methods

    # key creation, here key = value
    def key(self, value):
        return value
#        try :
#            hash(value)
#            key = value
#            return key
#        except :
#            raise ValueError, "TreeElement must be hashable"
    
    def has(self, elem):
        if elem.tree == self :  
            return self.has_key(elem.key)
        else :
            return self.has_value(elem.value)
            
    def has_key(self, key):   
        return dict.has_key(self, key)
 
    # for now it's the same thing
    def has_value(self, value):   
        return dict.has_key(self, self.key(value))
        
    def isatom(self):
        """ A tree is atomic if it contains only one element (single root, no subtrees)"""
        roots = self.roots()
        if len(roots) == 1 and not roots[0].child :
            return True
        else :
            return False
    
    def formated(self):
        """ Returns a formated string displaying each line with identation for that tree """
        if self :
            deq = deque(reversed( [(root,0) for root in self.roots()] ) )
            result = ""
            while deq :
                elem, level = deq.pop()
                if elem.child :
                    for c in reversed([k for k in elem.childs()]) :
                        deq.append((c, level+1))            
                result += ">"*level+str(elem.value)+"\n"
        
            return result 
        else :
            return None

    def __init__(self, *args):
        """The initializer"""
        if args:
            # modified to allow initialisation from a nested list call on *args with args = theList            
            if len(args)==1 and util.isIterable(args[0]) :
                args = tuple(args[0])
            # create the dummy 'None' element as top root
            self[None] = None
            parent = self[None]
            last = parent
            for arg in args :
                if arg :
                    if isinstance(arg, IndexedTree) :
                        self.graft(arg)
                        last = arg.lastroot()
                    elif util.isIterable(arg) :
                        self.graft(IndexedTree(*arg), last, None)    
                        # last not changing it is grafted under it not after                    
                    else :
                        element = self.add(arg, parent)
                        last = element 
        else :
            self = {}

    # redefine get and set methods to always use elements
    def __getitem__(self,val):
        if isinstance(val, TreeElement) :
            value = val.value
        else :
            value = val
        key = self.key(value)
        if self.has_key(key) :
            return dict.__getitem__(self, key)
        else :
            raise KeyError, "%r not in IndexedTree" % val
        
    def __setitem__(self,key,val):
        if isinstance(key, TreeElement) :
            key = key.key
        if isinstance(val, TreeElement) :       
            value = val.value
        else :
            value = val
        if not key :
            key = self.key(value)
        # no checking, will initialize or overwrite with a new element with None index and a new key
        dict.__setitem__(self, key, TreeElement(value, self))

    def get(self, elem, default=None):
        if isinstance(key, TreeElement) :
            key = elem.key
        else :
            key = elem    
        if self.has_key(key):
            return self[key]
        else:
            return default
 
    # removes an element and reparent its childs to its former parent
    # to remove whole subtree use prune instead
    def pop(self, key):
        if isinstance(key, TreeElement) :
            key = key.key         
        if self.has_key(key) :
            pass    # prune
        else :
            raise KeyError, "IndexedTree does not contain %r" % key

    # x.__cmp__(y) <==> cmp(x,y) works as for dict
    
    # accepts Elements or subtrees
    def __contains__(self, arg):
        if self :
            if isinstance(arg, IndexedTree) :
                result = True
                for root in arg.roots() :
                    if self.has(root) :
                        result = result and self[root].subtree() == arg[root].subtree()
                    else :
                        result = False
                        break
                return result                    
            elif isinstance(arg, TreeElement) :
                return self.has(arg)
            else :
                return self.has_value(arg)
        else :
            return false 
 
    def add(self, val, parent=None, next=None):
        if isinstance(val, TreeElement) :       
            value = val.value
        else :
            value = val
        key = self.key(value)
        elem = TreeElement(value, self)
        self[elem] = elem
        elem = self[elem]
        elem.parent = parent
        if next :
            elem.next = next
        return elem

    def __strIter(self):
        temp = []
        for root in self.roots() :
            ctemp = [child.subtree().__strIter() for child in root.childs()]
            if ctemp :
                temp.append("'%s', (%s)" % (str(root), ", ".join(ctemp)))
            else :
                temp.append("'%s'" % str(root))
        return "%s" % (", ".join(temp))

    def __str__(self):
        if self:
            return "(%s)" % (self.__strIter())
        else:
            return "()"

    def __unicodeIter(self):
        temp = []
        for root in self.roots() :
            ctemp = [child.subtree().__unicodeIter() for child in root.childs()]
            if ctemp :
                temp.append(u"'%s', (%s)" % (unicode(root), u", ".join(ctemp)))
            else :
                temp.append(u"'%s'" % unicode(root))
        return u"%s" % (u", ".join(temp))
 
    def __unicode__(self):
        if self:
            return u"(%s)" % (self.__unicodeIter())
        else:
            return u"()"

    def __reprIter(self):
        temp = []
        for root in self.roots() :
            ctemp = [child.subtree().__reprIter() for child in root.childs()]
            if ctemp :
                temp.append(u"%r, (%s)" % (root.value, u", ".join(ctemp)))
            else :
                temp.append(u"%r"%root.value)
        return u"%s" % (u", ".join(temp))
                
    def __repr__(self):
        if self:
            return u"%s(%s)" % (self.__class__.__name__, self.__reprIter())
        else:
            return u"%s()" % self.__class__.__name__ 
         
    # IndexedTree iterators
    
    def elements(self):
        """Direct iterate on keys, order is undefined."""
        if self:
            for k in self.keys() :
                if k:
                    yield self[k]    # Element     
               
    # make default iterator a preorder iterator, as "flat" list of elements won't make sens
    def __iter__(self):
        """Default iterator is preorder."""
        for e in self.preorder() :
            yield e
  
    def preorderElements (self) :
        """ iterator doing a preorder expansion of args """
        deq = deque(reversed( [(root,0) for root in self.roots()] ) )
        result = deque()
        while deq :
            elem, level = deq.pop()
            if elem.child :
                for c in reversed([k for k in elem.childs()]) :
                    deq.append((c, level+1))            
            result.append(elem)
    
        return tuple(result)  
                    
    def preorder(self):
        """The standard preorder traversal iterator."""
        if self:
            for root in self.roots():
                yield root
                for child in root.childs() :
                    subtree = child.subtree()
                    for elem in subtree.preorder() :
                        yield elem
    # pre = property(__iter_preorder, None, None, """ Preorder iterator on the elements of the tree """)

    def postorder(self):
        """Postorder traversal of a tree."""
        if self:
            for root in self.roots():
                for child in root.childs() :
                    subtree = child.subtree()
                    for elem in subtree.postorder() :
                        yield elem
                yield root
    # post = property(__iter_preorder, None, None, """ Postorder iterator on the elements of the tree """)
    
    def breadth(self):
        """breadth first traversal of a tree."""
        if self:   
            deq = deque(x for x in self.roots())
            while deq :
                elem = deq.popleft()
                if elem.child :
                    for c in elem.childs() :
                        deq.append (c)
                yield elem
            
    # breadth = property(__iter_preorder, None, None, """ Breadth first iterator on the elements of the tree """)
    
    #The "inplace" iterators.
    def subtrees(self):
        """Preorder iterator over the subtrees, modifying tree while in an iterator loop is not advised."""
        for tree in self.presubtrees():
            yield tree

    def presubtrees(self):
        """Preorder iterator over the subtrees, modifying tree while in an iterator loop is not advised."""
        if self:
            for root in self.roots():
                yield root.subtree()
                for child in root.childs() :
                    subtree = child.subtree()
                    for tree in subtree.presubtrees():
                        yield tree

    def postsubtrees(self):
        """Postorder iterator over the subtrees.

        Warning: As always, do not use this iterator in a for loop while altering
        the structure of the tree."""
        pass

    def breadthsubtrees(self):
        """breadth first traversal of a tree."""
        pass
    


#    #The "inplace" iterators.
#    def subtree(self):
#        """Preorder iterator over the subtrees.
#
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""
#
#        if self:
#            yield self
#            for subtree in self.childs:
#                for tree in subtree.subtree():
#                    yield tree
#
#    def postsubtree(self):
#        """Postorder iterator over the subtrees.
#
#        Warning: As always, do not use this iterator in a for loop while altering
#        the structure of the tree."""
#
#        if self:
#            for subtree in self.childs:
#                for tree in subtree.postsubtree():
#                    yield tree
#            yield self
#
#    def breadthsubtree(self):
#        """breadth first traversal of a tree."""
#        if self:
#            yield self        
#            deq = deque(x for x in self.childs)
#            while deq :
#                arg = deq.popleft()
#                if not arg.isatom() :
#                    for a in arg.childs :
#                        deq.append (a)
#                else :
#                    yield arg
    
    
    # methods that don't need an additionnal argument  
    def firstroot (self) :
        root = None
        if self.has_key(None) :
            # first ordered root
            root = self[None].child
        else :       
            for k in self.keys() :
                if not self[k].parent :
                    root = self[k]
                    break
        if root :
            return root
        else :
            raise ValueError, "IndexedTree should have at least one root"
    #firstroot = property(__firstRoot, None, None, "The first root (to get them in correct order).")
 
    def roots(self):
        """ Get all roots (elements with None as parent) """
        root = self.firstroot()
        yield root
        for s in root.siblings() :
            yield s
    #roots = property(__iter_roots, None, None, "The iterator over the roots.")   

    def lastroot (self) :
        roots = [k for k in self.roots()]
        if roots :
            return roots[-1]
        else :
            raise ValueError, "IndexedTree should have at least one root"
 
    def leaves(self):
        """ Get all leaves (elements with None as child) """
        for elem in self.pre() :
            if not elem.child :
                yield elem
    #leaves = property(__iter_leaves, None, None, "The iterator over the roots.") 
    
    # TODO : probably not the fastest method here
    def depth(self):
        """ Get maximum depth (distance from root to furthest leave) of the tree """
        max_depth=0
        for l in self.leaves() :
            depth = l.depth()
            if depth > max_depth :
                max_depth = depth
        return max_depth           
    #depth = property(__get_depth, None, None, "The total depth of the tree (maximum depth of the subtrees).")
                    
     #Add or delete trees to the given node of the tree.
    def graft(self, arg, parent=None, next=None):
        """Attach a tree or element as child to the given node of the tree, if no node is given, it is added as a separate tree at root level"""

        if self:                                     
            # print "Argument %s of type %s" % (arg, type(arg))
            if isinstance(arg, IndexedTree):
                # keys must be unique ('None' key is a special case)
                inter = set(self.keys())&set(arg.keys())-set([None])
                if inter :
                    raise ValueError, "Both IndexedTrees share common elements: %s" % inter
                # possibly check for duplicate per subtree and skip only those with duplicates
                # add entries of arg to self
                # can do something faster with update and key translation than element by element addition
                # redefined update if key != val as here and to update tree wek ref
                # roots = [k for k in arg.roots()]
                # self.update(arg)
                # reparent the roots
                # for root in roots :
                #    root.parent = parent
                
                # slow way, recurse add
                for root in arg.roots() :
                    self.add(root, parent, next)
                    for child in root.childs() :
                        self.graft(child.subtree(), parent=self[root])

                    
            elif isinstance(arg, IndexedTree.element) :
                 self.add(arg, parent, next)     
            else :
                raise TypeeError, "Only Trees or Elements can be grafted to other Trees"
        else:
            self = IndexedTree(arg)
    

    def prune(self, arg):
        """ Ungrafts a subtree from the current node. """
        pass
            


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

def indexedTreeFromChildLink (isExactChildFn, *args):
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
    deq = deque(IndexedTree(arg) for arg in args)
    lst = []
    it = 0
    while deq:
        it+=1
        # print "iteration %i deq= %s, lst= %s"% (it, deq, lst)
        c = deq.popleft()
        hasParent = False        
        for p in list(deq)+lst :
            for pr in filterIter(lambda x:isExactChildFn(c.firstroot().value, x.value), p.preorder()) :
                # print "%s is child of %s" % (c, pr)                        
                if not hasParent :
                    # print "graft %s on %s, under %s" % (c, p, pr) 
                    p.graft(c, p[pr])
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


#iTree = IndexedTree ('a', ('aa', 'ab'), 'b', ('ba', 'bb'), 'c', ('ca', 'cb'))
#print iTree.formated()
#jTree = IndexedTree ('1', ('11', '12'), '2', ('21', '22'), '3', ('31', '32'))
#print jTree.formated()
#kTree = IndexedTree(1, (2, (20, 21, (210, 211)), 3, (30, 31)) )
#print kTree.formated()
#print repr(iTree)
#print iTree
#print unicode(iTree)
#print iTree.formated()
#sub = iTree['a'].subtree()
#print sub
#print iTree['ba'].parent
#
#print [k.value for k in iTree]
#print [k.value for k in iTree.postorder()]
#print [k.value for k in iTree.breadth()]
#print "-----------------"
#print [k.value for k in iTree.preorder()]
#print map(lambda x:x.value, iTree.preorderElements())
#
#for t in iTree.subtrees() :
#    print t
#print [k.value for k in iTree['ba'].parents()]

