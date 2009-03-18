# script created by pymel.melparse.mel2py from mel file:
# /Users/chad/Documents/dev/python/_published/pymel/examples/texturePathUI.mel

from pymel import *
import os
"""/////////////////////////////////////////////////////////////////////////////
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	Find & Replace Texture Paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Developed by	:	Chad Dombrova
Production		:	Luma Pictures, Inc.  www.luma-pictures.com
Related Project	:	All

Description :
Script for doing find and replace operations on texture paths.

Usage :
Enter text to search for.  After results are displayed you may select certain paths
to perform replace on (shift select to do multiple) or check the 'all' button to operate
on all found paths.

Version History :
- 1.3	Added case sensitivity to replace; Added Windows Slash Support (thanks Hays)
- 1.2	Added Enter Command for both Find and Replace functions
- 1.1	Fixed Number of Matches off by one
		Fixed Error on double click when AE is already open
- 1.0

To Do :
- Either move replaced paths to another pane, or add a symbol, change color, or change font so
	that they are not confused with paths that have not been operated on
- Progress Bar
- Update List doesn't seem to work correctly
- Status Bar showing the node associated with the found text


/////////////////////////////////////////////////////////////////////////////"""
# subsutition with case sensitivity controls
def substituter(ignoreCase, match, input_, replace):
	if ignoreCase:
		inputStr=input_.lower()
		matchStr=match.lower()
		if mel.gmatch(inputStr, ("*" + str(matchStr) + "*")):
			inputLen = len(inputStr)
			matchLen = len(matchStr)
			i = 0
			for i in range(1,(inputLen + 1 - matchLen)):
				tmpStr = inputStr[i-1:i + matchLen - 1-1]
				#				print $tmpStr; print "\n";
				if mel.gmatch(tmpStr, matchStr):
					break
					
				
			returnStr = ''
			#			print $i; print "\n";
			if i>1:
				returnStr=input_[0:i - 1-1]
				#			print $returnStr; print "\n";
				
			returnStr+=replace
			if i + matchLen<inputLen:
				returnStr+=input_[i + matchLen-1:inputLen-1]
				# add on the remaining string, if it exists
				
			return returnStr
			
		
		else:
			return mel.substitute(match, input_, replace)
			
		
	
	else:
		return mel.substitute(match, input_, replace)
		
	

def texturePathUI():
	textureFindWindow = "textureFindWindow"
	if window(textureFindWindow,exists=1):
		deleteUI(textureFindWindow)
		
	window(textureFindWindow,title="Find & Replace Texture Paths")
	form = formLayout()
	column = columnLayout(adj=1,rowSpacing=4)
	rowLayout(adj=2,nc=2,cw=(1, 60),cat=(1, "both", 2))
	text(l="Find:")
	textField('findField',ec=lambda *args: mm.eval('lm_Find'))
	setParent('..')
	rowLayout(adj=2,nc=2,cw=(1, 60),cat=(1, "both", 2))
	text(l="Replace:")
	textField('replaceField',ec=lambda *args: mm.eval('lm_Replace'))
	setParent('..')
	setParent('..')
	row = rowLayout(numberOfColumns=5,
		cw5=(60, 72, 72, 150, 80))
	columnLayout()
	button(align="center",c=lambda *args: mm.eval("lm_Find"),label="Find")
	setParent('..')
	columnLayout()
	button(align="center",c=lambda *args: mm.eval("lm_Replace 0"),label="Replace")
	# rename off
	setParent('..')
	columnLayout()
	button(align="center",c=lambda *args: mm.eval("lm_Replace 1"),label="Rename")
	# rename on
	setParent('..')
	columnLayout()
	radioButtonGrp('allCheckBox',nrb=2,cw2=(80, 60),la2=("selected", "all"),w=140,sl=1)
	setParent('..')
	columnLayout()
	checkBox('caseSensativeBox',l="ignore case",v=1)
	setParent('..')
	setParent('..')
	row2 = rowLayout(nc=2,cw=(1, 60))
	text(l="matches: ")
	text('numMatchesText',align="left",l=" ")
	setParent('..')
	pane = paneLayout()
	'''-configuration "vertical2"'''
	textScrollList('selectionList',
		allowMultiSelection=True,
		dcc=lambda *args: mm.eval('lm_DoubleClickCommand'),
		dkc=lambda *args: mm.eval('lm_DeleteKeyCommand'))
	formLayout(form,
		edit=1,
		attachControl=[(row, "top", 5, column), (row2, "top", 5, row), (pane, "top", 5, row2)],
		attachForm=[(column, "top", 5), (column, "left", 5), (column, "right", 5), (row, "left", 20), (row, "right", 5), (row2, "left", 20), (row2, "right", 5), (pane, "left", 5), (pane, "right", 5), (pane, "bottom", 5)])
	showWindow()
	

def lm_Replace(rename):
	global foundTexNodeArray
	findPath = textField('findField',q=1,text=1)
	findPath=mel.fromNativePath(findPath)
	# Added Windows Slash Support - by Hays Clark
	if not len(findPath):
		confirmDialog(b="OK",m="You Must Enter Text to Find",t="Warning")
		return 
		
	replacePath = textField('replaceField',q=1,text=1)
	replacePath=mel.fromNativePath(replacePath)
	# Added Windows Slash Support - by Hays Clark
	ignoreCase = checkBox('caseSensativeBox',q=1,v=1)
	# Get File Paths //
	filePathArray = textScrollList('selectionList',q=1,allItems=1)
	# Get Indices of Selected Items //
	indexArray = []
	# do all
	if radioButtonGrp('allCheckBox',q=1,sl=1) - 1:
		i = 0
		for i in range(0,textScrollList('selectionList',q=1,numberOfItems=1)):
			indexArray[i]=i + 1
			
		
	
	else:
		indexArray=textScrollList('selectionList',q=1,selectIndexedItem=1)
		# Do the Operation
		
	for index in indexArray:
		oldFilePath = getAttr(str(foundTexNodeArray[index]) + ".ftn")
		# string $filePath = $filePathArray[$index-1];
		filePath = substituter(ignoreCase, findPath, oldFilePath, replacePath)
		if rename:
			if Path(oldFilePath).access(os.W_OK):
				Path(oldFilePath).move(filePath)
				# sysFile requires the new name to come first
				setAttr((str(foundTexNodeArray[index]) + ".ftn"),filePath,type="string")
				
			
			else:
				mel.warning(oldFilePath + " does not exist or is not writable. Skipping file rename.\n")
				filePath=oldFilePath
				
			
		setAttr((str(foundTexNodeArray[index]) + ".ftn"),filePath,type="string")
		# Replace old Path with New Path, converting from 1-based to 0-based index //
		filePathArray[index - 1]=filePath
		
	textScrollList('selectionList',removeAll=1,e=1)
	# Clear List //
	# Rebuild List //
	for filePath in filePathArray:
		textScrollList('selectionList',e=1,append=filePath)
		# Reselect the Items that were changed //
		
	for index in indexArray:
		textScrollList('selectionList',selectIndexedItem=index,e=1)
		
	return 
	

def lm_Find():
	textScrollList('selectionList',removeAll=1,e=1)
	# Initialize and Clear Array in which to store Matches //
	global foundTexNodeArray
	foundTexNodeArray=[]
	findPath = textField('findField',q=1,text=1)
	texnode=(ls(typ="file"))
	#  determine if it is a case sensative search //
	ignoreCase = checkBox('caseSensativeBox',q=1,v=1)
	if ignoreCase == 1:
		findPath=findPath.lower()
		
	i = 1
	for elem in texnode:
		filePath = (getAttr(str(elem) + ".ftn"))
		if ignoreCase == 1:
			filePath2=filePath.lower()
			
		
		else:
			filePath2=filePath
			
		if mel.gmatch(filePath2, ("*" + findPath + "*")):
			textScrollList('selectionList',e=1,append=filePath)
			# Update Scroll List with Path //
			# Store Corresponding File Node //
			foundTexNodeArray[i]=elem
			i+=1
			
		
	numMatch = len(foundTexNodeArray)
	if numMatch>0:
		numMatch-=1
		
	text('numMatchesText',align="left",e=1,l=numMatch)
	

def lm_DoubleClickCommand():
	global foundTexNodeArray
	index = textScrollList('selectionList',q=1,sii=1)
	select(foundTexNodeArray[index[0]])
	mel.showEditor(foundTexNodeArray[index[0]])
	

def lm_DeleteKeyCommand():
	indexArray = textScrollList('selectionList',q=1,sii=1)
	for index in indexArray:
		textScrollList('selectionList',e=1,rii=index)
		
	

def lm_SelectAll():
	numberOfItems = textScrollList('selectionList',q=1,numberOfItems=1)
	i = 1
	for i in range(i,numberOfItems+1):
		textScrollList('selectionList',sii=i,e=1)
		
	

def lm_DeselectAll():
	textScrollList('selectionList',e=1,da=1)
	

texturePathUI()
