"""
.. classtree:: ProxyUni

.. dotgraph:: 

    main -> parse -> execute; 
    main -> init; 
    main -> cleanup; 
    execute -> make_string; 
    execute -> printf 
    init -> make_string; 
    main -> printf; 
    execute -> compare; 

"""

import re, inspect, sys, os
import external.ply.lex as lex
import external.ply.yacc as yacc

#from namedtuple import namedtuple
from common import capitalize, uncapitalize
from pwarnings import *
from arguments import *
from utilitytypes import *

# increase from 0 to 1 or 2 for more debug feedback
def verbose() :
    return 0

def currentfn() :
    try :
        return sys._getframe(1).f_code.co_name
    except :
        pass

   
class NameParseError(Exception):
    pass

class ParsingWarning(ExecutionWarning):
    pass


        
ProxyUni = proxyClass( unicode, 'ProxyUnicode', dataFuncName='__name__', remove=['__getitem__']) # 2009 Beta 2.1 has issues with passing classes with __getitem__

# For parsed objects, Token or upper level constructs
class Parsed(ProxyUni):
   
    _parser = None
    _accepts = ()
    _name = None
    
#class Parsed(unicode):
#   
#    _parser = None
#    _accepts = ()

    @classmethod
    def accepts(cls, other) :
        """ Checks if this Parsed class can accept another object as a subpart without reparsing """
        if isinstance(other, Parsed) :
            for t in cls._accepts :           
                if t == other.__class__.__name__ :
                    return True
        return False
    
    def compileName( self ):
        newname = ''
        partList = []
        def getParts( obj, newname ):
            try:
                for x in obj.parts:
                    #print repr(x)
                    newname = getParts(x, newname)
            except AttributeError:
                #print "DEAD", repr(obj)
                newname += unicode(obj._name)
            return newname
        self._name = getParts( self, newname )
        return self._name
    
    __name__ = compileName
    
    @classmethod
    def getParserClass(cls, parsername ):
        pass
    
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
                # parser is a class                
                if inspect.isclass(parser) :
                    parsername = parser.__name__
                    if not issubclass (parser, Parser):
                        raise ValueError, "Parser %s specified in Parsed class %s is not a Parser class" % (parsername, cls.__name__)    
                # parser is a string
                elif parser in ParserClasses() :
                    parsername = parser
                    parser = ParserClasses()[parsername]
                else :
                    raise ValueError, "Invalid Parser specification %r in Parsed class %s" % (parser, cls.__name__)
                
                # build class Parser, replace class _parser by the Parser instance object

                # print "Building parser instance of Parser %s for Parsed class: %s" % (parser, cls.__name__)
                # replace _parser attribute (which held a Parser class or classname) with parser class instance
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
        errmsg = ''
        # print "Calling parser %s with debug %s" % (cls.classparser(), debug)
        result = cls.classparser().parse(data, debug=debug)
        if cls.classparser().errorcount :
            # use error or warning ?
            errmsg = "cannot parse '%s' to a valid %s, %d parser errors" % (data, clsname, cls.classparser().errorcount)
            result._valid = False
        elif not isinstance(result, cls) :
            # parse successful but returned a different class than exected
            errmsg = "parsing '%s' is valid, but as a %s Parsed object, and not as a %s Parsed object as it was parsed against" % (data, result.__class__.__name__, clsname)
            result._valid = False        
        elif not result == data :
            # should return a Parsed object with the same string value as the parsed string
            errmsg = "parsing '%s' raised no error, but the resulting name is %s is different from the imput string %s " % (result, data)
            result._valid = False
        else :
            # parse successful
            result._valid = True
            
        # position is set to position of first found Parsed object
        if (result.sub) :
            result._pos = result.sub[0].pos
        else :
            result._pos = 0
        # check for error in parsing and correct and raise a warning or raise an error
        # TODO : corrections and error handling
        if not result._valid :
            # can try to auto-correct some badly formed names
            raise NameParseError, errmsg
        
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
    
    def setSubItem(self, index, value):
        """ Change the value of one of the Parsed sub parts.  The new value will first be parsed as the same
        type as it is replacing."""
        cls = self._sub[index].__class__
        sublist = list(self._sub)
        sublist[index] = cls(value)
        self._sub = tuple(sublist)
    
    @property
    def pos(self):
        """ position of that Parsed object """
        return self._pos                
    def isValid(self):
        """ Validity """
        return self._valid
    
    def copy(self):
        """return an new independent copy of the parsed object""" 
        return self.__class__(self._sub)
    
    def findType(self, type):
        res = []
        for x in self.sub:
            if isinstance(x,type):
                res.append( x )
            else:
                res += x.findType(type)
        return res
    
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
        
        if (cls is Parsed or cls is Token) : #issubclass(cls, Token) ):
            if ptype is not None :
                if verbose():
                    print "__new__ called on Parsed/Token %s with type %r" % (cls.__name__, ptype)
                newcls = ParsedClasses().get(ptype, None)
                # can only specify an existing subclass of cls
                if newcls is None :
                    raise TypeError, "Type %s does not correspond to any existing Parsed sub-class (%s does not exist)" % (ptype, cls.__name__  )
                else :
                    clsname = newcls.__name__            
                if not issubclass(newcls, cls) :
                    raise TypeError, "Type %s would create a class %s that is not a sub-class of the class %s that __new__ was called on" % (ptype, clsname, cls.__name__)
            else :
                raise TypeError, "Class %s is an abstract class and can't be created directly, you must specify a valid sub-type" % (cls.__name__)
        else :
            if verbose():
                print "__new__ called on explicit class %s" % (cls.__name__)
            clsname = cls.__name__
            newcls = cls
            
        # print "Creating new instance of Parsed class: %r" % newcls

        # process arguments and build, check arguments compatibility with that type
        pos = None
        sub = []
        valid = False
        value = data
        
        #if debug : print "VALUE1", value, repr(value)
        
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
            try :                 
                value = newcls.default()
                valid = True
            except :
                valid = False          
        elif isinstance(data, newcls) :
            #if debug : print "IS INSTANCE", data, repr(data)
            # from a similar class, copy it
            sub = data.sub
            pos = data.pos
            valid = data.isValid()
            value = unicode(data)            
        elif newcls.accepts(data) :
            #if debug : print "ACCEPTS", data, repr(data)
            # from a compatible Parsed sub class, build the sub list from it
            sub.append(data)
            pos = data.pos
            valid = data.isValid()
            value = unicode(data) 
        elif isSequence(data) and not isinstance(data, basestring): 
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
                    # now check if it's a suitable sub-part or derived class
                    if isinstance(a, newcls) :
                        sub += a.sub
                    elif newcls.accepts(a) :
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
            if debug : print "REPARSE", data, repr(data)
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
            if debug :
                print "%s: Will need to reparse value %r" % (clsname, value)                    
            newcls.classparserbuild(debug=debug)
            if debug : print "VALUE", value, type(value)
            result = newcls.classparse(value, debug=debug) 
            if debug : print "RESULT", result, type(result), isinstance(result, newcls)
            if result is not None and isinstance(result, newcls) :
                strvalue = unicode(result)
                valid = result._valid
                sub = result._sub
                pos = result._pos
                if debug : print "SUB", sub
            else :
                strvalue = ''
                valid = False
        else :
            raise TypeError, "invalid argument(s) %r, cannot be parsed to create a Parsed object of type %s" % (value, clsname)     
        
        if valid :  
            # create a unicode object with appropriate string value 
            newobj =  super(Parsed, cls).__new__(newcls)
            newobj._name = strvalue
            #if debug: print "NAME", newobj, type(newobj), sub#, inspect.getmro(newobj)                         
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
    
    def isNodeName(self):
        """ True if this dag path name is absolute (starts with '|') """
        return type(self) == MayaNodePath  
    def isAttributeName(self):
        """ True if this object is specified including one or more dag parents """
        return type(self) == NodeAttribute   
    def isComponentName(self):
        """ True if this object is specified as an absolute dag path (starting with '|') """
        return type(self) == Component
                             
    def __repr__(self):
        return u"%s('%s', %s)" % (self.__class__.__name__, self, self.pos)
       
# Parsers, all parser must derive from the Parser class

class Parser(object):
    """ Abstract Base class for all name parsers """
    def __new__(cls, *args, **kwargs):
        # this class is an abstract base class for all Parser classes, cannot be built directly
        
        if cls is Parser :
            # type argument can be the name of a Parser class or an instance of the class
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
            # subclasses of Parser
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
        parserspath = os.path.dirname(__file__)
        parserspath = os.path.join(parserspath, outputdir)
        if debug :
            print "nameparse parsers path", parserspath
        outputdir = None 
        method = kwargs.get('method', 'LALR')    
        if debug :
            print "Build for", self.__class__.__name__
            print "tokens:"
            for t in self.__class__.tokens :
                print "\t%s = %r" % (t, self.__class__.tokensDict[t])
            print "rules:"
            for t in self.__class__.rules :
                print "\t%s = %r" % (t, self.__class__.rulesDict[t].__doc__)
            print "start: %s" % start

        if self.lexer is None : 
            lextab=self.__class__.__name__+"_lex"
            lkwargs = {'debug':debug, 'lextab':lextab }
            print self
            self.lexer = lex.lex(object=self, **lkwargs)
        if self.parser is None :
            tabmodule=self.__class__.__name__+"_yacc_"+start
            pkwargs = {'outputdir':parserspath, 'debug':debug, 'tabmodule':tabmodule, 'start':start, 'method':method }
            self.parser = yacc.yacc(module=self, **pkwargs)
        
    def parse(self, data, **kwargs):
        self.errorcount = 0
        return self.parser.parse(data, lexer=self.lexer, **kwargs)

class Token(Parsed):
    """ A class for token types, allows direct initialization from a string and type without checking
        to avoid unnecessary double parse of the string """
    pass
            
            

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
            raise ValueError, "cannot build Token Parser from pattern %r. you must set the _pattern attribute to a valid regular expression" % pattern
    
    def parse(self, data, **kwargs):
        self.errorcount = 0
        if self.parser.match(data) is not None :
            return Token(data, type=self._type, pos=0)
        else :
            warnings.warn ("%s is not matching %s pattern %r" % (data, self.__class__.name, self._pattern))
            self.errorcount += 1

# special purpose empty parser
class EmptyTokenParser(Parser):
    
    def build(self,**kwargs):
        pass
    
    def parse(self, data, **kwargs):
        self.errorcount = 0
        if data :
            self.errorcount = 1
        else :
            return Empty()

# derived TokenParser classes will be built for every token definition detected in Parser classes in this module

class EmptyParser(Parser):
    """ Parser for the empty production """
    
    start = 'Empty'
    def p_empty(self, p) :
        'Empty : '
        pass

def isParsedClass (x) :
    try :
        return issubclass(x, Parsed)
    except :
        return False  
def isParserClass (x) :
    try :
        return issubclass(x, Parser)
    except :
        return False   

class autoparsed(type):
    def __new__(mcl, classname, bases, classdict):
        newcls = super(autoparsed, mcl).__new__(mcl, classname, bases, classdict)
        print newcls
        try:
            # find the attribute _parser, which holds the parser class for this Parsed type
            parsercls = classdict['_parser']
        except KeyError:
            pass
        else:
            classNameReg = re.compile('[a-zA-Z][a-zA-Z0-9]*')
            if isParserClass(parsercls):
                # automatically set the start attribute to the name of this class
                if 'start' not in parsercls.__dict__:
                    setattr( parsercls, 'start', classname )

                accepts_set= set(classdict.get('_accepts', []) )
                for name, obj in parsercls.__dict__.items() :
                    # print "class %s has attribute %s" % (parsercls.__name__, m)
                    if name.startswith('p_') :
                        k = name[2:]
                        if isinstance(obj, basestring) :
                            v = obj
                            needsWrapping = True
                        elif inspect.isfunction(obj) or inspect.ismethod(obj) :
                            v = inspect.getdoc(obj)
                            needsWrapping = False
                        else :
                            raise SyntaxError, "Token definition %s defines neither a string nor a function, unable to parse" % name
                        
                        # process the docstring
                        accepts = []
                        colonSplit = [ x.strip() for x in v.split(':')]
                        if len(colonSplit) == 1:
                            v = classname + ' : ' + v
                            colonSplit = [classname, colonSplit[0] ]
                            
                        if len(colonSplit) ==2 and colonSplit[0] != '':
                            pipeSplit = [ x.strip() for x in colonSplit[1].split('|') ]
                            for grp in pipeSplit:
                                accepts += [ x for x in grp.split() if classNameReg.match(x) and x!=classname ]
                        
                        accepts_set.update( accepts )
                        
                        if needsWrapping:
                            def p_func(self, p):
                                p[0] = newcls( *p[1:len(p)] )
                            p_func.__name__ = name
                            p_func.__doc__ = v
                            print "overwriting %s._parser.%s with yacc function: %r" % ( classname, name, v)
                            setattr(parsercls, name, p_func)
#                        k = m[0][2:]
#                        if k in tokensDict :
#                            warnings.warn("Token %s redefined in Parser %s" % (k, parser), UserWarning)
#                        tokensDict[k] = v
                
                setattr(newcls, '_accepts', tuple(accepts_set) )
                
        
        return newcls

def _getTokens(parsercls):
    tokensDict={}
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
    return tokensDict
 
# do it       
#_addedTokenClasses =_createTokenClasses(debug=verbose())

# Build a dict of all existing Parser and Parsed classes in this module
class ParsedClasses(dict) :
    __metaclass__ =  metaStatic

    
#def parsedClasses(module):  
#    return dict(inspect.getmembers(module, isParsedClass))
## Stores it at import so that the inspect method isn't recalled at each query
#ParsedClasses(parsedClasses())

class ParserClasses(dict) :
    __metaclass__ =  metaStatic

            
#def parserClasses(module): 
#    return dict(inspect.getmembers(module, isParserClass))
## Stores it at import so that the inspect method isn't recalled at each query
#ParserClasses(parserClasses())

# cache out a dictionary of all Parsed and Parser classes, and create token classes
def process(module=None):
    
    if module:
        # User supplied a module object.
        if isinstance(module, types.ModuleType):
            module_dict = module.__dict__          
#        elif isinstance(module, _INSTANCETYPE):
#            _items = [(k,getattr(module,k)) for k in dir(module)]
#            ldict = { }
#            for i in _items:
#                ldict[i[0]] = i[1]
        else:
            raise ValueError,"Expected a module"
        
    else:
        # No module given.  We might be able to get information from the caller.
        # Throw an exception and unwind the traceback to get the globals
        
        try:
            raise RuntimeError
        except RuntimeError:
            e,b,t = sys.exc_info()
            f = t.tb_frame
            f = f.f_back           # Walk out to our calling function
            module_dict = f.f_globals    # Grab its globals dictionary
    
    #_createTokenClasses(ldict, debug=verbose() )
    
    parserDict = {}
    parsedDict = {}
    tokensDict = {}
    for name, obj in module_dict.iteritems():
        if isParserClass(obj):
            parserDict[name]=obj
            tokensDict.update( _getTokens(obj) )
            
            parser = name
            parsercls = obj
            #parsercls = ParserClasses[parser]

        elif isParsedClass(obj):
            parsedDict[name]=obj
            if hasattr(obj, '_parser'):
                if isParserClass(obj._parser):
                    tokensDict.update( _getTokens(obj._parser) )
                    
    for token in tokensDict :
        pattern = tokensDict[token]
        parsedName = token
        parserName = token+"Parser"
        #if debug : 
        print "adding classes %s and %s for token %s of pattern r'%s'" % (parsedName, parserName, token, pattern)         
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
        module_dict[parsedName] = ThisToken
        module_dict[parserName] = ThisTokenParser
        parsedDict[parsedName] = ThisToken
        parserDict[parserName] = ThisTokenParser   
          
    ParserClasses( parserDict )
    ParsedClasses( parsedDict  )
    
        
