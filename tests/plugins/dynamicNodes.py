'''While new node types are generally created within the initializePlugin
call of a plugin, there is actually no requirement that this is the case.
Pymel therefore needs to be able to handle nodes created at any time - at least
for pymel.nodetypes.MyNodeType style access - so this plugin allows dynamic
node creation at any time, to test this.'''

import pymel.api.plugins as plugins
import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx

createdNodes = []

class addDynamicNodeCommand(plugins.Command):
    _name = 'addDynamicNode'

    @classmethod
    def createSyntax(cls):
        syntax = om.MSyntax()
        # the node type name
        syntax.addArg(om.MSyntax.kString)
        return syntax

    def doIt(self, args):
        argParser =  om.MArgParser(self.syntax(), args)
        nodeTypeName = argParser.commandArgumentString(0)
        print "creating node type: {}".format(nodeTypeName)
        createNode(nodeTypeName)


def createNode(nodeName, plugin=None):
    if isinstance(nodeName, unicode):
        nodeName = nodeName.encode('ascii')

    class NewNode(plugins.DependNode):
        _name = nodeName

        @classmethod
        def initialize(cls):
            nAttr = om.MFnNumericAttribute()
            cls.aFloat = nAttr.create("aFloat", "af", om.MFnNumericData.kFloat, 0.0)
            cls.addAttribute(cls.aFloat)

    if plugin is None:
        plugin = mpx.MFnPlugin.findPlugin('dynamicNodes')

    NewNode.__name__ = nodeName
    NewNode.register(plugin)
    createdNodes.append(NewNode)

## initialize the script plug-in
def initializePlugin(mobject):
    addDynamicNodeCommand.register(mobject)
    createNode('initialNode', plugin=mobject)

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    for nodeType in createdNodes:
        nodeType.deregister(mobject)
    addDynamicNodeCommand.deregister(mobject)
