import path, util, pymel, sys, os
from HTMLParser import HTMLParser

#---------------------------------------------------------------
#		Doc Parser
#---------------------------------------------------------------

class cmdDocParser(HTMLParser):
	def __init__(self):
		self.flags = {}  # shortname, argtype, docstring, and a list of modes (i.e. edit, create, query)
		self.currFlag = ''
		self.iData = 0
		self.dataTypes = ['shortname', 'argtype', 'docstring']
		self.active = False  # this is set once we reach the portion of the document that we want to parse
		HTMLParser.__init__(self)
	
	def startFlag(self, data):
		#print self, data
		#assert data == self.currFlag
		self.iData = 0
		self.flags[self.currFlag] = {'shortname': None, 'argtype': None, 'docstring': '', 'modes': [] }
	
	def addFlagData(self, data):
		if self.iData < 2:
			self.flags[self.currFlag][self.dataTypes[self.iData]] = data
		else:
			#self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).strip() + " "
			self.flags[self.currFlag]['docstring'] += data.replace( '\r\n', ' ' ).lstrip()
		self.iData += 1
		
	def endFlag(self):
		# cleanup last flag
		#data = self.flags[self.currFlag]['docstring']
		
		#print "ASSERT", data.pop(0), self.currFlag
		#self.flags[self.currFlag]['shortname'] = data.pop(0)
		self.iData = 0
		
	def handle_starttag(self, tag, attrs):
		#print "Encountered the beginning of a %s tag: %s" % (tag, attrs)
		if not self.active:
			if tag == 'a' and attrs[0][1] == 'hFlags':
				#print 'ACTIVE'
				self.active = 1
		
		elif tag == 'a' and attrs[0][0] == 'name':
			self.endFlag()
			#print "NEW FLAG", self.currFlag
			self.currFlag = attrs[0][1][4:]
			
	
		elif tag == 'img' and len(attrs) > 4:
			#print "MODES", attrs[1][1]
			self.flags[self.currFlag]['modes'].append(attrs[1][1])
			
	def handle_endtag(self, tag):
        #print "Encountered the end of a %s tag" % tag
		pass
	
	def handle_data(self, data):
		if not self.active:
			return
			
		if self.currFlag:
			stripped = data.strip()
			if stripped == 'Return value':
				self.active=False
				return
					
			if data and stripped and stripped not in ['(',')', '=', '], [']:
				#print "DATA", data
			
				if self.currFlag in self.flags:				
					self.addFlagData(data)
				else:
					self.startFlag(data)

def getCmdFlags( command, mayaVersion='8.5' ):
	f = open( util.mayaCommandHelpFile( command, mayaVersion ) )	
	parser = cmdDocParser()
	parser.feed( f.read() )
	f.close()
	return parser.flags

def writeCommand( command ):
	
	outFile = path.path( sys.modules[__name__].__file__ ).parent / 'commands' / command
	f = outFile.open( 'w' )
	f.write( str(getCmdFlags()) )
	f.close()
	
#---------------------------------------------------------------
		
def makeDocs( mayaVersion='8.5' ):
	"internal use only"
	
	import re
	import epydoc.cli
	
	pymeldir = util.moduleDir()
	os.chdir( pymeldir )
	sys.argv = [pymeldir, '--debug',  '--config=%s' % os.path.join( pymeldir, 'epydoc.cfg') ]
	epydoc.cli.cli(useLogger=False)
		
	docdir = pymeldir / 'docs'
	
	try:
		(docdir / 'CommandsPython').mkdir()
	except OSError:
		pass
	
	htmlFile = 'pymel-module.html'
	f = open( os.path.join( docdir, htmlFile), 'r'  )
	lines = f.readlines()
	f.close()
	
	reg = re.compile("(pymel-module.html#)([a-zA-Z0-9_]+)")
	for i, line in enumerate(lines):
		buf = reg.split( line )
		try:
			command = buf[2]
			localHelpFile = path( 'CommandsPython/' + command + '.html' )
			line = buf[0] + localHelpFile + buf[3]
			localHelpFile = docdir / localHelpFile
			if not localHelpFile.exists():				
				globalHelpFile = path( util.mayaCommandHelpFile( command, mayaVersion ) )
				print "copying", globalHelpFile, localHelpFile
				globalHelpFile.copy( localHelpFile.parent )
				
		except: pass
		lines[i] = line 
	
	f = open( os.path.join(pymeldir, 'docs', htmlFile), 'w' ) 
	f.writelines(lines)
	f.close()

	

#-----------------------------------------------
#  Command Help Documentation
#-----------------------------------------------


def writeCommandHelp(runTest=False):
	files = ['commandsCreation', 'commandsCtx', 'commandsUI', 'commandsEnhanced']
	baseDir = util.moduleDir()
	
	print "writing out doc dictionaries"
	
	commandHelp = {}
	for f in files:
		file = (baseDir / f).open( 'r' )
		
		for funcName in file:
			funcName = funcName.split()[0].strip()

			#---------------------------
			# 	Write Docs
			#---------------------------
						
			commandHelp[funcName] = {'help' : pymel.mel.help(funcName) }
				
			if f in ['commandsCreation','commandsUI']:
				commandHelp[funcName]['flagDocs' ] = getCmdFlags(funcName)
			
			#---------------------------
			# 	Test
			#---------------------------
			if f=='commandsCreation' and runTest:
				if funcName in [ 'character', 'lattice' ]:
					continue
				print funcName
				
				try:
					func = getattr(pymel.core, funcName)
				except AttributeError:
					func = getattr(cmds,funcName)
				try:
					cmds.select(cl=1)
					
					if funcName.endswith( 'onstraint'):
						s = cmds.polySphere()[0]
						c = cmds.polyCube()[0]
						obj = func(s,c)
					else:
						obj = func()
					
					
					
				except RuntimeError, msg:
					print "ERROR: failed creation:", msg
				except TypeError, msg:
					print "ERROR: failed creation:", msg
				else:
					if isinstance(obj, list):
						obj = obj[0]

					for flag, flagInfo in commandHelp[funcName]['flagDocs'].items():			
						if flag in ['query', 'edit']:
							continue
						modes = flagInfo['modes']
					
						cmd = "%s('%s', query=True, %s=True)" % (func.__name__, obj,  flag)
						try:
							if 'query' in modes:
							
								val = func( obj, **{'query':True, flag:True} )
								#print val
						except TypeError, msg:							
							if str(msg).startswith( 'Invalid flag' ):
								commandHelp[funcName]['flagDocs'].pop(flag,None)
							else:
								print cmd
								print "TypeError:", msg
						except RuntimeError, msg:
							print cmd
							print "RuntimeError:", msg	
					
						cmd =  "%s('%s', edit=True, %s=%s)" % (func.__name__, obj,  flag, val)
						try:
							if 'edit' in modes:
								if val is None:
									argMap = { 
										'boolean'	 	: True,
										'int'			: 0,
										'float'			: 0.0,
										'linear'		: 0.0,
										'double'		: 0.0,
										'angle'			: 0,
										'string' :		'persp'
									}
									
									argtype = flagInfo['argtype']
									if '[' in argtype:
										val = []
										for typ in argtype.strip('[]').split(','):
											val.append( argMap[typ.strip()] )
									else:
										val = argMap[argtype]					
							
								func( obj, **{'edit':True, flag:val} )

								#print "SKIPPING %s: need arg of type %s" % (flag, flagInfo['argtype'])
						except TypeError, msg:														
							if str(msg).startswith( 'Invalid flag' ):
								commandHelp[funcName]['flagDocs'].pop(flag,None)
							else:
								print cmd
								print "TypeError:", msg 
						except RuntimeError, msg:
							print cmd
							print "RuntimeError:", msg	
						except KeyError:
							print "UNKNOWN ARG:", flagInfo['argtype']
						val = None
			
						
		file.close()

	commandHelpFile.write_text( str( commandHelp ) )
	
	print "done"
	
# commandHelp file contains a dictionary of help info on various commands processed by helpers.writeCommandHelp()
commandHelp= {}
commandHelpFile = util.moduleDir() / 'commandHelp'
try:	
	commandHelp = eval( commandHelpFile.text() )
except:
	print "could not file dictionary of command help information at", commandHelpFile
