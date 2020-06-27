"""Functions for getting and comparing versions of Maya.

Class for storing apiVersions, which are the best method for comparing versions. ::

    >>> from pymel import versions
    >>> if versions.current() >= versions.v2008:
    ...     print("The current version is later than Maya 2008")
    The current version is later than Maya 2008
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import re
import struct
from maya.OpenMaya import MGlobal as _MGlobal

if False:
    from typing import *


def parseVersionStr(versionStr, extension=False):
    # type: (str, bool) -> str
    r"""
    Parse a verbose version string (like the one displayed in the Maya title
    bar) and return the base version.

    Parameters
    ----------
    versionStr : str
    extension : bool
        if True, leave the -x64 tag

    Returns
    -------
    str

    Examples
    --------
    >>> from pymel.all import *
    >>> versions.parseVersionStr('2008 Service Pack1 x64')
    '2008'
    >>> versions.parseVersionStr('2008 Service Pack1 x64', extension=True)
    '2008-x64'
    >>> versions.parseVersionStr('2008x64', extension=True)
    '2008-x64'
    >>> versions.parseVersionStr('8.5', extension=True)
    '8.5'
    >>> versions.parseVersionStr('2008 Extension 2')
    '2008'
    >>> versions.parseVersionStr('/Applications/Autodesk/maya2009/Maya.app/Contents', extension=True)
    '2009'
    >>> versions.parseVersionStr(r'C:\Program Files (x86)\Autodesk\Maya2008', extension=True)
    '2008'

    """
    if 'Preview' in versionStr:
        # Beta versions of Maya may use the format 'Preview Release nn x64', which
        # doesn't contain the actual Maya version. If we have one of those, we'll
        # make up the version from the API version. Not foolproof, but should work
        # in most cases.
        version = str(_MGlobal.apiVersion())[0:4]
        if extension and bitness() == 64:
            version += '-x64'
    else:
        # problem with service packs addition, must be able to match things such as :
        # '2008 Service Pack 1 x64', '2008x64', '2008', '8.5'

        # NOTE: we're using the same regular expression (parseVersionStr) to parse both the crazy human readable
        # maya versions as returned by about, and the maya location directory.  to handle both of these i'm afraid
        # the regular expression might be getting unwieldy

        ma = re.search(r"((?:maya)?(?P<base>[\d.]{3,})(?:(?:[ ].*[ ])|(?:-))?(?P<ext>x[\d.]+)?)", versionStr)
        version = ma.group('base')

        if extension and (ma.group('ext') is not None):
            version += "-" + ma.group('ext')
    return version


def bitness():
    # type: () -> int
    """
    The bitness of python running inside Maya as an int.

    Returns
    -------
    int
    """
    # NOTE: platform.architecture()[0] returns '64bit' on OSX 10.6 (Snow Leopard)
    # even when Maya is running in 32-bit mode. The struct technique
    # is more reliable.
    return struct.calcsize("P") * 8


_is64 = bitness() == 64
_current = _MGlobal.apiVersion()
_fullName = _MGlobal.mayaVersion()
_shortName = parseVersionStr(_fullName, extension=False)
_installName = _shortName + ('-x64' if (_is64 and _current < 201600) else '')


v85 = 200700
v85_SP1 = 200701
v2008 = 200800
v2008_SP1 = 200806
v2008_EXT2 = 200806
v2009 = 200900
v2009_EXT1 = 200904
v2009_SP1A = 200906
v2010 = 201000
v2011 = 201100
v2011_HOTFIX1 = 201101
v2011_HOTFIX2 = 201102
v2011_HOTFIX3 = 201103
v2011_SP1 = 201104
v2012 = 201200
v2012_HOTFIX1 = 201201
v2012_HOTFIX2 = 201202
v2012_HOTFIX3 = 201203
v2012_HOTFIX4 = 201204
v2012_SP1 = 201209
v2012_SAP1 = v2012_SP1
v2012_SP2 = 201217
v2012_SAP1SP1 = v2012_SP2
v2013 = 201300
v2014 = 201400
v2014_SP1 = 201402
v2014_SP2 = 201404
v2014_SP3 = 201406
v2014_EXT1 = 201450
v2014_EXT1SP1 = 201451
v2014_EXT1SP2 = 201459
v2015 = 201500
v2015_SP1 = 201501
v2015_SP2 = 201502
v2015_SP3 = 201505
v2015_SP4 = 201506
v2015_EXT1 = 201506
v2015_SP5 = 201507
v2015_EXT1SP5 = 201507
v2016 = 201600
v2016_SP3 = 201605
v2016_SP4 = 201607
v2016_EXT1 = v2016_SP3
v2016_EXT1SP4 = v2016_SP4
v20165 = 201650
v2016_EXT2 = v20165
v20165_SP1 = 201651
v2016_EXT2SP1 = v20165_SP1
v20165_SP2 = 201653
v2016_EXT2SP2 = v20165_SP2
v2017 = 201700
v2017U1 = 201701
v2017U2 = 201720
v2017U3 = 201740
v2018 = 20180000
v2018_1 = 20180100
v2018_2 = 20180200
v2018_3 = 20180300
v2018_4 = 20180400
v2018_5 = 20180500
v2018_6 = 20180600
v2018_7 = 20180700
v2019 = 20190000
v2019_1 = 20190100
v2019_2 = 20190200
v2019_3 = 20190300
v2020 = 20200000
v2020_1 = 20200100
v2021 = 20210000


def current():
    # type: () -> int
    """Get the current version of Maya

    Returns
    -------
    int
    """
    return _current


def fullName():
    return _fullName


def installName():
    return _installName


def shortName():
    return _shortName


def is64bit():
    # type: () -> bool
    """Whether this instance of Maya is 64-bit

    Returns
    -------
    bool
    """
    return _is64


def flavor():
    # type: () -> unicode
    """The 'flavor' of this instance of Maya

    Requires ``maya.cmds``.

    Returns
    -------
    unicode
    """
    import maya.cmds
    try:
        return maya.cmds.about(product=1).split()[1]
    except AttributeError:
        raise RuntimeError("This method cannot be used until maya is fully initialized")


def isUnlimited():
    # type: () -> bool
    """Whether this instance of Maya is 'Unlimited' (deprecated)

    Returns
    -------
    bool
    """
    return flavor() == 'Unlimited'


def isComplete():
    # type: () -> bool
    """Whether this instance of Maya is 'Unlimited' (deprecated)

    Returns
    -------
    bool
    """
    return flavor() == 'Complete'


def isRenderNode():
    # type: () -> bool
    """
    Returns
    -------
    bool
    """
    return flavor() == 'Render'


def isEval():
    # type: () -> bool
    """Whether this instance of Maya is an evaluation edition

    Requires ``maya.cmds``.

    Returns
    -------
    bool
    """
    import maya.cmds
    try:
        return maya.cmds.about(evalVersion=1)
    except AttributeError:
        raise RuntimeError("This method cannot be used until maya is fully initialized")

