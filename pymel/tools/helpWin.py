import sys
from pydoc import Helper
import pymel.core.windows as windows
import pymel.core.uitypes as uitypes
from cStringIO import StringIO

class HelpWindow(uitypes.Window):
    
    _windows = []
    
    def __new__(cls, *args, **kwargs):
        kwargs['create'] = True
        kwargs['t'] = "Python Help"
        self = uitypes.Window.__new__(cls, *args, **kwargs)
        cls._windows.append(self)
        return self
    
    def __init__(self, *args, **kwargs):
        with self:
            with windows.verticalLayout(ratios=[0,1]) as self.form:
                self.txtField = windows.textFieldGrp(l="Get Help on:", cc=lambda obj: self.getHelp(obj,doEval=True))
                self.scrlHelp = windows.scrollField(editable=0, wordWrap=0)
            for side in ["left","top","right"]: self.form.attachForm(self.txtField,side,2)
            for side in ["left","bottom","right"]: self.form.attachForm(self.scrlHelp,side,2)
            self.form.attachControl(self.scrlHelp,"top",2,self.txtField)
        self.setWidthHeight((600,800))
        self.helper = Helper(self, self)
        
    def write(self, m):
        self.scrlHelp.insertText(m)
        
    def readline(self):
        return self.txtField.getText()
    
    def getHelp(self, obj, doEval=False):
        before = sys.stdout
        sys.stdout = self
        self.scrlHelp.setText("")
        try:
            if doEval:
                obj = eval(obj,vars(sys.modules["__main__"]))
            t = type(obj)
            if t.__name__ == "instance" and t.__module__=="__builtin__":
                obj = obj.__class__
            self.helper(obj)
        finally:
            sys.stdout = before
        self.scrlHelp.setInsertionPosition(1)
        self.show()
 
def helpWin(obj, replace=True, *args):
    """
    Redirects pydoc's help outputs to a new window.
    @replace - replace the contents of the current window or create a new one
    
    Tip - reassign the built-in help function:
        >> help = pymel.tools.helpWin.helpWin
        >> help(pymel)      # result appears in new window
        
    """

    if not HelpWindow._windows:
        replace = False # force a new window
    else:
        helpWin = HelpWindow._windows[-1]
        
    if (not replace or not helpWin.exists()):
        helpWin = HelpWindow(name="winPythonHelp#")
    helpWin.getHelp(obj)
