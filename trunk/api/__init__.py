""" Loader for Maya api sub-package """
#import pymel.mayahook as mayahook

# this can be imported without having maya fully initialized
from allapi import *

## Maya needs to be running at this point - useful to doublecheck if we've skipped pymel.__init__
#from pymel.mayahook import mayaInit as _mayaInit, mayaIsRunning as _mayaIsRunning
#if not _mayaIsRunning():
#	_mayaInit()

# note can import from util but not from core, the dependency order should be from bottom up : util - api - core
from conversions import *
