"Parser for Maya.env"

import sys, os, os.path, logging
#import external.ply.lex as lex
try:
    from pymel.util.external.ply import lex
except ImportError:
    from ply import lex

from pymel.mayautils import getMayaAppDir

_logger = logging.getLogger(__name__)

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
    t_right_ignore = '[ \t]+'
    # careful, there seems to be a nasty bug where ply.lex takes $ as its literal value instead of in the 'end of line' meaning ?
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
        warnings.warn ( "Double '=' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), ExecutionWarning)
        # skip whole line
        self.lexer.begin('cancel')
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)
    def t_end_ASSIGN(self, t):
        r'[ \t]*=[ \t]*'
        warnings.warn ( "More than one '=' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), ExecutionWarning)
        # skip whole line
        self.lexer.begin('cancel')
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)
    # r-values will be parsed again depending on os name
    def t_end_VALUE(self, t):
        r'[^=^\n^#]+'
        # one and only one VALUE on right side of ASSIGN
        warnings.warn ( "More than one value at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (self.lexer.lineno), ExecutionWarning)
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
        warnings.warn ( "Illegal character '%s' at line %i, ignored" % (t.value[0], self.lexer.lineno), ExecutionWarning)
        self.lexer.skip(1)
    def t_INITIAL_error(self, t):
        warnings.warn ( "Invalid VAR name '%s' at line %i, line ignored" % (t.value[0], self.lexer.lineno), ExecutionWarning)
        # skip whole line
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)
    def t_left_error(self, t):
        warnings.warn ( "Illegal value '%s' at line %i, format for a Maya.env line is <VAR> = <value>, line ignored" % (t.value[0], self.lexer.lineno), ExecutionWarning)
        # skip whole line
        while self.lexer.lexpos<self.lexer.lexlen and self.lexer.lexdata[self.lexer.lexpos] != '\n' :
            self.lexer.skip(1)
    def t_right_error(self, t):
        warnings.warn ( "Illegal value '%s' at line %i, line ignored" % (t.value[0], self.lexer.lineno), ExecutionWarning)
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
    t_ignore = '^[ \t]+'

    def t_SEP(self, t):
        r':;'
        if t.value==';' and self.os != 'nt' :
            # t.value = ':'
            if not self.warn.SEP :
                warnings.warn ( "Line %i: the ';' separator should only be used on nt os, on linux or osx use ':' rather" % self.lexer.lineno, ExecutionWarning)
                self.warn.SEP = True
        return t
    # Valid l-values are env var names, must come first in line (INITIAL sate)
    def t_RVAR1(self, t) :
        r'\$[^\\^/^:^*^"^<^>^|^=^ ^\t^\n^#^$]+'
        if self.os == 'nt' :
            if not self.warn.VAR :
                warnings.warn ( "Line %i: $VAR should be used on linux or osx, \%VAR\% on nt" % self.lexer.lineno, ExecutionWarning)
                self.warn.VAR = True
        v = t.value.lstrip('$')
        if self.symbols.has_key(v) :
            t.value = self.symbols[v]
        return t
    def t_RVAR2(self, t) :
        r'\%[^\\^/^:^*^"^<^>^|^=^ ^\t^\n^#]+\%'
        if self.os != 'nt' :
            if not self.warn.VAR :
                warnings.warn ( "Line %i: $VAR should be used on linux or osx, \%VAR\% on nt" % self.lexer.lineno, ExecutionWarning)
                self.warn.VAR = True
        v = t.value.strip('%')
        if self.symbols.has_key(v) :
            t.value = self.symbols[v]
        return t
    # Assignation sign, ignore spaces around it
    def t_PATHSEP(self, t) :
        r'\/|\\'
        if self.os != 'nt' and t.value == '\\':
            if not self.warn.PATH :
                warnings.warn ( "Line %i: the '\\' path separator should only be used on nt, on linux or osx use '/' rather" % self.lexer.lineno, ExecutionWarning)
                self.warn.PATH = True
        return t
    # we just return the rest as-is
    # TODO: warnings if it's a path and path doesn't exist ?
    # Would need to differentiate % or $ wether we are on nt or not but py.lex
    # handles definitions strangely, like they are static / source time evaluated
    # removed % from the list of excluded characters as some definitions seem to use it :
    # $RMSTREE/icons/%B
    # TODO : Never seen it elsewhere, must check it doesn't collide with %VARNAME% on NT
    def t_VALUE(self, t):
            r'[^=^\n^#^$]+'
            return t

    def t_error(self, t):
        warnings.warn ( "Illegal character '%s' at line %i, ignored" % (t.value[0], self.lexer.lineno), ExecutionWarning)
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
    symbols = environ.copy()
    newsymbols = {}
    # first level lexer
    envLex = EnvLex()
    envLex.build()
    sep = os.path.pathsep
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
                    newvalue = None
                    action = 'Ignore'
                    if symbols.has_key(var) :

                        # For these variables ONLY, maya will append the value in maya.env to an exisiting environment variable
                        # (Default is for already defined value to override value in maya.env)
                        # (note the LACK of PYTHONPATH here... boo!)
                        if var in ('MAYA_SCRIPT_PATH',
                                   'MAYA_PLUG_IN_PATH',
                                   'MAYA_MODULE_PATH',
                                   'XBMLANGPATH'):
                            newvalue = self.symbols[var]+sep
                            action = 'Add'
                    else :
                        newvalue = ''
                        action = 'Set'
                    if newvalue is not None :
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
                        symbols[var] = newvalue
                        newsymbols[var] = newvalue
                    if action == 'Set' :
                        print u"%s set to value %s" % (var, unicode(newvalue))
                    elif action == 'Add' :
                        print u"%s was already set, appending value: %s" % (var, unicode(newvalue))
                    elif action == 'Ignore' :
                        print u"%s was already set, ignoring line: %s" % (var, unicode(tok.value))
                var = value = None
            elif tok.type=='CANCEL' :
                print "Line was ignored due to parsing errors: %s" % unicode(tok.value)
                var = value = None
            else :
                pass

    return newsymbols

# parse the Maya.env file and set the environment variables and python path accordingly
def parseMayaenv(envLocation=None, version=None) :
    """ parse the Maya.env file and set the environement variablas and python path accordingly.
        You can specify a location for the Maya.env file or the Maya version"""
    name = 'Maya.env'


    envPath = None
    if envLocation :
        envPath = envLocation
        if not os.path.isfile(envPath) :
            envPath = os.path.join(envPath, name)

    # no Maya.env specified, we look for it in MAYA_APP_DIR
    if not envPath or not envPath.isfile() :
        maya_app_dir = getMayaAppDir()
        if not maya_app_dir:
            _logger.warn("Neither HOME nor MAYA_APP_DIR is set, unable to find location of Maya.env")
            return False

        # try to find which version of Maya should be initialized
        if not version :
            # try to query version, will only work if reparsing env from a working Maya
            version = Version.installName()
            if version is None:
                # if run from Maya provided mayapy / python interpreter, can guess version
                _logger.debug("Unable to determine which verson of Maya should be initialized, trying for Maya.env in %s" % maya_app_dir)
        # look first for Maya.env in 'version' subdir of MAYA_APP_DIR, then directly in MAYA_APP_DIR
        if version and os.path.isfile(os.path.join(maya_app_dir, version, name)) :
            envPath = os.path.join(maya_app_dir, version, name)
        else :
            envPath = os.path.join(maya_app_dir, name)

    # finally if we have a possible Maya.env, parse it
    if os.path.isfile(envPath) :
        try :
            envFile = open(envPath)
        except :
            _logger.warn ("Unable to open Maya.env file %s" % envPath )
            return False
        success = False
        try :
            envTxt = envFile.read()
            envVars = parse(envTxt)
            # update env vars
            for v in envVars :
                #_logger.debug("%s was set or modified" % v)
                os.environ[v] = envVars[v]
            # add to syspath
            if envVars.has_key('PYTHONPATH') :
                #_logger.debug("sys.path will be updated")
                plist = os.environ['PYTHONPATH'].split(os.pathsep)
                for p in plist :
                    if not p in sys.path :
                        sys.path.append(p)
            success = True
        finally :
            envFile.close()
            return success
    else :
        if version :
            print"Found no suitable Maya.env file for Maya version %s" % version
        else :
            print"Found no suitable Maya.env file"
        return False