
.. currentmodule:: pymel.core.windows

==========================
Building User Interfaces
==========================

As with Maya nodes, pymel adds the ability to use object-oriented code for building MEL GUIs. Like nodes and 
PyNodes, every UI command in maya.cmds has a class counterpart in pymel derived from the base class `PyUI <pymel.core.uitypes.PyUI>`.
There is one class for every UI element type, each with necessary methods to get and set properties.  And as with nodes,
the procedural commands you already know and love are retrofitted to return `PyUI <pymel.core.uitypes.PyUI>` classes, so you don't have to completely change the way you code ::


    from pymel.core import *
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

The simplest method of setting up a callback is to pass the name of the callback function as a string. Maya will try to execute this as python code. Here's a simple example::


	from pymel.core import *

	def buttonPressed():
	    print "pressed!"

	win = window(title="My Window")
	layout = columnLayout()
	btn = button( command='buttonPressed()' )

	showWindow()

This example works fine if you run it from the script editor, but if you save it into a module, say ``myModule``, and then import that module as normal ( e.g. ``import myModule`` ), it will cease to work (assuming you haven't already run it from the script edtior).  This is because the *namespace* of the ``buttonPressed`` function has changed. It can no longer be found as ``buttonPressed``, because from Maya's perspective, its new location is ``myModule.buttonPressed``.

There are several solutions to this. 

	1. you can import the contents of ``myModule`` directly into the main namespace ( e.g. ``from myModule import *`` ). This will allow ``buttonPressed`` to be accessed without the namespace. This is not generally recommended as its clutters up your main namespace which could ultimately lead to name clashes.
	2. you can change your script and prefix the function with the module it will be imported from::

   		button( command="myModule.buttonPressed()" )

The problem with both of these solutions is that you must ensure that the module is *always* imported the same way, and, if you plan to share your module with someone, it's pretty impossible to do this.
  
A more robust solution is to include an import command in the string to execute::

    button( command="import myModule; myModule.buttonPressed()" )

That gives us a fairly reliable solution, but it still has one major drawback: any parameters that we wish to pass to our function must also be converted to strings. This becomes impractical when the parameters are complex objects,
such as dictionaries, lists, or other custom objects. 

So, while string callbacks may seem simple at first, they have limitations, and are generally not recommended.


Function Object
~~~~~~~~~~~~~~~  

When using this technique, you pass an actual function object instead of a string. ::

    from pymel.core import *
    
    def buttonPressed():
        print "pressed!"

    win = window(title="My Window")
    layout = columnLayout()    
    btn = button(command=buttonPressed)
    
    showWindow()

.. note::  The callback function has to be defined before it is passed to the command flag.


The difference from the previous example is subtle: ``command="buttonPressed()"`` is now ``command=buttonPressed``. The most important thing to realize here is that ``buttonPressed`` is not a string, it is a python function object. As such, if we had included ``()`` ( e.g. ``command=buttonPressed()`` ) we would have executed the ``buttonPressed`` function immediately, but we don't want that to happen yet. By leaving the parentheses off, we hand the function over to the UI element to execute later.  For most commands that support callbacks, Maya recognizes when you are passing a string and when you are passing a function, and it treats each differently when the callback is triggered.

This method is very robust, but there are a few caveats to be aware of.  To see what I mean, try executing the code above and pressing the button...

...when we press it, we get this error::

    # TypeError: buttonPressed() takes no arguments (1 given) # 

Why?! The `button` UI widget, like many others, automatically passes arguments to your function, whether you want them or not. Sometimes these arguments contain the state of the UI element, such as whether a checkbox is on or off, but in our case they are pretty useless.

.. note:: 
	The automatic passing of arguments to python callbacks is an attempt to recreate a feature of MEL. When creating callbacks in MEL you can request that your callback procedure be passed an argument when the callback is triggered.  Take the example below::

		radioButton -changeCommand "myRadButtCB #1";
		
	When the callback is executed, the ``#1`` gets replaced with the current state of the radioButton: ``0`` or ``1``.  Unfortunately, when using python callbacks, you can't request which arguments you want, you get them all.

So, to make our callback work, we need to modify the function to accept the argument that the button ``command`` callback is passing us::

    def buttonPressed(arg):
        print "pressed!"

The tricky part is that different UI elements pass differing numbers of arguments to their callbacks, and some pass none at all.  This is why it is best for your command to use the ``*args`` syntax, like so::

    def buttonPressed(*args):
        print "pressed! here are my arguments %s" % ( args, )
        
The asterisk in front of ``args`` allows the function to accept any quantity of passed arguments. All of the positional arguments to the function are stored in the variable ``args`` (without the ``*``) as a read-only list, known as a tuple. Making it a habit to use this syntax for your callbacks can save you a lot of headache.

Putting it all together::

    from pymel.core import *
    
    def buttonPressed(*args):
        print "pressed!"

    win = window(title="My Window")
    layout = columnLayout()    
    btn = button( command=buttonPressed )
    
    showWindow()


                
Lambda Functions
~~~~~~~~~~~~~~~~

The next technique builds on the last by simplifying the following situations:

	- You want to pass arguments to your callback function other than those automatically sent by the UI element
	- You're using a function that someone else wrote and can't add the ``*args`` to it 
	
For example, I want to pass our ``buttonPressed`` function a name argument.  Here's how we do this using a lambda function::

    from pymel.core import *
    
    def buttonPressed(name):
        print "pressed %s!" % name

    win = window(title="My Window")
    layout = columnLayout()   
    btn = button( command = lambda *args: buttonPressed('chad') )
    
    showWindow()

So, what exactly is a `lambda <http://docs.python.org/reference/expressions.html#lambda>`_?  It's a shorthand way of creating a simple function on one line. It's usually used when you need a function but you don't need to refer to it later by name, which makes it well suited for callbacks. Combining lambda functions with the lessons we learned above adds more versatility to command callbacks.  You can choose exactly which args you want to pass along. 

Let's clarify what a lambda is. In the above example, this portion of the code... ::

    lambda *args: buttonPressed('chad')
    
...could have been written as::

    def tempFunc(*args):
        return buttonPressed('chad')

We would have then passed ``tempFunc`` as the callback::

	btn = button( command = tempFunc )

Instead, we use the lambda to create the function on one line and pass it directly to the ``command`` flag. ::

	btn = button( command = lambda *args: buttonPressed('chad') )

.. The lambda has two parts, the argument definition to the left of the colon, ``lambda *args``, and the expression to the right, ``buttonPressed('chad')``.  

The lambda function serves as a mediator between the UI element and our real callback, ``buttonPressed``, giving us control over what arguments will be passed to ``buttonPressed``. In our example, we ignore all the arguments passed by the button and instead opt to pass the string ``'chad'``, however, if the circumstances require it, you could use the arguments in ``args`` as well::

	btn = button( command = lambda *args: buttonPressed('chad', args[0]) )

In the example above we're using the first of the arguments passed by the button (remember, ``args`` is a tuple, which is like a list) and passing it on to our callback in addition to the name string.  Keep in mind that for this to work our ``buttonPressed`` callback would need to be modified to accept two arguments.

Whew! That was a lot to learn, but unfortunately, this method has a drawback, too. It does not work properly when used in a 'for' loop. 

In the following example, we're going to make several buttons. Our intention is that each one will print a different name, but as you will soon see, we won't succeed. ::

	from pymel.core import *

	def buttonPressed(name):
	    print "pressed %s!" % name

	win = window(title="My Window")
	layout = columnLayout()
	names = ['chad', 'robert', 'james']
	for name in names:
	    button( label=name, command = lambda *args: buttonPressed(name) )

	showWindow()

When pressed, all the buttons will print 'james'. Why is this?   Think of a lambda as a "live" object.  It lives there waiting to execute the code it has been given, but the variables in that code are live too, so the value of the variable named ``character`` changes with each iteration through the loop, thereby changing the code that lambda is waiting to execute.  What is its value at the end of the loop?  It's 'james'. So all the lambda's execute the equivalent of::

    buttonPressed('james')

To solve this we need to "pin" down the value of our variable to keep it from changing.  To do this, pymel provides a `Callback` object...

Callback Objects
~~~~~~~~~~~~~~~~
In my experience this method handles all cases reliably and predictably, and solves the 'lambda' issue described above.
A `Callback` object is an object that behaves like a function, meaning it can be 'called' like a regular function.
The Callback object 'wraps' another function, and also stores the parameters to pass to that function. And, lucky for you, the Callback class is included with pymel.

Here's an example::

	from pymel.core import *

	def buttonPressed(name):
	    print "pressed %s!" % name

	win = window(title="My Window")
	layout = columnLayout()
	names = ['chad', 'robert', 'james']
	for name in names:
	    button( label=name, command = Callback( buttonPressed, name ) )

	showWindow()

Our example now works as intended.  The `Callback` class provides the magic that makes it work. 

Pay close attention to how the Callback is created:  the first argument, ``buttonPressed``, is the function to wrap, and the rest are arguments to that function. The Callback stores the function and its arguments separately and then combines them when it is called by the UI element.  

So, on assignment, something that looks like this... ::

	Callback( buttonPressed, name )

...on execution becomes::

	buttonPressed(name)

	
In this case, the variable ``name`` is the only additional argument, but the Callback class can accept any number of arguments or even keyword arguments, which it will dutifully pass along to your function when the callback is triggered.

The `Callback` class ignores any arguments passed in from the UI element, so you don't have to design your function to take these into account.  However, if you do want these, use the alternate callback object `CallbackWithArgs` which will pass the UI arguments after yours.

----------------------------------
Layouts
----------------------------------

Automatic Form Layouts
======================

One major pain in designing GUIs is the placing of controls in layouts. 
Maya provides the formLayout command which lets controls resize and keep their relationship with other controls, however the use of this command is somewhat cumbersome and unintuitive.
Pymel provides an extended FormLayout class, which handles the details of attaching controls to one another automatically::

    win = window(title="My Window")
    layout = horizontalLayout()
    for i in range(5):
        button(label="button %s" % i)
    layout.redistribute()    # now will redistribute horizontally
    win.show()


The 'redistribute' method redistributes the children (buttons in this case) evenly in their layout.
A formLayout will align its controls vertically by default. By using the 'verticalLayout' or 'horizontalLayout' commands you can explicitly override this (note that both commands still return a FormLayout object)::

By default, the control are redistributed evenly but this can be overridden::

    layout.redistribute(1,3,2)    # (For 5 elements, the ratios will then be 1:3:2:1:1)


You can also specify the ratios at creation time, as well as the spacing between the controls. A ratio of 0 means that the control will not be resized, and will keep a fixed size::

    win = window(title="My Window")
    layout = horizontalLayout(ratios=[1,0,2], spacing=10)
    for i in range(5):
        button(label="button %s" % i)
    layout.redistribute()    # now will redistribute horizontally
    win.show()

Finally, just for fun, you can also reset, flip and reverse the layout::

    layout.flip()     # flip the orientation
    layout.reverse()  # reverse the order of the controls
    layout.reset()    # reset the ratios


Streamlined GUI Creation with Context Managers
==============================================

Anyone who has coded GUIs in Maya using both MEL and python will tell you that if there is one thing they miss about MEL (and only one thing), it is the use of indentation to organize layout hierarchy. this is not possible in python because tabs are a syntactical element, indicating code blocks. In this release, PyMEL harnesses python's ``with`` statement to use indentation to streamlines the process of GUI creation.

Here is a comparison of the `uiTemplate` example from the Maya docs.

First, using ``maya.cmds``::

    import maya.cmds as cmds

    if cmds.uiTemplate('ExampleTemplate', exists=True):
        cmds.deleteUI('ExampleTemplate', uiTemplate=True)
    cmds.uiTemplate('ExampleTemplate')
    cmds.button(defineTemplate='ExampleTemplate',
                width=100, height=40, align='left')
    cmds.frameLayout(defineTemplate='ExampleTemplate', borderVisible=True,
                     labelVisible=False)

    window = cmds.window(menuBar=True,menuBarVisible=True)

    cmds.setUITemplate('ExampleTemplate', pushTemplate=True)
    cmds.columnLayout(rowSpacing=5)

    cmds.frameLayout()
    cmds.columnLayout()
    cmds.button(label='One')
    cmds.button(label='Two')
    cmds.button(label='Three')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.frameLayout()
    cmds.optionMenu()
    menuItem(label='Red')
    menuItem(label='Green')
    menuItem(label='Blue')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.setUITemplate(popTemplate=True)

    cmds.showWindow( window )

    menu()
    menuItem(label='One')
    menuItem(label='Two')
    menuItem(label='Sub', subMenu=True)
    menuItem(label='A')
    menuItem(label='B')
    setParent('..', menu=1)
    menuItem(label='Three')


Now, with PyMEL::

    from __future__ import with_statement # this line is only needed for 2008 and 2009
    from pymel.core import *

    template = uiTemplate('ExampleTemplate', force=True)
    template.define(button, width=100, height=40, align='left')
    template.define(frameLayout, borderVisible=True, labelVisible=False)

    with window(menuBar=True,menuBarVisible=True) as win:
        # start the template block
        with template:
            with columnLayout( rowSpacing=5 ):
                with frameLayout():
                    with columnLayout():
                        button(label='One')
                        button(label='Two')
                        button(label='Three')
                with frameLayout():
                    with optionMenu():
                        menuItem(label='Red')
                        menuItem(label='Green')
                        menuItem(label='Blue')
    # add a menu to an existing window
    with win:
        with menu():
            menuItem(label='One')
            menuItem(label='Two')
            with subMenuItem(label='Sub'):
                menuItem(label='A')
                menuItem(label='B')
            menuItem(label='Three')


Python's ``with`` statement was added in version 2.5 (Maya 2008 and 2009).  Its purpose is to provide automatic "enter" and "exit" functions for class instances that are designed to support it.  This is perfect for MEL GUI creation: for example, when we enter the ``with`` block using a PyMEL `ui.Layout` class or a command that creates one, the layout object sets itself to the active default parent, and when the code block ends, it restores the default parent to it's own parent. There is now little need to ever call `setParent`.  As you can see in the example, the ``with`` statement also works with windows, menus, and templates:  windows call `setParent` and `showWindow`, and templates are automatically "pushed" and "popped".
