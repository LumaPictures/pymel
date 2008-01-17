
"""
The ui module contains functions which are used to create ui elements, as well as their class counterparts.

Pymel UIs
=========

pymel adds more readability to ui building while also maintaining backward compatibility.  Every ui command in maya.cmds
is a class in pymel, which can behave like a command or like a class. More documentation on this to come, but for now
check out pipeGen.py in examples directory

Command Callbacks
-----------------

one common point of confusion is command callbacks with ui elements. There are several different ways to handle 
command callbacks on user interface widgets:  
						
Function Name as String
~~~~~~~~~~~~~~~~~~~~~~~

maya will try to execute this as a python command, but unless you know the namespace it will
be imported into, the function will not be recognized. notice how the namespace must be hardwired
into the command:

	>>> button( c="myCommand" )

or

	>>> button( c="myModule.myCommand" )

this method is not recommended.

Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is referenced by the command flag.  also, keep in mind many ui widgets such as radioButtonGrp
pass args to the function (to mimic the "myCommand #1" functionality in mel), which your function must accommodate. The
tricky part is that different ui elements pass differing numbers of args to their callbacks, and some pass none at all.
This is why it is best for your command to use the *args syntax to accept any quantity of args, and then deal with them
in the function.

	>>> def myCommand( *args ): print args # this definition must come first

	>>> button( c=myCommand )
				
Lambda Functions
~~~~~~~~~~~~~~~~
In my experience this is the best way to handle most command callbacks.  You can choose exactly which args you want
to pass along to your function and order of definition does not matter.

	>>> button( c= lambda *args: myCommand(args[0]) )

	>>> def myCommand( arg ): print "running", arg 


"""


try:
	import maya.cmds as cmds
except ImportError: pass

import factories, util, core

	
#-----------------------------------------------
#  Enhanced UI Commands
#-----------------------------------------------

scriptTableCmds = {}

def scriptTable(*args, **kwargs):
	"""
Maya Bug Fix:
	- fixed getCellCmd to work with python functions, previously only worked with mel callbacks
		IMPORTANT: you cannot use the print statement within the getCellCmd callback function or your values will not be returned to the table
	"""
	cb = kwargs.pop('getCellCmd', kwargs.pop('gcc',False) )
	if cb:
		if hasattr(cb, '__call__'):		
			uiName = cmds.scriptTable( *args, **kwargs )
			procName = 'getCellMel%d' % len(scriptTableCmds.keys())
			procCmd = "global proc string %s( int $row, int $column ){return python(\"pymel.scriptTableCmds['%s'](\" + $row + \",\" + $column + \")\");}" %  (procName,uiName) 
			#print procCmd
			mm.eval( procCmd )			
			scriptTableCmds[uiName] = cb
			
			# create a scriptJob to clean up the dictionary of functions
			popCmd = "python(\"scriptTableCmds.pop('%s',None)\")" % uiName 
			#print popCmd
			cmds.scriptJob( uiDeleted=(uiName, "python(\"pymel.scriptTableCmds.pop('%s',None)\")" % uiName ) )

			return cmds.scriptTable( uiName, e=1, getCellCmd=procName )
		else:
			kwargs['getCellCmd'] = cb	
	
	cmds.scriptTable( *args, **kwargs )
	

class UI(unicode):
	def __repr__(self):
		return u"%s('%s')" % (self.__class__.__name__, self)
	def getChildren(self, **kwargs):
		kwargs['long'] = True
		return filter( lambda x: x.startswith(self) and not x == self, core.lsUI(**kwargs))
	def getParent(self):
		return UI( '|'.join( self.split('|')[:-1] ) )
	def type(self):
		return objectTypeUI(self)
	def shortName(self):
		return self.split('|')[-1]

# customized ui classes							
class Window(UI):
	"""pymel window class"""
	__metaclass__ = factories.metaNode						
	def show(self):
		cmds.showWindow(self)
	def delete(self):
		cmds.deleteUI(self, window=True)
				
class FormLayout(UI):
	__metaclass__ = factories.metaNode
	def attachForm(self, *args):
		kwargs = {'edit':True}
		#if isinstance(list, args[0]):
		#	kwargs['attachForm'] = args
		#	return self.applyArgs(**kwargs)
			
		kwargs['attachForm'] = [args]
		cmds.formLayout(self,**kwargs)
		
	def attachControl(self, *args):
		kwargs = {'edit':True}
		kwargs['attachControl'] = [args]
		cmds.formLayout(self,**kwargs)		
		
	def attachNone(self, *args):
		kwargs = {'edit':True}
		kwargs['attachNone'] = [args]
		cmds.formLayout(self,**kwargs)	
		
	def attachPosition(self, *args):
		kwargs = {'edit':True}
		kwargs['attachPosition'] = [args]
		cmds.formLayout(self,**kwargs)
		
class TextScrollList(UI):
	__metaclass__ = factories.metaNode
	def extend( self, appendList ):
		""" append a list of strings"""
		
		for x in appendList:
			self.append(x)
			
	def selectIndexedItems( self, selectList ):
		"""select a list of indices"""
		for x in selectList:
			self.selectIndexedItem(x)

	def removeIndexedItems( self, removeList ):
		"""remove a list of indices"""
		for x in removeList:
			self.removeIndexedItem(x)
				
	def selectAll(self):
		"""select all items"""
		numberOfItems = self.getNumberOfItems()
		self.selectIndexedItems(range(1,numberOfItems+1))

_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly

def _createClassesAndFunctions():
	for funcName in factories.moduleCmds['ui']:
		classname = util.capitalize(funcName)
		if not hasattr( _thisModule, classname ):
			cls = factories.metaNode(classname, (UI,), {})
			cls.__module__ = __name__
			setattr( _thisModule, classname, cls )
		else:
			cls = getattr( _thisModule, classname )
	
		#funcName = util.uncapitalize( classname )
		func = factories.functionFactory( funcName, cls, _thisModule )
		if func:
			func.__module__ = __name__
			setattr( _thisModule, funcName, func )
		else:
			print "ui command not created", funcName
_createClassesAndFunctions()

def PyUI(strObj, type=None):
	try:
		if not type:
			type = core.objectTypeUI(strObj)
		return getattr(_thisModule, util.capitalize(type) )(strObj)
	except AttributeError:
		return UI(strObj)
	