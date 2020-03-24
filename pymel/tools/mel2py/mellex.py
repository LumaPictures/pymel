from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# ----------------------------------------------------------------------
# clex.py
#
# A lexer for ANSI C.
# ----------------------------------------------------------------------

import sys
sys.path.insert(0, "../..")

try:
    import pymel.util.external.ply.lex as lex
except ImportError:
    import ply.lex as lex

# Reserved words

# removed 'AUTO', 'CONST',  'CHAR', 'DOUBLE','ENUM', 'EXTERN', 'LONG', 'REGISTER', 'SHORT', 'SIGNED', 'STATIC', 'STRUCT', 'TYPEDEF','UNION', 'UNSIGNED', 'VOID', 'VOLATILE','GOTO',


reserved = (
    'BREAK', 'CASE', 'CONTINUE', 'DEFAULT', 'DO',
    'ELSE', 'FALSE', 'FLOAT', 'FOR', 'GLOBAL', 'IF', 'IN', 'INT', 'NO', 'ON', 'OFF', 'PROC',
    'RETURN', 'STRING', 'SWITCH', 'TRUE', 'VECTOR', 'MATRIX',
    'WHILE', 'YES',
)

tokens = reserved + (
    # Literals (identifier, integer constant, float constant, string constant, char const)
    'ID', 'VAR', 'ICONST', 'FCONST', 'SCONST',
    #'LOBJECT', 'ROBJECT',

    # Operators (+,-,*,/,%,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'NOT', 'CROSS',
    'LOR', 'LAND',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

    # Assignment (=, *=, /=, %=, +=, -=, ^=)
    'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
    'CROSSEQUAL',

    # Vector Component
    'COMPONENT',

    # Increment/decrement (++,--)
    'PLUSPLUS', 'MINUSMINUS',

    # Conditional operator (?)
    'CONDOP',

    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'SEMI', 'COLON',
    'CAPTURE',
    'LVEC', 'RVEC',

    # Comments
    'COMMENT', 'COMMENT_BLOCK',

    # Ellipsis (..)
    'ELLIPSIS',
)

# Completely ignored characters
t_ignore = ' \t\x0c'

# Newlines


def t_NEWLINE(t):
    r'\n+|\r+'
    t.lexer.lineno += t.value.count("\n")


# Operators
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
#t_OR               = r'\|'
#t_AND               = r'&'
t_NOT = r'!'
t_CROSS = r'\^'
t_LVEC = r'<<'
t_RVEC = r'>>'
t_LOR = r'\|\|'
t_LAND = r'&&'
t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='

# Assignment operators

t_EQUALS = r'='
t_TIMESEQUAL = r'\*='
t_DIVEQUAL = r'/='
t_MODEQUAL = r'%='
t_PLUSEQUAL = r'\+='
t_MINUSEQUAL = r'-='
t_CROSSEQUAL = r'^='

# Increment/decrement
t_PLUSPLUS = r'\+\+'
t_MINUSMINUS = r'--'

# ?
t_CONDOP = r'\?'

# Delimeters
#t_LBRACKET           = r'\['
#t_RBRACKET           = r'\]'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
#t_SEMI               = r';'
t_COLON = r':'
#t_COMPONENT           = r'\.[xyz]'

# Identifiers and reserved words

reserved_map = {}
for r in reserved:
    reserved_map[r.lower()] = r

# print reserved_map

id_state = None
suspend_depth = 0


def t_LPAREN(t):
    r'\('
    return t


def t_RPAREN(t):
    r'\)'
    return t

# def t_LOBJECT(t):
#    r'([|]?([:]?([.]?[A-Za-z_][\w]*)+)+)+?\['
#    return t

# def t_ROBJECT(t):
#    r'\]([|]?([:]?([.]?[A-Za-z_][\w]*)+)+)+?'
#    return t


def t_LBRACKET(t):
    r'\['
    return t


def t_RBRACKET(t):
    r'\]'
    return t


def t_CAPTURE(t):
    r'`'
    return t


def t_SEMI(t):
    r';'
    return t


def t_VAR(t):
    r'\$[A-Za-z_][\w_]*'
    return t


def t_COMPONENT(t):
    r'\.[xyz]'
    return t


def t_ELLIPSIS(t):
    r'\.\.'
    return t


def t_ID(t):
    # Starts with a letter or a pipe
    #
    # |path|myPrfx_1:myNode_1.myAttr_1[0].subAttr   or  ..
    # r'[A-Za-z_|](?:[\w_\.:|]|(?:\[\d+\]))*|\.\.'
    # r'[A-Za-z_|]([\w_\.:|]|(\[\d+\]))*|\.\.'
    # r'[A-Za-z_|][\w_\.:|]*(?:[\w_]|(?:\[\d+\]))+|[A-Za-z_]|\.\.'
    # '(%(id)s)*([.|](%(id)s)+)*[.|]?*|\.\.' % {'id': '[A-Za-z_][\w:]*(\[\d+\])?'}

    #   |    :    .     idName        [0]
    # r'([|]?([:]?([.]?[A-Za-z_][\w]*(\[\d+\])?)+)+)+?|\.\.'
    #   |    :    .     idName        [0] or [$var]
    # r'([|]?([:]?([.]?[A-Za-z_][\w]*(\[(\d+)|(\$[A-Za-z_][\w_]*)\])?)+)+)+?|\.\.'

    # r'[A-Za-z_][\w]*'
    r'([|]?([:]?([.]?[A-Za-z_][\w]*)+)+)+?'
    t.type = reserved_map.get(t.value, "ID")
    return t

# def t_OBJECT(t):
#
#    #   |    :    .     idName        [0]
#    #r'([|]?([:]?([.]?[A-Za-z_][\w]*(\[\d+\])?)+)+)+?|\.\.'
#
#    #r'[A-Za-z_][\w]|\.\.'
#    r'([|]?([:]?([.]?[A-Za-z_][\w]*)+)+)+?'
#    return t

# Integer literal
#t_ICONST = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'
t_ICONST = r'(0x[a-fA-F0-9]*)|\d+'

# Floating literal
# t_FCONST = r'((\d+)?(\.\d+)(e(\+|-)?(\d+))?|(\d+)e(\+|-)?(\d+))([lL]|[fF])?' # does not allow  1.
t_FCONST = r'(((\d+\.)(\d+)?|(\d+)?(\.\d+))(e(\+|-)?(\d+))?|(\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
# t_SCONST = r'\"([^\\\n]|(\\.))*?\"' # does not allow \ for spanning multiple lines
#t_SCONST = '\"([^\n]|\r)*\"'
#t_SCONST = r'"([^\n]|\\\n)*?"'
t_SCONST = r'"([^\\\n]|(\\.)|\\\n)*?"'

# Comments


def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/|/\*(.|\n)*?$'
    # r'/\*(.|\n)*?\*/'

    # r'/\*(.|\n)*?\*/|/\*(.|\n)*?$'
    # the second half of this regex is for matching block comments that
    # are terminated by the end of the file instead of by */

    t.lexer.lineno += t.value.count('\n')
    return t


def t_COMMENT(t):
    r'//.*'
    #t.lexer.lineno += t.value.count('\n')
    return t

# def t_INVALID(t):
#    r'[.~\|\'"]'
#    # these symbols cannot be used on their own,
#    # without this entry, they would simply be ignored rather than raising an error
#    return t

# def t_error(t):
#    #print "Illegal character %s" % repr(t.value[0])
#    t.lexer.skip(1)

# def t_error(t):
#    return t

#lexer = lex.lex(optimize=1)
#lexer = lex.lex()
# if __name__ == "__main__":
#    lex.runmain(lexer)
