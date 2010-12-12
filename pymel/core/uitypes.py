import sys, re
import pymel.util as _util
import pymel.internal.pmcmds as cmds
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as _versions
import windows as _windows
import maya.mel as _mm
import pymel.internal.plogging as _plogging

_logger = _internal.getLogger(__name__)

def _resolveUIFunc(name):
    if isinstance(name, basestring):

        try:
            return getattr(_windows,name)
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
        
class PyUI(unicode):
    """
    Pymel UI object
    """
    
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
                uiType = cmds.objectTypeUI(name)
                uiType = _uiTypesToCommands.get(uiType, uiType)
            except RuntimeError:
                try:
                    # some ui types (radioCollections) can only be identified with their shortname
                    uiType = cmds.objectTypeUI(name.split('|')[-1])
                    uiType = _uiTypesToCommands.get(uiType, uiType)
                except RuntimeError:
                    # we cannot query the type of rowGroupLayout children: check common types for these
                    uiType = None
                    for control in 'checkBox floatField button floatSlider intSlider ' \
                            'floatField textField intField optionMenu radioButton'.split():
                        if getattr(cmds, control)( name, ex=1, q=1):
                            uiType = control
                            break
                    if not uiType:
                        uiType = 'PyUI'
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
                    try:
                        if issubclass(newcls,Layout):
                            parent = _windows.layout(name, q=1, p=1)
                        elif issubclass(newcls,Menu):
                            parent = _windows.menu(name, q=1, p=1)
                        else:
                            parent = _windows.control(name, q=1, p=1)
                        if parent:
                            name = parent + '|' + name
                    except ValueError:
                        pass    # menuItem not found
                    except RuntimeError:
                        # editors don't have a long name, so we keep the short name
                        if name not in cmds.lsUI(long=True,editors=True):
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
        return PyUI( '|'.join(buf) )
    getParent = parent

    def type(self):
        try:
            return cmds.objectTypeUI(self)
        except:
            return None

    def shortName(self):
        return unicode(self).split('|')[-1]
    def name(self):
        return unicode(self)
    def window(self):
        return Window( self.name().split('|')[0] )

    delete = _factories.functionFactory( 'deleteUI', rename='delete' )
    rename = _factories.functionFactory( 'renameUI', rename='rename' )
    type = _factories.functionFactory( 'objectTypeUI', rename='type' )

    #@classmethod
    def exists(self):
        return self.__class__.__melcmd__( str(self), exists=True )

    if _versions.current() >= _versions.v2011:
        asQtObject = toQtControl
    
    def setAsParent(self):
        try:
            return cmds.setParent(self)
        except RuntimeError:
            try:
                return cmds.setParent(self, m=1)
            except:
                pass

        return self
    
    def __enter__(self):
        self._previousParents = (cmds.setParent(q=1), cmds.setParent(q=1,m=1))
        self.setAsParent()
        return self
    
    def __exit__(self, type, value, tb):
        cmds.setParent(self._previousParents[0])
        cmds.setParent(self._previousParents[1], m=1)
        
class Panel(PyUI):
    """pymel panel class"""
    __metaclass__ = _factories.MetaMayaUIWrapper
    # note that we're not actually customizing anything, but
    # we're declaring it here because other classes will have this
    # as their base class, so we need to make sure it exists first

    
class TreeView(PyUI):
    """pymel TreeView class"""
    __metaclass__ = _factories.MetaMayaUIWrapper
    

    def getItemParent(self, item):
        parentItem = self.__melcmd__(self, q=1, itemParent=item)
        return self.TreeItem(self, parentItem) if parentItem else self

    def getItemIndex(self, item):
        return self.__melcmd__(self, q=1, itemIndex=item)
    
    def getIsItemExpanded(self, item):
        return self.__melcmd__(self, q=1, isItemExpanded=item)
    
    def getIsLeaf(self, item):
        return self.__melcmd__(self, q=1, isLeaf=item)

    def getButtonState(self, name, button):
        return self.__melcmd__(self, q=True, buttonState=True)

    def setButtonState(self, name, button, state='buttonDown'):
        self.__melcmd__(self, q=True, buttonState=(name, button, state))


        
    def addItem(self, name, parent=None, **kw):
        self.__melcmd__(self, edit=True, addItem=(name, parent or ""), **kw)
        return self.TreeItem(self, name)
    
    def getSelectItem(self):
        return [self[name] for name in self.__melcmd__(self, q=True, selectItem=True) or []]

    def setSelectItem(self, item, select=True):
        return self.__melcmd__(self, e=1, selectItem=(item,select))
    
        
    def __getitem__(self, name):
        return self.TreeItem(self, name)
    
    class TreeItem(str):
        """
        Represent a Tree Item in a pymel TreeView.
        """
    
        def __new__(cls, treeView, name):
            self = str.__new__(cls, name)
            self.treeView = treeView
            return self
        
        def __repr__(self):
            return "%s('%s','%s')" % (self.__class__.__name__, self.treeView, self)
            
        def _call(self, funcName, *args, **kw):
            args = (self,) + args
            if kw.pop('_packArgs',True):
                args = args,
            return getattr(self.treeView, funcName)(*args, **kw)
        
        def _callNoPack(self, funcName, *args, **kw):
            kw['_packArgs'] = False
            return self._call(funcName, *args, **kw)
            
        def addItem(self, name):
            return self.treeView.addItem(name, self)
            
        def __getitem__(self, name):
            return self.treeView[name]
    
    # TODO - factories probably has some utility functions that can do this better a nicer...
    def getFunc(funcName, noPack=True):
        if noPack:
            def func(self, *a, **b):  return self._callNoPack(funcName, *a, **b)
        else:
            def func(self, *a, **b):  return self._call(funcName, *a, **b)
        func.__name__ = funcName
        return func
    
    # don't pack args
    for funcName in ('getIsLeaf', 'getItemExists', 'getItemParent', 'getItemIndex',
                     'setSelectItem', 'showItem', 'getIsItemExpanded',
                     'setButtonState', 'getButtonState', 
                     
                     ):
        setattr(TreeItem, funcName, getFunc(funcName))

    # pack multiple args
    for funcName in ('borderHighlite', 'borderHighliteColor', 
                     'buttonState', 'buttonStyle', 'buttonTextIcon', 'buttonTooltip',
                     'buttonTransparencyColor', 'buttonTransparencyOverride', 'setButtonVisible',
                     'displayLabel', 'displayLabelSuffix', 'expandItem', 'enableButton', 'enableLabel',
                     'expandItem', 'font', 'fontFace', 'highlite', 'highliteColor', 'image',
                     'textColor', 
                     ):
        setattr(TreeItem, funcName, getFunc(funcName, False))
        
    del getFunc

class ObjectTreeView(TreeView):
    """
    
    A convenience object-oriented interface for the TreeView widget.
    Use the 'addObject' method to add objects to the tree-view. 
    The ObjectTreeView will use the overridden ObjectTreeItem.getObjectParent to determine an object's parent
    and will create the appropriate tree-structure automatically.
    Use the 'getSelectedObjects' method to get back at the original objects that were added into the tree-view.
    
    Example:

        # The following example creates a tree-view from a path object (see pymel.util.path)
        
        # override basic methods in the
        class PathTreeItem(ObjectTreeView.ObjectTreeItem):
    
            @classmethod
            def getObjectParent(cls, object):
                # classmethod, determine the parent of an object. In this case, use the path object methods
                # to determine if the path is at the root mount-point ('C:\'), and if not return the parent
                # directory ('C:\Windows\System32\something.log' --> 'C:\Windows\System32') 
                return (not object.ismount() and object.parent)     
    
            def getDisplayLabel(self):
                return self.object.name or self.object    # self.object is the object this tree-item represents 
    
            def getIsBorderHighlighted(self):
                return len(self.object.splitall())%3==0   # causes the tree-item to be highlighted 
        
        with window() as win:
             with verticalLayout() as layout:
                 # create the ObjectTreeView, specifying the PathTreeItem as the treeItemClass
                 tree = ObjectTreeView(create=1, parent = layout, numberOfButtons = 2, treeItemClass=PathTreeItem )
        
        # Add the current workspace path to the tree-view
        tree.addObject(workspace.getcwd())

    """
    
    class ObjectTreeItem(TreeView.TreeItem):
        
        def __new__(cls, treeView, name, *args, **kwargs):
            try:
                return treeView[name]
            except KeyError:
                return super(ObjectTreeView.ObjectTreeItem, cls).__new__(cls, treeView, name)
            
        @classmethod
        def getObjectParent(cls, object):
            """
            Override this for the particular object type so that it returns it's parent object.
            NOTE - this method must be kept decorated as a 'classmethod'.
            """
            return None
        
        def refresh(self):
            self.displayLabel(self.getDisplayLabel())
            self.highlite(self.getIsHighlighted())
            self.borderHighlite(self.getIsBorderHighlighted())
            
        def getDisplayLabel(self):
            """
            Override this for the particular object type so that it returns the desired display-label
            to be shown in the ObjectTreeView
            """
            return str(self.object)
        
        def getIsHighlighted(self):
            return False
        
        def getIsBorderHighlighted(self):
            return False
        
        def editLabelCommad(self, newLabel):
            """
            Callback - override this for desired behavior when the display-label is edited by the user.
            return False/None to prevent the label from being edited. 
            """
            print newLabel
            return
        
        def expandCollapseCommand(self, expanded):
            """
            Callback - override this for desired behavior when the item is expanded or collapesed.
            """
            print expanded
            return
            
    
    def __new__(cls, *args, **kwargs):
        kwargs.pop('treeItemClass', None)
        return super(ObjectTreeView, cls).__new__(cls, *args, **kwargs)
        
    def __init__(self, *args, **kwargs):
        #self.objectParent = kwargs.pop('objectParent', lambda n: None)
        self.TreeItem = kwargs.pop('treeItemClass', self.ObjectTreeItem)
        self.allItems = {}

#        TODO - install these callbacks using mel :(..., since pure python isn't supported apparently
#
#        kw = set(kwargs)
#        if not set(('editLabelCommand','elc')) & kw:
#            self.editLabelCommand(self._editLabelCommand)
#        if not set(('expandCollapseCommand', 'ecc')) & kw:
#            self.expandCollapseCommand(self._expandCollapseCommand)
        
        
    def _editLabelCommand(self, name, newLabel):
        return self[name].editLabelCommad(newLabel)
    
    def _expandCollapseCommand(self, name, expanded):
        return self[name].expandCollapseCommand(expanded)
    
    def __getitem__(self, name):
        return self.allItems[long(name)]
        
    def getObjectItem(self, object):
        return self.allItems.get(hash(object))

    def addObject(self, object, refresh=True, expand=True):
        id = hash(object)
        
        parent = self.TreeItem.getObjectParent(object)
        
        parentItem = parent and (self.getObjectItem(parent) or self.addObject(parent, refresh, expand))
        
        try:
            item = self.allItems[id]
        except KeyError:
            self.allItems[id] = item = self.addItem(id, parentItem)
        item.object = object
        item.refresh()
        return item
    
    def removeAll(self):
        super(ObjectTreeView, self).removeAll()
        items = self.allItems.values()
        self.allItems = {}
        return [item.object for item in items]
    
    def reset(self):
        return [self.addObject(object, False) for object in sorted(self.removeAll())]
        
    def refresh(self):
        for item in self.allItems.itervalues():
            item.refresh()

    getSelectedItems = TreeView.getSelectItem
    
    def getSelectedObjects(self):
        return [item.object for item in self.getSelectedItems()]

    
class Layout(PyUI):

    def children(self):
        #return [ PyUI( self.name() + '|' + x) for x in self.__melcmd__(self, q=1, childArray=1) ]
        return [ PyUI( self.name() + '|' + x) for x in cmds.layout(self, q=1, childArray=1) or [] ]

    getChildren = children

    def walkChildren(self):
        for child in self.children():
            yield child
            if hasattr(child, 'walkChildren'):
                for subChild in child.walkChildren():
                    yield subChild

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

    def __exit__(self, *args):
        super(Window, self).__exit__(*args)
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
    def __exit__(self, *args):
        self.redistribute()
        super(AutoLayout, self).__exit__(*args)

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
        
    def getSelectIndexedItem(self):
        """
        Returns the current selection as list of indices.
        Modified to returns empty list if nothing is selected.
        """
        return cmds.textScrollList(self, q=1, selectIndexedItem=True) or []        

class PopupMenu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper
    
    def setAsParent(self):
        return cmds.setParent(self, m=1)
    

class OptionMenu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def setAsParent(self):
        return cmds.setParent(self, m=1)
    
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

class Menu(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper

    def getItemArray(self):
        """ Modified to return pymel instances """
        children = cmds.menu(self,query=True,itemArray=True)
        if children:
            return [MenuItem(item) for item in cmds.menu(self,query=True,itemArray=True)]
        else:
            return []
        
    def setAsParent(self):
        return cmds.setParent(self, m=1)

class SubMenuItem(Menu):
    
    __melui__ = 'menuItem'

#    def getBoldFont(self):
#        return cmds.menuItem(self,query=True,boldFont=True)
#
#    def getItalicized(self):
#        return cmds.menuItem(self,query=True,italicized=True)
    
    if _versions.current() >= _versions.v2011:
        asQtObject = toQtMenuItem
        
class CommandMenuItem(PyUI):
    __metaclass__ = _factories.MetaMayaUIWrapper

def MenuItem(name=None, create=False, **kwargs):
    if PyUI._isBeingCreated(name, create, kwargs):
        cls = CommandMenuItem
    else:
        try:
            uiType = cmds.objectTypeUI(name)
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
    _loaded = []
    def __new__(cls, classname, bases, classdict):
        newcls = super(AELoader, cls).__new__(cls, classname, bases, classdict)
        try:
             nodeType = newcls.nodeType()
        except ValueError:
             _logger.debug("could not determine node type for " + classname)
        else:
             modname = classdict['__module__']
             template = 'AE'+nodeType+'Template'
             cls.makeAEProc(modname, classname, template)
             if template not in cls._loaded:
                 cls._loaded.append(template)
        return newcls
    
    @staticmethod
    def makeAEProc(modname, classname, procname):
        _logger.info("making AE loader procedure: %s" % procname)
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
            if classname.endswith('Layout'):
                bases = (Layout,)
            elif classname.endswith('Panel'):
                bases = (Panel,)                
            else:
                bases = (PyUI,)
            dynModule[classname] = (_factories.MetaMayaUIWrapper, (classname, bases, {}) )

_createUIClasses()

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
    def __new__(cls, name=None, create=False, *args, **kwargs):

        if create:
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)

            def setPathCB(name):
                f = _windows.promptForPath()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f)

            cb = _windows.Callback( setPathCB, name )
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )

        return dynModule.TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )

    def setPath(self, path):
        self.setText( path )

    def getPath(self):
        import system
        return system.Path( self.getText() )

if sys.version_info > (2,6):
    from pymel.util.utilitytypes import OldUserList as UserList
else:
    from UserList import UserList

@_util.decorator
def refreshing(func):
    def dec(self, *x, **y):
        sel = self.getSelected()
        ret = func(self, *x, **y)
        self.refresh(reselect=False)
        self.select(sel)
        return ret
    return dec

class ObjectScrollList(UserList, TextScrollList):
    """
    A dynamic scroll-list widget that behaves similar to the built-in python list type.
    Override or set the 'objectToString' function to a function that function that will 
    return the string representation for an object for display in the scroll-list.
    
    Example:
    with window() as win:
        with verticalLayout() as layout:
            objectScroll = objectScrollList(parent = layout, allowMultiSelection=1, font='smallFixedWidthFont')
    
    # determine how the objects are displayed in the list
    objectScroll.objectToString = lambda n: "<%05d>" % n

    objectScroll.extend(range(10))    # add items
    objectScroll[-3:] = [20,30,40]    # modify using slicing
    objectScroll.select((6,9,1))      # select objects  
    print objectScroll.getSelected()
    # Result: [1, 6, 9] # 

    # modify the display method
    objectScroll.objectToString = lambda n: "<%4d>" % n
    objectScroll.refresh()
    
    # getSelected returns original objects, not strings.
    print objectScroll.getSelected()
    # Result: [1, 6, 9] # 
    
    """
    
    def __new__(cls, *args, **kwargs):
        #kwargs['create'] = True
        self = TextScrollList.__new__(cls, *args, **kwargs)
        return self
    
    def __init__(self, *args, **kwargs):
        initlist = kwargs.pop('initlist',None)
        TextScrollList.__init__(self, *args,**kwargs)
        UserList.__init__(self, initlist=initlist)
        self.objectToIndices = {}

        if self.getAllowMultiSelection():
            self._converter = lambda l: l
        else:
            self._converter = lambda l: l[0] if l else None

    __nonzero__ = lambda self: True
    
    objectToString = str

    d = locals()
    for fn in ['append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort',
               '__setslice__', '__delslice__', '__imul__', '__iadd__', '__setitem__']:
        func = refreshing(getattr(UserList,fn))
        d[fn] = func
    del d, func, fn

    #================================================================================
    
    def refresh(self, items=None, reselect=True):
        sel = reselect and self.getSelected()
        if items:
            if not hasattr(items, "__iter__"):
                items = [items]
            for o in items:
                if o in self.objectToIndices:
                    pos = self.objectToIndices[o][-1]
                    self.removeIndexedItem(pos)
                    self.appendPosition((pos, self.objectToString(o)))        
        else:
            self.removeAll(1)
            self.objectToIndices.clear()
            for i, o in enumerate(self.data):
                TextScrollList.append(self, self.objectToString(o))
                self.objectToIndices.setdefault(o,[]).append(i+1)
        if sel and self.data: self.select(sel)
        
    def select(self, objects):
        if not hasattr(objects,"__iter__"):
            objects = [objects]
        indices = [i for o in objects for i in self.objectToIndices.get(o,[])]
        self.setSelectIndexedItem(indices)

    @property
    def selectedIndices(self):
        return [i-1 for i in self.getSelectIndexedItem()]

    def getSelected(self):
        """
        Returns the currently selected object or None.
        If 'allowMultiSelection' is True then returns the list of objects (or empty list)
        """
        ret = [self[s] for s in self.selectedIndices]
        return self._converter(ret)

    getValue = getSelected

    def popSelected(self):
        ret = [self.pop(i) for i in reversed(self.selectedIndices)]
        ret.reverse()
        return self._converter(ret)


class ObjectMenu(UserList, OptionMenu):
    """
    A dynamic option-menu widget that behaves similar to the built-in python list type.
    Override or set the 'objectToString' function to a function that function that will 
    return the string representation for an object for display in the scroll-list.
    
    Example:
    with window() as win:
        with verticalLayout() as layout:
            objectScroll = objectScrollList(parent = layout, allowMultiSelection=1, font='smallFixedWidthFont')
    
    # determine how the objects are displayed in the list
    objectScroll.objectToString = lambda n: "<%05d>" % n

    # add items
    objectScroll.extend(range(10))
    
    # use basic list operations to modify the option-menu
    objectScroll[0] = 10
    objectScroll[3:] = [30,40,50]
    objectScroll.select(40)
    
    # getSelected returns original objects, not strings
    100 + objectScroll.getSelected()
    # Result: 140 # 
    """  
    def __init__(self, *args, **kwargs):
        #kwargs['create'] = True
        initlist = kwargs.pop('initlist',None)
        OptionMenu.__init__(self, *args,**kwargs)
        UserList.__init__(self, initlist=initlist)
        self.title = None
        self.objectToIndices = {}

    def __new__(cls, *args, **kwargs):
        #kwargs['create'] = True
        self = OptionMenu.__new__(cls, *args, **kwargs)
        return self

    __nonzero__ = lambda s: True
    objectToString = str

    d = locals()
    for fn in ['append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort',
               '__setslice__', '__delslice__', '__imul__', '__iadd__', '__setitem__']:
        func = refreshing(getattr(UserList,fn))
        d[fn] = func
    del d, func, fn

    #================================================================================

    def addMenuItems(self, items, title=None):
        self.data.extend(items)
        self.title = title
        self.refresh()
    
    def refresh(self, reselect=False):
        sel = reselect and self.getSelected()
        self.clear()
        offset = 1
        if self.title:
            _windows.menuItem(l = self.title, en = 0,parent = self)
            offset += 1
        self.objectToIndices.clear()
        for i, o in enumerate(self.data):
            _windows.menuItem(l = self.objectToString(o), parent = self)            
            self.objectToIndices.setdefault(o,[]).append(i+offset)
        if reselect: self.select(reselect)
        
    def select(self, object):
        if object and object in self.objectToIndices:
            self.setSelect(self.objectToIndices[object][-1])

    def getSelected(self):
        idx = self.getSelect()
        if idx:
            return self[idx-1]
        
    getValue = getSelected        

    def popSelected(self):
        ret = self.pop(self.getSelect())
        self.refresh()
        return ret

class ModalLayout(FormLayout):
    """
    A base class for creating Modal Dialog Boxes.
    To launch the dialog box, call the 'prompt' class-method on the derived class. All paramters will be passed directly to the 'buildLayout' method,
    which must be implemented on the derived class.
    
    To return a value from the prompt:       self.returnValue(value)
    To cancel the prompt and return None:    self.cancel()            
    
    Example:
    
        class ExampleLayout(ModalLayout):
        
            def buildLayout(self, defaultColor=None, *args, **kwargs):
                with verticalLayout(ratios=[0,1]) as self.topLayout:
                    with horizontalLayout() as self.buttons:
                        button(label="All", c=Callback(self.selected, all=True))
                        button(label="Select", c=pm.Callback(self.selected))
                        button(label="Cancel", c=pm.Callback(self.cancel))
                    self.list = objectScrollList(ams=True, p=self.topLayout )
                
                self.list[:] = ['blue', 'red', 'green', 'white']
                if defaultColor:
                    self.list.select(defaultColor)
        
            @classmethod
            def prompt(cls):
                return super(ExampleLayout, cls).prompt(title="Choose a color", width=500, height=100, defaultColor='red')
        
            def selected(self, all=False):
                if all:
                    return self.returnValue(self.list.data)
                self.returnValue(self.list.getSelected()) 
                
        print ExampleLayout.prompt()
    """
    value = None
    def __new__(cls, *args):
        p = cmds.setParent(q=True)
        self = FormLayout.__new__(cls, p)
        return self

    def __init__(self, *args):
        super(ModalLayout, self).__init__(spacing=0, orientation=FormLayout.VERTICAL)
        try:
            kwargs = self.kwargs
            args = self.args
            with self:
                self.buildLayout(*args, **kwargs)
    
            if 'width' in kwargs:         self.setWidth(kwargs['width'])
            if 'height' in kwargs:        self.setHeight(kwargs['height'])
        except Exception, e:
            self.__class__.exc_info = sys.exc_info()
            from maya.utils import executeDeferred
            executeDeferred(cmds.layoutDialog, dismiss="Error")
            
    def buildLayout(self, *args, **kwargs):
        txt = _windows.text(l="Override the 'buildLayout' method of this class")
        btn = _windows.button(l="(Close)", c=self.cancel)
        self.attachForm(btn,"bottom",2)
        self.attachForm(btn,"right",2)
        self.setWidth(250)
        
    def returnValue(self, value):
        """
        Call this method to dismiss the prompt window and return 'value'.
        """
        self.__class__.value = value
        return cmds.layoutDialog(dismiss="True")

    def cancel(self, *args):
        """
        Call this method to dismiss the prompt window and return None
        """
        return cmds.layoutDialog(dismiss="")

    @classmethod
    def prompt(cls, title="Dialog Box", width=100, height=200, *args, **kwargs):
        """
        Call this method to display the prompt window and wait for the user.
        """
        kwargs['width'] = width
        kwargs['height'] = height
        cls.args = args
        cls.kwargs = kwargs
        if _versions.current() > _versions.v2008:
            ret = str(cmds.layoutDialog(title=title, ui=cls))
        else:
            sys._tmp_cls = cls  # temporarily make this class object accessible globally
            ret = str(cmds.layoutDialog(title=title, ui="""python("import sys; sys._tmp_cls()")"""))
            del sys._tmp_cls
        
        if ret == "True":
            return cls.value
        elif ret == "Error":
            type, value, tb = cls.exc_info
            raise type, value, tb
    
class ListSelectLayout(ModalLayout):
    """
    This Layout Class is specifically designed to be used by the promptFromList function.
    A ModalLayout showing a list of items for the user to select from.
    """

    def buildLayout(self, items, prompt, ok, cancel, default, allowMultiSelection, 
                    width, height, objectToString, **kwargs):
        self.ams = allowMultiSelection
        self.items = list(items)
        kwargs.update(dict(dcc=self.returnSelection, allowMultiSelection=allowMultiSelection))
        
        with _windows.verticalLayout(ratios=[0,0,1], p=self) as self.topLayout:
            self.prompt = _windows.text(l=prompt)
            self.selectionList = _windows.objectScrollList(**kwargs)
            with _windows.horizontalLayout(ratios=[1,1]) as self.buttons:
                _windows.button(l=ok, c=self.returnSelection)
                _windows.button(l=cancel, c=self.cancel) 

        self.selectionList.objectToString = objectToString
        self.selectionList[:] = self.items
        if default:
            if not hasattr(default,"__iter__"):
                default = [default]
            self.selectionList.select(default)
        
        for side in ["top", "right", "left", "bottom"]:
            self.attachForm(self.topLayout, side, 0)
            self.topLayout.attachNone(self.buttons, "top")
            self.topLayout.attachControl(self.selectionList, "bottom", 0, self.buttons)
        
    def returnSelection(self, *args):
        self.returnValue(self.selectionList.getSelected())
    
def promptFromList(items, title="Selector", prompt="Select from list:", ok="Select", cancel="Cancel", 
                   default=None, allowMultiSelection=False, width=150, height=200, ams=False,
                   objectToString=str, **kwargs):
    """
    Prompt the user to select items from a list of objects.
    Any python object can be used, and it will be returned as the same object if selected (no forced conversion to string).
    
    @param title: Window title
    @param prompt: A message to display above the selection list
    @param ok: The text for the 'OK' button
    @param cancel: The text for the 'Cancel' button
    @param default: The default selection (single object or a list of objects)
    @param allowMultiSelection: Set to True  to allow multiple object selection
    @param ams: Short for 'allowMultiSelection'
    @param objectToString: The function to use when displaying the objects in the scroll list
    
    Example:
        ret = promptFromList([1,2,"hello",(4,5)], ams=1, default=[2,"hello"])
        print "%r" % ret
    """
    return ListSelectLayout.prompt(title=title, items=items, prompt=prompt, ok=ok, cancel=cancel, 
                             default=default, allowMultiSelection=allowMultiSelection or ams, 
                             width=width, height=height, objectToString=objectToString, **kwargs)


class FrameLayout(Layout):
    """pymel frame-layout class"""
    __metaclass__ = _factories.MetaMayaUIWrapper
    # note that we're not actually customizing anything, but
    # we're declaring it here because other classes will have this
    # as their base class, so we need to make sure it exists first    

class TextLayout(FrameLayout):
    
    def __new__(cls, name=None, create=False, parent=None, text=None):
        if create:
            self = _windows.frameLayout(labelVisible=bool(name), label=name or "Text Window", parent=parent)
        return FrameLayout.__new__(cls, self)

    def __init__(self, *args, **kwargs):
        with _windows.verticalLayout() as self.topForm:
            self.txtInfo =  _windows.scrollField(editable=False)
        
        self.setText(kwargs.get('text',""))
        
    def setText(self, text=""):
        from pprint import pformat
        if not isinstance(text, basestring):
            text = pformat(text)
        self.txtInfo.setText(text)
        self.txtInfo.setInsertionPosition(1)


# Unlike most ui widgets the progressWindow is unique and only has one instance in the maya session.
# For this reason its associated command only receive flags, and does not require the widget's name.
# The MetaMayaUIWrapper (which automatically creates methods for a given UI class) always passes 'self'
# into the underlying maya command, which is undesired in this case.
# To work around that we wrap the original progressWindow function with the following function, which
# skips the 'self' argument if it is indeed the singleton instance of the ProgressWindow
def myFunc(*args, **kwargs):
    if args:
        self = args[0]
        if self is ProgressWindow.__singleton__:
            args = args[1:]
    return cmds.progressWindow(*args, **kwargs)

_util.decorated(_windows.progressWindow, myFunc)
myFunc.__doc__ = _factories.addCmdDocsCallback("progressWindow")
_windows.progressWindow = myFunc

class ProgressWindow(object):
    """
    Blaaa
    """
    
    __metaclass__ = _factories.MetaMayaUIWrapper
    __singleton__ = None
    
    class StoppedByUser(KeyboardInterrupt): pass

    class ProgressHandler(_plogging.Handler):
        """
        This is the logging handler used to step the progress-bar.
        It is installed at the root of the logging tree when the progress window is first loaded,
        and removed when it window is closed.
        """
        def emit(self, record):
            if record.levelno>_plogging.DEBUG:
                self.progress.setStatus(self.format(record))
            if self.progress.getIsCancelled():
                self.progress._cancel()
            else:
                self.progress._doProgress()
    
        def handleError(self, *args, **kwargs):
            # normally handleError suppresses exceptions thrown while logging, but here we
            # need to allow the StoppedByUser to be raised so that it stops the progress
            raise
    
    _stack = []
    _history = {}
    __slots__ = '_globalProgress'   # used to keep track of the overall progress of nested-processes
    _handler = ProgressHandler(level=0)
    
    def __new__(cls):
        if not cls.__singleton__:
            cls.__singleton__ = object.__new__(cls)
        return cls.__singleton__

    def __init__(self):
        from pymel.core.language import optionVar
        _logger.debug("Loading progressWindow cached data...")
        for k,v in optionVar.iteritems():
            if k.startswith("%s.progress" % (__name__)):
                id = ".".join(k.split(".")[-2:])
                _logger.debug("    %-20s: %10d" % (k,v))
                self._history[id] = v
        self._globalProgress = 0        
    
    def _call(self,*args ,**kwargs):
        return _windows.progressWindow(*args ,**kwargs)

    def _cancelProgress(self):
        """
        Raises a StoppedByUser exception
        """
        raise self.StoppedByUser("(while in '%s')" % self._stack[-1][0])        

    def reset(self, **kwargs):
        self.end()
        self._call(edit=True,
            progress = 0,
            status = " "*100,   # this ensures the progress window will be wide enough
            isInterruptable = True,
            max = 100,
            min = 0)
        self._call(**kwargs)
        
        if self._handler not in _plogging.root.handlers:
            _plogging.root.addHandler(self._handler)
        self._handler.progress = self
        self._globalProgress = 0
        
    def end(self):
        self._call(endProgress=True)
        _plogging.root.removeHandler(self._handler)

    def _doProgress(self, by=1):
        self._globalProgress += by
        self.step(by)
        id, estimatedSteps, lastPosition = self._stack[-1]
        if (self._globalProgress - lastPosition)>=estimatedSteps:
            # we've hit the end, update the range to make it wider
            max = self._stack[-1][1] =  estimatedSteps * 1.5
            self.setMaxValue(max)

    def processBegin(self, func, estimatedSteps=None, title=None):
        """
        Begin a progress-tracked function/context. 
        This can be called in a nested fashion, meaning a new 'sub' process can begin before the 
        previous 'parent process' is over.
        """
        id = '%s.%s' % (func.__module__, func.__name__) if (func and callable(func)) else func
        self.setTitle(title or 
              ((func and callable(func)) and ("In Module '%s', Function '%s'..." % (func.__module__, func.__name__))) or 
              "(Processing...)") 
        estimatedSteps = estimatedSteps or self._history.get(id) or 100
        if not self._stack:
            # stack is empty - start fresh new progressWindow
            self.reset(max = estimatedSteps)
        else:
            self.setProgress(0)
        currentProgress = self._globalProgress
        self._stack.append([id, estimatedSteps, currentProgress])

    def processEnd(self):
        """
        End the current progress-tracked function/context.
        When the last process is ended the progressWindow will be finalized and closed.
        """
        if self._stack:
            id, estimatedSteps, lastPosition = self._stack.pop()
            actualSteps = self._globalProgress - lastPosition
            self._history[id] = int( .5 + # for rounding
                (.75 * actualSteps) + 
                (.25 * self._history.get(id,actualSteps))
                )
                
            self._call(edit=True, max=estimatedSteps, progress=lastPosition)
        
        # there's a good reason for not putting an 'else' here! (see self._stack.pop() above...?)
        if not self._stack:
            from pymel.core.language import optionVar
            self.end()
            # storing the actual progress of the tracked functions/contexts
            for k,v in self._history.iteritems():
                optionVar["%s.progress.%s" % (__name__, k)] = v    


# most of the keys here are names that are only used in certain circumstances
_uiTypesToCommands = {
    'radioCluster':'radioCollection',
    'rowGroupLayout' : 'rowLayout',
    'TcolorIndexSlider' : 'rowLayout',
    'TcolorSlider' : 'rowLayout',
    'floatingWindow' : 'window'
    }

dynModule._lazyModule_update()

