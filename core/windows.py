"""
Functions for creating UI elements, as well as their class counterparts.

====================
Pymel UIs
====================

pymel adds more readability to UI building while also maintaining backward compatibility.  Like nodes and 
`PyNode`s, every ui command in maya.cmds has a class counterpart in pymel derived from the base class `PyUI`.
The ui commands return these PyUI objects, and these have all of the various methods to get and set properties
on the ui element:

.. python::

    from pymel import *
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
this as a python function. Here's a simple example:

.. python::

    from pymel import *

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
and prefix the function with the module it will be imported from:

.. python::

    button( command="myModule.buttonPressed" )

The problem with both of these solutions is that you must ensure that the module is *always* imported the same way, and, if you plan
to share your module with someone, it's pretty impossible to do this.
  
A more robust solution is to include an import command in the string to execute. 

.. python::
    
    button ( command="import myModule; myModule.buttonPressed" )


Another major limitation with this method is that it is hard to pass parameters to these functions since these
have to be converted into a string representation. This becomes impractical when the parameters are complex objects,
such as dictionaries, lists, or other custom objects. 

So, as simple as the string method may seem at first, it's can actually be quite a pain. Because of these limitations, 
this method is not recommended.



Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is passed to the command flag.  

.. python::

    from pymel import *
    
    def buttonPressed(arg):
        print "pressed!"

    win = window(title="My Window")
    layout = columnLayout()    
    btn = button( command=buttonPressed )
    
    showWindow()

The difference from the previous example is subtle:  ``buttonPressed`` does not have quotes around it, meaning it is not a string.

This method is very robust, its primary weakness lies in passing arguments to our function.

In the above example, we defined our callback function like this:

.. python::

    def buttonPressed(arg):
        print "pressed!"

Notice that the function has one argument: ``arg``.  We had to include this argument in our callback function because the `button` UI widget,
like many others, automatically passes arguments to your function, whether you want them or not (These forced arguments allow python in Maya
to mimic the "myCommand #1" functionality in MEL). If we had defined our function like this...

.. python::

    def buttonPressed():
        print "pressed!"
        
...when we pressed our button we would have gotten this error:

.. python::

    # TypeError: buttonPressed() takes no arguments (1 given) # 

In our case, the arguments passed by the button are actually pretty useless, but sometimes they contain the state of the UI element, such as
whether a checkbox is on or off.  The tricky part is that different UI elements pass differing numbers of arguments to their callbacks, and some
pass none at all.  This is why it is best for your command to use the ``*args`` syntax, like so:

.. python::

    def buttonPressed(*args):
        print "pressed!"
        
The asterisk in front of ``args`` allows it to accept any quantity of passed arguments. Making it a habit to use this syntax for your callbacks
can save you a lot of headache.

Now, what if I want to pass a different argument to my function besides those automatically sent by the UI element, 
or what if I'm using a function that someone else wrote and I can't add the ``*args`` to it?  Fear not, there is a solution...

                
Lambda Functions
~~~~~~~~~~~~~~~~

Combining lambda functions with the lessons we learned above adds more versatility to command callbacks.  You can choose 
exactly which args you want to pass along.

.. python::

    from pymel import *
    
    def buttonPressed(name):
        print "pressed %s!" % name

    win = window(title="My Window")
    layout = columnLayout()   
    name = 'chad' 
    btn = button( command = lambda *args: buttonPressed(name) )
    
    showWindow()

So, what exactly is a lambda?  It's a special way of creating a function on one line. It's usually used when you need a function
but you don't need to refer to it later by name.

In the above example, this portion of the code...

.. python::

    name = 'chad'
    btn = button( command = lambda *args: buttonPressed(name) )
    
...could have been written as:

.. python::

    name = 'chad'
    def tempFunc(*args):
        return buttonPressed(name)
        
    btn = button( command = tempFunc )

The lambda is just a shorthand syntax that allows us to do it on one line.  The point of the lambda is to put a function in before of the callback that
does the real work so that we can control what arguments will be passed to it.

This method, too, has a drawback. It fails when used in a 'for' loop. In the following example, we're going to make several buttons.
Our intention is that each one will print a different name, but as you will soon see, we won't succeed.

.. python::

    from pymel import *
    
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
So all the lambda's execute:

.. python::

    buttonPressed('james')

To solve this we need to "pin" down the value of our variable to keep
it from changing.  To do this, pymel provides a `Callback` object...

Callback Objects
~~~~~~~~~~~~~~~~
In my experience this method handles all cases reliably and predictably, and solves the 'lambda' issue described above.
A `Callback` object is an object that behaves like a function, meaning it can be 'called' like a regular function.
The Callback object 'wraps' another function, and also stores the parameters to pass to that function.
Here's an example:
 
.. python::

    from pymel import *
    
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



import pmcmds as cmds
#import maya.cmds as cmds


import pymel.util as util
import factories as _factories
from factories import MetaMayaUIWrapper
from system import Path
from language import mel, melGlobals
import re
import pymel.mayahook.plogging as plogging
_logger = plogging.getLogger(__name__)

#-----------------------------------------------
#  Enhanced UI Commands
#-----------------------------------------------

def lsUI( **kwargs ):
    long = kwargs.pop( 'long', kwargs.pop( 'l', False ) )
    head = kwargs.pop( 'head', kwargs.pop( 'hd', None ) )
    tail = kwargs.pop( 'tail', kwargs.pop( 'tl', None) )
    
    if not kwargs:
        kwargs = { 
            'windows': 1, 'panels' : 1, 'editors' : 1, 'controls' : 1, 'controlLayouts' : 1,
            'collection' : 1, 'radioMenuItemCollections' : 1, 'menus' : 1, 'menuItems' : 1, 'contexts' : 1, 'cmdTemplates' : 1 }
    kwargs['long'] = long
    if head is not None: kwargs['head'] = head
    if tail is not None: kwargs['tail'] = tail
    return map( PyUI, util.listForNone( cmds.lsUI( **kwargs ) ) )
   
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
                            return python("__import__('%s').scriptTableCmds['%s'](" + $row + "," + $column + ")");}
                      """ %  (procName,__name__,key) 
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
            procCmd = """global proc int %s( int $row, int $column, string $val) {
                            return python("__import__('%s').scriptTableCmds['%s'](" + $row + "," + $column + ",'" + $val + "')");}
                      """ %  (procName,__name__,key)
            mel.eval( procCmd )
            scriptTableCmds[key] = cc
            
            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key,None)))
            cc = procName
        kwargs['cellChangedCmd'] = cc

    if kwargs:
        cmds.scriptTable( uiName, e=1, **kwargs)    
    return ScriptTable(uiName)
    
def getPanel(*args, **kwargs):
    return util.listForNone( cmds.getPanel(*args, **kwargs ) )


_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly


class UI(unicode):
    def __new__(cls, name=None, create=False, **kwargs):
        """
        Provides the ability to create the UI Element when creating a class
        
            >>> n = pm.Window("myWindow",create=True)
            >>> n.__repr__()
            # Result: Window('myWindow')
        """
        slc = kwargs.pop("slc",kwargs.pop("defer",kwargs.get('childCreators')))

        if slc:
            self = unicode.__new__(cls,name)
            postFunc = kwargs.pop('postFunc',None)
            childCreators = kwargs.pop('childCreators',None)
            self.slc = SmartLayoutCreator(
                            name, 
                            cls, 
                            kwargs, postFunc, childCreators)
            self.create = self.slc.create
            return self
        else:
            if cls._isBeingCreated(name, create, kwargs):
                name = cls.__melcmd__(name, **kwargs)
                _logger.debug("UI: created... %s" % name)
            return unicode.__new__(cls,name)

    @staticmethod
    def _isBeingCreated( name, create, kwargs):
        """
        create a new node when any of these conditions occur:
           name is None
           create is True
           parent flag is set
        """
        return not name or create or kwargs.get( 'parent', kwargs.get('p', None))
        
    def exists():
        try: return cls.__melcmd__(name, ex=1)
        except: pass
        
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)
    def getChildren(self, **kwargs):
        kwargs['long'] = True
        return filter( lambda x: x.startswith(self) and not x == self, lsUI(**kwargs))
    def getParent(self):
        return UI( '|'.join( unicode(self).split('|')[:-1] ) )
    def type(self):
        return cmds.objectTypeUI(self)
    def shortName(self):
        return unicode(self).split('|')[-1]
    def name(self):
        return unicode(self)
    
    delete = _factories.functionFactory( 'deleteUI', _thisModule, rename='delete' )
    rename = _factories.functionFactory( 'renameUI', _thisModule, rename='rename' )
    type = _factories.functionFactory( 'objectTypeUI', _thisModule, rename='type' )
     
# customized ui classes                            
class Window(UI):
    """pymel window class"""
    __metaclass__ = MetaMayaUIWrapper                        
    def show(self):
        cmds.showWindow(self)
    def delete(self):
        cmds.deleteUI(self, window=True)
    def __aftercreate__(self):
        self.show()

class FormLayout(UI):
    __metaclass__ = MetaMayaUIWrapper
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
        

    """ 
    Automatically distributes child controls in either a
    horizontal or vertical layout. Call 'redistribute' once done
    adding child controls.
    """
    enumOrientation = util.enum.Enum( 'Orientation', ['HORIZONTAL', 'VERTICAL'] )
    HORIZONTAL = enumOrientation.HORIZONTAL
    VERTICAL = enumOrientation.VERTICAL
    
    def __new__(cls, name=None, **kwargs):
        if not 'slc' in kwargs:
            kw = dict((k,kwargs.pop(k)) for k in ['orientation', 'ratios', 'reversed', 'spacing'] if k in kwargs)
        else:
            kw = {}
        self = UI.__new__(cls, name, **kwargs)
        kwargs.update(kw)
        cls.__init__(self, name, **kwargs)
        return self
        

    def __init__(self, name=None, orientation='VERTICAL', spacing=2, reversed=False, ratios=None, **kwargs):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        UI.__init__(self, **kwargs)
        self.spacing = spacing
        self.ori = self.enumOrientation.getIndex(orientation)
        self.reversed = reversed
        self.ratios = ratios and list(ratios) or []
    
    def flip(self):
        """Flip the orientation of the layout """
        self.ori = 1-self.ori
        self.redistribute(*self.ratios)
    
    def reverse(self):
        """Reverse the children order """
        self.reversed = not self.reversed
        self.ratios.reverse()
        self.redistribute(*self.ratios)
        
    def reset(self):
        self.ratios = []
        self.reversed = False
        self.redistribute()
        
    sides = [["top","bottom"],["left","right"]]
    def redistribute(self,*ratios):
        """ Redistribute the child controls based on the given ratios.
            If not ratios are given (or not enough), 1 will be used 
        """
        
        children = self.getChildArray()
        if not children:
            return
        if self.reversed: children.reverse()
        
        ratios = list(ratios) or self.ratios or []
        ratios += [1]*(len(children)-len(ratios))
        self.ratios = ratios
        total = sum(ratios)       
         
        for i in range(len(children)):
            child = children[i]
            for side in self.sides[self.ori]:
                self.attachForm(child,side,self.spacing)

            if i==0:
                self.attachForm(child,
                    self.sides[1-self.ori][0],
                    self.spacing)
            else:
                self.attachControl(child,
                    self.sides[1-self.ori][0],
                    self.spacing,
                    children[i-1])
            
            if ratios[i]:
                self.attachPosition(children[i],
                    self.sides[1-self.ori][1],
                    self.spacing,
                    float(sum(ratios[:i+1]))/float(total)*100)
            else:
                self.attachNone(children[i],
                    self.sides[1-self.ori][1])
                
    def __aftercreate__(self, *args, **kwargs):
        self.redistribute()
    
    def vDistribute(self,*ratios):
        self.ori = VERTICAL.index
        self.redistribute(*ratios)
        
    def hDistribute(self,*ratios):
        self.ori = HORIZONTAL.index
        self.redistribute(*ratios)

# for backwards compatiblity
AutoLayout = FormLayout        

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



class TextScrollList(UI):
    __metaclass__ = MetaMayaUIWrapper
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

class OptionMenu(UI):
    __metaclass__ = MetaMayaUIWrapper
    def addMenuItems( self, items, title=None):
        """ Add the specified item list to the OptionMenu, with an optional 'title' item """ 
        if title:
            menuItem(l = title, en = 0,parent = self)
        for item in items:
            menuItem(l = item, parent = self)
            
    def clear(self):  
        """ Clear all menu items from this OptionMenu """
        for t in self.getItemListLong() or []:
            cmds.deleteUI(t)
    addItems = addMenuItems

       
#===============================================================================
# Provides classes and functions to facilitate UI creation in Maya
#===============================================================================


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

	# This implementation of the Callback object uses private members
	# to store static call information so that the call can be made through
	# a mel call, thus making the entire function call undoable
    _callData = None
    @staticmethod
    def _doCall():
        (func, args, kwargs) = Callback._callData
        Callback._callData = func(*args, **kwargs)

    def __init__(self,func,*args,**kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self,*args):
        Callback._callData = (self.func, self.args, self.kwargs)
        mel.python("__import__('pymel').Callback._doCall()")
        return Callback._callData    
    
class CallbackWithArgs(Callback):
    def __call__(self,*args,**kwargs):
        kwargsFinal = self.kwargs.copy()
        kwargsFinal.update(kwargs)
        Callback._callData = (self.func, self.args + args, kwargsFinal)
        mel.python("__import__('pymel').Callback._doCall()")
        return Callback._callData    
        
    



class SmartLayoutCreator:
    """
    Create a set of layouts and controls using a nested data structure.
    Example (just try it...):
    .. python::
    
        SLC = pm.SmartLayoutCreator
        
        class SLCExample:
          
            def __init__(self):
                  slc = SLC(name   = "win",                                 # name for the ui element
                            uiFunc = pm.Window,                             # callable that will create the ui element
                            kwargs = {"create":True, "title":"SLC Example"}, # keyword arguments for uiFunc
                            postFunc = pm.Window.show,                      # a callable to invoke after creating the element and its children
                            childCreators = [                               # nested ui elements, defined as further SLC objects 
                                # (non-verbose SLC declaration:)
                                SLC("layout", pm.VerticalLayout, dict(ratios=[1,1.5,2,2.5,3,3.5]), pm.VerticalLayout.redistribute,
                                    # create buttons using list comprehension:
                                    childCreators = [
                                        SLC("lbl" + str.capitalize(), pm.text, dict(al="center",l=str,bgc=[i/3.0,i/4.0,1])) 
                                            for (i,str) in enumerate("this is a dead parrot".split())
                                        ] + 
                                        [SLC("btn", pm.button, dict(l="Click Me!", c=lambda *x: self.layout.flip()))]
                                    )
                                ]
                            )
                  # create the layout, and place the named ui elements as new values in the 'creation' dictionary
                  slc.create(creation = self.__dict__)
                    
                  # now we can access ui elements via their name as designated in the SLC:  
                  self.lblYes.backgroundColor([.8,1,.8])
        
        slcEx = SLCExample()
                            
    """
    debug = False
    
    def __init__(self, name=None, uiFunc=None, kwargs=None, postFunc=None, childCreators=None):
        """
        @param name: None, or a name for this gui element. This will be the key under-which 
            the gui object will be stored in the 'creation' dictionary.
        @param uiFunc: A pointer to the function that would build this ui element.
        @param kwargs: A dictionary of arguments for the ui function.
        @param postFunc: Optional - a function that would be invoked once this ui elemnt and all of its children have been created. 
            A single argument is passed to the function which is this ui element
        @param childCreators: Optional - A list of child SLC objects that would create additional child-elements under this ui-element
            Examples: buttons within a layout, menu-items within menus, popup-menus on any other ui elements, etc.
        """  
        assert (uiFunc is None) or callable(uiFunc), uiFunc
        assert kwargs is None or isinstance(kwargs,dict), kwargs
        assert postFunc is None or callable(postFunc), postFunc
        assert childCreators is None or isinstance(childCreators,list), childCreators
        self.__dict__.update(vars())
        
    def create(self, creation=None, parent=None, debug=False):
        """ 
        Create the ui elements defined in this SLC. 
        Named elements will be inserted into the 'creation' dictionary, which is also the return value of this function.
        The top ui element can be explicitly placed under 'parent', or implicitly under the current ui parent.
        """  
        
        if creation is None:
            creation = {}
        childCreators = self.childCreators or []
        if self.kwargs is None:
            self.kwargs = dict()
        if parent and self.uiFunc: self.kwargs["parent"] = parent
        
        if (self.debug or debug) and not isinstance(debug,basestring):
            debug = "\t"
        
        if debug:
            log = debug + "> uiFunc: %r(%r)" % (self.uiFunc, self.kwargs)
        self.me = self.uiFunc and self.uiFunc(**self.kwargs) or parent
        
        if self.name:
            creation[self.name] = self.me
        if debug:
            #log += (" : %-50r" % self.me) + (" - %r" % self.name if self.name else "")
            _logger.debug(log)

        [child.create(creation=creation,parent=self.me,debug=debug and debug+"\t") for child in childCreators]
        
        if self.postFunc: 
            self.postFunc(self.me)
            if debug:
                _logger.debug(debug + "< postFunc: %s" % self.postFunc) 
        elif hasattr(self.me,'__aftercreate__'):
            self.me.__aftercreate__()
            if debug:
                _logger.debug(debug + "< postFunc: %s" % self.me.__aftercreate__) 
        return creation

SLC = SmartLayoutCreator
class SmartLayoutCreator2(SmartLayoutCreator):
    def __init__(self, uiFunc=None, name=None, childCreators=None, postFunc=None, **kwargs):
        SmartLayoutCreator.__init__(self,name, uiFunc, kwargs, postFunc, childCreators)
        
SLT = SmartLayoutCreator2
"""
SLT gives a cleaner interface to SLC. 

The arguments are the gui function, an optional access 'name', and any keyword arguments acceptable by the Maya equivalent of that function. 
Finally, the optional 'childCreators' accepts a list of additional SLTs that would be nested under the parent gui element.
As before, SLT returns a dictionary which contains the 'named' gui elements for easy access.
The 'SLT.create' method accepts a dictionary into which it will put the named elements, so this can normally be 'self.__dict__' if a gui is initialized from within a class method.
See '_ListSelectLayout' below.

Example:
        res = SLT(window, 'win', title='SLT Example', childCreators=[
            SLT(verticalLayout, ratios=[0,0,1,1,1], bgc=[.5,.5,.5], childCreators=[
                SLT(text, l='Label 1', childCreators=[
                    SLT(popupMenu, b=3, childCreators=[
                        SLT(menuItem, l='Example 1'),
                        SLT(menuItem, l='Example 2'),
                    ])
                ]),
                SLT(textField, tx="Test"),
            ] + [SLT(button, name='btn%s' % i, l='Button %s'%i) for i in "ABC"])
        ]).create()
        
        res['btnA'].backgroundColor([1,.5,.5])
        map(res['btnA'].setVisible,[0,1])
"""

def labeledControl(label, uiFunc, kwargs, align="left", parent=None, ratios=None):
    dict = SLC("layout", horizontalLayout, {"ratios":ratios}, AutoLayout.redistribute,  [
                SLC("label", text, {"l":label,"al":align}),
                SLC("control", uiFunc, kwargs)
            ]).create(parent=parent)
    control = dict["control"]
    if not isinstance(control,UI):
        control = UI(control)
    control.label = dict["label"] 
    control.layout = dict["layout"]
    return control

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


                     
def _createClassesAndFunctions():
    for funcName in _factories.uiClassList:
        
        # Create Class
        classname = util.capitalize(funcName)
        #classname = funcName[0].upper() + funcName[1:]
        if not hasattr( _thisModule, classname ):
            try:
                cls = MetaMayaUIWrapper(classname, (UI,), {})
            except AttributeError:
                _logger.warning("Could not resolve '%s' - skipping..." % classname)
            cls.__module__ = __name__
            setattr( _thisModule, classname, cls )
        else:
            cls = getattr( _thisModule, classname )
    
        # Create Function
        #funcName = util.uncapitalize( classname )
        func = _factories.functionFactory( funcName, cls, _thisModule, uiWidget=True )
        if func:
            func.__module__ = __name__
            #cls.__melcmd__ = func
            setattr( _thisModule, funcName, func )
        else:
            print "ui command not created", funcName
            
    moduleShortName = __name__.split('.')[-1]
    for funcName in _factories.moduleCmds[ moduleShortName ] :
        if funcName not in _factories.uiClassList:
            #print "bad stuff", funcName
            #func = None
            func = _factories.functionFactory( funcName, returnFunc=None, module=_thisModule )
            if func:
                func.__module__ = __name__
                setattr( _thisModule, funcName, func )
            
_createClassesAndFunctions()

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


class _ListSelectLayout(FormLayout):
    
    args = None
    selection = None
    def __new__(cls, *args, **kwargs):
        self = cmds.setParent(q=True)
        self = FormLayout.__new__(cls, self)
        return self
    
    def __init__(self, *args ,**kwargs):
        (items, prompt, ok, cancel, default, allowMultiSelection, width, height) = _ListSelectLayout.args
        self.ams = allowMultiSelection
        self.items = list(items)
        SLC("topLayout", verticalLayout, dict(ratios=[0,0,1]), AutoLayout.redistribute, [
            SLC("prompt", text, dict(l=prompt)),
            SLC("selectionList", textScrollList, dict(dcc=self.returnSelection, allowMultiSelection=allowMultiSelection)),
            SLC("buttons", horizontalLayout, dict(ratios=[1,1]), AutoLayout.redistribute, [
                SLC(None, button, dict(l=ok, c=self.returnSelection)),
                SLC(None, button, dict(l=cancel, c=Callback(layoutDialog, dismiss=""))), 
            ]),
        ]).create(parent=self, creation=self.__dict__)

        self.selectionList.append(map(str, self.items))
        if default:
            if not hasattr(default,"__iter__"):
                default = [default]
            for i in default:    
                self.selectionList.setSelectItem(str(i))
        
        width  = width  or 150
        height = height or 200
        self.setWidth(width)
        self.setHeight(height)
        for side in ["top", "right", "left", "bottom"]:
            self.attachForm(self.topLayout, side, 0)
            self.topLayout.attachNone(self.buttons, "top")
            self.topLayout.attachControl(self.selectionList, "bottom", 0, self.buttons)

        
    def returnSelection(self, *args):
        _ListSelectLayout.selection = [self.items[i-1] for i in self.selectionList.getSelectIndexedItem() or []]
        if _ListSelectLayout.selection:        
            if not self.ams:
                _ListSelectLayout.selection = _ListSelectLayout.selection[0]
            return layoutDialog(dismiss=_ListSelectLayout.selection and "True" or "")

def promptFromList(items, title="Selector", prompt="Select from list:", ok="Select", cancel="Cancel", default=None, allowMultiSelection=False, width=None, height=None, ams=False):
    """ Prompt the user to select items from a list of objects """
    _ListSelectLayout.args = (items, prompt, ok, cancel, default, allowMultiSelection or ams, width, height)
    ret = str(layoutDialog(title=title, ui="""python("import sys; sys.modules['%s']._ListSelectLayout()")""" % (__name__)))
    if ret:
        return _ListSelectLayout.selection

class TextLayout(FrameLayout):
    """A frame-layout with a textfield inside, used by the 'textWindow' function"""
    
    def __new__(cls, name=None, parent=None, text=None):
        self = frameLayout(labelVisible=bool(name), label=name or "Text Window", parent=parent)
        return FrameLayout.__new__(cls, self)

    def __init__(self, parent, text=None):
        
        SLC("topForm", verticalLayout, dict(), AutoLayout.redistribute, [
            SLC("txtInfo", scrollField, {"editable":False}),
        ]).create(self.__dict__, parent=self, debug=False)
        self.setText(text)
        
    def setText(self, text=""):
        from pprint import pformat
        if not isinstance(text, basestring):
            text = pformat(text)
        self.txtInfo.setText(text)
        self.txtInfo.setInsertionPosition(1)
        
def textWindow(title, text, size=None):

        self = window("TextWindow#",title=title)
        try:
            self.main = TextLayout(parent=self, text=text)
            self.setWidthHeight(size or [300,300])
            self.setText = self.main.setText
            self.show()
            return self
        finally:
            deleteUI(self)
    
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
        
    return PathButtonGrp( name=name, create=create, *args, **kwargs ) 

class PathButtonGrp( TextFieldButtonGrp ):
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
                f = promptForPath()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f)
            
            cb = Callback( setPathCB, name ) 
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )
            
        return TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )
        
    def setPath(self, path):
        self.setText( path )
       
    def getPath(self):
        return Path( self.getText() )
    
def vectorFieldGrp( *args, **kwargs ):
    return VectorFieldGrp( *args, **kwargs ) 
 
class VectorFieldGrp( FloatFieldGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        if create:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = 3
            name = cmds.floatFieldGrp( name, *args, **kwargs)

        return FloatFieldGrp.__new__( cls, name, create=False, *args, **kwargs )
        
    def getVector(self):
        x = floatFieldGrp( self, q=1, v1=True )
        y = floatFieldGrp( self, q=1, v2=True )
        z = floatFieldGrp( self, q=1, v3=True )
        return datatypes.Vector( [x,y,z] )
    
    def setVector(self, vec):
        floatFieldGrp( self, e=1, v1=vec[0], v2=vec[1], v3=vec[2] )
        
        return datatypes.Vector( [x,y,z] )

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
#            ctrl = CheckBoxGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#            
#        elif dataType in ["int"]:
#            ctrl = IntFieldGrp
#            getter = ctrl.getValue1
#            setter = ctrl.setValue1
#            #if hasDefault: ctrl.setValue1( int(default) )
#                
#        elif dataType in ["float"]:
#            ctrl = FloatFieldGrp
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
#            ctrl = TextFieldGrp
#            getter = ctrl.getText
#            setter = ctrl.setText
#            #if hasDefault: ctrl.setText( str(default) )
#        else:
#             raise TypeError  
##        else:
##            ctrl = TextFieldGrp( l=labelStr )
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
    
    if UI._isBeingCreated(name, create, kwargs):
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
                
        ctrl = CheckBoxGrp( name, create, **kwargs )
        
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
            
            ctrl = IntSliderGrp( name, create, **kwargs )
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider and float kwargs
            for arg in fieldSliderArgs + floatFieldArgs + verticalArgs: 
                kwargs.pop(arg, None)
            ctrl = IntFieldGrp( name, create, **kwargs )
            
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
            ctrl = FloatSliderGrp( name, create, **kwargs )
            getter = ctrl.getValue
            setter = ctrl.setValue
        else:
            # remove field/slider kwargs
            for arg in fieldSliderArgs + verticalArgs: 
                kwargs.pop(arg, None)
            ctrl = FloatFieldGrp( name, create, **kwargs )
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
        ctrl = TextFieldGrp( name, create, **kwargs )
        getter = ctrl.getText
        setter = ctrl.setText
        #if hasDefault: ctrl.setText( str(default) )
    else:
        raise TypeError, "Unsupported dataType: %s" % dataType
#        else:
#            ctrl = TextFieldGrp( l=labelStr )
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


def PyUI(strObj, type=None):
    try:
        if not type:
            type = cmds.objectTypeUI(strObj)
        return getattr(_thisModule, util.capitalize(type) )(strObj)
    except AttributeError:
        return UI(strObj)
    
def getMainProgressBar():
    return ProgressBar(melGlobals['gMainProgressBar'])    

     
