
.. currentmodule:: pymel.core.windows

==========================
Building User Interfaces
==========================

pymel adds more readability to UI building while also maintaining backward compatibility.  Like nodes and 
PyNodes, every UI command in maya.cmds has a class counterpart in pymel derived from the base class `PyUI`.
The ui commands return these PyUI objects, and these have all of the various methods to get and set properties
on the ui element::


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
this as a python function. Here's a simple example::


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
and prefix the function with the module it will be imported from::

    button( command="myModule.buttonPressed" )

The problem with both of these solutions is that you must ensure that the module is *always* imported the same way, and, if you plan
to share your module with someone, it's pretty impossible to do this.
  
A more robust solution is to include an import command in the string to execute. ::

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

    from pymel import *
    
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
to mimic the "myCommand #1" functionality in MEL). If we had defined our function like this...::

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
exactly which args you want to pass along.::

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

In the above example, this portion of the code...::

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
Our intention is that each one will print a different name, but as you will soon see, we won't succeed. ::

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

