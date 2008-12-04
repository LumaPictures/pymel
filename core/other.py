import pmtypes.pmcmds as cmds
import re

import pmtypes.factories as _factories
_factories.createFunctions( __name__ )


class DependNodeName(unicode):

    def node(self):
        """for compatibility with AttributeName class"""
        return self
            
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super(unicode, self).__getattr__(attr)
            
        return AttributeName( '%s.%s' % (self, attr) )
        
        #raise AttributeNameError, 'AttributeName does not exist %s' % attr


    def objExists (self, **kwargs):
        "objExists"
        return cmds.objExists(self, **kwargs)
    exists = objExists 
           
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
        
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)


    def stripNamespace(self, levels=0):
        """
        Returns a new instance of the object with its namespace removed.  The calling instance is unaffected.
        The optional levels keyword specifies how many levels of cascading namespaces to strip, starting with the topmost (leftmost).
        The default is 0 which will remove all namespaces.
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
        return self.strip('|').split('|')[-1].split(':')[:-1]
            
    def namespace(self):
        """Returns the namespace of the object with trailing colon included"""
        return ':'.join(self.namespaceList()) + ':'
        
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
        given AttributeName."""
        return AttributeName( '%s.%s' % (self, attr) )
    
    
    
class AttributeName(DependNodeName):
    attrItemReg = re.compile( '\[(\d+:*\d*)\]$')
            
    def __init__(self, attrName):
        if '.' not in attrName:
            raise TypeError, "%s: AttributeNames must include the node and the AttributeName. e.g. 'nodeName.AttributeName' " % self
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
            'lambert1.groupNode'
        """
        try:
            return AttributeName(AttributeName.attrItemReg.split( self )[0])
        except:
            raise TypeError, "%s is not a multi AttributeName" % self
    
    def plugNode(self):
        'plugNode'
        return DependNodeName( str(self).split('.')[0])

    node = plugNode
    
    def plugAttr(self):
        """plugAttr
        
            >>> SCENE.persp.t.tx.plugAttr()
            't.tx'
        """
        return '.'.join(str(self).split('.')[1:])
    
    def lastPlugAttr(self):
        """
        
            >>> SCENE.persp.t.tx.lastPlugAttr()
            'tx'
        """
        return self.split('.')[-1]
        
    def nodeName( self ):
        'basename'
        return self.split('|')[-1]
    
    def item(self, asSlice=False, asString=False):
        try:
            item = AttributeName.attrItemReg.search(self).group(1)
            if asString:
                return "[%s]" % str(item)
            val = item.split(":")
            val = map(int,val)
            if len(val)>1:
                return asSlice and slice(*val) or val
            return val[0]
        except: return None    