from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import sys
import os
import re
import os.path
from . import mellex

try:
    from pymel.util.external.ply import *
except ImportError:
    from ply import *

from pymel.util import unescape
import pymel
import pymel.util as util
import pymel.internal.factories as factories

tokens = mellex.tokens


def p_translation_unit(t):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration'''
    pass
    # print "translation_unit"
    #t[0] = assemble(t, 'p_translation_unit')
    # print '\n'

# external-declaration:


def p_external_declaration(t):
    '''external_declaration : function_definition
                            | group'''
    pass
    # print "external_declaration", t[1]
    #t[0] = assemble(t, 'p_external_declaration')
    # if t.lexer.verbose:
    #    print "external_declaration", t[0]

# function-definition:


def p_function_definition(t):
    '''function_definition :  function_declarator function_specifiers_opt ID LPAREN function_arg_list_opt RPAREN group'''
    #t[0] = assemble(t, 'p_function_definition')

    # add to the ordered list of procs
    t.lexer.proc_list.append(t[3])

    # global proc
    if t[1]:
        # print "adding global"
        t.lexer.global_procs[t[3]] = {'returnType': t[2], 'args': t[5]}
        #t[0] = addHeldComments(t, 'func') + "def %s(%s):\n%s\n" % (t[3], ','.join(t[6]) , entabLines( t[9]) )

    # local proc gets prefixed with underscore
    else:
        # print "adding local"
        t.lexer.local_procs[t[3]] = {'returnType': t[2], 'args': t[5]}
        #t[0] = addHeldComments(t, 'func') + "def _%s(%s):\n%s\n" % (t[3], ','.join(t[6]) , entabLines( t[9]) )


def p_function_declarator(t):
    '''function_declarator : GLOBAL PROC
                           | PROC'''
    # string
    # string[]
    #
    if len(t) == 2:
        # print "local proc"
        t[0] = False
    else:
        # print "global proc"
        t[0] = True


def p_type_specifier(t):
    '''type_specifier : INT
                      | FLOAT
                      | STRING
                      | VECTOR
                      | MATRIX
                      '''
    # print "type_specifier"
    t[0] = t[1]

# function-specifiers


def p_function_specifiers_opt(t):
    '''function_specifiers_opt : type_specifier
                                  | type_specifier LBRACKET RBRACKET
                                  | empty'''
    # string
    # string[]
    #
    # print "function_specifiers_opt"
    if len(t) == 2:
        t[0] = t[1]
    else:
        t[0] = t[1] + '[]'
    #t[0] = assemble(t, 'p_function_specifiers_opt')


def p_function_arg(t):
    '''function_arg : type_specifier VAR
                    | type_specifier VAR LBRACKET RBRACKET'''
    #t[0] = assemble(t, 'p_function_arg')
    if len(t) == 3:
        t[0] = (t[1], t[2])
    else:
        t[0] = (t[1] + '[]', t[2])


def p_function_arg_list(t):
    '''function_arg_list : function_arg
                        | function_arg_list COMMA function_arg'''

    #t[0] = assemble(t, 'p_function_arg_list')
    if len(t) > 2:
        t[0] = t[1] + [t[3]]
    # start a new list
    else:
        t[0] = [t[1]]


def p_function_arg_list_opt(t):
    '''function_arg_list_opt : function_arg_list
                        |  empty'''

    #t[0] = assemble(t, 'p_function_arg_list_opt')
    if not t[1]:
        t[0] = []
    else:
        t[0] = t[1]


def p_declaration_specifiers(t):
    '''declaration_specifiers : type_specifier
                              | GLOBAL type_specifier'''
    # print "declaration_specifiers"
    if len(t) == 2:
        t[0] = (None, t[1])
    else:
        t[0] = (t[1], t[2])


def p_group_list_opt(t):
    '''group_list_opt : group_list
                | empty
                '''
    # print "group_list_opt"
    t[0] = t[1]


def p_group_list(t):
    '''group_list : group_list group
            | group'''
    pass
#    print "group_list"
#    if len(t) == 2:
#        t[0] = [t[1]]
#    else:
#        t[0] = t[1] + [t[2]]


def p_group(t):
    '''group : element
            | LBRACE group_list_opt RBRACE'''
    pass
#    if len(t) == 2:
#        print "group", t[1]
#        t[0] = t[1]
#    else:
#        print "adding brackets", t[2]
#        t[0] = t[2]

# def p_element_list_opt(t):
#    '''element_list_opt : element_list
#                | empty
#                '''
#    print "empty"
#    t[0] = t[1]
#
# def p_element_list(t):
#    '''element_list : element
#                | element_list element
#                '''
#    if len(t) == 2:
#        t[0] = [t[1]]
#    else:
#        t[0] = t[1] + [t[2]]


def p_element(t):
    '''element : declaration_specifiers
            | BREAK
            | CASE
            | CONTINUE
            | DEFAULT
            | DO
            | ELSE
            | FALSE
            | FOR
            | IF
            | IN
            | NO
            | ON
            | OFF
            | RETURN
            | SWITCH
            | TRUE
            | WHILE
            | YES
            | ID
            | VAR
            | ICONST
            | FCONST
            | SCONST
            | PLUS
            | MINUS
            | TIMES
            | DIVIDE
            | MOD
            | NOT
            | CROSS
            | LOR
            | LAND
            | LT
            | LE
            | GT
            | GE
            | EQ
            | NE
            | EQUALS
            | TIMESEQUAL
            | DIVEQUAL
            | MODEQUAL
            | PLUSEQUAL
            | MINUSEQUAL
            | CROSSEQUAL
            | COMPONENT
            | PLUSPLUS
            | MINUSMINUS
            | CONDOP
            | LPAREN
            | RPAREN
            | LBRACKET
            | RBRACKET
            | COMMA
            | SEMI
            | COLON
            | CAPTURE
            | LVEC
            | RVEC
            | COMMENT
            | COMMENT_BLOCK
            | ELLIPSIS

            '''
    # print "element", t[1]
    t[0] = t[1]


def p_empty(t):
    '''empty : '''
    pass
    #t[0] = assemble(t, 'p_empty')

# def p_error(t):
#    print "error"
#    pass
