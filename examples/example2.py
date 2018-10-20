import pymel.core as pm

s = pm.polySphere()[0]  # second in list is the history node, if construction history is on
c = pm.polyCube()[0]

print c, s
c.setTranslation([0, 2, 0])
s.setTranslation([1, -2, 0])

g = pm.group(s, c, n='newGroup')

print "The children of %s are %s" % (g, g.getChildren())
# print g.getChildren()[0].getShape()
print "difference =", c.translate.get() - s.translate.get()  # basic vector operation

s2 = s.duplicate()[0]

# move the new sphere relatively along the z axis
s2.setTranslation([0, 0, -2], relative=1)

# cycle through and move some verts.
# we're moving each verts a relative amount based on its vertex number
num = s2.numVertices()
for i, vert in enumerate(s2.verts):
    pm.move(vert, [i / float(num), 0, 0], r=1)

# save the current scene scene
currScene = pm.saveAs('pymel_test_main.ma')

# the parent property gives the parent directory of the current scene.
# the / (slash or divide) operator serves as an os independent way of concatenating paths
# it is a shortut to os.path.join
exportScene = currScene.parent / 'pymel_test_ref.ma'

# if a file already exists where we want to export, delete it first
if exportScene.exists():
    print "removing existing pymel export scene"
    exportScene.remove()

print "exporting new scene:", exportScene
pm.exportSelected(exportScene, f=1)

# delete the original group
pm.delete(g)

# reference it in a few times
for i in range(1, 4):
    ref = pm.createReference(exportScene, namespace=('foo%02d' % i))
    # offset each newly created reference:
    # first we list all the nodes in the new reference, and get the first in the list.
    # this will be the 'newGroup' node.
    allRefNodes = ref.nodes()
    print "moving", allRefNodes[0]
    allRefNodes[0].tx.set(2 * i)

# print out some information about our newly created references
allRefs = pm.listReferences()
for r in allRefs:
    print r.namespace, r.refNode, r.withCopyNumber()

# the namespace property of the FileReference class can be used to set the namespace as well as to get it.
allRefs[2].namespace = 'super'

# but if we have to change the namespace of the objects after they have been imported
# there is a different, albeit, more complicated way
ns = allRefs[0].namespace
allRefs[0].importContents()

# heres one way to change the namespace
try:
    pm.namespace(add='bar')
except:
    pass

for node in pm.ls(ns + ':*', type='transform'):
    newname = node.swapNamespace('bar')
    print "renaming %s to %s" % (node, newname)
    node.rename(newname)

# unload the other one
allRefs[1].unload()
