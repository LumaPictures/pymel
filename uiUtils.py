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

    def __init__(self, orientation=VERTICAL, spacing=2, reverse=False, *args,**kwargs):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        self.spacing = spacing
        self.ori = orientation
        self.reversed = reversed
        self.ratios = []
    
    def flip(self):
        """Flip the orientation of the layout """
        self.ori = 1-self.ori
        self.redistribute(*self.ratios)
    
    def reverse(self):
        """Reverse the children order """
        self.reversed = not self.reversed
        self.ratios.reverse()
        self.redistribute(*self.ratios) 
        
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
        
        ratios = list(ratios) or []
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



class SmartLayoutCreator:
    """TODO"""
    def __init__(self, name=None, uiFunc=None, kwargs=None, postFunc=None, childCreators=None):
        assert (uiFunc is None) or callable(uiFunc), uiFunc
        assert kwargs is None or isinstance(kwargs,dict), kwargs
        assert postFunc is None or callable(postFunc), postFunc
        assert childCreators is None or isinstance(childCreators,list), childCreators
        self.__dict__.update(vars())
        
    def create(self, creation=None, parent=None):
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
        


def promptBox(title,message,okText,cancelText,**kwargs):
    """ Prompt for a value. Returns the string value or None if cancelled """
    ret = promptDialog(t=title, m=message, b=[okText,cancelText], db=okText, cb=cancelText,**kwargs)
    if ret==okText:
        return promptDialog(q=1,tx=1)
    
def confirmBox(title, message, yes="Yes", no="No", defaultToYes=True):
    """ Prompt for confirmation. Returns True/False """
    ret = confirmDialog(t=title,    m=message,     b=[yes,no], 
                           db=(defaultToYes and yes or no), 
                           ma="center", cb="No", ds="No")
    return (ret==yes)
                        
                        