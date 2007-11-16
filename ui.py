
"""
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


import maya.cmds as cmds
import pymel


		
class _BaseUI(unicode):
	"""The abstract base UI class. Each mel UI command has its own subclass of this base class.  The command's flags become methods of
	its respective class.  Editing and querying the flags follows a simple convention: 
	_capitalize the flag and prefix with 'set' or 'get', respectively.  For example: 
	
		>>> myButton = button()	
		>>> height = myButton.getHeight() # query the height
		>>> myButton.setHeight(height+10) # edit the height	
	
	Alternately, to edit a flag, you can also use the unaltered
	name of the flag as the method name, since this sometimes adds to readability. To clear a 
	textScrollList, for example, you could use 'removeAll()' instead of 'setRemoveAll()'. This
	example also illustrates that if no argument is passed to an edit/set command, it defaults to
	True. 
	
	
	A simple UI example:
		>>> from pymel import *

		>>> def buttonPressCB( args ):
		...	print "running button callback with these args", args
		...	print "textField value is", textFieldButtonGrp('myTextBtnGrp').getText()
		...	print "checkbox value is",  ckGrp.getValue1()
		>>> def checkBoxCB( args ):
		...	print "running checkbox callback with these args", args
		>>> win = window()
		>>> columnLayout()
		>>> ckGrp = checkBoxGrp('myChkBxGrp', cc = lambda *args: checkBoxCB(args) ) # pass the provided args to the callback command
		>>> textFieldButtonGrp('myTextBtnGrp', bc= lambda *args: buttonPressCB("someValue") ) # pass your own value to the callback command
		>>> win.show()
		>>> ckGrp.setValue1(1)
	 
	"""
	
	"""
	def __init__(self, name=None, **kwargs ):
		
		self._name = name
		self._name = self._applyArgs(**kwargs)
	"""	
	def __new__(cls, name=None, **kwargs):
		
		func = getattr( cmds, cls.__name__)
		
		args = []
		if name:
			args.append(name)
			
			# when we are passed a name, but no keyword arguments and the ui element already exists we will assume 
			# this is an attempt to create an instace of the class to use in an oo way -- no ui element will be created.
			if not kwargs and apply( func, args, {'exists':True} ):
				self = unicode.__new__(cls, name)
				self._name = name		
				return self	
				
		res = apply( func, args, kwargs)
		
		# this class overrides the function of the same name in maya.cmds. it can also be used in the traditional 
		# fashion as a command, acting exactly like the original command. 
		#print "results", res
		if 'q' in kwargs or 'query' in kwargs or 'ex' in kwargs	or 'exists' in kwargs:
			#print "query"
			return res
		
		#print "creating class"
		
		if not name:
			name = res
			
		self = unicode.__new__(cls, name)
		self._name = name		
		return self
		
	#def __repr__(self):
	#	return "%s('%s')" % (self.__class__.__name__, self)
	
	"""
	def __str__(self):
		return self._name
	"""
		
	def _applyArgs(self, **kwargs):
		func = getattr( cmds, self.__class__.__name__)
		return apply( func, [self._name], kwargs)
		
	def __setattr__(self, attr, value):
		#print "set", attr, value
		if not attr.startswith('_'):			
			kwargs = {'edit':True}
			kwargs[attr] = value
			return self._applyArgs(**kwargs)
		self.__dict__[attr] = value

	"""
	def __getattr__(self, attr):
		kwargs = {'query':True}
		kwargs[attr] = True
		return self._applyArgs(**kwargs)
	"""
	def __getattr__(self, command):
		if command.startswith('__'):
			return self.__dict__[command]
		
		kwargs = {}
		# shortname access
		if len(command) <= 3:
			kwargs['query'] = True
			kwargs[command] = True
			return self._applyArgs(**kwargs)
			
		# get command
		if command.startswith('get'):
			command = command[3].lower() + command[4:]
			kwargs['query'] = True	
							
		# explicit set command
		elif command.startswith('set'):
			command = command[3].lower() + command[4:]
			kwargs['edit'] = True
				
		# implicit set command
		else:
			kwargs['edit'] = True
					
		def _call(value=True):	
			kwargs[command] = value	
			#print kwargs						
			return self._applyArgs(**kwargs)
		return _call
		
	def exists(self):
		kwargs = {'exists':True}	
		return self._applyArgs(**kwargs)
		
	def delete(self):
		cmds.deleteUI(self._name)

'''		
class _BaseUIOLD(object):
	def __init__(self, name, **kwargs ):
		#if 'exists' in kwargs or maya.cmds.window( name, exists=1):
		#	pass
		#else:
		#	maya.cmds.window(name, **kwargs)
		self._name = name
	
	def _applyArgs(self, **kwargs):
		func = getattr( cmds, self.__class__.__name__)
		return apply( func, [self._name], kwargs)
	
	def __setattr__(self, attr, value):
		#print "set", attr, value
		if not attr.startswith('_'):			
			kwargs = {'edit':True}
			kwargs[attr] = value
			return self._applyArgs(**kwargs)
		self.__dict__[attr] = value
	
	def exists(self):
		kwargs = {'exists':True}	
		return self._applyArgs(**kwargs)
	
	def create(self):
		return self._applyArgs()
	
	def delete(self):
		cmds.deleteUI(self._name)
'''
	
uiCommands = [
	'window',					
	'attrColorSliderGrp',
	'attrControlGrp',
	'attrFieldGrp',
	'attrFieldSliderGrp',
	'attrNavigationControlGrp',
	'button',
	'canvas',
	'channelBox',
	'checkBox',
	'checkBoxGrp',
	'cmdScrollFieldExecuter',
	'cmdScrollFieldReporter',
	'cmdShell',
	'colorIndexSliderGrp',
	'colorSliderButtonGrp',
	'colorSliderGrp',
	'commandLine',
	'control',
	'floatField',
	'floatFieldGrp',
	'floatScrollBar',
	'floatSlider',
	'floatSlider2',
	'floatSliderButtonGrp',
	'floatSliderGrp',
	'gradientControl',
	'gradientControlNoAttr',
	'helpLine',
	'hudButton',
	'hudSlider',
	'hudSliderButton',
	'iconTextButton',
	'iconTextCheckBox',
	'iconTextRadioButton',
	'iconTextRadioCollection',
	'iconTextScrollList',
	'iconTextStaticLabel',
	'image',
	'intField',
	'intFieldGrp',
	'intScrollBar',
	'intSlider',
	'intSliderGrp',
	'layerButton',
	'messageLine',
	'nameField',
	'palettePort',
	'picture',
	'progressBar',
	'radioButton',
	'radioButtonGrp',
	'radioCollection',
	'rangeControl',
	'scriptTable',
	'scrollField',
	'separator',
	'shelfButton',
	'shellField',
	'soundControl',
	'swatchDisplayPort',
	'switchTable',
	'symbolButton',
	'symbolCheckBox',
	'text',
	'textField',
	'textFieldButtonGrp',
	'textFieldGrp',
	'textScrollList',
	'timeControl',
	'timePort',
	'toolButton',
	'toolCollection',
	'columnLayout',		
	'formLayout',		
	'frameLayout',
	'gridLayout',
	'layout',
	'menuBarLayout',
	'paneLayout',
	'rowColumnLayout',
	'rowLayout',
	'scrollLayout',
	'shelfLayout',
	'shelfTabLayout'	
]

menuCommands = [
	'artBuildPaintMenu',
	'attrEnumOptionMenu',
	'attrEnumOptionMenuGrp',
	'attributeMenu',
	'hotBox',
	'menu',
	'menuEditor',
	'menuItem',
	'menuSet',
	'menuSetPref',
	'optionMenu',
	'optionMenuGrp'
]

uiCommands += menuCommands

def uiClassFactory( funcName ):	
	class generatedClass( _BaseUI ): pass	
	generatedClass.__name__ = funcName
	generatedClass.__module__ = 'pymel'
	return generatedClass

'''	
for funcName in uiCommands:
	try:
		setattr( pymel, funcName, uiClassFactory( funcName) )
	except NameError: 
		print "pymel: cannot create class for ui element", funcName


# customized ui classes							
class window(_BaseUI):
	"""pymel window class"""						
	def show(self):
		cmds.showWindow(self._name)
	def delete(self):
		cmds.deleteUI(self._name, window=True)
				
class formLayout(_BaseUI):
	def attachForm(self, *args):
		kwargs = {'edit':True}
		#if isinstance(list, args[0]):
		#	kwargs['attachForm'] = args
		#	return self.applyArgs(**kwargs)
			
		kwargs['attachForm'] = [args]
		self._applyArgs(**kwargs)
		
	def attachControl(self, *args):
		kwargs = {'edit':True}
		kwargs['attachControl'] = [args]
		self._applyArgs(**kwargs)		
		
	def attachNone(self, *args):
		kwargs = {'edit':True}
		kwargs['attachNone'] = [args]
		self._applyArgs(**kwargs)	
		
	def attachPosition(self, *args):
		kwargs = {'edit':True}
		kwargs['attachPosition'] = [args]
		self._applyArgs(**kwargs)
		
class textScrollList(_BaseUI):
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
'''	

# customized ui classes							
class Window_(unicode):
	"""pymel window class"""						
	def show(self):
		cmds.showWindow(self)
	def delete(self):
		cmds.deleteUI(self, window=True)
				
class FormLayout_(unicode):
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
		
class TextScrollList_(unicode):
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