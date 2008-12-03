"""
prototype for a pymel ipython configuration

Current Features:
	tab completion of depend nodes, dag nodes, and attributes
	automatic import of pymel

Future Features:
	tab completion of PyNode attributes
	color coding of tab complete options:
		- to differentiate between methods and attributes
		- dag nodes vs depend nodes
		- shortNames vs longNames
	magic commands
	bookmarking of maya's recent project and files

To Use:
	place in your PYTHONPATH
	add the following line to the 'main' function of $HOME/.ipython/ipy_user_conf.py::
	
		import ipymel 

Author: Chad Dombrova
Version: 0.1
"""
try:
	import maya
except ImportError:
	import warnings
	warnings.warn( "ipymel can only be setup if the maya package can be imported" )
else:
		
	import IPython.ipapi
	ip = IPython.ipapi.get()
	
	import readline
	delim = readline.get_completer_delims()
	delim = delim.replace('|', '') # remove pipes
	delim = delim.replace(':', '') # remove colon
	readline.set_completer_delims(delim)
	
	import pymel, re
	
	def finalPipe(obj):
		"""
		DAG nodes with children should end in a pipe (|), so that each successive pressing 
		of TAB will take you further down the DAG hierarchy.  this is analagous to TAB 
		completion of directories, which always places a final slash (/) after a directory.
		"""
		
		if pymel.cmds.listRelatives( obj ):
			return obj + "|" 
		return obj
	
	def splitDag(obj):
		buf = obj.split('|')
		tail = buf[-1]
		path = '|'.join( buf[:-1] )
		return path, tail
	
	def expand( obj ):
		"""
		allows for completion of objects that reside within a namespace. for example,
		``tra*`` will match ``trak:camera`` and ``tram``
		
		for now, we will hardwire the search to a depth of three recursive namespaces.
		TODO:
		add some code to determine how deep we should go
		
		"""
		return (obj + '*', obj + '*:*', obj + '*:*:*')
			
	def pymel_node_completer(self, event): 
			
		#print "\nDAG", repr(event.symbol), repr(event.line)
		#print "\nbegin"
		
		#--------------
		# Attributes
		#--------------
		m = re.search( r"([a-zA-Z_0-9|:.]+)\.(\w*)$", event.line)
		if m:
			# the node var may actually be a plug
			node, attr = m.groups()
			#print node, attr
			long_attrs = pymel.cmds.listAttr( node )
			short_attrs = pymel.cmds.listAttr( node , shortNames=1)
			# if node is a plug  ( 'persp.t' ), the first result will be the passed plug
			if '.' in node:
				attrs = long_attrs[1:] + short_attrs[1:]
			else:
				attrs = long_attrs + short_attrs
			return [ u'%s.%s' % (node, a) for a in attrs if a.startswith(attr) ]
	
		#--------------
		# Nodes
		#--------------
		# grab up any characters that might comprise a valid maya node, mounted on the right
		m = re.search( '[a-zA-Z_0-9|:]+$', event.line)
		if m is None: 
			return []
		
		obj = m.group()
	
	
		kwargs = {}
		
		# full path from root |
		if obj.startswith('|'):
			res = pymel.cmds.ls( expand(obj), l=1 )
			#print res
			return [ finalPipe(x) for x in res]
		   
		# partial path
		elif '|' in obj:
			origObj = obj
			parentPath, tail = splitDag(origObj)
			tmp = pymel.cmds.ls(parentPath, l=1)
			if len(tmp) == 1:
				parentPath = tmp[0]
				#print parentPath
				#print tail
				obj = parentPath + '|' + tail
				res = pymel.cmds.ls ( expand(obj), l=1)
				# revert full path back to original formatting
				res = [ finalPipe(x).replace( obj, origObj ) for x in res ]
				#print res
				return res
			else:
				#print "more than one", tmp
				return []
		else:
			#print "fallback"
			tmpres = pymel.cmds.ls( expand(obj) )
			#print tmpres
			res = []
			for x in tmpres:
				x =  finalPipe(x.split('|')[-1])
				#x = finalPipe(x)
				if x not in res:
					res.append(x)
			#print res
			return res
	
	
	ip.set_hook('complete_command', pymel_node_completer , re_key = ".+(\s+|\()" )
	#ip.set_hook('complete_command', pymel_node_completer, str_key = "dag" ) # for testing
	
	ip.ex("from pymel import *")
	# if you don't want pymel imported into the main namespace, you can replace the above with something like:
	#ip.ex("import pymel as pm")
