"""Low-level maya and pymel utilities.  Functions in this module are used by both `pymel.api` and `pymel.core`,
and are able to be defined before maya.standalone is initialized.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from .plogging import getLogger
