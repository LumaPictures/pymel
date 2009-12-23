"""
To use python attribute editor templates, first create a python package or maodule named
'AETemplates'. 

When a attribute editor template is requested by Maya, pymel will look for an `uitypes.AETemplate` subclass to 
create the layout for the desired node type. Here's what it looks for to find a match:
  1. a `uitypes.AETemplate` subclass whose name matches the format ``AE<nodeType>Template`` ( ex. AETemplates.AElambertTemplate )
  2. if ``AETemplates`` is a package with sub-modules, it will look for a sub-module with a name that 
      matches the convention: ``AE<nodeType>Template`` that contains a `uitypes.AETemplate` class of the same name ( ex. AETemplates.AElambertTemplate.AElambertTemplate )
  3. any `uitypes.AETemplate` subclass which has its _nodeName class attribute set to the name the desired node type.
  
The example below demonstrates the simplest case, which is the first. It provides a layout for the mib_amb_occlusion mental ray shader.
"""
    
from pymel.core import *

class LocalizedTemplate(ui.AETemplate):
    "automatically apply language localizations to template arguments"
    def _applyLocalization(self, name):
        if name is not None and len(name)>2 and name[0] == 'k' and name[1].isupper():
            return mel.uiRes('m_' + self.__class__.__name__ + '.' + name)
        return name

    def addControl(self, control, label=None, **kwargs):
        label = self._applyLocalization(label)
        ui.AETemplate.addControl(self, control, label=label, **kwargs)
    
    def beginLayout(self, name, collapse=True):
        name =  self._applyLocalization(name)
        ui.AETemplate.beginLayout(self, name, collapse=collapse)

class MentalRayTemplate(LocalizedTemplate):
    def __init__(self, nodeName):
        LocalizedTemplate.__init__(self,nodeName)
        mel.AEswatchDisplay(nodeName)
        self.beginScrollLayout()
        self.buildBody(nodeName)
        mel.AEmentalrayBaseTemplate(nodeName)
        self.endScrollLayout()
    
class AEmib_amb_occlusionTemplate(MentalRayTemplate):
    def colorChanged(self, node):
        print "changed", node
    def new(self, attr):
        print "new", attr
        self.samplesCtrl = cmds.attrFieldSliderGrp(attribute=attr, min=0, 
            sliderMinValue=2, sliderMaxValue=256,
            step=1.0, sliderStep=1.0, label=self._applyLocalization("kSamples"))
    def replace(self, attr):
        print "replace", attr
        self.samplesCtrl(e=1,attribute=attr)
    def buildBody(self, nodeName):
        print "building", nodeName
        self.beginLayout("kParams",collapse=0)
        self.callCustom(self.new, self.replace, "samples")
        self.addControl("bright", label="kBright", changeCommand=self.colorChanged)
        self.addControl("dark", label="kDark", changeCommand=self.colorChanged)
        self.addControl("spread", label="kSpread", preventOverride=True)
        self.addControl("max_distance", label="kMaxDistance")
        self.addControl("reflective", label="kReflective")
        self.addControl("output_mode", label="kOutputMode")
        self.addControl("occlusion_in_alpha", label="kOcclusionInAlpha")
        self.addControl("falloff", label="kFalloff")
        self.addControl("id_inclexcl", label="If You See This It Worked")
        self.endLayout()
        self.suppress("id_nonself")
        self.dimControl(nodeName, "spread", True)
