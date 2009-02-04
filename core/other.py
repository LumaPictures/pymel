"""
Functions which are not listed in the maya documentation, such as commands created by plugins, 
as well as the name parsing classes `DependNodeName`, `DagNodeName`, and `AttributeName`.
"""

import pmcmds as cmds
import re

import factories as _factories
_factories.createFunctions( __name__ )


#--------------------------
# Object Wrapper Classes
#--------------------------

class NameParser(unicode):
    def __new__(cls, strObj):
        """Casts a string to a pymel class. Use this function if you are unsure which class is the right one to use
        for your object."""
    
        # the if statement was failing for some types (ex: pymel.node.Vertex), 
        # so forcing into unicode string:

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

        
    def getParent(self):
        """
        Returns the parent attribute
        """    
        if self.count('.') > 1:
            return AttributeName('.'.join(self.split('.')[:-1]))

    def addAttr( self, **kwargs):    
        kwargs['longName'] = self.plugAttr()
        kwargs.pop('ln', None )
        return addAttr( self.node(), **kwargs )
    
    def setAttr(self, *args, **kwargs):
        from pymel.core.general import setAttr
        return setAttr(self, *args, **kwargs)
        
    set = setAttr
    add = addAttr
    

class DependNodeName( NameParser ):
    #-------------------------------
    #    Name Info and Manipulation
    #-------------------------------

    def node(self):
        """for compatibility with AttributeName class"""
        return self
        
            
    def exists(self, **kwargs):
        "objExists"
        return cmds.objExists(**kwargs)

            
    _numPartReg = re.compile('([0-9]+)$')
    
    def stripNum(self):
        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
        the name will be returned unchanged."""
        try:
            return DependNodeName._numPartReg.split(self)[0]
        except:
            return unicode(self)
            
    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised."""
        
        try:
            return DependNodeName._numPartReg.split(self)[1]
        except:
            raise "No trailing numbers to extract on object ", self

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found"""
        name = self.shortName().nextName()
        while name.exists():
            name = name.nextName()
        return name
                
    def nextName(self):
        """Increment the trailing number of the object by 1"""
        try:
            groups = DependNodeName._numPartReg.split(self)
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return self.__class__(formatStr % ( groups[0], (int(num) + 1) ))
        except:
            raise "could not find trailing numbers to increment"
            
    def prevName(self):
        """Decrement the trailing number of the object by 1"""
        try:
            groups = DependNodeName._numPartReg.split(self)
            num = groups[1]
            formatStr = '%s%0' + unicode(len(num)) + 'd'            
            return self.__class__(formatStr % ( groups[0], (int(num) - 1) ))
        except:
            raise "could not find trailing numbers to decrement"

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
    
    def getParent(self):
        'firstParentOf'

        return DagNodeName( '|'.join( self.split('|')[:-1] ) )

        
            
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
    

 