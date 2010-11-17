
"""
General utilities which are pymel-independent."
"""
import sys, codecs, os, os.path, re, platform

from collections import *

# If we're using python < 2.6, collections doesn't have namedtuple
if 'namedtuple' not in globals():
    from namedtuple import namedtuple
from common import *
from arguments import *
from utilitytypes import *
#from trees import *
from arrays import *
from enum import *
from path import *
from decoration import *
from shell import *
#import nameparse




