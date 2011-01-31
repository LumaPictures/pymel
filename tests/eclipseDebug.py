# Put in whatever code you want to use for an eclipse debug run here...


#mayapy -c "import pymel.core as pm; plug='stereoCamera'; pm.loadPlugin(plug) if not pm.pluginInfo(plug, loaded=1, q=1) else 'doNothing'; print '*******loaded******'; pm.unloadPlugin(plug, f=1); print '*****unloaded*******'"

import pymel.core as pm
node = pm.nt.Transform('persp')
attr = node.attr('translate')
attr.set( (1,2,3) )
