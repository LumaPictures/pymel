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

# to store sub parts of a Parsed object
class SubParts(list) :
    """ Class to hold parsed data abstract syntax tree,
        it's a list of Parsed objects, each containing a list
        of it's sub Parsed object in its subparts """
    def __init__(self, *args):
        if args :
            invalid = []
            for arg in args :
                if isinstance (arg, Parsed) :
                    self.append(arg)
                elif isIterable (arg) :
                    for a in SubParts(*arg) :
                        self.append(a)
                else :
                    invalid.append(arg)
            if invalid :
                raise TypeError, "SubParts can only contain Parsed objects, %r invalid" % tuple(invalid)
    def __add__(self, other):
        result = self
        other = SubParts(other)
        for a in other :
            result.append(a)
        return result
    def __iadd__(self, other):
        other = SubParts(other)
        for a in other :
            self.append(a)   
    def parsedname(self):
        return "".join(map(unicode, self))

# For parsed objects, Token or upper level constructs
class Parsed(unicode):
   
    _parser = None
    _accepts = ()

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

                print "Building parser instance of Parser %s for Parsed class: %s" % (parser, cls.__name__)
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
        print "Calling parser %s with debug %s" % (cls.classparser(), debug)
        result = cls.classparser().parse(data, debug=debug)
        if cls.classparser().errorcount :
            # use error or warning ?
            raise NameParseError, "cannot parse '%s' to a valid %s, %d parser errors" % (data, clsname_, cls.classparser().errorcount)
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
            ptype = capitalize(kwargs.get('type', data.type))
        elif isinstance(data, Parsed) :
            ptype = data.__class__
        # can override type with the keyword 'type'                            
        ptype=kwargs.get('type', ptype)
        
        if (cls is Parsed or cls is Token) :
            if ptype is not None :
                print "__new__ called on %s with type %r" % (cls.__name__, ptype)
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
            print "__new__ called on explicit class %s" % (cls.__name__)
            clsname = cls.__name__
            newcls = cls
            
        print "Creating new instance of Parsed class: %r" % newcls

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
                value = Token(data.value, ptype=capitalize(data.type), pos=data.pos)

        if data is None and newcls is Empty :
            # nothing to do
            value = ''
            valid = True            
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
                for a in data :
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
            print "No reparsing necessary for a resulting value %s (%r)" % (value, value)            
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
            if m[0].startswith('t_') and isinstance(m[1], basestring) :
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
            return Token(data, type=capitalize(self._type), pos=0)
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
    t_alphabetic    = r'([a-z]+)|([A-Z]+[a-z]*)'
    t_number   = r'[0-9]+'
    
    def p_alpha(self, p):
        ''' alpha : alphabetic'''                 
        p[0] = Token(p[1], type='Alphabetic', pos=p.lexpos(1))                    
    def p_num(self, p):
        ''' num : number'''            
        p[0] = Token(p[1], type='Number', pos=p.lexpos(1))

# trailing numbers at the end of a name group
# must be declared before AlphaPart and NumPart to take precedence
class NameTailParser(NameBaseParser):
    """ Parser for trailing numbers at the end of a name group """
    start = 'tail'
    # must be declared before part / apart / npart to take precedence
    def p_tail(self, p):
        ''' tail : num
                    | empty'''
        p[0] = NameTail(p[1])   
    def p_empty(self, p):
        'empty :'
        p[0] = Empty()  

class NameAlphaPartParser(NameBaseParser):
    """ Parser for a name part starting with a letter """
    start = 'apart'
    
    def p_apart_concat(self, p):
        '''apart : apart alpha
                    | apart num'''
        p[0] = p[1] + p[2]        
    def p_apart(self, p):
        '''apart : alpha'''       
        p[0] = NameAlphaPart(p[1])   

class NameNumPartParser(NameBaseParser):
    """ Parser for a name part starting with a number """
    start = 'npart'
   
    def p_npart_concat(self, p):
        '''npart : npart alpha
                    | npart num'''   
        p[0] = p[1] + p[2]        
    def p_npart(self, p):
        '''npart : num'''      
        p[0] = NameNumPart(p[1])   
       
class NamePartParser(NameAlphaPartParser, NameNumPartParser):
    """ Parser for a name part of either the NameAlphaPart or NameNumPart kind """
    start = 'part'

    def p_part(self, p):
        '''part : apart
                    | npart'''       
        p[0] = NamePart(p[1])    

class NameHeadParser(NameTailParser, NameAlphaPartParser):
    """
        A Parser for a suitable group for a name head : one or more parts, the first part starting with a letter,
        and an optionnal tail of trailing numbers    
    """
    start = 'head'
    
    def p_head(self, p):
        ''' head : apart tail '''
        p[0] = NameHead(p[1], p[2])

class NameBodyParser(NameTailParser, NamePartParser):        
    """
        A Parser for a name group, that might not be suitable for name head:
        one or more parts, the first part can start with a number,
        and an optional tail of trailing numbers.
        If the NameBody only composed of one NameNumPart, that part will be considered the tail        
    """
    start = 'body'
    
    def p_body(self, p):
        ''' body : npart tail
                    | apart tail
                    | tail '''             
        if len(p) == 3 :
            p[0] = NameBody(p[1], p[2])   
        else :
            p[0] = NameBody(p[1])
               
class NameGroupParser(NameHeadParser, NameBodyParser):    
    """
        A Parser for a name group of either the NameHead or NameBody kind
    """    
    start = 'group'
    def p_group(self, p):
        ''' group : head
                        | body '''                     
        p[0] = NameGroup(p[1])

class NameSeparatorParser(Parser):
    """ A Parser for the MayaName NameGroup separator : one or more underscores """
    t_underscore  = r'_+'
             
    def p_sep(self, p):
        ''' sep : underscore '''   
        p[0] = Token(p[1], type='Underscore', pos=p.lexpos(1))
            
class MayaNameParser(NameGroupParser, NameSeparatorParser):    
    """
        A Parser for the most basic Maya Name : several name groups separated by one or more underscores,
        starting with a NameHead or one or more underscore, followed by zero or more NameGroup
    """

    start = 'name'
    
    def p_name_error(self, p):
        'name : error'
        print "Syntax error in head. Bad expression"
        
    # a atomic Maya name is in the form (_)*head(_group)*(_)*
    def p_name_concat(self, p):
        ''' name : name sep head  
                    | name sep body '''
        p[0] = p[1] + p[2] + p[3]      
    def p_name(self, p):
        ''' name : sep body  
                    | head '''
        if len(p) == 3 :
            p[0] = MayaName(p[1], p[2])
        else :
            p[0] = MayaName(p[1])

    # always lower precedence than parts we herit the parser from 
    # TODO : gather precedence from base classes
    precedence = ( ('left', 'underscore'),
                   ('right', ('alphabetic', 'number') ),
                 )

# parsed objects for Maya Names
# TODO : build _accepts from yacc rules directly

class NamePart(Parsed):
    """ A name part of either the NameAlphaPart or NameNumPart kind """
    _parser = NamePartParser
    _accepts = ('Alphabetic', 'Number')
    
    def isNum(self):
        if self.sub :
            return type(self.sub[0]) == 'Number'
        else :
            return False
    def isAlpha(self):
        if self.sub :
            return type(self.sub[0]) == 'Alphabetic'
        else :
            return False

class NameTail(Parsed):
    """ The Trailing numbers at the end of a name group """
    _parser = NameTailParser
    _accepts = ('Empty', 'Number')
    
class NameAlphaPart(NamePart):
    """ A name part starting with a letter """
    _parser = NameAlphaPartParser
    _accepts = ('Alphabetic',)  

    def isNum(self):
        return False
    def isAlpha(self):
        return True
        
class NameNumPart(NamePart):
    """ A name part starting with a letter """
    _parser = NameNumPartParser
    _accepts = ('Number','Alphabetic')    

    def isNum(self):
        return True
    def isAlpha(self):
        return False
    
class NameGroup(Parsed):    
    """
        A NameGroup (one or more consecutive NameParts) of either the NameHead or NameBody kind
    """    
    _parser = NameGroupParser
    _accepts = ('Alphabetic', 'Number')       

    @property
    def parts(self):
        """ All parts of that name group """
        return self.sub
    
    @property
    def tail(self):
        """ The tail (trailing numbers if any) of that name group """
        if self.sub and self.sub[-1].isNum() :
            return (self.sub[-1])

    def isHead(self):
        """ If that group can be the head of a name (starts with an alpha part) """
        if self.sub and self.sub[0].isAlpha() :
            return True
        else :
            return False

class NameBody(NameGroup):        
    """
        A NameGroup suitable for the start of a MayaName :
        one or more parts, the first part can start with a number,
        and an optional tail of trailing numbers.
        If the NameBody only composed of only one NameNumPart, that part will be considered the tail        
    """
    _parser = NameBodyParser
    _accepts = ('NameAlphaPart', 'NameNumPart', 'NameTail') 
    
class NameHead(NameBody):
    """ 
        A NameGroup suitable for the start of a MayaName : one or more parts, the first part starting with a letter,
        and an optional tail of trailing numbers    
    """
    _parser = NameHeadParser
    _accepts = ('NameAlphaPart', 'NameTail')   

    def isHead(self):
        """ If that group can be the head of a name (starts with an alpha part) """
        return True
               
class NameSeparator(Parser):
    """ the MayaName NameGroup separator : one or more underscores """
    _parser = NameSeparatorParser
    _accepts = ('Underscore',)   
                      
    def reduce(self):
        """ Reduce multiple underscores to one """
        return NameSeparator(Token('_', type='Underscore', pos=0))
    
class MayaName(Parsed):
    """
        The most basic Maya Name : several name groups separated by one or more underscores,
        starting with a NameHead or one or more underscore, followed by zero or more NameGroup
    """
    _parser = MayaNameParser
    _accepts = () 

# Empty special Parsed class
class Empty(Parsed):
    _parser = EmptyParser
    _accepts = () 
    
print "end of normal defs here"
print __name__

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
            if m[0].startswith('t_') and isinstance(m[1], basestring) :
                k = m[0][2:]
                if k in tokensDict :
                    warnings.warn("Token %s redefined in Parser %s" % (k, parser), UserWarning)
                tokensDict[k] = m[1]    
    for token in tokensDict :
        pattern = tokensDict[token]
        parsedName = capitalize(token)
        parserName = capitalize(token)+"Parser"
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

name = NameGroup('some', 'Maya')

data = 'someMaya'
name = NameGroup(data)
print type (name)
print repr(name)
for t in name.tokens :
    print t
for t in name.parts :
    print t
print name.tail
print name.sub
print name.isHead()

#
#print "Name Parsing Test"
#while True:
#    expr = raw_input(":")
#    if not expr: break
#    try:
#        name = MayaAtomName(expr)
#    except NameParseError, e:
#        print e
#        for t in name.tokens() :
#            print (t.type, t)         
#    else:
#        print name, repr(name)
 
#class MayaShortName(ParsedBase): 
#    _parser = MayaAtomNameParser()
#    _parser.build()   
    
     

#print "Name Parsing Test"
#while True:
#    expr = raw_input(":")
#    if not expr: break
#    try:
#        name = MayaNameGroup(expr)
#    except NameParseError, e:
#        print "NameParseError:", e
#        print "tokens"
#        for t in name.tokens :
#            print repr(t)        
#    else:
#        print "name:%s (%r)" % (name, name)
#        print "is valid:", name.isValid()
#        print "name data:", name.data
#        print "tokens:"
#        for t in name.tokens :
#            print repr(t)
#        print "parts:", name.parts
#        print "tail:", name.tail       
#        print "is head:", name.isHead()

#data = 'someMaya'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t)    
# 
#data = '323Maya32'
#name = ParsedBase(data)
#for t in name.tokens() :
#    print (t.type, t)        

#data = 'someMayaName92'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#    
#    
#data = 'someMaya45Name92'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#    
#data = 'some'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#   
#data = '323'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t)    
#    
#data = '32some45Name'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t)     
#    
#data = '32some45Name92'
#name = ParsedBase(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#    
#data = 'someMayaName92_123ThisIs67Body45_andSomeTail32'
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t)       
#
#data = 'someMayaName92_45_andSomeTail32'
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t) 
#    
#data = '_someMayaName92__45_andSomeTail32_'
#name = MayaAtomName(data)
#print repr(name)
#for t in name.tokens() :
#    print (t.type, t)           

#name = MayaName('someMayaName92')
#print name
#for t in name.tokens() :
#    print (t.type, t)
#
#name = MayaName('someMayaName92')
#print name
#for t in name.tokens() :
#    print (t.type, t)
#    
#name = MayaName('456Name92')
#print name
#for t in name.tokens() :
#    print (t.type, t)
#
#name = MayaName('test_Name92')
#print name
#for t in name.tokens() :
#    print (t.type, t)
#    
#name = MayaName('456Name92')
#print name
#for t in name.tokens() :
#    print (t.type, t)    

#t_COLON   = r':'
#t_VERTICAL  = r'\|'