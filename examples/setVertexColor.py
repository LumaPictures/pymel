
import pymel.all as pymel
import pymel.core as pm
from pymel.core.datatypes import *
from time import time
import unittest

def doIt(obj):
    obj.createColorSet('edgeLength')
    colors = []
    for i, vtx in enumerate(obj.vtx):
        #iterate through vertices
        #print vtx, vtx._range, vtx.getIndex(), vtx.getPosition()
        edgs = vtx.connectedEdges()
        totalLen=0
        edgCnt=0
        for edg in edgs:
            edgCnt += 1
            #print edg
            #print "getting length"
            l = edg.getLength()
            #print "length", l
            totalLen += l

        avgLen=totalLen / edgCnt

        currColor = vtx.getColor()
        color = pm.dt.Color.black
        # only set blue if it has not been set before
        if currColor.b<=0.0:
            color.b = avgLen
        color.r = avgLen
        colors.append(color)


    print len(colors)
    obj.setColors( colors )
    obj.updateSurface()

    pm.polyColorPerVertex( obj, e=1, colorDisplayOption=1 )