from testingutils import TestCaseExtended, isEquivalenceRelation
import pymel.mayahook.apicache as apicache

class TestConversions(TestCaseExtended):
    
    # test ApiClassesToApiEnums equivalence
    
    # test that nodes in _ls(nodeTypes=True) are createable, nodes NOT in it AREN'T
    
    # test against 'old' values of reserved maya types
    
    # test that all maya types found in old methods still found
    
    # test that dynamically created maya nodeHierarchy agrees with doc-parsed nodeHierarchy

    # test that for all MFnX, MFnX.hasObj(mObj) == mObj.hasFn(MFnX.type())
    
    # test that for all mayatypes, if we create a node of that type, MFnDependencyNode.typeName() agrees with
    # original value
    
    #test that mayaTypesToApiEnums is one-to-one relation
    
    # test that mayaTypesToApiEnums builds apiEnumsToMayaTypes correctly on initialization
    pass


def oldNewCacheCompare():
    import pymel.api as api
    
    oldReserved = set(old.reservedMayaTypes.iterkeys())
    newReserved = set(api.conversions._MayaTypesBuilder()[api.reservedMayaTypes])
    oldAll = oldReserved.union(old.mayaTypesToApiEnums.iterkeys())
    newAll = newReserved.union(api.conversions._MayaTypesBuilder()[api.mayaTypesToApiEnums].iterkeys())
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