import re, inspect
import ply.lex as lex
import ply.yacc as yacc

#from namedtuple import namedtuple
from common import capitalize, uncapitalize
from mexceptions import *
from arguments import *
from utilitytypes import *

def verbose() :
    return True

def currentfn() :
    try :
        return sys._getframe(1).f_code.co_name
    except :
        pass
    
class NameParseError(Exception):
    pass

class ParsingWarning(ExecutionWarning):
    pass


# For parsed objects, Token or upper level constructs
class Parsed(unicode):
   
    _parser = None
    _accepts = ()

    @classmethod
    def default(cls):
        return None                 
    @classmethod
    def accepts(cls, other) :
        """ Checks if this Parsed class can accept another object as a subpart without reparsing """
        if isinstance(other, Parsed) :
            for t in cls._accepts :           
                if t == other.__class__.__name__ :
                    return True
        return False
    
    # init class attributes, all objects of a Parsed class share the same parser
    # TODO : check if it can be a problem with multithreading ? In that case we'll need a parser per instance  
    @classmethod  
    def classparserbuild(cls, **kwargs):
        """ Inits class Parser, all instances of a Parsed class share the same yacc parser object """
        
        clsname = cls.__name__
        try :  
            # class declaration specifies a parser class
            parser = cls._parser
        except :
            # default rule
            parsername = cls.__name__+"Parser"
            parser = ParserClasses().get(parsername, None)
            cls._parser = parser                
            warnings.warn ("could not read '_parser' for %s, building Parser name %s from Parsed class name %s" % (cls, parsername, clsname), UserWarning)

        if parser is not None :
            # if parser hasn't been built yet, build it
            if not isinstance(parser, Parser) :                
                if inspect.isclass(parser) :
                    parsername = parser.__name__
                    if not issubclass (parser, Parser):
                        raise ValueError, "Parser %s specified in Parsed class %s is not a Parser class" % (parsername, cls.__name__)    
                elif parser in ParserClasses() :
                    parsername = parser
                    parser = ParserClasses()[parsername]
                else :
                    raise ValueError, "Invalid Parser specification %r in Parsed class %s" % (parser, cls.__name__)
                
                # build class Parser, replace class _parser by the Parser instance object

                # print "Building parser instance of Parser %s for Parsed class: %s" % (parser, cls.__name__)
                cls._parser = parser()
                cls._parser.build(**kwargs)
                # return cls._parser
        else :
            raise TypeError, "Parsed class %s does not define a parser, check declarations" % cls.__name__
        
    @classmethod                
    def classparse(cls, data, **kwargs):
        clsname = cls.__name__
        data = unicode(data)
        debug = kwargs.get('debug', verbose())
        # print "Calling parser %s with debug %s" % (cls.classparser(), debug)
        result = cls.classparser().parse(data, debug=debug)
        if cls.classparser().errorcount :
            # use error or warning ?
            raise NameParseError, "cannot parse '%s' to a valid %s, %d parser errors" % (data, clsname, cls.classparser().errorcount)
            result._valid = False
        elif isinstance(result, cls) and result == data :
            # should return a Parsed object with the same string value as the parsed string
            result._valid = True
        else :
            # probably a misformed Parser as no errors where counted yet result string doesn't match data
            raise NameParseError, "unexpected parsing error while parsing '%s' to a valid %s, check Parser definition" % (data, clsname)
            result._valid = False
            
        # position is set to position of first found Parsed object
        if (result.sub) :
            result._pos = result.sub[0].pos
        else :
            result._pos = 0
        # check for error in parsing and correct and raise a warning or raise an error
        # TODO : corrections and error handling
        if not result._valid :
            raise NameParseError, "cannot parse '%s' to a valid %s" % (data, clsname)
        
        return result 
          
    @classmethod
    def classparser(cls):
        """ parser object for that class """
        return cls._parser

    # instance methods

    def parse(self, data, **kwargs):
        return self.__class__.classparse(data, **kwargs)
  
    @property
    def parser(self):
        """ parser object for that class """
        return self.__class__.classparser()
    @property 
    def tokens(self ):
        """ iterates self as leaf level lexed tokens """
        for i in expandArgs(self._sub) :
            if isinstance(i, Token) :
                yield i
    @property
    def sub(self):
        """ Internally stored parsing data for this Parsed object sub parts """
        return self._sub
    @property
    def pos(self):
        """ position of that Parsed object """
        return self._pos                
    def isValid(self):
        """ Validity """
        return self._valid
    
             
    def __new__(cls, *args, **kwargs):
        """ Creation of a Parsed object from a LexToken, other Parsed of compatible type or string,
            if a string is passed it will be parsed and checked for compatibility with this Parsed type """
        
        debug = kwargs.get('debug', verbose())    
        # type checking   
        data = None
        if args :
            if len(args) == 1:
                data = args[0]
            else :
                data = tuple(args)
        
        # some data (when initializing from single arg) can define the type of Parsed object to be created
        ptype = None
        if data is None : 
            # only authorize Empty to be built without arguments
            ptype = 'Empty'
        elif isinstance(data, lex.LexToken) :
            ptype = kwargs.get('type', data.type)
        elif isinstance(data, Parsed) :
            ptype = data.__class__
        # can override type with the keyword 'type'                            
        ptype=kwargs.get('type', ptype)
        
        if (cls is Parsed or cls is Token) :
            if ptype is not None :
                # print "__new__ called on %s with type %r" % (cls.__name__, ptype)
                newcls = ParsedClasses().get(ptype, None)
                # can only specify an existing subclass of cls
                if newcls is None :
                    raise TypeError, "Type %s does not correspond to any existing Parsed sub-class (%s does not exist)" % (ptype, clsname)
                else :
                    clsname = newcls.__name__            
                if not issubclass(newcls, cls) :
                    raise TypeError, "Type %s would create a class %s that is not a sub-class of the class %s that __new__ was called on" % (ptype, clsname, cls.__name__)
            else :
                raise TypeError, "Class %s is an abstract class and can't be created directly, you must specify a valid sub-type" % (cls.__name__)
        else :
            # print "__new__ called on explicit class %s" % (cls.__name__)
            clsname = cls.__name__
            newcls = cls
            
        # print "Creating new instance of Parsed class: %r" % newcls

        # process arguments and build, check arguments compatibility with that type
        pos = None
        sub = []
        valid = False
        value = data
        
        # special case for LexToken
        if isinstance(data, lex.LexToken) :        
            if issubclass(newcls, Token) :
                # from a unique lex Token, do not check if also creating a Token
                sub = []
                pos = data.lexpos
                value = data.value
                valid = True                  
            else :
                # build a Token from it
                value = Token(data.value, ptype=data.type, pos=data.pos)

        if data is None :
            # Tokens can have default value to allow initialization without arguments
            if newcls is Empty :
                value = ''
                valid = True
            else :                 
                default = newcls.default()
                if default :
                    value = default
                    valid = True
                else :
                    valid = False          
        elif isinstance(data, newcls) :
            # from a similar class, copy it
            sub = data.sub
            pos = data.pos
            valid = data.isValid()
            value = unicode(data)            
        elif newcls.accepts(data) :
            # from a compatible Parsed sub class, build the sub list from it
            sub.append(data)
            pos = data.pos
            valid = data.isValid()
            value = unicode(data) 
        elif isSequence(data) : 
            # building from sub parts, must be of the same type and in class _accepts
            # TODO : use yacc own rules for accepts
            if data :
                valid = True
                p = 0
                for arg in data :
                    # converts LexTokens directly
                    if isinstance(arg, lex.LexToken) :        
                        a = Token(arg.value, ptype=arg.type, pos=data.pos)                    
                    else :
                        a = arg
                    # now check if it's a suitable sub-part
                    if newcls.accepts(a) :
                        sub.append(a)
                    else :
                        valid = False
                        break
                value = u"".join(map(unicode, data))                  
                if valid :
                    pos = sub[0].pos
                else :
                    sub = []                    
            else :
                value = ''
        else :
            # reparse unless it's a Token we already know the type of
            value = unicode(data)
            if issubclass(newcls, Token) and newcls is not Token :
                sub = []
                pos = 0
                valid = True
            else :
                valid = False
                   
        # parse if necessary
        if valid :
            # print "No reparsing necessary for a resulting value %s (%r)" % (value, value)            
            strvalue = unicode(value)        
        elif isinstance(value, basestring) :
            print "Will need to reparse value %s (%r)" % (value, value)                    
            newcls.classparserbuild(debug=debug)
            result = newcls.classparse(value, debug=debug) 
            if result is not None :
                strvalue = unicode(result)
                valid = result._valid
                sub = result._sub
                pos = result._pos
            else :
                strvalue = ''
                valid = False
        else :
            raise TypeError, "invalid argument(s) %r cannot be parsed to create a Parsed object of type %s" % (value, clsname)     
        
        if valid :  
            # create a unicode object with appropriate string value 
            newobj =  super(Parsed, cls).__new__(newcls, strvalue)                           
            # set instance attributes
            newobj._sub = tuple(sub)
            newobj._valid = valid        
            # override for pos
            pos = kwargs.get('pos', pos)
            if pos is not None :
                pos += kwargs.get('offset', 0)
                
            if pos is None or (isinstance(pos, int) and pos>=0) :
                newobj._pos = pos
            else :
                raise ValueError, "A Parsed pos can only be None or an unsigned int, %r invalid" % pos        

        return newobj                                           

    def __add__(self, other):
        """ p1.__add__(p2) <==> p1+p2 
            if p1 and p2 are of the same Parsed type, it's equivalent to reparsing str(p1) + str(p2)
            if p2 is an accepted sub part of p1, it adds it to the sub-parts
        """
        # The Parsed _accepts defines validity
        # TODO : use yacc own rules to check validity without a full reparse
        cls = self.__class__
        selfvalid = self.isValid()
        sublist = list(self.sub)
        value = unicode(self)
        # check other's type
        if isinstance(other, cls) :
            othervalid = other.isValid()
            sublist += other.sub
        elif self.accepts(other) :
            othervalid = other.isValid()
            sublist.append(other)
        elif isinstance(other, basestring) :
            othervalid = False
        else :
            raise TypeError, "cannot add %s and %s" % (type(self), type(other))
        
        if selfvalid and othervalid :
            # no reparse
            result = cls(*sublist)
        else :
            # reparse
            result = cls(unicode(self)+unicode(other))
        
        return result
                                
    def __repr__(self):
        return u"%s('%s', %s)" % (self.__class__.__name__, self, self.pos)
       
class Token(Parsed):
    """ A class for token types, allows direct initialization from a string and type without checking
        to avoid unnecessary double parse of the string """
    pass
            
# Parsers, all parser must derive from the Parser class

class Parser(object):
    """ Abstract Base class for all name parsers """
    def __new__(cls, *args, **kwargs):
        # this class is an abstract base class for all Parser classes, cannot be built directly
        
        if cls is Parser :
            ptype=kwargs.get('type', None)
            if ptype is None :
                raise TypeError, "must specify a Parser class" 
            elif isinstance(ptype, Parser) and not ptype is Parser :
                parsercls = ptype   
            elif ptype in ParserClasses() :
                parsercls = ParserClasses()[ptype]
            else :
                raise TypeError, "invalid Parser type: %s" % ptype            
        else :
            parsercls = cls
        # need to build the tokens and precedence tuples from inherited declarations
        # gather tokens and rules definition from Parser class members (own and inherited)
        parsercls.tokensDict = {}
        parsercls.rulesDict = {}
        for m in inspect.getmembers(parsercls) :
            if m[0].startswith('t_') and m[0] != 't_error' :
                k = m[0][2:]
                if isinstance(m[1], basestring) :
                    v = m[1]
                elif inspect.isfunction(m[1]) or inspect.ismethod(m[1]) :
                    v = m[1].__doc__
                else :
                    raise SyntaxError, "Token definition %s defines neither a string nor a function, unable to parse" % m[0]
                k = m[0][2:]
                parsercls.tokensDict[k] = m[1]                      
            elif m[0].startswith('p_') and inspect.ismethod(m[1]) and m[0] != 'p_error' :
                k = m[0][2:]
                parsercls.rulesDict[k] = m[1]
        # class must have a start attribute for __init__, start can be None though
        # must not inherit start as parsed would not parse own class new rules
        if not 'start' in parsercls.__dict__ :
            parsercls.start = None          
                
        parsercls.tokens = tuple(parsercls.tokensDict.keys())
        rules = list(parsercls.rulesDict.keys())
        # Sort them by line number of declaration as it's how the yacc builder works to order rules
        # TODO : some more explicit rule order handling (when precedence isn't an option) ?
        rules.sort(lambda x,y: cmp(parsercls.rulesDict[x].func_code.co_firstlineno,parsercls.rulesDict[y].func_code.co_firstlineno))   
        # print "sorted rules:", [(r, parsercls.rulesDict[r].func_code.co_firstlineno) for r in rules]
        parsercls.rules = tuple(rules)
     
        # TODO : same for precedence rules
        return super(Parser, cls).__new__(parsercls, *args, **kwargs)
                            
    def __init__(self, *args, **kwargs):   
        self.errorcount = 0
        self.lexer = None
        self.parser = None
            
    def t_error(self,t):
        warnings.warn ("illegal character in '%s' at %i: '%s'" % (t.lexer.lexdata, t.lexpos, t.value[0]), ParsingWarning, stacklevel=1)
        self.errorcount += 1
        t.lexer.skip(1)

    def p_error(self,p):
        print "error token", p
        if p is None :
            warnings.warn ("unexpected end of file", ParsingWarning, stacklevel=1)
        else :
            warnings.warn ("syntax error in '%s' at %i: '%s'" % (p.lexer.lexdata, p.lexpos, p.value), ParsingWarning, stacklevel=1)
        self.errorcount += 1

        # Just discard the token and tell the parser it's okay.
        # yacc.errok()
        #yacc.errok(). This resets the parser state so it doesn't think it's in error-recovery mode. This will prevent an error token from being generated and will reset the internal error counters so that the next syntax error will call p_error() again.
        #yacc.token(). This returns the next token on the input stream.
        #yacc.restart(). This discards the entire parsing stack and resets the parser to its initial state.  
        
    def build(self,**kwargs):
        debug = kwargs.get('debug', verbose())
        start = kwargs.get('start', self.__class__.start)  
        outputdir = kwargs.get('outputdir', 'parsers') 
        method = kwargs.get('method', 'LALR')    
        if debug :
            print "Build for", self.__class__.__name__
            print "tokens:"
            for t in self.__class__.tokens :
                print "\t%s = %s" % (t, self.__class__.tokensDict[t])
            print "rules:"
            for t in self.__class__.rules :
                print "\t%s = %s" % (t, self.__class__.rulesDict[t].__doc__)
            print "start: %s" % start

        if self.lexer is None : 
            lextab=self.__class__.__name__+"_lex"
            lkwargs = {'debug':debug, 'lextab':lextab }
            self.lexer = lex.lex(object=self, **lkwargs)
        if self.parser is None :
            tabmodule=self.__class__.__name__+"_yacc_"+start
            pkwargs = {'outputdir':outputdir, 'debug':debug, 'tabmodule':tabmodule, 'start':start, 'method':method }
            self.parser = yacc.yacc(module=self, **pkwargs)
        
    def parse(self, data, **kwargs):
        self.errorcount = 0
        return self.parser.parse(data, lexer=self.lexer, **kwargs)

# special purpose empty parser
class EmptyParser(Parser):
    
    def build(self,**kwargs):
        pass
    
    def parse(self, data, **kwargs):
        self.errorcount = 0
        if data :
            self.errorcount = 1
        else :
            return Empty()

# token parser, can directly use re
class TokenParser(Parser):
    """ Abstract base class for Token parser """
    _pattern = None
    _type = None
    
    def build(self,**kwargs):
        pattern = kwargs.get('pattern', self.__class__._pattern)
        try :
            self.parser = re.compile(pattern)
        except :
            raise ValueError, "cannot build Token Parser from pattern %r", pattern
    
    def parse(self, data, **kwargs):
        self.errorcount = 0
        if self.parser.match(data) is not None :
            return Token(data, type=self._type, pos=0)
        else :
            warnings.warn ("%s is not matching %s pattern %r" % (data, self.__class__.name, self._pattern))
            self.errorcount += 1

# derived TokenParser classes will be built for every token definition detected in Parser classes in this module

# Parsers deriver from the Parser base class
# for Maya names parsing

# NOTE : order of declaration is important as yacc only considers
# lineno of function declaration to order the rules
# TODO : modify Yacc to take mro of class then relative line no or use decorators ?

# no parsed class for this, the tokens Parsers and Parsed will be created automatically anyway
class NameBaseParser(Parser):
    """ Base for name parser with common tokens """
    t_Alpha    = r'([a-z]+)|([A-Z]+[a-z]*)'
    t_Num   = r'[0-9]+'

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
    t_Underscore  = r'_+'
    
    start = 'NameSep' 
    def p_sep_concat(self, p):
        ''' NameSep : NameSep Underscore '''   
        p[0] = p[1] + Token(p[1], type='Underscore', pos=p.lexpos(1))       
    def p_sep(self, p):
        ''' NameSep : Underscore '''   
        p[0] = NameSep(Token(p[1], type='Underscore', pos=p.lexpos(1)))
            
class MayaNameParser(NameGroupParser, NameSepParser):    
    """
        A Parser for the most basic Maya Name : several name groups separated by one or more underscores,
        starting with an alphabetic part or one or more underscore, followed by zero or more NameGroup(s)
        separated by underscores
    """

    start = 'MayaName'
    
    def p_name_error(self, p):
        'MayaName : error'
        print "Syntax error in MayaName. Bad expression"
        
    # a atomic Maya name is in the form (_)*head(_group)*(_)*
    def p_name_concat(self, p):
        ''' MayaName : MayaName NameSep NameGroup
                        | MayaName NameSep '''
        if len(p) == 4 :
            p[0] = (p[1] + p[2]) + p[3]    
        else :
            p[0] = p[1] + p[2]  
    def p_name(self, p):
        ''' MayaName : NameSep NameGroup  
                    | NameAlphaGroup '''
        if len(p) == 3 :
            p[0] = MayaName(p[1], p[2])
        else :
            p[0] = MayaName(p[1])

    # always lower precedence than parts we herit the parser from 
    # TODO : gather precedence from base classes
    precedence = ( ('left', 'Underscore'),
                   ('right', ('Alpha', 'Num') ),
                 )

class NamespaceSepParser(Parser):
    """ A Parser for the NamespaceName separator """
    t_Colon  = r':'
    
    start = 'NamespaceSep' 
    def p_nspace_sep(self, p):
        ''' NamespaceSep : Colon '''   
        p[0] = NamespaceSep(Token(p[1], type='Colon', pos=p.lexpos(1)))    

    precedence = ( ('left', ('Colon') ),
                   ('left', 'Underscore'),
                   ('right', ('Alpha', 'Num') ),
                 )
        
class NamespaceNameParser(MayaNameParser, NamespaceSepParser):
    """ A Parser for NamespaceName, Maya namespaces names """

    start = 'NamespaceName'

    def p_nspace_concat(self, p):
        ''' NamespaceName : NamespaceName MayaName NamespaceSep '''
        p[0] = p[1] + NamespaceName(p[2], p[3])
    def p_nspace(self, p) :
        ''' NamespaceName : MayaName NamespaceSep 
                    | NamespaceSep '''
        if len(p) == 3 :
            p[0] = NamespaceName(p[1], p[2])
        else :
            p[0] = NamespaceName(p[1])
                                    
class MayaShortNameParser(NamespaceNameParser, MayaNameParser):
    """ A parser for MayaShortName, a short object name (without preceding path) with a possible preceding namespace """
    
    start = 'MayaShortName'
    
    def p_sname(self, p) :
        ''' MayaShortName : NamespaceName MayaName  
                    | MayaName '''
        if len(p) == 3 :
            p[0] = MayaShortName(p[1], p[2])
        else :
            p[0] = MayaShortName(p[1])           

# parsed objects for Maya Names
# TODO : build _accepts from yacc rules directly

# Atomic Name element, an alphabetic or numeric word
class NamePart(Parsed):
    """ A name part of either the NameAlphaPart or NameNumPart kind
        Rule : NamePart = NameAlphaPart | NameNumPart """
    _parser = NamePartParser
    _accepts = ('Alpha', 'Num')
    
    def isAlpha(self):
        return isinstance(self.sub[0], Alpha)       
    def isNum(self):  
        return isinstance(self.sub[0], Num) 
    
class NameAlphaPart(NamePart):
    """ A name part made of alphabetic letters
        Rule : NameAlphaPart = r'([a-z]+)|([A-Z]+[a-z]*)' """
    _parser = NameAlphaPartParser
    _accepts = ('Alpha', )
         
    def isAlpha(self):
        return True        
    def isNum(self):
        return False

class NameNumPart(NamePart):
    """ A name part made of numbers
        Rule : NameNumPart = r'[0-9]+' """
    _parser = NameNumPartParser
    _accepts = ('Num', )
         
    def isAlpha(self):
        return False        
    def isNum(self):
        return True
       
# A Name group, all the consecutive parts between two underscores
class NameGroup(Parsed):
    """ A name group of either the NameAlphaGroup or NameNumGroup kind
        Rule : NameGroup = NameAlphaGroup | NameNumGroup """
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
        if self.last.isNum() :
            return (self.last)

   
class NameAlphaGroup(NameGroup):
    """ A name group starting with an alphabetic part
        Rule : NameAlphaGroup  = NameAlphaPart NamePart * """ 
    _parser = NameAlphaGroupParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NamePart')  

    def isNum(self):
        return False
    def isAlpha(self):
        return True
        
class NameNumGroup(NameGroup):
    """ A name group starting with an alphabetic part
        Rule : NameAlphaGroup  = NameAlphaPart NamePart * """ 
    _parser = NameNumGroupParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NamePart')     

    def isNum(self):
        return True
    def isAlpha(self):
        return False
    
# separator for name groups               
class NameSep(Parsed):
    """ the MayaName NameGroup separator : one or more underscores
        Rule : NameSep = r'_+' """
    _parser = NameSepParser
    _accepts = ('Underscore',)  
    
    @classmethod
    def default(cls):  
        return Token('_', type='Underscore', pos=0)              
    def reduced(self):
        """ Reduce multiple underscores to one """
        return NameSep()

# a short Maya name without namespaces or attributes    
class MayaName(Parsed):
    """ The most basic Maya Name : several name groups separated by one or more underscores,
        starting with a NameHead or one or more underscore, followed by zero or more NameGroup
        Rule : MayaName = (NameSep * NameAlphaGroup) | (NameSep + NameNumGroup)  ( NameSep NameGroup ) * NameSep * """

    _parser = MayaNameParser
    _accepts = ('NameAlphaGroup', 'NameNumGroup', 'NameGroup', 'NameSep') 

    @property
    def groups(self):
        """ All groups of that Maya name, skipping separators """
        result = []
        for s in self.parts :
            if not isinstance(s, NameSep) :
                result.append(s)
        return tuple(result)
    @property
    def parts(self):
        """ All groups of that name, including separators """
        return self.sub   
    @property
    def first(self):
        """ First group of that Maya name """
        return self.parts[0]   
    @property
    def last(self):
        """ Last group of that Maya name """
        return self.parts[-1]        
    @property
    def tail(self):
        """ The tail (trailing numbers if any) of that Maya Name """
        if self.groups :
            return self.groups[-1].tail
    def reduced(self):
        """ Reduces all separators in thet Maya Name to one underscore, eliminates head and tail separators if not needed """
        groups = self.groups
        result = []
        if groups :
            if groups[0].isNum() :
                result.append(NameSep())
            result.append(groups[0])
            for g in groups[1:] :
                result.append(NameSep())
                result.append(g)
            return self.__class__(*result)
        else :
            return self        

class NamespaceSep(Parsed):
    """ The Maya Namespace separator : the colon ':' 
        Rule : NamespaceSep = r':' """
    _parser = NamespaceSepParser
    _accepts = ('Colon',) 
    
    @classmethod
    def default(cls):  
        return Token(':', type='Colon', pos=0)          
        
class NamespaceName(Parsed):
    """ A Maya namespace name, one or more MayaName separated by ':'
        Rule : NamespaceName = (NameSep * NameAlphaGroup) | (NameSep + NameNumGroup)  ( NameSep NameGroup ) * NameSep * """
    _parser = NamespaceNameParser
    _accepts = ('NamespaceSep', 'MayaName') 
    @property
    def spaces(self):
        """ All different individual namespaces in that Maya namespace, skipping separators """
        result = []
        for s in self.parts :
            if not isinstance(s, NamespaceSep) :
                result.append(s)
        return tuple(result)      
    @property
    def parts(self):
        """ All parts of that namespace, including separators """
        return self.sub         
    @property
    def first(self):
        """ First individual namespace of that namespace """
        try: 
            return self.spaces[0]
        except :
            pass  
    @property
    def last(self):
        """ Last individual namespace in that namespace """
        try: 
            return self.spaces[-1]
        except :
            pass  
      
    def isAbsolute(self):
        """ True if this namespace is an absolute namespace path (starts with ':') """
        return isinstance(self.parts[0], NamespaceSep)

            
class MayaShortName(Parsed):
    """ A short object name in Maya, a Maya name, possibly preceded by a NamespaceName
        Rule : MayaShortName = NamespaceName ? MayaName """
    _parser = MayaShortNameParser
    _accepts = ('NamespaceName', 'MayaName') 
        
    @property
    def parts(self):
        """ All parts of that namespace, including separators """
        return self.sub         
    @property
    def node(self):
        """ The node name (without any namespace) of the Maya short object name """
        return self.parts[-1]
    @property
    def namespace(self):
        """ The namespace name (full) of the Maya short object name """
        if isinstance(self.parts[0], NamespaceName) :
            return self.parts[0]   
    def isAbsoluteNamespace(self):
        """ True if this object is specified in an absolute namespace """
        if self.namespace :
            return self.namespace.isAbsolute()
        else :
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
        
#t_COLON   = r':'
#t_VERTICAL  = r'\|'
                
# Empty special Parsed class
class Empty(Parsed):
    _parser = EmptyParser
    _accepts = () 
    
print "end of normal defs here"

# Current module
#_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly
_thisModule = __import__(__name__)
print "object _thisModule built"
#print _thisModule
#print dir(_thisModule)

def _parsedClass (x) :
    try :
        return issubclass(x, Parsed)
    except :
        return False  
def _parserClass (x) :
    try :
        return issubclass(x, Parser)
    except :
        return False   
        
# generates classes and parsers (re based) for Tokens found in thus module Parser definitions classes
def _createTokenClasses():
    result = 0
    tokensDict = {}
    # temp list of Parser classes 
    ParserClasses = dict(inspect.getmembers(_thisModule, _parserClass))    
    # collect tokens definitions in each classes
    for parser in ParserClasses :
        parsercls = ParserClasses[parser]
        for m in parsercls.__dict__.items() :
            # print "class %s has attribute %s" % (parsercls.__name__, m)
            if m[0].startswith('t_') and m[0] != 't_error' :
                k = m[0][2:]
                if isinstance(m[1], basestring) :
                    v = m[1]
                elif inspect.isfunction(m[1]) or inspect.ismethod(m[1]) :
                    v = m[1].__doc__
                else :
                    raise SyntaxError, "Token definition %s defines neither a string nor a function, unable to parse" % m[0]
                k = m[0][2:]
                if k in tokensDict :
                    warnings.warn("Token %s redefined in Parser %s" % (k, parser), UserWarning)
                tokensDict[k] = v    
    for token in tokensDict :
        pattern = tokensDict[token]
        parsedName = token
        parserName = token+"Parser"
        print "adding classes %s and %s for token %s of pattern %r" % (parsedName, parserName, token, pattern)         
        class ThisToken(Token):
            """ Token stub class """            
        class ThisTokenParser(TokenParser):
            """ Token Parser stub class """      
        # set the Token Parser class attributes
        ThisTokenParser.__name__ = parserName
        #ThisTokenParser.__doc__ = "Parser for token %s=%r" % (token, pattern)
        ThisTokenParser.__module__ = __name__
        ThisTokenParser._pattern = pattern 
        ThisTokenParser._type = token   
        # set the Token class attributes
        ThisToken.__name__ = parsedName
        # ThisToken.__doc__ = "Parser for token %s=%r" % (token, pattern)
        ThisToken.__module__ = __name__
        ThisToken._parser = ThisTokenParser        
        # add to the module
        setattr( _thisModule, parsedName, ThisToken )
        setattr( _thisModule, parserName, ThisTokenParser )
        result += 1
    return result
                
# do it       
_addedTokenClasses =_createTokenClasses()
print "Module %s dynamically added %d Token classes" % (__file__, _addedTokenClasses)
#print dir(_thisModule)

# Build a dict of all existing Parser and Parsed classes in this module
class ParsedClasses(dict) :
    __metaclass__ =  metaStatic
def parsedClasses():  
    return dict(inspect.getmembers(_thisModule, _parsedClass))
# Stores it at import so that the inspect method isn't recalled at each query
ParsedClasses(parsedClasses())

class ParserClasses(dict) :
    __metaclass__ =  metaStatic
def parserClasses(): 
    return dict(inspect.getmembers(_thisModule, _parserClass))
# Stores it at import so that the inspect method isn't recalled at each query
ParserClasses(parserClasses())

print "end here"
print ParsedClasses()
print ParserClasses()



 
    
if __name__ == '__main__' :
    # interractive test for names parsing
    print "Name Parsing Test"
    while True:
        expr = raw_input("> ")
        if not expr: break
        try:
            fullname = MayaShortName(expr)
        except NameParseError, e:
            print "NameParseError:", e
            try :
                print "tokens"
                for t in fullname.tokens :
                    print repr(t) 
            except :
                pass                     
        else:
            print "full name:%s (%r)" % (fullname, fullname)
            print "is valid:", fullname.isValid()
            namespace = fullname.namespace
            node = fullname.node
            if namespace :
                print "\t%s : %s" % (namespace.__class__.__name__, namespace)
                print "\t[%s-%s] name spaces:" % (namespace.first, namespace.last), " ".join(namespace.spaces)
                print "\t[%s-%s] parts:" % (namespace.first, namespace.last), " ".join(namespace.parts)
                print "\tis absolute:", namespace.isAbsolute()
                for name in namespace.spaces :
                    print "\t\tindividual name space: %s (%r)" % (name, name)
                    print "\t\t[%s-%s] groups:" % (name.first, name.last), " ".join(name.groups)
                    print "\t\t[%s-%s] parts:" % (name.first, name.last), " ".join(name.parts)                
                    print "\t\ttail:", name.tail
                    print "\t\treduced:", name.reduced()
                    for group in name.groups :
                        print "\t\t\tgroup:%s (%r)" % (group, group)
                        print "\t\t\t[%s-%s] parts:" % (group.first, group.last), " ".join(group.parts)
                        print "\t\t\ttail:", group.tail       
                        print "\t\t\tis ok for head:", group.isAlpha()
                        print "\t\t\tparts:", group.parts
                        print "\t\t\ttokens:"
                        for t in group.tokens :
                            print repr(t)                  
            # always a node
            name = node
            print "\t%s : %s" % (name.__class__.__name__, name)
            print "\t[%s-%s] groups:" % (name.first, name.last), " ".join(name.groups)
            print "\t[%s-%s] parts:" % (name.first, name.last), " ".join(name.parts)
            print "\ttail:", name.tail
            print "\treduced:", name.reduced()
            for group in name.groups :
                print "\t\tgroup:%s (%r)" % (group, group)
                print "\t\t[%s-%s] parts:" % (group.first, group.last), " ".join(group.parts)
                print "\t\ttail:", group.tail       
                print "\t\tis ok for head:", group.isAlpha()
                print "\t\tparts:", group.parts
                print "\t\ttokens:"
                for t in group.tokens :
                    print repr(t)        

  
