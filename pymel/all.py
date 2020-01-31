"""Imports all of pymel into one namespace, for use during interactive scripting"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
import pymel as _pymel
_pymel.all = sys.modules[__name__]

from pymel import internal
import pymel.internal.startup
doFinalize = pymel.internal.startup.finalizeEnabled
pymel.internal.startup.finalizeEnabled = False
from pymel.internal import plogging
from pymel.internal import factories
from pymel import mayautils

#logger = plogging.getplogging.pymelLogger(__name__)
plogging.pymelLogger.debug('imported internal')

from pymel import api
plogging.pymelLogger.debug('imported api')

from pymel.core import *
plogging.pymelLogger.debug('imported core')

# for wrapped math functions
from pymel.util.arrays import *

from pymel.core import datatypes

from pymel import versions

from pymel.core import nodetypes
from pymel.core.nodetypes import *

# if in batch mode we may not have UI commands
if not cmds.about(batch=True):
    from pymel.core.uitypes import *

# These two were imported into 'old' pymel top level module,
# so make sure they're imported here as well
from pymel import core
from pymel import tools

# some submodules do 'import pymel.core.pmcmds as cmds' -
# this ensures that when the user does 'from pymel import *',
# cmds is always maya.cmds
import maya.cmds as cmds

# Run delayed finalize now, so that if userSetup imports all,
# it has access to everything it should
pymel.internal.startup.finalizeEnabled = doFinalize
pymel.internal.startup.finalize()
