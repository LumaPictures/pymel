# script created by pymel.melparse.mel2py from mel file:
# /Volumes/luma/_globalSoft/mel/published/luma5.0/luma/texture/texturePathUI.mel

# this is the UI after it has been modified to use some of pymel's special ui features.

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
def substituter(ignoreCase,match,input_,replace):
	if ignoreCase:
		inputStr=input_.lower()
		matchStr=match.lower()
		if mel.gmatch(inputStr, ("*" + matchStr + "*")):
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

	try:
		deleteUI("textureFindWindow", window=True)
	except:
		pass
			
	win = window("textureFindWindow")
	win.setTitle("Find & Replace Texture Paths")
	
	form = formLayout()
	column = columnLayout(adj = 1,rowSpacing = 4)
	rowLayout(adj=2,
		nc=2,
		cw=(1, 60),
		cat=(1, "both", 2))
		
	text(l="Find:")
	textField('findField',ec=lambda *args: lm_Find() )
	setParent('..')
	
	rowLayout(adj=2,
		nc=2,
		cw=(1, 60),
		cat=(1, "both", 2))
	text(l="Replace:")
	textField('replaceField',ec=lambda *args: lm_Replace() )
	setParent('..')
	setParent('..')
	
	row = rowLayout(numberOfColumns = 5,cw5 = (60, 72, 72, 150, 80))
	columnLayout()
	button(align="center",c=lambda *args: lm_Find(),label="Find")
	setParent('..')
	
	columnLayout()
	button(align="center",c=lambda *args: lm_Replace(0),label="Replace")
	# rename off
	setParent('..')
	
	columnLayout()
	button(align="center",c=lambda *args: lm_Replace(1),label="Rename")
	# rename on
	setParent('..')
	
	columnLayout()
	radioButtonGrp('allCheckBox',
		nrb=2,
		cw2=(80, 60),
		la2=("selected", "all"),
		sl=1)
	setParent('..')
	
	columnLayout()
	checkBox('caseSensativeBox',l="ignore case",v=1)
	setParent('..')
	setParent('..')
	
	row2 = rowLayout(nc = 2,cw = (1, 60))
	text(l="matches: ")
	text('numMatchesText',align="left",l=" ")
	setParent('..')
	
	pane = paneLayout()

	textScrollList('selectionList',
		allowMultiSelection=True,
		dcc=lambda *args: lm_DoubleClickCommand(),
		dkc=lambda *args: lm_DeleteKeyCommand())
		
	form.attachControl	(row, "top", 5, column)
	form.attachForm		(row, "left", 20)
	form.attachForm		(row, "right", 5)
	
	form.attachForm		(row2, "left", 20)
	form.attachForm		(row2, "right", 5)
	form.attachControl	(row2, "top", 5, row)
	
	form.attachControl	(pane, "top", 5, row2)
		
	form.attachForm		(column, "top", 5)
	form.attachForm		(column, "left", 5)
	form.attachForm		(column, "right", 5)

	form.attachForm		(pane, "left", 5)
	form.attachForm		(pane, "right", 5)
	form.attachForm		(pane, "bottom", 5)
	
	win.show()
	

def lm_Replace(rename):
	global foundTexNodeArray
	findPath = textField('findField').getText()
	
	findPath = mel.fromNativePath(findPath)
	# Added Windows Slash Support - by Hays Clark
	if not len(findPath):
		confirmDialog(b="OK",m="You Must Enter Text to Find",t="Warning")
		return 
		
	replacePath = textField('replaceField').getText()
	
	# Added Windows Slash Support - by Hays Clark
	replacePath = mel.fromNativePath(replacePath)
	ignoreCase = checkBox('caseSensativeBox').getValue()
	
	# Get File Paths //
	selList = textScrollList('selectionList')
	filePathArray = selList.getAllItems()
	
	# Get Indices of Selected Items //
	indexArray = []
	# do all
	if radioButtonGrp('allCheckBox').getSelect() - 1:
		indexArray = range(1,selList.getNumberOfItems()+1)

	else:
		indexArray=selList.getSelectIndexedItem()
		# Do the Operation
		
	for index in indexArray:
		oldFilePath = foundTexNodeArray[index].ftn.get()
		# string $filePath = $filePathArray[$index-1];
		filePath = substituter(ignoreCase, findPath, oldFilePath, replacePath)
		if rename:
			if MFile(oldFilePath).access(os.W_OK):
				sysFile(oldFilePath,ren=filePath)
				# sysFile requires the new name to come first
				foundTexNodeArray[index].ftn.set(filePath)
				
			
			else:
				mel.warning(oldFilePath + " does not exist or is not writable. Skipping file rename.\n")
				filePath=oldFilePath
						
		else:
			foundTexNodeArray[index].ftn.set(filePath)
			# Replace old Path with New Path, converting from 1-based to 0-based index //
			
		filePathArray[index-1] = filePath
		
	selList.removeAll()
	
	# Clear List //
	# Rebuild List //
	selList.extend(filePathArray)
	
	# Reselect the Items that were changed //	
	selList.selectIndexedItems(indexArray)
		
	return 
	

def lm_Find():
	selList = textScrollList('selectionList')
	selList.removeAll()
	
	# Initialize and Clear Array in which to store Matches //
	global foundTexNodeArray
	foundTexNodeArray=[]
	findPath = textField('findField').getText()

	#  determine if it is a case sensative search //
	ignoreCase = checkBox('caseSensativeBox').getValue()
	if ignoreCase == 1:
		findPath=findPath.lower()
		
	foundTexNodeArray.append(0)
	for elem in ls(typ="file"):
		filePath = elem.ftn.get()
		if ignoreCase == 1:
			filePath2=filePath.lower()
				
		else:
			filePath2=filePath
			
		if findPath in filePath2:
			selList.append(filePath)
			# Update Scroll List with Path //
			# Store Corresponding File Node //
			foundTexNodeArray.append(elem)
			
		
	numMatch = len(foundTexNodeArray)
	if numMatch>0:
		numMatch-=1
		
	text('numMatchesText').setLabel(numMatch)
	

def lm_DoubleClickCommand():
	global foundTexNodeArray
	index = textScrollList('selectionList',q = 1,sii = 1)
	foundTexNodeArray[index[0]].select()
	mel.showEditor(foundTexNodeArray[index[0]])
	

def lm_DeleteKeyCommand():
	selList = textScrollList('selectionList')
	indexArray = selList.getSelectIndexedItem()
	selList.removeIndexedItem(indexArray)

def lm_SelectAll():
	textScrollList('selectionList').selectAll()		
	

def lm_DeselectAll():
	textScrollList('selectionList').deselectAll()
	

texturePathUI()
