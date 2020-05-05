from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from builtins import input
from builtins import range

from pymel.util.objectParser import *

__all__ = [  # 'NameParseError', 'ParsingWarning',
    #'ProxyUni', 'NameParsed',
    'NamePart', 'NameAlphaPart', 'NameNumPart', 'NameGroup',
    'NameAlphaGroup', 'NameNumGroup', 'NameSep', 'MayaName', 'NamespaceSep', 'Namespace',
    'MayaShortName', 'DagPathSep', 'MayaNodePath', 'AttrSep', 'NameIndex', 'NameRangeIndex',
    'Component', 'Attribute', 'AttributePath', 'NodeAttribute', 'MayaObjectName',
    'getBasicPartList', 'parse']

# Parsers deriver from the Parser base class
# for Maya names parsing

# NOTE : order of declaration is important as yacc only considers
# lineno of function declaration to order the rules
# TODO : modify Yacc to take mro of class then relative line no or use decorators ?

# no parsed class for this, the Parsers and NameParsed class for each token (e.g. t_Alpha and --> Alpha, AlphaParser) will be created automatically anyway


class NameBaseParser(Parser):

    """ Base for name parser with common tokens """
    t_Alpha = r'([a-z]+)|([A-Z]+[a-z]*)'
    t_Num = r'[0-9]+'

    start = None


class NameAlphaPartParser(NameBaseParser):

    """ Parser for a name part starting with a letter """
    start = 'NameAlphaPart'

    def p_apart(self, p):
        '''NameAlphaPart : Alpha'''
        p[0] = NameAlphaPart(Token(p[1], type='Alpha', pos=p.lexpos(1)))


class NameNumPartParser(NameBaseParser):

    """ Parser for a name part starting with a number """
    start = 'NameNumPart'

    def p_npart(self, p):
        '''NameNumPart : Num'''
        p[0] = NameNumPart(Token(p[1], type='Num', pos=p.lexpos(1)))


class NamePartParser(NameAlphaPartParser, NameNumPartParser):

    """ Parser for a name part of either the NameAlphaPart or NameNumPart kind """
    start = 'NamePart'

    def p_part(self, p):
        '''NamePart : NameAlphaPart
                    | NameNumPart'''
        p[0] = NamePart(p[1])


class NameAlphaGroupParser(NameAlphaPartParser, NameNumPartParser):

    """
        A Parser for suitable groups for a name head : one or more name parts, the first part starting with a letter
        NameAlphaGroup = NameAlphaPart NamePart *
    """
    start = 'NameAlphaGroup'

    def p_agroup_concat(self, p):
        ''' NameAlphaGroup : NameAlphaGroup NameAlphaPart
                                |  NameAlphaGroup NameNumPart '''
        p[0] = p[1] + p[2]

    def p_agroup(self, p):
        ''' NameAlphaGroup : NameAlphaPart '''
        p[0] = NameAlphaGroup(p[1])


class NameNumGroupParser(NameAlphaPartParser, NameNumPartParser):

    """
        A Parser for suitable groups for a name body : one or more name parts, the first part starting with a number
        NameNumGroup = NameNumPart NamePart *
    """
    start = 'NameNumGroup'

    def p_ngroup_concat(self, p):
        ''' NameNumGroup : NameNumGroup NameAlphaPart
                                | NameNumGroup NameNumPart '''
        p[0] = p[1] + p[2]

    def p_ngroup(self, p):
        ''' NameNumGroup : NameNumPart '''
        p[0] = NameNumGroup(p[1])


class NameGroupParser(NameAlphaGroupParser, NameNumGroupParser):

    """
        A Parser for a name group of either the NameAlphaGroup or NameNumGroup kind
    """
    start = 'NameGroup'

    def p_group(self, p):
        ''' NameGroup : NameAlphaGroup
                        | NameNumGroup '''
        p[0] = NameGroup(p[1])


class NameSepParser(Parser):

    """ A Parser for the MayaName NameGroup separator : one or more underscores """
    t_Underscore = r'_+'

    start = 'NameSep'

    def p_sep_concat(self, p):
        ''' NameSep : NameSep Underscore '''
        p[0] = p[1] + Token(p[1], type='Underscore', pos=p.lexpos(1))

    def p_sep(self, p):
        ''' NameSep : Underscore '''
        p[0] = NameSep(Token(p[1], type='Underscore', pos=p.lexpos(1)))

    # always lower precedence than parts we herit the parser from
    # TODO : gather precedence from base classes
    precedence = (('left', 'Underscore'),
                  ('right', ('Alpha', 'Num')),
                  )


class MayaNameParser(NameSepParser, NameGroupParser):

    """
        A Parser for the most basic Maya Name : several name groups separated by one or more underscores,
        starting with an alphabetic part or one or more underscore, followed by zero or more NameGroup(s)
        separated by underscores
    """

    start = 'MayaName'

    def p_name_error(self, p):
        'MayaName : error'
        print("Syntax error in MayaName. Bad expression")

    # a atomic Maya name is in the form (_)*head(_group)*(_)*
    def p_name_concat(self, p):
        ''' MayaName : MayaName NameSep NameGroup
                        | MayaName NameSep '''
        if len(p) == 4:
            p[0] = (p[1] + p[2]) + p[3]
        else:
            p[0] = p[1] + p[2]

    def p_name(self, p):
        ''' MayaName : NameSep NameGroup
                    | NameAlphaGroup '''
        if len(p) == 3:
            p[0] = MayaName(p[1], p[2])
        else:
            p[0] = MayaName(p[1])


class NamespaceSepParser(Parser):

    """ A Parser for the Namespace separator """
    t_Colon = r':'

    start = 'NamespaceSep'

    def p_nspace_sep(self, p):
        ''' NamespaceSep : Colon '''
        p[0] = NamespaceSep(Token(p[1], type='Colon', pos=p.lexpos(1)))

    precedence = (('left', 'Colon'),
                  ('left', 'Underscore'),
                  ('right', 'Alpha', 'Num'),
                  )


class NamespaceParser(NamespaceSepParser, MayaNameParser, EmptyParser):

    """ A Parser for Namespace, Maya namespaces names """

    start = 'Namespace'

    def p_nspace_concat(self, p):
        ''' Namespace : Namespace MayaName NamespaceSep '''
        p[0] = p[1] + Namespace(p[2], p[3])

    def p_nspace(self, p):
        ''' Namespace : MayaName NamespaceSep
                    | NamespaceSep
                    | Empty '''
        if len(p) == 3:
            p[0] = Namespace(p[1], p[2])
        else:
            p[0] = Namespace(p[1])


class MayaShortNameParser(NamespaceParser, MayaNameParser):

    """ A parser for MayaShortName, a short object name (without preceding path) with a possible preceding namespace """

    start = 'MayaShortName'

    def p_sname(self, p):
        ''' MayaShortName : Namespace MayaName
                            | MayaName '''
        if len(p) == 3:
            p[0] = MayaShortName(p[1], p[2])
        else:
            p[0] = MayaShortName(Namespace(pos=p.lexpos(1)), p[1])


class DagPathSepParser(Parser):

    """ A Parser for the DagPathSep separator """
    t_Pipe = r'\|'

    start = 'DagPathSep'

    def p_dpath_sep(self, p):
        ''' DagPathSep : Pipe '''
        p[0] = DagPathSep(Token(p[1], type='Pipe', pos=p.lexpos(1)))

    precedence = (('left', 'Pipe'),
                  ('left', 'Colon'),
                  ('left', 'Underscore'),
                  ('left', 'Alpha', 'Num'),
                  )


class MayaNodePathParser(DagPathSepParser, MayaShortNameParser):

    """ a Parser for Maya node name, an optional leading DagPathSep followed by one or more
        MayaShortName separated by DagPathSep """

    start = 'MayaNodePath'

    def p_node_concat(self, p):
        ''' MayaNodePath : MayaNodePath DagPathSep MayaShortName '''
        p[0] = p[1] + MayaNodePath(p[2], p[3])

    def p_node(self, p):
        ''' MayaNodePath : DagPathSep MayaShortName
                                | MayaShortName '''
        if len(p) == 3:
            p[0] = MayaNodePath(p[1], p[2])
        else:
            p[0] = MayaNodePath(p[1])


class AttrSepParser(Parser):

    """ A Parser for the MayaAttributePath separator """
    t_Dot = r'\.'

    start = 'AttrSep'

    def p_attr_sep(self, p):
        ''' AttrSep : Dot '''
        p[0] = AttrSep(Token(p[1], type='Dot', pos=p.lexpos(1)))

    precedence = (('left', 'Dot'),
                  ('left', 'Pipe'),
                  ('left', 'Colon'),
                  ('left', 'Underscore'),
                  ('left', 'Alpha', 'Num'),
                  )


class NameIndexParser(Parser):

    """ A Parser for attribute or component name indexes, in the form [<int number>] """
    t_Index = r'\[(?:[0-9]+|-1)\]'

    start = 'NameIndex'

    def p_index(self, p):
        ''' NameIndex : Index '''
        p[0] = NameIndex(Token(p[1], type='Index', pos=p.lexpos(1)))

    precedence = (('left', 'Index'),
                  ('left', 'Dot'),
                  ('left', 'Pipe'),
                  ('left', 'Colon'),
                  ('left', 'Underscore'),
                  ('left', 'Alpha', 'Num'),
                  )


class NameRangeIndexParser(Parser):

    r""" A Parser for an index specification for an attribute or a component index,
        in the form [<optional int number>:<optional int number>]
        Rule : NameIndex = r'\[[0-9]*:[0-9]*\]' """
    t_RangeIndex = r'\[[0-9]*:[0-9]*\]'

    start = 'NameRangeIndex'

    def p_rindex(self, p):
        ''' NameRangeIndex : RangeIndex '''
        p[0] = NameIndex(Token(p[1], type='RangeIndex', pos=p.lexpos(1)))

    precedence = (('left', 'RangeIndex'),
                  ('left', 'Index'),
                  ('left', 'Dot'),
                  ('left', 'Pipe'),
                  ('left', 'Colon'),
                  ('left', 'Underscore'),
                  ('left', 'Alpha', 'Num'),
                  )


class SingleComponentNameParser(NameRangeIndexParser, NameIndexParser, MayaNameParser):

    r""" A NameParsed for the reserved single indexed components names:
        vtx,
        Rule : NameIndex = r'\[[0-9]*:[0-9]*\]' """


class DoubleComponentNameParser(NameRangeIndexParser, NameIndexParser, MayaNameParser):
    pass


class TripleComponentNameParser(NameRangeIndexParser, NameIndexParser, MayaNameParser):
    pass


class ComponentNameParser(SingleComponentNameParser, DoubleComponentNameParser, TripleComponentNameParser):
    pass

# NOTE : call these attributes and the couple(node.attribute) a plug like in API ?


class NodeAttributeNameParser(NameIndexParser, MayaNameParser):

    """ Parser for a Attribute, the name of a Maya attribute on a Maya node, a MayaName with an optional NameIndex """

    start = 'Attribute'

    def p_nodeattr_error(self, p):
        'Attribute : error'
        print("Invalid node attribute name")

    def p_nodeattr(self, p):
        ''' Attribute : MayaName NameIndex
                                    | MayaName '''
        if len(p) == 3:
            p[0] = Attribute(p[1], p[2])
        else:
            p[0] = Attribute(p[1])


class NodeAttributePathParser(AttrSepParser, NodeAttributeNameParser):

    """ Parser for a full path of a Maya attribute on a Maya node, as one or more AttrSep ('.') separated Attribute """

    start = 'AttributePath'

    def p_nodeattrpath_concat(self, p):
        ''' AttributePath : AttributePath AttrSep Attribute '''
        p[0] = AttributePath(p[1], p[2], p[3])

    def p_nodeattrpath(self, p):
        ''' AttributePath : Attribute '''
        p[0] = AttributePath(p[1])


class AttributeNameParser(NodeAttributePathParser, MayaNodePathParser):

    """ Parser for the name of a Maya attribute, a MayaNodePath followed by a AttrSep and a AttributePath """

    start = 'NodeAttribute'

    def p_attribute(self, p):
        ''' NodeAttribute : MayaNodePath AttrSep AttributePath'''
        p[0] = NodeAttribute(p[1], p[2], p[3])

# ComponentNameParser


class MayaObjectNameParser(AttributeNameParser):

    """ A Parser for an unspecified object name in Maya, can be a dag object name, a node name,
        an plug name, or a component name. """

    start = 'MayaObjectName'

    def p_mobject(self, p):
        ''' MayaObjectName : MayaNodePath
                            | NodeAttribute '''
        p[0] = MayaObjectName(p[1])


class NameParsed(Parsed):

    def isNodeName(self):
        """ True if this dag path name is absolute (starts with '|') """
        return type(self) == MayaNodePath

    def isAttributeName(self):
        """ True if this object is specified including one or more dag parents """
        return type(self) == NodeAttribute

    def isComponentName(self):
        """ True if this object is specified as an absolute dag path (starting with '|') """
        return type(self) == Component

# NameParsed objects for Maya Names
# TODO : build _accepts from yacc rules directly

# Atomic Name element, an alphabetic or numeric word


class NamePart(NameParsed):

    """
    A name part of either the NameAlphaPart or NameNumPart kind

        Rule : NamePart = `NameAlphaPart` | `NameNumPart`

        Composed Of: `NameAlphaPart`, `NameNumPart`

        Component Of: `NameNumGroup`
    """
    _parser = NamePartParser
    _accepts = ('Alpha', 'Num')

    def isAlpha(self):
        return isinstance(self.sub[0], Alpha)

    def isNum(self):
        return isinstance(self.sub[0], Num)


class NameAlphaPart(NamePart):

    """
    A name part made of alphabetic letters

        Rule : NameAlphaPart = r'([a-z]+)|([A-Z]+[a-z]*)'

        Component Of: `NameNumGroup`, `NameAlphaGroup`
    """
    _parser = NameAlphaPartParser
    _accepts = ('Alpha', )

    def isAlpha(self):
        return True

    def isNum(self):
        return False


class NameNumPart(NamePart):

    """
    A name part made of numbers

        Rule : NameNumPart = r'[0-9]+'

    """
    _parser = NameNumPartParser
    _accepts = ('Num', )

    # to allow initialization from a single int
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], int):
            nargs = [Token(u"%s" % args[0], type='Num', pos=0)]
        else:
            nargs = list(args)
        return super(NameNumPart, cls).__new__(cls, *nargs, **kwargs)

    @ property
    def value(self):
        return int(str(self))

    def isAlpha(self):
        return False

    def isNum(self):
        return True

# A Name group, all the consecutive parts between two underscores


class NameGroup(NameParsed):

    """
    A name group of either the NameAlphaGroup or NameNumGroup kind

        Rule : NameGroup = `NameAlphaGroup` | `NameNumGroup`

        Composed Of: `NameAlphaGroup`, `NameNumGroup`

        Component Of: `MayaName`
    """
    _parser = NameGroupParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NamePart')

    def isNum(self):
        return self.parts[0].isNum()

    def isAlpha(self):
        return self.parts[0].isAlpha()

    @property
    def parts(self):
        """ All parts of that name group """
        return self.sub

    @property
    def first(self):
        """ First part of that name group """
        return self.parts[0]

    @property
    def last(self):
        """ Last part of that name group """
        return self.parts[-1]

    @property
    def tail(self):
        """ The tail (trailing numbers if any) of that name group """
        if self.last.isNum():
            return (self.last)

    def nextName(self):
        tail = self.tail
        if tail is not None:
            padding = str(len(self.tail))
            formatStr = '%0' + padding + 'd'
            newval = formatStr % (tail.value + 1)
            self.setSubItem(-1, newval)

    def prevName(self):
        tail = self.tail
        if tail is not None:
            padding = str(len(self.tail))
            formatStr = '%0' + padding + 'd'
            newval = formatStr % (tail.value - 1)
            self.setSubItem(-1, newval)


class NameAlphaGroup(NameGroup):

    """
    A name group starting with an alphabetic part

        Rule : NameAlphaGroup  = `NameAlphaPart` `NamePart` *

        Composed Of: `NameAlphaPart`, `NamePart`

        Component Of: `NameNumGroup`
    """
    _parser = NameAlphaGroupParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NamePart')

    def isNum(self):
        return False

    def isAlpha(self):
        return True


class NameNumGroup(NameGroup):

    """
    A name group starting with an alphabetic part

        Rule : NameAlphaGroup  = `NameAlphaPart` `NamePart` *

        Composed Of: `NameAlphaPart`, `NamePart`

        Component Of: `MayaName`
    """
    _parser = NameNumGroupParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NamePart')

    def isNum(self):
        return True

    def isAlpha(self):
        return False

# separator for name groups


class NameSep(NameParsed):

    """
    the MayaName NameGroup separator : one or more underscores

        Rule : NameSep = r'_+'

        Component Of: `MayaName`
    """
    _parser = NameSepParser
    _accepts = ('Underscore',)

    @classmethod
    def default(cls):
        return Token('_', type='Underscore', pos=0)

    def reduced(self):
        """ Reduce multiple underscores to one """
        return NameSep()

# a short Maya name without namespaces or attributes


class MayaName(NameParsed):

    """
    The most basic Maya Name : several name groups separated by one or more underscores,
    starting with a NameHead or one or more underscore, followed by zero or more NameGroup

        Rule : MayaName = (`NameSep` * `NameAlphaGroup`) | (`NameSep` + `NameNumGroup`)  ( `NameSep` `NameGroup` ) * `NameSep` *

        Composed Of: `NameSep`, `NameAlphaGroup`, `NameNumGroup`, `NameGroup`

        Component Of: `Namespace`, `MayaShortName`, `Attribute`
    """

    _parser = MayaNameParser
    _accepts = ('NameAlphaGroup', 'NameNumGroup', 'NameGroup', 'NameSep')

    @property
    def parts(self):
        """ All groups of that name, including separators """
        return self.sub

    @property
    def groups(self):
        """ All groups of that Maya name, skipping separators """
        result = []
        for s in self.parts:
            if not isinstance(s, NameSep):
                result.append(s)
        return tuple(result)

    @property
    def first(self):
        """ First group of that Maya name """
        if self.groups:
            return self.groups[0]

    @property
    def last(self):
        """ Last group of that Maya name """
        if self.groups:
            return self.groups[-1]

    @property
    def tail(self):
        """ The tail (trailing numbers if any) of that Maya Name """
        if self.groups:
            return self.groups[-1].tail

    def reduced(self):
        """ Reduces all separators in thet Maya Name to one underscore, eliminates head and tail separators if not needed """
        groups = self.groups
        result = []
        if groups:
            if groups[0].isNum():
                result.append(NameSep())
            result.append(groups[0])
            for g in groups[1:]:
                result.append(NameSep())
                result.append(g)
            return self.__class__(*result)
        else:
            return self

#    def stripNum(self):
#        """Return the name of the node with trailing numbers stripped off. If no trailing numbers are found
#        the name will be returned unchanged."""
#        try:
#            return DependNode._numPartReg.split(self)[0]
#        except:
#            return unicode(self)

    def extractNum(self):
        """Return the trailing numbers of the node name. If no trailing numbers are found
        an error will be raised."""

        return self.tail

    def nextUniqueName(self):
        """Increment the trailing number of the object until a unique name is found"""
        name = self.shortName().nextName()
        while name.exists():
            name = name.nextName()
        return name

    def nextName(self):
        """Increment the trailing number of the object by 1"""
        try:
            self.last.nextName()
        except AttributeError:
            raise Exception("could not find trailing numbers to increment")

    def prevName(self):
        """Decrement the trailing number of the object by 1"""
        try:
            self.last.prevName()
        except AttributeError:
            raise Exception("could not find trailing numbers to decrement")


class NamespaceSep(NameParsed):

    """
    The Maya Namespace separator : the colon ':'

        Rule : NamespaceSep = r':'

        Component Of: `Namespace`
    """
    _parser = NamespaceSepParser
    _accepts = ('Colon',)

    @classmethod
    def default(cls):
        return Token(':', type='Colon', pos=0)


class Namespace(NameParsed):

    """
    A Maya namespace name, one or more MayaName separated by ':'

        Rule : Namespace = `NamespaceSep` ? (`MayaName` `NamespaceSep`) +

        Composed Of: `NamespaceSep`, `MayaName`

        Component Of: `MayaShortName`
    """
    _parser = NamespaceParser
    _accepts = ('NamespaceSep', 'MayaName', 'Empty')

    @classmethod
    def default(cls):
        return Empty()

    @property
    def parts(self):
        """ All parts of that namespace, including separators """
        return self.sub

    @property
    def spaces(self):
        """ All different individual namespaces in that Maya namespace, skipping separators """
        result = []
        for s in self.parts:
            if not isinstance(s, NamespaceSep):
                result.append(s)
        return tuple(result)

    def setSpace(self, index, space):
        """Set the namespace at the given index"""
        count = 0
        for i, s in enumerate(self.sub):
            if not isinstance(s, NamespaceSep):
                if count == index:
                    self.setSubItem(i, space)
                    return
                count += 1
        raise IndexError("This node has %s namespaces. The given index %s is out of range" % (len(self.spaces), index))

    def pop(self, index=0):
        """Remove an individual namespace (no separator). An index of 0 (default) is the shallowest (leftmost) in the list"""
        index * 2
        sub = list(self.sub)
        # remove both MayaName and NamespaceSep
        res1 = str(sub.pop(index))
        res2 = sub.pop(index)
        self._sub = tuple(sub)
        if index < 0:
            return res2
        return res1

    def append(self, namespace):
        """Append a namespace. Can include separator and multiple namespaces. The new namespace will be the shallowest (leftmost) namespace."""
        if not namespace.endswith(':'):
            namespace += ':'
        newparts = list(Namespace(namespace).parts)
        sub = list(self.sub)
        self._sub = tuple(newparts + sub)

    @property
    def separator(self):
        return NamespaceSep()

    @property
    def path(self):
        """ All nested namespaces in that Maya namespace """
        if self.isAbsolute():
            result = [self.__class__(self.separator, self.first)]
        else:
            result = [self.__class__(self.first)]
        for s in self.spaces[1:]:
            result.append(result[-1] + self.separator + s)
        return tuple(result)

    @property
    def space(self):
        """ Last namespace of the individual namespaces """
        return self.spaces[-1]

    @property
    def parents(self):
        """ All the nested namespaces names (full) in the namespace but the last, starting from last up """
        if len(self.path) > 1:
            return tuple(reversed(self.path[:-1]))
        else:
            return ()

    @property
    def parent(self):
        """ All the individual namespaces in the namespace but the last, starting from last up, without separators """
        if self.parents:
            return self.parents[0]

    @property
    def first(self):
        """ First individual namespace of that namespace """
        try:
            return self.spaces[0]
        except:
            pass

    @property
    def last(self):
        """ Last individual namespace in that namespace """
        try:
            return self.spaces[-1]
        except:
            pass

    def isAbsolute(self):
        """ True if this namespace is an absolute namespace path (starts with ':') """
        if self.parts:
            return isinstance(self.parts[0], NamespaceSep)
        else:
            return False


class MayaShortName(NameParsed):

    """
    A short node name in Maya, a Maya name, possibly preceded by a Namespace

        Rule : MayaShortName = `Namespace` ? `MayaName`

        Composed Of: `Namespace`, `MayaName`

        Component Of: `MayaNodePath`
    """
    _parser = MayaShortNameParser
    _accepts = ('Namespace', 'MayaName')

    @property
    def parts(self):
        """ All parts of that namespace, including separators """
        return self.sub

    def getBaseName(self):
        "Get the short node name of the object"
        return self.sub[-1]

    def setBaseName(self, name):
        """Set the name of the object.  Should not include namespace"""
        return self.setSubItem(-1, name)
    basename = property( getBaseName, setBaseName, doc=""" The short node name without any namespace of the Maya short object name """ )

    def addPrefix(self, prefix):
        """Add a prefix to the node name. This must produce a valid maya name (no separators allowed)."""
        self.setBaseName(prefix + str(self.getBaseName()))

    def addSuffix(self, suffix):
        """Add a suffix to the node name. This must produce a valid maya name (no separators allowed)."""
        self.setBaseName(str(self.getBaseName()) + suffix)

    def getBaseNamespace(self):
        "Get the namespace for the current node"
        # if isinstance(self.parts[0], Namespace) :
        #    return self.parts[0]
        return self.sub[0]

    def setNamespace(self, namespace):
        "Set the namespace. The provided namespace may be nested and should including a trailing colon unless it is empty."""
        self.setSubItem(0, namespace)
    namespace = property( getBaseNamespace, setNamespace, doc=""" The namespace name (full) of the Maya short object name """ )

    def isAbsoluteNamespace(self):
        """ True if this object is specified in an absolute namespace """
        if self.namespace:
            return self.namespace.isAbsolute()
        else:
            return False
#    @property
#    def groups(self):
#        """ All parts of that name group, skipping separators """
#        result = []
#        for s in self.parts :
#            if not isinstance(s, NameSep) :
#                result.append(s)
#        return tuple(result)
#    @property
#    def parts(self):
#        """ All parts of that maya short name, that is a possible namespace and node name """
#        return self.sub

    @property
    def first(self):
        """ All parts of that name group """
        return self.parts[0]

    @property
    def last(self):
        """ All parts of that name group """
        return self.parts[-1]


class DagPathSep(NameParsed):

    r"""
    The Maya long names separator : the pipe '|'

        Rule : DagPathSep = r'\|'

        Component Of: `MayaNodePath`
    """
    _parser = DagPathSepParser
    _accepts = ('Pipe',)

    @classmethod
    def default(cls):
        return Token('|', type='Pipe', pos=0)


class MayaNodePath(NameParsed):

    """
    A node name in Maya, one or more MayaShortName separated by DagPathSep, with an optional leading DagPathSep

        Rule : MayaNodePath = `DagPathSep` ? `MayaShortName` (`DagPathSep` `MayaShortName`) *

        Composed Of: `DagPathSep`, `MayaShortName`

        Component Of: `Component`, `NodeAttribute`

    Example
        >>> import pymel.util.nameparse as nameparse
        >>> obj = nameparse.parse( 'group1|pCube1|pCubeShape1' )
        >>> obj.setNamespace( 'foo:' )
        >>> print(obj)
        foo:group1|foo:pCube1|foo:pCubeShape1
        >>> print(obj.parent)
        foo:group1|foo:pCube1
        >>> print(obj.node)
        foo:pCubeShape1
        >>> print(obj.node.basename)
        pCubeShape1
        >>> print(obj.node.namespace)
        foo:

    """

#    class _parser(DagPathSepParser, MayaShortNameParser):
#        """ a Parser for Maya node name, an optional leading DagPathSep followed by one or more
#            MayaShortName separated by DagPathSep """
#
#        start = 'MayaNodePath'
#
#        def p_node_concat(self, p) :
#            ''' MayaNodePath : MayaNodePath DagPathSep MayaShortName '''
#            p[0] = p[1] + MayaNodePath(p[2], p[3])
#        def p_node(self, p) :
#            ''' MayaNodePath : DagPathSep MayaShortName
#                                    | MayaShortName '''
#            if len(p) == 3 :
#                p[0] = MayaNodePath(p[1], p[2])
#            else :
#                p[0] = MayaNodePath(p[1])

    _parser = MayaNodePathParser
    _accepts = ('DagPathSep', 'MayaShortName')

    @property
    def parts(self):
        """ All parts of that node name, including separators """
        return self.sub

    @property
    def nodes(self):
        """ All the short names in the dag path including the last, without separators """
        result = []
        for p in self.parts:
            if not isinstance(p, DagPathSep):
                result.append(p)
        return tuple(result)

    def shortName(self):
        """ The last short name of the path """
        return self.nodes[-1]
    node = property(shortName)

    @property
    def separator(self):
        return DagPathSep()

    @property
    def nodePaths(self):
        """ All the long names in the dag path including the last"""
        if self.isAbsolute():
            result = [self.__class__(self.separator, self.first)]
        else:
            result = [self.__class__(self.first)]
        for s in self.nodes[1:]:
            result.append(result[-1] + self.separator + s)
        return tuple(result)

    @property
    def parents(self):
        """ All the dags in the dag hierarchy above the last node, starting from last up """
        if len(self.nodes) > 1:
            return tuple(reversed(self.nodePaths[:-1]))
        else:
            return ()

    @property
    def parent(self):
        """ Parent of the last node in the dag hierarchy """
        if self.parents:
            return self.parents[0]

    @property
    def first(self):
        """ First node name of that dag path name (root of the path) """
        return self.nodes[0]

    @property
    def root(self):
        """ First node name of that dag path name (root of the path) """
        return self.nodes[0]

    @property
    def last(self):
        """ Last node name of that dag path name (leaf of the path, equivalent to self.node) """
        return self.nodes[-1]

    def addPrefix(self, prefix):
        """Add a prefix to all nodes in the path. This must produce a valid maya name (no separators allowed)."""
        for node in self.nodes:
            node.setBaseName(prefix + str(node.getBaseName()))

    def addSuffix(self, suffix):
        """Add a suffix to all nodes in the path. This must produce a valid maya name (no separators allowed)."""
        for node in self.nodes:
            node.setBaseName(str(node.getBaseName()) + suffix)

    def setNamespace(self, namespace):
        "Set the namespace for all nodes in this path. The provided namespace may be nested and should including a trailing colon unless it is empty."""
        for node in self.nodes:
            node.setNamespace(namespace)

    def addNamespace(self, namespace):
        "Append the namespace for all nodes in this path."""
        for node in self.nodes:
            node.namespace.append(namespace)

    def popNamespace(self, index=0):
        """Remove an individual namespace (no separator) from all nodes in this path. An index of 0 (default) is the shallowest (leftmost) in the list.
        Returns a tuple containing the namespace popped from each node in the path or None if the node had no namespaces."""
        result = []
        for node in self.nodes:
            try:
                result.append(node.namespace.pop(index))
            except IndexError:
                result.append(None)
        return tuple(result)

    def popNode(self, index=-1):
        """Remove a node from the end of the path"""
        result = []
        parts = list(self.sub)
        index *= 2
        if index < 0 or isinstance(parts[0], DagPathSep):
            index += 1

        if len(parts) <= 2:
            raise ValueError("No more objects left to remove")
        result1 = parts.pop(index)
        result2 = parts.pop(index)
        self._sub = tuple(parts)
        return result1

    def addNode(self, node):
        """Add a node to the end of the path"""
        parts = list(self.sub)
        parts.extend([DagPathSep(), MayaShortName(node)])
        self._sub = tuple(parts)

    def isShortName(self):
        """ True if this object node is specified as a short name (without a path) """
        return len(self.nodes) == 1

    def isDagName(self):
        """ True if this object is specified including one or more dag parents """
        return len(self.nodes) > 1

    def isLongName(self):
        """ True if this object is specified as an absolute dag path (starting with '|') """
        return isinstance(self.parts[0], DagPathSep)
    isAbsolute = isLongName


class AttrSep(NameParsed):

    r"""
    The Maya attribute separator : the dot '.'

        Rule : AttrSep = r'\.'

        Component Of: `Component`, `AttributePath`, `NodeAttribute`
    """
    _parser = DagPathSepParser
    _accepts = ('Dot',)

    @classmethod
    def default(cls):
        return Token('.', type='Dot', pos=0)


class NameIndex(NameParsed):

    r"""
    An index specification for an attribute or a component index, in the form [<int number>]

        Rule : NameIndex = r'\[[0-9]+\]'

        Component Of: `Attribute`
    """
    _parser = NameIndexParser
    _accepts = ('Index',)

    # to allow initialization from a single int
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], int):
            nargs = [Token(u"[%s]" % args[0], type='Index', pos=0)]
        else:
            nargs = list(args)
        return super(NameIndex, cls).__new__(cls, *nargs, **kwargs)

    @property
    def value(self):
        """ Index of that node attribute name """
        return int(self.strip("[]"))


class NameRangeIndex(NameParsed):

    r"""
    An index specification for an attribute or a component index, in the form::
        [<optional int number>:<optional int number>]

        Rule : NameIndex = r'\[[0-9]*:[0-9]*\]'


    """
    _parser = NameRangeIndexParser
    _accepts = ('RangeIndex',)

    @classmethod
    def default(cls):
        return Token(u"[:]", type='RangeIndex', pos=0)
    # to allow initialization from one or two int

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], int):
            nargs = [Token(u"[%s:]" % args[0], type='RangeIndex', pos=0)]
        elif len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
            nargs[Token(u"[%s:%s]" % (args[0], args[1]), type='RangeIndex', pos=0)]
        else:
            nargs = list(args)
        return super(NameIndex, cls).__new__(cls, *nargs, **kwargs)

    @property
    def start(self):
        """ start of that component index range """
        return self.bounds[0]

    @property
    def end(self):
        """ end (inclusive) of that component index range """
        return self.bounds[1]

    @property
    def bounds(self):
        """ start and end bounds (inclusive) of that component index range """
        s = self.strip("[]").split(":")
        r = [None, None]
        if s[0]:
            r[0] = int(s[0])
        if s[1]:
            r[1] = int(s[1])
        return tuple(r)

    @property
    def range(self):
        """ Python styled range (start and exclusive end) of that component index range """
        s = self.strip("[]").split(":")
        r = [None, None]
        if s[0]:
            r[0] = int(s[0])
        if s[1]:
            r[1] = int(s[1]) + 1
        return tuple(r)

# components

# class NodeComponentName(NameParsed):
#    """ A Maya component name of any of the single, double or triple indexed kind """
#    _parser = NodeComponentNameParser
#    _accepts = ('MayaName', 'NameIndex', 'NameRangeIndex')
#
# class NodeSingleComponentName(Component):
#    _parser = NodeSingleComponentNameParser
#    _accepts = ('MayaName', 'NameIndex', 'NameRangeIndex')
#
# class NodeDoubleComponentName(Component):
#    _parser = NodeDoubleComponentNameParser
#    _accepts = ('MayaName', 'NameIndex', 'NameRangeIndex')
#
# class NodeTripleComponentName(Component):
#    _parser = NodeTripleComponentNameParser
#    _accepts = ('MayaName', 'NameIndex', 'NameRangeIndex')
#
#


class Component(NameParsed):

    """
    A Maya component name of any of the single, double or triple indexed kind

        Rule : Component = SingleComponentName | DoubleComponentName | TripleComponentName

        Component Of: `MayaObjectName`
    """
    _parser = ComponentNameParser
    _accepts = ('MayaNodePath', 'AttrSep', 'NodeComponentName')
#
# class SingleComponentName(Component):
#    """ A Maya single component name, in the form node name . component
#        Rule : SingleComponentName = MayaNodePath AttrSep NodeSingleComponentName """
#    _parser = SingleComponentNameParser
#    _accepts = ('MayaNodePath', 'AttrSep', 'NodeSingleComponentName')
#
# class DoubleComponentName(Component):
#    """ A Maya double component name, in the form node name . component
#        Rule : DoubleComponentName = MayaNodePath AttrSep NodeDoubleComponentName """
#    _parser = DoubleComponentNameParser
#    _accepts = ('MayaNodePath', 'AttrSep', 'NodeDoubleComponentName')
#
# class TripleComponentName(Component):
#    """ A Maya triple component name, in the form node name . component
#        Rule : TripleComponentName = MayaNodePath AttrSep NodeTripleComponentName """
#    _parser = TripleComponentNameParser
#    _accepts = ('MayaNodePath', 'AttrSep', 'NodeTripleComponentName')

# Decided to avoid the API denomination where attributes exist on nodes and a specific node+attribute association
# is called a plug as most scripting people are used to calling both attributes ?


class Attribute(NameParsed):

    """
    The name of a Maya attribute on a Maya node, a MayaName with an optional NameIndex

        Rule : Attribute = `MayaName` `NameIndex` ?

        Composed Of: `MayaName`, `NameIndex`

        Component Of: `AttributePath`
    """
    _parser = NodeAttributeNameParser
    _accepts = ('MayaName', 'NameIndex')

    @property
    def parts(self):
        """ All groups of that name, including separators """
        return self.sub

    @property
    def name(self):
        """ name(without index) of that node attribute name """
        return self.parts[0]

    @property
    def bracketedIndex(self):
        """ Index of that node attribute name """
        if len(self.parts) > 1:
            return self.parts[-1]

    @property
    def index(self):
        """ Int value of the index of that node attribute name """
        if self.bracketedIndex:
            return self.bracketedIndex.value

    def isCompound(self):
        return False


class AttributePath(NameParsed):

    """
    The full path of a Maya attribute on a Maya node, as one or more AttrSep ('.') separated Attribute

        Rule : AttributePath = ( `Attribute` `AttrSep` ) * `Attribute`

        Composed Of: `Attribute`, `AttrSep`

        Component Of: `NodeAttribute`
    """

    _parser = NodeAttributePathParser
    _accepts = ('AttrSep', 'Attribute')

    @property
    def parts(self):
        """ All parts of that node attribute path name, including separators """
        return self.sub

    @property
    def attributes(self):
        """ All the node attribute names in that node attribute path, including the last, without separators """
        result = []
        for p in self.parts:
            if not isinstance(p, AttrSep):
                result.append(p)
        return tuple(result)

    @property
    def separator(self):
        return AttrSep()

    @property
    def path(self):
        """ All nested namespaces in that Maya namespace """
        result = [self.__class__(self.separator, self.first)]
        for s in self.attributes[1:]:
            result.append(result[-1] + self.separator + s)
        return tuple(result)

    @property
    def parents(self):
        """ All the node attributes names (full) in the attribute path above the last node attribute name, starting from last up """
        if len(self.path) > 1:
            return tuple(reversed(self.path[:-1]))
        else:
            return ()

    @property
    def parent(self):
        """ Parent of the last node attribute name in the path """
        if self.parents:
            return self.parents[0]

    @property
    def first(self):
        """ First node attribute name of that node attribute path (root of the path) """
        return self.attributes[0]

    @property
    def last(self):
        """ Last node attribute name of that node attribute path (leaf of the path, equivalent to self.attribute) """
        return self.attributes[-1]

    def isCompound(self):
        return len(self.attributes) > 1


class NodeAttribute(NameParsed):

    """
    The name of a Maya node and attribute (plug): a MayaNodePath followed by a AttrSep and a AttributePath

        Rule : NodeAttribute = `MayaNodePath` `AttrSep` `AttributePath`

        Composed Of: `MayaNodePath`, `AttrSep`, `AttributePath`

        Component Of: `MayaObjectName`


        >>> nodeAttr = NodeAttribute( 'persp|perspShape.focalLength' )
        >>> nodeAttr.attributes
        (Attribute('focalLength', 17),)
        >>> nodeAttr.nodePath
        MayaNodePath('persp|perspShape', 0)
        >>> nodeAttr.shortName()
        NodeAttribute('perspShape.focalLength', 0)
        >>>
        >>> nodeAttr2 = NodeAttribute( 'persp.translate.tx' )
        >>> nodeAttr2.attributes
        (Attribute('translate', 6), Attribute('tx', 16))

    """
    _parser = AttributeNameParser
    _accepts = ('MayaNodePath', 'AttrSep', 'AttributePath')

    @property
    def parts(self):
        """ All parts of that attribute name, including separators """
        return self.sub
#    @property
#    def groups(self):
#        """ All groups of that attribute name, ie a node name and a node attribute name """
#        return (self.parts[0], self.parts[2])

    @property
    def separator(self):
        return AttrSep()

    @property
    def nodePath(self):
        """The node part of the plug"""
        return self.parts[0]

    @property
    def attribute(self):
        """The attribute part of the plug"""
        attr = self.parts[2]
        if not attr.isCompound():
            return attr.last
        return attr

    def shortName(self):
        """Just the node and attribute without the full dag path. Returns a copy."""
        new = self.copy()
        for i in range(len(new.nodePath.nodes) - 1):
            new.nodePath.popNode(0)
        return new

    @property
    def attributes(self):
        """ All the node attribute names in that node attribute path, including the last, without separators """
        attr = self.attribute
        if isinstance(attr, Attribute):
            return (attr,)
        else:
            return self.attribute.attributes

    def popNode(self):
        """Remove a node from the end of the path, preserving any attributes (Ex. pCube1|pCubeShape1.width --> pCube1.width)."""
        self.nodePath.popNode()

#    @property
#    def first(self):
#        """ Equivalent to self.node """
#        return self.groups[0]
#    @property
#    def last(self):
#        """  Equivalent to self.attribute """
#        return self.groups[2]


# finally a generic catch-all
class MayaObjectName(NameParsed):

    """
    An object name in Maya, can be a dag object name, a node name,
    an plug name, a component name or a ui name

        Rule : MayaObjectName = `MayaNodePath` | `NodeAttribute` | `Component`

        Composed Of: `MayaNodePath`, `NodeAttribute`, `Component`
    """
    _parser = MayaObjectNameParser
    _accepts = ('MayaNodePath', 'NodeAttribute')

    @property
    def object(self):
        """ The actual Maya object name (node, attribute or component) it encapsulate """
        return self.sub[0]

    @property
    def type(self):
        """ What kind of Maya object is it, a node, an attribute or a component """
        return type(self.object)

    @property
    def parts(self):
        """ All parts of that object name, including separators """
        return self.object.parts

    @property
    def nodes(self):
        """ All the short names in the dag path including the last, without separators """
        return self.object.node.nodes

    @property
    def node(self):
        """ The full path of the node"""
        if self.isNodeName():
            return self.object
        else:
            return self.object.node

    @property
    def attributes(self):
        """ All the node attribute names in that node attribute path, including the last, without separators """
        return self.object.attribute.attributes

    @property
    def attribute(self):
        """ The attribute (full) name for a NodeAttribute (node.attribute) name """
        if self.isAttributeName():
            return self.object.attribute

    @property
    def component(self):
        """ The component name for a Component (node.component) name """
        if self.isComponentName():
            return self.object.component

    def isNodeName(self):
        """ True if this dag path name is absolute (starts with '|') """
        return self.type == MayaNodePath

    def isAttributeName(self):
        """ True if this object is specified including one or more dag parents """
        return self.type == NodeAttribute

    def isComponentName(self):
        """ True if this object is specified as an absolute dag path (starting with '|') """
        return self.type == Component

# Empty special NameParsed class


class Empty(NameParsed):
    _parser = EmptyParser
    _accepts = ()

    @classmethod
    def default(cls):
        return ''


process()

# print "end of normal defs here"

# Current module
_thisModule = __import__(__name__, globals(), locals(), [''])  # last input must included for sub-modules to be imported correctly
#_thisModule = __import__(__name__)
# print "object _thisModule built"
# print _thisModule
# print dir(_thisModule)


# print "Module %s dynamically added %d Token classes" % (__file__, _addedTokenClasses)
# print dir(_thisModule)


def getBasicPartList(name):
    """
    convenience function for breaking apart a maya object to the appropriate level for pymel name parsing

        >>> getBasicPartList('thing|foo:bar.attr[0].child')
        [MayaNodePath('thing|foo:bar', 0), MayaName('attr', 14), NameIndex('[0]', 18), MayaName('child', 22)]
    """
    partList = []

    def getParts(obj):
        try:
            for i, x in enumerate(obj.parts):
                # print "part", i, repr(x)
                if isinstance(x, MayaNodePath) or isinstance(x, MayaName) or isinstance(x, NameIndex):
                    partList.append(x)
                else:
                    getParts(x)
        except AttributeError:
            # print "deadend", repr(obj)
            pass

    getParts(MayaObjectName(name))
    return partList


def parse(name):
    """main entry point for parsing a maya node name"""
    return MayaObjectName(name).object

# restrict visibility to NameParsed classes :
# __all__ = ParsedClasses().keys()
# print "nameparse.py exporting: ", __all__
# print "end here"
# print ParsedClasses()
# print ParserClasses()

# testing


def _decomposeGroup(name, ident=0):
    tab = "\t" * ident
    print(tab + "group:%s (%r)" % (name, name))
    print(tab + "[%s-%s] parts:" % (name.first, name.last), " ".join(name.parts))
    print(tab + "tail:", name.tail)
    print(tab + "is ok for head:", name.isAlpha())


def _decomposeName(name, ident=0):
    tab = "\t" * ident
    print(tab + "name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
    print(tab + "[%s-%s] groups: " % (name.first, name.last), " ".join(name.groups))
    print(tab + "tail: ", name.tail)
    print(tab + "reduced: ", name.reduced())
    for group in name.groups:
        _decomposeGroup(group, ident=ident + 1)


def _decomposeNamespace(name, ident=0):
    tab = "\t" * ident
    print(tab + "namespace: %s (%r)" % (name, name))
    if name:
        print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
        print(tab + "separator: %s" % name.separator)
        print(tab + "[%s-%s] name spaces:" % (name.first, name.last), " ".join(name.spaces))
        print(tab + "space: ", name.space)
        print(tab + "parent: ", name.parent)
        print(tab + "path: ", " ".join(name.path))
        print(tab + "parents: ", " ".join(name.parents))
        print(tab + "is absolute:", name.isAbsolute())
        for space in name.spaces:
            _decomposeName(space, ident=ident + 1)


def _decomposeShortName(name, ident=0):
    tab = "\t" * ident
    print(tab + "short name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.first, name.last), " ".join(name.parts))
    print(tab + "namespace: %s" % name.namespace)
    print(tab + "name: %s" % name.name)
    print(tab + "is absolute namespace: ", name.isAbsoluteNamespace())
    _decomposeNamespace(name.namespace, ident=ident + 1)
    _decomposeName(name.name, ident=ident + 1)


def _decomposeNodeName(name, ident=0):
    tab = "\t" * ident
    print(tab + "node name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
    print(tab + "separator: %s" % name.separator)
    print(tab + "[%s-%s] nodes: " % (name.first, name.last), " ".join(name.nodes))
    print(tab + "node: ", name.node)
    print(tab + "parent: ", name.parent)
    print(tab + "path: ", " ".join(name.path))
    print(tab + "parents: ", " ".join(name.parents))
    print(tab + "is short name: ", name.isShortName())
    print(tab + "is dag name: ", name.isDagName())
    print(tab + "is long name: ", name.isLongName())
    for node in name.nodes:
        _decomposeShortName(node, ident=ident + 1)


def _decomposeNodeAttributeName(name, ident=0):
    tab = "\t" * ident
    print(tab + "node attribute name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
    print(tab + "name: ", name.name)
    print(tab + "index: %s" % name.index)
    print(tab + "indexValue: %s" % name.indexValue)
    _decomposeName(name.name, ident=ident + 1)


def _decomposeNodeAttributePathName(name, ident=0):
    tab = "\t" * ident
    print(tab + "node attribute path name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
    print(tab + "separator: %s" % name.separator)
    print(tab + "[%s-%s] attributes: " % (name.first, name.last), " ".join(name.attributes))
    print(tab + "attribute: ", name.attribute)
    print(tab + "parent: ", name.parent)
    print(tab + "path: ", " ".join(name.path))
    print(tab + "parents: ", " ".join(name.parents))
    for attr in name.attributes:
        _decomposeNodeAttributeName(attr, ident=ident + 1)


def _decomposeAttributeName(name, ident=0):
    tab = "\t" * ident
    print(tab + "attribute name: %s (%r)" % (name, name))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))
    print(tab + "separator: %s" % name.separator)
    print(tab + "node: ", name.node)
    print(tab + "attribute: ", name.attribute)
    _decomposeNodeName(name.node, ident=ident + 1)
    _decomposeNodeAttributePathName(name.attribute, ident=ident + 1)


def _decomposeObjectName(name, ident=0):
    tab = "\t" * ident
    print(tab + "That object name is a %s" % name.type.__name__)
    print(tab + "object: %s (%r)" % (name.object, name.object))
    print(tab + "[%s-%s] parts: " % (name.parts[0], name.parts[-1]), " ".join(name.parts))

    print(tab + "node: ", name.node)
    print(tab + "attribute (if any): ", name.attribute)
    print(tab + "component (if any): ", name.component)

    if name.isNodeName():
        _decomposeNodeName(name.object, ident=ident + 1)
    elif name.isAttributeName():
        _decomposeAttributeName(name.object, ident=ident + 1)
    elif name.isComponentName():
        _decomposeComponentName(name.object, ident=ident + 1)
    else:
        raise ValueError("type should be MayaNodePath, NodeAttribute or Component")


def _test(expr):
    """ Tests the name parsing of the string argument expr and displays results """

    try:
        # name = MayaNodePath(expr)
        name = MayaObjectName(expr)
    except NameParseError as e:
        print("NameParseError:", e)
        try:
            print("tokens")
            for t in name.tokens:
                print(repr(t))
        except:
            pass
    else:
        print("=" * 80)
        print("full name:%s (%r)" % (name, name))
        print("is valid:", name.isValid())
        _decomposeObjectName(name)
        print("=" * 80)


def _itest():
    """ Inerractive name parsing test, enter a name and see result decomposition """

    print("Interractive Name Parsing Test")
    while True:
        expr = input("> ")
        if not expr:
            break
        _test(expr)


if __name__ == '__main__':
    # test('SPACE:pre_someMaya12Name10_12')
    # interractive test for names parsing
    _itest()

