
import pymel
from pymel import *
from pymel.datatypes import *
from time import time
import unittest

def doIt(obj):
    colors = []
    for i, vtx in enumerate(obj.vtx):
        #iterate through vertices
        #print vtx, vtx._range, vtx.getIndex(), vtx.getPosition()
        edgs=vtx.toEdges()
        totalLen=0
        edgCnt=0
        for edg in edgs:
            edgCnt += 1
            #print edg
            #print "getting length"
            l = edg.getLength()
            #print "length", l
            totalLen += l
#                
#                 verts=edg.toVertices()
#                
#                 pOne=verts[0].getPosition()
#                 pTwo=verts[1].getPosition()
#                 pDif = pOne - pTwo
#
#                 totalLen += pDif.mag()
   
        avgLen=totalLen / edgCnt
        #print avgLen
       
        currColor = vtx.getColor(0)
        color = Color.black
        # only set blue if it has not been set before
        if currColor.b<=0.0:
            color.b = avgLen
        color.r = avgLen
        colors.append(color)


    print len(colors)
    obj.setVertexColors( colors, xrange(len(colors)) )
    obj.updateSurface()
       
    polyColorPerVertex( obj, e=1, colorDisplayOption=1 )
