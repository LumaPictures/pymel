
""" still a work in progress. this might not be used"""



import maya.cmds
from core import MPath
	
class Scene(object):
	
	def getName(self):
		return MPath(maya.cmds.file( q=1, sn=1))
	
	def getTime(self):
		"""get the current time as a float"""
		return maya.cmds.currentTime(q=1)

	def setTime( self, time ):
		"""set the current time """
		return maya.cmds.currentTime(time)
	
	name = property( getName )	
	time = property( getTime, setTime )

	
scene = Scene()		

#sys.modules[__name__] = Scene()
