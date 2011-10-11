"""
Functions for creating UI elements, as well as their class counterparts.
"""

import re, sys, functools, traceback

import pymel.util as _util
import pymel.internal.pmcmds as cmds
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as _versions

from language import mel, melGlobals
from system import Path as _Path
# Don't import uitypes  - we want to finish setting up the commands in this
# module before creating the uitypes classes; this way, the methods on the
# uitypes classes can use the functions from THIS module, and inherit things
# like simpleCommandWraps, etc
#import uitypes as _uitypes
    
_logger = _internal.getLogger(__name__)

_thisModule = sys.modules[__name__]
# Note - don't do
#     __import__('pymel.core.windows').XXX
# ...as this will get the 'original' module, not the dynamic one!
# Do:
#    import pymel.core.windows; import sys; sys.modules[pymel.core.windows].XXX
# instead!
thisModuleCmd = "import %s; import sys; sys.modules[%r]" % (__name__, __name__)

#-----------------------------------------------
#  Enhanced UI Commands
#-----------------------------------------------

def _lsUI( **kwargs ):
    long = kwargs.pop( 'long', kwargs.pop( 'l', True ) )
    head = kwargs.pop( 'head', kwargs.pop( 'hd', None ) )
    tail = kwargs.pop( 'tail', kwargs.pop( 'tl', None) )

    if not kwargs:
        kwargs = {
            'windows': 1, 'panels' : 1, 'editors' : 1, 'controls' : 1, 'controlLayouts' : 1,
            'collection' : 1, 'radioMenuItemCollections' : 1, 'menus' : 1, 'menuItems' : 1,
            'contexts' : 0, 'cmdTemplates' : 1
            }
    kwargs['long'] = long
    if head is not None: kwargs['head'] = head
    if tail is not None: kwargs['tail'] = tail
    return _util.listForNone(cmds.lsUI(**kwargs))

# all optionMenus are popupMenus, but not all popupMenus are optionMenus
_commandsToUITypes = {
    'optionMenu':'popupMenu',
    }

def _findLongName(name, type=None):
    # this remap is currently for OptionMenu, but the fix only works in 2011
    # lsUI won't list popupMenus or optionMenus
    kwargs = { 'long' : True}
    if type:
        kwargs['type'] = _commandsToUITypes.get(type, type)

    uiObjs = _util.listForNone(_lsUI( **kwargs ))
    res = [ x for x in uiObjs if x.endswith( '|' + name) ]
    if len(res) > 1:
        raise ValueError, "found more than one UI element matching the name %s" % name
    elif len(res) == 0:
        raise ValueError, "could not find a UI element matching the name %s" % name
    return res[0]

def lsUI( **kwargs ):
    """
Modified:
  - long defaults to True
  - if no type is passed, defaults to all known types
    """
    import uitypes
    return [ uitypes.PyUI(x) for x in _lsUI( **kwargs ) ]

scriptTableCmds = {}

def scriptTable(*args, **kwargs):
    """
Maya Bug Fix:
    - fixed getCellCmd to work with python functions, previously only worked with mel callbacks
        IMPORTANT: you cannot use the print statement within the getCellCmd callback function or your values will not be returned to the table
    """
    import uitypes    
    cb = kwargs.pop('getCellCmd', kwargs.pop('gcc',None) )
    cc = kwargs.pop('cellChangedCmd', kwargs.pop('ccc',None) )

    uiName = cmds.scriptTable( *args, **kwargs )
    if "q" in kwargs or "query" in kwargs:
        return uiName

    kwargs.clear()
    if cb:
        if hasattr(cb, '__call__'):
            procName = 'getCellMel%d' % len(scriptTableCmds.keys())
            key = '%s_%s' % (uiName,procName)

            procCmd = """global proc string %s( int $row, int $column ) {
                            return python(%s.scriptTableCmds['%s'](" + $row + "," + $column + ")");}
                      """ %  (procName, thisModuleCmd, key)
            mel.eval( procCmd )
            scriptTableCmds[key] = cb

            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key,None)))
            cb = procName
        kwargs['getCellCmd'] = cb
    if cc:
        if hasattr(cc, '__call__'):
            procName = 'cellChangedCmd%d' % len(scriptTableCmds.keys())
            key = '%s_%s' % (uiName,procName)
            # Note - don't do
            #     __import__('pymel.core.windows').XXX
            # ...as this will get the 'original' module, not the dynamic one!
            # Do:
            #    import pymel.core.windows; import sys; sys.modules[pymel.core.windows].XXX
            # instead!
            procCmd = """global proc int %s( int $row, int $column, string $val) {
                            return python("%s.scriptTableCmds['%s'](" + $row + "," + $column + ",'" + $val + "')");}
                      """ %  (procName, thisModuleCmd, key)
            mel.eval( procCmd )
            scriptTableCmds[key] = cc

            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key,None)))
            cc = procName
        kwargs['cellChangedCmd'] = cc

    if kwargs:
        cmds.scriptTable( uiName, e=1, **kwargs)
    return uitypes.ScriptTable(uiName)

def getPanel(*args, **kwargs):
    typeOf = kwargs.pop('typeOf', kwargs.pop('to', None) )
    if typeOf:
        # typeOf flag only allows short names
        kwargs['typeOf'] = typeOf.rsplit('|',1)[-1]
    return cmds.getPanel(*args, **kwargs )
#
#
#def textScrollList( *args, **kwargs ):
#    """
#Modifications:
#  - returns an empty list when the result is None for queries: selectIndexedItem, allItems, selectItem queries
#    """
#    res = cmds.textScrollList(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('selectIndexedItem', 'sii'), ('allItems', 'ai'), ('selectItem', 'si',)] )
#
#def optionMenu( *args, **kwargs ):
#    """
#Modifications:
#  - returns an empty list when the result is None for queries: itemListLong, itemListShort queries
#    """
#    res = cmds.optionMenu(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )
#
#def optionMenuGrp( *args, **kwargs ):
#    """
#Modifications:
#  - returns an empty list when the result is None for queries: itemlistLong, itemListShort queries
#    """
#    res = cmds.optionMenuGrp(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )
#
#def modelEditor( *args, **kwargs ):
#    """
#Modifications:
#  - casts to PyNode for queries: camera
#    """
#    res = cmds.modelEditor(*args, **kwargs)
#    if kwargs.get('query', kwargs.get('q')) and kwargs.get( 'camera', kwargs.get('cam')):
#        import general
#        return general.PyNode(res)
#    return res

#===============================================================================
# Provides classes and functions to facilitate UI creation in Maya
#===============================================================================

class BaseCallback(object):
    """
    Base class for callbacks.
    """
    def __init__(self,func,*args,**kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.traceback = traceback.format_stack()

if _versions.current() >= _versions.v2009:

    class Callback(BaseCallback):
        """
        Enables deferred function evaluation with 'baked' arguments.
        Useful where lambdas won't work...

        It also ensures that the entire callback will be be represented by one
        undo entry.

        Example:

        .. python::

            import pymel as pm
            def addRigger(rigger, **kwargs):
                print "adding rigger", rigger

            for rigger in riggers:
                pm.menuItem(
                    label = "Add " + str(rigger),
                    c = Callback(addRigger,rigger,p=1))   # will run: addRigger(rigger,p=1)
        """
        def __call__(self,*args):
            cmds.undoInfo(openChunk=1)
            try:
                try:
                    return self.func(*self.args, **self.kwargs)
                except Exception, e:
                    raise _factories.CallbackError(self, e)
            finally:
                cmds.undoInfo(closeChunk=1)

    class CallbackWithArgs(Callback):
        def __call__(self,*args,**kwargs):
            # not sure when kwargs would get passed to __call__,
            # but best not to remove support now
            kwargsFinal = self.kwargs.copy()
            kwargsFinal.update(kwargs)
            cmds.undoInfo(openChunk=1)
            try:
                try:
                    return self.func(*self.args + args, **kwargsFinal)
                except Exception, e:
                    raise _factories.CallbackError(self, e)                
            finally:
                cmds.undoInfo(closeChunk=1)
else:

    class Callback(BaseCallback):
        """
        Enables deferred function evaluation with 'baked' arguments.
        Useful where lambdas won't work...
        Example:

        .. python::

            import pymel as pm
            def addRigger(rigger, **kwargs):
                print "adding rigger", rigger

            for rigger in riggers:
                pm.menuItem(
                    label = "Add " + str(rigger),
                    c = Callback(addRigger,rigger,p=1))   # will run: addRigger(rigger,p=1)
        """

        # This implementation of the Callback object uses private members
        # to store static call information so that the call can be made through
        # a mel call, thus making the entire function call undoable
        _callData = None
        @staticmethod
        def _doCall():
            (func, args, kwargs) = Callback._callData
            Callback._callData = func(*args, **kwargs)

        def __call__(self,*args):
            Callback._callData = (self.func, self.args, self.kwargs)
            try:
                mel.python("%s.Callback._doCall()" % thisModuleCmd)
            except Exception, e:
                raise _factories.CallbackError(self.func, e)   
            return Callback._callData

    class CallbackWithArgs(Callback):
        def __call__(self,*args,**kwargs):
            kwargsFinal = self.kwargs.copy()
            kwargsFinal.update(kwargs)
            Callback._callData = (self.func, self.args + args, kwargsFinal)
            try:
                mel.python("%s.Callback._doCall()" % thisModuleCmd)
            except Exception, e:
                raise _factories.CallbackError(self.func, e)
            return Callback._callData


def verticalLayout(*args, **kwargs):
    kwargs['orientation'] = 'vertical'
    return autoLayout(*args, **kwargs)

def horizontalLayout(*args, **kwargs):
    kwargs['orientation'] = 'horizontal'
    return autoLayout(*args, **kwargs)

def promptBox(title, message, okText, cancelText, **kwargs):
    """ Prompt for a value. Returns the string value or None if cancelled """
    ret = promptDialog(t=title, m=message, b=[okText,cancelText], db=okText, cb=cancelText,**kwargs)
    if ret==okText:
        return promptDialog(q=1,tx=1)

def promptBoxGenerator(*args, **kwargs):
    """ Keep prompting for values until cancelled """
    while 1:
        ret = promptBox(*args, **kwargs)
        if not ret: return
        yield ret

def confirmBox(title, message, yes="Yes", no="No", *moreButtons, **kwargs):
    """ Prompt for confirmation. Returns True/False, unless 'moreButtons' were specified, and then returns the button pressed"""

    default = kwargs.get("db", kwargs.get("defaultButton")) or yes

    ret = confirmDialog(t=title,    m=message,     b=[yes,no] + list(moreButtons),
                           db=default,
                           ma="center", cb=no, ds=no)
    if moreButtons:
        return ret
    else:
        return (ret==yes)

def informBox(title, message, ok="Ok"):
    """ Information box """
    confirmDialog(t=title, m=message, b=[ok], db=ok)


class PopupError( Exception ):
    """Raise this exception in your scripts to cause a confirmDialog to be opened displaying the error message.
    After the user presses 'OK', the exception will be raised as normal. In batch mode the promptDialog is not opened.

    Parameters
    ----------
    msgOrException : str or Exception instance
        If a string, then the actual exception object returned / raised will
        be a PopupError instance, and the message displayed will be this arg;
        if an Exception instance, then the expection object returned / raised
        will be the given instance
    title : str
        title of the dialog
    button : str
        text on the confirm button of the dialog
    msg : str Or None
        If msgOrException was not an exception instance, this is ignored; if it
        is, then this controls what the displayed message is. If it is None,
        then the displayed message is the first arg of the exception instance,
        or the empty string if it has no args. If it is a string, then that will
        be the displayed message.
    icon : str
        icon to use for the confirm dialog (see confirmDialog docs for available
        icons)    
    """
    def __new__(cls, msgOrException, title='Error', button='Ok', msg=None,
                icon='critical'):
        if not isinstance(msgOrException, (basestring, Exception)):
            raise TypeError(msgOrException)
        
        if not cmds.about(batch=1):
            if not isinstance(msgOrException, Exception):
                msg = msgOrException
            elif msg is None:
                args = getattr(msgOrException, 'args', [])
                if args:
                    msg = args[0]
                else:
                    msg = ''
            confirmDialog(title=title, message=msg, button=button, icon=icon)
        if isinstance(msgOrException, Exception):
            return msgOrException
        else:
            return super(PopupError, cls).__new__(cls, msgOrException)

    def __init__(self, msg, *args, **kwargs):
        super(PopupError, self).__init__(msg)

def promptForFolder():
    """ Prompt the user for a folder path """

    # a little trick that allows us to change the top-level 'folder' variable from
    # the nested function ('getfolder') - use a single-element list, and change its content
    folder = [None]
    def getfolder(*args):
        folder[0] = args[0]
    ret = cmds.fileBrowserDialog(m=4, fc=getfolder, an="Get Folder")
    folder = _Path(folder[0])
    if folder.exists():
        return folder


def promptForPath(**kwargs):
    """ Prompt the user for a folder path """

    if cmds.about(linux=1):
        return _Path(fileDialog(**kwargs))

    else:
        # a little trick that allows us to change the top-level 'folder' variable from
        # the nested function ('getfolder') - use a single-element list, and change its content

        folder = [None]
        def getfolder(*args):
            folder[0] = args[0]

        kwargs.pop('fileCommand',None)
        kwargs['fc'] = getfolder
        
        if 'mode' not in kwargs:
            kwargs['mode'] = 0

        kwargs['an'] = kwargs.pop('an', kwargs.pop('actionName', "Select File"))
        ret = cmds.fileBrowserDialog(**kwargs)
        folder = _Path(folder[0])
        if folder: 
            #Ensure something was entered/selected. But don't test if it exists
            # as this would break mode 1/100+ causing them to return None
            return folder


def fileDialog(*args, **kwargs):
    ret = cmds.fileDialog(*args, **kwargs )
    if ret:
        return _Path( ret )

def showsHourglass(func):
    """ Decorator - shows the hourglass cursor until the function returns """
    def decoratedFunc(*args, **kwargs):
        cmds.waitCursor(st=True)
        try:
            return func(*args, **kwargs)
        finally:
            cmds.waitCursor(st=False)
    decoratedFunc.__doc__ = func.__doc__
    decoratedFunc.__name__ = func.__name__
    decoratedFunc.__module__ = func.__module__
    return decoratedFunc



def pathButtonGrp( name=None, *args, **kwargs ):
    import uitypes    
    if name is None or not cmds.textFieldButtonGrp( name, ex=1 ):
        create = True
    else:
        create = False

    return uitypes.PathButtonGrp( name=name, create=create, *args, **kwargs )

def folderButtonGrp( name=None, *args, **kwargs ):
    import uitypes    
    if name is None or not cmds.textFieldButtonGrp( name, ex=1 ):
        create = True
    else:
        create = False

    return uitypes.FolderButtonGrp( name=name, create=create, *args, **kwargs )

def vectorFieldGrp( *args, **kwargs ):
    import uitypes
    return uitypes.VectorFieldGrp( *args, **kwargs )


def uiTemplate(name=None, force=False, exists=None):
    import uitypes    
    if exists:
        return cmds.uiTemplate(name, exists=1)
    else:
        return uitypes.UITemplate(name=name, force=force)

def setParent(*args, **kwargs):
    """
Modifications
  - returns None object instead of the string 'NONE'
    """
    import uitypes    
    result = cmds.setParent(*args, **kwargs)
    if kwargs.get('query', False) or kwargs.get('q', False):
        if result == 'NONE':
            result = None
        else:
            result = uitypes.PyUI(result)
    return result

def currentParent():
    "shortcut for ``ui.PyUI(setParent(q=1))`` "
    
    return setParent(q=1)

def currentMenuParent():
    "shortcut for ``ui.PyUI(setParent(q=1, menu=1))`` "
    return setParent(q=1, menu=1)

# fix a bug it becomes impossible to create a menu after setParent has been called
def menu(*args, **kwargs):
    """
Modifications
  - added ability to query parent
    """
    if _versions.current() < _versions.v2011:
        # on create only
        if not ( kwargs.get('query', False) or kwargs.get('q', False) ) \
            and not ( kwargs.get('edit', False) or kwargs.get('e', False) ) \
            and not ( kwargs.get('parent', False) or kwargs.get('p', False) ):
            kwargs['parent'] = cmds.setParent(q=1)

    if ( kwargs.get('query', False) or kwargs.get('q', False) ) \
            and ( kwargs.get('parent', False) or kwargs.get('p', False) ):
        name = unicode(args[0])
        if '|' not in name:
            try:
                name = _findLongName(name, 'menu')
            except ValueError:
                name = _findLongName(name, 'popupMenu')
        return name.rsplit('|',1)[0]

    result = cmds.menu(*args, **kwargs)

    if ( kwargs.get('query', False) or kwargs.get('q', False) ) \
            and ( kwargs.get('itemArray', False) or kwargs.get('ia', False) ) \
            and result is None:
        result = []
    return result

def _createClassCommands():
    def createCallback( classname ):
        """
        create a callback that will trigger lazyLoading
        """
        def callback(*args, **kwargs):
            import uitypes
            res = getattr(uitypes, classname)(*args, **kwargs)
            return res
        return callback

    for funcName in _factories.uiClassList:
        # Create Class
        classname = _util.capitalize(funcName)
        #cls = _uitypes[classname]

        # Create Function
        func = _factories.functionFactory( funcName, createCallback(classname), _thisModule, uiWidget=True )
        if func:
            func.__module__ = __name__
            setattr(_thisModule, funcName, func)


def _createOtherCommands():
    moduleShortName = __name__.split('.')[-1]
    nonClassFuncs = set(_factories.moduleCmds[moduleShortName]).difference(_factories.uiClassList)
    for funcName in nonClassFuncs:
        func = _factories.functionFactory( funcName, returnFunc=None, module=_thisModule )
        if func:
            func.__module__ = __name__
            setattr(_thisModule, funcName, func)
            # want this call to work regardless of order we call _createClassCommandParis / _createCommands
            if sys.modules[__name__] != _thisModule:
                setattr( sys.modules[__name__], funcName, func )

_createClassCommands()
_createOtherCommands()

def autoLayout(*args, **kwargs):
    import uitypes
    return uitypes.AutoLayout(*args, **kwargs)

autoLayout.__doc__ = formLayout.__doc__

def subMenuItem(*args, **kwargs):
    """
    shortcut for ``menuItem(subMenu=True)``
    """
    kwargs['subMenu'] = True
    return menuItem(*args, **kwargs)


#class ValueControlGrp( UI ):
#    def __new__(cls, name=None, create=False, dataType=None, numberOfControls=1, **kwargs):
#
#        if cls._isBeingCreated(name, create, kwargs):
#            assert dataType
#            if not isinstance(dataType, basestring):
#                try:
#                    dataType = dataType.__name__
#                except AttributeError:
#                    dataType = str(dataType)
#
#            # if a dataType such as float3 or int2 was passed, get the number of ctrls
#            try:
#                numberOfControls = int(re.search( '(\d+)$', dataType ).group(0))
#            except:
#                pass
#
#            dataType = dataType.lower()
#
#            kwargs.pop('dt',None)
#            kwargs['docTag'] = dataType
##            kwargs.pop('nf', None)
##            kwargs['numberOfFields'] = 3
##            name = cmds.floatFieldGrp( name, *args, **kwargs)
#
#        #labelStr = kwargs.pop( 'label', kwargs.pop('l', str(dataType) ) )
#        if dataType in ["bool"]:
#            ctrl = _uitypes.CheckBoxGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#
#        elif dataType in ["int"]:
#            ctrl = _uitypes.IntFieldGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#
#        elif dataType in ["float"]:
#            ctrl = _uitypes.FloatFieldGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( float(default) )
#
#        elif dataType in ["vector", "Vector"]:
#            ctrl = VectorFieldGrp
#            getter = ctrl.getVector
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setVector( default )
#
#        elif dataType in ["path", "Path", "FileReference"]:# or pathreg.search( argName.lower() ):
#            ctrl = PathButtonGrp
#            getter = ctrl.getPath
#            setter = ctrl.setPath
#            #if hasDefault: ctrl.setText( default.__repr__() )
#
#        elif dataType in ["string", "unicode", "str"]:
#            ctrl = _uitypes.TextFieldGrp
#            getter = ctrl.getText
#            setter = ctrl.setText
#            #if hasDefault: ctrl.setText( str(default) )
#        else:
#             raise TypeError
##        else:
##            ctrl = _uitypes.TextFieldGrp( l=labelStr )
##            getter = makeEvalGetter( ctrl.getText )
##            #setter = ctrl.setValue1
##            #if hasDefault: ctrl.setText( default.__repr__() )
#        cls.__melcmd__ = staticmethod( ctrl.__melcmd__ )
#        self = ctrl.__new__( cls, name, create, **kwargs )
#        self.getter = getter
#        self.ctrlClass = ctrl
#        return self
#
#    def getValue(self):
#        return self.getter(self)

def valueControlGrp(name=None, create=False, dataType=None, slider=True, value=None, numberOfControls=1, **kwargs):
    """
    This function allows for a simplified interface for automatically creating UI's to control numeric values.

    A dictionary of keywords shared by all controls can be created and passed to this function and settings which don't pertain
    to the element being created will will be ignore.  For example, 'precision' will be ignored by all non-float UI and
    'sliderSteps' will be ignore by all non-slider UIs.

    :Parameters:
        dataType : string or class type
            The dataType that the UI should control.  It can be a type object or the string name of the type.
            For example for a boolean, you can specify 'bool' or pass in the bool class. Also, if the UI is meant to
            control an array, you can pass the type name as a stirng with a integer suffix representing the array length. ex. 'bool3'

        numberOfControls : int
            A parameter for specifying the number of controls per control group.  For example, for a checkBoxGrp, numberOfControls
            will map to the 'numberOfCheckBoxes' keyword.

        slider : bool
            Specify whether or not sliders should be used for int and float controls. Ignored for other
            types, as well as for int and float arrays

        value : int, int list, bool, bool list, float, float list, string, unicode, Path, Vector,
            The value for the control. If the value is for an array type, it should be a list or tuple of the appropriate
            number of elements.

    A straightforward example:

    .. python::

        settings = {}
        settings['step'] = 1
        settings['precision'] = 3
        settings['vertical'] = True # for all checkBoxGrps, lay out vertically
        win = window()
        columnLayout()
        setUITemplate( 'attributeEditorTemplate', pushTemplate=1 )
        boolCtr = valueControlGrp( dataType='bool', label='bool', **settings)
        bool3Ctr = valueControlGrp( dataType='bool', label='bool', numberOfControls=3, **settings)
        intCtr = valueControlGrp( dataType=int, label='int', slider=False, **settings)
        intSldr = valueControlGrp( dataType=int, label='int', slider=True, **settings)
        int3Ctrl= valueControlGrp( dataType=int, label='int', numberOfControls=3, **settings)
        floatCtr = valueControlGrp( dataType=float, label='float', slider=False, **settings)
        floatSldr = valueControlGrp( dataType=float, label='float', slider=True, **settings)
        pathCtrl = valueControlGrp( dataType=Path, label='path', **settings)
        win.show()


    Here's an example of how this is meant to be used in practice:

    .. python::

        settings = {}
        settings['step'] = 1
        settings['precision'] = 3
        win = window()
        columnLayout()
        types=[ ( 'donuts?',
                    bool,
                    True ),
                # bool arrays have a special label syntax that allow them to pass sub-labels
                ( [ 'flavors', ['jelly', 'sprinkles', 'glazed']],
                    'bool3',
                    [0,1,0]),
                ( 'quantity',
                  int,
                  12 ),
                ( 'delivery time',
                  float,
                  .69)
                ]
        for label, dt, val in types:
            valueControlGrp( dataType=dt, label=label, value=val, **settings)
        win.show()

    """
    import uitypes

    def makeGetter( ctrl, methodName, num ):
        def getter( ):
            res = []
            for i in range( num ):
                res.append( getattr(ctrl, methodName + str(i+1) )() )
            return res
        return getter

    def makeSetter( ctrl, methodName, num ):
        def setter( args ):
            for i in range( num ):
                getattr(ctrl, methodName + str(i+1) )(args[i])
        return setter

    # the options below are only valid for certain control types.  they can always be passed to valueControlGrp, but
    # they will be ignore if not applicable to the control for this dataType.  this allows you to create a
    # preset configuration and pass it to the valueControlGrp for every dataType -- no need for creating switches, afterall
    # that's the point of this function

    sliderArgs = [ 'sliderSteps', 'ss', 'dragCommand', 'dc' ]
    fieldArgs = [ 'field', 'f', 'fieldStep', 'fs', 'fieldMinValue', 'fmn', 'fieldMaxValue', 'fmx' ]
    fieldSliderArgs = ['step', 's', 'minValue', 'min', 'maxValue', 'max', 'extraLabel', 'el'] + sliderArgs + fieldArgs
    floatFieldArgs = ['precision', 'pre']
    verticalArgs = ['vertical', 'vr'] #checkBoxGrp and radioButtonGrp only

    if uitypes.PyUI._isBeingCreated(name, create, kwargs):
        assert dataType, "You must pass a dataType when creating a new control"
        if not isinstance(dataType, basestring):
            try:
                dataType = dataType.__name__
            except AttributeError:
                dataType = str(dataType)

        # if a dataType such as float3 or int2 was passed, get the number of ctrls
        try:
            buf = re.split( '(\d+)', dataType )
            dataType = buf[0]
            numberOfControls = int(buf[1])
        except:
            pass
    else:
        # control command lets us get basic info even when we don't know the ui type
        dataType = control( name, q=1, docTag=1)
        assert dataType

    numberOfControls = int(numberOfControls)
    if numberOfControls < 1:
        numberOfControls = 1
    elif numberOfControls > 4:
        numberOfControls = 4

    #dataType = dataType.lower()
    kwargs.pop('dt',None)
    kwargs['docTag'] = dataType

    if dataType in ["bool"]:
        if numberOfControls > 1:
            kwargs.pop('ncb', None)
            kwargs['numberOfCheckBoxes'] = numberOfControls

        # remove field/slider and float kwargs
        for arg in fieldSliderArgs + floatFieldArgs:
            kwargs.pop(arg, None)

        # special label handling
        label = kwargs.get('label', kwargs.get('l',None) )
        if label is not None:
            # allow label passing with additional sub-labels:
            #    ['mainLabel', ['subLabel1', 'subLabel2', 'subLabel3']]
            if _util.isIterable(label):
                label, labelArray = label
                kwargs.pop('l',None)
                kwargs['label'] = label
                kwargs['labelArray' + str(numberOfControls) ] = labelArray

        ctrl = uitypes.CheckBoxGrp( name, create, **kwargs )

        if numberOfControls > 1:
            getter = makeGetter(ctrl, 'getValue', numberOfControls)
            setter = makeSetter(ctrl, 'setValue', numberOfControls)
        else:
            getter = ctrl.getValue1
            setter = ctrl.setValue1
        #if hasDefault: ctrl.setValue1( int(default) )

    elif dataType in ["int"]:
        if numberOfControls > 1:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = numberOfControls
            slider = False

        if slider:
            # remove float kwargs
            for arg in floatFieldArgs + verticalArgs:
                kwargs.pop(arg, None)
            # turn the field on by default
            if 'field' not in kwargs and 'f' not in kwargs:
                kwargs['field'] = True

            ctrl = uitypes.IntSliderGrp( name, create, **kwargs )
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider and float kwargs
            for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
                kwargs.pop(arg, None)
            ctrl = uitypes.IntFieldGrp( name, create, **kwargs )

            getter = ctrl.getValue1
            setter = ctrl.setValue1
        #if hasDefault: ctrl.setValue1( int(default) )

    elif dataType in ["float"]:
        if numberOfControls > 1:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = numberOfControls
            slider = False

        if slider:
            for arg in verticalArgs:
                kwargs.pop(arg, None)

            # turn the field on by default
            if 'field' not in kwargs and 'f' not in kwargs:
                kwargs['field'] = True
            ctrl = uitypes.FloatSliderGrp( name, create, **kwargs )
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider kwargs
            for arg in fieldSliderArgs + verticalArgs:
                kwargs.pop(arg, None)
            ctrl = uitypes.FloatFieldGrp( name, create, **kwargs )
            getter = ctrl.getValue1
            setter = ctrl.setValue1
        #if hasDefault: ctrl.setValue1( float(default) )

    elif dataType in ["vector", "Vector"]:
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = VectorFieldGrp( name, create, **kwargs )
        getter = ctrl.getVector
        setter = ctrl.setValue1
        #if hasDefault: ctrl.setVector( default )

    elif dataType in ["path", "Path", "FileReference"]:# or pathreg.search( argName.lower() ):
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = PathButtonGrp( name, create, **kwargs )
        getter = ctrl.getPath
        setter = ctrl.setPath
        #if hasDefault: ctrl.setText( default.__repr__() )

    elif dataType in ["string", "unicode", "str"]:
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = uitypes.TextFieldGrp( name, create, **kwargs )
        getter = ctrl.getText
        setter = ctrl.setText
        #if hasDefault: ctrl.setText( str(default) )
    else:
        raise TypeError, "Unsupported dataType: %s" % dataType
#        else:
#            ctrl = uitypes.TextFieldGrp( l=labelStr )
#            getter = makeEvalGetter( ctrl.getText )
#            #setter = ctrl.setValue1
#            #if hasDefault: ctrl.setText( default.__repr__() )

        #new = ctrl( name, create, **kwargs )
    ctrl.getValue = getter
    ctrl.setValue = setter
    ctrl.dataType = ctrl.getDocTag

    if value is not None:
        ctrl.setValue(value)

    # TODO : remove setDocTag
    return ctrl


def getMainProgressBar():
    import uitypes
    return uitypes.ProgressBar(melGlobals['gMainProgressBar'])

# Now that we've actually created all the functions, it should be safe to import
# uitypes...
if _versions.current() >= _versions.v2011:
    from uitypes import toQtObject, toQtLayout, toQtControl, toQtMenuItem, toQtWindow
