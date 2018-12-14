.. currentmodule:: pymel

**********
What's New
**********

==================================
Version 1.1.0
==================================

----------------------------------
Non-Backward Compatible Changes
----------------------------------
- removed support for maya versions before 2017
- general: AttributeSpec.parent() now returns None instead of erroring
- datatypes: Quaternion.asEulerRotation now returns a datatypes.EulerRotation
  as intended, instead of OpenMaya.MEulerRotation; since dt.EulerRotation
  inherits from om.MEulerRotation, they should mostly be compatible, but if you
  need a om.MEulerRotation, just cast directly - ie,
  om.MEulerRotation(dt.Quaternion().asEulerRotation())
- uitypes: OptionMenuGrp.getParent() now returns a PyUI object, instead of a
  string, as intended.  This brings it's behavior in line with most other PyUI
  .getParent() calls, including RowLayout.getParent() and Layout.getParent(),
  from which OptionMenuGrp inherits
- uitypes: PopupMenu.getItemArray() now returns PyUI objects, instead of
  strings, as intended.  This brings it's behavior in line with Menu
  .getItemArray(), from which it inherits
- nodetypes: Due to a bug, the following methods were wrapped on a random
  scattering of subclasses of the named classes. They were ever intended to be
  wrapped at all.  They are all being removed - exact methods and reasoning
  below:

  - **DagNode.setObject**: dangerous - changes the node we're wrapping out from
    underneath us
  - **DependNode.addAttribute**: dangerous, because it only took
    AttributeSpec objects as inputs. In addition to being fairly obscure,
    they are mostly constructed from existing attributes - but the API
    explicitly warns against adding an attribute using an MObject that's already
    added to another node. Use addAttr method instead.
  - **DependNode.attribute**: too confusing to have both "attr" and "attribute"
    which return different types of objects. Use attrSpec instead. Also, the old
    wrap only worked with integer indices, which wasn't useful in most
    situations (attrSpec works with either string names, Attribute objects, or
    indices).
  - **DependNode.findPlug**: dangerous, as it allowed returning networked mplugs.
    Use attr method instead. The api docs warn that networked plugs should not
    be used if you might be breaking connections, thus why these are
    considerered dangerous. Also, it only worked when fed AttributeSpec, a
    little known / used part of pymel.
  - **DependNode.reorderedAttribute**: obscure, and apparently only useful
    during file IO
  - **Shape.dagPath**: useless, as it just always returned self
  - **Shape.getPath**: useless, as it just always returned self

----------------------------------
Changes
----------------------------------
- all: The basic way methods and commands are wrapped has been altered.
  Formerly, all items were wrapped dynamically, at runtime; now, they are
  wrapped and "baked", using templates, when a pymel release is made. The end
  result should be code that is more much readable and understandable for end
  users.
- general: AttributeDefaults renamed to AttributeSpec, which better reflects
  what it is: a specification for the type on an attribute, not associated with
  any single node.  The AttributeDefaults name is preserved as an alias for
  backwards compatibility.
- nodetypes: Due to a bug, the following methods were wrapped on a random
  scattering of subclasses of the named classes. They were ever intended to be
  wrapped at all.  They are being marked as deprecated, and will raise a
  warning, if used on any of the subclasses for which they are implemented:

    DependNode.findAlias, DependNode.getAffectedAttributes, DependNode
    .getAffectedByAttributes, DependNode.getAliasList, DependNode
    .getConnections, DependNode.plugsAlias, DependNode.setAlias, Transform
    .getRotationQuaternion, Transform.setRotationQuaternion

- nodetypes: The following methods were removed from Shape: model, removeChild,
  and removeChildAt. They were never intended to be wrapped, and were non-
  functional, so removing them should not introduce any backwards-compatibility
  issues.
- nodetypes:Shape.getAllPaths was moved from Shape to DagNode, and marked
  deprecated. It was only wrapped as a result of a bug, it has a misleading name
  (it returns PyNodes, not paths), and is functionally equivalent to
  getInstances(). However, since it may have been in use, and we don't wish to
  break backward compatibility, we are marking it as deprecated.  We are moving
  it to DagNode, instead of Shape, because the fact that it was defined on
  Shape and not Transform made it give incorrect / misleading results.  This is
  because the Transform node will check it's first shape for attributes it
  can't find defined on itself - the net result is that, even though it's not
  defined on Transform, if it had a shape, it would "appear" to be, but return
  the "wrong" results - ie PyNodes corresponding to all instances of the
  first shape, NOT the transform itself.
- nodetypes: AnimCurve.timedAnimCurveTypeForPlug/unitlessAnimCurveTypeForPlug
  turned into classmethods, as they don't require / operate on a specific
  AnimCurve
- conf: add a new setting to pymel.conf, "deleted_pynode_name_access", to
  to control the behavior when a deleted node's name is queried / used.  The
  current behavior - of issuing a warning, but returning the old name - is now
  deprecated, and at some point the default will be changed to "error", which
  will cause pymel to raise a DeletedMayaNodeError.  If you wish to keep the
  old behavior - and not be nagged that it may be changed at some point the
  future - change the setting to "warn".  You may also set it to "ignore" if you
  want to not even issue a warning. (The current default setting is
  "warn_deprecated", which will behave just like "warn", except with an
  additional FutureWarning to remind you to change the setting in pymel.conf)
- util: Singleton: eliminate DeprecationWarning for object.__init__(*p, **k)
- nodetypes: tweak new constraint-weight-query syntax - we now allow
  constraint(q=1, weight=True), instead of constraint(q=1, weight=[]); also,
  may use a tuple (or other non-list iterable) for weight

- general: remove unused kwargs for Attribute.affects/affected
- uitypes: make a base PyUIContainer parent class for Layout and Window

----------------------------------
Additions
----------------------------------
- all: Add maya-2019 support
- all: python-3 / "typing" style type comments added to many / most commands
  and methods
- general: AttributeSpec may now be constructed from a string (which names an
  existing Attribute), an Attribute, an MPlug, or another AttributeSpec.
  DependNode.attrSpec now also accepts all these objects as well.
- uitypes: Many layout flags were were not wrapped on Layout; they now are,
  which also means all sub-classes inherit these methods as well (though many
  subclasses already had their own overrides for many of these commands). The
  full set of new methods on Layout is:

    dragCallback, dropCallback, getAnnotation, getBackgroundColor, getChildArray,
    getDocTag, getEnable, getEnableBackground, getFullPathName, getHeight,
    getHighlightColor, getIsObscured, getManage, getNumberOfChildren,
    getNumberOfPopupMenus, getPopupMenuArray, getPreventOverride, getVisible,
    getVisibleChangeCommand, getWidth, noBackground, setAnnotation,
    setBackgroundColor, setDocTag, setEnable, setEnableBackground, setHeight,
    setHighlightColor, setManage, setPreventOverride, setVisible,
    setVisibleChangeCommand, setWidth, statusBarMessage

- nodetypes: Some api method wraps were re-enabled on DependNode, DagNode, and
  ObjectSet. Formerly, some of these methods were implemented on some
  subclasses of these node types; they are now uniformly available on the base
  node.  Note that some of these methods represent new functionality, while
  others merely duplicate existing functionality (ie, DagNode.partialPathName
  <=> DagNode.name); however, we wanted to provide a uniform interface, and did
  not want to break backward compatibility, so they were enabled on their base
  classes. The set of new methods is:

    Camera.getFarClippingPlane, Camera.setFarClippingPlane,
    Camera.getNearClippingPlane, Camera.setNearClippingPlane,
    DagNode.fullPathName, DagNode.isInstancedAttribute, DagNode.partialPathName,
    DagNode.setInstanceable, DependNode.allocateFlag, DependNode.attributeClass,
    DependNode.deallocateAllFlags, DependNode.deallocateFlag,
    DependNode.dgCallbacks, DependNode.dgTimer, DependNode.dgTimerOff,
    DependNode.dgTimerOn, DependNode.dgTimerQueryState, DependNode.dgTimerReset,
    DependNode.getAliasAttr, DependNode.hasAttribute, DependNode.isNewAttribute,
    DependNode.removeAttribute, DependNode.setFlag, DependNode.typeName,
    ObjectSet.addMember, ObjectSet.isMember, ObjectSet.removeMember

- nodetypes: Transform.rotateByQuaternion added, and accepts either a
  Quaternion/MQuaternion or four separate floats
- nodetypes: DependNode.deleteAttr now accepts Attribute objects (first
  verifying that it is an attribute on the same node as self)
- nodetypes: Added a DependNode.typeName classmethod - similar to
  DependNode.type / general.nodeType, but unlike those, it does not require an
  actual instance of a node, or call any mel / api functions - instead, it just
  returns the type that the given class wraps.  When called from an instance,
  should always give the same result as DependNode.type, since pymel always
  ensures that the most specific node class is used to create any PyNode
- util.enum: EnumValue objects now have a __hash__, and so can be stored in dicts / sets
- versions: add v2018_1, v2018_1, v2018_2, v2019_3, v2019
- general: added getDefault method to Attribute class
- language: allow optionvars to save long types
- all: standardize on numpy-style docstrings with PEP484 type annotations.
- general: allow adding of 2 (1-dimensional) components - ie, you can now add
  two MeshVertex objects, containing verts for the same mesh, together to get
  a new MeshVertex object representing their union
- nodetypes: add Transform.getRotateOrientation / setRotateOrientation
  these are distinct from the existing getRotateAxis / setRotateAxis
  (from MEL), because they operate on quaternions, which are what the
  transform "actually" stores under the hood - and so it seems potentially
  useful to give direct access.
- general: expand types of objects that AttributeSpec constructor accepts -
  str, Attribute object, AttributeSpec object, MPlug, MObject
- nodetypes: make DependNode.deleteAttr work with Attribute
- datatypes: expand set of things you can construct a Quaternion with: lists
  of floats, ints, another Quaternion, an MQuaternion, axis-angle, rotate
  vector-to-vector
- nodetypes: added an undoable Camera.setNearFarClippingPlanes
- system: UndoChunk can take an optional chunk "name" to show up in undo list

----------------------------------
Bug Fixes
----------------------------------
- uitypes.OptionMenu.getItemArray() now fixed, and returns PyUI objects
- nodetypes: fixed issue with DependNode.attrSpec incorrectly caching dynamic
  attrs
- datatypes: fix getPlugValue for Angle and Time plugs (would error previously)
- core: Added defensive code to prevent callback id leaks in some scenarios
- nodetypes: THblendShape was incorrectly mapped to kPluginSkinCluster
- nodetypes: fix DagNode.exists() (was raising error in some situations)
- general: fix indexing components with an iterable - ie, myMesh.f[(1,2,5)]
- nodetypes: fix for ikHandle not returning PyNodes (issue #410)
- general: fix for parenting with grouping of args; fixes issue #406
- virtual nodes: fix for plugins.PyNodeMethod
- nodetypes: fix for creating PyNode wraps for node types added outside of
  plugin init - ie, some mtoa nodes get created outside of the plugin init
- core: fix for plugin unloaded callback when using plugin name with extension -
  ie, pm.unloadPlugin("myPlugin.py")
- nodetypes: make TransferAttribute use MFnWeightGeometryFilter
- nodetypes: AnimCurve.addKey / evaluate / AnimCurve.findClosest now work for
  all curve types, not just time-to-float types
- nodetypes: fix for creation of Locator() - thanks bob-white!


==================================
Version 1.0.10
==================================

----------------------------------
Changes
----------------------------------
- default testing engine changes to pytest (from nose)
- remove ply as requirement, as we have pymel.util.external.ply
- utilitytypes: make LazyLoadModule a class, not func

----------------------------------
Additions
----------------------------------
- added support for 2018
- system: add FileReference.nodes(recursive=True) flag
- Adding pm.isModified function (replacement for cmds.file(q=1, modified=1)
  (thanks, bob-white!)
- Added file reference remove flags (thanks, wesbondie!)
- added mergeNamespaceWithParent and mergeNamespaceWithRoot to
  FileReference.remove to match docs (thanks mjmvisser!)
- add kwargs support to getClassfication - issue #343 (thanks kartikg3!)
- plugins: add FileTranslator plugin helper base class to pymel.api.plugins
- util.enum: add Enum.itervalues
- maintenance: make stub generation more general-purpose; add cli
- stubs: improvements to PEP484 pyi stub file generation
- tests support pytest now

----------------------------------
Bug Fixes
----------------------------------
- fix for Attribute equality for compound multi attrs
- cmds.file(new=1, type='mayaAscii') will crash maya - pm.newFile() will now
  automatically ignore any type/typ flags to avoid this - issue #346
  (thanks bob-white!)
- fix for mesh.numTriangles() raising a TypeErorr - issue #388
  (thanks kartikg3!)
- fix for uitypes.Menu.getItemArray exceptions (thanks bob-white!)
- plogging: fix for setting of root logging level (thanks sdalgo!)
- fix to deal with nodes showing up multiple times in inheritance tree from
  cmds.nodeType (ie, aiSkyDomeLight)
- ipymel now working again with modern versions of IPython
- fix for PyNode becoming invalid if instance is reparented in some situations
- deprecated api-wrapped functions weren't returning values
- dynamically create PyNodes from nodetypes - fixes issue with some maya node
  types that can't get detected on plugin load
- fix for hasParent/hasChild/isParentOf/isChildOf with underworld nodes
- pm.parent will set PyNodes fed in to use the correct instance / parent
- better fix for mayapy segfaults (run maya.standalone.uninitialize)
- factories: some functions using MFloatPoint weren't doing unit conversion
- some node types that are dag nodes don't work with MFnDagNode - however,
  .nodeName() should still work (as that doesn't need MFnDagNode)
- nodetypes: attempt to deal with crash with instances;
  get it when you add an instance of an object, and then access the old object;
  this doesn't completely solve the issue, but it may be impossible to avoid
  completely without a patch for the underlying problem from autodesk
- fix for pm.listNamespaces() returning duplicates weed out - issue #380
  (thanks mjmvisser!)
- datatypes: fix to deal with new swig-generated setattr in 2018
- factories: fix for fromInternalUnits with ref-casts
- factories: fix for isMayaType, for weird types
  (ie, TadskAssetInstanceNode_TdependNode, which is a parent of adskMaterial)
- factories: prefer non-deprecated api methods
- startup: fix some hangs on exit in maya 2016.51
- pymel.conf: fix name of fix_linux_mayapy_segfault
- stubs: fix for detection of os.environ


==================================
Version 1.0.9
==================================

----------------------------------
Changes
----------------------------------
- turn fixMayapy2011SegFault on by default, control with config

----------------------------------
Additions
----------------------------------
- added support for 2017
- Added support for PySide2

----------------------------------
Bug Fixes
----------------------------------
- arrays: fix error messages for non-existent axes (issue #369)
- general: remove hard-coded getSetAttrCmds; also fix tests (default is short attr names)
- general: Fix for showNamespaces breaking ls
- general: Mesh*.connected* raises error if list is empty (issue #367)
- general: Fix a bug where parenting to a non-existent node did not raise an error
- language: restore gFilterUIDefaultAttributeFilterList, in prep for autodesk fix
- ui: textField and text lose their type (issue #349)


==================================
Version 1.0.8
==================================

----------------------------------
Changes
----------------------------------
- ui: update promptForFolder to use fileDialog2
- core: don't abort loading pymel if error adding a plugin command
- system: ensure sceneName always returns Path('') for untitled scenes (this was the described behavior, but it would return e.g. /path/to/untitled.mb under some circumstances)
- system: changed FileInfo to inherit from collections.MutableMapping. This gives it a complete dictionary interface, like OptionVarDict.
- language: added support for namespace-protected MEL procedure calls. (issue #359).
- update ipymel to work with newer ipython versions

----------------------------------
Additions
----------------------------------
- added support for 2016.5
- nodetypes: added ObjectSet.forceElement
- pmcmds: give wrapped commands unique co_name, for better cProfile info
- general: added ability to pass type to addAttr. The type is automatically determined to be a dataType or an attributeType

----------------------------------
Bugfixes
----------------------------------
- general: fix for getMin/Max with multi attr elements
- general: fix listRelatives to make combo of allDescendents, shapes, noIntermediate work
- general: fix for parent(removeObject=True)
- general: fix particle attribute in ParticleComponent.attr(). (issue #350)
- general: fix spaceLocator not returning unique names. (issue #320)
- startup: fix for installation of exit handler in fixMayapy2011SegFault
- uitypes: fix for TextScrollList.selectIndexedItems / selectAll. (issue 110)
- uitypes: fix docs for MainProgressBar
- all: don't try to UI modules when Maya runs in batch mode
- datatypes: fix for Matrix/TransformationMatrix scale/rotate properties
- nodetypes: fix Shape.getTransform() to return shape node's transform. (issue #311)
- utils: fix runOverriddenModule() to use os.stat compare in case of Windows OS, where samefile would error. (issue #358).


==================================
Version 1.0.7
==================================

----------------------------------
Changes
----------------------------------

- general: MultiAttrs now support __delitem__
- uitype: use PySide in toQtObject methods if no PyQt
- language: added mel.globals alias for melGlobals
- core: improve API undo callbacks
- system: saveFile resets name if filename is messed up
- system: make loadReference give more informative error if ref not loaded
- system: optimized FileReference.__init__
- system: switched file cmd used by iterReferences for more stable referenceQuery
- docs: improved the look of the docs
- util.arrays: Array objects now explicitly unhashable, added totuple
- utils.path: allow the pattern argument for various methods to take a compiled regular expression pattern.

----------------------------------
Additions
----------------------------------

- added support for 2016
- language: added Env.playbackTimes convenience property for getting/setting all timeline values at once
- allapi: added example usage to SafeApiPtr
- general: added Attribute.iterDescendants
- system: added mode and caseSensitive args to Translator.fromExtension
- nodetypes: added topLevel and descendants kwargs to DependNode.listAttr
- nodetypes: added Camera.isDisplayGateMask method
- nodetypes: added closestPolygon keyword arg to getUVAtPoint
- uitypes: added toPySide* functions for casting maya UI strings to PySide objects
- pymel.conf: added option to source initialPlugins.mel
- pymel.conf: added option to prefer PyQt4 or PySide
- util.arguments: added support for sets, useChangedKeys to compareCascadingDicts
- util.common: added inMaya() func
- stubs: make stub Mel.__getattr__ accept anything
- stubs: added PySide stubs

----------------------------------
Bugfixes
----------------------------------

- system: fixed bug with referenceQuery which occured when editStrings and liveEdits flags are True
- system: fixed bug with ReferenceEdit.remove() where self.rawEditData was referred to as a method instead of a property.
- ipymel: pressing ctrl-c no longer quits maya
- logging: fixed bug preventing logging menus from displaying


==================================
Version 1.0.6
==================================

----------------------------------
Non-Backward Compatible Changes
----------------------------------

- joint.limitSwitchX/Y/Z: now return [bool, bool] when queried, just like the mel command, to indicate whether the limit is on for the min/max
- joint.radius: now returns the float radius, instead of [radius]

----------------------------------
Changes
----------------------------------

- general: addAttr/setEnums now accept strings, lists, or dicts for setting enums
- other: cast NameParser arguments to unicode
- factories: issue deprecation warning for deprecated functions only when they're actually used

----------------------------------
Additions
----------------------------------

- added support for 2015
- added (functional) namespace method to Attribute, Component
- general: added mute accessors to Attributes
- system: provide ReferenceEdit.rawEditData property for getting faster unparsed access to reference edits
- nodetypes: added stripUnderworld flag to DependNode.nodeName(), and default it to true.  This removes the underworld prefix (the node prior to ->) from nodeName().
- ipymel: update for ipython 0.11
- util.arguments: compareCascadingDicts can show which keys have been added (as opposed to just changed)
- system: added workspace.expandName

----------------------------------
Bugfixes
----------------------------------

- general: for the keyframe command, the upper / lower limits substituted in for the "index" flag, when no upper/lower limits were given, are now correct; formerly, the behavior of index=":" would vary depending on where (in time) the first and last keyframes were
- general: timerange flags (ie, keyframe(time=...), findKeyframe(time=...), etc) now provide correct results when no upper/lower limits given; formerly, the time=":" would vary depending on if / which objects were selected
- animation: Joint.angleX/Y/Z and Joint.stiffnessX/Y/Z now work
- nodetypes: Container.getParentContainer, Container.getRootTransform, and Character.getClipScheduler now all return None instead of raising a runtime error if no object was found
- system: FileReference.fullNamespace and iterReferences/listReferences with namespaces=1 now handle situations where reference node itself is in a non-root namespace correctly
- general: when instantiating PyNode from an MPlug, to get the PyNode for the node, create from the underlying mobject, not the name (which may not be unique)
- animation: fix for Joint.getAngleX/Y/Z, .getStiffnessX/Y/Z; joint.radius no longer returns list
- mel2py: numerous fixes / tweaks
- system: handle situations where reference node itself is in a non-root namespace
- system: FileReference.nodes fix when reference contains no nodes
- general: duplicate - special-case workaround for duplicating a single underworld node with no children
- general: fix for duplicate + non-unique names
- general: duplicate - workaround for bug introduced in 2014
- nodetypes: fix for getAllParents with underworld nodes
- Upgrade path.py to version 5.0 from github (https://github.com/jaraco/path.py).  This fixes an issue with Maya2014, python 2.7.3, and Windows where path().isdir() raised an error.
- general: cmds.group returns unique name in maya > 2014
- fix for virtual classes
- versions: parsing for 'Preview Release' format - from Dean Edmonds

==================================
Version 1.0.5
==================================

----------------------------------
Non-Backward Compatible Changes
----------------------------------

- DagNode.isVisible:  has a new flag, checkOverride, which is on by default, and considers visibility override settings
- referenceQuery/FileReference.getReferenceEdits: if only one of successfulEdits/failedEdits is given, and it is false, we now assume that the desire is to return the other type (and set that flag to true); formerly, this would result in NO edits being returned
- parent no longer raises an error if setting an object's parent to it's current parent; this makes it behave similarly to the mel command, and to DagNode.setParent
- renameFile now automatically sets the 'type' if none is supplied (helps avoid renaming a file to 'foo.ma', then saving it as 'mayaBinary')
- general: 1D components have index() method: can no longer use string.index()
- uitypes: make PyUI.parent return None instead of PyUI('')

----------------------------------
Changes
----------------------------------

- for maya versions >= 2012, creation of "ghost" plugin nodes no longer needed
- general: change to Component to speed up len(PyNode('pCube1Shape').vtx)
- general: parent and DagNode.setParent now share common codebase
- general: when find unknown component type, default to just printing a warning and returning generic Component
- general: demoted raiseLog warning about unknown component type to DEBUG
- general: added uniqueObjExists function
- general: speedup for string representation of complete MeshVertexFace
- general: made listRelatives/listHistory/listConnections have same behavior for None and empty list
- system: clarified doc not about removeReferenceEdits not erroring
- system: FileReference.replaceWith - enable kwargs
- system: renameFile automatically sets type
- system: changed referenceQuery so when only one of successful/failed passed, other flag is opposite value
- language: make catch take args/kwargs
- nodetypes: attrDefaults - use MNodeClass in versions >= 2012, _GhostObjMaker otherwise
- nodetypes: Transform.setRotation now takes args as EulerRotation, Quaternion, or iterable of 3 or 4 elements
- nodetypes: isVisible checks overrideVisibility
- stubs: catch more dict-like-objects; special case exclude for maya.precomp.precompmodule
- stubs: create dummy data objects when safe; better handling of builtins
- stubs: use static code analysis to decide whether to include a child module in a parent module's namespace
- stubs: better representations for builtin data types
- stubs: get all names in module, better 'import *' detection
- plogging: added raiseLog func/method
- plogging: small tweaks to way default ERRORLEVEL is set, and raiseLog is added onto loggers
- ipymel: make sure stuff imported into global namespace in userSetup.py is available in IPython

----------------------------------
Additions
----------------------------------

- nodetypes: added stripNamespace option to DependNode.name
- general: disconnectAttr - support for disconnecting only certain directions
- general: MeshFace - added numVertices as alias for polygonVertexCount
- general: added DiscreteComponent.totalSize method
- general: added ParticleComponent class
- other: added DependNodeName.nodeName (for compatibility with DagNodeName)
- nodetypes: added DagNode.listComp
- datatypes: added equivalentSpace
- utilitytypes: proxyClass - added module kwarg to control __module__
- system: added FileReference.parent()
- system: listReferences - added loaded/unloaded kwargs
- system: added UndoChunk context manager
- system: Namespace.remove/.clean - added reparentOtherChildren kwarg
- system: added support for regexps to path.listdir/.files/.dirs
- system: added successful/failedEdits flags to FileReference.removeReferenceEdits
- windows: confirmBox - added returnButton kwarg to force return of button label
- plugins: added an example for creating plugin nodes
- util.enum: added Enum.__eq__/__ne__
- py2mel: added include/excludeFlagArgs
- system: added proper hash function for FileReference

----------------------------------
Bugfixes
----------------------------------

- general: fix for potential crashes due to using cached/invalid MFn
- general: fix pm.PyNode('pCube1.vtx[*]')[2] to work like like pm.PyNode('pCube1').vtx[2]
- general: fix for HashableSlice comparison (fixes bug with component indexing)
- general: Component - fixes for complete-component shortcut don't use with empty meshes don't use for subd components (including SubdUV) use ffd1LatticeShape.pt[*], not .pt[*][*][*]
- general: SubdEdge - hack to avoid a maya bug which causes crash
- language: MelGlobal.initVar now initializes in mel
- language: remove annoying callback error spam; instead make info available in a log from Callback.printRecentError()
- uitypes: fix for 2012 SP2 issue with objectTypeUI not working for windows with menu bars
- nodetypes: Transform.setRotation - fix for setting with EulerRotation object and non-standard rotation order or unit
- nodetypes: fix for ObjectSet.__len__
- nodetypes: AnimLayer.getAttribute - query dagSetMembers.inputs() to get full/unique path
- nodetypes: fix typo in name of NurbsCurve/Surface.controlVerts (not conrolVerts)
- core: _pluginLoaded - added fix for addPluginPyNodes triggered on reference load (fix for 2012+ only)
- core: fix erroneous 'could not find callback id' warnings
- utilitytypes: universalmethod now has doc pulled from original func
- util.conditions: bugfix for __ror__, added __str__
- allapi: toApiObject - low-level fix for Nucleus attributes
- startup: don't use fixMayapy2011SegFault in >= 2013, seg fault was addressed by Autodesk
- stubs: fixes for objects with multiple aliases in a module
- py2mel: bugfixes, bugfix for excludeFlagArgs

==================================
Version 1.0.4
==================================

----------------------------------
Changes
----------------------------------

- core.uitypes: improved AETemplates to work when created from within a scripted plugin
- tools.mel2py: now output exact same filename as input on Windows
- core.nodetypes: Transform.getRotation  - can get as euler or quaternion
- extras: improved reliability of stub files (for pydev, wing, etc)
- core: doing select([], replace=True) should clear selection
- api.allapi: replace toMObjectName with MObjectName
- core: namespace - root option is now False (for backward compatibility)
- core: MeshVertex.setColors - set colors for all verts in MeshVertex
- core: re-implement noIntermediate flag to listRelatives
- plogging: PYMEL_LOGLEVEL env var now sets minimum level for all pymel loggers
- core: use new 2012 pluginInfo flags for getting more command types
- core.windows: PopupError can now raise another exception type
- examples: update customClasses.py example

----------------------------------
Additions
----------------------------------

- util.path: added boolean normcase keyword arg to path.canonicalpath()
- api.plugins: added in classes for all MPxNode classes and methods for querying class / MPx to MPx enum mappings
- api.plugins: added new overridable methods which generate node callbacks:  timeChagned, forcedUpdate, nodeAdded, nodeRemoved, preConnectionMade
- versions: added maya2012 hotfix 1,2,3,4
- core: Attribute.setDirty / evaluate
- core: DependNode.rename() now supports pyMel unique flag preserveNamespace
- core: added check to ensure name passed to DependNode.rename() is shortname
- core: implemented DependNode.rename() flags: i.e. ignoreShape can now be used
- core.uitypes: added Layout.findChild() which takes the shortname of a child as a string and returns the PyUI object

----------------------------------
Bugfixes
----------------------------------

- mayautils: fix so recurseMayaScriptPath, when given explicit roots, doesn't wipe out old paths
- core: fixed bug where __pymelUndoNode was created in non root namespace
- tools.pymelScrollFieldReporter: use mel2py.melparse (issue 247)
- core: fixed FileReference.importContents(removeNamespace=True)
- core: _pluginLoaded callback now correctly triggered by importing
- core:  fix promptForPath doesn't work for mode 1/100 due to testing for the existance of the path.
- core.nodetypes: fix for DependNode.rename(preserveNamespace=True) when node in root namespace
- core.nodetypes: fixed bug with RenderLayer.added/removeAdjustments
- core.nodetypes: fix for DagNode.getAllParents (and test)
- core.nodetypes: fix for DependNode.hasAttr(checkShape=False)
- core.nodetypes: fix for AnimCurve.addKeys (issue 234)
- internal.startup: fix for error message when fail to import maya.cmds.about
- core: fixed addAttr(q=1, dataType=1) so it does not error if non-dynamic attr
- core: pythonToMelCmd - fixed bug when flagInfo['args'] was not a class
- core: pythonToMelCmd - fix for flags where numArgs > 1
- maya.utils: formatGuiException - fix for, ie, IOError / OSError
- updated 2012 caches to fix issue 243

==================================
Version 1.0.3
==================================

----------------------------------
Changes
----------------------------------

- UI classes that have 'with' statement support now set parent back to previous
  'with' object if there are nested with statements; if not in a nested with
  statement, resets parent back to UI element's parent (or more precisely, the
  first element that is not a rowGroupLayout element)
- ``with OptionMenuGrp()`` will set parent menu properly
- 'Unit' support for Quaternion objects is now removed (as it doesn't make
  any sense)
- can now pass in PyNode class objects to functions / methods that expect a
  mel node class name - ie:

     listRelatives(allDescendents=True, type=nt.Joint)

  is equivalent to:

     listRelatives(allDescendents=True, type='joint')
- other: NameParser(dagObj) now always gives a DagNodeName even if shortName has no |


----------------------------------
Non-Backward Compatible Changes
----------------------------------

- PyNode('*') - or any other non-unique name - now returns an error
  use ls('*') if you wish to return a list of possible nodes
- By default, the root pymel logger outputs to sys.__stdout__ now, instead of
  sys.stderr; can be overriden to another stream in sys (ie, stdout, stderr,
  __stderr__, __stdout__) by setting the MAYA_SHELL_LOGGER_STREAM environment
  variable
- skinCluster, tangentConstraint, poleVectorConstraint, and
  pointOnPolyConstraint commands now return a PyNode when creating, instead of a
  list with one item
- skinCluster command / node's methods / flags for querying deformerTools,
  influence, weightedInfluence now return PyNodes, not strings
- Attribute.elements now returns an empty list instead of None
- general: Attribute.affects/affected return empty list when affects returns None
- setParent returns PyUI / None; menu(itemArray) returns [] for None
- general: make Attribute.elements() return empty list for None
- shape attribute lookup on all child shapes (like mel does)

----------------------------------
Additions
----------------------------------

- Shape.setParent automatically adds --shape flag
- nodetypes: added isVisible
- added MGlobal.display* methods to pymel.core.system namespace
- other: added NameParser.stripGivenNamespace()
- language: OptionVarList has more helpful error message when __setitem__ attempted
- nodetypes: getSiblings can now take kwargs
- Added MainProgressBar context manager
- Added isUsedAsColor method to Attribute class
- Added wrapper for listSets function
- Added method listSets to PyNode class
- Added a folderButtonGrp
- system: added Namespace.move
- system: added Namespace.listNodes
- mel2py: python mel command now translated to pymel.python (ie, maya.cmds.python)
- general: added Attribute.indexMatters
- language: added animStart/EndTime to Env
- system: added in a 'breadth'-first recursive search mode to iterReferences
- general: added ability to set enum Attributes with string values (issue 35)
- plogging: set logging level with PYMEL_LOGLEVEL env var
- Added isRenderable() method to object set.
- deprecate PyNode.__getitem__
- mayautils: executeDeferred now takes args, like maya.utils.executeDeferred

----------------------------------
Bugfixes
----------------------------------

- py2mel failing with functions that take \*args/\*\*kwargs
- eliminated / fixed various 'warning' messages on pymel startup
- MayaNodeError / MayaAttributeError not being raised when a node / attribute not found
- some maya cmds were not handling 'stubFunc' correctly
- renderLayer.listAdjustments() was not functioning
- MainProgressBar fixed
- language: OptionVarList __init__ no longer raises deprecation warning
- listSets() throws away non-existant 'defaultCreaseDataSet' that maya.cmds.listSets() returns
- fix for dealing with maya bug where constraint angle offsets always returned in radians (but set in degrees)
- fixes for incorrect formatting of error strings in some cases
- fixes for unloading of commands/nodetypes when plugins unloaded (and pymel.all was imported first)
- miscellaneous documentation fixes
- fix for mayautils.executeDeferred when invoked with args
- fix for Attribute.getAllParents()
- fix for aliased multi/compound attributes
- fix for Attribute.isSettable with multi/compound attributes
- fix for Attribute.exists with multi/compound attributes
- fix for Attribute.type with multi/compound attributes dynamic attributes
- fix for published container node attributes / aliases
- fixes for plugin callback failing when plugin has uncreate-able nodes
- fixes for multiple iterators of a mutli-attribute not being independent
- fix for MeshVertex.setColor
- fix for MeshVertex.isConnectedTo
- fix for MeshVertex.getColor
- fix for MeshEdge.isConnectedTo
- fix for MeshFace.isConnectedTo
- fix for plogging handling case where various env. variables exist, but are empty
- Fix for Layout.children() Layout.children() now returns empty list if layout has no kids intead of raising error.
- listConnections: fix so rotatePivot always Attribute (not component)
- uitypes: bugfixes to AETemplates.  corrected UITemplate to represent an existing uiTemplate if instantiated with the name of an existing template
- nodetypes: fixed a bug where Transform.setScalePivot was internally using MFnTransform.setScalePivotTranslation
- fixed a bug in pythonToMel where python booleans were not converted to integer. this caused the Mel class to not work properly with booleans.
- core.general: fix a bug with sets command where noWarnings was interpreted as a set flag, instead of a boolean flag
- Namespace: fix for getParent()
- general: various attr name fixes (stripping of [-1] indices, etc)
- nameparse: enable parsing of [-1] indices (for attributes)
- nodetypes: enable parsing of [-1] indices (for attributes)
- nodetypes: setParent to current parent no longer errors
- util.enum: fix for repr of EnumDict
- fixes for referenceQuery
- attr.exists() should return False if the node no longer exists
- datatypes: fixed bug to allow Point * FloatMatrix
- general: bugfix for Attribute.attrName
- utilitytypes: EquivalencePairs.get now correctly retrieves value=>key
- nodetypes: fixed setParent(world=1) bug
- uitypes: Fix issues with the popup and with support.
- pm.mel.command translation would fail with no-arg bool flags (like -q, -e)
- language: mel command translation makes no assumptions for unknown commands; None is translated to empty string, not 'None'
- bugfix for uiTemplate(exists=1)
- general: Attribute.elements() now correctly works with array and element plugs
- fix get/set rotation by using eulerRotation
- startup: changes to fix issues with maya -prompt and plugins loading pymel
- fix for TransformationMatrix.get/setRotation, removed Quaternion units
- datatypes: fixes for EulerRotation
- fix for ui heights for pymelControlPanel
- uitypes: bugfix for with statement parent setting on exit
- mesh: fixes to allow creating component objects for empty meshes (ie, createNode('mesh').vtx)
- mesh: made more num* functions work with empty meshes
- core.general: fix for move with no object
- datatypes: fix for EulerRotation comparison/len
- fix for menu('someOptionMenu')
- FileReference: initialize correctly from a path
- windows: bugfix - informBox wasn't using 'ok' kwarg
- plogging: bugfix for 182 - crash due to creating loggers as iterating over dict
- arrays: fix for dot/outer product error messages (issue 158)
- fix for 'no useName' and MfknSkinCluster.setBlendWeights warnings on startup
- Fixed language import in MainProgressBar
- fix for Issue 216: renderLayer.listAdjustments()
- docfix for issue 192
- fix for constraint angle offset query always being in radians
- nodetypes: fix for multi/compound alias attrs
- nodetypes: fixes for published container node attributes / aliases
- general: made attribute iterator independent
- general: fix for isSettable with multi/compound attributes
- general: fix so getAllParents doesn't return orig object
- general: fix for Attribute.exists with multi/compound attrs
- Attribute.type() now works with multi/compound, dynamic attrs
- fixes for mesh components

==================================
Version 1.0.2
==================================

----------------------------------
Changes
----------------------------------

- rolled back ``listConnections()`` change from 1.0.1

commands wrapped to return PyNodes
----------------------------------
- ``container()``

----------------------------------
Additions
----------------------------------

- added functions for converting strings to PyQt objects: ``toQtObject()``, ``toQtLayout()``, ``toQtControl()``, ``toQtMenuItem()``, ``toQtWindow()``
- added method for converting PyMEL UI objects to PyQt objects: ``UI.asQtObject()``

----------------------------------
Bugfixes
----------------------------------

- fixed a bug where ``nt.Conditions()`` created a script condition


==================================
Version 1.0.1
==================================

----------------------------------
Changes
----------------------------------

- ``listConnections``: when destination is shape, always returns shape (not transform)
- ``select([])`` only clears selection if mode is replace
- deprecated ``Attribute.firstParent()``

----------------------------------
Additions
----------------------------------

- ``mel2py``: now does packages/subpackages for recursed mel subdirectories
- added various dict-like methods to OptionVarDict
- added new EnumDict support which ``Attribute.getEnum`` returns
- added support to ``getAttr()`` / ``Attribute.get()`` for getting message attributes, which are returned as DependNodes
- added ``core.system.saveFile()``
- added ``pymel.versions.is64bit()``
- added new directory helpers to mayautils: ``getMayaAppDir()``, ``getUserPrefsDir()``, and ``getUserScriptsDir()``
- added ``DependNode.longName()``, ``DependNode.shortName()``, and ``DependNode.nodeName()`` for easy looping through mixed lists of DependNodes and DagNodes
- added ``FileInfo.__delitem__()``
- added ``DependNode.deleteAttr()``

----------------------------------
Bugfixes
----------------------------------

- unloading plugins no longer raises an error
- python AE templates were not being found. fixed.
- fixed a bug in api wrap, where ``MScriptUtil`` was not allocating space
- fixed a bug with ``Transform.setMatrix()``
- ``pymel.versions.installName()`` is more reliable on 64-bit systems, which were sometimes detecting the installName incorrectly
- ``Attribute('mytransform.scalePivot')`` now returns an the scalePivot attribute
- ``getAttr()`` / ``Attribute.get()`` bugfix with multi-attr
- ``nodetypes``: fixed bug 172 where nested selection sets were raising an error when getting members
- ``getPanel`` now always return panels
- ``uitypes``: all panel classes now properly inherit from Panel
- fixed some keywords that had been mistakenly refactored
- ``core.general``: fixed a bug where dependNodes were not returned when duplicated


==================================
Version 1.0.0
==================================

----------------------------------
Non-Backward Compatible Changes
----------------------------------

- pymel no longer has 'everything' in namespace - use ``pymel.all`` for this
- ``pymel.core.nodetypes`` now moved to it's own namespace
- ``pymel.mayahook.Version`` functionality moved to ``pymel.versions`` module. to compare versions, instead of Version class, use, for example, ``pymel.versions.current()`` >= ``pymel.versions.v2008``
- ``pymel.mayahook.mayautils.getMayaVersion()`` / ``getMayaVersion(extension=True)`` replaced with ``pymel.versions.installName()``
- ``pymel.mayahook.mayautils.getMayaVersion(extension=True)`` replaced with ``pymel.versions.shortName()``
- removed 0_7_compatibility_mode

- removed deprecated and inapplicable string methods from , base of all PyNodes:

- removed Smart Layout Creator in favor of 'with' statement support
- ``DagNode.getParent()`` no longer accepts keyword arguments
- Renamed ``UI`` base class to ``PyUI``
- ``sceneName()`` now returns a Path class for an empty string when the scene is untitled. this makes it conform more to ``cmds.file(q=1, sceneName=1)``
- replaced listNamespace with listNamespace_new from 0.9 line

removed deprecated methods
--------------------------
- ``Attribute``: ``__setattr__``, ``size``
- ``Camera``: ``getFov``, ``setFov``, ``getFilmAspect``
- ``Mesh``: ``vertexCount``, ``edgeCount``, ``faceCount``, ``uvcoordCount``, ``triangleCount``
- ``SelectSet``: ``issubset``, ``issuperset``, ``update``
- Mesh components: ``toEdges``, ``toFaces``, ``toVertices``
- ``ProxiUnicode``: ``__contains__,  __len__, __mod__, __rmod__, __mul__, __rmod__, __rmul__, expandtabs, translate, decode, encode, splitlines, capitalize, swapcase, title, isalnum, isalpha, isdigit, isspace, istitle, zfill``

----------------------------------
Features
----------------------------------

- added support for creation of class-based python Attribute Editor templates, using ``ui.AETemplate``
- added 'with statement' compatibility to UI Layout and Menu classes
- added the ability to generate completion files for IDEs like Wing, Eclipse, and Komodo

----------------------------------
Tools
----------------------------------

- ``ipymel``: added colorization to dag command
- ``py2mel``: now works with lambdas and methods.  new option to provide a list or dictionary of mel types.
- re-added missing scriptEditor files
- added upgradeScripts, a tool for converting 0.9 scripts to be 1.0 compatible

----------------------------------
Changes
----------------------------------

- moved functions for working with the shell into ``util.shell``
- split out ui classes from ``core.windows`` into ``core.uitypes`` for lazy loading
- for versions >= 2009, use open/close undo chunks instead of mel hack to ensure that an entire callback can be undone in one go
- improved ``lsUI()``
- moved component types out of nodetypes and into general
- ``__repr__`` for nodetypes, uitypes, and datatypes reflect their location so as not to cause confusion.  using short module names nt, ui, and dt.
- caches are now compressed for speed
- allow setting ``pymel.conf`` location via environment variable PYMEL_CONF
- ``DagNode.getBoundingBox()`` now allows you to specify space
- ensured that the 'name' flag for surface and curve operates on shape as well
- changes to allow ``myCube.vtx[1,3,5]``
- commands wrapped by pmcmds that raise a standard TypeError for a non-existent object will now raise a MayaObjectError
- simplified getParent code on Attribute and DagNode to improve function signatures.
- fixed a bug with ``ls(editable=1)``
- fixed a bug with ObjectSets containing DagNodes
- callbacks: extra debug information is printed in tracebacks

commands wrapped to return PyNodes
----------------------------------
- ``skinCluster(q=1, geometry=1)``
- ``addAttr(q=1, geometry=1)``
- ``addDynamic()``
- ``addPP()``
- ``constraint()``
- ``animLayer()``
- ``annnotate()``
- ``arclen()``
- ``art3dPaintCtx()``
- ``artAttrCtx()``
- ``modelEditor(q=1,camera=1)``
- ``dimensionShape()``

----------------------------------
Additions
----------------------------------

- added ``TwoWayDict``/``EquivalencePair`` to ``utilitytypes``
- added ``preorder()``, ``postorder()``, and``breadth()`` functions in ``util.arguments``, which have more intuitive arguments
- added new ``Layout`` class that all layouts inherit from
- added ``UITemplate`` class
- added usable ``__iter__`` to workspace dict / file dict objects
- added two tier setup scripts for maya (user/site) just like with python. This new ``siteSetup.py`` is intended for studio setup of maya and reserved ``userSetup.py`` for user level scripts.
- added a partial replacement maya package with a logger with a shell and gui handler qne changed plogging to use the new default maya logger
- added ``setAttr``/``getAttr`` support for all numeric datatypes, along with tests
- added ``Transform.getShapes()`` for returning a list of shapes
- added ``FileReference`` comparison operators
- added ``DependNode.longName(stripNamespace=False,level=0)``
- added ``SkinCluster.setWeights()``
- added ``AnimCurve.addKeys()``
- added regex flag to ls command
- added ``FileInfo.get()``
- added ``util.common.subpackages()`` function for walking package modules
- added ``util.conditions.Condition`` class for creating object-oriented condition testing
- ``pymel.conf``: added a fileLogger
- added ``Path.canonicalpath()`` and ``Path.samepath()``
- mel2py: added command-line flags, ability to recurse

added support for attribute aliases
-----------------------------------
- ``DependNode.attr()`` now casts aliases to Attributes properly (PyNode already does)
- added ``DependNode.listAliases()``
- added 'alias' keyword to ``DependNode.listAttr()``
- added ``Attribute.setAlias()``, ``Attribute.getAlias()``

----------------------------------
Bugfixes
----------------------------------

- fixed instantiation of PyNode from MPlug instance
- fixed a bug where Maya version was incorrectly detected when Maya was installed to a custom location
- fixed bug where wrap of function which took multiple refs all pointed to same ``MScriptUtil``
- fixed wrapping of unsigned ptr api types
- fixed negative comp indices
- ``mel2py``: bugfix with ``mel2pyStr()``


==================================
Version 0.9.2
==================================

----------------------------------
Changes and Additions
----------------------------------

- added support for 2010 and python 2.6
- added basic support for all component types
- added a 'removeNamespace' flag to ``FileReference.importContents()``
- added support for open-ended time ranges for command like keyframes (Issue 82)
- enhanced ``keyframe`` function: if both valueChange and timeChange are queried, the result will be a list of (time,value) pairs
- added ability to pass a list of types to ``ls`` 'type' argument, as you can with ``listRelatives``
- added checkLocalArray and checkOtherArray arguments to ``Attribute.isConnectedTo`` which will cause the function to also test mulit/array elements
- improved ``core.language.pythonToMel()`` reliability on lists
- improved custom virtual class workflow
- added functionality to ``pymel.tools.py2mel`` for dynamically creating MEL commands based on python functions/classes
- added a new module ``pymel.api.plugins`` for working with api plugins in a more reasonable and automated fashion
- updated eclipse integration documentation

easy_install improvements
-------------------------
- setup now copies over a readline library for 2010 OSX using ``readline.so`` from toxik which is more compatible
- changed ipymel to be part of the default install instead of an extra package
- fixed interpreter path of ipymel and other executable scripts on OSX
- setup now detects and fixes invalid python installations on Linux which previously caused ``distutils`` and thus ``setup.py`` to fail


----------------------------------
Bugfixes
----------------------------------

- ``importFile()``, ``createReference()``, ``loadReference()``, and ``openFile()`` now return PyNodes when passed returnNewNodes flag (Issue 85)
- fixed rare bug with Vista where ``platform.system`` was failing during startup (Issue 87)
- fixed a bug with plugin loading to intelligently handle when callback does not get a name
- fixed ``optionMenu`` and ``optionMenuGrp`` to return empty lists instead of None
- restored ``core.other.AttributeName.exists()`` method
- fixed a bug in 0.7_compatibility_mode
- fixed minor bug in ``listRelatives()``
- fixed a bug where curve command was returning a string instead of a PyNode (Issue 96)


==================================
Version 0.9.1
==================================

----------------------------------
Changes and Additions
----------------------------------

- new feature:  virtual subclasses.  allows the user to create their own subclasses which are returned by ``PyNode``
- added ``v2009sp1`` and ``v2009sp1a`` to ``Version``
- changed ``MelGlobals.__getitem__`` to raise a KeyError on missing global, instead of a typeError
- ``util.path`` now supports regular expression filtering in addition to globs.
- moved ``moduleDir()`` from ``util`` to ``mayahook`` since it is explicitly for pymel.
- ensured that all default plugins are loaded when creating the api cache so that we can avoid calculating those each time the plugins are loaded
- added a new `errors` flag to recurseMayaScriptPath for controlling how to handle directory walking errors: warn or ignore
- moved ``pwarnings`` to ensure that ``pymel.util`` is completely separated from maya
- adding new sphinx documentation. modifying source docstrings where necessary.
- setParent now allows ``None`` arg to specify world parent
- adopted a standard setuptools-compliant package layout, with pymel as a subdirectory of the top level
- forced line numbers on for ``Mel.eval``
- changed ipymel to use $MAYA_LOCATION to find mayapy instead of /usr/bin/env
- changed datatypes examples to demonstrate the necessity to include a namespace
- added ``groupname``, ``get_groupname``, and ``chgrp`` to ``Path`` class for dealing with unix groups as strings instead of as gid's
- added alias ``path.Path`` for ``path.path`` so as to follow PEP8
- added a new option to ``pymel.conf`` to allow disabling of mel initialization in standalone mode.
- added ability to set logger verbosity using PYMEL_LOGLEVEL environment variable.  great for quick testing.

----------------------------------
Bugfixes
----------------------------------

- fixed a bug in ``undoInfo()``
- fixed a bug that was breaking ``mel2py``
- fixed a bug with logging that was locking it to INFO level.  INFO is now the default, but it can be properly changed in ``pymel.conf``
- fixed input casting of ``datatypes.Time``
- bug fixes in error handling within path class
- fixed issue 65: ``DependencyNode.listAttr()`` broken
- made sure ``NameParse`` objects are stringified before fed to ``MFnDependencyNode.findPlug()``
- added a few more reserved types so as to avoid creating them, which can lead to crashes on some setups
- fixed issue 66 where nodes could be created twice when using PEP8 style class instantiation: ``pm.Locator``
- ``path.walk*`` methods now properly prune all directories below those that do not match the supplied patterns
- maya bug workaround: changed pluginLoaded callback to API-based for 2009 and later
- fixed bug in ``hasAttr()``
- removed bug in ``arrays.dot`` where incorrect duplicate definition was taking precedence
- fixed bug in ``PyNode.__ne__()`` when comparing DagNodes to DependNodes
- fixed Issue 72: cannot select lists of components
- fixed bug with startup on windows (backslashes not escaped)
- fix for ``Component('pCube1.vtx[3]')``
- fix for nurbsCurveCV('nurbsCircle1') failing
- pythonToMel and Mel now properly convert ``datatypes.Vectors`` to mel vectors ( <<0,0,0>> ). ``MelGlobals`` now returns ``datatypes.Vectors``
- fixed bug with ``duplicate(addShape=1)``
- fixed a bug where selectionSets can't be selected
- fixed a bug with ``sets()`` when it returns lists
- fixed issue 76, where non-unique joint names were returned by ``pymel.joint`` and thus were unsuccessfully cast to ``nodetypes.Joint``
- fixed issue 80, regading incorrect association of ``nodetypes.File`` with ``cmds.file.``
- fixed a bug in ``connectAttr()`` that was preventing connection errors from being raised when the force flag was used






