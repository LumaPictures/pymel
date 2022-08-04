from typing import *

def parseVersionStr(versionStr: str, extension: bool = ...) -> str: ...
def bitness() -> int: ...

v85: int
v85_SP1: int
v2008: int
v2008_SP1: int
v2008_EXT2: int
v2009: int
v2009_EXT1: int
v2009_SP1A: int
v2010: int
v2011: int
v2011_HOTFIX1: int
v2011_HOTFIX2: int
v2011_HOTFIX3: int
v2011_SP1: int
v2012: int
v2012_HOTFIX1: int
v2012_HOTFIX2: int
v2012_HOTFIX3: int
v2012_HOTFIX4: int
v2012_SP1: int
v2012_SAP1 = v2012_SP1
v2012_SP2: int
v2012_SAP1SP1 = v2012_SP2
v2013: int
v2014: int
v2014_SP1: int
v2014_SP2: int
v2014_SP3: int
v2014_EXT1: int
v2014_EXT1SP1: int
v2014_EXT1SP2: int
v2015: int
v2015_SP1: int
v2015_SP2: int
v2015_SP3: int
v2015_SP4: int
v2015_EXT1: int
v2015_SP5: int
v2015_EXT1SP5: int
v2016: int
v2016_SP3: int
v2016_SP4: int
v2016_EXT1 = v2016_SP3
v2016_EXT1SP4 = v2016_SP4
v20165: int
v2016_EXT2 = v20165
v20165_SP1: int
v2016_EXT2SP1 = v20165_SP1
v20165_SP2: int
v2016_EXT2SP2 = v20165_SP2
v2017: int
v2017U1: int
v2017U2: int
v2017U3: int
v2018: int
v2018_1: int
v2018_2: int
v2018_3: int
v2018_4: int
v2018_5: int
v2018_6: int
v2018_7: int
v2019: int
v2019_1: int
v2019_2: int
v2019_3: int
v2020: int
v2020_1: int
v2020_2: int
v2020_3: int
v2020_4: int
v2021: int
v2022: int
v2023: int

def current() -> int: ...
def fullName() -> str: ...
def installName() -> str: ...
def shortName() -> str: ...
def is64bit() -> bool: ...
def flavor() -> str: ...
def isUnlimited() -> bool: ...
def isComplete() -> bool: ...
def isRenderNode() -> bool: ...
def isEval() -> bool: ...
