"""
A tree module that can wrap either pure python tree or the networkx library if present
"""


#Import generators.
from __future__ import generators
#Pymel add
# removed as it's 2.5 only
# import functools as ftools
from collections import *
import inspect
import warnings
import weakref as weak
from copy import *


#Utility

def isSequence(x):
    return type(x) is list or type(x) is tuple
              
def isTree(x):
    return (type(type(x)) is MetaTree)

def isImmutableTree(x):
    if isTree(x) :
        return x.__getattribute__('parent').fset is None
    else :
        return False

def isMutableTree(x):
    if isTree(x) :
        return x.__getattribute__('parent').fset is not None
    else :
        return False
    
class MetaTree(type):
    # to create Tree classes
    class PyTree():
        """Core methods for pure python trees implementation"""
        # these are the methods depending on implementation
        # a weak ref proxy of the parent/super (containing Tree) to allow faster parent lookup methods
        _pRef = None
        # the storage for value (top element of that tree)
        _value = None
        # the storage for subtrees, must be an iterable (and ordered if you want to have siblings order)
        # can be immutable or mutable
        _subtrees = None
        
        # decorator to identify write methods (that are only valid for mutable trees)
        def mutabletree(f) :
            f.mutabletree = True
            return f          

        # Conversion to correct storage for subtrees
        def _toSubtree(cls, subtrees):
            """ Converts a list/tuple of subtrees to the appropriate date structure for that class
                Returns None for None or an empty list or tuple """
            if subtrees :
                return cls.TreeType(subtrees)
            else :
                return None       
        _toSubtree = classmethod(_toSubtree)
        
        # init
        def __init__(self, *args, **kwargs):
            """ The initializer, it allows for initializing forests as all first level values will be considered roots """
            parent = kwargs.get('parent', None)
            if parent is not None :
                pRef = weak.ref(parent)
            else :
                pRef = None
            roots = []
            for arg in args :
                childs = []
                if isTree(arg) :
                    # we need to do a shallow copy if it's not the same tree type, or not already a subtree of self
                    if isinstance(arg, self.__class__) and arg.parent is self :
                        avalue = arg.value
                        if avalue : 
                            roots += [arg]                                                      # one item in childs : the subtree
                        else :
                            roots += [c for c in arg.childs()]                    # all childs of subtree in childs
                    else :                    
                        avalue = arg.value
                        if avalue : 
                            roots += [self.__class__(avalue, tuple(c for c in arg.childs()), parent=self)]     # one item in childs : the subtree
                        else :
                            roots += [self.__class__(c, parent=self) for c in arg.childs()]                    # all childs of subtree in childs             
                elif isSequence(arg) :
                    # we use sequences to encapsulate childs
                    d = {'parent':self}
                    sub = self.__class__(*arg, **d)
                    if sub.value :
                        childs = [sub]
                    else :
                        childs = list(sub.childs())
                elif arg is not None :
                    # argument at top level is a root
                    sub = self.__class__()
                    sub._pRef = pRef
                    sub._value = arg
                    roots.append(sub)
                else :
                    raise ValueError, "None cannot be a tree element"
                # add resulting childs if any
                if childs :
                    # parent to previous entry if previous entry has no childs, childs are already self.__class__ copies
                    # coming from a sequence expansion                  
                    if roots and not roots[-1].hasChilds() :
                        for c in childs :
                            c._pRef = weak.ref(roots[-1])
                        roots[-1]._subtrees = self.__class__._toSubtree(childs)                 
                    else :
                        roots += childs
                
            if not roots :
                self._pRef = None
                self._value = None
                self._subtrees = None                 
            elif len(roots) == 1 :
                # we don't need the None root if the tree is not a forest
                self._pRef = pRef               
                self._value = roots[0]._value               # roots is filled with copies so not need to copy again
                self._subtrees = roots[0]._subtrees
            else :
                # more than one root, a None root as added on top
                self._pRef = pRef
                self._value = None
                self._subtrees = self.__class__._toSubtree(roots)
            # update the weak refs of childs to self
            for sub in self.childs() :
                sub._pRef = weak.ref(self)

        def __nonzero__(self) :
            try:
                return (self._value is not None or self._subtrees is not None)
            except :
                return False 
        def isElement(self):
            if self :
                return (self._value is not None and self._subtrees is None)
            else :
                return False
        def hasChilds(self):
            if self :
                return (self._subtrees is not None)
            else :
                return False                                           
        # by default only define get methods, set will be defined if the data type is mutable
        # and properties than can be either read only or read-write will be (re)defined accordingly at class creation
        # we always return trees / elements which value an be read from the value property
        
        # to be bound to properties
        def _get_value(self):
            return self._value
        # only for mutable
        @ mutabletree
        def _set_value(self, value):
            if value is not None :
                self._value = value               
        def _get_parent(self) :
            if self._pRef :
                # can remove 
                if not self._pRef() is self :
                    return self._pRef()
                else :
                    raise RuntimeError, "Loop detected in tree %r on parent of %s", (self, self._get_value())
        # only for mutable
        @ mutabletree         
        def _set_parent(self, parent) :
            if parent is None :
                # unparenting
                if self._pRef is None :
                    return
                else :
                    oldparent = self._pRef()
                    # FIXME : we more or less assume it's a list here using remove instead of more generic iterable methods
                    oldparent._subtrees.remove(self)
                    # clean old parent subtrees if it dropped to 0
                    l = len(tuple(oldparent._subtrees))
                    if l == 0 :
                        oldparent._subtrees = None
                    elif l == 1 :
                        # if old parent was a forest and now has only only child, get rid of the None root
                        if oldparent._get_value() is None :
                            c = tuple(oldparent._subtrees)[0]
                            oldparent._set_value(c._get_value())
                            oldparent._subtrees = c._subtrees
                    # remove reference from self to old parent
                    self._pRef = None
            elif isinstance(parent, self.__class__) :
                if not parent is self :
                    # first unparent nicely if needed                    
                    if self._pRef is not None :
                        if self._pRef() is parent :
                            # what the fuss then ?
                            return
                        else :
                            # unparent
                            self._set_parent(None)
                    # then reparent as last child under 'parent'
                    # if self is actually a forest, we'll instead parent all childs of self
                    if self._get_value() is not None :
                        subs = [self]
                    else :
                        subs = list(iter(self._subtrees))
                    for s in subs :
                        s._pRef = weak.ref(parent)
                        if parent._subtrees is None :
                            parent._subtrees = [s]
                        else :
                            # should not happen if the usual methods are used 
                            for c in iter(parent._subtrees) :
                                if c is s :          # not == of course
                                    raise RuntimeError, "Self was already present in the childs of parent?"
                            parent._subtrees.append(s)
                    # now make self point to the new parent instead
                    if self._get_value() is None :
                        p = parent._get_parent()
                        self._pRef = weak.ref(p)
                        self._value = parent._value
                        self._subtrees = parent._subtrees                          
                else :
                    raise RuntimeError, "Setting self parent to itself would create a loop in tree %r" % self
            else :
                raise TypeError, "Can only reparent self to same type '%s' than self, not to '%s'" % (type(self), type(parent))                                                  
        def _get_next(self) :
            try :
                return self.siblings().next()
            except StopIteration:
                return None
        @ mutabletree
        def _set_next(self, next) :
            parent = self._get_parent()
            if parent is not None :
                if parent._subtrees is not None :
                    l = len(tuple(parent._subtrees))
                    if l :
                        if next is None :
                            # nothing to do if self is unique child
                            if len(sseq) > 1  :
                                # FIXME : we more or less assume it's a list here using remove instead of more generic iterable method
                                try :
                                    parent._subtrees.remove(self)
                                except ValueError :
                                    raise RuntimeError, u"Invalid tree, parent of self '%s' does not have self in its subtrees" % self.value
                                parent._subtrees.append(self)
                        else :
                            if not isinstance(next, self.__class__) :
                                next = self.__class__(next)
                            # nothing to do if self == next
                            if self != next :
                                it = iter(parent._subtrees)
                                for s in it :
                                    if s == self :
                                        try :
                                            n = it.next()
                                        except StopIteration :
                                            n = iter(parent._subtrees).next()
                                        # nothing to do is next is already self's next
                                        if n != next :
                                            # FIXME : we more or less assume it's a list here using remove and insert instead of more generic iterable methods
                                            parent._subtrees.remove(self)
                                            try :
                                                j = parent._subtrees.index(next)
                                            except ValueError :   
                                                raise ValueError, "Provided next element '%s' is not a sibling of self '%s'" % (next.value, self.value)
                                            parent._subtrees.insert(j, self)
                                # if self was not found, something is very wrong
                                raise RuntimeError, u"Invalid tree, parent of self '%s' does not have self in its subtrees" % self.value           
                    else :
                        raise RuntimeError, u"Invalid tree, parent of self '%s' has an empty subtrees list" % self.value                    
                else :
                    raise RuntimeError, u"Invalid tree, parent of self '%s' has an empty subtrees list" % self.value
            raise ValueError, "Self has no parent, we can't change it's order in the list of its siblings, having none"        
        # methods (for both mutable and immutable)
        def childs(self):
            """ Returns an iterator on all childs of self, or an empty iterator if self has no childs """
            if self._subtrees :
                return iter(self._subtrees)
            else :
                return iter(self.__class__.TreeType())              
        def siblings (self):
            """ Returns an iterator on self siblings, not including self and starting with self next sibling,
                if self has no siblings (self has no parent or is unique child) then returns an empty iterator """
            parent = self._get_parent()
            if not parent :
                return iter(self.__class__.TreeType())
            else :
                cseq = tuple(parent.childs())
                for i in range(len(cseq)) :
                    if cseq[i] is self : # not ==
                        return iter(cseq[i+1:]+cseq[:i])
                # self should be in it's parents subtrees
                raise RuntimeError, u"Invalid tree, parent of %s does not have this subtree in its 'childs'" % self.value
        # get and __getitem__         
        # methods only for mutable
        @ mutabletree
        def add(self, element, parent=None, next=None):
            """ Add an element to self. parent and next element can be specified.
                Element will be added as a child of parent, parent can be any element or subtree of self:
                if parent is specified as a value there must exactly one match in self or an exception will be raised
                if parent is None, element will be added as a sibling of self's top node(s)
                if next is not none, element will be added before next in the childs of parent, else as a last childs """
            if self :
                if not isinstance(element, self.__class__) :
                    element = self.__class__(element)
                if parent is None :
                    parent = self._get_parent()
                    if parent is None :
                        value = self._get_value()
                        if value is not None :
                            # if self is not already a forest, make it one
                            subs = None
                            if self._subtrees is not None :
                                subs = list(iter(self._subtrees))                        
                            selfchild = self.__class__()
                            selfchild._pRef = weak.ref(self)
                            selfchild._set_value(value)
                            selfchild._subtrees = self.__class__._toSubtree(subs)
                            if subs :
                                for sub in subs :
                                    sub._pRef = weak.ref(selfchild)
                            # must do manually
                            self._value = None
                            self._subtrees = self.__class__._toSubtree([selfchild])
                            # print self.debug()
                            # print selfchild.debug()
                        parent = self
                else :
                    # parent must be actually a subtree of self, not a subtree of another tree that happens to be equal in value
                    parent = self[parent]
                element._set_parent(parent) 
            else :
                if isTree(element) :
                    value = element._get_value()
                else :
                    value = element
                self._set_value(value)
                
        @ mutabletree       
        def remove(self, element):
            """ Remove element from self, along with everything under it, will raise an exception if element is not in self """
            # TODO : only handle case where element is subtree of self here and let caller handle search for subtree from value
            self[element].parent = None
        # set and __setitem__
                                   
    class NxTree() :
        """Core methods for trees based on the networkx library """
        
                
    # now the methods for an immutable tree, not depending on implementation
    class ImTree() :
        """The methods for an immutable Tree class."""
                                  
        # Default iterator will allow conversion to list
        # do we want to return values, or skip this alltogether
        # as it force to explicitely declare [tree] to build a list of trees ?
        def __iter__(self):
            """Default iterator is preorder."""
            for e in self.preorder() :
                yield e                   # or yield e.value ?
        
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
                while deq :
                    arg = deq.popleft()
                    yield arg
                    for a in arg.childs() :
                        deq.append (a)     

        def child (self, index=0):
            """ Returns nth child (by default first), is it exists """
            try :
                childs = [k for k in self.childs()]
                return childs[index]
            except :
                return None      
        def parents (self):
            """Returns an iterator on path from element to top root, starting with first parent, empty iterator means self is root"""
            parents = []
            parent = self.parent
            while parent :
                parents.append(parent)
                parent = parent.parent
            return iter(parents)
        def root (self):
            """ Root node of self, if self is a subtree, will travel up to top most node of containing tree """
            root = self
            parent = self.parent
            while parent :
                if parent.value :
                    root = parent
                parent = parent.parent
            return root
        def tops (self):
            """ Iterator on the top nodes of self, the subtrees that have no parent in self,
                will yield only self if self isn't a forest """
            if self.value :
                    yield self
            else :
                for c in self.childs() :
                    yield c
        def top (self, index=0):
            """ The nth top node of self (by default first) """
            try :
                tops = [k for k in self.tops()]
                return tops[index]
            except :
                return None                                                       
        def depth (self) :
            """Depth of self, the distance to self's root"""
            parents = self.parents()
            depth = 0
            for p in parents :
                depth += 1
            return depth        
        def leaves(self):
            """ Get an iterator on all leaves under self """
            for elem in self.preorder() :
                if not elem.hasChilds() :
                    yield elem
        def level(self, dist=0):
            """ Get an iterator on all elements at the specified distance of self, negative distance means up, positive means down """
            deq = deque((self, 0))
            while deq :
                arg, level = deq.popleft()
                if level == dist :
                    yield arg
                elif level > dist :
                    if arg.parent :
                        deq.append((arg.parent, level-1))
                else :
                    for c in arg.childs() :
                        deq.append((c, level+1))
        # Comparison, contains, etc
        #Number of elements in the tree.
        def size(self):
            """Returns the number of elements (nodes) in the tree."""
            ret = 0
            for s in self:
                ret += 1
            return ret
        # use it for len(self)
        __len__ = size            
        def height(self):
            """ Get maximum downward depth (distance from element to furthest leaf downwards of it) of the tree """
            max_depth=0   
            deq = deque((self,0))
            while deq :
                arg, level = deq.popleft()
                if arg.value :
                    level += 1                
                if not arg.isElement() :
                    for a in arg.childs() :
                        deq.append ((a, level))
                else :
                    if level > max_depth :
                        max_depth = level
            return max_depth                   
        # added equivalence test here
        def __eq__(self, other):
            """Checks for equality of two trees."""
            #Both trees not empty.
            if self and other:
                #Compare values.
                if self is other :
                    return True
                elif self.value != self.__class__(other).value:
                    return False
                elif len(self) != len(other) :
                    return False
                else :
                    return reduce(lambda x, y:x and y, map(lambda c1, c2:c1 == c2, self.childs(), other.childs()), True)
            #Both trees empty.
            elif not self and not other:
                return True
            else:
                return False
        def __ne__(self, other):
            return not self.__eq__(other)
        # compare using only top value (if compare is defined for value type) or all values ?  
        def __contains__(self, element):
            """Returns True if element is in the tree, False otherwise."""
            if isTree(element) :
                for sub in self.breadth():
                    if element == sub:
                        return True
                return False          
            else :
                for sub in self.breadth():
                    if element == sub.value:
                        return True
                return False
        # identity, not equivalence test
        def issubtree(self, other) :
            if isinstance(other, self.__class__) :
                parent = self
                while parent :
                    if parent is other :
                        return True
                    parent = parent.parent
            return False
        # this will be redefined for indexed trees where the uniqueness of the elements can allow a more efficient search
        def path (self, element, **kwargs):
            """ Returns an iterator of the path to specified element if found, including starting element,
                empty iterator means no path found.
                For trees where duplicate values are allowed, shortest path is returned """
            # test if we have a hit 
            test = False
            if isTree(element) :
                test = (self == element)
            else :
                test = (self.value == element)         
            if test :
                return iter(tuple([self]))
            depth = kwargs.get("depth", 0)
            found = kwargs.get("found", None)
            # abort if a path of length found has been found, as we will explore parent or childs of self, shortest path we can still
            # hope to find in this branch is depth+1
            if found is not None and not found > abs(depth) + 1 :
                return None            
            # else keep searching
            up = kwargs.get("up", False)
            down = kwargs.get("down", False)
            if not (up or down) :
                up = down = True
            seekup = None
            seekdown = None
            if up and self.parent :
                pitpath = self.parent.path(element, up=True, depth=depth-1, found=found)
                if pitpath :
                    seekup = [self]+list(pitpath)
            if down :
                for c in self.childs() :
                    citpath = c.path(element, down=True, depth=depth+1, found=found)
                    if citpath :
                        cpath = [self]+list(citpath)
                        if not seekdown or len(cpath) < len(seekdown) :
                            seekdown = cpath
                            # length of path is number of nodes in path minus one
                            found = len(seekdown) -1 + abs(depth)
                            # no need to check rest of childs now if found is just depth + 1
                            if not found > abs(depth) + 1 :
                                break
            path = tuple([])
            if seekup and seekdown :
                if len(seekup) <= len(seekdown) :
                    # for equal distance, prefer up
                    path = seekup
                else :
                    path = seekdown
            elif seekup :
                path = seekup
            elif seekdown :
                path = seekdown
            if path :
                # print "found path %s" % path
                return iter(path)
               
        def dist (self, element):
            """Returns distance from self to element, 0 means self==element, None if no path exists"""
            dist = None
            path = tuple(self.path(element))
            if path :
                dist = -1
                for n in path :
                    dist +=1
            return dist
        
        # str, unicode, represent
        def _strIter(self):
            res = ""
            value = self.value           
            if value :
                res = "'%s'" % str(value)
            temp = [sub._strIter() for sub in self.childs()]
            if temp :
                if res :
                    res += ", (%s)" % ", ".join(temp)
                else :
                    res = ", ".join(temp)
            return res

        def __str__(self):
            if self:
                return "(%s)" % (self._strIter())
            else:
                return "()"

        def _unicodeIter(self):
            res = u""
            value = self.value      
            if value :
                res = u"'%s'" % unicode(value)
            temp = [sub._unicodeIter() for sub in self.childs()]
            if temp :
                if res :
                    res += u", (%s)" % u", ".join(temp)
                else :
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
            if value :
                res = "%r" % value
            if temp :
                if res :
                    res += ", (%s)" % ", ".join(temp)
                else :
                    res = ", ".join(temp)
            return res

        def __repr__(self):
            if self:
                return "%s(%s)" % (self.__class__.__name__, self._reprIter())
            else:
                return "()"
    
        def formatted(self, depth=0):
            """ Returns an indented string representation of the tree """
            if self :
                value = self.value
                result = ""
                if value :
                    result += u">"*depth+u"%s\n" % value
                for c in self.childs() :
                    result += c.formatted(depth+1)
                return result    

        def debug(self, depth=0):
            """ Returns an detailed representation of the tree fro debug purposes"""
            if self :
                parent = self.parent
                pvalue = None                
                if parent :
                    pvalue = parent.value
                next = self.next
                nvalue = None                
                if next :
                    nvalue = next.value                    
                result = u">"*depth+u"r:%r<%i>" % (self.value, id(self))
                if parent : 
                    result += ", p:%r<%i>" % (pvalue, id(parent))
                else :
                    result += ", p:None"
                if next :
                    result += ", n:%r<%i>" % (nvalue, id(next))
                else :
                    result += ", n:None"
                result += "\n"                  
                for a in self.childs() :
                    result += a.debug(depth+1)
                return result   
 
        # get the matching subtree to that subtree or element, will be redefined in the case of an indexed tree
        # not that it can return a tuple if same element/subtree is present more than once in tree
        def __getitem__(self,value):
            """ Get a subtree from the Tree, given an element or value.
                Note that to be consistent with __getitem__ usual behavior, it will raise an exception
                it it doesn't find exactly one match (0 or more), method get will be more user friendly
                on non indexed trees.
                It's also possible to seek a path : a list of elements or values, it will limit the results
                to the subtrees that match the last item of the path, and whose parents match the path.
                A path can be relative, or absolute if starting with None as first item """
            result = self.get(value)
            l = len(result)
            if l==1 :
                return result[0]
            elif l == 0 :
                raise KeyError, "No  match for %s in Tree" % value
            else :
                raise KeyError, "More than one match for %s in Tree (%i found)" % (value, l)
            
        def get(self, value, default=tuple()):
            """ Identical to the __getitem__ method but will return a default value instead of raising KeyError
                if nor result is found """
            result = []
            # explore breadth first so that closest items are found faster            
            if isTree(value) :
                # do a faster check in case value is a subtree of self
                if value.issubtree(self) :
                    return [value]
                # normal equivalence test
                for e in self.breadth() :
                    if value == e :
                        result.append(e)
            elif isSequence(value) :
                # we seek a path, a list of value that must be found in order,
                # if list starts with None it means it's an absolute path (starting at root)
                if value :
                    if value[0] is None :
                        result = [self]
                    else :
                        result += list(self.get(value[0]))
                    for p in value[1:] :
                        if result :
                            found = []
                            for t in result :
                                for c in t.childs() :
                                    if c.value == self.__class__(p).value :
                                        found.append(c)
                            result = found
                        else :
                            break                                       
            else :
                for e in self.breadth() :
                    if value == e.value :
                        result.append(e)
            if not result :
                return default
            else :
                return tuple(result)
                
        def copy(self, cls = None):
            """ Shallow copy of a tree.
                An extra class argument can be given to copy with a different
                (tree) class. No checks are made on the class. """
            if cls is None:
                cls = self.__class__
            if self:
                if self.value :
                    subtrees = (self.value,tuple(self.childs()))
                else :
                    subtrees = tuple(self.childs())
                return cls(*subtrees)
            else:
                return cls()
            
        # TODO : isParent (tree, other), isChild(tree, other), inter, union, substraction ?

    class InImTree() :
        """ Additionnal methods for indexed immutable trees """
            
    class MuTree() :
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
    
        def prune(self, element) :
            """ Ungrafts element from self, with everything under it """
            element = self[element]
            self.remove(element)
        
        def pop(self, element) :
            """ Delete top node of self and reparent all it's subtrees under it's current parent.
                If self was a root all it's subtrees become separate trees of a forest under the 'None' root.
                self will now have the new parent as top node """
            element = self[element]
            parent = element.parent       
            for c in element.childs() :
                self.graft(c, parent)
            self.remove(element)         
           
        # TODO: reroot, in-place intersection, union, sub etc  
        def reroot(self, element) :
            """ Reroot self so that element is self new top node """
            pass    
                    
    class InMuTree(object) :
        """ Additionnal methods for indexed mutable trees """        
        pass

 
            
    # class creation 
    def __new__(mcl, classname, bases, classdict):
        # Build a Tree class deriving from a base iterable class, base class must have methods __init__,  __iter__ and __nonzero__
        # by default use list
#        if not bases :
#            bases = (list, )
        # check if base meets requirement, either we derive from another Tree class or from the type that will be used for internal storage
        mutable = None
        indexed = None
        # check for keywords
        if classdict.has_key('mutable') :
            mutable = (classdict['mutable'] == True)
            del classdict['mutable']
        if classdict.has_key('indexed') :
            indexed = (classdict['indexed'] == True)
            del classdict['indexed']
        treeType = None
        # default storage types depending on type of tree
        if mutable :
            treeType = list
        else :
            treeType = tuple            
        # check base classes          
        newbases = []
        for base in bases :
            if type(base) == MetaTree :
                mubase = hasattr(base, 'add')
                inbase = hasattr(base, 'key')
                # Tree type is most complete type of all base classes
                if treeType == None or (not mutable and mubase) or (not indexed and inbase) :
                    treeType = base.treeType
                    mutable = mubase
                    indexed = inbase                   
            # if we need to filter base classes ?
            newbases.append(base)

        # if we couldn't determine a tree type from keywords or base classes, raise an exception                
        if not treeType :
            raise TypeError, "Tree classes must derive from another Tree class, or an iterable type that defines __init__, __iter__ and __nonzero__ at least"
        # store the type of iterable used to represent the class subtrees
        newbases = tuple(newbases)

        # build dictionnary for that class
        newdict = {}
        # methods depending on implementations
        coredict = {}
        # if networkx not present
        for k in MetaTree.PyTree.__dict__.keys() :
            # drawback of organising methods in "fake" classes is we get an uneeded entries
            # don't need __module__ or the decorator mutabletree            
            if k not in ('__module__', 'mutabletree') :
                coredict[k] = MetaTree.PyTree.__dict__[k]
            
        # use methods of core implementation that are relevant to this type of trees
        for k in coredict :
            m = coredict[k]
            if mutable or not hasattr(m, 'mutabletree') :
                newdict[k] = coredict[k]
        
        # set properties read only or read-write depending on the available methods   
        newdict['value'] = property(newdict.get('_get_value', None), newdict.get('_set_value', None), None, """ Value of the top element of that tree """)
        newdict['parent'] = property(newdict.get('_get_parent', None), newdict.get('_set_parent', None), None, """ The parent tree of that tree, or None if tree isn't a subtree """)
        newdict['next'] = property(newdict.get('_get_next', None), newdict.get('_set_next', None), None, """ Next tree in the siblings order, or None is self doesn't have siblings """)          
         
        # upper level methods, depending on type of tree
        # only restriction is you cannot override core methods
        basedict = MetaTree.ImTree.__dict__
        if mutable :
            # add the mutable methods
            mutabledict = MetaTree.MuTree.__dict__
            basedict.update(basedict, **mutabledict)
            
        # update with methods declared at class definition       
        basedict.update(basedict, **classdict)
        # methods that must be defined here depending on the preceding 

        # add  methods unless they clash with core methods
        for k in basedict :
            if k in newdict :
                if k == '__doc__' :
                    newdict[k] = newdict[k] + "\n" + basedict[k]
                else :
                    warnings.warn("Can't override method or propery %s in Trees" % k)
            else :
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

                 
    #To get info on the kind of tree class that was created
#    def __get_treeType(cls):
#        return cls.__treeType
#    tree = property(__get_treeType, doc = "The characteristics of the tree class.")

    def __get_TreeType(cls):
        return cls._TreeType
    TreeType = property(__get_TreeType, None, None, "The type used for internal tree storage for that tree class.")
    
    def __repr__(cls):
        return "%s<TreeType:%r>" % (cls.__name__, cls.TreeType)  


class FrozenTree():
    __metaclass__ =  MetaTree            
    mutable = False
    indexed = False
                    
class Tree():
    __metaclass__ =  MetaTree
    mutable = True
    indexed = False
    
#class IndexedFrozenTree():
#    __metaclass__ =  MetaTree            
#    mutable = False
#    indexed = True
#                    
#class IndexedTree():
#    __metaclass__ =  MetaTree
#    mutable = True
#    indexed = True    



# old code, will be removed as soon as tests are conclusive
  
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

    def formatted (self) :
        """ returns an indented formatted string for display """
        stack = [(self,0)]
        result = ""
        while stack :
            arg, level = stack.pop()
            if not arg.isatom() :
                stack.append( (oldTree(arg.cargo), level) )
                stack += [(x,level+1) for x in arg.childs]
            else :
                result = ">"*level+str(arg.cargo)+"\n"+result
        
        return result

    #The oldTree iterators.
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
        """Shallow copy of a oldTree object."""
        if self:
            if self.isatom():
                return self.__class__(self.cargo)
            else:
                temp = tuple([subtree.copy() for subtree in self.childs])
                return self.__class__(self.cargo, *temp)
        else:
            return self.__class__()


#oldTree implementations.
class oldTree(BaseTree):
    """
    Class implementing an immutable generalized tree type.
        You can initialize explicitely or directly from a nested sequence:
    >>> theTree = oldTree(1, oldTree(2, oldTree(20), oldTree(21, oldTree(210), oldTree(211))), oldTree(3, oldTree(30), oldTree(31)))
    >>> theOtherTree = oldTree(1, (2, (20), (21, (210), (211))), (3, (30), (31)))
    >>> print theTree == theOtherTree
    To build a tree of sequences:
    >>> seqTree = oldTree((1, 2, 3), oldTree((4, 5, 6)), oldTree((7, 8, 9)))
    >>> seqOtherTree = oldTree( (1,2,3), ((4, 5, 6),), ((7, 8, 9),), )
    >>> seqTree == seqOtherTree
    >>> [k for k in seqTree]
    >>> [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
            """

    def __init__(self, *args):
        """The initializer."""
        if args:
            # modified to allow initialisation from nested lists or tuples
            if len(args)==1 and isSequence(args[0]) :
                args = tuple(args[0])
            self.__head = [args[0]]
            for arg in args[1:] :
                if not isinstance(arg, BaseTree) :
                    if isSequence(arg) :
                        self.__head.append(oldTree(*arg))
                    else :
                        self.__head.append(oldTree(arg))
                elif isinstance(arg, oldFrozenTree) :
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
            if isinstance(t, oldTree):
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
                return oldFrozenTree(self.cargo)
            else:
                args = (self.cargo,)
                args = args + tuple([subtree.toFrozenTree() for subtree in self.childs])
                return oldFrozenTree(*args)
        else:
            return oldFrozenTree()

# Immutable tree
class oldFrozenTree(BaseTree):
    """
    Class implementing an immutable generalized tree type.
        You can initialize explicitely or directly from a nested sequence:
    >>> theFrozenTree = oldFrozenTree(1, oldTree(2, oldTree(20), oldTree(21, oldTree(210), oldTree(211))), oldTree(3, oldTree(30), oldTree(31)))
    >>> theOtherFrozenTree = oldFrozenTree(1, (2, (20), (21, (210), (211))), (3, (30), (31)))
    >>> print theFrozenTree == theOtherFrozenTree
            """
    def __init__(self, *args):
        """The initializer"""
        if args:
            # modified to allow initialisation from a nested list call on *args with args = theList            
            if len(args)==1 and isSequence(args[0]) :
                arg = tuple(args[0])
            self.__head = (args[0],)
            for arg in args[1:] :
                if not isinstance(arg, BaseTree) :
                    if isSequence(arg) :
                        self.__head = self.__head + (oldFrozenTree(*arg),)
                    else :
                        self.__head = self.__head + (oldFrozenTree(arg),)
                elif isinstance(arg, oldTree) :
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
                return oldTree(self.cargo)
            else:
                args = (self.cargo,)
                args = args + tuple([subtree.toTree() for subtree in self.childs])
                return oldTree(*args)
        else:
            return oldTree()
        
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
            self.__tree = weak.proxy(tree)
            self.__value = value
            self.__key = self.tree.key(value)
            # element is "nowhere" until parented somehwere    
            self.__index = TripleIndex()               
            #if tree.has_key(key) :
            #    self.__index = weak.proxy(dict.__getitem__(tree, key).__ownIndex)
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
        for c in self.childs() :
            yield c
            for e in c.below() :
                yield e
    #below = property(__iter_below, None, None, """ Preorder iterator on all elements in tree below the element """)

    def preorder(self):
        yield self
        for c in self.childs() :
            for e in c.preorder() :
                yield e
    
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
    
    def formatted(self):
        """ Returns a formatted string displaying each line with identation for that tree """
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
            if len(args)==1 and isSequence(args[0]) :
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
                    elif isSequence(arg) :
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
        """ iterator doing a preorder expansion of the tree elements """
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
                for c in root.preorder() :
                    yield c
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
def oldTreeFromChildLink (isExactChildFn, *args):
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
    deq = deque(oldTree(arg) for arg in args)
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

def treeFromChildLink (isExactChildFn, *args):
    """
    This function will build a tree from the provided sequence and a comparison function in the form:
        cmp(a,b): returns True if a is a direct child of b, False else
    >>> lst = ['aab', 'aba', 'aa', 'bbb', 'ba', 'a', 'b', 'bb', 'ab', 'bab', 'bba']
    >>> def isChild(s1, s2) :
    >>> return s1.startswith(s2) and len(s1)==len(s2)+1
    >>> a = treeFromChildLink (isChild, *lst)
    >>> print a[0].formatted()
    A child cannot have more than one parent, if the isChild is ambiguous an exception will be raised
    >>> def isChild(s1, s2) :
    >>>     return s1.startswith(s2) 
    >>> forest = treeFromChildLink (isChild, lst)    
    """
    deq = deque()
    for arg in args :
        deq.append(Tree(arg))
    lst = []
    it = 0
    while deq:
        it+=1
        #print "iteration %i deq= %s, lst= %s"% (it, deq, lst)
        c = deq.popleft()
        hasParent = False        
        for p in list(deq)+lst :
            pars = list(filterIter(lambda x:isExactChildFn(c.top().value, x.value), p.preorder()))
            for pr in pars :
                #print "%s is child of %s" % (c, pr)                        
                if not hasParent :
                    pr.graft(c, pr)
                    hasParent = True
                else :
                    # should only be one parent, break on first encountered
                    raise ValueError, "A child in Tree cannot have multiple parents, check the provided isChild(c, p) function: '%s'" % isExactChildFn.__name__
        # If it's a root we move it to final list
        if not hasParent :
            #print "%s has not parent, it goes to the list as root" % str(c)
            lst.append(c)
    
    # print "final list %s" % str(lst)
    if len(lst) == 1 :
        return lst[0]
    else :
        return tuple(lst)


#    >>> for tree in forest :
#    >>>     print tree
#    A child cannot have more than one parent, if the isChild is ambiguous an exception will be raised
#    >>> def isChild(s1, s2) :
#    >>>     return s1.startswith(s2) 
#    >>> forest = treeFromChildLink (isChild, lst)   

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
#print iTree.formatted()
#jTree = IndexedTree ('1', ('11', '12'), '2', ('21', '22'), '3', ('31', '32'))
#print jTree.formatted()
#kTree = IndexedTree(1, (2, (20, 21, (210, 211)), 3, (30, 31)) )
#print kTree.formatted()
#print repr(iTree)
#print iTree
#print unicode(iTree)
#print iTree.formatted()
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

#oTree = oldTree(1, 2, 3)
#type(oTree)
#print oTree.formatted()