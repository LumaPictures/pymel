import pickle
path = r"C:\Documents and Settings\Elrond\My Documents\maya\2008-x64\PyMelBase\pyScripts\pymel\mayaCmdsList2009.bin"
file = open(path, mode='rb')
cmdlist,nodeHierarchy,uiClassList,nodeCommandList,moduleCmds = pickle.load(file)
print "moduleCmds:"
for key, val in moduleCmds.iteritems():
	print "module: %s" % key
	print val
	print

#import pymel