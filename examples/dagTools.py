"""
    An exemple of use of the Tree library, returns the arguments, or the current selection
    if nothing is provided :
    Open maya file skel.ma then :
    >>> select('FBX_Hips', hierarchy=True)
    >>> lst = ls(selection=True)
    >>> print lst
    >>> tree = asHierarchy (*lst)
    >>> print tree
    >>> print repr(tree)
    >>> lst
    >>> [k for k in tree]
"""

def isExactChildFn(c, p) :
    """ a function to check if c is a direct child of p """    
    if (c is not None) and (p is not None) :
        #print "checking if "+c+" is child of "+p
        prt = c.getParent()
        if prt is not None and p is not None :
            return prt == p
        elif prt is None and p is None :
            return True
        else :
            return False
    else :
        return False

def asHierarchy (*args) :
    """returns a Tree containing the PyMel objects representing Maya nodes that were passed
        as argument, or the current seleciton if no arguments are provided,
        in a way that mimics the Maya scene hierarchy existing on these nodes."""

    if len(args) == 0 :
        nargs = ls( selection=True)
    else :
        args = util.expandListArgs (*args)
        nargs = map(PyNode, args)
    # print "Arguments: %s"+str(nargs)
    result = treeFromChildLink (isExactChildFn, *nargs)
    # print "Result: %s"+str(result)
    return result

