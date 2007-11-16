#! /usr/local/bin/python

"""

Created from the ansi c example included with ply, which is based on the grammar in K&R, 2nd Ed.

"""




import sys, os, re, path
import mellex
from ply import *

try:
	from pymel import *
except ImportError:
	print "maya.cmds module cannot be found. be sure to run this script through maya and not from the command line. Continuing, but without command support"
	
class token(str):
	def __new__(cls, val, type, globalVar=False):
		self=str.__new__(cls,val)		
		self.type = type
		self.globalVar = globalVar
		return self


def substring(x, t):
	"""convert:
			substring( var, 2, (len(var)) )
		to:
			var[1:]
			
		or:
			substring( var, 3, var2 )
		to:
			var[1:var2]
			
		or:
			substring( var, 3, var2 )
		to:
			var[1:var2]			
			"""
	def makeSlice( var, arg):
		if arg.startswith('(') and arg.endswith(')'):
			arg = arg[1:-1]	
		try:
			return str( int(arg)-1 )						
		except ValueError:
			m = re.match( '\(*\s*len\s*\(\s*' + var + '\s*\)\s*\)*(.*)', arg )
			if m:
				return m.group(1)

			else:
				return '%s-1' % arg
				

	start = makeSlice(x[0], x[1])
	end = makeSlice(x[0], x[2])
	
	return '%s[%s:%s]' % (x[0], start, end )
			
# dictionary of functions used to remap procedures to python commands
proc_remap = { 

		# strings
		'capitalizeString' 		: lambda x, t: '%s.capitalize()' 	% (x[0]),	
		'strip' 				: lambda x, t: '%s.strip()' 		% (x[0]),
		'stringArrayToString' 	: lambda x, t: '%s.join(%s)' 		% (x[1],x[0]),
		'stringArrayCatenate'	: lambda x, t: '%s + %s' 			% (x[0],x[1]),
		'stringArrayContains'	: lambda x, t: '%s in %s' 			% (x[0],x[1]),
		'stringArrayCount'		: lambda x, t: '%s.count(%s)'		% (x[1],x[0]),
		'stringArrayRemove'		: lambda x, t: '[x for x in %s if x not in %s]'	% (x[1],x[0]),
		'stringToStringArray'	: lambda x, t: '%s.split(%s)' 		% (x[0],x[1]),
		'startsWith'			: lambda x, t: '%s.startswith(%s)' 	% (x[0],x[1]),
		'endsWith'				: lambda x, t: '%s.endswith(%s)' 	% (x[0],x[1]),
		'tolower'				: lambda x, t: '%s.lower()' 		% (x[0]),
		'toupper'				: lambda x, t: '%s.upper()' 		% (x[0]),
		'substring'				: substring,

		# misc. keywords
		'size' 					: lambda x, t: 'len(%s)' 			% (', '.join(x)),				
		'print'					: lambda x, t: 'print %s' 			% (x[0]),
		'clear'					: lambda x, t: '%s=[]' 				% (x[0]),
		'eval'					: lambda x, t: 'mel.eval(%s)' 		% (x[0]),
		'sort'					: lambda x, t: 'sorted(%s)'			% (x[0]),
		
		# error handling
		'catch'					: lambda x, t: 'catch( lambda: %s )' % (x[0]),
		'catchQuiet'			: lambda x, t: 'catch( lambda: %s )' % (x[0]),

		# system
		'system'				: lambda x, t: ( 'os.system( %s )' 	% (x[0]), t.parser.used_modules.add('os') )[0],
		'exec'					: lambda x, t: ( 'os.popen2( %s )' 	% (x[0]), t.parser.used_modules.add('os') )[0],
		#'fopen'				: lambda x, t: 'open(%s)' % (', '.join(x)),
		#'fprint'				: lambda x, t: '%s.write(%s)' % (x[0], x[1]),
		#'fclose'				: lambda x, t: '%s.close(%s)' % (x[0], x[1]),
		#'fflush'				: lambda x, t: '%s.flush()' % (x[0]),
		#'fgetline'				: lambda x, t: '%s.readline()' % (x[0]),
		#'frewind'				: lambda x, t: '%s.seek(0)' % (x[0]),
		
		# no python equivalents
		#'fgetword'				: lambda x, t: '%s.seek(0)' % (x[0]),
		#'feof'					: lambda x, t: '%s.seek(0)' % (x[0]),
		#'fread'				: lambda x, t: '%s.seek(0)' % (x[0]),
		
		'filetest'				: lambda x, t: (  (  t.parser.used_modules.add('os'),  # add os module for access()
												{ 	'-r' : "MPath(%(path)s).access(os.R_OK)",
													'-l' : "MPath(%(path)s).islink()",
													'-w' : "MPath(%(path)s).access(os.W_OK)",
													'-x' : "MPath(%(path)s).access(os.X_OK)",
													'-f' : "MPath(%(path)s).isfile()",
													'-d' : "MPath(%(path)s).isdir()",
													'-h' : "MPath(%(path)s).islink()",
													'-f' : "MPath(%(path)s).exists() and path.path('%(path)s').getsize()",
													'-L' : "MPath(%(path)s).islink()",
													}[ x[0] ] % { 'path' :x[1] }) 	
												)[1], 
												
		'sysFile'				: lambda x, t: { 	'-delete'	: "MPath(%(path)s).remove()",
													'-del'		: "MPath(%(path)s).remove()",
													'-rename'	: "MPath(%(path)s).move(%(param)s)",
													'-ren'		: "MPath(%(path)s).move(%(param)s)",
													'-move'		: "MPath(%(path)s).move(%(param)s)",
													'-mov'		: "MPath(%(path)s).move(%(param)s)",
													'-copy'		: "MPath(%(path)s).copy(%(param)s)",
													'-cp'		: "MPath(%(path)s).copy(%(param)s)",
													'-makeDir'	: "MPath(%(path)s).mkdir()",
													'-md' 		: "MPath(%(path)s).mkdir()",
													'-removeEmptyDir' : "MPath(%(path)s).removedirs()",
													'-red' 		: "MPath(%(path)s).removedirs()"
													}[ x[0] ] % { 'path' :x[-1], 'param':x[-2] }	
}

global_procs = {}
tag = '# script created by pymel.melparse.mel2py'
currentFiles = []
proc_module = {}


# Get the list of reserved words -- any variables or procedures that conflict with these keywords will be renamed with a trailing underscore
tokens = mellex.tokens
builtin_module = __import__('__main__').__builtins__
reserved= set( dir(builtin_module) )
reserved.update( ['and', 'assert', 'break', 'class', 'continue',
	'def', 'del', 'elif', 'else', 'except',
	'exec', 'finally' 	'for', 'from', 'global',
	'if', 'import', 'in', 'is', 'lambda',
	'not', 'or', 'pass', 'print', 'raise',
	'return', 'try', 'while'] )


def vprint(t, *args):
	if t.parser.verbose:
		print args
	
def assemble(t, funcname, separator='', matchFormatting=False):	
	
	#print "STARTING", lineno
	
	res = ''
			 
	if len(t) > 1:
		type = None
		tokens = []
		for i in range(1, len(t)):
			if i is not None:				
				tokens.append(t[i])
				try:
					if t[i].type:
						type = t[i].type
						#print 'assembled', funcname, p[i], type 
				except: pass
		"""
		tokens = [p[1]]
		lineno = p.lineno(1)
		#if t.parser.verbose:
		#	print p[1], lineno
		for i in range(2, len(p)):
			if p[i] is not None:				
				if matchFormatting and p.lineno(i) != lineno:
					if t.parser.verbose:
						print "split lines", p[i], p.lineno(i)
					#p[i] = '\n' + p[i]
					#tokens.append( '\n' + p[i])
					tokens.append( p[i] + '\n\t' )
					lineno = p.lineno(i)
				else:
					tokens.append(p[i])
					try:
						if p[i].type:
							type = p[i].type
							print 'assembled', funcname, p[i], type 
					except: pass
		"""
		res = token( separator.join(tokens), type )
	
	#res = separator.join(p[1:])

	if t.parser.verbose == 2:
		print funcname, res
	#elif t.parser.verbose == 1:
	#	print 'assembled', funcname
	
	#if p[0].find('def') >= 0:
	#	print funcname
	#	print "'%s'" % p[0]
	return res



def addComments( t, funcname = '' ):
	
	if t.parser.verbose:
		print "adding comments:", funcname, t.parser.comment_queue
	t[0] += ''.join(t.parser.comment_queue) #+ t[0]
	t.parser.comment_queue = []

def addHeldComments( t, funcname = '' ):
	
	commentList = t.parser.comment_queue_hold.pop()
	
	#commentList = ['# ' + x for x in commentList]
	
	if t.parser.verbose:
		print t.parser.comment_queue_hold
		print "adding held comments:", funcname, commentList
			
	t[0] = ''.join(commentList) + t[0]


def addHeldComments2( code, t, funcname = '' ):
	
	commentList = t.parser.comment_queue_hold.pop()
	
	commentList = ['# ' + x for x in commentList]
	
	if t.parser.verbose:
		print t.parser.comment_queue_hold
		print "adding held comments:", funcname, commentList
			
	return ''.join(commentList) + code
	
def holdComments():
	t.parser.comment_queue_hold.append( t.parser.comment_queue )
	t.parser.comment_queue = []


	
def entabLines( line ):
	
	buf = line.split('\n')
	#for x in buf:
	#	if x.startswith(''):
	#		print 'startswith space!', x
	
	res = '\n'.join( map( lambda x: '\t'+x, buf) )
	if line.endswith('\n'):
		res += '\n'
	return res


# translation-unit:
"""
translation_unit
	external_declaration
		function_definition
		declaration
"""

def p_translation_unit(t):
	'''translation_unit : external_declaration
						| translation_unit external_declaration'''
	t[0] = assemble(t, 'p_translation_unit')
	#print '\n'

# external-declaration:
def p_external_declaration(t):
	'''external_declaration : statement
							| function_definition'''
	t[0] = assemble(t, 'p_external_declaration')
	#if t.parser.verbose:
	#	print "external_declaration", t[0]

# function-definition:
def p_function_definition(t):
	'''function_definition :  function_declarator function_specifiers_opt ID LPAREN function_arg_list_opt RPAREN add_comment compound_statement'''
	#t[0] = assemble(t, 'p_function_definition')
	global global_procs
	
	t.parser.local_procs.append(t[3])
	if t[1].startswith('global'):
		if t.parser.curr_module in global_procs:
			global_procs[t.parser.curr_module].add(t[3])
		else:
			global_procs[t.parser.curr_module] = set([t[3]])
		
	t[0] = "def %s(%s):\n%s\n" % (t[3], t[5], entabLines(t[8]) )
	addHeldComments(t, 'func')

def p_add_comment(t):
	'''add_comment :'''
	if t.parser.verbose:
		print "holding", t.parser.comment_queue
	t.parser.comment_queue_hold.append( t.parser.comment_queue )
	t.parser.comment_queue = []

# function-specifiers
def p_function_specifiers_opt(t):
	'''function_specifiers_opt : type_specifier
						   	   | type_specifier LBRACKET RBRACKET
						   	   | empty'''
	# string
	# string[]
	#
	t[0] = assemble(t, 'p_function_specifiers_opt')
	
def p_function_declarator(t):
	'''function_declarator : GLOBAL PROC
						   | PROC'''
	# string
	# string[]
	#
	t[0] = assemble(t, 'p_function_declarator')
	
def p_function_arg(t):
	'''function_arg : type_specifier variable
					| type_specifier variable LBRACKET RBRACKET'''
	t[0] = assemble(t, 'p_function_arg')
	t[0] = t[2]
	t.parser.type_map[t[2]] = t[1]
	
def p_function_arg_list(t):
	'''function_arg_list : function_arg
						| function_arg_list COMMA function_arg'''
							
	t[0] = assemble(t, 'p_function_arg_list')
	if len(t) == 2:
		t[0] = t[1]
	else:
		t[0] = t[1] + ', ' + t[3]

def p_function_arg_list_opt(t):
	'''function_arg_list_opt : function_arg_list
						|  empty'''
							
	t[0] = assemble(t, 'p_function_arg_list_opt')
		
			
# declaration:
def p_declaration_statement(t):
	'''declaration_statement : declaration_specifiers init_declarator_list SEMI'''
	# int var=6;
	# int var1=6, var2=9;
	#	
	#t[0] = assemble(t, 'p_declaration_statement')



	def includeGlobalVar( var ):
		# handle whether we initialize this variable to the value of the mel global variable.
		# in some cases, the global variable is only for passing within the same script, in which
		# case the python global variable will suffice.  in other cases, we may want to retrieve a
		# global set by maya.
		
		incl_reg = t.parser.format_options.get('global_var_include_regex','.*')		# if nothing set, match all
		excl_reg = t.parser.format_options.get('global_var_exclude_regex','$')		# if nothing set, match none
		if re.match(incl_reg, var) and not re.match(excl_reg, var):	
			return True
		else:
			return False
	
	t[0] = ''
	
	isGlobal = False
	typ = t[1].split()
	if len(typ) == 2:
		assert typ[0] == 'global'
		typ = typ[1]
		isGlobal = True		
	else:
		typ = typ[0]
			
	for declaration in t[2]:					
		if len(declaration)==1:
			init = None
			var = declaration[0]
			# array
			if '[]' in var:
				var = var.strip().strip('[]')
				init = '[]'
			# non -array
			else:
				init = { 
					'string': "''",
					'int':	'0',
					'float': '0.0',
					'vector': 'MVec()'
				}[  typ  ]
				
			# global variable -- overwrite init	
			if isGlobal:
				
				t.parser.type_map[var] = typ
					
				t.parser.global_vars.add( var )
					
				t[0] += 'global %s\n' % var
				
				if includeGlobalVar( var):	
					# if init is brackets, then it's an array, and the type needs to be string[], int[], etc
					#print "get mel global var", var
					if init == '[]':
						typ += '[]'
					t[0] += "%s = getMelGlobal('%s','%s')\n" % (var, typ, var) 
				
			else:
				t.parser.type_map[var] = typ
				t[0] += '%s = %s\n' % (var, init)	
			
		else:
			#print buf
			for i,elem in enumerate(declaration):
				declaration[i] = elem.strip()
				if declaration[i].endswith('[]'):
					declaration[i] = declaration[i][:-2]
					
			t.parser.type_map[declaration[0]] = typ
			
			if isGlobal:
						
				#print "global var", buf[:-1]
				
				for global_var in declaration[:-1]:
					#print "set mel global var", global_var
					t.parser.global_vars.add(global_var)
					
					t[0] += 'global %s\n' % global_var 
					t[0] += '%s=%s\n' % (global_var, declaration[-1])
					if includeGlobalVar( global_var):
						t[0] += "setMelGlobal( '%s', '%s', %s )\n" % ( typ, global_var, global_var)
			else:
				t[0] += ' = '.join( declaration ) + '\n'
			
			
	addComments( t, 'declaration_statement' )


# declaration-specifiers
def p_declaration_specifiers(t):
	'''declaration_specifiers : type_specifier
							  | GLOBAL type_specifier'''
	# int
	# global int
	#
	t[0] = assemble(t, 'p_declaration_specifiers', ' ')
		
# type-specifier:
def p_type_specifier(t):
	'''type_specifier : INT
					  | FLOAT
					  | STRING
					  | VECTOR
					  '''
	t[0] = assemble(t, 'p_type_specifier')

# init-declarator-list:
def p_init_declarator_list(t):
	'''init_declarator_list : init_declarator
							| init_declarator_list COMMA init_declarator'''
	# var=6;
	# var1=6, var2=9;
	#
	#t[0] = assemble(t, 'p_init_declarator_list')
	
	if len(t)>2:
		t[0] = t[1] + [t[3]]
	else:
		t[0] = [t[1]]
		
	

# init-declarator
def p_init_declarator(t):
	'''init_declarator : declarator
						| declarator EQUALS assignment_expression'''
	# var=6
	#
	#t[0] = assemble(t, 'p_init_declarator', ' ')
	
	if len(t) > 2:
		t[0] = [t[1], t[3]]
		
	else:
		t[0] = [t[1]]
	

	
# declarator:
def p_declarator(t):
	'''declarator : variable
				  | declarator LBRACKET constant_expression_opt RBRACKET'''
#					| LPAREN declarator RPAREN		removed 11/05 in effort to get cast_expression working 				  
#					| declarator LPAREN parameter_type_list RPAREN 
#					| declarator LPAREN identifier_list RPAREN 
#					| declarator LPAREN RPAREN '''  
	# var
	# var[]
	# var[1]
	t[0] = assemble(t, 'p_declarator')
	#if len(t) == 5:
	#	if not t[3]:
	#		t[0] = t[1]


# Optional fields in abstract declarators
def p_constant_expression_opt_1(t):
	'''constant_expression_opt : empty'''
	t[0] = assemble(t, 'p_constant_expression_opt_1')

def p_constant_expression_opt_2(t):
	'''constant_expression_opt : constant_expression'''
	t[0] = assemble(t, 'p_constant_expression_opt_2')


# statement:
def p_statement(t):
	'''statement : expression_statement
			  | selection_statement
			  | iteration_statement
			  | jump_statement
			  | declaration_statement
			  | command_statement
			  | compound_statement'''
#			  | comment'''
	
	t[0] = assemble(t, 'p_statement')
	#t[0] = '\t' + t[0]

	
# labeled-statement:
def REMOVED_labeled_statement_1(t):
	'''labeled_statement : ID COLON statement'''
	# N/A ?
	t[0] = assemble(t, 'p_labeled_statement_1')



def p_labeled_statement_list(t):
	'''labeled_statement_list : labeled_statement
				  | labeled_statement_list labeled_statement'''

	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = t[1] + [t[2]]
		
def REMOVED_labeled_statement_2(t):
	'''labeled_statement : CASE constant_expression COLON statement_list_opt'''
	#t[0] = assemble(t, 'p_labeled_statement_2')
	t[0] = ['case %s == ' + t[2] + ':\n'] + t[4]

def REMOVED_labeled_statement_3(t):
	'''labeled_statement : DEFAULT COLON statement_list'''
	#t[0] = assemble(t, 'p_labeled_statement_3')
	
	t[0] = ['else:\n'] + t[3] 
		
def p_labeled_statement_2(t):
	'''labeled_statement : CASE constant_expression COLON statement_list_opt'''
	#t[0] = assemble(t, 'p_labeled_statement_2')
	fallthrough = True
	block = []
	for line in t[4]:
		lines = [ x + '\n' for x in line.split('\n')]
		block.extend(lines)
	
	i=0
	for i,line in enumerate(block):
		#print "--->", line
		if line.startswith('break'):
			#print "---breaking----"
			fallthrough = False
			break
			
	block = block[:i]
		
	t[0] = [t[2], block, fallthrough]
	
def p_labeled_statement_3(t):
	'''labeled_statement : DEFAULT COLON statement_list'''
	#t[0] = assemble(t, 'p_labeled_statement_3')
	block = []
	for line in t[3]:
		if line.startswith('break'):
			fallthrough = False
			break
		block.append(line)
		
	t[0] = [None, block, False]
	
# expression-statement:
def p_expression_statement(t):
	'''expression_statement : expression_opt SEMI'''
	#t[0] = assemble(t, 'p_expression_statement')
	
	t[0] = t[1] + '\n'
	addComments(t)
	
# compound-statement:
def p_compound_statement(t):
	'''compound_statement   : LBRACE statement_list RBRACE
							| LBRACE RBRACE''' # causes reduce/reduce conflict with postfix_expression
		 
	#print "compound, emptying queue:", t.parser.comment_queue
	#t[0] = ''.join(t.parser.comment_queue)
	#t.parser.comment_queue = []
	
	#t[0] = assemble(t, 'p_compound_statement')
	
	if len(t) == 4:
		t[0] = ''.join(t[2])
	else:
		t[0] = 'pass\n'		
		addComments(t, 'compound_pass')

def p_statement_list_opt(t):
	'''statement_list_opt : statement_list
				  | empty'''
	#t[0] = assemble(t, 'p_expression_list_opt')
	if isinstance(t[1],list):
		t[0] = t[1]
	else:
		t[0] = []

# statement-list:
def p_statement_list(t):
	'''statement_list   : statement
						| statement_list statement'''
	#t[0] = assemble(t, 'p_statement_list')
	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = t[1] + [t[2]]
		
# selection-statement
def p_selection_statement_1(t):
	'''selection_statement : IF LPAREN expression RPAREN statement'''
	t[0] = assemble(t, 'p_selection_statement_1')
	t[0] = 'if %s:\n%s' % (t[3],entabLines(t[5]))
	
def p_selection_statement_2(t):
	'''selection_statement : IF LPAREN expression RPAREN statement ELSE add_comment statement '''
	#t[0] = assemble(t, 'p_selection_statement_2')
		
	t[0] = 'if %s:\n%s\n' % (t[3], entabLines(t[5]))
	
	# elif correction
	match = re.match( r'(?:\s*)(if\b.*:)', t[8] )
	elseStmnt = ''
	if match:		
		elseStmnt='el%s\n%s' % ( match.group(1), t[8][match.end()+1:] )
	else:
		elseStmnt='else:\n%s' % ( entabLines(t[8]) )
	
	t[0] += addHeldComments2( elseStmnt, t, 'if/else')
	#addHeldComments(t, 'if/else')
		
def p_selection_statement_3(t):
	'''selection_statement : SWITCH LPAREN expression RPAREN add_comment LBRACE labeled_statement_list RBRACE'''
	#t[0] = assemble(t, 'p_selection_statement_3')
	
	"""	
	cases = t[7]  # a 2d list: a list of cases, each with a list of lines
	#cases[1:-1]:
	t[0] = ''
	#print cases
	for i,thiscase in enumerate(cases):
		#print 'MAIN', thiscase[0] % t[3]
		
		# create the first line of the statement block
		caseline = thiscase[0]
		if caseline.startswith('case'):
			if i==0:
				caseline = 'if' + caseline[4:]
			else:
				caseline = 'elif' + caseline[4:]
		try:
			t[0] += caseline % t[3]
		except TypeError:
			t[0] += caseline
			
		broken = False
		for case in cases[i:]:
			if broken == True:
				break	
			for line in case[1:]:		
				if line == 'break\n':
					broken = True
					break				
				t[0] += '\t' + line
	"""
	t[0] = ''				
	cases = t[7]  # a 2d list: a list of cases, each with a list of lines
	variable = t[3]
	i = 0
	control = ''
	while i < len(cases):
			
		if i == 0:
			control = 'if'
		else:
			control = 'elif'
				
		mainCondition = cases[i][0]
		conditions = set([])
		lines = []
		
		for j, (condition, block, fallthrough) in enumerate(cases[i:]):	
			
			if len(block):
				lines.extend(block)
			else:
				conditions.add(condition)
				i += 1 # on the next while loop, we will skip this case, because it is now subsumed under the current case
				
			if not fallthrough:
				if condition is not None and len(conditions) == j:
					conditions.add(condition)
					
				break
					
		i += 1
		conditions.add( mainCondition )
		conditions = list(conditions)
		block = entabLines( ''.join( lines ) )
		if len(conditions)>1:		
			t[0] += '%s %s in [%s]:\n%s' % ( control, variable, ','.join(conditions), block )
		else:
			if conditions[0] is None:
				t[0] +=  'else:\n%s' % ( block )
			else:
				t[0] +=  '%s %s == %s:\n%s' % ( control, variable, conditions[0], block )
	
							
	#print t[0]

	addHeldComments(t, 'switch')
	
def REMOVED_selection_statement_3(t):
	'''selection_statement : SWITCH LPAREN expression RPAREN add_comment LBRACE labeled_statement_list RBRACE'''
	#t[0] = assemble(t, 'p_selection_statement_3')
		
	cases = t[7]  # a 2d list: a list of cases, each with a list of lines
	#cases[1:-1]:
	t[0] = ''
	#print cases
	for i in range(1,len(cases)):
		# if previous block fell through
		if cases[i-1][2]:
			func_name = 'switch_%s_%s()' % (t[3], i+1)
			if cases[i][0] is None:
				func_name = 'switch_%s_default()' % (t[3])
				
			t[0] += 'def %s:\n%s' % (func_name, entabLines(cases[i][1])) 
			cases[i][1] = func_name + '\n'
			
	for i, (condition, x, x) in enumerate(cases):
		if condition:
			if i == 0:
				t[0] += 'if %s == %s:\n' % (t[3], condition)
			else:
				t[0] += 'elif %s == %s:\n' % (t[3], condition)
		else:
			t[0] += 'else:\n'
			
		for (x, block, fallthrough) in cases[i:]:	
			t[0] += entabLines(block)
			if not fallthrough:
				break
				
	print t[0]

	addHeldComments(t, 'switch')
		
# iteration_statement:
def p_iteration_statement_1(t):
	'''iteration_statement : WHILE LPAREN expression RPAREN add_comment statement'''
	#t[0] = assemble(t, 'p_iteration_statement_1')
	t[0] = 'while %s:\n%s\n' % (t[3], entabLines(t[6]) )
	addHeldComments(t, 'while')
	
def p_iteration_statement_2(t):
	'''iteration_statement : FOR LPAREN expression_list_opt SEMI expression_list_opt SEMI expression_list_opt RPAREN add_comment statement '''
	#t[0] = assemble(t, 'p_iteration_statement_2')
		
	#------------------------------------------------------------------
	# for( init_expr; cond_expr; update_expr
	#------------------------------------------------------------------
	# for( iterator=start; iterator(relop)stop; iterator(+/-=)step )
	#------------------------------------------------------------------
	
	# regular expression for a variable
	var_reg = re.compile(r'[A-Za-z_][\w_]*')
		
	init_exprs = t[3]
	cond_exprs = t[5]
	update_exprs = t[7]
	
	if len(cond_exprs) > 1:
		raise ValueError, """Python does not support for loops of format '(init_exp; cond_exp; update_exp)'.
In order to convert these statements to python, there can be only one conditional expression. I found %d (%s). Please correct this portion of the loop: %s""" % (len(cond_exprs), ','.join(cond_exprs), t[5])
	
	#---------------------------------------------
	# Conditional Expression  --> End
	#---------------------------------------------
	# the conditional expression becomes the end value of a range() function
	# there can be only one variable driven by the range expression, so there can be only one coniditional expression
	end = None
	regex = re.compile('\s*(<=|>=|<|>)\s*')
	cond_buf = regex.split(cond_exprs[0])  
	cond_relop = cond_buf.pop(1)	# cond_buf now contains 2 values, one of which will become our iterator
	cond_vars = set( filter( var_reg.match, cond_buf) )
	
	#---------------------------------------------
	# Update Expression --> Step
	#---------------------------------------------
	# The initialization is optional, so the next most important expression is the update expression.  
	iterator = None
	step = None
	update_op = None
	count = 0
	regex = re.compile('\s*(\+\+|--|\+=|-=)\s*')
	for expr in update_exprs:
		# expr: i++
		update_buf = regex.split(expr)
		update_op = update_buf.pop(1)
		# update_opt:  ++
		try:
			update_vars = filter( var_reg.match, update_buf)			
			iterator = list(cond_vars.intersection(update_vars))
			#print cond_vars, tmp, iterator
		except IndexError:
			count += 1
		else:
			if len(iterator) > 1:
				raise ValueError, """Python does not support for loops of format '(init_exp; cond_exp; update_exp)'.
In order to convert these statements to python, for loop iterator must appear only once in the update expression. I found %d (%s). Please correct this portion of the loop: %s.""" % ( len(iterator), ','.join(iterator), t[7] )	
			try:
				iterator = iterator[0]
				update_buf.remove(iterator)
				cond_buf.remove(iterator)
				step = update_buf[0]
				end = cond_buf[0]
				break
			except:
				iterator = None
	
	if iterator is None:
		raise ValueError, """Python does not support for loops of format '(init_exp; cond_exp; update_exp)'.
In order to convert these statements to python, for loop iterator must appear alone on one side of the conditional expression. Please correct this portion of the loop: %s.""" % ( t[5] )
			
	update_exprs.pop(count)
	
	#print "iterator:%s, update_op:%s, update_expr:%s, step:%s" % (iterator, update_op, update_exprs, step)

	# determine the step
	if update_op.startswith('-'):
		step = '-'+step
		if cond_relop == '>=':
			end = end + '-1'
	elif cond_relop == '<=':
		end = end + '+1'
	
	#---------------------------------------------
	# initialization --> start
	#---------------------------------------------
	start = None
	init_reg = re.compile('\s*=\s*')
	
	for expr in init_exprs:
		init_buf = init_reg.split(expr)
		try:
			init_buf.remove(iterator)
		except ValueError:
			pass
		else:
			if len(init_buf):
				start = init_buf[0]
			else:
				start = iterator
	
	#print "start: %s, end: %s, step: %s" % (start, end, step)
	
	if step == '1':
		t[0] = 'for %s in range(%s,%s):\n%s' % (iterator, start, end, entabLines(t[10]))
	else:
		t[0] = 'for %s in range(%s,%s,%s):\n%s' % (iterator, start, end, step, entabLines(t[10]) )

	if len( update_exprs ):
		t[0] += '\n' + entabLines('\n'.join(update_exprs) + '\n')
		
	addHeldComments(t, 'for')
	
def p_iteration_statement_3(t):
	'''iteration_statement : FOR LPAREN variable IN expression seen_FOR RPAREN add_comment statement '''
	#t[0] = assemble(t, 'p_iteration_statement_3')
	t[0] = 'for %s in %s:\n%s' % (t[3], t[5], entabLines(t[9]))
	addHeldComments(t, 'for')

def p_seen_FOR(t):
	'''seen_FOR :'''

	t.parser.type_map[t[-3].strip()] = t[-1].type	

	
def p_iteration_statement_4(t):
	'''iteration_statement : DO statement WHILE LPAREN expression RPAREN SEMI'''
	t[0] = assemble(t, 'p_iteration_statement_4')
	
	t[0] = t[2]	+ '\n'
	t[0] += 'while %s:\n%s\n' % (t[5], entabLines(t[2]) )
	addHeldComments(t, 'do while')

# jump_statement:
def p_jump_statement(t):
	'''jump_statement : CONTINUE SEMI
					| BREAK SEMI
					| RETURN expression_opt SEMI'''
	t[0] = assemble(t, 'p_jump_statement')
	if len(t)==4:
		t[0] = t[1] + ' ' + t[2] + '\n'
	else:
		t[0] = t[1] + '\n'
	addComments(t)
	
# optional expression
def p_expression_opt(t):
	'''expression_opt : empty
					  | expression'''
	t[0] = assemble(t, 'p_expression_opt')




# expression:
"""" 
ID
constant
SCONST
LPAREN expression RPAREN
	primary
		postfix
			unary
				cast
					multiplicative
						additive
							shift
								relational
									equality
										AND
											exclusive_or
												inclusive_or
													logical_and
														logical_or
															conditional
																constant
																assignment
																	expression
"""

def p_expression(t):
	'''expression : assignment_expression'''
	t[0] = assemble(t, 'p_expression')

def p_expression_list_opt(t):
	'''expression_list_opt : expression_list
				  | empty'''
	#t[0] = assemble(t, 'p_expression_list_opt')
	if isinstance(t[1],list):
		t[0] = t[1]
	else:
		t[0] = []
	
def p_expression_list(t):
	'''expression_list : assignment_expression
				  | expression_list COMMA assignment_expression'''
	#t[0] = assemble(t, 'p_expression')
	if len(t) == 2:
		t[0] = [t[1]]
	else:
		t[0] = t[1] + [t[3]]

	
# assigment_expression:
def p_assignment_expression(t):

	'''assignment_expression : conditional_expression
							| postfix_expression assignment_operator assignment_expression''' # changed first item from unary to postfix
#							| CAPTURE assignment_expression CAPTURE'''
#							| unary_expression assignment_operator CAPTURE assignment_expression CAPTURE'''
	t[0] = assemble(t, 'p_assignment_expression')
	if len(t) == 4:
		#print t[1], t[2], t[3]
		
		# remove array brackets
		if t[2] and t[1].endswith('[]'):
			t[0] = ' '.join( [ t[1][:-2], t[1], t[2] ] )
		
		# fill in the append string
		elif t[2] == '=' and t[1].endswith('.append(%s)'):  # replaced below due to a var[len(var)]
			t[0] = t[1] % t[3]
		

# assignment_operator:
def p_assignment_operator(t):
	'''
	assignment_operator : EQUALS
						| TIMESEQUAL
						| DIVEQUAL
						| MODEQUAL
						| PLUSEQUAL
						| MINUSEQUAL
						| LSHIFTEQUAL
						| RSHIFTEQUAL
						| ANDEQUAL
						| OREQUAL
						| XOREQUAL
						'''
	t[0] = assemble(t, 'p_assignment_operator')
	
# conditional-expression
def p_conditional_expression_1(t):
	'''conditional_expression : logical_or_expression'''
	t[0] = assemble(t, 'p_conditional_expression_1', ' ')

def p_conditional_expression_2(t):
	'''conditional_expression : logical_or_expression CONDOP expression COLON conditional_expression '''
	t[0] = assemble(t, 'p_conditional_expression_2')
	t[0] = '%s and %s or %s' % ( t[1], t[3], t[5] )
# constant-expression
def p_constant_expression(t):
	'''constant_expression : conditional_expression'''
#							| CAPTURE command CAPTURE'''
	t[0] = assemble(t, 'p_constant_expression')
	

# logical-or-expression
def p_logical_or_expression_1(t):
	'''logical_or_expression : logical_and_expression
							 | logical_or_expression LOR logical_and_expression'''
	t[0] = assemble(t, 'p_logical_or_expression', ' ')
	if len(t) == 4:
		t[0] = '%s or %s' % (t[1], t[3])
		
# logical-and-expression
def p_logical_and_expression_1(t):
	'''logical_and_expression : inclusive_or_expression
							  | logical_and_expression LAND inclusive_or_expression'''
	t[0] = assemble(t, 'p_logical_and_expression', ' ')
	if len(t) == 4:
		t[0] = '%s and %s' % (t[1], t[3])
		
# inclusive-or-expression:
def p_inclusive_or_expression_1(t):
	'''inclusive_or_expression : exclusive_or_expression
							   | inclusive_or_expression OR exclusive_or_expression'''
	t[0] = assemble(t, 'p_inclusive_or_expression_2', ' ')

# exclusive-or-expression:
def p_exclusive_or_expression_1(t):
	'''exclusive_or_expression : and_expression
							   | exclusive_or_expression XOR and_expression'''
	t[0] = assemble(t, 'p_exclusive_or_expression_2', ' ')

# AND-expression
def p_and_expression_1(t):
	'''and_expression : equality_expression
					  | and_expression AND equality_expression'''
	t[0] = assemble(t, 'p_and_expression_2', ' ')


# equality-expression:
def p_equality_expression_1(t):
	'''equality_expression : relational_expression
							| equality_expression EQ relational_expression
							| equality_expression NE relational_expression'''
	t[0] = assemble(t, 'p_equality_expression_3', ' ')

# relational-expression:

def p_relational_expression_1(t):
	'''relational_expression : shift_expression
							 | relational_expression LT shift_expression
							 | relational_expression GT shift_expression
							 | relational_expression LE shift_expression
							 | relational_expression GE shift_expression'''
	t[0] = assemble(t, 'p_relational_expression_5')

# shift-expression
def p_shift_expression(t):
    'shift_expression : additive_expression'
    t[0] = assemble(t, 'p_shift_expression')

# additive-expression
def p_additive_expression(t):
	'''additive_expression : multiplicative_expression
							| additive_expression PLUS multiplicative_expression
							| additive_expression MINUS multiplicative_expression'''
	t[0] = assemble(t, 'p_additive_expression', ' ')
	
	
	if len(t) == 4 and t[2] == '+':
		#print t[1], t[1].type, t[3], t[3].type
		if t[1].type == 'string' and t[3].type != 'string':
			t[0] = token( '%s + str(%s)' % (t[1], t[3]) , 'string' )
		if t[3].type == 'string' and t[1].type != 'string':
			t[0] = token( 'str(%s) + %s' % (t[1], t[3]), 'string' )
		
	#	if t[1].endswith('"'):
	#		t[0] = t[1][:-1] + '%s" % ' + t[3]
		
# multiplicative-expression

def p_multiplicative_expression(t):
	'''multiplicative_expression : cast_expression
								| multiplicative_expression TIMES cast_expression
								| multiplicative_expression DIVIDE cast_expression
								| multiplicative_expression MOD cast_expression'''
	t[0] = assemble(t, 'p_multiplicative_expression', ' ')




# cast-expression:
def p_cast_expression(t):
	'''cast_expression : unary_expression
						| unary_command_expression
						| type_specifier LPAREN expression RPAREN
						| LPAREN type_specifier RPAREN cast_expression'''
	t[0] = assemble(t, 'p_cast_expression')
	if len(t) == 5 and t[1] == 'string':
		t[0] = 'str(%s)' % t[3]
	elif len(t) == 5 and t[1] == '(':
		if t[2] == 'string':
			t[0] = 'str(%s)' % ( t[4] )
		else:
			t[0] = '%s(%s)' % (t[2], t[4] )
			
# unary-expression			
def p_unary_expression(t):
	'''unary_expression : postfix_expression
						| unary_operator cast_expression'''
	t[0] = assemble(t, 'p_unary_expression')
	if len(t)>2:
		if t[1] == '!':
			t[0] = 'not ' + t[2]
		else:
			t[0] = t[1] + ' ' + t[2]
		
def p_unary_expression_2(t):
	'''unary_expression : PLUSPLUS unary_expression
						| MINUSMINUS unary_expression'''
	# ++$var --> var+=1
	t[0] = assemble(t, 'p_unary_expression')
	t[0] = t[2] + t[1][0] + '=1'


# unary-command-expression:
def p_unary_command_expression(t):
	'''unary_command_expression : procedure_expression
								| unary_operator procedure_expression'''
	t[0] = assemble(t, 'p_unary_expression')
	if len(t)>2:
		if t[1] == '!':
			t[0] = 'not ' + t[2]
		else:
			t[0] = t[1] + ' ' + t[2]
			
# unary-operator
def p_unary_operator(t):
	'''unary_operator : PLUS 
					| MINUS
					| NOT'''
	t[0] = assemble(t, 'p_unary_operator')
				
# procedure_expression
def p_procedure_expression(t):
	'''procedure_expression : command_expression
				 			| procedure'''
	t[0] = assemble(t, 'p_procedure_expression')

def p_procedure(t):
	'''procedure : ID LPAREN procedure_expression_list RPAREN
				 | ID LPAREN RPAREN '''
	#t[0] = assemble(t, 'p_procedure')
	#t[0] = 'mel.' + t[0]
	if len(t) == 5:
		t[0] = command_format( t[1], t[3], t )
	else:
		t[0] = command_format( t[1],[], t )

def p_procedure_expression_list(t):
	'''procedure_expression_list : additive_expression
							   | procedure_expression_list COMMA additive_expression'''
							   #| procedure_expression_list COMMA comment command_expression'''
	
	#t[0] = assemble(t, 'p_procedure_expression_list', matchFormatting=False )

	if len(t)>2:
		t[0] = t[1] + [t[3]]
	else:
		t[0] = [t[1]]
					
	return
	
	if len(t) == 4:
		t[2] = None

	elif len(t) == 5:
		t[2] = None
		t[3] += t[4]
		t[4] = None

	t[0] = assemble(t, 'p_procedure_expression_list', ', ')
	
	
# command expression
def p_command_expression(t):
	'''command_expression : CAPTURE command CAPTURE'''
	t[0] = assemble(t, 'p_command_expression')
	t[0] = t[2]
					
# postfix-expression:
def p_postfix_expression(t):
	'''postfix_expression : primary_expression
							| postfix_expression LBRACKET expression RBRACKET
							| postfix_expression PLUSPLUS
							| postfix_expression MINUSMINUS'''
#							| postfix_expression LBRACE initializer_list RBRACE'''
#							| postfix_expression command_input_list'''
							
	# $var
	# $var[2-4]
	# myProc( arg1, $var)
	# myProc()
	# $var++
	
	t[0] = assemble(t, 'p_postfix_expression')
	# ++ and -- must be converted to += and -=
	if len(t) == 3:
		t[0] = t[1] + t[2][0] + '=1'
		
	# element
	elif len(t)==5:
		if not t[3]:
			t[0] = t[1]
		elif t[3] == 'len(%s)' % t[1]:
			t[0] = t[1] + '.append(%s)'
		else:
			lenSubtractReg = re.compile( 'len\(%s\)\s*(-)' % t[1] )
			try:
				# assignment relative to the end of the array:   x[-1]
				t[0] = '%s[%s]' % (t[1], ''.join(lenSubtractReg.split( t[3] )) )  
			except:
				t[0] = '%s[%s]' % (t[1], t[3])

def p_postfix_expression_2(t):
	'''postfix_expression : LBRACE expression_list_opt RBRACE'''
							
	# array
	
	#t[0] = assemble(t, 'p_postfix_expression')
	t[0] = '[%s]' % ','.join(t[2])
		
def p_postfix_expression_3(t):
	'''postfix_expression : LSHIFT expression_list RSHIFT'''
							
	# vector
	
	#t[0] = assemble(t, 'p_postfix_expression')
	t[0] = 'MVec([%s])' % ','.join(t[2])	

# primary-expression:
def p_primary_expression(t):
	'''primary_expression :	boolean
						| LPAREN expression RPAREN'''
	t[0] = assemble(t, 'p_primary_expression')
	
def p_primary_expression1(t):
	'''primary_expression :	 ICONST'''
	t[0] = token(t[1], 'int')
	if t.parser.verbose == 2:
		print "p_primary_expression", t[0]
	
def p_primary_expression2(t):
	'''primary_expression :	 SCONST'''
	t[0] = token(t[1], 'string')
	if t.parser.verbose == 2:
		print "p_primary_expression", t[0]
	
def p_primary_expression3(t):
	'''primary_expression :	 FCONST'''
	t[0] = token(t[1], 'float')
	if t.parser.verbose == 2:
		print "p_primary_expression", t[0]
	
def p_primary_expression4(t):
	'''primary_expression :	 variable'''	
	t[0] = token(t[1], t.parser.type_map.get(t[1], None) )
	if t.parser.verbose == 2:
		print "p_primary_expression", t[0]
	
	#print "mapping", t[1], t.parser.type_map.get(t[1], None) 
	#print "p_primary_expression", t[0]

# comment
#def p_comment(t):
#	'''comment : COMMENT'''
#	t[0] = '#' + t[1][2:] + '\n'

#def p_comment_block(t):
#	'''comment : COMMENT_BLOCK'''
#	t[0] = '"""%s"""' % t[1][2:-2] + '\n'

	
# types	
	
def p_boolean(t):
	'''boolean : TRUE
			   | FALSE'''
	t[0] = t[1].capitalize()

def p_boolean2(t):
	'''boolean : ON'''
	t[0] = 'True'
	
def p_boolean3(t):
	'''boolean : OFF'''
	t[0] = 'False'
		
def p_variable(t):
	'''variable : VAR'''
	if t[1] in reserved:
		t[0] = t[1] + '_'
	else:
		t[0] = t[1]



# Commands
def getCommandFlags( command ):

	try:
		#print "getting flags for", command
		lines = cmds.help( command ).split('\n')
		synopsis = lines.pop(0)
		#print synopsis
		lines.pop(0) # 'Flags'
		#print lines
		flags = {}
		for line in lines:
			tokens = line.split()
			try:
				tokens.remove('(multi-use)')
			except:
				pass
			#print tokens
			if len(tokens):
				numArgs = len(tokens)-2
				shortFlag = str(tokens[0])
				longFlag = str(tokens[1])
				commandFlag = False
				if 'command' in longFlag.lower():
					commandFlag = True
				
				flags[shortFlag] = (numArgs, commandFlag)
				flags[longFlag]  = (numArgs, commandFlag)
		#print command, flags
		return flags
	except:
		#print "No help for:", command
		return None
			
def getAllCommandFlags():
	import maya.cmds as cmds
	funcs = filter( lambda x: not x.startswith('_'), dir(cmds) )
	commands = {}
	for func in funcs:
		flags = getCommandFlags( func )
		if flags is not None:
			commands[func] = flags
	return commands

def scriptModule( procedure ):
	""" determine if this procedure has been or will be converted into python, and if so, what module it belongs to """
	
	global currentFiles
	global proc_module
	
	if procedure in proc_module:
		return proc_module[procedure]
	
	#try:
	result = mel.whatIs( procedure )
	buf = result.split( ':' )
	#print buf
	if buf[0] == 'Mel procedure found in':
		fullpath = path.path( buf[1] )
		name = fullpath.namebase
		#print procedure, name
		if fullpath in currentFiles:
			proc_module[procedure] = name
			return name
				
		for f in sys.path:
			f = path.path( f + os.sep + name  + '.py' )
			if f.isfile():
				lines = f.lines()
				if lines[0].startswith(tag):
					proc_module[procedure] = name
					return name
					
					
	#except:
	#	#print "No help for:", command
	#	return None
		

		
	
def command_format(command, args, t):
			
	if len(args) == 1 and args[0].startswith('(') and args[0].endswith(')'):
		args[0] = args[0][1:-1]
		
	flags = getCommandFlags(command)
	
	if t.parser.verbose:
		print 'p_command: input_list', command, args, flags
	
	

	# commands with custom replacements	
	try:
		return proc_remap[command](args, t)		
	except KeyError: pass

	
	# Mel procedures and commands without help documentation
	if flags is None:			
		args = ', '.join(args)
	
		if command in t.parser.local_procs:
			return '%s(%s)' % (command, args)
	
		module = scriptModule( command )
	
		if module:
			t.parser.used_modules.add( module )
			return '%s.%s(%s)' % (module, command, args)
	
		return 'mel.%s(%s)' % (command, args)
	
	# commands with help documentation
	try:
		#print 'FLAGS', t[1], flags
		#print 'ARGS', args
		kwargs = {}
		pargs = []
		argTally=[]	
		numArgs = 0
		commandFlag = False
		flagReg = re.compile("-\s*([A-Za-z][\w_]*)")
		queryMode = False
		currFlag = None
		for token in args:				
			flagmatch = flagReg.match( token )
			#if token.startswith('-'):
			
			#----- Flag -----
			if flagmatch:
				if numArgs > 0:
					raise ValueError, 'reached a new flag before receiving all necessary args for last flag'

				(numArgs, commandFlag) = flags[ token ]
				
				token = token[1:]
				#print 'new flag', token, numArgs
							
				if numArgs == 0 or queryMode:
					kwargs[token]='1'
					numArgs=0
				else:
					currFlag = token
			
				# moved this after the queryMode check, bc sometimes the query flag expects a value other than a boolean
				if token in ['q', 'query']:
					queryMode = True
			
			elif numArgs == 1:
				if commandFlag:
					token = 'lambda *args: mm.eval(%s)' % token
				
				argTally.append(token)
				#print 'last flag arg', currFlag, argTally
				if len(argTally)==1:			
					argTally = argTally[0]
				else:
					argTally = '(%s)' % ', '.join(argTally)
				
				if currFlag in kwargs:
					if isinstance(kwargs[currFlag], list):
						kwargs[currFlag].append( argTally )
						#print "appending kwarg", currFlag, kwargs
					else:
						kwargs[currFlag] = [ kwargs[currFlag], argTally ]
						#print "adding kwarg", currFlag, kwargs
				else:
					#print "new kwarg", currFlag, kwargs 
					kwargs[currFlag] = argTally
					
				numArgs=0
				argTally=[]
				currFlag = None
				
			elif numArgs > 0:
				argTally.append(token)
				#print 'adding arg', currFlag, argTally
				numArgs-=1
			else:
				pargs.append(token)
		"""
		try:
			if kwargs[-1].endswith('='):
				kwargs[-1] += '1';
		except IndexError:
			pass
		"""
			
		#print 'final kw list', kwargs
		
		# functions that clash with python keywords and ui functions must use the cmds namespace
		# ui functions in pymel work in a very different, class-based way, so, by default we'll convert to the standard functions
		if command in ['file','filter','help','quit']: # + uiCommands:
			command = 'cmds.' + command
		if command == 'eval':
			command = 'mm.' + command
		
		if command == 'python':
			args = map( lambda x: x.strip('"'), args[0].split(' + ') )
			print args
			return ''.join(args)
		
	
		for flag, value in kwargs.items():
			if value is None:
				value = '1'
			if isinstance( value, list):
				sep = ','
				if len(value) > t.parser.format_options['kwargs_newline_threshhold']:
					sep = ',\n\t'
				pargs.append( '%s=[%s]' % ( flag, sep.join(value) )  )
			else:
				pargs.append( '%s=%s' % (flag, value) )
		
		sep = ','
		if len(pargs) > t.parser.format_options['args_newline_threshhold']:
			sep = ',\n\t'
		
		res =  '%s(%s)' % (command, sep.join( pargs ) )
		return res
		
	except KeyError, key:
		print "Error Parsing: Flag %s does not appear in help for command %s. Skipping command formatting" % (key, command)
		return '%s(%s) # <---- Formatting this command failed. You will have to fix this by hand' % (command, ', '.join(args))

def p_command_statement(t):
	'''command_statement : ID SEMI
			| ID command_statement_input_list SEMI'''
	#print "p_command_statement"

	if len(t) == 3:
		t[0] = command_format(t[1], [], t) + '\n'
	else:	
		t[0] = command_format(t[1], t[2], t) + '\n'
	addComments(t)
			
def p_command(t):
	'''command : ID
			| ID command_input_list'''
	#print "p_command"
	if len(t) == 2:
		t[0] = command_format(t[1],[], t)
	else:	
		t[0] = command_format(t[1], t[2], t)

	
	

			
def p_command_input_list(t):
	'''command_input_list : command_input
						  | command_input_list command_input'''
	#t[0] = assemble(t, 'p_command_input_list')	
	#print 'command_input_list', t[1:]
	
	#t[0] = ' '.join(t[1:])
	if len(t)>2:
		#print "append"
		t[0] = t[1] + [t[2]]
	else:
		#print "new"
		t[0] = [t[1]]
		
def p_command_input(t):
	'''command_input : unary_expression
				 	 | command_flag'''
	t[0] = assemble(t, 'p_command_input')

def p_command_input_2(t):
	'''command_input : ID'''
	t[0] = "'%s'" % t[1]

def p_command_statement_input_list(t):
	'''command_statement_input_list : command_statement_input
						  			| command_statement_input_list command_statement_input'''
	#t[0] = assemble(t, 'p_command_input_list')	
	#print 'command_input_list', t[1:]
	
	#t[0] = ' '.join(t[1:])
	if len(t)==2:
		t[0] = [t[1]]		
	else:
		t[0] = t[1] + [t[2]]
		
def p_command_statement_input(t):
	'''command_statement_input : unary_expression
					 | command_expression
					 | command_flag'''
	t[0] = assemble(t, 'p_command_input')

def p_command_statement_input_2(t):
	'''command_statement_input : ID'''
	t[0] = "'%s'" % t[1]
	
def p_flag(t):
	'''command_flag : MINUS ID'''
	t[0] = assemble(t, 'p_flag')
	

	t[0] = t[1] + { 	'import': 'i',
		 		 			'del'	: 'delete' 
					}.get( t[2], t[2] )
		

		

# Other
def p_empty(t):
	'''empty : '''
	t[0] = assemble(t, 'p_empty')

def _error(t):
	print "Error parsing script, attempting to read forward and restart parser"
	while 1:
		tok = yacc.token()             # Get the next token
		if not tok or tok.type == 'RBRACE': break
	yacc.restart()

def p_error(t):
	if t is None:
		raise ValueError, 'script has no contents'
	
	if t.type == 'COMMENT':
		#print "Removing Comment", t.value
		# Just discard the token and tell the parser it's okay.		
		comment = '#' + t.value[2:] + '\n'
		#if t.parser.verbose:
		#print "queueing comment", comment
		parser.comment_queue.append( comment )
		yacc.errok()
	elif t.type == 'COMMENT_BLOCK':
		comment = t.value[2:-2]
		
		if '"' in comment:
			comment = "'''" + comment + "'''\n"
		else:
			comment = '"""' + comment + '"""\n'
		#if t.parser.verbose:
		#print "queueing comment", comment
		parser.comment_queue.append( comment )
		yacc.errok()	
		
	else:
		print "Error parsing script at %s, attempting to read forward and restart parser" % t.value
		while 1:
			tok = yacc.token()             # Get the next token
			if not tok or tok.type == 'RBRACE': break
		yacc.restart()



import profile
# Build the grammar

parser = yacc.yacc(method='''LALR''')

#profile.run("yacc.yacc(method='''LALR''')")



