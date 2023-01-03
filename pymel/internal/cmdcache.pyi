from typing import *
from . import cachebase as cachebase, plogging as plogging
from _typeshed import Incomplete

TYPE_CHECKING: bool
FlagInfo: Incomplete
CommandInfo: Incomplete
NodeHierarchy = List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]]
CmdInfoCacheType = Tuple[CommandInfo, NodeHierarchy, List[str], List[str], Dict[str, List[str]]]
SparseFlagInfo: Incomplete
SparseCommandInfo: Incomplete
moduleNameShortToLong: Incomplete
moduleCommandAdditions: Incomplete
secondaryFlags: Incomplete
UI_COMMANDS: Incomplete
nodeTypeToNodeCommand: Incomplete
cmdlistOverrides: Incomplete

def getInternalCmds(errorIfMissing: bool = ...): ...
def getCmdInfoBasic(command: str) -> CommandInfo: ...
def getCmdInfo(command: str, version: str, python: bool = ...) -> CommandInfo: ...
def fixCodeExamples(style: str = ..., force: bool = ...): ...
def getModuleCommandList(category, version: Incomplete | None = ...): ...
def getCallbackFlags(cmdInfo): ...
def getModule(funcName, knownModuleCmds): ...
def cmdArgMakers(force: bool = ...): ...
def nodeCreationCmd(func, nodeType): ...
def testNodeCmd(funcName, cmdInfo, nodeCmd: bool = ..., verbose: bool = ...): ...

class CmdExamplesCache(cachebase.PymelCache):
    NAME: str
    DESC: str
    USE_VERSION: bool

class CmdProcessedExamplesCache(CmdExamplesCache):
    USE_VERSION: bool

class CmdDocsCache(cachebase.PymelCache):
    NAME: str
    DESC: str

class CmdCache(cachebase.SubItemCache):
    NAME: str
    DESC: str
    ITEM_TYPES: Incomplete
    nodeHierarchy: Incomplete
    uiClassList: Incomplete
    nodeCommandList: Incomplete
    moduleCmds: Incomplete
    def rebuild(self) -> None: ...
    def build(self) -> CmdInfoCacheType: ...
    def fromRawData(self, data): ...
    def toRawData(self, data): ...
