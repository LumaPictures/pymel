from testingutils import TestCaseExtended, isEquivalenceRelation
from pymel.api.conversions import *

class TestConversions(TestCaseExtended):
    
    # test ApiClassesToApiEnums equivalence
    
    # test that nodes in _ls(nodeTypes=True) are createable, nodes NOT in it AREN'T
    
    # test against 'old' values of reserved maya types
    
    # test that all maya types found in old methods still found
    
    # test that dynamically created maya nodeHierarchy agrees with doc-parsed nodeHierarchy

    # test that for all MFnX, MFnX.hasObj(mObj) == mObj.hasFn(MFnX.type())
    
    # test that for all mayatypes, if we create a node of that type, MFnDependencyNode.typeName() agrees with
    # original value
    
    #test that MayaTypesToApiEnums is one-to-one relation
    
    # test that MayaTypesToApiEnums builds ApiEnumsToMayaTypes correctly on initialization
    pass


def oldNewCacheCompare():
    import pymel.api as api
    
    oldReserved = set(old.ReservedMayaTypes().iterkeys())
    newReserved = set(api.conversions._MayaTypesBuilder()[api.ReservedMayaTypes])
    oldAll = oldReserved.union(old.MayaTypesToApiEnums().iterkeys())
    newAll = newReserved.union(api.conversions._MayaTypesBuilder()[api.MayaTypesToApiEnums].iterkeys())
    oldAllNotNewAll = oldAll - newAll
    newAllNotOldAll = newAll - oldAll
    print("(all) In old but not in new:")
    print(oldAllNotNewAll)
    print
    print("(all) In new but not in old:")
    print(newAllNotOldAll )
    print
    print("(reserved) In old but not in new:")
    print(oldReserved - newReserved - oldAllNotNewAll )
    print
    print("(reserved) In new but not in old:")
    print(newReserved - oldReserved - newAllNotOldAll )