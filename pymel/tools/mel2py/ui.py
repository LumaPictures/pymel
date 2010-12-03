from pymel.core.windows import window, cmdScrollFieldExecuter, informBox, horizontalLayout, button
from pymel.core.uitypes import Window
from pymel.tools.mel2py import mel2pyStr

class MelToPythonWindow(Window):

    def __new__(cls, name=None):
        self = window(title=name or "Mel To Python")
        return Window.__new__(cls, self)

    def convert(self, *x):
        
        if self.mel.getHasSelection():
            self.mel.copySelection()
            self.python.clear()
            self.python.pasteSelection()
            mel = self.python.getText()
        else:
            mel = self.mel.getText()
        try:
            py = mel2pyStr(mel)
        except Exception, e:
            informBox("Mel To Python","Conversion Error:\n%s" % e)
        else:
            self.python.setText(py)


    def __init__(self):
        with horizontalLayout(ratios=[1,.1,1]):
            self.mel = cmdScrollFieldExecuter()
            self.button = button(l="->", c=self.convert, bgc=[.5,.7,1])
            self.python = cmdScrollFieldExecuter(st="python")
        self.setWidthHeight([600,800])
        self.show()

