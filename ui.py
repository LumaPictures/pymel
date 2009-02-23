"""
Functions for creating UI elements, as well as their class counterparts.

Pymel UIs
=========

pymel adds more readability to UI building while also maintaining backward compatibility.  Like nodes and 
`PyNode`s, every ui command in maya.cmds has a class counterpart in pymel derived from the base class `PyUI`.
The ui commands return these PyUI objects, and these have all of the various methods to get and set properties
on the ui element:

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
    
    

Command Callbacks
-----------------

One common point of confusion is command callbacks with ui elements. There are several different ways to handle 
command callbacks on user interface widgets:  
                        
Function Name as String
~~~~~~~~~~~~~~~~~~~~~~~

maya will try to execute this as a python command, but unless you know the namespace it will
be imported into, the function will not be recognized. notice how the namespace must be hardwired
into the command:

    >>> button( c="myCommand" )

or

    >>> button( c="myModule.myCommand" )
    
or

    >>> button ( c="import myModule; myModule.myCommand" )

Another major limitation with this method is that it is hard to pass parameters to these functions since these
have to be converted into a string representation. This becomes impractical when the parameters are complex objects,
such as dictionaries, lists, or other custom objects.

This method is not recommended.

Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is referenced by the command flag.  also, keep in mind many ui widgets such as radioButtonGrp
pass args to the function (to mimic the "myCommand #1" functionality in mel), which your function must accommodate. The
tricky part is that different ui elements pass differing numbers of args to their callbacks, and some pass none at all.
This is why it is best for your command to use the *args syntax to accept any quantity of args, and then deal with them
in the function.

    >>> def myCommand( *args ): print args # this definition must come first

    >>> button( c=myCommand )
    
                
Lambda Functions
~~~~~~~~~~~~~~~~
This is the way to handle most common command callbacks.  You can choose exactly which args you want
to pass along to your function and order of definition does not matter.

    >>> button( c= lambda *args: myCommand(args[0]) )

    >>> def myCommand( arg ): print "running", arg 


or, ignoring the arguments altogether

    
    >>> someParameter = 10
    
    >>> button( c= lambda *args: myCommand(someParameter) )

    >>> def myCommand( param ): print "running", param 


This method fails when used in a 'for' loop:

    >>> def myPrint(c): print c
    >>>
    >>> for i in range(5):
    >>>    button(label="Button %s" % i, c=lambda *args: myPrint(i))

Whichever button is pressed they will all print '4', since they all use a single 'lambda' object.


Callback Objects
~~~~~~~~~~~~~~~~
In my experience this method handles all cases reliably and predictably, and solves the 'lambda' issue described above.
A Callback object is an object that behaves like a function, meaning it can be 'called' like a regular function.
The Callback object 'wraps' another function, and also stores the parameters to pass to that function.
Here's an example:
 
    >>> def func(a,b,p): print a, b, p
    >>> func(1, p=5, b=2)    # normal invokation of the function

Here's a Callback object that creates the same effect:
    
 - first parameter is the function to wrap; the rest are parameters to that function
    >>> myCallback = Callback(func, 1, p=5, b=2)
 - Deferred evaluation of the function
    >>> myCallback()

So, when used in as a button command:

    >>> button(c=Callback(func, 1, p=5, b=2))


Here's the example from the section above, converted to use a Callback object:
    
    >>> def myPrint(c): print c
    >>>
    >>> for i in range(5):
    >>>    button(label="Button %s" % i, c=Callback(myPrint,i))



Layouts
~~~~~~~

One major pain in designing GUIs is the placing controls in layouts. 
Maya provides the formLayout command which lets controls resize and keep their relationship with other controls, however
the use of this command is somewhat combersome and unintuitive.
Pymel provides an extended FormLayout class, which handles the details of attaching controls to one another automatically:


    >>> win = window(title="My Window")
    >>> layout = formLayout()
    >>> for i in range(5):
    >>>     button(label="button %s" % i)
    >>> win.show()


The 'redistribute' method should now be used to redistributes the children (buttons in this case) evenly in their layout    
    >>> layout.redistribute()


A formLayout will align its controls vertically by default. By using the 'verticalLayout' or 'horizontalLayout' commands
you can explicitly override this (note that both commands still return a FormLayout object):

    >>> win = window(title="My Window")
    >>> layout = horizontalLayout()
    >>> for i in range(5):
    >>>     button(label="button %s" % i)
    >>> layout.redistribute()    # now will redistribute horizontally
    >>> win.show()


By default, the control are redistributed evenly but this can be overridden:

    >>> layout.redistribute(1,3,2)    # (For 5 elements, the ratios will then be 1:3:2:1:1)


You can also specify the ratios at creation time, as well as the spacing between the controls:
(A ratio of 0 (zero) means that the control will not be resized, and will keep a fixed size:)

    >>> win = window(title="My Window")
    >>> layout = horizontalLayout(ratios=[1,0,2], spacing=10)
    >>> for i in range(5):
    >>>     button(label="button %s" % i)
    >>> layout.redistribute()    # now will redistribute horizontally
    >>> win.show()
    


Finally, just for fun, you can also reset, flip and reverse the layout:

    >>> layout.flip()     # flip the orientation
    >>> layout.reverse()  # reverse the order of the controls
    >>> layout.reset()    # reset the ratios


"""


try:
    import maya.cmds as cmds
except ImportError: pass

import factories, util, core, path
Path = path.path

    
#-----------------------------------------------
#  Enhanced UI Commands
#-----------------------------------------------

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
            core.mel.eval( procCmd )
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
            core.mel.eval( procCmd )
            scriptTableCmds[key] = cc
            
            # create a scriptJob to clean up the dictionary of functions
            cmds.scriptJob(uiDeleted=(uiName, lambda *x: scriptTableCmds.pop(key,None)))
            cc = procName
        kwargs['cellChangedCmd'] = cc

    if kwargs:
        cmds.scriptTable( uiName, e=1, **kwargs)
    
    return ScriptTable(uiName)
    

class UI(unicode):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        """
        Provides the ability to create the UI Element when creating a class
        
            >>> n = pm.Window("myWindow",create=True)
            >>> n.__repr__()
            # Result: Window('myWindow')
        """
        def seekUpBases(test, cls):
            ret = test(cls)
            if ret:
                return (ret, cls)
            else:
                for superCls in cls.__bases__:
                    ret = seekUpBases(test, superCls)
                    if ret:
                        return ret
                return None

        if create:
            ret = seekUpBases(lambda cls: getattr(_thisModule, util.uncapitalize(cls.__name__), None), cls)
            if not ret:
                raise "Could not find a UI creator function for class '%s'" % cls
            createFunc = ret[0] 
            name = createFunc(name, *args, **kwargs)
        return unicode.__new__(cls,name)
    
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)
    def getChildren(self, **kwargs):
        kwargs['long'] = True
        return filter( lambda x: x.startswith(self) and not x == self, core.lsUI(**kwargs))
    def getParent(self):
        return UI( '|'.join( self.split('|')[:-1] ) )
    def type(self):
        return objectTypeUI(self)
    def shortName(self):
        return self.split('|')[-1]

# customized ui classes                            
class Window(UI):
    """pymel window class"""
    __metaclass__ = factories.metaNode                        
    def show(self):
        cmds.showWindow(self)
    def delete(self):
        cmds.deleteUI(self, window=True)
                
class FormLayout(UI):

    __metaclass__ = factories.metaNode

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
    HORIZONTAL, VERTICAL = range(2)
    sides = [["top","bottom"],["left","right"]]

    
    def __new__(cls, name=None, **kwargs):
        if not 'slc' in kwargs:
            kw = dict((k,kwargs.pop(k)) for k in ['orientation', 'ratios', 'reversed', 'spacing'] if k in kwargs)
        else:
            kw = {}
        self = UI.__new__(cls, name, **kwargs)
        kwargs.update(kw)
#        print cls
#        cls.__init__(self, name=name, **kwargs)
        return self
    
        
    def __init__(self, name=None, orientation=-1, spacing=2, reversed=False, ratios=None, **kwargs):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        UI.__init__(self, **kwargs)
        self.spacing = spacing
        self.ori = orientation
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

    def __aftercreate__(self, *args, **kwargs):
        self.redistribute()

    def redistribute(self,*ratios):
        """ Redistribute the child controls based on the given ratios.
            If not ratios are given (or not enough), 1 will be used 
            win=window()
            win.show()
            al=AutoLayout(create=1,parent=win)
            [pm.button(l=i,parent=al) for i in "yes no cancel".split()] # create 3 buttons
            al.redistribute(2,2) # First two buttons will be twice as big as the 3rd button
        """
        if self.ori not in [self.VERTICAL, self.HORIZONTAL]:
            print "Invalid orientation for %r" % self
            return
            
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

# for backwards compatiblity
AutoLayout = FormLayout

def autoLayout(*args, **kwargs):
    kw = dict((k,kwargs.pop(k)) for k in ['orientation', 'ratios', 'reversed', 'spacing'] if k in kwargs)
    ret = formLayout(*args, **kwargs)
    ret.__init__(**kw)
    return ret

def verticalLayout(*args, **kwargs):
    kwargs['orientation'] = FormLayout.VERTICAL
    return autoLayout(*args, **kwargs)

def horizontalLayout(*args, **kwargs):
    kwargs['orientation'] = FormLayout.HORIZONTAL
    return autoLayout(*args, **kwargs)


        
class FrameLayout(UI):
    __metaclass__ = factories.metaNode
    

        
class TextScrollList(UI):
    __metaclass__ = factories.metaNode
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
    __metaclass__ = factories.metaNode
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



class Callback:
    """
    Enables deferred function evaulation with 'baked' arguments.
    Useful where lambdas won't work...
    Example: 
        def addRigger(rigger):
            ...
            
        for rigger in riggers:
            pm.menuItem(
                label = "Add " + str(rigger),
                c = Callback(addRigger,rigger,p=1))   # will run: addRigger(rigger,p=1)
    """

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
        core.mel.python("__import__('pymel').Callback._doCall()")
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
    def __init__(self, name=None, uiFunc=None, kwargs=None, postFunc=None, childCreators=None):
        assert (uiFunc is None) or callable(uiFunc), uiFunc
        assert kwargs is None or isinstance(kwargs,dict), kwargs
        assert postFunc is None or callable(postFunc), postFunc
        assert childCreators is None or isinstance(childCreators,list), childCreators
        self.__dict__.update(vars())
        
    def create(self, creation=None, parent=None, debug=False, depth=0):
        """ 
        Create the ui elements defined in this SLC. 
        Named elements will be inserted into the 'creation' dictionary, which is also the return value of this function.
        The top ui element can be explicitly placed under 'parent', or implicitly under the current ui parent.
        """  
        
        if creation is None:
            creation = {}
        childCreators = self.childCreators or []
        if parent and self.uiFunc: self.kwargs["parent"] = parent
        
        if debug:
            print ">>"*depth  + "uiFunc: %s" % self.uiFunc
        self.me = self.uiFunc and self.uiFunc(**self.kwargs) or parent
        
        if self.name:
            creation[self.name] = self.me
        if debug:
            print ">>"*depth  + "result: (%s) - %s" % (self.name, self.me)

        [child.create(creation=creation,parent=self.me,debug=debug,depth=depth+1) for child in childCreators]
        
        if hasattr(self.me, "__aftercreate__"):
            self.me.__aftercreate__()
            if debug:
                print ">>"*depth + "__aftercreate__: %s" % self.me.__aftercreate__ 
        elif self.postFunc: 
            self.postFunc(self.me)
            if debug:
                print ">>"*depth + "postFunc: %s" % self.postFunc 
        return creation

SLC = SmartLayoutCreator
class SmartLayoutCreator2(SmartLayoutCreator):
    def __init__(self, func=None, name=None, childCreators=None, postFunc=None, **kwargs):
        SmartLayoutCreator.__init__(self,name,func,kwargs,postFunc,childCreators)
        
SLT = SmartLayoutCreator2


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
                           ma="center", cb="No", ds="No")
    return ret if moreButtons else (ret==yes)

def informBox(title, message, ok="Ok"):
    """ Information box """
    confirmDialog(t=title, m=message, b=["Ok"], db="Ok")
    
    
def promptForFolder():
    """ Prompt the user for a folder path """
    return promptForPath(mode=4)


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
    """This Layout Class is specifically designed to be used by the promptFromList function"""
    args = None
    selection = None
    def __new__(cls, *args, **kwargs):
        self = core.setParent(q=True)
        self = FormLayout.__new__(cls, self)
        return self
    
    def __init__(self):
        (items, prompt, ok, cancel, default, allowMultiSelection, width, height, kwargs) = _ListSelectLayout.args
        self.ams = allowMultiSelection
        self.items = list(items)
        kwargs.update(dict(dcc=self.returnSelection, allowMultiSelection=allowMultiSelection))
        SLC("topLayout", verticalLayout, dict(ratios=[0,0,1]), AutoLayout.redistribute, [
            SLC("prompt", text, dict(l=prompt)),
            SLC("selectionList", textScrollList, kwargs),
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

def promptFromList(items, title="Selector", prompt="Select from list:", ok="Select", cancel="Cancel", default=None, allowMultiSelection=False, width=None, height=None, ams=False, **kwargs):
    """ Prompt the user to select items from a list of objects """
    _ListSelectLayout.args = (items, prompt, ok, cancel, default, allowMultiSelection or ams, width, height, kwargs)
    ret = str(layoutDialog(title=title, ui="""python("import sys; sys.modules['%s']._ListSelectLayout()")""" % (__name__)))
    if ret:
        return _ListSelectLayout.selection


class TextLayout(FrameLayout):
    
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
        except:
            deleteUI(self)
            raise

    
def showsHourglass(func):
    """
    Decorator - shows the hourglass cursor until the function returns
    """
    def decoratedFunc(*args, **kwargs):
        cmds.waitCursor(st=True)
        try:
            return func(*args, **kwargs)
        finally:
            cmds.waitCursor(st=False)
    decoratedFunc.__doc__ = func.__doc__
    decoratedFunc.__name__ = func.__name__
    return decoratedFunc


_lastException = None
def announcesExceptions(title="Exception Caught", message="'%(exc)s'\nCheck script-editor for details", ignoredExecptiones=None):
    """
    Decorator - shows an information box to the user with any exception raised in a sub-routine.
    Note - the exception is re-raised.
    """
    
    if not ignoredExecptiones:
        ignoredExecptiones = tuple()
    else:
        ignoredExecptiones = tuple(ignoredExecptiones)
        
    def decoratingFunc(func):
        def decoratedFunc(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ignoredExecptiones:
                raise
            except Exception, e:
                global _lastException
                if e is _lastException:
                    return
                else:
                    _lastException = e
                import sys
                sys.excepthook(*sys.exc_info())
                informBox(title, message % dict(exc=e))
                raise
        return decoratedFunc
    return decoratingFunc

    
class MelToPythonWindow(Window):

    def __new__(cls, name=None):
        self = window(title=name or "Mel To Python")
        return Window.__new__(cls, self)

    def convert(w):
        from mel2py import mel2pyStr
        if cmds.cmdScrollFieldExecuter(w.mel,q=1,hasSelection=1):
            cmds.cmdScrollFieldExecuter(w.mel,e=1,copySelection=1)
            cmds.cmdScrollFieldExecuter(w.python,e=1,clear=1)
            cmds.cmdScrollFieldExecuter(w.python,e=1,pasteSelection=1)
            mel = cmds.cmdScrollFieldExecuter(w.python,q=1,text=1)
        else:
            mel = cmds.cmdScrollFieldExecuter(w.mel,q=1,text=1)
        try:
            py = mel2pyStr(mel)
        except Exception, e:
            confirmDialog(t="Mel To Python",m="Conversion Error:\n%s" % e,b=["Ok"], db="Ok")
        else:
            cmds.cmdScrollFieldExecuter(w.python,e=1,text=py)
    

    def __init__(self):
        SLC(None, horizontalLayout, dict(ratios=[1,.1,1]), AutoLayout.redistribute, [
              SLC("mel", cmds.cmdScrollFieldExecuter, {}),
              SLC("button", button, dict(l="->", c=lambda *x: self.convert(), bgc=[.5,.7,1])),
              SLC("python", cmds.cmdScrollFieldExecuter, dict(st="python"))
              ]).create(self.__dict__,parent=self)
        
        self.setWidthHeight([600,800])
        self.show()





_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createClassesAndFunctions():
    for funcName in factories.moduleCmds['ui']:
        classname = util.capitalize(funcName)
        if not hasattr( _thisModule, classname ):
            cls = factories.metaNode(classname, (UI,), {})
            cls.__module__ = __name__
            setattr( _thisModule, classname, cls )
        else:
            cls = getattr( _thisModule, classname )
    
        #funcName = util.uncapitalize( classname )
        func = factories.functionFactory( funcName, cls, _thisModule )
        if func:
            func.__module__ = __name__
            setattr( _thisModule, funcName, func )
        else:
            print "ui command not created", funcName
_createClassesAndFunctions()

def PyUI(strObj, type=None):
    try:
        if not type:
            type = core.objectTypeUI(strObj)
        return getattr(_thisModule, util.capitalize(type) )(strObj)
    except AttributeError:
        return UI(strObj)
    
def getMainProgressBar():
    return ProgressBar(core.getMelGlobal("string",'gMainProgressBar'))    
    
