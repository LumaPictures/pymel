import sys, os
import ply
import ply.lex as lex
import warnings

# lexer and parser for the Maya.env file

# first level lexer : form LVAR ASSIGN VALUE, then second level parsing of VALUE
# variables substitution are done as in Maya, taking only into account already defined vars
# when line is encountered
class EnvLex :
    """ ply.lex lexer class to parse Maya.env file """
    
    def __init__(self):
        self.states = ( ('left','exclusive'), ('right','exclusive'), ('end','exclusive'), ('cancel','exclusive') )
        self.line = '' 
    def build(self, **kwargs):
        self.lexer = lex.lex(object=self,**kwargs)
            
    tokens = (
        'COMMENT',
        'ASSIGN',
        'VAR',
        'VALUE',
        'OK',
        'CANCEL',
        'newline'
    )

    # First level parsing : form LVAR ASSIGN VALUE
    t_ANY_ignore_COMMENT = r'\#[^\n]*'
    # Ignore starting spaces only
    t_INITIAL_ignore = '^[ \t]+'
    t_left_ignore = '[ \t]+'
    t_right_ignore = '[ \t]+$'
    t_end_ignore = '[ \t]+$'
    t_cancel_ignore = '[^\n]+'
    # Valid l-values are env var names, must come first in line (INITIAL sate)
    def t_VAR(self, t) :
        r'[^\\^\/^\:^\*^\"^\<^\>^\|^=^ ^\t^\n^#]+'
        # VAR can only be on left side of ASSIGN (INITIAL parser state)
        self.lexer.begin('left')
        self.line += t.value
        return t
    # Assignation sign, ignore spaces around it
    def t_left_ASSIGN(self, t):
        r'[ \t]*=[ \t]*'
        self.lexer.begin('right')
        t.value = t.value.strip()
        self.line += t.value
        return t
    # r-values will be parsed again depending on os name        
    def t_right_VALUE(self, t):
        r'[^=^\n^#]+'
        # one and only one VALUE on right side of ASSIGN
        self.lexer.begin('end')
        self.line += t.value
        return t
    # More than one equal sign per line would be an error
    def t_right_ASSIGN(self, t):
        r'[ \t]*=[ \t]*'
        warnings.warn ( "Double '=' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), UserWarning)
        # skip whole line
        self.lexer.begin('cancel')
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)          
    def t_end_ASSIGN(self, t):
        r'[ \t]*=[ \t]*'
        warnings.warn ( "More than one '=' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), UserWarning)
        # skip whole line
        self.lexer.begin('cancel')
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)        
    # r-values will be parsed again depending on os name        
    def t_end_VALUE(self, t):
        r'[^=^\n^#]+'
        # one and only one VALUE on right side of ASSIGN
        warnings.warn ( "More than one value at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), UserWarning)
        # skip whole line
        self.lexer.begin('cancel')
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)                           
    # Ignore ending spaces and count line no
    def t_ANY_newline(self, t):
        r'[ \t]*\n+'
        st = self.lexer.current_state()
        if st == 'end' :
            t.type = 'OK'
            t.value = self.line
        elif st == 'INITIAL' :
            pass
        else :
            t.type = 'CANCEL'
            v = ''
            i = self.lexer.lexpos-2
            while i>0 and self.lexer.lexdata[i] != '\n' :
                v = self.lexer.lexdata[i] + v
                i -= 1
            t.value = v
        self.lexer.begin('INITIAL')
        self.line = ''
        # Cound nb of new lines, removing white space
        self.lexer.lineno += len(t.value.lstrip(' \t'))          
        return t
    # Error handling rules
    def t_ANY_error(self, t):
        warnings.warn ( "Illegal character '%s' at line %i, ignored" % (t.value[0], self.lexer.lineno), UserWarning)        
        self.lexer.skip(1)
    def t_INITIAL_error(self, t):
        warnings.warn ( "Invalid VAR name '%s' at line %i, line ignored" % (t.value[0], self.lexer.lineno), UserWarning)
        # skip whole line
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)      
    def t_left_error(self, t):
        warnings.warn ( "Illegal value '%s' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (t.value[0], self.lexer.lineno), UserWarning)
        # skip whole line
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)        
    def t_right_error(self, t):
        warnings.warn ( "Illegal value '%s' at line %i, line ignored" % (t.value[0], self.lexer.lineno), UserWarning)
        # skip whole line
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)
                                 
    # Test it
    def test(self,data):
        self.lexer.input(data)
        while 1:
             tok = self.lexer.token()
             if not tok: break
             print tok

# second level lexer : os dependant parsing of values and variable substitution
class ValueLex :
    """ second level lexer to parse right-values depending on os name """
    
    class Warn :
        """ a ValueLex subclass to reset warning count """
        def __init__(self):
            self.SEP = False
            self.VAR = False
            self.PATH = False
            
    def __init__(self, symbols, osname = os.name):
        self.os = osname
        self.symbols = symbols
        self.line = 0
        self.warn = ValueLex.Warn()
    def build(self, **kwargs):
        self.lexer = lex.lex(object=self,**kwargs)
    
    tokens = (
        'SEP',
        'RVAR1',
        'RVAR2',
        'PATHSEP',
        'VALUE'
    )
    # ignore ending space
    t_ignore = '[ \t]+$'
    
    def t_SEP(self, t):
        r':;'
        if t.value==';' and self.os != 'nt' :
            # t.value = ':'
            if not self.warn.SEP :
                warnings.warn ( "Line %i: the ';' separator should only be used on nt os, on linux or osx use ':' rather" % self.lexer.lineno, UserWarning)
                self.warn.SEP = True
        return t   
    # Valid l-values are env var names, must come first in line (INITIAL sate)
    def t_RVAR1(self, t) :
        r'\$[^\\^\/^\:^\*^\"^\<^\>^\|^=^ ^\t^\n^#]+'
        if self.os == 'nt' :
            if not self.warn.VAR :
                warnings.warn ( "Line %i: $VAR should be used on linux or osx, \%VAR\% on nt" % self.lexer.lineno, UserWarning)
                self.warn.VAR = True
        v = t.value.lstrip('$')         
        if self.symbols.has_key(v) :
            t.value = self.symbols[v]
        return t
    def t_RVAR2(self, t) :
        r'\%[^\\^\/^\:^\*^\"^\<^\>^\|^=^ ^\t^\n^#]+\%'
        if self.os != 'nt' :
            if not self.warn.VAR :
                warnings.warn ( "Line %i: $VAR should be used on linux or osx, \%VAR\% on nt" % self.lexer.lineno, UserWarning)
                self.warn.VAR = True         
        v = t.value.strip('%')         
        if self.symbols.has_key(v) :
            t.value = self.symbols[v]
        return t   
    # Assignation sign, ignore spaces around it
    def t_PATHSEP(self, t) :
        r'\/|\\'
        if self.os != 'nt' :
            if not self.warn.PATH :
                warnings.warn ( "Line %i: the '\\' path separator should only be used on nt os, on linux or osx use '/' rather" % self.lexer.lineno, UserWarning)
                self.warn.PATH = True
        return t               
    # we just return the rest as-is
    # TODO: warnings if it's a path and path doen'st exist ?        
    def t_VALUE(self, t):
        r'[^=^\n^#]+'
        return t
       
    def t_error(self, t):
        warnings.warn ( "Illegal character '%s' at line %i, ignored" % (t.value[0], self.lexer.lineno), UserWarning)        
        self.lexer.skip(1)
        
    # Test it
    def test(self,data):
        self.lexer.input(data)
        while 1:
             tok = self.lexer.token()
             if not tok: break
             print tok 
    
# Do the 2 level parse of a Maya.env format text and return a symbol table of the declared env vars
def parse(text, environ=os.environ, osname=os.name):
    symbols = environ
    # first level lexer
    envLex = EnvLex()
    envLex.build()
    if osname == 'nt' :
        sep = ';'
    else :
        sep = ':'
    # easier if we have a closing newline before eof
    if not text.endswith('\n') :
        text += '\n'
    envLex.lexer.input(text)
    # second level lexer for values
    valueLex =  ValueLex(symbols, osname)
    valueLex.build() 
    tok = 'dummy'       
    while tok:
        tok = envLex.lexer.token()
        if tok is not None :
            if tok.type=='VAR' :
                var = tok.value
            elif tok.type=='VALUE' :
                value = tok.value
            elif tok.type=='OK' :          
                # secondary parsing on value depending on os
                # update defined env vars up to now
                if var is not None :
                    # It's quite hard to guess what Maya does with pre-existant env vars when they are also declared
                    # in Maya.env. It seems to ignore Maya,env in most of these cases, except for MAYA_SCRIPT_PATH
                    # where it will add the content o Maya.env to the predefined var
                    # for PATH, MAYA_PLUGIN_PATH and LD_LIBRARY_PATH on linux it seems to add his own stuff, disreguarding
                    # Maya.env if the the variable was pre-existant. If you notice (or want) different behaviors you can 
                    # change it here                    
                    if symbols.has_key(var) :
                        if var=='MAYA_SCRIPT_PATH' :
                            newvalue = self.symbols[var]+sep
                            print u"Value will be added to pre-existing value of %s: %s" % (var, unicode(value))                              
                        else :
                            newvalue = None
                            print u"%s was already set, ignoring line: %s" % (var, unicode(tok.value))  
                    else :
                        newvalue = ''
                    if newvalue is not None :
                        print "Setting %s" % var
                        # only display warning for a better feedback there,
                        # as even if it makes no sense we can in all cases affect the value to the env var                    
                        valueLex.symbols = symbols
                        valueLex.lexer.input(value)
                        valueLex.lexer.lineno = tok.lineno
                        valueLex.warn = ValueLex.Warn()
                        vtok = 'dummy'
                        while vtok:
                            vtok = valueLex.lexer.token()
                            if vtok is not None :                               
                                newvalue += vtok.value
                        print u"%s set to %s" % (var, unicode(newvalue))
                        symbols[var] = newvalue
                var = value = None
            elif tok.type=='CANCEL' :
                print "Line was ignored due to parsing errors: %s" % tok.value
                var = value = None           
            else :
                pass
        
    return symbols