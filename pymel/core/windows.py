"""
Functions for creating UI elements, as well as their class counterparts.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from builtins import range
from builtins import str
from past.builtins import basestring
import re
import sys
import functools
import traceback

import pymel.util as _util
import pymel.internal.factories as _factories
import pymel.internal as _internal
import pymel.versions as _versions

from pymel.internal.factories import Callback, CallbackWithArgs

from pymel.core.language import mel, melGlobals
from pymel.core.system import Path as _Path

if False:
    from typing import *
    from maya import cmds
else:
    import pymel.internal.pmcmds as cmds  # type: ignore[no-redef]

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


# ----------------------------------------------
#  Enhanced UI Commands
# ----------------------------------------------

def _lsUI(**kwargs):
    long = kwargs.pop('long', kwargs.pop('l', True))
    head = kwargs.pop('head', kwargs.pop('hd', None))
    tail = kwargs.pop('tail', kwargs.pop('tl', None))

    if not kwargs:
        kwargs = {
            'windows': 1, 'panels': 1, 'editors': 1, 'controls': 1, 'controlLayouts': 1,
            'collection': 1, 'radioMenuItemCollections': 1, 'menus': 1, 'menuItems': 1,
            'contexts': 0, 'cmdTemplates': 1
        }
    kwargs['long'] = long
    if head is not None:
        kwargs['head'] = head
    if tail is not None:
        kwargs['tail'] = tail
    return _util.listForNone(cmds.lsUI(**kwargs))

# all optionMenus are popupMenus, but not all popupMenus are optionMenus
_commandsToUITypes = {
    'optionMenu': 'popupMenu',
}


def _findLongName(name, type=None):
    # this remap is currently for OptionMenu, but the fix only works in 2011
    # lsUI won't list popupMenus or optionMenus
    kwargs = {'long': True}
    if type:
        kwargs['type'] = _commandsToUITypes.get(type, type)

    uiObjs = _util.listForNone(_lsUI(**kwargs))
    res = [x for x in uiObjs if x.endswith('|' + name)]
    if len(res) > 1:
        raise ValueError("found more than one UI element matching the name %s" % name)
    elif len(res) == 0:
        raise ValueError("could not find a UI element matching the name %s" % name)
    return res[0]


def lsUI(**kwargs):
    """
Modified:
  - long defaults to True
  - if no type is passed, defaults to all known types
    """
    from . import uitypes
    return [uitypes.PyUI(x) for x in _lsUI(**kwargs)]

scriptTableCmds = {}


def scriptTable(*args, **kwargs):
    """
Maya Bug Fix:
    - fixed getCellCmd to work with python functions, previously only worked with mel callbacks
        IMPORTANT: you cannot use the print statement within the getCellCmd callback function or your values will not be returned to the table
    """
    from . import uitypes
    cb = kwargs.pop('getCellCmd', kwargs.pop('gcc', None))
    cc = kwargs.pop('cellChangedCmd', kwargs.pop('ccc', None))

    uiName = cmds.scriptTable(*args, **kwargs)
    if "q" in kwargs or "query" in kwargs:
        return uiName

    kwargs.clear()
    if cb:
        if hasattr(cb, '__call__'):
            procName = 'getCellMel%d' % len(scriptTableCmds.keys())
            key = '%s_%s' % (uiName, procName)

            procCmd = """global proc string %s( int $row, int $column ) {
                            return python(%s.scriptTableCmds['%s'](" + $row + "," + $column + ")");}
                      """ %  (procName, thisModuleCmd, key)
            mel.eval(procCmd)
            scriptTableCmds[key] = cb

            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key, None)))
            cb = procName
        kwargs['getCellCmd'] = cb
    if cc:
        if hasattr(cc, '__call__'):
            procName = 'cellChangedCmd%d' % len(scriptTableCmds.keys())
            key = '%s_%s' % (uiName, procName)
            # Note - don't do
            #     __import__('pymel.core.windows').XXX
            # ...as this will get the 'original' module, not the dynamic one!
            # Do:
            #    import pymel.core.windows; import sys; sys.modules[pymel.core.windows].XXX
            # instead!
            procCmd = """global proc int %s( int $row, int $column, string $val) {
                            return python("%s.scriptTableCmds['%s'](" + $row + "," + $column + ",'" + $val + "')");}
                      """ %  (procName, thisModuleCmd, key)
            mel.eval(procCmd)
            scriptTableCmds[key] = cc

            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key, None)))
            cc = procName
        kwargs['cellChangedCmd'] = cc

    if kwargs:
        cmds.scriptTable(uiName, e=1, **kwargs)
    return uitypes.ScriptTable(uiName)


def getPanel(*args, **kwargs):
    typeOf = kwargs.pop('typeOf', kwargs.pop('to', None))
    if typeOf:
        # typeOf flag only allows short names
        kwargs['typeOf'] = typeOf.rsplit('|', 1)[-1]
    return cmds.getPanel(*args, **kwargs)
#
#
# def textScrollList( *args, **kwargs ):
#    """
# Modifications:
#  - returns an empty list when the result is None for queries: selectIndexedItem, allItems, selectItem queries
#    """
#    res = cmds.textScrollList(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('selectIndexedItem', 'sii'), ('allItems', 'ai'), ('selectItem', 'si',)] )
#
# def optionMenu( *args, **kwargs ):
#    """
# Modifications:
#  - returns an empty list when the result is None for queries: itemListLong, itemListShort queries
#    """
#    res = cmds.optionMenu(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )
#
# def optionMenuGrp( *args, **kwargs ):
#    """
# Modifications:
#  - returns an empty list when the result is None for queries: itemlistLong, itemListShort queries
#    """
#    res = cmds.optionMenuGrp(*args, **kwargs)
#    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )
#
# def modelEditor( *args, **kwargs ):
#    """
# Modifications:
#  - casts to PyNode for queries: camera
#    """
#    res = cmds.modelEditor(*args, **kwargs)
#    if kwargs.get('query', kwargs.get('q')) and kwargs.get( 'camera', kwargs.get('cam')):
#        import pymel.core.general
#        return general.PyNode(res)
#    return res


# ==============================================================================
# Provides classes and functions to facilitate UI creation in Maya
# ==============================================================================

def verticalLayout(*args, **kwargs):
    kwargs['orientation'] = 'vertical'
    return autoLayout(*args, **kwargs)


def horizontalLayout(*args, **kwargs):
    kwargs['orientation'] = 'horizontal'
    return autoLayout(*args, **kwargs)


def promptBox(title, message, okText, cancelText, **kwargs):
    """ Prompt for a value. Returns the string value or None if cancelled """
    ret = promptDialog(t=title, m=message, b=[okText, cancelText], db=okText, cb=cancelText, **kwargs)
    if ret == okText:
        return promptDialog(q=1, tx=1)


def promptBoxGenerator(*args, **kwargs):
    """ Keep prompting for values until cancelled """
    while 1:
        ret = promptBox(*args, **kwargs)
        if not ret:
            return
        yield ret


def confirmBox(title, message, yes="Yes", no="No", *moreButtons, **kwargs):
    # type: (str, str, str, str, *str, **Any) -> Union[bool, str]
    """ Prompt for confirmation.

    Parameters
    ----------
    title : str
        The title of the confirmation window
    message : str
        The message in the body of the window
    yes : str
        The label of the first/'yes' button
    no : str
        The label of the second/'no' button
    moreButtons : str
        strings indicating the labels for buttons beyond the second
    returnButton : bool
        by default, if there are only two buttons, the return value is a boolean
        indicating whether the 'yes' button was pressed; if you wish to always
        force the label of the pressed button to be returned, set this to True
    kwargs : Any
        keyword args to pass to the underlying confirmDialog call

    Returns
    -------
    result : Union[bool, str]
        by default, if there are only two buttons, the return value is a boolean
        indicating whether the 'yes' button was pressed; otherwise, if there
        were more than two buttons or the returnButton keyword arg was set to
        True, the name of the pressed button is returned (or the dismissString,
        as explained in the docs for confirmDialog)
    """

    returnButton = kwargs.pop('returnButton', False)
    default = kwargs.get("db", kwargs.get("defaultButton")) or yes

    ret = confirmDialog(t=title, m=message, b=[yes, no] + list(moreButtons),
                        db=default,
                        ma="center", cb=no, ds=no)
    if moreButtons or returnButton:
        return ret
    else:
        return (ret == yes)


def informBox(title, message, ok="Ok"):
    """ Information box """
    confirmDialog(t=title, m=message, b=[ok], db=ok)


class PopupError(Exception):

    """Raise this exception in your scripts to cause a confirmDialog to be opened displaying the error message.
    After the user presses 'OK', the exception will be raised as normal. In batch mode the promptDialog is not opened.
    """
    def __new__(cls, msgOrException, title='Error', button='Ok', msg=None,
                icon='critical'):
        # type: (Union[str, Exception], str, str, Optional[str], str) -> PopupError
        """
        Parameters
        ----------
        msgOrException : Union[str, Exception]
            If a string, then the actual exception object returned / raised will
            be a PopupError instance, and the message displayed will be this arg;
            if an Exception instance, then the expection object returned / raised
            will be the given instance
        title : str
            title of the dialog
        button : str
            text on the confirm button of the dialog
        msg : Optional[str]
            If msgOrException was not an exception instance, this is ignored; if it
            is, then this controls what the displayed message is. If it is None,
            then the displayed message is the first arg of the exception instance,
            or the empty string if it has no args. If it is a string, then that will
            be the displayed message.
        icon : str
            icon to use for the confirm dialog (see confirmDialog docs for available
            icons)
        """
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
    ret = cmds.fileDialog2(fm=3, okc='Get Folder')
    if ret:
        folder = _Path(ret[0])
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

        kwargs.pop('fileCommand', None)
        kwargs['fc'] = getfolder

        if 'mode' not in kwargs:
            kwargs['mode'] = 0

        kwargs['an'] = kwargs.pop('an', kwargs.pop('actionName', "Select File"))
        ret = cmds.fileBrowserDialog(**kwargs)
        folder = _Path(folder[0])
        if folder:
            # Ensure something was entered/selected. But don't test if it exists
            # as this would break mode 1/100+ causing them to return None
            return folder


def fileDialog(*args, **kwargs):
    ret = cmds.fileDialog(*args, **kwargs)
    if ret:
        return _Path(ret)


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


def pathButtonGrp(name=None, *args, **kwargs):
    from . import uitypes
    if name is None or not cmds.textFieldButtonGrp(name, ex=1):
        create = True
    else:
        create = False

    return uitypes.PathButtonGrp(name=name, create=create, *args, **kwargs)


def folderButtonGrp(name=None, *args, **kwargs):
    from . import uitypes
    if name is None or not cmds.textFieldButtonGrp(name, ex=1):
        create = True
    else:
        create = False

    return uitypes.FolderButtonGrp(name=name, create=create, *args, **kwargs)


def vectorFieldGrp(*args, **kwargs):
    from . import uitypes
    return uitypes.VectorFieldGrp(*args, **kwargs)


def uiTemplate(name=None, force=False, exists=None):
    from . import uitypes
    if exists:
        return cmds.uiTemplate(name, exists=1)
    else:
        return uitypes.UITemplate(name=name, force=force)


def setParent(*args, **kwargs):
    """
Modifications
  - returns None object instead of the string 'NONE'
    """
    from . import uitypes
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
    if ( kwargs.get('query', False) or kwargs.get('q', False) ) \
            and (kwargs.get('parent', False) or kwargs.get('p', False)):
        name = str(args[0])
        if '|' not in name:
            try:
                name = _findLongName(name, 'menu')
            except ValueError:
                name = _findLongName(name, 'popupMenu')
        return name.rsplit('|', 1)[0]

    result = cmds.menu(*args, **kwargs)

    if ( kwargs.get('query', False) or kwargs.get('q', False) ) \
            and ( kwargs.get('itemArray', False) or kwargs.get('ia', False) ) \
            and result is None:
        result = []
    return result


def autoLayout(*args, **kwargs):
    from . import uitypes
    return uitypes.AutoLayout(*args, **kwargs)


def subMenuItem(*args, **kwargs):
    """
    shortcut for ``menuItem(subMenu=True)``
    """
    kwargs['subMenu'] = True
    return menuItem(*args, **kwargs)


# class ValueControlGrp( UI ):
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
# else:
##            ctrl = _uitypes.TextFieldGrp( l=labelStr )
##            getter = makeEvalGetter( ctrl.getText )
# setter = ctrl.setValue1
# if hasDefault: ctrl.setText( default.__repr__() )
#        cls.__melcmd__ = staticmethod( ctrl.__melcmd__ )
#        self = ctrl.__new__( cls, name, create, **kwargs )
#        self.getter = getter
#        self.ctrlClass = ctrl
#        return self
#
#    def getValue(self):
#        return self.getter(self)

def valueControlGrp(name=None, create=False, dataType=None, slider=True, value=None, numberOfControls=1, **kwargs):
    # type: (Any, Any, Union[str, type], bool, Union[int, bool, float, str, Path, Vector, List[Union[int, bool, float]]], int, **Any) -> None
    """
    This function allows for a simplified interface for automatically creating UI's to control numeric values.

    A dictionary of keywords shared by all controls can be created and passed to this function and settings which don't pertain
    to the element being created will will be ignore.  For example, 'precision' will be ignored by all non-float UI and
    'sliderSteps' will be ignore by all non-slider UIs.

    Parameters
    ----------
    dataType : Union[str, type]
        The dataType that the UI should control.  It can be a type object or the string name of the type.
        For example for a boolean, you can specify 'bool' or pass in the bool class. Also, if the UI is meant to
        control an array, you can pass the type name as a stirng with a integer suffix representing the array length. ex. 'bool3'
    numberOfControls : int
        A parameter for specifying the number of controls per control group.  For example, for a checkBoxGrp, numberOfControls
        will map to the 'numberOfCheckBoxes' keyword.
    slider : bool
        Specify whether or not sliders should be used for int and float controls. Ignored for other
        types, as well as for int and float arrays
    value : Union[int, bool, float, str, Path, Vector, List[Union[int, bool, float]]]
        The value for the control. If the value is for an array type, it should be a list or tuple of the appropriate
        number of elements.

    Examples
    --------
    A straightforward example::

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


    Here's an example of how this is meant to be used in practice::

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
    from . import uitypes

    def makeGetter(ctrl, methodName, num):
        def getter():
            res = []
            for i in range(num):
                res.append(getattr(ctrl, methodName + str(i + 1))())
            return res
        return getter

    def makeSetter(ctrl, methodName, num):
        def setter(args):
            for i in range(num):
                getattr(ctrl, methodName + str(i + 1))(args[i])
        return setter

    # the options below are only valid for certain control types.  they can always be passed to valueControlGrp, but
    # they will be ignore if not applicable to the control for this dataType.  this allows you to create a
    # preset configuration and pass it to the valueControlGrp for every dataType -- no need for creating switches, afterall
    # that's the point of this function

    sliderArgs = ['sliderSteps', 'ss', 'dragCommand', 'dc']
    fieldArgs = ['field', 'f', 'fieldStep', 'fs', 'fieldMinValue', 'fmn', 'fieldMaxValue', 'fmx']
    fieldSliderArgs = ['step', 's', 'minValue', 'min', 'maxValue', 'max', 'extraLabel', 'el'] + sliderArgs + fieldArgs
    floatFieldArgs = ['precision', 'pre']
    verticalArgs = ['vertical', 'vr']  # checkBoxGrp and radioButtonGrp only

    if uitypes.PyUI._isBeingCreated(name, create, kwargs):
        assert dataType, "You must pass a dataType when creating a new control"
        if not isinstance(dataType, basestring):
            try:
                dataType = dataType.__name__
            except AttributeError:
                dataType = str(dataType)

        # if a dataType such as float3 or int2 was passed, get the number of ctrls
        try:
            buf = re.split(r'(\d+)', dataType)
            dataType = buf[0]
            numberOfControls = int(buf[1])
        except:
            pass
    else:
        # control command lets us get basic info even when we don't know the ui type
        dataType = control(name, q=1, docTag=1)
        assert dataType

    numberOfControls = int(numberOfControls)
    if numberOfControls < 1:
        numberOfControls = 1
    elif numberOfControls > 4:
        numberOfControls = 4

    #dataType = dataType.lower()
    kwargs.pop('dt', None)
    kwargs['docTag'] = dataType

    if dataType in ["bool"]:
        if numberOfControls > 1:
            kwargs.pop('ncb', None)
            kwargs['numberOfCheckBoxes'] = numberOfControls

        # remove field/slider and float kwargs
        for arg in fieldSliderArgs + floatFieldArgs:
            kwargs.pop(arg, None)

        # special label handling
        label = kwargs.get('label', kwargs.get('l', None))
        if label is not None:
            # allow label passing with additional sub-labels:
            #    ['mainLabel', ['subLabel1', 'subLabel2', 'subLabel3']]
            if _util.isIterable(label):
                label, labelArray = label
                kwargs.pop('l', None)
                kwargs['label'] = label
                kwargs['labelArray' + str(numberOfControls)] = labelArray

        ctrl = uitypes.CheckBoxGrp(name, create, **kwargs)

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

            ctrl = uitypes.IntSliderGrp(name, create, **kwargs)
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider and float kwargs
            for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
                kwargs.pop(arg, None)
            ctrl = uitypes.IntFieldGrp(name, create, **kwargs)

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
            ctrl = uitypes.FloatSliderGrp(name, create, **kwargs)
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider kwargs
            for arg in fieldSliderArgs + verticalArgs:
                kwargs.pop(arg, None)
            ctrl = uitypes.FloatFieldGrp(name, create, **kwargs)
            getter = ctrl.getValue1
            setter = ctrl.setValue1
        #if hasDefault: ctrl.setValue1( float(default) )

    elif dataType in ["vector", "Vector"]:
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = VectorFieldGrp(name, create, **kwargs)
        getter = ctrl.getVector
        setter = ctrl.setValue1
        #if hasDefault: ctrl.setVector( default )

    elif dataType in ["path", "Path", "FileReference"]:  # or pathreg.search( argName.lower() ):
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = PathButtonGrp(name, create, **kwargs)
        getter = ctrl.getPath
        setter = ctrl.setPath
        #if hasDefault: ctrl.setText( default.__repr__() )

    elif dataType in ["string", "unicode", "str"]:
        # remove field/slider kwargs
        for arg in fieldSliderArgs + floatFieldArgs + verticalArgs:
            kwargs.pop(arg, None)
        ctrl = uitypes.TextFieldGrp(name, create, **kwargs)
        getter = ctrl.getText
        setter = ctrl.setText
        #if hasDefault: ctrl.setText( str(default) )
    else:
        raise TypeError("Unsupported dataType: %s" % dataType)
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
    from . import uitypes
    return uitypes.ProgressBar(melGlobals['gMainProgressBar'])

# ------ Do not edit below this line --------

@_factories.addCmdDocs
def attrColorSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrColorSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrColorSliderGrp)
    return res

@_factories.addCmdDocs
def attrControlGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrControlGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrControlGrp)
    return res

@_factories.addCmdDocs
def attrEnumOptionMenu(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrEnumOptionMenu(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrEnumOptionMenu)
    return res

@_factories.addCmdDocs
def attrEnumOptionMenuGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrEnumOptionMenuGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrEnumOptionMenuGrp)
    return res

@_factories.addCmdDocs
def attrFieldGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ebc', 'extraButtonCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrFieldGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrFieldGrp)
    return res

@_factories.addCmdDocs
def attrFieldSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ebc', 'extraButtonCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrFieldSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrFieldSliderGrp)
    return res

@_factories.addCmdDocs
def attrNavigationControlGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cad', 'ce', 'cn', 'cnd', 'connectAttrToDropped', 'connectNodeToDropped', 'connectToExisting', 'createNew', 'd', 'defaultTraversal', 'dgc', 'disconnect', 'dpc', 'dragCallback', 'dropCallback', 'dtv', 'ebc', 'extraButtonCommand', 'i', 'ignore', 'relatedNodes', 'ren', 'u', 'unignore', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attrNavigationControlGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttrNavigationControlGrp)
    return res

@_factories.addCmdDocs
def attributeMenu(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['regPulldownMenuCommand', 'rpm', 'unregPulldownMenuCommand', 'upm']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.attributeMenu(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AttributeMenu)
    return res

@_factories.addCmdDocs
def colorIndexSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.colorIndexSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ColorIndexSliderGrp)
    return res

@_factories.addCmdDocs
def colorSliderButtonGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['bc', 'buttonCommand', 'cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'sbc', 'symbolButtonCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.colorSliderButtonGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ColorSliderButtonGrp)
    return res

@_factories.addCmdDocs
def colorSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.colorSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ColorSliderGrp)
    return res

@_factories.addCmdDocs
def columnLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.columnLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ColumnLayout)
    return res

@_factories.addCmdDocs
def colorEditor(*args, **kwargs):
    from . import uitypes
    res = cmds.colorEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ColorEditor)
    return res

@_factories.addCmdDocs
def floatField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'ec', 'enterCommand', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatField)
    return res

@_factories.addCmdDocs
def floatFieldGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatFieldGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatFieldGrp)
    return res

@_factories.addCmdDocs
def floatScrollBar(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatScrollBar(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatScrollBar)
    return res

@_factories.addCmdDocs
def floatSlider(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatSlider(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatSlider)
    return res

@_factories.addCmdDocs
def floatSlider2(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc1', 'cc2', 'changeCommand1', 'changeCommand2', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatSlider2(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatSlider2)
    return res

@_factories.addCmdDocs
def floatSliderButtonGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['bc', 'buttonCommand', 'cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'sbc', 'symbolButtonCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatSliderButtonGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatSliderButtonGrp)
    return res

@_factories.addCmdDocs
def floatSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.floatSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FloatSliderGrp)
    return res

@_factories.addCmdDocs
def frameLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'collapseCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ec', 'expandCommand', 'pcc', 'pec', 'preCollapseCommand', 'preExpandCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.frameLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FrameLayout)
    return res

@_factories.addCmdDocs
def iconTextButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'commandRepeatable', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'handleNodeDropCallback', 'hnd', 'labelEditingCallback', 'lec', 'rpt', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextButton)
    return res

@_factories.addCmdDocs
def iconTextCheckBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextCheckBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextCheckBox)
    return res

@_factories.addCmdDocs
def iconTextRadioButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextRadioButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextRadioButton)
    return res

@_factories.addCmdDocs
def iconTextRadioCollection(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dcm', 'disableCommands']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextRadioCollection(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextRadioCollection)
    return res

@_factories.addCmdDocs
def iconTextScrollList(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'drc', 'dropCallback', 'dropRectCallback', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextScrollList(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextScrollList)
    return res

@_factories.addCmdDocs
def iconTextStaticLabel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.iconTextStaticLabel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IconTextStaticLabel)
    return res

@_factories.addCmdDocs
def intField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'ec', 'enterCommand', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.intField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IntField)
    return res

@_factories.addCmdDocs
def intFieldGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.intFieldGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IntFieldGrp)
    return res

@_factories.addCmdDocs
def intScrollBar(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.intScrollBar(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IntScrollBar)
    return res

@_factories.addCmdDocs
def intSlider(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.intSlider(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IntSlider)
    return res

@_factories.addCmdDocs
def intSliderGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.intSliderGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.IntSliderGrp)
    return res

@_factories.addCmdDocs
def paneLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'separatorMovedCommand', 'smc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.paneLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.PaneLayout)
    return res

@_factories.addCmdDocs
def panel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.panel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Panel)
    return res

@_factories.addCmdDocs
def radioButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.radioButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RadioButton)
    return res

@_factories.addCmdDocs
def radioButtonGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'cc1', 'cc2', 'cc3', 'cc4', 'changeCommand', 'changeCommand1', 'changeCommand2', 'changeCommand3', 'changeCommand4', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'of1', 'of2', 'of3', 'of4', 'ofc', 'offCommand', 'offCommand1', 'offCommand2', 'offCommand3', 'offCommand4', 'on1', 'on2', 'on3', 'on4', 'onCommand', 'onCommand1', 'onCommand2', 'onCommand3', 'onCommand4', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.radioButtonGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RadioButtonGrp)
    return res

@_factories.addCmdDocs
def radioCollection(*args, **kwargs):
    from . import uitypes
    res = cmds.radioCollection(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RadioCollection)
    return res

@_factories.addCmdDocs
def radioMenuItemCollection(*args, **kwargs):
    from . import uitypes
    res = cmds.radioMenuItemCollection(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RadioMenuItemCollection)
    return res

@_factories.addCmdDocs
def symbolButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.symbolButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.SymbolButton)
    return res

@_factories.addCmdDocs
def symbolCheckBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.symbolCheckBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.SymbolCheckBox)
    return res

@_factories.addCmdDocs
def textCurves(*args, **kwargs):
    from . import uitypes
    res = cmds.textCurves(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TextCurves)
    return res

@_factories.addCmdDocs
def textField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['aie', 'alwaysInvokeEnterCommandOnReturn', 'cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ec', 'enterCommand', 'receiveFocusCommand', 'rfc', 'tcc', 'textChangedCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.textField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TextField)
    return res

@_factories.addCmdDocs
def textFieldButtonGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['bc', 'buttonCommand', 'cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'fcc', 'forceChangeCommand', 'tcc', 'textChangedCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.textFieldButtonGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TextFieldButtonGrp)
    return res

@_factories.addCmdDocs
def textFieldGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'fcc', 'forceChangeCommand', 'tcc', 'textChangedCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.textFieldGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TextFieldGrp)
    return res

@_factories.addCmdDocs
def text(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'drc', 'dropCallback', 'dropRectCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.text(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Text)
    return res

@_factories.addCmdDocs
def textScrollList(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dcc', 'deleteKeyCommand', 'dgc', 'dkc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.textScrollList(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TextScrollList)
    wraps = _factories.simpleCommandWraps['textScrollList']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def toolButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.toolButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ToolButton)
    return res

@_factories.addCmdDocs
def toolCollection(*args, **kwargs):
    from . import uitypes
    res = cmds.toolCollection(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ToolCollection)
    return res

@_factories.addCmdDocs
def window(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'closeCommand', 'minimizeCommand', 'mnc', 'rc', 'restoreCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.window(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Window)
    return res

@_factories.addCmdDocs
def blendShapeEditor(*args, **kwargs):
    from . import uitypes
    res = cmds.blendShapeEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.BlendShapeEditor)
    return res

@_factories.addCmdDocs
def blendShapePanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.blendShapePanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.BlendShapePanel)
    return res

@_factories.addCmdDocs
def button(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.button(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Button)
    return res

@_factories.addCmdDocs
def checkBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ofc', 'offCommand', 'onCommand', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.checkBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CheckBox)
    return res

@_factories.addCmdDocs
def checkBoxGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'cc1', 'cc2', 'cc3', 'cc4', 'changeCommand', 'changeCommand1', 'changeCommand2', 'changeCommand3', 'changeCommand4', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'of1', 'of2', 'of3', 'of4', 'ofc', 'offCommand', 'offCommand1', 'offCommand2', 'offCommand3', 'offCommand4', 'on1', 'on2', 'on3', 'on4', 'onCommand', 'onCommand1', 'onCommand2', 'onCommand3', 'onCommand4', 'onc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.checkBoxGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CheckBoxGrp)
    return res

@_factories.addCmdDocs
def confirmDialog(*args, **kwargs):
    from . import uitypes
    res = cmds.confirmDialog(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ConfirmDialog)
    return res

@_factories.addCmdDocs
def fontDialog(*args, **kwargs):
    from . import uitypes
    res = cmds.fontDialog(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FontDialog)
    return res

@_factories.addCmdDocs
def formLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.formLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.FormLayout)
    return res

_menu = menu

@_factories.addCmdDocs
def menu(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmc', 'pmo', 'postMenuCommand', 'postMenuCommandOnce']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = _menu(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Menu)
    return res

@_factories.addCmdDocs
def menuBarLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.menuBarLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.MenuBarLayout)
    return res

@_factories.addCmdDocs
def menuEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'obc', 'optionBoxCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.menuEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.MenuEditor)
    return res

@_factories.addCmdDocs
def menuItem(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'cmd', 'command', 'commandModifier', 'ddc', 'dmc', 'dragDoubleClickCommand', 'dragMenuCommand', 'ec', 'echoCommand', 'ecr', 'enableCommandRepeat', 'pmc', 'pmo', 'postMenuCommand', 'postMenuCommandOnce', 'rtc', 'runTimeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.menuItem(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.MenuItem)
    return res

@_factories.addCmdDocs
def menuSet(*args, **kwargs):
    from . import uitypes
    res = cmds.menuSet(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.MenuSet)
    return res

@_factories.addCmdDocs
def promptDialog(*args, **kwargs):
    from . import uitypes
    res = cmds.promptDialog(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.PromptDialog)
    return res

@_factories.addCmdDocs
def scrollField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'cc', 'changeCommand', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ec', 'enterCommand', 'keyPressCommand', 'kpc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.scrollField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ScrollField)
    return res

@_factories.addCmdDocs
def scrollLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'rc', 'resizeCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.scrollLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ScrollLayout)
    return res

@_factories.addCmdDocs
def scriptedPanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.scriptedPanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ScriptedPanel)
    return res

@_factories.addCmdDocs
def scriptedPanelType(*args, **kwargs):
    from . import uitypes
    res = cmds.scriptedPanelType(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ScriptedPanelType)
    return res

@_factories.addCmdDocs
def shelfButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'commandRepeatable', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'ecr', 'enableCommandRepeat', 'handleNodeDropCallback', 'hnd', 'labelEditingCallback', 'lec', 'rpt', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shelfButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ShelfButton)
    return res

@_factories.addCmdDocs
def shelfLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shelfLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ShelfLayout)
    return res

@_factories.addCmdDocs
def shelfTabLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'closeTabCommand', 'ctc', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'newTabCommand', 'ntc', 'pmc', 'postMenuCommand', 'preSelectCommand', 'psc', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.shelfTabLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ShelfTabLayout)
    return res

@_factories.addCmdDocs
def tabLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'closeTabCommand', 'ctc', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'newTabCommand', 'ntc', 'pmc', 'postMenuCommand', 'preSelectCommand', 'psc', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.tabLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.TabLayout)
    return res

@_factories.addCmdDocs
def outlinerEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['sec', 'selectCommand', 'soc', 'sortCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.outlinerEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.OutlinerEditor)
    return res

@_factories.addCmdDocs
def optionMenu(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['acc', 'alwaysCallChangeCommand', 'beforeShowPopup', 'bsp', 'cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'pmc', 'pmo', 'postMenuCommand', 'postMenuCommandOnce', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.optionMenu(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.OptionMenu)
    wraps = _factories.simpleCommandWraps['optionMenu']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def outlinerPanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.outlinerPanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.OutlinerPanel)
    return res

@_factories.addCmdDocs
def optionMenuGrp(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'pmc', 'pmo', 'postMenuCommand', 'postMenuCommandOnce', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.optionMenuGrp(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.OptionMenuGrp)
    wraps = _factories.simpleCommandWraps['optionMenuGrp']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def animCurveEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dcc', 'denormalizeCurvesCommand', 'm', 'menu', 'ncc', 'normalizeCurvesCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.animCurveEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AnimCurveEditor)
    return res

@_factories.addCmdDocs
def animDisplay(*args, **kwargs):
    from . import uitypes
    res = cmds.animDisplay(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.AnimDisplay)
    return res

@_factories.addCmdDocs
def separator(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.separator(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Separator)
    return res

@_factories.addCmdDocs
def visor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cmd', 'command']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.visor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Visor)
    return res

@_factories.addCmdDocs
def layout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.layout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Layout)
    return res

@_factories.addCmdDocs
def layoutDialog(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ui', 'uiScript']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.layoutDialog(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.LayoutDialog)
    return res

@_factories.addCmdDocs
def layerButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'cc', 'changeCommand', 'command', 'dcc', 'dgc', 'doubleClickCommand', 'dpc', 'dragCallback', 'dropCallback', 'hideOnPlaybackCommand', 'hpc', 'rc', 'renameCommand', 'tc', 'typeCommand', 'vc', 'vcc', 'visibleChangeCommand', 'visibleCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.layerButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.LayerButton)
    return res

@_factories.addCmdDocs
def hyperGraph(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['bco', 'breakConnectionCommand', 'ddc', 'directoryPressCommand', 'dp', 'dragAndDropBehaviorCommand', 'edc', 'edd', 'edgeDblClickCommand', 'edgeDimmedDblClickCommand', 'edgeDropCommand', 'edgePressCommand', 'edgeReleaseCommand', 'edr', 'ep', 'er', 'fc', 'focusCommand', 'nco', 'ndc', 'ndr', 'nm', 'nodeConnectCommand', 'nodeDblClickCommand', 'nodeDropCommand', 'nodeMenuCommand', 'nodePressCommand', 'nodeReleaseCommand', 'np', 'nr']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hyperGraph(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.HyperGraph)
    return res

@_factories.addCmdDocs
def hyperPanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hyperPanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.HyperPanel)
    return res

@_factories.addCmdDocs
def hyperShade(*args, **kwargs):
    from . import uitypes
    res = cmds.hyperShade(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.HyperShade)
    return res

@_factories.addCmdDocs
def rowColumnLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.rowColumnLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RowColumnLayout)
    return res

@_factories.addCmdDocs
def rowLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.rowLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RowLayout)
    return res

@_factories.addCmdDocs
def renderWindowEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.renderWindowEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.RenderWindowEditor)
    return res

@_factories.addCmdDocs
def glRenderEditor(*args, **kwargs):
    from . import uitypes
    res = cmds.glRenderEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.GlRenderEditor)
    return res

_scriptTable = scriptTable

@_factories.addCmdDocs
def scriptTable(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['acc', 'afterCellChangedCmd', 'cbc', 'ccc', 'cellBackgroundColorCommand', 'cellChangedCmd', 'cellForegroundColorCommand', 'cfc', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'gcc', 'getCellCmd', 'rowsRemovedCmd', 'rowsToBeRemovedCmd', 'rrc', 'rtc', 'scc', 'selectionChangedCmd', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = _scriptTable(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ScriptTable)
    return res

@_factories.addCmdDocs
def keyframeStats(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.keyframeStats(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.KeyframeStats)
    return res

@_factories.addCmdDocs
def keyframeOutliner(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.keyframeOutliner(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.KeyframeOutliner)
    return res

@_factories.addCmdDocs
def canvas(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'pc', 'pressCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.canvas(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Canvas)
    return res

@_factories.addCmdDocs
def channelBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.channelBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ChannelBox)
    return res

@_factories.addCmdDocs
def gradientControl(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.gradientControl(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.GradientControl)
    return res

@_factories.addCmdDocs
def gradientControlNoAttr(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'ckc', 'currentKeyChanged', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.gradientControlNoAttr(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.GradientControlNoAttr)
    return res

@_factories.addCmdDocs
def gridLayout(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.gridLayout(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.GridLayout)
    return res

@_factories.addCmdDocs
def messageLine(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.messageLine(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.MessageLine)
    return res

@_factories.addCmdDocs
def popupMenu(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmc', 'pmo', 'postMenuCommand', 'postMenuCommandOnce']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.popupMenu(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.PopupMenu)
    return res

@_factories.addCmdDocs
def modelEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ec', 'editorChanged', 'obf', 'objectFilter', 'objectFilterList', 'objectFilterListUI', 'objectFilterUI', 'obu', 'ofl', 'ofu']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.modelEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ModelEditor)
    wraps = _factories.simpleCommandWraps['modelEditor']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

@_factories.addCmdDocs
def modelPanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.modelPanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ModelPanel)
    return res

@_factories.addCmdDocs
def helpLine(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.helpLine(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.HelpLine)
    return res

@_factories.addCmdDocs
def hardwareRenderPanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hardwareRenderPanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.HardwareRenderPanel)
    return res

@_factories.addCmdDocs
def image(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.image(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.Image)
    return res

@_factories.addCmdDocs
def nodeIconButton(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nodeIconButton(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.NodeIconButton)
    return res

@_factories.addCmdDocs
def commandLine(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'ec', 'enterCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.commandLine(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CommandLine)
    return res

@_factories.addCmdDocs
def progressBar(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.progressBar(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ProgressBar)
    return res

@_factories.addCmdDocs
def defaultLightListCheckBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.defaultLightListCheckBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.DefaultLightListCheckBox)
    return res

@_factories.addCmdDocs
def exclusiveLightCheckBox(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.exclusiveLightCheckBox(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ExclusiveLightCheckBox)
    return res

@_factories.addCmdDocs
def clipSchedulerOutliner(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.clipSchedulerOutliner(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ClipSchedulerOutliner)
    return res

@_factories.addCmdDocs
def clipEditor(*args, **kwargs):
    from . import uitypes
    res = cmds.clipEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.ClipEditor)
    return res

@_factories.addCmdDocs
def deviceEditor(*args, **kwargs):
    from . import uitypes
    res = cmds.deviceEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.DeviceEditor)
    return res

@_factories.addCmdDocs
def devicePanel(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pmp', 'popupMenuProcedure']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.devicePanel(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.DevicePanel)
    return res

@_factories.addCmdDocs
def dynPaintEditor(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.dynPaintEditor(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.DynPaintEditor)
    return res

@_factories.addCmdDocs
def nameField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'nameChangeCommand', 'ncc', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nameField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.NameField)
    return res

@_factories.addCmdDocs
def cmdScrollFieldExecuter(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cco', 'commandCompletion', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'fcc', 'fileChangedCommand', 'filterKeyPress', 'fkp', 'mcc', 'modificationChangedCommand', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.cmdScrollFieldExecuter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CmdScrollFieldExecuter)
    return res

@_factories.addCmdDocs
def cmdScrollFieldReporter(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'eac', 'echoAllCommands', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.cmdScrollFieldReporter(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CmdScrollFieldReporter)
    return res

@_factories.addCmdDocs
def cmdShell(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.cmdShell(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.CmdShell)
    return res

@_factories.addCmdDocs
def nameField(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'nameChangeCommand', 'ncc', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nameField(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.NameField)
    return res

@_factories.addCmdDocs
def palettePort(*args, **kwargs):
    from . import uitypes
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'ce', 'changeCommand', 'colorEdited', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.palettePort(*args, **kwargs)
    if not kwargs.get('query', kwargs.get('q', False)):
        res = _factories.maybeConvert(res, uitypes.PalettePort)
    return res

saveShelf = _factories.getCmdFunc('saveShelf')

@_factories.addCmdDocs
def runTimeCommand(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'ca', 'cl', 'command', 'commandArray', 'commandLanguage', 'dca', 'defaultCommandArray', 'nc', 'ndc', 'nuc', 'numberOfCommands', 'numberOfDefaultCommands', 'numberOfUserCommands', 'uca', 'userCommandArray']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.runTimeCommand(*args, **kwargs)
    return res

saveAllShelves = _factories.getCmdFunc('saveAllShelves')

@_factories.addCmdDocs
def soundControl(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'pc', 'pressCommand', 'rc', 'releaseCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.soundControl(*args, **kwargs)
    return res

@_factories.addCmdDocs
def flowLayout(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.flowLayout(*args, **kwargs)
    return res

toggleWindowVisibility = _factories.getCmdFunc('toggleWindowVisibility')

webBrowserPrefs = _factories.getCmdFunc('webBrowserPrefs')

thumbnailCaptureComponent = _factories.getCmdFunc('thumbnailCaptureComponent')

disableIncorrectNameWarning = _factories.getCmdFunc('disableIncorrectNameWarning')

saveViewportSettings = _factories.getCmdFunc('saveViewportSettings')

@_factories.addCmdDocs
def hotBox(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ncc', 'noClickCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hotBox(*args, **kwargs)
    return res

@_factories.addCmdDocs
def componentBox(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.componentBox(*args, **kwargs)
    return res

@_factories.addCmdDocs
def hotkeyCheck(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cmd', 'commandModifier']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hotkeyCheck(*args, **kwargs)
    return res

outputWindow = _factories.getCmdFunc('outputWindow')

@_factories.addCmdDocs
def rangeControl(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changedCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.rangeControl(*args, **kwargs)
    return res

overrideModifier = _factories.getCmdFunc('overrideModifier')

@_factories.addCmdDocs
def webBrowser(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.webBrowser(*args, **kwargs)
    return res

workspaceControlState = _factories.getCmdFunc('workspaceControlState')

spreadSheetEditor = _factories.getCmdFunc('spreadSheetEditor')

createEditor = _factories.getCmdFunc('createEditor')

@_factories.addCmdDocs
def nodeEditor(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'cnc', 'contentsChangedCommand', 'createNodeCommand', 'fc', 'fcn', 'filterCreateNodeTypes', 'focusCommand', 'keyPressCommand', 'keyReleaseCommand', 'kpc', 'krc', 'layoutCommand', 'lc', 'pms', 'popupMenuScript', 'scc', 'settingsChangedCallback', 'tabChangeCommand', 'tcc', 'toolTipCommand', 'ttc']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nodeEditor(*args, **kwargs)
    return res

@_factories.addCmdDocs
def hudSliderButton(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['bpc', 'brc', 'buttonPressCommand', 'buttonReleaseCommand', 'sdc', 'sliderDragCommand', 'sliderPressCommand', 'sliderReleaseCommand', 'spc', 'src']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hudSliderButton(*args, **kwargs)
    return res

@_factories.addCmdDocs
def hudButton(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['pc', 'pressCommand', 'rc', 'releaseCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hudButton(*args, **kwargs)
    return res

@_factories.addCmdDocs
def treeLister(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'favoritesCallback', 'fcb', 'rc', 'refreshCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.treeLister(*args, **kwargs)
    return res

objectTypeUI = _factories.getCmdFunc('objectTypeUI')

menuSetPref = _factories.getCmdFunc('menuSetPref')

setStartupMessage = _factories.getCmdFunc('setStartupMessage')

@_factories.addCmdDocs
def timeControl(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'pc', 'pressCommand', 'rc', 'releaseCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.timeControl(*args, **kwargs)
    return res

multiTouch = _factories.getCmdFunc('multiTouch')

renameUI = _factories.getCmdFunc('renameUI')

grabColor = _factories.getCmdFunc('grabColor')

connectControl = _factories.getCmdFunc('connectControl')

@_factories.addCmdDocs
def hotkey(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cmd', 'commandModifier', 'pcr', 'pressCommandRepeat', 'rcr', 'releaseCommandRepeat']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hotkey(*args, **kwargs)
    return res

windowPref = _factories.getCmdFunc('windowPref')

lsUI = _factories.addCmdDocs(lsUI)

@_factories.addCmdDocs
def colorInputWidgetGrp(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.colorInputWidgetGrp(*args, **kwargs)
    return res

canCreateCaddyManip = _factories.getCmdFunc('canCreateCaddyManip')

progressWindow = _factories.getCmdFunc('progressWindow')

@_factories.addCmdDocs
def timeField(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'ec', 'enterCommand', 'receiveFocusCommand', 'rfc', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.timeField(*args, **kwargs)
    return res

@_factories.addCmdDocs
def nameCommand(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nameCommand(*args, **kwargs)
    return res

minimizeApp = _factories.getCmdFunc('minimizeApp')

loadUI = _factories.getCmdFunc('loadUI')

refreshEditorTemplates = _factories.getCmdFunc('refreshEditorTemplates')

panelConfiguration = _factories.getCmdFunc('panelConfiguration')

@_factories.addCmdDocs
def annotate(*args, **kwargs):
    res = cmds.annotate(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['annotate']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

setUITemplate = _factories.getCmdFunc('setUITemplate')

defaultNavigation = _factories.getCmdFunc('defaultNavigation')

contentBrowser = _factories.getCmdFunc('contentBrowser')

@_factories.addCmdDocs
def nodeOutliner(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['ac', 'addCommand', 'dc', 'dc', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'mc', 'menuCommand', 'sc', 'selectCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nodeOutliner(*args, **kwargs)
    return res

@_factories.addCmdDocs
def falloffCurveAttr(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.falloffCurveAttr(*args, **kwargs)
    return res

editor = _factories.getCmdFunc('editor')

showSelectionInTitle = _factories.getCmdFunc('showSelectionInTitle')

inViewMessage = _factories.getCmdFunc('inViewMessage')

setNodeTypeFlag = _factories.getCmdFunc('setNodeTypeFlag')

buttonManip = _factories.getCmdFunc('buttonManip')

inViewEditor = _factories.getCmdFunc('inViewEditor')

editorTemplate = _factories.getCmdFunc('editorTemplate')

@_factories.addCmdDocs
def timeFieldGrp(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dc', 'dgc', 'dpc', 'dragCallback', 'dragCommand', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.timeFieldGrp(*args, **kwargs)
    return res

componentEditor = _factories.getCmdFunc('componentEditor')

@_factories.addCmdDocs
def dockControl(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'closeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'fcc', 'floatChangeCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.dockControl(*args, **kwargs)
    return res

mayaDpiSetting = _factories.getCmdFunc('mayaDpiSetting')

setFocus = _factories.getCmdFunc('setFocus')

@_factories.addCmdDocs
def headsUpDisplay(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['c', 'command']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.headsUpDisplay(*args, **kwargs)
    return res

deleteUI = _factories.getCmdFunc('deleteUI')

setMenuMode = _factories.getCmdFunc('setMenuMode')

workspacePanel = _factories.getCmdFunc('workspacePanel')

@_factories.addCmdDocs
def workspaceControl(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'closeCommand', 'ui', 'uiScript', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.workspaceControl(*args, **kwargs)
    return res

@_factories.addCmdDocs
def falloffCurve(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cc', 'changeCommand', 'dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.falloffCurve(*args, **kwargs)
    return res

panelHistory = _factories.getCmdFunc('panelHistory')

@_factories.addCmdDocs
def control(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.control(*args, **kwargs)
    return res

@_factories.addCmdDocs
def hudSlider(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dc', 'dragCommand', 'pc', 'pressCommand', 'rc', 'releaseCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hudSlider(*args, **kwargs)
    return res

savePrefObjects = _factories.getCmdFunc('savePrefObjects')

linearPrecision = _factories.getCmdFunc('linearPrecision')

@_factories.addCmdDocs
def swatchDisplayPort(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'pc', 'pressCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.swatchDisplayPort(*args, **kwargs)
    return res

hotkeySet = _factories.getCmdFunc('hotkeySet')

autoPlace = _factories.getCmdFunc('autoPlace')

dimWhen = _factories.getCmdFunc('dimWhen')

uiTemplate = _factories.addCmdDocs(uiTemplate)

savePrefs = _factories.getCmdFunc('savePrefs')

textManip = _factories.getCmdFunc('textManip')

@_factories.addCmdDocs
def nodeTreeLister(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'favoritesCallback', 'fcb', 'rc', 'refreshCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.nodeTreeLister(*args, **kwargs)
    return res

@_factories.addCmdDocs
def viewManip(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['p', 'postCommand', 'pr', 'preCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.viewManip(*args, **kwargs)
    return res

@_factories.addCmdDocs
def treeView(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['cmc', 'contextMenuCommand', 'dad', 'dc2', 'dgc', 'dpc', 'dragAndDropCommand', 'dragCallback', 'dropCallback', 'ecc', 'editLabelCommand', 'elc', 'expandCollapseCommand', 'idc', 'irc', 'itemDblClickCommand', 'itemDblClickCommand2', 'itemRenamedCommand', 'pc', 'pressCommand', 'rightPressCommand', 'rpc', 'sc', 'scc', 'selectCommand', 'selectionChangedCommand', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.treeView(*args, **kwargs)
    return res

artBuildPaintMenu = _factories.getCmdFunc('artBuildPaintMenu')

@_factories.addCmdDocs
def picture(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.picture(*args, **kwargs)
    return res

@_factories.addCmdDocs
def switchTable(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.switchTable(*args, **kwargs)
    return res

@_factories.addCmdDocs
def timePort(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.timePort(*args, **kwargs)
    return res

_getPanel = getPanel

@_factories.addCmdDocs
def getPanel(*args, **kwargs):
    res = _getPanel(*args, **kwargs)
    wraps = _factories.simpleCommandWraps['getPanel']
    for func, wrapCondition in wraps:
        if wrapCondition.eval(kwargs):
            res = func(res)
            break
    return res

loadPrefObjects = _factories.getCmdFunc('loadPrefObjects')

@_factories.addCmdDocs
def soundPopup(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.soundPopup(*args, **kwargs)
    return res

disable = _factories.getCmdFunc('disable')

scmh = _factories.getCmdFunc('scmh')

@_factories.addCmdDocs
def hotkeyEditorPanel(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.hotkeyEditorPanel(*args, **kwargs)
    return res

setParent = _factories.addCmdDocs(setParent)

scriptEditorInfo = _factories.getCmdFunc('scriptEditorInfo')

saveMenu = _factories.getCmdFunc('saveMenu')

headsUpMessage = _factories.getCmdFunc('headsUpMessage')

showWindow = _factories.getCmdFunc('showWindow')

workspaceLayoutManager = _factories.getCmdFunc('workspaceLayoutManager')

@_factories.addCmdDocs
def toolBar(*args, **kwargs):
    if len(args):
        doPassSelf = kwargs.pop('passSelf', False)
    else:
        doPassSelf = False
    for key in ['dgc', 'dpc', 'dragCallback', 'dropCallback', 'vcc', 'visibleChangeCommand']:
        try:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = _factories.makeUICallback(cb, args, doPassSelf)
        except KeyError:
            pass
    res = cmds.toolBar(*args, **kwargs)
    return res

autoLayout.__doc__ = formLayout.__doc__
