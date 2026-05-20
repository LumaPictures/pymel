from pymel.util.testing import TestCase, setupUnittestModule
import pymel.util.trees as trees

class testCase_typeTrees(TestCase):
    def setUp(self):
        self.types = ('dependNode', ('FurAttractors', ('FurCurveAttractors', 'FurDescription', 'FurGlobals'), 'abstractBaseCreate'))
        self.tree = trees.Tree( *(self.types) )
    def test01_parentMethod(self):
        """ Test the parent method on type tree """
        pass
    def tearDown(self):
        pass


# to be organised in nice unit tests :


#print dir(FrozenTree)
#print dir(Tree)
##print dir(IndexedFrozenTree)
##print dir(IndexedTree)
#a = Tree ('a', ('aa', 'ab'), 'b', ('ba', 'bb'))
#print a
#print list(a)
#print list(a.preorder())
#print str(a)
#print repr(a)
#print unicode(a)
#print a.formatted()
#print a.debug()
#t = Tree ('a', ('aa', 'ab'))
#print id(t)
#print t.debug()
#t.graft('b')
#print id(t)
#print t.debug()
#b = Tree ('a')
#print id(b)
#print b.debug()
#b.graft('b')
#print b.debug()
#b.graft('ab', 'a')
#print b.debug()
#aa = Tree ('aa', ('aaa', 'aab'))
#print id(aa)
#print aa.debug()
## FIXME : next doesn't work
#b.graft(aa, 'a', 'ab')
#print id(b)
#print id(aa), id(b['aa'])
#print b.debug()
#b.remove('ab')
#ab = FrozenTree('ab', ('aba', 'abb'))
#print id(ab)
#print ab.debug()
#b.graft(ab, 'a')
#print id(b)
#print id(ab), id(b['ab'])
#print b.debug()
#b.graft('c')
#print b.debug()
#b.remove('c')
#print b.debug()
#b.graft('c', 'b')
#print b.debug()
#b.graft(('ba', 'bb'), 'c')
#print b.debug()
## FIXME : pop not working yet
## b.pop('c')
#print b.debug()
#b.prune('a')
#print b.debug()
#b.graft(('a', ('aa', 'ab')), None, 'b')
#print b.debug()
#print list(b.tops())
#print b.top(0)
#print b.top(1)
##print isinstance(a, list)
##print issubclass(a.__class__, list)
#print id(a)
#print a.root()
#print id(a)
#print a.next
#print a.child(0)
#print a.child(0).next
#print a.formatted()
#print a.debug()
#b = a
#print b.debug()
#c = a.copy()
#print c.debug()
#print c.formatted()
#print a == b
#print a is b
#print a == c
#print a is c
#for k in a.breadth() :
#    print k.value
#for k in a :
#    print k.value
#for k in a.postorder() :
#    print k.value
#
#A = Tree ('a', ('aa', ('aaa', 'aab', 'aac'), 'ab', 'ac', ('aca', 'acb')), 'b', ('ba', 'bb'), 'c', ('ca', ('caa', 'cab', 'cac'), 'cb', ('cba', 'cbb'), 'cc', ('cca', 'ccb', 'ccc')))
#print id(A)
#for k in A :
#    print k.value
#for k in A.preorder() :
#    print k.value
#for k in A.postorder() :
#    print k.value
#for k in A.breadth() :
#    print k.value
#print b in a
#print c in a
#print a.child(0) in a
#print c.child(0) in a
#print c.child(0).value in a
#for k in A :
#    parentValues = [j.value for j in k.parents()]
#    root = k.root()
#    if root :
#        rootValue = root.value
#    else :
#        rootValue = None
#    print "%s: %s, %s" % (k.value, rootValue, parentValues)
#
#
#temp = Tree ('a', ('aa', 'ab'), 'b', ('ba', 'bb'))
#suba = temp['aa']
#print suba
#print suba.root()
#print temp
#print id(temp)
#print suba.root().parent
#print id(suba.root().parent)
##print a[a.child(0)]
##print a
##l = a['a']
##print l
##print a[('a', 'aa')]
#del (temp)
## print a
#print suba
#print suba.root()
#print suba.root().parent
#print id(suba.root().parent)
#d = Tree ('a', ('aa', 'ab'), 'b', ('aa', 'ab'))
#def getAsList(tree, value):
#    msg = ""
#    try :
#        tree[value]
#        print "Found exactly one match"
#    except :
#        msg =  "Not exactly one match"
#    f = tree.get(value, [])
#    if msg :
#        print msg+": %i found" % len(f)
#    for k in f:
#        print k, k.parent
#    return f
#getAsList(d, 'aa')
#getAsList(d,('b', 'ab'))
#getAsList(d,'xyz')
#getAsList(d,(None, 'aa'))
#getAsList(d,(None, d.child(0).child(0)))
#getAsList(d,(None, 'a', 'aa'))
#getAsList(d,('a', 'aa'))
#A = Tree ('a', ('aa', ('aaa', 'aab', 'aac'), 'ab', 'ac', ('aca', 'acb')), 'b', ('ba', 'bb'), 'c', ('ca', ('caa', 'cab', 'cac'), 'cb', ('cba', 'cbb'), 'cc', ('cca', 'ccb', 'ccc')))
#print list(A.path('aca'))
#for k in A.path('aca') :
#    print k.value
#for k in A['aca'].path(A) :
#    if k.value :
#        print k.value
#


#def getParent(c) :
#    res = cmds.listRelatives(c, parent=True)
#    if res :
#        return res[0]
#
#def isExactChildFn(c, p) :
#    """ a function to check if c is a direct child of p """
#    if (c is not None) and (p is not None) :
#        #print "checking if "+c+" is child of "+p
#        prt = getParent(c)
#        if prt is not None and p is not None :
#            return prt == p
#        elif prt is None and p is None :
#            return True
#        else :
#            return False
#    else :
#        return False
#
#def asOldHierarchy (*args) :
#    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
#        as argument, or the current seleciton if no arguments are provided,
#        in a way that mimics the Maya scene hierarchy existing on these nodes.
#        Note that:
#        >>> cmds.file ("~/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
#        >>> File read in 0 seconds.
#        >>> u'~/pymel/examples/skel.ma'
#        >>> select ('FBX_Hips', replace=True, hierarchy=True)
#        >>> sel=ls(selection=True)
#        >>> skel=asHierarchy (sel)
#        >>> skel.find('FBX_Head')
#        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
#        >>> skel.parent('FBX_Head')
#        >>> Joint('FBX_Neck1')
#        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
#        >>> True """
#
#    if len(args) == 0 :
#        nargs = cmds.ls( selection=True)
#    else :
#        args = util.expandArgs (*args)
#        # nargs = map(PyNode, args)
#    nargs = args
#    # print "Arguments: %s"+str(nargs)
#    result = oldTreeFromChildLink (isExactChildFn, *nargs)
#    # print "Result: %s"+str(result)
#    return result
#
#def asHierarchy (*args) :
#    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
#        as argument, or the current seleciton if no arguments are provided,
#        in a way that mimics the Maya scene hierarchy existing on these nodes.
#        Note that:
#        >>> cmds.file ("~/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
#        >>> File read in 0 seconds.
#        >>> u'~/pymel/examples/skel.ma'
#        >>> select ('FBX_Hips', replace=True, hierarchy=True)
#        >>> sel=ls(selection=True)
#        >>> skel=asHierarchy (sel)
#        >>> skel.find('FBX_Head')
#        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
#        >>> skel.parent('FBX_Head')
#        >>> Joint('FBX_Neck1')
#        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
#        >>> True """
#
#    if len(args) == 0 :
#        nargs = cmds.ls( selection=True)
#    else :
#        args = util.expandArgs (*args)
#        # nargs = map(PyNode, args)
#    nargs = args
#    # print "Arguments: %s"+str(nargs)
#    result = treeFromChildLink (isExactChildFn, *nargs)
#    # print "Result: %s"+str(result)
#    return result
#
#def asIndexedHierarchy (*args) :
#    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
#        as argument, or the current seleciton if no arguments are provided,
#        in a way that mimics the Maya scene hierarchy existing on these nodes.
#        Note that:
#        >>> cmds.file ("~/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
#        >>> File read in 0 seconds.
#        >>> u'~/pymel/examples/skel.ma'
#        >>> select ('FBX_Hips', replace=True, hierarchy=True)
#        >>> sel=ls(selection=True)
#        >>> skel=asHierarchy (sel)
#        >>> skel.find('FBX_Head')
#        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
#        >>> skel.parent('FBX_Head')
#        >>> Joint('FBX_Neck1')
#        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
#        >>> True """
#
#    if len(args) == 0 :
#        nargs = cmds.ls( selection=True)
#    else :
#        args = util.expandArgs (*args)
#        # nargs = map(PyNode, args)
#    nargs = args
#    # print "Arguments: %s"+str(nargs)
#    result = indexedTreeFromChildLink (isExactChildFn, *nargs)
#    # print "Result: %s"+str(result)
#    return result
#
#def asNetworkXHierarchy (*args) :
#    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
#        as argument, or the current seleciton if no arguments are provided,
#        in a way that mimics the Maya scene hierarchy existing on these nodes.
#        Note that:
#        >>> cmds.file ("~/pymel/examples/skel.ma", f=True, typ="mayaAscii",o=True)
#        >>> File read in 0 seconds.
#        >>> u'~/pymel/examples/skel.ma'
#        >>> select ('FBX_Hips', replace=True, hierarchy=True)
#        >>> sel=ls(selection=True)
#        >>> skel=asHierarchy (sel)
#        >>> skel.find('FBX_Head')
#        >>> Tree(Joint('FBX_Head'), Tree(Joint('FBX_LeftEye')), Tree(Joint('FBX_RightEye')))
#        >>> skel.parent('FBX_Head')
#        >>> Joint('FBX_Neck1')
#        >>> util.expandArgs( skel ) == tuple(sel) and sel == [k for k in skel]
#        >>> True """
#
#    if len(args) == 0 :
#        nargs = cmds.ls( selection=True)
#    else :
#        args = util.expandArgs (*args)
#        # nargs = map(PyNode, args)
#    nargs = args
#    # print "Arguments: "+str(nargs)
#    result = networkXTreeFromChildLink (isExactChildFn, *nargs)
#    # print "Result: "+str(result)
#    return result
#
#
#
#def networkXTreeFromChildLink (isExactChildFn, *args):
#    """
#    This function will build a tree from the provided sequence and a comparison function in the form:
#        cmp(a,b): returns True if a is a direct child of b, False else
#    >>> lst = ['aab', 'aba', 'aa', 'bbb', 'ba', 'a', 'b', 'bb', 'ab', 'bab', 'bba']
#    >>> def isChild(s1, s2) :
#    >>>     return s1.startswith(s2) and len(s1)==len(s2)+1
#    >>> forest = treeFromChildLink (isChild, lst)
#    >>> for tree in forest :
#    >>>     print tree
#    A child cannot have more than one parent, if the isChild is ambiguous an exception will be raised
#    >>> def isChild(s1, s2) :
#    >>>     return s1.startswith(s2)
#    >>> forest = treeFromChildLink (isChild, lst)
#    """
#    deq = deque()
#    for arg in args :
#        t = nt.Tree()
#    t.add_node(arg)
#    t.root = arg
#    deq.append(t)
#    lst = []
#    it = 0
#    while deq:
#        it+=1
#        # print "iteration %i" % it
#        c = deq.popleft()
#    r = c.root
#        hasParent = False
#    fulllist = list(deq)+lst
#    sd = len(deq)
#    nextlist = []
#        for p in fulllist :
#        plist = []
#        for n in p.nodes_iter() :
#        # print "Is %s child of %s?" % (r, n)
#                if isExactChildFn(r, n) :
#                    plist.append(n)
#                    # print "%s is child of %s!" % (r, n)
#        for pr in plist :
#                if not hasParent :
#                    # print "graft %s on %s, under %s" % (r, p.root, pr)
#                    np = p.union_sub(c, v_from=p.root, v_to=c.root)
#            np.root = p.root
#            p = np
#                    hasParent = True
#                else :
#                    # should only be one parent, break on first encountered
#                    raise ValueError, "A child in Tree cannot have multiple parents, check the provided isChild(c, p) function: '%s'" % isExactChildFn.__name__
#            nextlist.append(p)
#    deq = deque(nextlist[:sd])
#    lst = nextlist[sd:]
#    # If it's a root we move it to final list
#        if not hasParent :
#            # print "%s has no parent, it goes to the list as root" % str(c.root)
#            lst.append(c)
#
#    # print "final list %s" % str(lst)
#    if len(lst) == 1 :
#        return lst[0]
#    else :
#        return tuple(lst)

setupUnittestModule(__name__)