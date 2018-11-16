import os
import unittest
import tempfile
import shutil
import itertools
from pprint import pprint

import pymel.core as pm
import pymel.versions
import maya.cmds as cmds

class testCase_references(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.mkdtemp(prefix='referencesTest')
        print "created temp dir: %s" % self.temp

        # Refs:
        #  sphere.ma
        #    (no refs)
        #  cube.ma
        #    :sphere => sphere.ma
        #  cone.ma
        #    :cubeInCone => cube.ma
        #      :cubeInCone:sphere => sphere.ma
        #  master.ma
        #    :sphere1 => sphere.ma
        #    :sphere2 => sphere.ma
        #    :cube1 => cube.ma
        #      :cube1:sphere => sphere.ma
        #    :cone1 => cone.ma
        #      :cone1:cubeInCone => cube.ma
        #        :cone1:cubeInCone:sphere => sphere.ma

        # create sphere file
        print "sphere file"
#        cmds.file(new=1, f=1)
        pm.newFile(f=1)
        sphere = pm.polySphere()
        # We will use this to test failed ref edits...
        pm.addAttr(sphere, ln='zombieAttr')
        self.sphereFile = pm.saveAs( os.path.join( self.temp, 'sphere.ma' ), f=1 )

        # create cube file
        print "cube file"
        pm.newFile(f=1)
        pm.polyCube()
        pm.createReference( self.sphereFile, namespace='sphere' )
        pm.PyNode('sphere:pSphere1').attr('translateX').set(2)
        self.cubeFile = pm.saveAs( os.path.join( self.temp, 'cube.ma' ), f=1 )

        # create cone file
        print "cone file"
        pm.newFile(f=1)
        pm.polyCone()
        pm.createReference( self.cubeFile, namespace='cubeInCone' )
        pm.PyNode('cubeInCone:pCube1').attr('translateZ').set(2)
        pm.PyNode('cubeInCone:sphere:pSphere1').attr('translateZ').set(2)
        self.coneFile = pm.saveAs( os.path.join( self.temp, 'cone.ma' ), f=1 )

        print "master file"
        pm.newFile(f=1)
        self.sphereRef1 = pm.createReference( self.sphereFile, namespace='sphere1' )
        pm.PyNode('sphere1:pSphere1').attr('translateY').set(2)
        self.sphereRef2 = pm.createReference( self.sphereFile, namespace='sphere2' )
        pm.PyNode('sphere2:pSphere1').attr('translateY').set(4)
        self.cubeRef1 = pm.createReference( self.cubeFile, namespace='cube1' )
        pm.PyNode('cube1:sphere:pSphere1').attr('translateY').set(6)
        pm.PyNode('cube1:pCube1').attr('translateY').set(6)
        self.coneRef1 = pm.createReference( self.coneFile, namespace='cone1' )
        self.masterFile = pm.saveAs(os.path.join(self.temp, 'master.ma'), f=1)

    def tearDown(self):
        pm.newFile(f=1)
        shutil.rmtree(self.temp, ignore_errors=True)

    def createFailedEdits(self):
        # Animate the zombieAttrs
        for transform in [x.getParent() for x in pm.ls(type='mesh')]:
            try:
                zombie = transform.attr('zombieAttr')
            except pm.MayaAttributeError:
                continue
            zombie.setKey(t=1, v=1)
            zombie.setKey(t=2, v=2)
            zombie.setKey(t=3, v=4)

        # want to create another successful edit, so we can tell just by number of edits
        # whether we got failed, successful, or both
        #   failed = 1
        #   successful = 2
        #   both = 3
        pm.setAttr(self.sphereRef1.namespace + ':pSphere1.rotate', (30,0,0))

        self.masterFile = pm.saveAs(os.path.join(self.temp, 'master.ma'), f=1)


        # deleting the attr should give some failed ref edits in the master...
        pm.openFile(self.sphereFile, f=1)
        pm.SCENE.pSphere1.zombieAttr.delete()
        pm.saveFile(f=1)

        pm.openFile(self.masterFile, f=1)
        self.sphereRef1 = pm.FileReference(namespace='sphere1')
        self.sphereRef2 = pm.FileReference(namespace='sphere2')
        self.cubeRef1 = pm.FileReference(namespace='cube1')
        self.coneRef1 = pm.FileReference(namespace='cone1')

    def test_iterRefs_depth(self):
        # Test that each subsequent ref is either a child of the previous ref,
        # or the sibling of of some ref higher in the stack'''
        refStack = []
        for ref in pm.iterReferences(recursive=True):
            splitNS = ref.fullNamespace.split(':')
            if len(splitNS) <= len(refStack):
                refStack = refStack[:len(splitNS) - 1]

            self.assertEqual(splitNS[:-1], refStack)
            refStack.append(ref.namespace)

    def test_iterRefs_breadth(self):
        # Test that each subsequent ref is has a recursive depth >= the
        # previous ref
        refDepth = 0
        for ref in pm.iterReferences(recursive=True, recurseType='breadth'):
            splitNS = ref.fullNamespace.split(':')
            thisDepth = len(splitNS)
            self.assertTrue(thisDepth >= refDepth)
            refDepth = thisDepth

    def test_basic_file_cmds(self):
        print "Exporting all", os.path.join( self.temp, 'all.ma' )
        expFile = pm.exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)
        print "Importing"
        # if we don't do this newFile first, maya crashes...
        #   BSPR-18231 Maya crashes on import after exporting with references
        pm.newFile(f=1)
        pm.importFile( expFile )
        print "Exporting all"
        pm.exportAll( os.path.join( self.temp, 'all.ma' ), preserveReferences=1, force=1)
        print "Exporting animation"
        pm.exportAnim( os.path.join( self.temp, 'anim.ma' ), force=1)
        pm.select(pm.SCENE.persp)
        print "Exporting selected animation"
        pm.exportSelectedAnim( os.path.join( self.temp, 'selAnim.ma' ), force=1)

    def test_file_reference(self):
        self.assert_( isinstance( self.sphereRef1, pm.FileReference ) )
        self.assert_( isinstance( self.sphereRef1.refNode, pm.PyNode ) )
        self.assert_( self.sphereRef1.namespace == 'sphere1' )
        self.assert_( self.sphereRef1.isLoaded() )
        self.sphereRef1.unload()
        self.assert_( self.sphereRef1.isDeferred() )
        self.sphereRef1.load()
        self.sphereRef1.exportAnim( os.path.join( self.temp, 'refAnim.ma' ), force=1 )
        pm.select( self.sphereRef1.nodes() )
        self.sphereRef1.exportSelectedAnim( os.path.join( self.temp, 'selRefAnim.ma' ), force=1 )
        self.sphereRef1.remove()
        self.sphereRef2.importContents()

    def test_file_reference_creation(self):
        for ref in pm.listReferences(recursive=True):
            self.assertEqual(ref, pm.FileReference(pm.PyNode(ref.refNode)))
            self.assertEqual(ref, pm.FileReference(str(ref.refNode)))
            self.assertEqual(ref, pm.FileReference(pm.Path(ref.withCopyNumber())))
            self.assertEqual(ref, pm.FileReference(str(ref.withCopyNumber())))
            self.assertEqual(ref, pm.FileReference(namespace=ref.fullNamespace))

    def test_file_reference_remove_merge_namespace_parent(self):
        pm.openFile(self.masterFile, f=1)
        self.sphereRef1 = pm.FileReference(namespace='sphere1')
        pm.system.Namespace('sphere1').setCurrent()
        pm.system.Namespace.create('foobar')
        pm.system.Namespace('sphere1:foobar').setCurrent()
        pm.modeling.polyCube(n='testCube')
        self.tempRef1 = pm.system.createReference(self.sphereFile, namespace='foobar')
        pm.modeling.polyCube(n=':sphere1:foobar:foobar:bob')
        self.assertTrue(cmds.objExists(':sphere1:foobar:testCube'))
        self.assertTrue(cmds.objExists(':sphere1:foobar:foobar:bob'))
        self.assertFalse(cmds.objExists(':testCube'))
        self.assertFalse(cmds.objExists(':sphere1:testCube'))
        self.assertFalse(cmds.objExists(':sphere1:foobar1:testCube'))
        self.assertFalse(cmds.objExists(':sphere1:foobar:foobar:testCube'))
        self.assertFalse(cmds.objExists(':bob'))
        self.assertFalse(cmds.objExists(':sphere1:bob'))
        self.assertFalse(cmds.objExists(':sphere1:foobar:bob'))
        self.assertFalse(cmds.objExists(':sphere1:foobar1:bob'))
        pm.system.FileReference(self.tempRef1).remove(mergeNamespaceWithParent=1)
        # Before maya 2018, there was a bug where removing the ref, which lives
        # in "sphere1:foobar:foobar", would also delete "sphere1:foobar" -
        # leaving just "sphere1:", where everything was moved into...
        if pymel.versions.current() < pymel.versions.v2018:
            # when it deletes sphere1:foobar, it tries to move sphere1:foobar:foobar
            # to sphere1:foobar... but apparently that causes a name conflict,
            # so it makes sphere1:foobar1 instead
            self.assertTrue(cmds.objExists(':sphere1:testCube'))
            self.assertTrue(cmds.objExists(':sphere1:foobar1:bob'))
            self.assertFalse(cmds.objExists(':testCube'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:testCube'))
            self.assertFalse(cmds.objExists(':sphere1:foobar1:testCube'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:foobar:testCube'))
            self.assertFalse(cmds.objExists(':bob'))
            self.assertFalse(cmds.objExists(':sphere1:bob'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:bob'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:foobar:bob'))
        else:
            self.assertTrue(cmds.objExists(':sphere1:foobar:testCube'))
            self.assertTrue(cmds.objExists(':sphere1:foobar:bob'))
            self.assertFalse(cmds.objExists(':testCube'))
            self.assertFalse(cmds.objExists(':sphere1:testCube'))
            self.assertFalse(cmds.objExists(':sphere1:foobar1:testCube'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:foobar:testCube'))
            self.assertFalse(cmds.objExists(':bob'))
            self.assertFalse(cmds.objExists(':sphere1:bob'))
            self.assertFalse(cmds.objExists(':sphere1:foobar1:bob'))
            self.assertFalse(cmds.objExists(':sphere1:foobar:foobar:bob'))


    def test_file_reference_remove_merge_namespace_root(self):
        pm.openFile(self.masterFile, f=1)
        self.sphereRef1 = pm.FileReference(namespace='sphere1')
        pm.system.Namespace('sphere1').setCurrent()
        pm.modeling.polyCube(n='testCube')
        pm.system.FileReference(self.sphereRef1).remove(mergeNamespaceWithRoot=1)
        self.assertIn('testCube', pm.system.namespaceInfo(':', ls=1))

    def test_file_reference_remove_force(self):
        pm.openFile(self.masterFile, f=1)
        self.sphereRef1 = pm.FileReference(namespace='sphere1')
        pm.system.Namespace('sphere1').setCurrent()
        pm.modeling.polyCube(n='testCube')
        pm.system.FileReference(self.sphereRef1).remove(force=True)
        self.assertFalse(pm.general.objExists('testCube'))

    def test_failed_ref_edits(self):
        self.createFailedEdits()

        sphereRefs = [x for x in pm.listReferences(recursive=True)
                      if x.path.endswith('sphere.ma')]
        for ref in sphereRefs:
            print "testing failed ref edits on: %s" % ref
            self.assertEqual(1, len(pm.referenceQuery(ref,successfulEdits=False,failedEdits=True,es=True)))
            self.assertEqual(1, len(cmds.referenceQuery(str(ref.refNode), successfulEdits=False,failedEdits=True,es=True)))

    def test_import(self):
        ref = self.sphereRef1
        sphere = 'sphere1:pSphere1'
        self.assertTrue(pm.PyNode(sphere).isReferenced())
        ref.importContents()
        self.assertFalse(pm.PyNode(sphere).isReferenced())

    def test_import_remove_namespace(self):
        ref = self.sphereRef1
        nsSphere = 'sphere1:pSphere1'
        noNsSphere = 'pSphere1'
        self.assertTrue(pm.PyNode(nsSphere).isReferenced())
        self.assertFalse(pm.objExists(noNsSphere))
        ref.importContents(removeNamespace=True)
        self.assertFalse(pm.objExists(nsSphere))
        self.assertFalse(pm.PyNode(noNsSphere).isReferenced())

    def test_getReferenceEdits(self):
        def doTest(successfulEdits, failedEdits, force, expectedNum):
            self.setUp()
            self.createFailedEdits()

            # Should have 3 total, 2 successful, 1 failed
            refNode = str(self.sphereRef1.refNode)
            testKwargs = {'editStrings':True, 'onReferenceNode':refNode}

            testKwargs['successfulEdits'] = False
            testKwargs['failedEdits'] = True
            self.assertEqual(len(cmds.referenceQuery(refNode, **testKwargs)), 1)

            testKwargs['successfulEdits'] = True
            testKwargs['failedEdits'] = False
            self.assertEqual(len(cmds.referenceQuery(refNode, **testKwargs)), 2)

            testKwargs['successfulEdits'] = True
            testKwargs['failedEdits'] = True
            self.assertEqual(len(cmds.referenceQuery(refNode, **testKwargs)), 3)

            kwargs = {}
            if successfulEdits is not None:
                kwargs['successfulEdits'] = successfulEdits
            if failedEdits is not None:
                kwargs['failedEdits'] = failedEdits

            self.assertEqual(len(self.sphereRef1.getReferenceEdits(**kwargs)),
                             expectedNum)

        for force in (True, False):
            doTest(None, None, force, 3)    # should get all
            doTest(None, True, force, 1)    # should get failed
            doTest(None, False, force, 2)   # should get successful

            doTest(True, None, force, 2)    # should get successful
            doTest(True, True, force, 3)    # should get all
            doTest(True, False, force, 2)   # should get successful

            doTest(False, None, force, 1)   # should get failed
            doTest(False, True, force, 1)   # should get failed
            doTest(False, False, force, 0)  # should get none


    def test_removeReferenceEdits(self):
        def doTest(successfulEdits, failedEdits, force, expectedNum):
            self.setUp()
            self.createFailedEdits()

            # Should have 3 total, 2 successful, 1 failed
            refNode = str(self.sphereRef1.refNode)
            getKwargs = {'editStrings':True, 'onReferenceNode':refNode}

            getKwargs['successfulEdits'] = False
            getKwargs['failedEdits'] = True
            self.assertEqual(len(cmds.referenceQuery(refNode, **getKwargs)), 1)

            getKwargs['successfulEdits'] = True
            getKwargs['failedEdits'] = False
            self.assertEqual(len(cmds.referenceQuery(refNode, **getKwargs)), 2)

            getKwargs['successfulEdits'] = True
            getKwargs['failedEdits'] = True
            self.assertEqual(len(cmds.referenceQuery(refNode, **getKwargs)), 3)

            kwargs = {}
            if successfulEdits is not None:
                kwargs['successfulEdits'] = successfulEdits
            if failedEdits is not None:
                kwargs['failedEdits'] = failedEdits

            if force:
                kwargs['force'] = True

            self.sphereRef1.removeReferenceEdits(**kwargs)

            self.assertEqual(len(cmds.referenceQuery(refNode, **getKwargs)),
                             expectedNum)

        # force=True - possible to remove successful edits
        doTest(None, None, True, 0)    # should remove all
        doTest(None, True, True, 2)    # should remove failed
        doTest(None, False, True, 1)   # should remove successful
        doTest(True, None, True, 1)    # should remove successful
        doTest(True, True, True, 0)    # should remove all
        doTest(True, False, True, 1)   # should remove successful
        doTest(False, None, True, 2)   # should remove failed
        doTest(False, True, True, 2)   # should remove failed
        doTest(False, False, True, 3)  # should remove none

        # force=False - not possible to remove successful edits
        doTest(None, None, False, 2)    # should remove failed (tries: all)
        doTest(None, True, False, 2)    # should remove failed (tries: failed)
        doTest(None, False, False, 3)   # should remove none (tries: successful)
        doTest(True, None, False, 3)    # should remove none (tries: successful)
        doTest(True, True, False, 2)    # should remove failed (tries: all)
        doTest(True, False, False, 3)   # should remove none (tries: successful)
        doTest(False, None, False, 2)   # should remove failed (tries: failed)
        doTest(False, True, False, 2)   # should remove failed (tries: failed)
        doTest(False, False, False, 3)  # should remove none (tries: none)


    def test_parent(self):
        self.assertEqual(pm.FileReference(namespace='sphere1').parent(), None)
        self.assertEqual(pm.FileReference(namespace='sphere2').parent(), None)
        self.assertEqual(pm.FileReference(namespace='cube1').parent(), None)
        self.assertEqual(pm.FileReference(namespace='cone1').parent(), None)

        self.assertEqual(pm.FileReference(namespace='cube1:sphere').parent(),
                         pm.FileReference(namespace='cube1'))
        self.assertEqual(pm.FileReference(namespace='cone1:cubeInCone').parent(),
                         pm.FileReference(namespace='cone1'))
        self.assertEqual(pm.FileReference(namespace='cone1:cubeInCone:sphere').parent(),
                         pm.FileReference(namespace='cone1:cubeInCone'))

    def test_listReferences(self):
        self.assertEqual(set(pm.listReferences()),
                         set([pm.FileReference(namespace='sphere1'),
                              pm.FileReference(namespace='sphere2'),
                              pm.FileReference(namespace='cube1'),
                              pm.FileReference(namespace='cone1'),
                             ]))

    def test_listReferences_recursive(self):
        self.assertEqual(set(pm.listReferences(recursive=True)),
                         set([pm.FileReference(namespace='sphere1'),
                              pm.FileReference(namespace='sphere2'),
                              pm.FileReference(namespace='cube1'),
                              pm.FileReference(namespace='cone1'),
                              pm.FileReference(namespace='cube1:sphere'),
                              pm.FileReference(namespace='cone1:cubeInCone'),
                              pm.FileReference(namespace='cone1:cubeInCone:sphere'),
                             ]))

    def _test_listReferences_options(self, expectedRefs, kwargs):
        for namespaces in (True, False):
            for refNodes in (True, False):
                for references in (True, False):
                    expected = set()
                    for ref in expectedRefs:
                        thisExpected = []
                        if namespaces:
                            thisExpected.append(ref.fullNamespace)
                        if refNodes:
                            thisExpected.append(ref.refNode)
                        if references:
                            thisExpected.append(ref)
                        if len(thisExpected) == 1:
                            thisExpected = thisExpected[0]
                        else:
                            thisExpected = tuple(thisExpected)
                        expected.add(thisExpected)
                    result = pm.listReferences(namespaces=namespaces,
                                               refNodes=refNodes,
                                               references=references,
                                               **kwargs)
                    self.assertEqual(set(result), expected)

    def test_listReferences_options(self):
        expectedRefs = set([pm.FileReference(namespace='sphere1'),
                            pm.FileReference(namespace='sphere2'),
                            pm.FileReference(namespace='cube1'),
                            pm.FileReference(namespace='cone1'),
                           ])
        self._test_listReferences_options(expectedRefs, {})

    def test_listReferences_options_recursive(self):
        expectedRefs = set([pm.FileReference(namespace='sphere1'),
                            pm.FileReference(namespace='sphere2'),
                            pm.FileReference(namespace='cube1'),
                            pm.FileReference(namespace='cone1'),
                            pm.FileReference(namespace='cube1:sphere'),
                            pm.FileReference(namespace='cone1:cubeInCone'),
                            pm.FileReference(namespace='cone1:cubeInCone:sphere'),
                           ])
        self._test_listReferences_options(expectedRefs, {'recursive':True})

    def test_listReferences_loaded_unloaded(self):
        def doTestForKwargPermutation(loaded, unloaded, expected):
            kwargs = {}
            if loaded is not None:
                kwargs['loaded'] = loaded
            if unloaded is not None:
                kwargs['unloaded'] = unloaded

            allRefs = pm.listReferences(recursive=True)

            if expected == 'all':
                expected = set(allRefs)
            elif expected == 'loaded':
                expected = set(x for x in allRefs if x.isLoaded())
            elif expected == 'unloaded':
                expected = set(x for x in allRefs if not x.isLoaded())
            elif expected == 'none':
                expected = set()
            else:
                raise ValueError(expected)

            result = set(pm.listReferences(recursive=True, **kwargs))
            self.assertEqual(result, expected)

            expected = set(x for x in expected if x.parent() is None)
            result = set(pm.listReferences(recursive=False, **kwargs))
            self.assertEqual(result, expected)

        def doTestForRefPermuation(loadedByNS):
            self.setUp()

            # Note that we always need to track by namespace... we cannot use
            # persistant FileReferences objects, since they are tied to
            # a reference node... and if a parent reference node is unloaded,
            # they may be come invalid

            for ns, loaded in loadedByNS.iteritems():
                if not loaded:
                    ref = pm.FileReference(namespace=ns)
                    if not loaded:
                        print "unloading: %r" % ns
                        ref.unload()

            pprint(loadedByNS)

            # All files should now be set up with the appropriate
            # loaded/unloaded refs... confirm
            for ns, loaded in loadedByNS.iteritems():
                try:
                    wasLoaded = pm.FileReference(namespace=ns).isLoaded()
                except RuntimeError:
                    wasLoaded = False
                self.assertEqual(loaded, wasLoaded)

            doTestForKwargPermutation(None, None, 'all')
            doTestForKwargPermutation(None, True, 'unloaded')
            doTestForKwargPermutation(None, False, 'loaded')

            doTestForKwargPermutation(True, None, 'loaded')
            doTestForKwargPermutation(True, True, 'all')
            doTestForKwargPermutation(True, False, 'loaded')

            doTestForKwargPermutation(False, None, 'unloaded')
            doTestForKwargPermutation(False, True, 'unloaded')
            doTestForKwargPermutation(False, False, 'none')

        def loadedRefPermutations(parentReference=None):
            '''Returns dicts mapping from namespaces to whether they are loaded
            or not

            Returns all possible such dicts, taking into account the fact that
            if a ref is unloaded, all it's subrefs will also be unloaded (and,
            in fact, won't even seem to exist)
            '''
            finalPermutations = []

            namespaces = pm.listReferences(parentReference=parentReference,
                                           namespaces=True,
                                           references=False)

            # now, get all the possible permutations for each sub-ref, assuming
            # that sub-ref is loaded

            subPermutationsByNS = {}
            for namespace in namespaces:
                subsForNS = loadedRefPermutations(parentReference=pm.FileReference(namespace=namespace))
                if subsForNS:
                    subPermutationsByNS[namespace] = subsForNS

            # Now get all loaded/unloaded permutations for top namespaces...
            for loadedVals in itertools.product((True, False),
                                                repeat=len(namespaces)):
                topByNamespace = dict(zip(namespaces, loadedVals))

                # then, find any sub-permutations for refs which are loaded
                possibleSubPermutations = []
                for ns, loaded in topByNamespace.iteritems():
                    if loaded and ns in subPermutationsByNS:
                        possibleSubPermutations.append(subPermutationsByNS[ns])

                # finally, if we iterate over all the products of all possible
                # sub-perms, and combine all the resulting dicts, we should
                # get all the final permutations...
                if possibleSubPermutations:
                    for subPermSelections in itertools.product(*possibleSubPermutations):
                        topCopy = dict(topByNamespace)
                        for subPermItem in subPermSelections:
                            topCopy.update(subPermItem)
                        finalPermutations.append(topCopy)
                else:
                    # there are no sub-permutations, just append the current
                    # permutation for top-level refs
                    finalPermutations.append(topByNamespace)
            return finalPermutations

        allPerms = loadedRefPermutations()
        # sanity check - should be 48 perms
        self.assertEqual(len(allPerms), 48)
        for loadedByNS in allPerms:
            doTestForRefPermuation(loadedByNS)

    def test_fullNamespace(self):
        # first, test that the namespaces are as expected, when all the ref
        # nodes are "normal" / unaltered

        expected = [
            (u'sphere1',
             pm.FileReference(u'/usr/tmp/referencesTest/sphere.ma',
                               refnode=u'sphere1RN')),
            (u'sphere2',
             pm.FileReference(u'/usr/tmp/referencesTest/sphere.ma{1}',
                              refnode=u'sphere2RN')),
            (u'cube1',
             pm.FileReference(u'/usr/tmp/referencesTest/cube.ma',
                              refnode=u'cube1RN')),
            (u'cube1:sphere',
             pm.FileReference(u'/usr/tmp/referencesTest/sphere.ma{2}',
                              refnode=u'cube1:sphereRN')),
            (u'cone1',
             pm.FileReference(u'/usr/tmp/referencesTest/cone.ma',
                              refnode=u'cone1RN')),
            (u'cone1:cubeInCone',
             pm.FileReference(u'/usr/tmp/referencesTest/cube.ma{1}',
                              refnode=u'cone1:cubeInConeRN')),
            (u'cone1:cubeInCone:sphere',
             pm.FileReference(u'/usr/tmp/referencesTest/sphere.ma{3}',
                              refnode=u'cone1:cubeInCone:sphereRN'))
        ]

        self.assertEqual(pm.listReferences(namespaces=1, recursive=1),
                         expected)

        self.assertEqual(self.coneRef1.namespace, 'cone1')
        self.assertEqual(self.coneRef1.fullNamespace, 'cone1')
        self.assertEqual(self.coneRef1.refNode.namespace(), '')

        cubeInConeRef = pm.FileReference(refnode='cone1:cubeInConeRN')
        self.assertEqual(cubeInConeRef.namespace, 'cubeInCone')
        self.assertEqual(cubeInConeRef.fullNamespace, 'cone1:cubeInCone')
        self.assertEqual(cubeInConeRef.refNode.namespace(), 'cone1:')

        sphereInCubeInConeRef = pm.FileReference(refnode='cone1:cubeInCone:sphereRN')
        self.assertEqual(sphereInCubeInConeRef.namespace, 'sphere')
        self.assertEqual(sphereInCubeInConeRef.fullNamespace,
                         'cone1:cubeInCone:sphere')
        self.assertEqual(sphereInCubeInConeRef.refNode.namespace(),
                         'cone1:cubeInCone:')

        # now, try changing the namespace of one of the refnodes...
        pm.Namespace.create('foobar')
        coneRefNode = self.coneRef1.refNode
        coneRefNode.unlock()
        coneRefNode.rename('foobar:%s' % coneRefNode)
        coneRefNode.lock()

        # now, make sure that results are as expected (ie, the namespace of the
        # reference itself should be UNCHANGED, even though the namespace of the
        # reference node has changed...
        self.assertEqual(pm.listReferences(namespaces=1, recursive=1),
                         expected)

        self.assertEqual(self.coneRef1.namespace, 'cone1')
        self.assertEqual(self.coneRef1.fullNamespace, 'cone1')
        self.assertEqual(self.coneRef1.refNode.namespace(), 'foobar:')

        self.assertEqual(cubeInConeRef.namespace, 'cubeInCone')
        self.assertEqual(cubeInConeRef.fullNamespace, 'cone1:cubeInCone')
        self.assertEqual(cubeInConeRef.refNode.namespace(), 'cone1:')

        self.assertEqual(sphereInCubeInConeRef.namespace, 'sphere')
        self.assertEqual(sphereInCubeInConeRef.fullNamespace,
                         'cone1:cubeInCone:sphere')
        self.assertEqual(sphereInCubeInConeRef.refNode.namespace(),
                         'cone1:cubeInCone:')

    def test_live_edits_returning_an_empty_list(self):
        """testing if the le=True or liveEdits=True with no reference edit will
        return an empty list
        """
        # create a new reference with no edits
        ref = pm.createReference(self.sphereFile, namespace='sphere')
        edits = pm.referenceQuery(ref, es=1, le=1)
        self.assertEqual(edits, [])

class testCase_fileInfo(unittest.TestCase):
    # Only need to test these methods, because we've based the fileInfo on
    # collections.MutableMapping, and this is these are the required methods to implement that interface.
    # __delitem__, __getitem__, __iter__, __len__, __setitem__



    def setUp(self):
        pm.newFile(f=1)
        self.rawDict = {'testKey': 'testValue'}
        for key, val in self.rawDict.iteritems():
            cmds.fileInfo(key, val)

    def test_get(self):
        default = "the default value!"
        self.assertEqual(pm.fileInfo.get('NoWayDoIExist', default), default)
        self.assertEqual(pm.fileInfo.get('NoWayDoIExist'), None)
        self.assertEqual(pm.fileInfo.get('testKey'), cmds.fileInfo('testKey', q=1)[0])
        self.assertEqual(pm.fileInfo.get('testKey'), self.rawDict['testKey'])

    def test_getitem(self):
        self.assertRaises(KeyError, lambda: pm.fileInfo['NoWayDoIExist'])
        self.assertEqual(pm.fileInfo['testKey'], cmds.fileInfo('testKey', q=1)[0])
        self.assertEqual(pm.fileInfo['testKey'], self.rawDict['testKey'])

    def test_delitem(self):
        _dict = {}
        self.assertNotEqual(_dict.items(), pm.fileInfo.items())
        del pm.fileInfo['testKey']
        self.assertEqual(_dict.items(), pm.fileInfo.items())

    def test_iter(self):
        self.assertEqual(sorted(pm.fileInfo), sorted(self.rawDict))

    def test_len(self):
        self.assertEqual(len(pm.fileInfo), len(self.rawDict))


class testCase_namespaces(unittest.TestCase):
    def setUp(self):
        cmds.file(f=1, new=1)
        cmds.namespace( add='FOO' )
        cmds.namespace( add='BAR' )
        cmds.namespace( add='FRED' )
        cmds.namespace( add='BAR', parent=':FOO')
        cmds.namespace( add='CALVIN', parent=':FOO:BAR')
        cmds.sphere( n='FOO:sphere1' )
        cmds.sphere( n='FOO:sphere2' )
        cmds.sphere( n='BAR:sphere1' )
        cmds.sphere( n='FOO:BAR:sphere1' )

    def test_listNodes(self):
        self.assertEqual(set(pm.Namespace('FOO').listNodes()),
                         set([pm.PyNode('FOO:sphere1'),
                              pm.PyNode('FOO:sphere1Shape'),
                              pm.PyNode('FOO:sphere2'),
                              pm.PyNode('FOO:sphere2Shape'),
                              ]))
        self.assertEqual( set(pm.Namespace('FOO').listNodes(recursive=False)),
                          set([pm.PyNode('FOO:sphere1'),
                               pm.PyNode('FOO:sphere1Shape'),
                               pm.PyNode('FOO:sphere2'),
                               pm.PyNode('FOO:sphere2Shape'),
                               ]))
        self.assertEqual( set(pm.Namespace('FOO').listNodes(recursive=True)),
                          set([pm.PyNode('FOO:sphere1'),
                               pm.PyNode('FOO:sphere1Shape'),
                               pm.PyNode('FOO:sphere2'),
                               pm.PyNode('FOO:sphere2Shape'),
                               pm.PyNode('FOO:BAR:sphere1'),
                               pm.PyNode('FOO:BAR:sphere1Shape'),
                          ]))
    def test_listNamespaces(self):
        self.assertEqual(set(pm.Namespace('FOO').listNamespaces()),
                         set([pm.Namespace('FOO:BAR'),
                              ]))
        self.assertEqual(set(pm.Namespace('FOO').listNamespaces(recursive=False)),
                         set([pm.Namespace('FOO:BAR'),
                              ]))
        self.assertEqual(set(pm.Namespace('FOO').listNamespaces(recursive=True)),
                         set([pm.Namespace('FOO:BAR'),
                              pm.Namespace('FOO:BAR:CALVIN')
                              ]))
