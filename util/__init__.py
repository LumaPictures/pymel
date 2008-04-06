
"Util contains functions and classes which are required by pymel.  These helper utilities do not require pymel to operate and can be useful in other code."

import sys, codecs, os, os.path, re, platform

from collections import *

from mexceptions import *
from namedtuple import namedtuple
from common import *
from arguments import *
from utilitytypes import *
from mayautils import *
from trees import *

import envparse

if os.name == 'nt' :
    maya = 'maya.exe'
    sep = ';'
else :
    maya = 'maya.bin'
    sep = ':'


