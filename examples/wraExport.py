from pymel import *

"""
The WRa files reads as follows.

NBELEMS ? - The number of elements
ELEM_NAMES - Name of each element

Each possible animation axis is given an attribute number listed in an index, for example ETRNX(translation in x axis) is number 3

the raw data line read as, RAw_DATA, FRAME NUMBER, element number(in this case 0,1 or 2 for camera, interest or up_vector), attribute number, attribute value



So therefore when you read the 1st RAW_DATA line of the 1_metre_cube_cam.wra file

RAW_DATA	1	0	0	12.044739

it says the following

at frame 1 the camera element x rotation value is  12.044739


when you read the 13th RAW_DATA line of the 1_metre_cube_cam.wra file

RAW_DATA	1	1	3	-2.566832

it says the following 

at frame  1 the interest element x translation value is -2.566832
"""

def wraExport( outFile=None, tag=''):
	
	if not outFile:
		if tag:
			outFile = sceneName().stripext() + '_' + tag + '.wra'
		else:
			outFile = sceneName().stripext() + ".wra"
	
	f = open( outFile, 'w')
	# get anim start, end from time slider
	start = env.getMinTime()
	end = env.getMaxTime()
	objs = selected()
	print "Writing out anim for frames %d-%d to %s" % (start, end, outFile)

	# header
	f.write( """#
#
# Scene name : %s
# 
#
""" %  sceneName() )

	# object and element list
	f.write( 'NBELEMS %d\n' % len(objs) )
	f.write( 'ELEM_NAMES %s\n' % (' '.join(objs)) )
	f.write( """# Attribute index
#    0 : ROTX
#    1 : ROTY
#    2 : ROTZ
#    3 : ETRNX
#    4 : ETRNY
#    5 : ETRNZ
#    6 : SCALX
#    7 : SCALY
#    8 : SCALZ
SAVED_ATTRS 0 1 2 3 4 5 6 7 8
""")

	# data
	for frame in range( int(start), int(end)+1):
		currentTime( frame )
		for i, obj in enumerate( objs ):
			
			attrs = []
			# we use getTranslation and getRotation to ensure that we get the values in world space
			attrs.extend( obj.getRotation( ws=1 ) )
			attrs.extend( obj.getTranslation( ws=1 ) ) 
			attrs.extend( obj.scale.get() )
			#attrs.extend( [1.0,1.0,1.0] )
			
			for j, attr in enumerate(attrs):
				#print 'RAW_DATA\t%d\t%d\t%d\t%f' % ( frame, i, j, attr )
				f.write( 'RAW_DATA\t%d\t%d\t%d\t%f\n' % ( frame, i, j, attr ) )
	
	f.close()
	print "finished"


def emberExport():
	# export camera anim
	try:
		select('conCam')	
	except:
		print "camera must be named 'conCam'"
	else:
		wraExport(tag='cam')
	
	# export boat anim
	try:
		ls( 'mineCar_dup', r=1)[0].select()		
	except:
		print "boat must be named 'mineCar_dup' (but it can be in any namespace)"
	else:
		wraExport(tag='boat')
				
	