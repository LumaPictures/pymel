"Low-level maya and pymel utilities"

from mayautils import *
#from envparse import *
from optionvars import *
from version import *
#assert mayaInit() 
import mexceptions
import plogging
from plogging import getLogger
pymel_options = parsePymelConfig()