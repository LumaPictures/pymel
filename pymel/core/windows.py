"""
Functions for creating UI elements, as well as their class counterparts.
"""

"""

====================
Pymel UIs
====================

pymel adds more readability to UI building while also maintaining backward compatibility.  Like nodes and 
`PyNode`s, every ui command in maya.cmds has a class counterpart in pymel derived from the base class `PyUI`.
The ui commands return these PyUI objects, and these have all of the various methods to get and set properties
on the ui element::

    from pymel.all import *
    win = window(title="My Window")
    layout = columnLayout()
    chkBox = checkBox(label = "My Checkbox", value=True, parent=layout)
    btn = button(label="My Button", parent=layout)
    def buttonPressed(*args):
        if chkBox.getValue():
            print "Check box is CHECKED!"
            btn.setLabel("Uncheck")
        else:
            print "Check box is UNCHECKED!"
            btn.setLabel("Check")
    btn.setCommand(buttonPressed)
    win.show()
    
    
----------------------------------
Command Callbacks
----------------------------------


One common point of confusion when building UIs with python is command callbacks. There are several different ways to handle 
command callbacks on user interface widgets.
                        
Function Name as String
~~~~~~~~~~~~~~~~~~~~~~~

The simplest method of setting up a callback is to pass the name of the callback function as a string. Maya will try to execute 
this as a python function. Here's a simple example::

    from pymel.all import *

    def buttonPressed(arg):
        print "pressed!"
        
    win = window(title="My Window")
    layout = columnLayout()
    btn = button( command='buttonPressed' )
        
    showWindow()

This example works fine if you run it from the script editor, but if you save it into a module, say ``myModule``, and then import that
module as normal ( e.g. ``import myModule`` ), it will cease to work (assuming you haven't already run it from the script edtior).  
This is because the *namespace* of the function has changed. It can no longer be found as ``buttonPressed``, because from 
Maya's perspective, its new location is ``myModule.buttonPressed``.

There are several solutions to this.  First, you can import the contents of ``myModule`` directly into the main namespace ( e.g. 
``from myModule import *`` ). This will allow ``buttonPressed`` to be accessed without the namespace. Alterately, you can change your script 
and prefix the function with the module it will be imported from::

    button( command="myModule.buttonPressed" )

The problem with both of these solutions is that you must ensure that the module is *always* imported the same way, and, if you plan
to share your module with someone, it's pretty impossible to do this.
  
A more robust solution is to include an import command in the string to execute::
    
    button ( command="import myModule; myModule.buttonPressed" )


Another major limitation with this method is that it is hard to pass parameters to these functions since these
have to be converted into a string representation. This becomes impractical when the parameters are complex objects,
such as dictionaries, lists, or other custom objects. 

So, as simple as the string method may seem at first, it's can actually be quite a pain. Because of these limitations, 
this method is not recommended.



Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is passed to the command flag::

    from pymel.all import *
    
    def buttonPressed(arg):
        print "pressed!"

    win = window(title="My Window")
    layout = columnLayout()    
    btn = button( command=buttonPressed )
    
    showWindow()

The difference from the previous example is subtle:  ``buttonPressed`` does not have quotes around it, meaning it is not a string.

This method is very robust, its primary weakness lies in passing arguments to our function.

In the above example, we defined our callback function like this::

    def buttonPressed(arg):
        print "pressed!"

Notice that the function has one argument: ``arg``.  We had to include this argument in our callback function because the `button` UI widget,
like many others, automatically passes arguments to your function, whether you want them or not (These forced arguments allow python in Maya
to mimic the "myCommand #1" functionality in MEL). If we had defined our function like this::

    def buttonPressed():
        print "pressed!"
        
...when we pressed our button we would have gotten this error::

    # TypeError: buttonPressed() takes no arguments (1 given) # 

In our case, the arguments passed by the button are actually pretty useless, but sometimes they contain the state of the UI element, such as
whether a checkbox is on or off.  The tricky part is that different UI elements pass differing numbers of arguments to their callbacks, and some
pass none at all.  This is why it is best for your command to use the ``*args`` syntax, like so::

    def buttonPressed(*args):
        print "pressed!"
        
The asterisk in front of ``args`` allows it to accept any quantity of passed arguments. Making it a habit to use this syntax for your callbacks
can save you a lot of headache.

Now, what if I want to pass a different argument to my function besides those automatically sent by the UI element, 
or what if I'm using a function that someone else wrote and I can't add the ``*args`` to it?  Fear not, there is a solution...

                
Lambda Functions
~~~~~~~~~~~~~~~~

Combining lambda functions with the lessons we learned above adds more versatility to command callbacks.  You can choose 
exactly which args you want to pass along::

    from pymel.all import *
    
    def buttonPressed(name):
        print "pressed %s!" % name

    win = window(title="My Window")
    layout = columnLayout()   
    name = 'chad' 
    btn = button( command = lambda *args: buttonPressed(name) )
    
    showWindow()

So, what exactly is a lambda?  It's a special way of creating a function on one line. It's usually used when you need a function
but you don't need to refer to it later by name.

In the above example, this portion of the code::

    name = 'chad'
    btn = button( command = lambda *args: buttonPressed(name) )
    
...could have been written as::

    name = 'chad'
    def tempFunc(*args):
        return buttonPressed(name)
        
    btn = button( command = tempFunc )

The lambda is just a shorthand syntax that allows us to do it on one line.  The point of the lambda is to put a function in before of the callback that
does the real work so that we can control what arguments will be passed to it.

This method, too, has a drawback. It fails when used in a 'for' loop. In the following example, we're going to make several buttons.
Our intention is that each one will print a different name, but as you will soon see, we won't succeed::

    from pymel.all import *
    
    def buttonPressed(name):
        print "pressed %s!" % name

    win = window(title="My Window")
    layout = columnLayout()   
    names = [ 'chad', 'robert', 'james' ]
    for character in names:
        button( label=name, command = lambda *args: buttonPressed(character) )
    
    showWindow()

When pressed, all the buttons will print 'james'. Why is this?   Think of a lambda as
a "live" or dynamic object.  It lives there waiting to execute the
code it has been given, but the variables in that code are live too, so the value of
the variable named ``character`` changes with each
iteration through the loop, thereby changing the code that lambda is
waiting to execute.  What is its value at the end of the loop?  It's 'james'.
So all the lambda's execute::

    buttonPressed('james')

To solve this we need to "pin" down the value of our variable to keep
it from changing.  To do this, pymel provides a `Callback` object...

Callback Objects
~~~~~~~~~~~~~~~~
In my experience this method handles all cases reliably and predictably, and solves the 'lambda' issue described above.
A `Callback` object is an object that behaves like a function, meaning it can be 'called' like a regular function.
The Callback object 'wraps' another function, and also stores the parameters to pass to that function.
Here's an example::

    from pymel.all import *
    
    def buttonPressed(name):
        print "pressed %s!" % name

    win = window(title="My Window")
    layout = columnLayout()   
    names = [ 'chad', 'robert', 'james' ]
    for character in names:
        button( label=name, command = Callback( buttonPressed, character )
    
    showWindow()

Our example now works as intended.  The `Callback` class provides the magic that makes it work. Pay close attention to 
how the Callback is created:  first parameter is the function to wrap, 
the ``buttonPressed`` function, and the rest are parameters to that function, in our case ``character``.  The Callback stores the
function and its arguments and then combines them when it is called by the UI element.  The `Callback` class ignores any arguments
passed in from the UI element, so you don't have to design your function to take these into account.  However, if you do want these, 
use the alternate callback object `CallbackWithArgs`: the additional
arguments will be added to the end of yours.


----------------------------------
Layouts
----------------------------------

One major pain in designing GUIs is the placing controls in layouts. 
Maya provides the formLayout command which lets controls resize and keep their relationship with other controls, however
the use of this command is somewhat combersome and unintuitive.
Pymel provides an extended FormLayout class, which handles the details of attaching controls to one another automatically:


    >>> win = window(title="My Window")
    >>> layout = formLayout()
    >>> for i in range(5):
    ...     button(label="button %s" % i)
    >>> win.show()


The 'redistribute' method should now be used to redistributes the children (buttons in this case) evenly in their layout    
    >>> layout.redistribute()


A formLayout will align its controls vertically by default. By using the 'verticalLayout' or 'horizontalLayout' commands
you can explicitly override this (note that both commands still return a FormLayout object):

    >>> win = window(title="My Window")
    >>> layout = horizontalLayout()
    >>> for i in range(5):
    ...     button(label="button %s" % i)
    >>> layout.redistribute()    # now will redistribute horizontally
    >>> win.show()


By default, the control are redistributed evenly but this can be overridden:

    >>> layout.redistribute(1,3,2)    # (For 5 elements, the ratios will then be 1:3:2:1:1)


You can also specify the ratios at creation time, as well as the spacing between the controls:
(A ratio of 0 (zero) means that the control will not be resized, and will keep a fixed size:)

    >>> win = window(title="My Window")
    >>> layout = horizontalLayout(ratios=[1,0,2], spacing=10)
    >>> for i in range(5):
    ...     button(label="button %s" % i)
    >>> layout.redistribute()    # now will redistribute horizontally
    >>> win.show()
    


Finally, just for fun, you can also reset, flip and reverse the layout:

    >>> layout.flip()     # flip the orientation
    >>> layout.reverse()  # reverse the order of the controls
    >>> layout.reset()    # reset the ratios


"""


import re, sys
import pmcmds as cmds
import pymel.util as util
import factories as _factories
from factories import MetaMayaUIWrapper
from system import Path
from language import mel, melGlobals
import pymel.mayahook.plogging as plogging
import uitypes
from pymel import version

_logger = plogging.getLogger(__name__)

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
            'contexts' : 1, 'cmdTemplates' : 1 
            }
    kwargs['long'] = long
    if head is not None: kwargs['head'] = head
    if tail is not None: kwargs['tail'] = tail
    return util.listForNone(cmds.lsUI(**kwargs))

def lsUI( **kwargs ):
    """
Modified:
  - long defaults to True
  - if no type is passed, defaults to all known types
    """
    return [ uitypes.PyUI(x) for x in _lsUI( **kwargs ) ]
   
scriptTableCmds = {}

def scriptTable(*args, **kwargs):
    """
Maya Bug Fix:
    - fixed getCellCmd to work with python functions, previously only worked with mel callbacks
        IMPORTANT: you cannot use the print statement within the getCellCmd callback function or your values will not be returned to the table
    """
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
    return util.listForNone( cmds.getPanel(*args, **kwargs ) )


def textScrollList( *args, **kwargs ):
    res = cmds.textScrollList(*args, **kwargs)
    return _factories.listForNoneQuery( res, kwargs, [('selectIndexedItem', 'sii'), ('allItems', 'ai'), ('selectItem', 'si',)] )

def optionMenu( *args, **kwargs ):
    res = cmds.optionMenu(*args, **kwargs)
    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )

def optionMenuGrp( *args, **kwargs ):
    res = cmds.optionMenuGrp(*args, **kwargs)
    return _factories.listForNoneQuery( res, kwargs, [('itemListLong', 'ill'), ('itemListShort', 'ils')] )

#===============================================================================
# Provides classes and functions to facilitate UI creation in Maya
#===============================================================================

class CallbackError(Exception): pass

if version.CURRENT >= version.v2009:

    class Callback(object):
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
    
        def __init__(self,func,*args,**kwargs):
            self.func = func
            self.args = args
            self.kwargs = kwargs
        
        def __call__(self,*args):
            cmds.undoInfo(openChunk=1)
            try:
                return self.func(*self.args, **self.kwargs)
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
                return self.func(*self.args + args, **self.kwargsFinal)
            finally:
                cmds.undoInfo(closeChunk=1)
else:
    
    class Callback(object):
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
    
        def __init__(self,func,*args,**kwargs):
            self.func = func
            self.args = args
            self.kwargs = kwargs
            
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
                raise CallbackError('Error during callback: %s\n_callData: %r' % (e, Callback._callData))
            return Callback._callData
        
    class CallbackWithArgs(Callback):
        def __call__(self,*args,**kwargs):
            kwargsFinal = self.kwargs.copy()
            kwargsFinal.update(kwargs)
            Callback._callData = (self.func, self.args + args, kwargsFinal)
            try:
                mel.python("%s.Callback._doCall()" % thisModuleCmd)
            except Exception, e:
                raise CallbackError('Error during callback: %s\n_callData: %r' % (e, Callback._callData))
            return Callback._callData
        
    
def autoLayout(*args, **kwargs):
    kw = dict((k,kwargs.pop(k)) for k in ['orientation', 'ratios', 'reversed', 'spacing'] if k in kwargs)
    ret = formLayout(*args, **kwargs)
    ret.__init__(**kw)
    return ret

def verticalLayout(*args, **kwargs):
    kwargs['orientation'] = 'VERTICAL'
    return autoLayout(*args, **kwargs)

def horizontalLayout(*args, **kwargs):
    kwargs['orientation'] = 'HORIZONTAL'
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
    confirmDialog(t=title, m=message, b=["Ok"], db="Ok")
    

class PopupError( Exception ): 
    """Raise this exception in your scripts to cause a promptDialog to be opened displaying the error message.
    After the user presses 'OK', the exception will be raised as normal. In batch mode the promptDialog is not opened."""
    
    def __init__(self, msg):
        Exception.__init__(self, msg)
        if not cmds.about(batch=1):
            ret = informBox('Error', msg)


def promptForFolder():
    """ Prompt the user for a folder path """
    
    # a little trick that allows us to change the top-level 'folder' variable from 
    # the nested function ('getfolder') - use a single-element list, and change its content
    folder = [None]
    def getfolder(*args):
        folder[0] = args[0]
    ret = cmds.fileBrowserDialog(m=4, fc=getfolder, an="Get Folder")
    folder = Path(folder[0])
    if folder.exists():
        return folder

       
def promptForPath(**kwargs):
    """ Prompt the user for a folder path """
    
    if cmds.about(linux=1):
        return Path(fileDialog(**kwargs))
    
    else:
        # a little trick that allows us to change the top-level 'folder' variable from 
        # the nested function ('getfolder') - use a single-element list, and change its content
        
        folder = [None]
        def getfolder(*args):
            folder[0] = args[0]
        
        kwargs.pop('fileCommand',None)
        kwargs['fc'] = getfolder
        
        kwargs['an'] = kwargs.pop('an', kwargs.pop('actionName', "Select File"))
        ret = cmds.fileBrowserDialog(**kwargs)
        folder = Path(folder[0])
        if folder.exists():
            return folder        
        
    
def fileDialog(*args, **kwargs):
    ret = cmds.fileDialog(*args, **kwargs )
    if ret:
        return Path( ret )

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
    if name is None or not cmds.textFieldButtonGrp( name, ex=1 ):
        create = True
    else:
        create = False
        
    return uitypes.PathButtonGrp( name=name, create=create, *args, **kwargs ) 
 
def vectorFieldGrp( *args, **kwargs ):
    return uitypes.VectorFieldGrp( *args, **kwargs ) 
 

def _createClassCommands():
    
    
    def createCallback( classname ):
        def callback(*args, **kwargs):
            #print "creating ui element", classname
            return getattr(uitypes, classname)(*args, **kwargs)
        return callback
     
    for funcName in _factories.uiClassList:
        # Create Class
        classname = util.capitalize(funcName)
        #cls = uitypes[classname]
    
        # Create Function
        func = _factories.functionFactory( funcName, createCallback(classname), _thisModule, uiWidget=True )
        if func:
            func.__module__ = __name__
            # Since we're not using LazyLoading objects for funcs, add them
            # to both the dynamic module and this module, so we don't have
            # preface them with 'uitypes.' when referencing from this module
            setattr(uitypes, funcName, func)
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
#            ctrl = uitypes.CheckBoxGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#            
#        elif dataType in ["int"]:
#            ctrl = uitypes.IntFieldGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#                
#        elif dataType in ["float"]:
#            ctrl = uitypes.FloatFieldGrp
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
#            ctrl = uitypes.TextFieldGrp
#            getter = ctrl.getText
#            setter = ctrl.setText
#            #if hasDefault: ctrl.setText( str(default) )
#        else:
#             raise TypeError  
##        else:
##            ctrl = uitypes.TextFieldGrp( l=labelStr )
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
    
    if uitypes.UI._isBeingCreated(name, create, kwargs):
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
            if util.isIterable(label):
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
    return uitypes.ProgressBar(melGlobals['gMainProgressBar'])    

  
