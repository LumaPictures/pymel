from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from pymel.core.windows import *


class MelToPythonWindow(Window):

    def __new__(cls, name=None):
        self = window(title=name or "Mel To Python")
        return Window.__new__(cls, self)

    def convert(w):
        from .. import mel2pyStr
        if cmds.cmdScrollFieldExecuter(w.mel, q=1, hasSelection=1):
            cmds.cmdScrollFieldExecuter(w.mel, e=1, copySelection=1)
            cmds.cmdScrollFieldExecuter(w.python, e=1, clear=1)
            cmds.cmdScrollFieldExecuter(w.python, e=1, pasteSelection=1)
            mel = cmds.cmdScrollFieldExecuter(w.python, q=1, text=1)
        else:
            mel = cmds.cmdScrollFieldExecuter(w.mel, q=1, text=1)
        try:
            py = mel2pyStr(mel)
        except Exception as e:
            confirmDialog(t="Mel To Python", m="Conversion Error:\n%s" % e, b=["Ok"], db="Ok")
        else:
            cmds.cmdScrollFieldExecuter(w.python, e=1, text=py)

    def __init__(self):
        formLayout(slc=True, ratios=[1, .1, 1], orientation=FormLayout.HORIZONTAL, childCreators=[
            cmdScrollFieldExecuter("mel", slc=True),
            button("button", slc=True, l="->", c=lambda *x: self.convert(), bgc=[.5, .7, 1]),
            cmdScrollFieldExecuter("python", slc=True, st="python")
        ]).create(self.__dict__, parent=self, debug=1)

        self.setWidthHeight([600, 800])
        self.show()
