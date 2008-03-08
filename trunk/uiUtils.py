"""
Provides classes and functions to facilitate UI c in Maya
"""
from ui import *


class AutoLayout(FormLayout):
    """ 
    Automatically distributes child controls in either a
    horizontal or vertical layout. Call 'redistribute' once done
    adding child controls.
    """
    HORIZONTAL, VERTICAL = range(2)
    sides = [["top","bottom"],["left","right"]]

    def __new__(cls,  *args, **kwargs):
        kwargs.pop("orientation",None)
        kwargs.pop("spacing",None)
        kwargs.pop("reversed",None)
        kwargs.pop("ratios",None)
        return FormLayout.__new__(cls, *args, **kwargs)
        
    def __init__(self, orientation=VERTICAL, spacing=2, reversed=False, ratios=None, *args,**kwargs):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
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
        
    def redistribute(self,*ratios):
        """ Redistribute the child controls based on the given ratios.
            If not ratios are given (or not enough), 1 will be used 
            win=Window(create=1)
            win.show()
            al=AutoLayout(create=1,parent=win)
            [pm.Button(create=1,l=i,parent=al) for i in "yes no cancel".split()] # create 3 buttons
            al.redistribute(2,2) # First two buttons will be twice as big as the 3rd button
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
        
class HorizontalLayout(AutoLayout):
    """ Alias for AutoLayout with a HORIZONTAL orientation """
    def __init__(self, *args,**kwargs):
        kwargs["orientation"] = AutoLayout.HORIZONTAL
        AutoLayout.__init__(self, *args, **kwargs)

class VerticalLayout(AutoLayout):
    """ Alias for AutoLayout with a VERTICAL orientation """
    def __init__(self, *args,**kwargs):
        kwargs["orientation"] = AutoLayout.VERTICAL
        AutoLayout.__init__(self, *args, **kwargs)    

def autoLayout(*args, **kwargs):
    kwargs["create"] = True
    return AutoLayout(*args, **kwargs)

def horizontalLayout(*args, **kwargs):
    kwargs["create"] = True
    return HorizontalLayout(*args, **kwargs)

def verticalLayout(*args, **kwargs):
    kwargs["create"] = True
    return VerticalLayout(*args, **kwargs)



class SmartLayoutCreator:
    """
    Create a set of layouts and controls using a nested data structure.
    Example (just try it...):
        
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
        
    def create(self, creation=None, parent=None):
        """ 
        Create the ui elements defined in this SLC. 
        Named elements will be inserted into the 'creation' dictionary, which is also the return value of this function.
        The top ui element can be explicitly placed under 'parent', or implicitly under the current ui parent.
        """  
        
        if creation is None:
            creation = {}
        childCreators = self.childCreators or []
        if parent and self.uiFunc: self.kwargs["parent"] = parent
        self.me = self.uiFunc and self.uiFunc(**self.kwargs) or parent
        
        if self.name:
            creation[self.name] = self.me
        [child.create(creation=creation,parent=self.me) for child in childCreators]
        if self.postFunc: self.postFunc(self.me)
        return creation

SLC = SmartLayoutCreator
        
def labeledControl(label, uiFunc, kwargs, align="left", parent=None, ratios=None):
    dict = SLC("layout", HorizontalLayout, {"create":True, "ratios":ratios}, HorizontalLayout.redistribute,  [
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
    
def confirmBox(title, message, yes="Yes", no="No", defaultToYes=True):
    """ Prompt for confirmation. Returns True/False """
    ret = confirmDialog(t=title,    m=message,     b=[yes,no], 
                           db=(defaultToYes and yes or no), 
                           ma="center", cb="No", ds="No")
    return (ret==yes)
                        
                        
                        
                            