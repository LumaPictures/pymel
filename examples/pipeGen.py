from __future__ import with_statement
from pymel.all import *

"""
work in progress:

tool for creating procedural pipes

pipes can be moved in a typical hierarchical way by selecting joint handles and moving or rotating.
this will move all pipes below it in the pipe chain.

in addition, by hitting insert or holding the d (pivot) key, only the selected joint will be moved,
preserving the position of all other joints.

to run:
	>>> import pymel.examples.pipeGen as pipeGen
	>>> pipeGen.pipeGenWin()

to create pipes via a script:

	>>> pipeGen.startPipe()
	>>> pipeGen.extendPipe()

"""


ALPHABET = 'ABCDEFGHIJKLMNOP'



def startPipe( basename='pipe', 
			pipeRadius = 0.2,
			jointRadius = 0.02,
			subdivAxis = 16,
			subdivJoint = 8,
			jointLength = .8,
			connectorRadius = .1,
			connectorThickness = .2,
			connectorOffset = .001
			):
	print basename
	i=1
	name = basename + str(i)
	while ls( name + '_Jnt0'):
		i += 1
		name = basename + str(i)
	
	try:
		startPos = selected()[0].getTranslation(ws=1)
	except:
		startPos = [0,0,0]
		
	select(cl=1)
	
	rigGrp = group(empty=True, n='%s_RigGrp' % name)
	geoGrp = group(empty=True, n='%s_GeoGrp' % name)
	
	root = joint( name=name+'_Jnt0')

	trans = group(empty=True, n='%s_Elbow0' % name)
	pointConstraint( root, trans )

	root.scale.lock()
	
	root.addAttr( 'globalPipeRadius', 
			defaultValue=pipeRadius, 
			min=.0001 )
	root.globalPipeRadius.showInChannelBox(1)
	
	root.addAttr( 'globalJointRadius', 
		defaultValue=jointRadius  )
	root.globalJointRadius.showInChannelBox(1)

	root.addAttr( 'subdivisionsAxis', at = 'short', 
		defaultValue=subdivAxis, 
		min=4 )
	root.subdivisionsAxis.showInChannelBox(1)
	
	root.addAttr( 'subdivisionsJoint', at = 'short', 
		defaultValue=subdivJoint )
	root.subdivisionsJoint.showInChannelBox(1)

	root.addAttr( 'globalConnectorRadius',
		defaultValue=connectorRadius )
	root.globalConnectorRadius.showInChannelBox(1)
	
	root.addAttr( 'globalConnectorThickness',
		defaultValue=connectorThickness )
	root.globalConnectorThickness.showInChannelBox(1)
	
	root.addAttr( 'globalConnectorOffset',
		min = 0,
		defaultValue=connectorOffset )
	root.globalConnectorOffset.showInChannelBox(1)
					
	root.radius.showInChannelBox(0)
	root.displayHandle = 1
	
	root.setParent(rigGrp)
	trans.setParent(rigGrp)
	
	root.setTranslation( startPos )
	root.select()
	extendPipe(jointLength)
	

'''
def makeConnectors( parent, name, num):
	# Connectors
	pipe, pipeist = polyCylinder( height = 1, radius=1,
						name = '%s_ConnectorGeo1%s' % (name, num) )
'''						
						

def extendPipe( jointLength=1 ):
	
	defaultLength = 3.0
	currJnt = ''
	name = ''
	root = ''
	
	newJnts = []
	
	for sel in selected():
		sel.select()
		# for now, there's no branching, so we find the deepest joint
		try:
			currJnt = sel
			name = currJnt.split('_')[0]
			root = Joint( '%s_Jnt0' % name )
		
		except:
			raise "select an object on the pipe that you want to extend"
		
		
		# naming
		#----------
		num = int(currJnt.extractNum())

		try:
			twoPrev = int(currJnt.getParent().getParent().extractNum())
		except:
			twoPrev = num-2

		try:
			prev =	int(currJnt.getParent().extractNum())
		except:
			prev = num-1

		curr = num
		new = int(currJnt.nextUniqueName().extractNum())
		
		print "extending from", currJnt, new
	
		branchNum = len(currJnt.getChildren())
		#print '%s has %s children' % (currJnt, branchNum)
		if branchNum:
			print "new segment is a branching joint"
			currJnt.addAttr( 'pipeLengthInBtwn%s' % branchNum, min=0 )
			#currJnt.attr( 'pipeLengthInBtwn%s' % branchNum ).showInChannelBox(1)
		
		#print twoPrev, prev, curr, new
		
		rigGrp = '%s_RigGrp' % name
		geoGrp = '%s_GeoGrp' % name
	
		# new skeletal joint
		#---------------------		
		
		if new>1:
			prevJnt = Joint( '%s_Jnt%s' % (name, prev) )
			pos = 2*currJnt.getTranslation(ws=1) - prevJnt.getTranslation(ws=1)
		else:
			prevJnt = None
			pos = currJnt.getTranslation(ws=1) + [0,defaultLength,0]
		
		newJnt = joint( p=pos, n= '%s_Jnt%s' % (name, new) )
		# re-orient the last created joint, which is considered our current joint
		joint( currJnt, e=1, zeroScaleOrient=1, secondaryAxisOrient='yup', orientJoint='xyz')
	
	
	
		# pymel method: NEEDS FIXING
		#currJnt.setZeroScaleOrient(1)
		#currJnt.setSecondaryAxisOrient('yup') # Flag secondaryAxisOrient can only be used in conjunction with orientJoint flag.
		#currJnt.setOrientJoint('xyz')
		newJnt.scale.lock()
	
		newJnt.addAttr( 'pipeLength', 
			defaultValue=jointLength, min=.0001 )
		newJnt.pipeLength.showInChannelBox(1)

		newJnt.addAttr( 'pipeLengthInBtwn0', min=0 )
		#newJnt.attr( 'pipeLengthInBtwn0' ).showInChannelBox(1)
		
		newJnt.addAttr( 'pipeLeadIn', dv=0, min=0 )
		newJnt.pipeLeadIn.showInChannelBox(1)

		newJnt.addAttr( 'radiusMultiplier', dv=1, min=0 )
		newJnt.radiusMultiplier.showInChannelBox(1)
		newJnt.displayHandle = 1
	
		newJnt.radius.showInChannelBox(0)
	
		# bend hierarchy
		#-----------------
					
		trans = group( empty=1, n='%s_Elbow%s' % (name, new))
		trans.rotateOrder = 1

		aimConstraint( 	currJnt, trans, 
							aimVector = [0, -1, 0],
			 				upVector = [-1, 0, 0]
							)
		pointConstraint( newJnt, trans )
	
		trans.setParent( rigGrp )
	
		# keep the end joint oriented along the joint chain so that it can be slid back
		# and forth to change the length of the current pipe segment
		delete( orientConstraint( trans, newJnt ) )
		
		# Main Pipe
		#------------
		pipe, pipeHist = polyCylinder( height = 1, radius=1,
							name = '%s_Geo%s' % (name, new) )
		pipeHist = pipeHist.rename( '%s_GeoHist%s' % (name, new)  )
	
		pipe.setPivots( [0, -.5, 0], r=1 )
	
		
		root.globalPipeRadius >> pipe.sx 
		root.globalPipeRadius >> pipe.sz 
	
		pipeHist.createUVs = 3   # normalize and preserve aspect ratio 
		root.subdivisionsAxis >> pipeHist.subdivisionsAxis

	
		# Pipe Connectors
		#-------------
		pipeConn1, pipeConnHist1 = polyCylinder( height = .1, radius=1,
							name = '%s_Connector1AGeo%s' % (name, new) )
		pipeConnHist1 = pipeConnHist1.rename( '%s_Connector1AHist%s' % (name, new)  )
		pipeConn1.setPivots( [0, -.05, 0], r=1 )
		pipeConn1.setParent( pipe, relative=True )
		pipeConn1.rotate.lock()
		root.subdivisionsAxis >> pipeConnHist1.subdivisionsAxis
	
		
		pipeConn2, pipeConnHist2 = polyCylinder( height = .1, radius=1,
							name = '%s_Connector2AGeo%s' % (name, new) )
		pipeConnHist2 = pipeConnHist2.rename( '%s_Connector2AHist%s' % (name, new)  )
		pipeConn2.setPivots( [0, .05, 0], r=1 )
		pipeConn2.setParent( pipe, relative=True )
		pipeConn2.rotate.lock()
		root.subdivisionsAxis >> pipeConnHist2.subdivisionsAxis

		pipeConn1, pipeConnHist1 = polyCylinder( height = .1, radius=1,
							name = '%s_Connector1BGeo%s' % (name, new) )
		pipeConnHist1 = pipeConnHist1.rename( '%s_Connector1BHist%s' % (name, new)  )
		pipeConn1.setPivots( [0, -.05, 0], r=1 )
		pipeConn1.setParent( pipe, relative=True )
		pipeConn1.rotate.lock()
		pipeConn1.visibility = 0
		root.subdivisionsAxis >> pipeConnHist1.subdivisionsAxis
	
		
		pipeConn2, pipeConnHist2 = polyCylinder( height = .1, radius=1,
							name = '%s_Connector2BGeo%s' % (name, new) )
		pipeConnHist2 = pipeConnHist2.rename( '%s_Connector2BHist%s' % (name, new)  )
		pipeConn2.setPivots( [0, .05, 0], r=1 )
		pipeConn2.setParent( pipe, relative=True )
		pipeConn2.rotate.lock()
		pipeConn2.visibility = 0
		root.subdivisionsAxis >> pipeConnHist2.subdivisionsAxis
		
		
		pipe.setParent( geoGrp )
		
							
		#constraints
		pointConstraint( currJnt, pipe )
		aim = aimConstraint( newJnt, pipe )
		aim.offsetZ = -90 

		

		# convert the previous pipe joint into a bendy joint
		if new > 1:
			currElbow = PyNode('%s_Elbow%s' % (name, curr) )
			pipeLoc = spaceLocator( n= '%s_PipeDummy%s' % (name, new) )
			pipeLoc.hide()
	
			tweak = group(n='%s_ElbowTweak%s' % (name, new))
			tweak.rotateOrder = 2
			#tweak.translate = currElbow.translate.get()
			tweak.setParent( currElbow, r=1 )	
			aimConstraint( 	prevJnt, tweak, 
							aimVector = [1, 0, 0],
			 				upVector = [0, -1, 0],
							skip=['z', 'x'] )
					
							
			# Pipe Joint
			#------------
			pipeJnt, pipeJntHist = polyCylinder( height = 1, radius=1,
								name = '%s_JntGeo%s' % (name, new),
								subdivisionsAxis = 20,
								subdivisionsHeight = 30 )
			pipeJnt.setParent( geoGrp )
			pipeJnt.sy = jointLength
			pipeJnt.visibility = 0
			pipeJntHist = pipeJntHist.rename( '%s_JntGeoHist%s' % (name, new)  )
			pipeJntHist.createUVs = 3   # normalize and preserve aspect ratio
	
			root.subdivisionsAxis >> pipeJntHist.subdivisionsAxis
			root.subdivisionsJoint >> pipeJntHist.subdivisionsHeight 
	
			# constraints	
			parentConstraint( pipeLoc, pipeJnt )
			pipeJnt.translate.lock()
			pipeJnt.rotate.lock()
			#pipeJnt.scale.lock()

		
			aim = PyNode('%s_Elbow%s_aimConstraint1' % (name, curr))
			aim.setWorldUpType( 2 )
			aim.setWorldUpObject( newJnt )
		
			bend, bendHandle = nonLinear( '%s_JntGeo%s' % (name, new),
				type='bend' )
			bendHandle = Transform(bendHandle).rename( '%s_BendHandle%s' % (name, new) )
			bendHandle.sx =.5
			bendHandle.hide()
		
			bend.rename( '%s_Bend%s' % (name, new) )
		
			parentConstraint( '%s_ElbowTweak%s' % (name, new), bendHandle )
		
			aim = '%s_ElbowTweak%s_aimConstraint1' % (name, new)
			#aim.worldUpType.set( 1 )
			aimConstraint( aim, e=1, worldUpType='object', worldUpObject=newJnt )

			bendHandle.setParent(rigGrp)
		
			expr = """
	float $v1[];
	$v1[0] = %(name)s_Elbow%(twoPrev)s.translateX - %(name)s_Elbow%(prev)s.translateX;
	$v1[1] = %(name)s_Elbow%(twoPrev)s.translateY - %(name)s_Elbow%(prev)s.translateY;
	$v1[2] = %(name)s_Elbow%(twoPrev)s.translateZ - %(name)s_Elbow%(prev)s.translateZ;

	float $v2[];
	$v2[0] = %(name)s_Elbow%(curr)s.translateX - %(name)s_Elbow%(prev)s.translateX;
	$v2[1] = %(name)s_Elbow%(curr)s.translateY - %(name)s_Elbow%(prev)s.translateY;
	$v2[2] = %(name)s_Elbow%(curr)s.translateZ - %(name)s_Elbow%(prev)s.translateZ;
	float $mag = sqrt ( $v2[0]*$v2[0] + $v2[1]*$v2[1] + $v2[2]*$v2[2] );
	float $angleData[] = `angleBetween -v1 $v1[0] $v1[1] $v1[2] -v2 $v2[0] $v2[1] $v2[2] `;
	float $angle = $angleData[3];

	if ( !equivalentTol($angle,180.0, 0.1) ) 
	{
	float $jointDeg = 180 - $angle;
	float $jointRad = -1 * deg_to_rad( $jointDeg );
	%(name)s_Bend%(curr)s.curvature = $jointRad/2;

	%(name)s_ElbowTweak%(curr)s.rotateZ = $jointDeg/2;
	%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s = %(name)s_Jnt%(prev)s.pipeLength;
	float $pipeLength = %(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s;

	float $centerAngleRad = deg_to_rad(90 -$angle/2);
	float $delta = 0;
	float $pipeLengthRatio = 1;

	if ($centerAngleRad > 0.0) {
		float $radius = .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s/ $centerAngleRad;
		$delta = $radius - ($radius * cos( $centerAngleRad ));
		$pipeLengthRatio = .5 * $pipeLength / ( $radius * sin( $centerAngleRad ) );
		$pipeLength *= $pipeLengthRatio;
	}
	%(name)s_PipeDummy%(curr)s.translateX = -1*$delta;

	%(name)s_BendHandle%(curr)s.scaleX = .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s;
	%(name)s_BendHandle%(curr)s.scaleY = %(name)s_BendHandle%(curr)s.scaleX;
	%(name)s_BendHandle%(curr)s.scaleZ = %(name)s_BendHandle%(curr)s.scaleX;

	%(name)s_JntGeo%(curr)s.scaleY = $pipeLength * (1.0+%(name)s_Jnt%(curr)s.pipeLeadIn);
	%(name)s_JntGeo%(curr)s.scaleX = %(name)s_Jnt0.globalPipeRadius + %(name)s_Jnt0.globalJointRadius;
	%(name)s_JntGeo%(curr)s.scaleZ = %(name)s_JntGeo%(curr)s.scaleX;
	%(name)s_JntGeo%(curr)s.visibility = 1;
	%(name)s_Connector1BGeo%(curr)s.visibility=1;
	%(name)s_Connector2BGeo%(curr)s.visibility=1;
	}
	else
	{
	%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s = 0;
	%(name)s_JntGeo%(curr)s.scaleY = 0;
	%(name)s_JntGeo%(curr)s.visibility = 0;
	%(name)s_Connector1BGeo%(curr)s.visibility=0;
	%(name)s_Connector2BGeo%(curr)s.visibility=0;
	}
	%(name)s_Connector1AGeo%(curr)s.scaleY = %(name)s_Jnt0.globalConnectorThickness * (1/%(name)s_Geo%(curr)s.scaleY);
	%(name)s_Connector2AGeo%(curr)s.scaleY = %(name)s_Connector1AGeo%(curr)s.scaleY;
	%(name)s_Connector1AGeo%(curr)s.translateY = -.5 + %(name)s_Connector1AHist%(curr)s.height/2 + .1*%(name)s_Jnt0.globalConnectorOffset;
	%(name)s_Connector2AGeo%(curr)s.translateY = 0.5 - %(name)s_Connector1AHist%(curr)s.height/2 - .1*%(name)s_Jnt0.globalConnectorOffset;
	%(name)s_Connector1AGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector1AGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2AGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2AGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;

	%(name)s_Connector1BGeo%(curr)s.scaleY = %(name)s_Jnt0.globalConnectorThickness * (1/%(name)s_Geo%(curr)s.scaleY);
	%(name)s_Connector2BGeo%(curr)s.scaleY = %(name)s_Connector1BGeo%(curr)s.scaleY;
	%(name)s_Connector1BGeo%(curr)s.translateY = -.5 + %(name)s_Connector1BHist%(curr)s.height/2 - .1*%(name)s_Jnt0.globalConnectorOffset - .1*%(name)s_Connector1BGeo%(curr)s.scaleY;
	%(name)s_Connector2BGeo%(curr)s.translateY = 0.5 - %(name)s_Connector1BHist%(curr)s.height/2 + .1*%(name)s_Jnt0.globalConnectorOffset + .1*%(name)s_Connector1BGeo%(curr)s.scaleY;
	%(name)s_Connector1BGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector1BGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2BGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2BGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;

	%(name)s_Geo%(curr)s.scaleY = $mag - .5*%(name)s_Jnt%(curr)s.pipeLengthInBtwn0 - .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s;
	normalize($v2);
	%(name)s_Geo%(curr)s_pointConstraint1.offsetX = .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s * $v2[0];
	%(name)s_Geo%(curr)s_pointConstraint1.offsetY = .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s * $v2[1];
	%(name)s_Geo%(curr)s_pointConstraint1.offsetZ = .5*%(name)s_Jnt%(prev)s.pipeLengthInBtwn%(branch)s * $v2[2];
	""" % { 	'twoPrev' : prev,
				'prev' : 	curr,
				'curr'	: 	new,
				'new'	:	new+1,
				'name': 	name,
				'branch':	branchNum
					
			}
			#print expr
			print 'editing %s_PipeExpr%s' % (name, new)
			#expression( '%s_PipeExpr%s' % (name, curr), e=1, s=expr, ae=1  )
			expression( s=expr, ae=1, n = '%s_PipeExpr%s' % (name, new)  )
		
	
		# special case for first joint
		else:
			expr = """
	float $x = %(newJnt)s.tx;
	float $y = %(newJnt)s.ty;
	float $z = %(newJnt)s.tz;
	float $mag = sqrt ( $x*$x + $y*$y + $z*$z );
	%(name)s_Geo%(curr)s.sy = $mag - .5*%(newJnt)s.pipeLengthInBtwn0;

	%(name)s_Connector1AGeo%(curr)s.scaleY = %(name)s_Jnt0.globalConnectorThickness * 1/%(name)s_Geo%(curr)s.scaleY;
	%(name)s_Connector2AGeo%(curr)s.scaleY = %(name)s_Connector1AGeo%(curr)s.scaleY;
	%(name)s_Connector1AGeo%(curr)s.translateY = -.5 + %(name)s_Connector1AHist%(curr)s.height/2 + .1*%(name)s_Jnt0.globalConnectorOffset;
	%(name)s_Connector2AGeo%(curr)s.translateY = 0.5 - %(name)s_Connector1AHist%(curr)s.height/2 - .1*%(name)s_Jnt0.globalConnectorOffset;
	%(name)s_Connector1AGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector1AGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2AGeo%(curr)s.scaleX = 1 + %(name)s_Jnt0.globalConnectorRadius;
	%(name)s_Connector2AGeo%(curr)s.scaleZ = 1 + %(name)s_Jnt0.globalConnectorRadius;
		""" % { 'newJnt': newJnt, 
				'curr'	: 	new,
				'name': 	name	
			}
			print 'creating %s_PipeExpr1' % (name)
			expression( s=expr, ae=1, n = '%s_PipeExpr1' % (name))
	
		'''	
		expr = """
	%(pipeJnt)s.scaleX = %(root)s.globalPipeRadius + %(root)s.globalJointRadius;
	%(pipeJnt)s.scaleZ = %(pipeJnt)s.scaleX;
	""" % {	'pipeJnt': pipeJnt, 
			'root' : '%s_Jnt0' % (name) }
	
		print 'creating %s_PipeExpr%s' % (name, new)
		expression( s=expr, ae=1, n = '%s_PipeExpr%s' % (name, new))
		'''
	
		pipe.translate.lock()
		pipe.rotate.lock()
		#pipe.scale.lock()
		newJnts.append( newJnt )
	select(newJnts)

class pipeGenWin(object):
	
	def __init__(self):
		try:
			deleteUI( 'PipeGenWin' )
		except: pass
	
		win = window('PipeGenWin')
		with win:
			with columnLayout():	
				with frameLayout( l='Creation', labelVisible=False):
					with columnLayout():		
						with rowLayout( nc=3, cw3=[80, 80, 240], cal=([1,'center'], [2,'right'])):
							button( l='Create', w=80, c= lambda *args: self.newPipeCB())	
							text( l='Name' )
							self.createGrp = textField( text='pipe', w=90)
						separator(w=400)
				
						with rowLayout( nc=2, cw2=[80, 320], cal=[1,'center']):
							#text( l='Segments' )
							button( l='Extend', w=80, c = lambda *args: self.extendPipeCB() )
							self.numSegments = intSliderGrp(
								cw3=[80,40,50],
								l='Segments',
								value=1,
								field=1,
								min=1, max=20 )
				
				with frameLayout( l='Pipe Properties', labelVisible=True):
					with columnLayout():
						self.pipeRadius = floatSliderGrp( l='Radius', 
							value=.22,
							field=True,
							precision = 3,
							min=.0001, max=10 )
						self.subdivAxis = intSliderGrp( l='Axis Segments', 
							value=16,
							field=True,
							min=3, max=80 )	
						
				with frameLayout( l='Connector Properties', labelVisible=True):
					with columnLayout():
						self.connectorRadius = floatSliderGrp( l='Connector Radius', 
							value=.1,
							field=True,
							precision = 3,
							min=0, max=10 )		
						self.connectorThickness = floatSliderGrp( l='Connector Height', 
							value=.2,
							field=True,
							precision = 3,
							min=.001, max=10 )
						self.connectorOffset = floatSliderGrp( l='Connector Offset', 
							value=.001,
							field=True,
							precision = 3,
							min=0, max=4 )
		
				with frameLayout( l='Joint Properties', labelVisible=True):
					with columnLayout():	
						self.jointRadius = floatSliderGrp( l='Radius', 
							value=0,
							field=True,
							precision = 3,
							min=0, max=10 )
						self.subdivJoint = intSliderGrp( l='Joint Segments', 
							value=8,
							field=True,
							min=1, max=80 )	
						self.jointLength = floatSliderGrp( l='Joint Length', 
							value=1.2,
							field=True,
							precision = 3,
							min=0.0001, max=10 )

		
	def newPipeCB(self):
		
		kwargs={}
		kwargs['pipeRadius'] = self.pipeRadius.getValue()
		kwargs['jointRadius'] = self.jointRadius.getValue()
		kwargs['subdivAxis'] = self.subdivAxis.getValue()
		kwargs['subdivJoint'] = self.subdivJoint.getValue()
		kwargs['jointLength'] = self.jointLength.getValue()
		kwargs['connectorRadius'] = self.connectorRadius.getValue()
		kwargs['connectorThickness'] = self.connectorThickness.getValue()
		kwargs['connectorOffset'] = self.connectorOffset.getValue()
		startPipe( self.createGrp.getText(), **kwargs )
		
	def extendPipeCB(self):
		kwargs={}
		kwargs['jointLength'] = self.jointLength.getValue()
		for i in range( self.numSegments.getValue() ):
			extendPipe(**kwargs)


"""
TODO

Fixed Joints:
Y-joints
T-joints
Straight joint

Size change Adapter

"""




