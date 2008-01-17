# ----------------------------------------------------------------------
# clex.py
#
# A lexer for ANSI C.
# ----------------------------------------------------------------------

import sys
sys.path.insert(0,"../..")

import ply.lex as lex

# Reserved words

#removed 'AUTO', 'CONST',  'CHAR', 'DOUBLE','ENUM', 'EXTERN', 'LONG', 'REGISTER', 'SHORT', 'SIGNED', 'STATIC', 'STRUCT', 'TYPEDEF','UNION', 'UNSIGNED', 'VOID', 'VOLATILE','GOTO',


reserved = (
	'BREAK', 'CASE', 'CONTINUE', 'DEFAULT', 'DO',
	'ELSE', 'FALSE', 'FLOAT', 'FOR', 'GLOBAL', 'IF', 'IN', 'INT', 'ON', 'OFF', 'PROC',
	'RETURN', 'STRING', 'SWITCH', 'TRUE', 'VECTOR',
	'WHILE',
	)

tokens = reserved + (
	# Literals (identifier, integer constant, float constant, string constant, char const)
	'ID', 'VAR', 'ICONST', 'FCONST', 'SCONST',

	# Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
	'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
	'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT',
	'LOR', 'LAND',
	'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
	
	# Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
	'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
	'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL',

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

	# Comments
	'COMMENT', 'COMMENT_BLOCK',
	
	# Ellipsis (...)
	#'ELLIPSIS',
	)

# Completely ignored characters
t_ignore		   = ' \t\x0c'

# Newlines
def t_NEWLINE(t):
	r'\n+|\r+'
	t.lexer.lineno += t.value.count("\n")


		
# Operators
t_PLUS			   = r'\+'
t_MINUS			= r'-'
t_TIMES			   = r'\*'
t_DIVIDE		   = r'/'
t_MOD			   = r'%'
t_OR			   = r'\|'
t_AND			   = r'&'
t_NOT			   = r'!'
t_XOR			   = r'\^'
t_LSHIFT		   = r'<<'
t_RSHIFT		   = r'>>'
t_LOR			   = r'\|\|'
t_LAND			   = r'&&'
t_LT			   = r'<'
t_GT			   = r'>'
t_LE			   = r'<='
t_GE			   = r'>='
t_EQ			   = r'=='
t_NE			   = r'!='

# Assignment operators

t_EQUALS		   = r'='
t_TIMESEQUAL	   = r'\*='
t_DIVEQUAL		   = r'/='
t_MODEQUAL		   = r'%='
t_PLUSEQUAL		   = r'\+='
t_MINUSEQUAL	   = r'-='
t_LSHIFTEQUAL	   = r'<<='
t_RSHIFTEQUAL	   = r'>>='
t_ANDEQUAL		   = r'&='
t_OREQUAL		   = r'\|='
t_XOREQUAL		   = r'^='

# Increment/decrement
t_PLUSPLUS		   = r'\+\+'
t_MINUSMINUS	   = r'--'

# ?
t_CONDOP		   = r'\?'

# Delimeters
#t_LBRACKET		   = r'\['
#t_RBRACKET		   = r'\]'
t_LBRACE		   = r'\{'
t_RBRACE		   = r'\}'
t_COMMA			   = r','
#t_SEMI			   = r';'
t_COLON			   = r':'


# Identifiers and reserved words

reserved_map = { }
for r in reserved:
	reserved_map[r.lower()] = r
	
#print reserved_map

id_state = None
suspend_depth = 0

			
def t_LPAREN(t):
	r'\('
	return t
	
def t_RPAREN(t):
	r'\)'
	return t

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
	t.value = t.value[1:]
	return t

def t_ID(t):
	# Starts with a letter or a pipe
	#
	#
	# |path|myPrfx_1:myNode_1.myAttr_1[0].subAttr   or  ..
	r'[A-Za-z_|](?:[\w_\.:|]|(?:\[\d+\]))*|\.\.'
	#r'[A-Za-z_|][\w_\.:|]*(?:[\w_]|(?:\[\d+\]))+|[A-Za-z_]|\.\.'
	t.type = reserved_map.get(t.value,"ID")
	return t

	
	
# Integer literal
t_ICONST = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'

# Floating literal
t_FCONST = r'((\d+)?(\.\d+)(e(\+|-)?(\d+))?|(\d+)e(\+|-)?(\d+))([lL]|[fF])?'

# String literal
t_SCONST = r'\"([^\\\n]|(\\.))*?\"'
#t_SCONST = '\"([^\n]|\r)*\"'

# Comments
def t_COMMENT_BLOCK(t):
	r'/\*(.|\n)*?\*/|/\*(.|\n)*?$'
	#r'/\*(.|\n)*?\*/'
	
	#r'/\*(.|\n)*?\*/|/\*(.|\n)*?$'
	# the second half of this regex is for matching block comments that
	# are terminated by the end of the file instead of by */
	
	#t.lineno += t.value.count('\n')
	return t
	
def t_COMMENT(t):
	r'//.*'
	#t.lineno += t.value.count('\n')
	return t

#def t_INVALID(t):
#	r'[.~\|\'"]'
#	# these symbols cannot be used on their own, 
#	# without this entry, they would simply be ignored rather than raising an error
#	return t
	
#def t_error(t):
#	#print "Illegal character %s" % repr(t.value[0])
#	t.lexer.skip(1)
	
#lexer = lex.lex(optimize=1)
lexer = lex.lex()
if __name__ == "__main__":
	lex.runmain(lexer)

	



