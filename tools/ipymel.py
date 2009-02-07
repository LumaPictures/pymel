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
	
	import inspect, re, glob,os,shlex,sys
	import pymel
	
	import IPython.Extensions.ipy_completers
	
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
	
	def complete_node_with_no_path( node ):
		tmpres = pymel.cmds.ls( expand(node) )
		#print "node_with_no_path", tmpres, node, expand(node)
		res = []
		for x in tmpres:
			x =  finalPipe(x.split('|')[-1])
			#x = finalPipe(x)
			if x not in res:
				res.append( x )
		#print res
		return res
	
	def complete_node_with_attr( node, attr ):
		#print "noe_with_attr", node, attr
		long_attrs = pymel.cmds.listAttr( node )
		short_attrs = pymel.cmds.listAttr( node , shortNames=1)
		# if node is a plug  ( 'persp.t' ), the first result will be the passed plug
		if '.' in node:
			attrs = long_attrs[1:] + short_attrs[1:]
		else:
			attrs = long_attrs + short_attrs
		return [ u'%s.%s' % ( node, a) for a in attrs if a.startswith(attr) ]
					
	def pymel_node_completer(self, event): 
			
		#print "\nDAG", repr(event.symbol), repr(event.line)
		#print "\nbegin"
		line = event.line
		#line = event.line.replace( 'SCENE.', '' )
		
		#print "\nDAG", repr(event.symbol), repr(line)
		
		#--------------
		# Attributes
		#--------------
		m = re.search( r"([a-zA-Z_0-9|:.]+)\.(\w*)$", line)
		if m:
			# the node var may actually be a plug
			node, attr = m.groups()
			#print "attribute", node, attr
			if node == 'SCENE':
				return ['SCENE.' + x for x in complete_node_with_no_path(attr) ]
			elif node.startswith('SCENE.'):
				node = node.replace('SCENE.', '')
				return ['SCENE.' + x for x in complete_node_with_attr(node, attr) ]
			return complete_node_with_attr(node, attr)

	
		#--------------
		# Nodes
		#--------------
		# grab up any characters that might comprise a valid maya node, mounted on the right

		m = re.search( r'[a-zA-Z_0-9|:]+$', line)
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
			return complete_node_with_no_path(obj)
	
	greedy_cd_completer = False
	
	def filepath_completer(self, event):
		relpath = event.symbol
		#print repr(relpath), repr(event.line)
		#print event # dbg
#		if '-b' in event.line:
#			# return only bookmark completions
#			bkms = self.db.get('bookmarks',{})
#			return bkms.keys()
#	
#		
#		if event.symbol == '-':
#			width_dh = str(len(str(len(ip.user_ns['_dh']) + 1)))
#			# jump in directory history by number
#			fmt = '-%0' + width_dh +'d [%s]'
#			ents = [ fmt % (i,s) for i,s in enumerate(ip.user_ns['_dh'])]
#			if len(ents) > 1:
#				return ents
#			return []
#	
#		if event.symbol.startswith('--'):
#			return ["--" + os.path.basename(d) for d in ip.user_ns['_dh']]
		
		if relpath.startswith('~'):
			relpath = os.path.expanduser(relpath).replace('\\','/')
		found = []
		for d in [f.replace('\\','/') for f in glob.glob(relpath+'*')
				  #if os.path.isdir(f)
				  ]:
			if ' ' in d:
				# we don't want to deal with any of that, complex code
				# for this is elsewhere
				raise IPython.ipapi.TryNext
			if os.path.isdir(d):
				d += '/'
			found.append( d )
	
		if not found:
			return [relpath]
	
	
		def single_dir_expand(matches):
			"Recursively expand match lists containing a single dir."
			
			if len(matches) == 1 and os.path.isdir(matches[0]):
				# Takes care of links to directories also.  Use '/'
				# explicitly, even under Windows, so that name completions
				# don't end up escaped.
				d = matches[0]
				if d[-1] in ['/','\\']:
					d = d[:-1]
	
				subdirs = [p for p in os.listdir(d) if os.path.isdir( d + '/' + p) and not p.startswith('.')]
				if subdirs:
					matches = [ (d + '/' + p) for p in subdirs ]
					return single_dir_expand(matches)
				else:
					return matches
			else:
				return matches
	
		if greedy_cd_completer:
			return single_dir_expand(found)
		else:
			return found
	
#	m = re.compile( '(.*(File)$)|(.*(Reference)$)|(^(export).*)' )
#	pathCmds = [ '(%s)' % name for name, obj in inspect.getmembers( pymel.core.system, inspect.isfunction ) if m.match(name) ]
#	regkey = '|'.join( pathCmds )
	
	#ip.set_hook('complete_command', pymel_node_completer , re_key = ".+(\s+|\()" )
	
	#ip.set_hook('complete_command', IPython.Extensions.ipy_cyeahompleters.cd_completer , re_key = regkey )
	ip.set_hook('complete_command', filepath_completer , re_key = ".+(\s+|\()" )
	ip.set_hook('complete_command', pymel_node_completer , re_key = "(.+(\s+|\())|(SCENE\.)" )
	#ip.set_hook('complete_command', filepath_completer , str_key = "openFile" )
	#ip.set_hook('complete_command', pymel_node_completer, str_key = "dag" ) # for testing
	
	ip.ex("from pymel import *")
	# if you don't want pymel imported into the main namespace, you can replace the above with something like:
	#ip.ex("import pymel as pm")
