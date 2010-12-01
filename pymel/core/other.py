"""
Functions which are not listed in the maya documentation, such as commands created by plugins,
as well as the name parsing classes `DependNodeName`, `DagNodeName`, and `AttributeName`.
"""

import re
import pymel.internal.pmcmds as cmds
import pymel.internal.factories as _factories
_factories.createFunctions( __name__ )


#--------------------------
# Object Wrapper Classes
#--------------------------

class NameParser(unicode):
    PARENT_SEP = '|'

    def __new__(cls, strObj):
        """Casts a string to a pymel class. Use this function if you are unsure which class is the right one to use
        for your object."""

        # the if statement was failing for some types (ex: pymel.node.Vertex),
        # so forcing into unicode string:
        if cls is not NameParser:
            newcls = cls
        else:
            newcls = _getParserClass(strObj)
        self = super(NameParser, cls).__new__(newcls, strObj)
        return self

    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)

    #def __unicode__(self):
    #    return u"%s" % self

    def __getattr__(self, attr):
        """
            >>> NameParser('foo:bar').spangle
            AttributeName('foo:bar.spangle')

        """
        if attr.startswith('__') and attr.endswith('__'):
            return super(NameParser, self).__getattr__(attr)

        return AttributeName( '%s.%s' % (self, attr) )

        #raise AttributeNameError, 'AttributeName does not exist %s' % attr

    def stripNamespace(self, levels=0):
        """
        Returns a new instance of the object with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.

            >>> NameParser('foo:bar.spangle').stripNamespace()
            AttributeName('bar.spangle')

        """

        nodes = []
        for x in self.split('|'):
            y = x.split('.')
            z = y[0].split(':')
            if levels:
                y[0] = ':'.join( z[min(len(z)-1,levels):] )

            else:
                y[0] = z[-1]
            nodes.append( '.'.join( y ) )
        return self.__class__( '|'.join( nodes) )

    def swapNamespace(self, prefix):
        """Returns a new instance of the object with its current namespace replaced with the provided one.
        The calling instance is unaffected."""
        return self.__class__.addPrefix( self.stripNamespace(), prefix+':' )

    def namespaceList(self):
        """Useful for cascading references.  Returns all of the namespaces of the calling object as a list"""
        return self.lstrip('|').rstrip('|').split('|')[-1].split(':')[:-1]

    def namespace(self):
        """Returns the namespace of the object with trailing colon included"""
        nsList = self.namespaceList()
        if nsList:
            return  ':'.join(nsList) + ':'
        return ''

    def addPrefix(self, prefix):
        'addPrefixToName'
        name = self
        leadingSlash = False
        if name.startswith('|'):
            name = name[1:]
            leadingSlash = True
        name = self.__class__( '|'.join( map( lambda x: prefix+x, name.split('|') ) ) )
        if leadingSlash:
            name = '|' + name
        return self.__class__( name )


    def attr(self, attr):
        """access to AttributeName of a node. returns an instance of the AttributeName class for the
        given AttributeName.

            >>> NameParser('foo:bar').attr('spangle')
            AttributeName('foo:bar.spangle')

        """
        return AttributeName( '%s.%s' % (self, attr) )



class AttributeName(NameParser):
    """

    """
    attrItemReg = re.compile( '\[(\d+:*\d*)\]$')

    #def __repr__(self):
    #    return "AttributeName('%s')" % self

    def __init__(self, attrName):
        if '.' not in attrName:
            raise TypeError, "%s: AttributeNames must include the node and the AttributeName. e.g. 'nodeName.AttributeNameName' " % self
        self.__dict__['_multiattrIndex'] = 0

    def __getitem__(self, item):
        return AttributeName('%s[%s]' % (self, item) )

    # Added the __call__ so to generate a more appropriate exception when a class method is not found
    def __call__(self, *args, **kwargs):
        raise TypeError("The object <%s> does not support the '%s' method" % (repr(self.node()), self.plugAttr()))


    def array(self):
        """
        Returns the array (multi) AttributeName of the current element
            >>> n = AttributeName('lambert1.groupNodes[0]')
            >>> n.array()
            AttributeName('lambert1.groupNodes')
        """
        try:
            return AttributeName(AttributeName.attrItemReg.split( self )[0])
        except:
            raise TypeError, "%s is not a multi AttributeName" % self

    def plugNode(self):
        """plugNode

        >>> NameParser('foo:bar.spangle.banner').plugNode()
        DependNodeName('foo:bar')

        """
        return NameParser( unicode(self).split('.')[0])

    node = plugNode

    def plugAttr(self):
        """plugAttr

        >>> NameParser('foo:bar.spangle.banner').plugAttr()
        u'spangle.banner'

        """
        return '.'.join(unicode(self).split('.')[1:])

    def lastPlugAttr(self):
        """
        >>> NameParser('foo:bar.spangle.banner').lastPlugAttr()
        u'banner'

        """
        return self.split('.')[-1]


    def nodeName( self ):
        'basename'
        return self.split('|')[-1]

    def item(self, asSlice=False, asString=False):
        try:
            item = AttributeName.attrItemReg.search(self).group(1)
            if asString:
                return "[%s]" % unicode(item)
            val = item.split(":")
            val = map(int,val)
            if len(val)>1:
                return asSlice and slice(*val) or val
            return val[0]
        except: return None


    def getParent(self, generations=1):
        """
        Returns the parent attribute

        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> AttributeName("Cube1.multiComp[3].child.otherchild").getParent(2)
                  AttributeName('Cube1.multiComp[3]')

              Negative values will traverse from the top, not counting the initial node name:

                  >>> AttributeName("Cube1.multiComp[3].child.otherchild").getParent(-2)
                  AttributeName('Cube1.multiComp[3].child')

              A value of 0 will return the same node.
              The default value is 1.

              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown).
        """

        if generations==0:
            return self

        split = self.split('.')
        if -len(split) < generations < len(split) - 1:
            if generations < 0:
                # Move it one over to account for the initial node name
                splitIndex = 1 - generations
            else:
                splitIndex = -generations
            try:
                return AttributeName('.'.join(split[:splitIndex]))
            except:
                pass

    def addAttr( self, **kwargs):
        kwargs['longName'] = self.plugAttr()
        kwargs.pop('ln', None )
        from pymel.core.general import addAttr
        return addAttr( self.node(), **kwargs )

    def setAttr(self, *args, **kwargs):
        from pymel.core.general import setAttr
        return setAttr(self, *args, **kwargs)

    set = setAttr
    add = addAttr

    def exists(self):
        node = self.plugNode()
        attr = self.plugAttr()
        if not node or not attr:
            return False

        if not cmds.objExists(node):
            return False

        # short name
        if attr in cmds.listAttr( node, shortNames=1) + cmds.listAttr( node):
            return True

        return False


class DependNodeName( NameParser ):
    #-------------------------------
    #    Name Info and Manipulation
    #-------------------------------

    def node(self):
        """for compatibility with AttributeName class"""
        return self


    def exists(self, **kwargs):
        "objExists"
        return bool( cmds.objExists(self, **kwargs) )


    _numPartReg = re.compile('([0-9]+)$')

    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged."""
        try:
            return DependNodeName._numPartReg.split(self)[0]
        except IndexError:
            return unicode(self)

    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised."""

        try:
            return DependNodeName._numPartReg.split(self)[1]
        except IndexError:
            raise ValueError, "No trailing numbers to extract on object %s" % self

    def nextUniqueName(self):
        """
        Increment the trailing number of the object until a unique name is found

        If there is no trailing number, appends '1' to the name.
        Will always return a different name than the current name, even if the
            current name already does not exist.
        """
        try:
            name = self.nextName()
        except ValueError:
            name = self.__class__(self + '1')
        while name.exists():
            name = name.nextName()
        return name

    def nextName(self):
        """Increment the trailing number of the object by 1"""

        groups = DependNodeName._numPartReg.split(self)
        if len(groups) > 1:
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'
            return self.__class__(formatStr % ( groups[0], (int(num) + 1) ))
        else:
            raise ValueError, "could not find trailing numbers to increment on object %s" % self

    def prevName(self):
        """Decrement the trailing number of the object by 1"""
        groups = DependNodeName._numPartReg.split(self)
        if len(groups) > 1:
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'
            return self.__class__(formatStr % ( groups[0], (int(num) - 1) ))
        else:
            raise ValueError, "could not find trailing numbers to decrement on object %s" % self

class DagNodeName(DependNodeName):

#    def __eq__(self, other):
#        """ensures that we compare longnames when checking for dag node equality"""
#        try:
#            return unicode(self.longName()) == unicode(DagNodeName(other).longName())
#        except (TypeError,IndexError):
#            return unicode(self) == unicode(other)
#
#    def __ne__(self, other):
#        """ensures that we compare longnames when checking for dag node equality"""
#        try:
#            return unicode(self.longName()) != unicode(DagNodeName(other).longName())
#        except (TypeError,IndexError):
#            return unicode(self) != unicode(other)

    #--------------------------
    #    DagNodeName Path Info
    #--------------------------
    def root(self):
        'rootOf'
        return DagNodeName( '|' + self.longName()[1:].split('|')[0] )

    def getRoot(self):
        """unlike the root command which determines the parent via string formatting, this
        command uses the listRelatives command"""

        par = None
        cur = self
        while 1:
            par = cur.getParent()
            if not par:
                break
            cur = par
        return cur

    def firstParent(self):
        'firstParentOf'

        return DagNodeName( '|'.join( self.split('|')[:-1] ) )

    def getParent(self, generations=1):
        """
        Returns the parent node

        Modifications:
            - added optional generations flag, which gives the number of levels up that you wish to go for the parent;
              ie:
                  >>> DagNodeName("NS1:TopLevel|Next|ns2:Third|Fourth").getParent(2)
                  DagNodeName('NS1:TopLevel|Next')

              Negative values will traverse from the top, not counting the initial node name:

                  >>> DagNodeName("NS1:TopLevel|Next|ns2:Third|Fourth").getParent(-3)
                  DagNodeName('NS1:TopLevel|Next|ns2:Third')

              A value of 0 will return the same node.
              The default value is 1.

              Since the original command returned None if there is no parent, to sync with this behavior, None will
              be returned if generations is out of bounds (no IndexError will be thrown).
        """

        if generations==0:
            return self

        split = self.split('|')
        if -len(split) <= generations < len(split):
            try:
                return DagNodeName('|'.join(split[:-generations]))
            except:
                pass


#    def shortName( self ):
#        'shortNameOf'
#        try:
#            return self.__class__( cmds.ls( self )[0] )
#        except:
#            return self

    def nodeName( self ):
        'basename'
        return self.split('|')[-1]



def _getParserClass(strObj):
    strObj = unicode(strObj)

    if '.' in strObj:
        newcls = AttributeName
            # Return Component Arrays ======================================================
            #            attr = obj.array().plugAttr()
            #            if attr in ["f","vtx","e","map"]:
            #                comps = getattr(Mesh(obj.node()), attr)
            #                return comps.__getitem__(obj.item(asSlice=1))
            #            else:
            #                return obj
            #===============================================================================


    elif '|' in strObj:
        newcls = DagNodeName
    else:
        newcls = DependNodeName
    return newcls


def find(node, searchOrder=("FN", "FNWN", "LN", "LNWN")):
    """
    Uses a 'best-match' algorithm to find a fully qualified node-name within the current scene.
    Based on code presented by Rob Tesdahl, CafeFX, at the 2008 Maya Developers Conference.
    
    Name Permutations
    
     -    Full name (FN)
     -    Full name without namespaces (FNWN)
     -    Leaf name (LN)
     -    Leaf name without namespaces (LNWN)
     -    *Parent DAG path (PP)
     -    *Parent DAG path without namespaces (PPWN)
     -    *Attribute name (AN)
     
     * Currently not implemented, but left for completeness
    """
    from general import PyNode, MayaNodeError
    
    data = parseMayaName(node)
    for t in searchOrder:
        try:
            return PyNode(data[t])
        except MayaNodeError:
            pass
        except KeyError:
            raise NotImplementedError(t)

def parseMayaName( fullPath ):
    """
    Parses a given node name into a dictionary of name permutations (see above)
    """
    fullPath = str(fullPath)
    nameTokens = fullPath.split( "|" )
    fullNameWithoutNamespaces = removeNamespaces( fullPath )
    
    #
    # leafName is the last token of the fullName, as split by '|'.
    # parentPath is the full name up to, but not including, the 
    # leafName and the preceding "|".
    #
    leafName = nameTokens[-1]
    parentPath = fullPath[:-len(leafName)-1]
    #
    # For paths that include underworld nodes, the parentPath
    # would end with the underworld separator "->".  This does not
    # need to be considered in the parsing of the full name.  It
    # just needs to be removed from the parsed elements.
    #
    if parentPath.endswith("->"):
        parentPath = parentPath[:-2]
    #
    # Remove namespaces in the leafName and parentPath.
    # But store the namespace for the leafName, if any.
    #
    leafNamespaces = leafName.split(":")
    leafNameWithoutNamespaces = leafNamespaces[-1]
    leafNamespace = ""
    if len( leafNamespaces ) > 1:
        leafNamespace = ":".join( leafNamespaces[:-1] )
    parentPathWithoutNamespaces = removeNamespaces( parentPath )

    # Pull off an attribute name, if one exists.
    attributeName = ""
    nodeAttributeTokens = leafName.split( "." )
    if len( nodeAttributeTokens ) > 1:
        attributeName = ".".join( nodeAttributeTokens[1:] ) 

    pathInfo = {
        'FN': fullPath, 
        'FNWN': fullNameWithoutNamespaces, 
        'LN': leafName, 
        'LNWN': leafNameWithoutNamespaces, 
        'PP': parentPath, 
        'PPWN': parentPathWithoutNamespaces, 
        'AN': attributeName, 
        'LNS': leafNamespace, 
        }
    return pathInfo

 
def removeNamespaces( path ):
    #
    # To remove the namespace from the path input string:
    # 1) Split on "->" to get all "underworld" parts, UW
    # 2) For each UW, U:
    # 3)     Split on "|" to get each part of the path, P
    # 4)     For each P, p:
    # 5)         Split on ":" and take the last one
    # 6)     Rejoin P's
    # 7) Rejoin UW's
    #
    pathPieces = []
    underWorldTokens = path.split( "->" )
    for uw in underWorldTokens:
        underWorldPieces = []
        pathTokens = uw.split( "|" )
        for p in pathTokens:
            namespaceTokens = p.split( ":" )
            thisPathPiece = namespaceTokens[-1]
            underWorldPieces.append( thisPathPiece )
        thisUnderWorldPiece = "|".join( underWorldPieces )
        pathPieces.append( thisUnderWorldPiece )
    pathWithoutNamespaces = "->".join( pathPieces )
    return pathWithoutNamespaces
