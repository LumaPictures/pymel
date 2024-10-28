
# copyright Chad Dombrova    chadd@luma-pictures.com
# created at luma pictures   www.luma-pictures.com

"""
*******************************
          PyMEL
*******************************

PyMEL makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of MEL commands into python functions. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. PyMEL
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.

=======================================
    Special Thanks
=======================================

Special thanks to those studios with the foresight to support an open-source project of this nature:  Luma Pictures,
Attitude Studio, and ImageMovers Digital.

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()

__versiontuple__ = (1, 5, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(x) for x in __versiontuple__) + __version_suffix__
__authors__ = ['Chad Dombrova', 'Paul Molodowitch', 'Olivier Renouard', 'Ofer Koren']
