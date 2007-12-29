"""
	string $objs[] = `ls -type transform`;
	for ($x in $objs) {
		print (longNameOf($x)); print "\n";	
		
		// make and break some connections
		connectAttr( $x + ".sx") ($x + ".sy");
		connectAttr( $x + ".sx") ($x + ".sz");
		disconnectAttr( $x + ".sx") ($x + ".sy");
		string $conn[] = `listConnections -s 0 -d 1 -p 1 ($x + ".sx")`;
		for ($inputPlug in $conn)
			disconnectAttr ($x + ".sx") $inputPlug;
		
		// add and set a string array attribute with the history of this transform's shape
		if ( !`attributeExists "newAt" $x`)
			addAttr -ln newAt -dataType stringArray $x;
		string $shape[] = `listRelatives -s $x`;
		string $history[] = `listHistory $shape[0]`;
		string $elements = "";
		for ($elem in $history) 
			$elements += "\"" + $elem + "\" ";
		eval ("setAttr -type stringArray " + $x + ".newAt " + `size $history` + $elements);
		print `getAttr ( $x + ".newAt" )`;
		
		// get and set some attributes
		setAttr ($x + ".rotate") 1 1 1;
		float $trans[] = `getAttr ($x + ".translate")`;
		float $scale[] = `getAttr ($x + ".scale")`;
		$trans[0] *= $scale[0];
		$trans[1] *= $scale[1];
		$trans[2] *= $scale[2];
		setAttr ($x + ".scale") $trans[0] $trans[1] $trans[2];	
		
		// call some other scripts	
		myMelScript( `nodeType $x`, $trans );
	}
"""
import maya.mel as mm
import maya.cmds as cmds

mm.eval("""
global proc myMelScript( string $type, float $val[] )
{ print $val; }
""")

def defaultPython():

	objs = cmds.ls( type= 'transform') 
	if objs is not None:					# returns None when it finds no matches
		for x in objs:
			print mm.eval('longNameOf("%s")' % x)
			
			# make and break some connections
			cmds.connectAttr(   '%s.sx' % x,  '%s.sy' % x )
			cmds.connectAttr(   '%s.sx' % x,  '%s.sz' % x )
			cmds.disconnectAttr( '%s.sx' % x,  '%s.sy' % x)

			conn = cmds.listConnections( x + ".sx", s=0, d=1, p=1)
			# returns None when it finds no matches
			if conn is not None:				
				for inputPlug in conn:
					cmds.disconnectAttr( x + ".sx", inputPlug )
			
			# add and set a string array attribute with the history of this transform's shape
			if not mm.eval( 'attributeExists "newAt" "%s"' % x): 
				cmds.addAttr(  x, ln='newAt', dataType='stringArray')
			shape = cmds.listRelatives( x, s=1 )
			if shape is not None:
				history = cmds.listHistory( shape[0] )
			else:
				history = []
			args = tuple( ['%s.newAt' % x, len(history)] + history )
			cmds.setAttr( *args ,  **{ 'type' : 'stringArray' } )
			print cmds.getAttr ( x + ".newAt" )

			# get and set some attributes
			cmds.setAttr ( '%s.rotate' % x, 1,  1, 1 )
			scale = cmds.getAttr ( '%s.scale' % x )
			scale = scale[0] # maya packs the previous result in a list for no apparent reason
			trans = list( cmds.getAttr ( '%s.translate' % x )[0] )  # the tuple must be converted to a list for item assignment
			trans[0] *= scale[0]
			trans[1] *= scale[1]
			trans[2] *= scale[2]
			cmds.setAttr ( '%s.scale' % x, trans[0], trans[1], trans[2] )
			mm.eval('myMelScript("%s",{%s,%s,%s})' % (cmds.nodeType(x), trans[0], trans[1], trans[2]) )
			
def pymelPython():
	from pymel import *                   # safe to import into main namespace
	for x in ls( type='transform'):
		print x.longName()                # object oriented design
		
		# make and break some connections
		x.sx >> x.sy                      # connection operator	
		x.sx >> x.sz	
		x.sx <> x.sy                      # disconnection operator
		x.sx.disconnect()                 # smarter methods -- (automatically disconnects all inputs and outputs when no arg is passed)
		
		# add and set a string array attribute with the history of this transform's shape
		if not x.newAt.exists():
			x.newAt.add( dataType='stringArray')
		x.newAt = x.getShape().history()
		
		# get and set some attributes
		x.rotate =  [1,1,1]	
		trans = x.attr('translate').get()
		trans *= x.scale.get()           # vector math
		x._translate = trans              # ability to pass list/vector args
		mel.myMelScript( x.type(), trans) # automatic handling of mel commands

defaultPython()
pymelPython()
