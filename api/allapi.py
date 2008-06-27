
# import all available Maya API methods in this module (api)
from maya.cmds import about as _about
from maya.OpenMaya import *
from maya.OpenMayaAnim import *
try: from maya.OpenMayaCloth import *
except: pass
try : from maya.OpenMayaFX import *
except: pass
try : from maya.OpenMayaMPx import *
except: pass
if not _about(batch=True) :
    try : from maya.OpenMayaUI import *
    except: pass
try : from maya.OpenMayaRender import *
except: pass

