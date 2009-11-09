""" Loader for Maya api sub-package """
#import pymel.mayahook as mayahook

# this can be imported without having maya fully initialized
from allapi import *

# note can import from util but not from core, the dependency order should be from bottom up : util - api - core
from conversions import *
