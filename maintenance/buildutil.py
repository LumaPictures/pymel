"""
Code shared between build and buildstubs.

buildstubs is designed to run outside of mayapy.
"""
from __future__ import absolute_import, print_function
from typing import Optional
import pymel.internal.cmdcache

pymel.internal.cmdcache.CmdCache.version = '2023'
cmdcache = pymel.internal.cmdcache.CmdCache()
data = cmdcache.load()
datamap = dict(zip(cmdcache.cacheNames(), data))
CMDLIST = datamap['cmdlist']  # type: pymel.internal.cmdcache.CommandInfo


CORE_CMD_MODULES = [
    ('pymel.core.animation', '_general.PyNode'),
    ('pymel.core.context', None),
    ('pymel.core.effects', '_general.PyNode'),
    ('pymel.core.general', 'PyNode'),
    ('pymel.core.language', None),
    ('pymel.core.modeling', '_general.PyNode'),
    ('pymel.core.other', None),
    ('pymel.core.rendering', '_general.PyNode'),
    ('pymel.core.runtime', None),
    ('pymel.core.system', None),
]

CORE_CMD_MODULES_MAP = dict(CORE_CMD_MODULES)


class MelFunctionHelper(object):

    TYPING_TYPES = [
        'Union', 'Tuple', 'Callable', 'Any'
    ]

    def __init__(self, name: str, moduleName: Optional[str] = None):
        self.name = name
        self.info = CMDLIST[name]
        if moduleName is None:
            moduleName = 'pymel.core.' + self.info['type']
        self.moduleName = moduleName

    @classmethod
    def get(cls, name: str, moduleName: str):
        if not moduleName in CORE_CMD_MODULES_MAP:
            return None
        if name not in CMDLIST:
            return None
        return MelFunctionHelper(name)

    def _getType(self, typ) -> str:
        if isinstance(typ, str):
            if typ == 'timerange':
                return 'Union[str, Tuple[Union[int, float], Union[int, float]]]'
            elif typ == 'floatrange':
                # Note: we don't appear to add support for Tuple input like we
                # do for timerange
                return 'Union[str, int, float]'
            elif typ == 'time':
                return 'Union[int, float]'
            elif typ == 'PyNode':
                typ = 'PyNode' if self.moduleName == 'pymel.core.general' else '_general.PyNode'
            elif typ == 'script':
                return 'Union[str, Callable]'
            elif ' ' in typ:
                # I've seen one case of bad type name in our cmdlist cache
                typ = 'Any'
        else:
            typ = typ.__name__
        return typ

    def getFlagType(self, flagInfo: 'pymel.internal.cmdcache.FlagInfo') -> str:
        if flagInfo['numArgs'] < 2:
            return self._getType(flagInfo['args'])
        else:
            # FIXME: this may be affected by resultNeedsUnpacking
            return 'Tuple[%s]' % ', '.join(
                [self._getType(arg_type)
                 for arg_type in flagInfo['args']])

    def getArgs(self):
        # FIXME: assumes single *args is first. add better handling of args
        #  we intend to preserve
        newArgs = ['*args']
        for flagName, flagInfo in self.info['flags'].items():
            typ = self.getFlagType(flagInfo)
            newArgs.append('%s: %s = ...' % (flagName, typ))
            shortName = flagInfo['shortname']
            if shortName != flagName:
                newArgs.append('%s: %s = ...' % (shortName, typ))
        return newArgs

    def getSignature(self) -> str:
        return 'def %s(%s) -> Any: ...\n' % (self.name, ', '.join(self.getArgs()))
