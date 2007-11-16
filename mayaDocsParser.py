#!/usr/bin/python

from HTMLParser import HTMLParser
import path,sys, util

class cmdDocParser(HTMLParser):
	def __init__(self):
		self.flags = {}  # a dictionary of command flags, each containing a 2-elem tuple: data, and modes (i.e. edit, create, query)
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
					
if __name__ == '__main__':
	
	bakeCommand( sys.argv[1] )
	
	"""
	parser = cmdDocParser()
	f = open( '/Applications/Autodesk/maya8.5/docs/Maya8.5/en_US/CommandsPython/button.html')
	
	parser.feed( f.read() )
	

	for key, value in parser.flags.items():
		print "--------------"
		print key
		for value in value.values():
			
			
		#for i, text in enumerate(value[0]):
		#	print '%s) %s' % (i, text)
		#print value[1]
	"""