import sys, re
import pymel.util as _util
import pymel.internal.pmcmds as cmds
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as _versions
import maya.mel as _mm
_logger = _internal.getLogger(__name__)

def _resolveUIFunc(name):
    if isinstance(name, basestring):
        import windows
        try:
            return getattr(windows,name)
        except AttributeError:
            try:
                cls = getattr(dynModule,name)
                return cls.__melcmd__()
            except (KeyError, AttributeError):
                pass
    else:
        import inspect
        if inspect.isfunction(name):
            return name
        elif inspect.isclass(name) and issubclass(name, PyUI):
            name.__melcmd__()

    raise ValueError, "%r is not a known ui type" % name

if _versions.current() >= _versions.v2011:

    def toQtObject(mayaName):
        """
        Given the name of a Maya UI element of any type, return the corresponding QWidget or QAction.
        If the object does not exist, returns None

        When using this function you don't need to specify whether UI type is a control, layout,
        window, or menuItem, the first match -- in that order -- will be returned. If you have the full path to a UI object
        this should always be correct, however, if you only have the short name of the UI object,
        consider using one of the more specific variants: `toQtControl`, `toQtLayout`, `toQtWindow`, or `toQtMenuItem`.

        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findControl(mayaName)
        if ptr is None:
            ptr = mui.MQtUtil.findLayout(mayaName)
            if ptr is None:
                ptr = mui.MQtUtil.findMenuItem(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtcore.QObject)

    def toQtControl(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget.
        If the object does not exist, returns None

        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findControl(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)

    def toQtLayout(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget.
        If the object does not exist, returns None

        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findLayout(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)

    def toQtWindow(mayaName):
        """
        Given the name of a May UI control, return the corresponding QWidget.
        If the object does not exist, returns None

        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findWindow(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QWidget)

    def toQtMenuItem(mayaName):
        """
        Given the name of a May UI menuItem, return the corresponding QAction.
        If the object does not exist, returns None

        This only works for menu items. for Menus, use toQtControl or toQtObject

        .. note:: Requires PyQt
        """
        import maya.OpenMayaUI as mui
        import sip
        import PyQt4.QtCore as qtcore
        import PyQt4.QtGui as qtgui
        ptr = mui.MQtUtil.findMenuItem(mayaName)
        if ptr is not None:
            return sip.wrapinstance(long(ptr), qtgui.QAction)

# really, this should be in core.windows; but, due to that fact that this module
# is "higher" in the import hierarchy than core.windows, and we need this function
# here, we're just defining it here
@_factories.addMelDocs( 'objectTypeUI' )
def objectTypeUI(name, **kwargs):
    try:
        return cmds.objectTypeUI(name, **kwargs)
    except RuntimeError, topError:
        try:
            # some ui types (radioCollections) can only be identified with their shortname
            return cmds.objectTypeUI(name.split('|')[-1], **kwargs)
        except RuntimeError:
            # we cannot query the type of rowGroupLayout children: check common types for these
            uiType = None
            typesToCheck = 'checkBox floatField button floatSlider intSlider ' \
                    'floatField textField intField optionMenu radioButton'.split()
            if _versions.current() >= _versions.v2012_SP2:
                # 2012 SP2 introducted a bug where doing:
                # win = cmds.window(menuBar=True)
                # cmds.objectTypeUI(win)
                # would error...
                typesToCheck.append('window')
            for cmdName in typesToCheck:
                if getattr(cmds, cmdName)( name, ex=1, q=1):
                    uiType = cmdName
                    break
            if uiType:
                return uiType
            raise topError

class PyUI(unicode):
    def __new__(cls, name=None, create=False, **kwargs):
        """
        Provides the ability to create the PyUI Element when creating a class::

            import pymel.core as pm
            n = pm.Window("myWindow",create=True)
            n.__repr__()
            # Result: Window('myWindow')
        """

        if cls is PyUI:
            try:
                uiType = objectTypeUI(name)
            except RuntimeError:
                uiType = 'PyUI'
            uiType =  _uiTypesToCommands.get(uiType, uiType)

            try:
                newcls = getattr(dynModule, _util.capitalize(uiType) )
            except AttributeError:
                newcls = PyUI
                # objectTypeUI for panels seems to return weird results -
                # ie, TmodelPane ... check for them this way.
                # Other types should be detected correctly by objectTypeUI,
                # but this just provides a failsafe...
                for testType in 'panel scriptedPanel window control layout menu'.split():
                    if getattr(cmds, testType)( name, ex=1, q=1):
                        newcls = getattr(dynModule, _util.capitalize(testType),
                                         PyUI )
                        if newcls != PyUI:
                            break
        else:
            newcls = cls

        if not newcls is PyUI:
            if cls._isBeingCreated(name, create, kwargs):
                name = newcls.__melcmd__(name, **kwargs)
                _logger.debug("PyUI: created... %s" % name)
            else:
                # find the long name
                if '|' not in name and not issubclass(newcls,
                                                (Window,
                                                 Panel,
                                                 dynModule.ScriptedPanel,
                                                 dynModule.RadioCollection,
                                                 dynModule.ToolCollection)):
                    import windows
                    try:
                        if issubclass(newcls,Layout):
                            parent = windows.layout(name, q=1, p=1)
                        elif issubclass(newcls,OptionMenu):
                            parent = windows.optionMenu(name, q=1, p=1)
                        elif issubclass(newcls,Menu):
                            parent = windows.menu(name, q=1, p=1)
                        else:
                            parent = windows.control(name, q=1, p=1)
                        if parent:
                            name = parent + '|' + name

                    except RuntimeError:
                        # editors don't have a long name, so we keep the short name
                        if name not in cmds.lsUI( long=True,editors=True):
                            raise


        # correct for optionMenu
        if newcls == PopupMenu and cmds.optionMenu( name, ex=1 ):
            newcls = OptionMenu
        return unicode.__new__(newcls,name)

    @staticmethod
    def _isBeingCreated( name, create, kwargs):
        """
        create a new node when any of these conditions occur:
           name is None
           create is True
           parent flag is set
        """
        return not name or create or ( 'q' not in kwargs and kwargs.get('parent', kwargs.get('p', None)) )

    def __repr__(self):
        return u"ui.%s('%s')" % (self.__class__.__name__, self)
    def parent(self):
        buf = unicode(self).split('|')[:-1]
        if len(buf)==2 and buf[0] == buf[1] and _versions.current() < _versions.v2011:
            # pre-2011, windows with menus can have a strange name:
            # ex.  window1|window1|menu1
            buf = buf[:1]
        if not buf:
            return None
        return PyUI( '|'.join(buf) )
    getParent = parent

    def shortName(self):
        return unicode(self).split('|')[-1]
    def name(self):
        return unicode(self)
    def window(self):
        return Window( self.name().split('|')[0] )

    delete = _factories.functionFactory( 'deleteUI', rename='delete' )
    rename = _factories.functionFactory( 'renameUI', rename='rename' )
    type = objectTypeUI

    @classmethod
    def exists(cls, name):
        return cls.__melcmd__( name, exists=True )

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtControl

class Panel(PyUI):
    """pymel panel class"""
    __metaclass__ = _factories.MetaMayaUIWrapper
    # note that we're not actually customizing anything, but
    # we're declaring it here because other classes will have this
    # as their base class, so we need to make sure it exists first

_withParentStack = []
_withParentMenuStack = []

class Layout(PyUI):
    def __enter__(self):
        global _withParentStack
        _withParentStack.append(self)
        self.makeDefault()
        return self

    def __exit__(self, type, value, traceback):
        global _withParentStack
        _withParentStack.pop()
        if _withParentStack:
            parent = _withParentStack[-1]
        else:
            parent = self.pop()
            while parent and objectTypeUI(parent) == u'rowGroupLayout':
                parent = parent.pop()
        cmds.setParent(parent)

    def children(self):
        #return [ PyUI( self.name() + '|' + x) for x in self.__melcmd__(self, q=1, childArray=1) ]
        kids = cmds.layout(self, q=1, childArray=1)
        if kids:
            return [ PyUI( self.name() + '|' + x) for x in kids ]
        return []

    getChildren = children

    # TODO: add depth firt and breadth first options
    def walkChildren(self):
        """
        recursively yield all children of this layout
        """
        for child in self.children():
            yield child
            if hasattr(child, 'walkChildren'):
                for subChild in child.walkChildren():
                    yield subChild

    def findChild(self, shortName, recurse=False):
        if recurse:
            for child in self.walkChildren():
                if child.shortName() == shortName:
                    return child
        else:
            for child in self.children():
                if child.shortName() == shortName:
                    return child

    def addChild(self, uiType, name=None, **kwargs):
        if isinstance(uiType, basestring):
            uiType = getattr(dynModule, uiType)
        assert hasattr(uiType, '__call__'), 'argument uiType must be the name of a known ui type, a UI subclass, or a callable object'
        args = []
        if name:
            args.append(name)
        if kwargs:
            if 'parent' in kwargs or 'p' in kwargs:
                _logger.warn('parent flag is set by addChild automatically. passed value will be ignored' )
                kwargs.pop('parent', None)
                kwargs.pop('p', None)
        kwargs['parent'] = self
        res = uiType(*args, **kwargs)
        if not isinstance(res, PyUI):
            res = PyUI(res)
        return res

    def makeDefault(self):
        """
        set this layout as the default parent
        """
        cmds.setParent(self)

    def pop(self):
        """
        set the default parent to the parent of this layout
        """
        p = self.parent()
        cmds.setParent(p)
        return p

    def clear(self):
        children = self.getChildArray()
        if children:
            for child in self.getChildArray():
                cmds.deleteUI(child)

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtLayout

# customized ui classes
class Window(Layout):
    """pymel window class"""
    __metaclass__ = _factories.MetaMayaUIWrapper

#    if _versions.current() < _versions.v2011:
#        # don't set
#        def __enter__(self):
#            return self

    def __exit__(self, type, value, traceback):
        super(Window, self).__exit__(type, value, traceback)
        self.show()

    def show(self):
        cmds.showWindow(self)

    def delete(self):
        cmds.deleteUI(self, window=True)

    def layout(self):
        name = self.name()
        for layout in sorted(cmds.lsUI(long=True, controlLayouts=True)):
            # since we are sorted, shorter will be first, and the first layout we come across will be the base layout
            if layout.startswith(name):
                return PyUI(layout)

#            # create a child and then delete it to get the layout
#            res = self.addChild(cmds.columnLayout)
#            layout = res.parent()
#            res.delete()
#            return layout

    def children(self):
        res = self.layout()
        return [res] if res else []

    getChildren = children

    def window(self):
        return self

    def parent(self):
        return None
    getParent = parent

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtWindow

class FormLayout(Layout):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def __new__(cls, name=None, **kwargs):
        if kwargs:
            [kwargs.pop(k, None) for k in ['orientation', 'ratios', 'reversed', 'spacing']]

        self = Layout.__new__(cls, name, **kwargs)
        return self


    def __init__(self, name=None, orientation='vertical', spacing=2, reversed=False, ratios=None, **kwargs):
        """
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        Layout.__init__(self, **kwargs)
        self._spacing = spacing
        self._orientation = self.Orientation.getIndex(orientation)
        self._reversed = reversed
        self._ratios = ratios and list(ratios) or []

    def attachForm(self, *args):
        kwargs = {'edit':True}
        kwargs['attachForm'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachControl(self, *args):
        kwargs = {'edit':True}
        kwargs['attachControl'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachNone(self, *args):
        kwargs = {'edit':True}
        kwargs['attachNone'] = [args]
        cmds.formLayout(self,**kwargs)

    def attachPosition(self, *args):
        kwargs = {'edit':True}
        kwargs['attachPosition'] = [args]
        cmds.formLayout(self,**kwargs)

    HORIZONTAL = 0
    VERTICAL = 1
    Orientation = _util.enum.Enum( 'Orientation', ['horizontal', 'vertical'] )

    def flip(self):
        """Flip the orientation of the layout """
        self._orientation = 1-self._orientation
        self.redistribute(*self._ratios)

    def reverse(self):
        """Reverse the children order """
        self._reversed = not self._reversed
        self._ratios.reverse()
        self.redistribute(*self._ratios)

    def reset(self):
        self._ratios = []
        self._reversed = False
        self.redistribute()


    def redistribute(self,*ratios):
        """
        Redistribute the child controls based on the ratios.
        If not ratios are given (or not enough), 1 will be used
        """

        sides = [["top","bottom"],["left","right"]]

        children = self.getChildArray()
        if not children:
            return
        if self._reversed:
            children.reverse()

        ratios = list(ratios) or self._ratios or []
        ratios += [1]*(len(children)-len(ratios))
        self._ratios = ratios
        total = sum(ratios)

        for i, child in enumerate(children):
            for side in sides[self._orientation]:
                self.attachForm(child,side,self._spacing)

            if i==0:
                self.attachForm(child,
                    sides[1-self._orientation][0],
                    self._spacing)
            else:
                self.attachControl(child,
                    sides[1-self._orientation][0],
                    self._spacing,
                    children[i-1])

            if ratios[i]:
                self.attachPosition(children[i],
                    sides[1-self._orientation][1],
                    self._spacing,
                    float(sum(ratios[:i+1]))/float(total)*100)
            else:
                self.attachNone(children[i],
                    sides[1-self._orientation][1])

    def vDistribute(self,*ratios):
        self._orientation = int(self.Orientation.vertical)
        self.redistribute(*ratios)

    def hDistribute(self,*ratios):
        self._orientation = int(self.Orientation.horizontal)
        self.redistribute(*ratios)

class AutoLayout(FormLayout):
    """
    AutoLayout behaves exactly like `FormLayout`, but will call redistribute automatically
    at the end of a 'with' statement block
    """
    def __exit__(self, type, value, traceback):
        self.redistribute()
        super(AutoLayout, self).__exit__(type, value, traceback)

class RowLayout(Layout):
    __metaclass__ = _factories.MetaMayaUIWrapper

class TextScrollList(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    def extend( self, appendList ):
        """ append a list of strings"""

        for x in appendList:
            self.append(x)

    def selectIndexedItems( self, selectList ):
        """select a list of indices"""
        for x in selectList:
            self.selectIndexedItem(x)

    def removeIndexedItems( self, removeList ):
        """remove a list of indices"""
        for x in removeList:
            self.removeIndexedItem(x)

    def selectAll(self):
        """select all items"""
        numberOfItems = self.getNumberOfItems()
        self.selectIndexedItems(range(1,numberOfItems+1))

class Menu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def __enter__(self):
        global _withParentMenuStack
        _withParentMenuStack.append(self)
        self.makeDefault()
        return self

    def __exit__(self, type, value, traceback):
        global _withParentMenuStack
        _withParentMenuStack.pop()
        if _withParentMenuStack:
            cmds.setParent(_withParentMenuStack[-1], menu=True)
        else:
            parent = self
            while True:
                parent = parent.parent()
                # Maya 2012 Service Pack 2 (or SAP1, SP1) introduces a bug where
                # '' is returned, instead of None; problem being that doing
                # cmds.setParent(None, menu=True) is valid, but
                # cmds.setParent('', menu=True) is not
                if parent == '':
                    parent = None
                try:
                    cmds.setParent(parent, menu=True)
                except RuntimeError:
                    continue
                break

    def getItemArray(self):
        """ Modified to return pymel instances """
        children = cmds.menu(self,query=True,itemArray=True)
        if children:
            return [MenuItem(item) for item in cmds.menu(self,query=True,itemArray=True)]
        else:
            return []

    def makeDefault(self):
        """
        set this layout as the default parent
        """
        cmds.setParent(self, menu=True)

class PopupMenu(Menu):
    __metaclass__ = _factories.MetaMayaUIWrapper

class OptionMenu(PopupMenu):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def addMenuItems( self, items, title=None):
        """ Add the specified item list to the OptionMenu, with an optional 'title' item """
        if title:
            cmds.menuItem(l=title, en=0, parent=self)
        for item in items:
            cmds.menuItem(l=item, parent=self)

    def clear(self):
        """ Clear all menu items from this OptionMenu """
        for t in self.getItemListLong() or []:
            cmds.deleteUI(t)
    addItems = addMenuItems

class OptionMenuGrp(RowLayout):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def menu(self):
        for child in self.children():
            if isinstance(child, OptionMenu):
                return child

    # Want to set both the menu to the child |OptionMenu item, and the normal
    # parent to this...
    def __enter__(self):
        self.menu().__enter__()
        return super(OptionMenuGrp, self).__enter__()

    def __exit__(self, type, value, traceback):
        self.menu().__exit__(type, value, traceback)
        return super(OptionMenuGrp, self).__exit__(type, value, traceback)

class SubMenuItem(Menu):
    def getBoldFont(self):
        return cmds.menuItem(self,query=True,boldFont=True)

    def getItalicized(self):
        return cmds.menuItem(self,query=True,italicized=True)

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtMenuItem

class CommandMenuItem(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    __melui__ = 'menuItem'
    def __enter__(self):
        SubMenuItem(self).__enter__()
        return self

    def __exit__(self, type, value, traceback):
        return SubMenuItem(self).__exit__(type, value, traceback)

def MenuItem(name=None, create=False, **kwargs):
    if PyUI._isBeingCreated(name, create, kwargs):
        cls = CommandMenuItem
    else:
        try:
            uiType = objectTypeUI(name)
        except RuntimeError:
            cls = SubMenuItem
        else:
            if uiType == 'subMenuItem':
                cls = SubMenuItem
            else:
                cls = CommandMenuItem
    return cls(name, create, **kwargs)

class UITemplate(object):
    """
    from pymel.core import *

    # force deletes the template if it already exists
    template = ui.UITemplate( 'ExampleTemplate', force=True )

    template.define( button, width=100, height=40, align='left' )
    template.define( frameLayout, borderVisible=True, labelVisible=False )

    #    Create a window and apply the template.
    #
    with window():
        with template:
            with columnLayout( rowSpacing=5 ):
                with frameLayout():
                    with columnLayout():
                        button( label='One' )
                        button( label='Two' )
                        button( label='Three' )

                with frameLayout():
                    with columnLayout():
                        button( label='Red' )
                        button( label='Green' )
                        button( label='Blue' )
    """
    def __init__(self, name=None, force=False):
        if name and cmds.uiTemplate( name, exists=True ):
            if force:
                cmds.deleteUI( name, uiTemplate=True )
            else:
                self._name = name
                return
        args = [name] if name else []
        self._name = cmds.uiTemplate( *args )

    def __repr__(self):
        return '%s(%r)' % ( self.__class__.__name__, self._name)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, type, value, traceback):
        self.pop()

    def name(self):
        return self._name

    def push(self):
        cmds.setUITemplate(self._name, pushTemplate=True)

    def pop(self):
        cmds.setUITemplate( popTemplate=True)

    def define(self, uiType, **kwargs):
        """
        uiType can be:
            - a ui function or class
            - the name of a ui function or class
            - a list or tuple of the above
        """
        if isinstance(uiType, (list,tuple)):
            funcs = [ _resolveUIFunc(x) for x in uiType ]
        else:
            funcs = [_resolveUIFunc(uiType)]
        kwargs['defineTemplate'] = self._name
        for func in funcs:
            func(**kwargs)

    @staticmethod
    def exists(name):
        return cmds.uiTemplate( name, exists=True )

class AELoader(type):
    """
    Metaclass used by `AETemplate` class to create wrapping and loading mechanisms when an AETemplate instance is created
    """
    _loaded = []
    def __new__(cls, classname, bases, classdict):
        newcls = super(AELoader, cls).__new__(cls, classname, bases, classdict)
        try:
            nodeType = newcls.nodeType()
        except ValueError:
            _logger.debug("could not determine node type for " + classname)
        else:
            modname = classdict['__module__']
            if modname == '__builtin__':
                # since the module is __builtin__ our AE was probably included in the body of a scripted
                # plugin, which is called by maya in a strange way ( execfile? ).
                # give it a real home so we can load it later.
                mod = sys.modules['__builtin__']
                setattr( mod, classname, newcls )

            template = 'AE'+nodeType+'Template'
            cls.makeAEProc(modname, classname, template)
            if template not in cls._loaded:
                cls._loaded.append(template)
        return newcls

    @staticmethod
    def makeAEProc(modname, classname, procname):
        _logger.debug("making AE loader procedure: %s" % procname)
        contents = '''global proc %(procname)s( string $nodeName ){
        python("import %(__name__)s;%(__name__)s.AELoader.load('%(modname)s','%(classname)s','" + $nodeName + "')");}'''
        d = locals().copy()
        d['__name__'] = __name__
        import maya.mel as mm
        mm.eval( contents % d )

    @staticmethod
    def load(modname, classname, nodename):
        mod = __import__(modname, globals(), locals(), [classname], -1)
        try:
            cls = getattr(mod,classname)
            cls(nodename)
        except Exception:
            print "failed to load python attribute editor template '%s.%s'" % (modname, classname)
            import traceback
            traceback.print_exc()

    @classmethod
    def loadedTemplates(cls):
        "Return the names of the loaded templates"
        return cls._loaded

class AETemplate(object):
    """
    To create an Attribute Editor template using python, do the following:
     	1. create a subclass of `uitypes.AETemplate`
    	2. set its ``_nodeType`` class attribute to the name of the desired node type, or name the class using the
    convention ``AE<nodeType>Template``
    	3. import the module

    AETemplates which do not meet one of the two requirements listed in step 2 will be ignored.  To ensure that your
    Template's node type is being detected correctly, use the ``AETemplate.nodeType()`` class method::

        import AETemplates
        AETemplates.AEmib_amb_occlusionTemplate.nodeType()

    As a convenience, when pymel is imported it will automatically import the module ``AETemplates``, if it exists,
    thereby causing any AETemplates within it or its sub-modules to be registered. Be sure to import pymel
    or modules containing your ``AETemplate`` classes before opening the Atrribute Editor for the node types in question.

    To check which python templates are loaded::

    	from pymel.core.uitypes import AELoader
    	print AELoader.loadedTemplates()
    """

    __metaclass__ = AELoader

    _nodeType = None
    def __init__(self, nodeName):
        self._nodeName = nodeName

    @property
    def nodeName(self):
        return self._nodeName

    @classmethod
    def nodeType(cls):
        if cls._nodeType:
            return cls._nodeType
        else:
            m = re.match('AE(.+)Template$', cls.__name__)
            if m:
                return m.groups()[0]
            else:
                raise ValueError("You must either name your AETemplate subclass of the form 'AE<nodeType>Template' or set the '_nodeType' class attribute")
    @classmethod
    def controlValue(cls, nodeName, control):
        return cmds.editorTemplate(queryControl=(nodeName,control))
    @classmethod
    def controlLabel(cls, nodeName, control):
        return cmds.editorTemplate(queryLabel=(nodeName,control))
    @classmethod
    def reload(cls):
        "Reload the template. Beware, this reloads the module in which the template exists!"
        nodeType = cls.nodeType()
        form = "AttrEd" + nodeType + "FormLayout"
        exists = cmds.control(form, exists=1) and cmds.formLayout(form, q=1, ca=1)

        if exists:
            sel = cmds.ls(sl=1)
            cmds.select(cl=True)
            cmds.deleteUI(form)
            if sel:
                cmds.select(sel)
        reload(sys.modules[cls.__module__])

    def addControl(self, control, label=None, changeCommand=None, annotation=None, preventOverride=False, dynamic=False):
        args = [control]
        kwargs = {'preventOverride':preventOverride}
        if dynamic:
            kwargs['addDynamicControl'] = True
        else:
            kwargs['addControl'] = True
        if changeCommand:
            if hasattr(changeCommand, '__call__'):
                import pymel.tools.py2mel
                name = self.__class__.__name__ + '_callCustom_changeCommand_' + control
                changeCommand = pymel.tools.py2mel.py2melProc(changeCommand, procName=name, argTypes=['string'])
            args.append(changeCommand)
        if label:
            kwargs['label'] = label
        if annotation:
            kwargs['annotation'] = annotation
        cmds.editorTemplate(*args, **kwargs)
    def callCustom(self, newFunc, replaceFunc, *attrs):
        #cmds.editorTemplate(callCustom=( (newFunc, replaceFunc) + attrs))
        import pymel.tools.py2mel
        if hasattr(newFunc, '__call__'):
            name = self.__class__.__name__ + '_callCustom_newFunc_' + '_'.join(attrs)
            newFunc = pymel.tools.py2mel.py2melProc(newFunc, procName=name, argTypes=['string']*len(attrs))
        if hasattr(replaceFunc, '__call__'):
            name = self.__class__.__name__ + '_callCustom_replaceFunc_' + '_'.join(attrs)
            replaceFunc = pymel.tools.py2mel.py2melProc(replaceFunc, procName=name, argTypes=['string']*len(attrs))
        args = (newFunc, replaceFunc) + attrs
        cmds.editorTemplate(callCustom=1, *args)

    def suppress(self, control):
        cmds.editorTemplate(suppress=control)
    def dimControl(self, nodeName, control, state):
        #nodeName = nodeName if nodeName else self.nodeName
        #print "dim", nodeName
        cmds.editorTemplate(dimControl=(nodeName, control, state))

    def beginLayout(self, name, collapse=True):
        cmds.editorTemplate(beginLayout=name, collapse=collapse)
    def endLayout(self):
        cmds.editorTemplate(endLayout=True)

    def beginScrollLayout(self):
        cmds.editorTemplate(beginScrollLayout=True)
    def endScrollLayout(self):
        cmds.editorTemplate(endScrollLayout=True)

    def beginNoOptimize(self):
        cmds.editorTemplate(beginNoOptimize=True)
    def endNoOptimize(self):
        cmds.editorTemplate(endNoOptimize=True)

    def interruptOptimize(self):
        cmds.editorTemplate(interruptOptimize=True)
    def addSeparator(self):
        cmds.editorTemplate(addSeparator=True)
    def addComponents(self):
        cmds.editorTemplate(addComponents=True)
    def addExtraControls(self, label=None):
        kwargs = {}
        if label:
            kwargs['extraControlsLabel'] = label
        cmds.editorTemplate(addExtraControls=True, **kwargs)

    #TODO: listExtraAttributes


dynModule = _util.LazyLoadModule(__name__, globals())

def _createUIClasses():
    for funcName in _factories.uiClassList:
        # Create Class
        classname = _util.capitalize(funcName)
        try:
            cls = dynModule[classname]
        except KeyError:
            if classname.endswith( ('Layout', 'Grp') ):
                bases = (Layout,)
            elif classname.endswith('Panel'):
                bases = (Panel,)
            else:
                bases = (PyUI,)
            dynModule[classname] = (_factories.MetaMayaUIWrapper, (classname, bases, {}) )

_createUIClasses()

class MainProgressBar(dynModule.ProgressBar):
    '''Context manager for main progress bar

    If an exception occur after beginProgress() but before endProgress() maya
    gui becomes unresponsive. Use this class to escape this behavior.

     :Parameters:
        minValue : int
            Minimum or startingvalue of progress indicatior. If the progress
            value is less than the minValue, the progress value will be set
            to the minimum.  Default value is 0

        maxValue : int
            The maximum or endingvalue of the progress indicator. If the
            progress value is greater than the maxValue, the progress value
            will be set to the maximum. Default value is 100.

        interuruptable : bool
            Set to True if the isCancelled flag should respond to attempts to
            cancel the operation. Setting this to true will put make the help
            line display message to the user indicating that they can cancel
            the operation.

    Here's an example:

    .. python::
        with MainProgressBar(0,20,True) as bar:
            bar.setStatus('Calculating...')
            for i in range(0,20):
                bar.setProgress(i)
                if bar.getIsCancelled():
                    break
    '''
    def __new__(cls, minValue=0, maxValue=100, interruptable=True):
        from language import melGlobals
        bar = dynModule.ProgressBar.__new__(
            cls, melGlobals['gMainProgressBar'], create=False)
        bar.setMinValue(minValue)
        bar.setMaxValue(maxValue)
        bar.setIsInterruptable(interruptable)
        return bar

    def __enter__(self):
        self.beginProgress()
        return self

    def __exit__(self, *args):
        self.endProgress()

class VectorFieldGrp( dynModule.FloatFieldGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        if create:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = 3
            name = cmds.floatFieldGrp( name, *args, **kwargs)

        return dynModule.FloatFieldGrp.__new__( cls, name, create=False, *args, **kwargs )

    def getVector(self):
        import datatypes
        x = cmds.floatFieldGrp( self, q=1, v1=True )
        y = cmds.floatFieldGrp( self, q=1, v2=True )
        z = cmds.floatFieldGrp( self, q=1, v3=True )
        return datatypes.Vector( [x,y,z] )

    def setVector(self, vec):
        cmds.floatFieldGrp( self, e=1, v1=vec[0], v2=vec[1], v3=vec[2] )

class PathButtonGrp( dynModule.TextFieldButtonGrp ):
    PROMPT_FUNCTION = 'promptForPath'

    def __new__(cls, name=None, create=False, *args, **kwargs):

        if create:
            import windows

            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)

            promptFunction = getattr(windows, cls.PROMPT_FUNCTION)
            def setPathCB(name):
                f = promptFunction()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f, forceChangeCommand=True)

            import windows
            cb = windows.Callback( setPathCB, name )
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )

        return super(PathButtonGrp, cls).__new__( cls, name, create=False, *args, **kwargs )

    def setPath(self, path, **kwargs):
        kwargs['forceChangeCommand'] = kwargs.pop('fcc',kwargs.pop('forceChangeCommand',True))
        self.setText( path , **kwargs )

    def getPath(self):
        import system
        return system.Path( self.getText() )

class FolderButtonGrp( PathButtonGrp ):
    PROMPT_FUNCTION = 'promptForFolder'

# most of the keys here are names that are only used in certain circumstances
_uiTypesToCommands = {
    'radioCluster':'radioCollection',
    'rowGroupLayout' : 'rowLayout',
    'TcolorIndexSlider' : 'rowLayout',
    'TcolorSlider' : 'rowLayout',
    'floatingWindow' : 'window'
    }

dynModule._lazyModule_update()

