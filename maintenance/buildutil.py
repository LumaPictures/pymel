"""
Code shared between build and buildstubs.

buildstubs is designed to run outside of mayapy, so do not import maya modules
here.
"""
from __future__ import absolute_import, print_function
from typing import List, Optional
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
CORE_CMD_MODULES_MAP.update({
    'pymel.core.nodetypes': 'general.PyNode',
    'pymel.core.uitypes': '_general.PyNode',
    'pymel.core.windows': '_general.PyNode',
})


def hasMode(flagInfo, mode):
    return mode in flagInfo.get('modes', [])


class MelFunctionHelper(object):

    TYPING_TYPES = [
        'Any', 'Callable', 'List', 'Optional', 'Tuple',  'Union', 'overload'
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

    def _getType(self, typ, asResult=False) -> str:
        if isinstance(typ, str):
            if typ == 'timerange':
                return 'str | Tuple[float, float] | Tuple[float]'
            elif typ == 'floatrange':
                # Note: we don't appear to add support for Tuple input like we
                # do for timerange
                return 'str | int | float'
            elif typ == 'time':
                return 'int | float'
            elif typ == 'PyNode':
                typ = CORE_CMD_MODULES_MAP.get(self.moduleName, '_general.PyNode')
                if asResult:
                    return typ
                else:
                    return '%s | str' % (typ,)
            elif typ == 'script':
                return 'str | Callable'
            elif ' ' in typ:
                # I've seen one case of bad type name in our cmdlist cache
                return 'Any'
        elif typ is bool and not asResult:
            # it's a common pattern coming from MEL to use 1/0 for True/False
            return 'bool | int'
        else:
            return typ.__name__

    def getFlagType(self, flagInfo: 'pymel.internal.cmdcache.FlagInfo',
                    asResult=False) -> str:
        if flagInfo['numArgs'] < 2:
            typ = self._getType(flagInfo['args'], asResult=asResult)
        else:
            # FIXME: this may be affected by resultNeedsUnpacking
            typ = 'Tuple[%s]' % ', '.join(
                [self._getType(arg_type, asResult=asResult)
                 for arg_type in flagInfo['args']])
        if not asResult and hasMode(flagInfo, 'multiuse'):
            typ = '%s | List[%s]' % (typ, typ)
        if not asResult and typ == 'str':
            typ = '_util.ProxyUnicode | %s' % typ
        return typ

    def getArgs(self, skip=None) -> List[str]:
        """
        Get list of argument definitions (including type) that should replace
        **kwargs
        """
        newArgs = []
        usedFlags = set()

        def addArg(name: str, typ: str) -> None:
            if name not in usedFlags:
                newArgs.append('%s: %s = ...' % (name, typ))
                usedFlags.add(name)

        for flagName, flagInfo in self.info['flags'].items():
            shortName = flagInfo['shortname']
            if skip and (flagName in skip or shortName in skip):
                continue

            typ = self.getFlagType(flagInfo, asResult=False)
            if hasMode(flagInfo, 'query') and typ != 'bool | int':
                typ = 'bool | int | %s' % typ

            addArg(flagName, typ)
            addArg(shortName, typ)

        return newArgs

    def getSignature(self) -> str:
        args = ['*args'] + self.getArgs()
        return 'def %s(%s) -> Any: ...\n' % (self.name, ', '.join(args))
