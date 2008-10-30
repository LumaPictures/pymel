"""
UI for controlling how api classes and mel commands are combined into pymel classes.

This UI modifies factories.apiToMelData which is pickled out to apiMelBridge.

It controls:
    which mel methods correspond to api methods
    disabling of api methods
    preference for overloaded methods (since currently only one overloaded method is supported)
    renaming of apiMethod


"""
 
from pymel import *
import inspect, re, os, pickle

frame_width = 800
          
class PymelControlPanel(object):
    def __init__(self):
        self.win = window(title='Pymel Control Panel')
        
        self.pane = paneLayout(configuration='vertical3', paneSize=([1,20,100], [3,20,100]) )
        
        # Lef Column: Api Classes
        self.classScrollList = textScrollList('apiClassList')
        setParent('..')
        
        # Center Column: Api Methods
        apiForm = formLayout()
        scroll = scrollLayout()
        #apiMethodForm = formLayout()
        self.apiMethodCol = columnLayout('apiMethodCol', rowSpacing=12)
        #apiMethodForm.attachForm( self.apiMethodCol, 'top', 2 )
        #apiMethodForm.attachForm( self.apiMethodCol, 'bottom', 2 )
        #apiMethodForm.attachForm( self.apiMethodCol, 'right', 2 )
        #apiMethodForm.attachForm( self.apiMethodCol, 'left', 2 )
        
        setParent('..') # column
        #setParent('..') # form
        setParent('..') # scroll
        status = helpLine(h=60)
        setParent('..') # form
        
        apiForm.attachForm( status, 'bottom', 5 )
        apiForm.attachForm( status, 'left', 5 )
        apiForm.attachForm( status, 'right', 5 )
        apiForm.attachForm( scroll, 'top', 5 )
        apiForm.attachForm( scroll, 'left', 5 )
        apiForm.attachForm( scroll, 'right', 5 )
        apiForm.attachControl( scroll, 'bottom', 5, status )
        
        # Right Column: Mel Methods
        melForm = formLayout()
        label1 = text( label='Unassigned Mel Methods' )
        self.unassignedMelMethodLister = textScrollList()
        label2 = text( label='Assigned Mel Methods' )
        self.assignedMelMethodLister = textScrollList()
        
        melForm.attachForm( label1, 'top', 5 )
        melForm.attachForm( label1, 'left', 5 )
        melForm.attachForm( label1, 'right', 5 )

        melForm.attachControl( self.unassignedMelMethodLister, 'top', 0, label1 )
        melForm.attachForm( self.unassignedMelMethodLister, 'left', 5 )
        melForm.attachForm( self.unassignedMelMethodLister, 'right', 5 )
        melForm.attachPosition( self.unassignedMelMethodLister, 'bottom', 5, 50 )
        
        melForm.attachControl( label2, 'top', 5,  self.unassignedMelMethodLister)
        melForm.attachForm( label2, 'left', 5 )
        melForm.attachForm( label2, 'right', 5 )
        
        melForm.attachControl( self.assignedMelMethodLister, 'top', 0, label2 )
        melForm.attachForm( self.assignedMelMethodLister, 'left', 5 )
        melForm.attachForm( self.assignedMelMethodLister, 'right', 5 )
        melForm.attachForm( self.assignedMelMethodLister, 'bottom', 5 )
        
        setParent('..')
        
        # key is a tuple of (class, method)
        self.classList = sorted( list( set( [ key[0] for key in factories.apiToMelData.keys()] ) ) )
        
        self.classScrollList.extend( self.classList )
        self.classScrollList.selectCommand( lambda: self.apiClassList_selectCB() )
        self.classFrames={}
        self.processClassFrames()
        
        scriptJob(uiDeleted=[str(self.win),cacheResults])
        
        self.win.show()

    
            
    @staticmethod    
    def getMelMethods(className):
        reg = re.compile('(.*[a-z])([XYZ])$')
        newlist = []
        origlist = factories.apiToMelMap['mel'][className]
        for method in origlist:
            m = reg.search(method)
            if m:
                newname = m.group(1) + '*'
                if newname not in newlist:
                    newlist.append(newname)
            else:
                newlist.append(method)
        return sorted(newlist)
       
    def apiClassList_selectCB(self, *args):
        sel = self.classScrollList.getSelectItem()
        if sel:
            self.buildClassColumn(sel[0])
    

    
    def assignMelMethod(self, method):
        #print "method %s is now assigned" % method
        if method in util.listForNone( self.unassignedMelMethodLister.getAllItems() ):
            self.unassignedMelMethodLister.removeItem(method)
            self.assignedMelMethodLister.append( method )
        
    def unassignMelMethod(self, method):
        #print "method %s is now unassigned" % method
        if method in util.listForNone( self.assignedMelMethodLister.getAllItems() ):
            self.assignedMelMethodLister.removeItem(method)
            self.unassignedMelMethodLister.append( method )
    

            
    def processClassFrames(self):
        """
        This triggers the generation of all the defaults for `factories.apiToMelData`, but it does
        not create any UI elements.  It creates `ClassFrame` instances, which in turn create
        `MethodRow` instances, but the creation of UI elements is delayed until a particular
        configuration is requested via `buildClassColumn`.
        """
        for className in self.classList:
            melMethods = self.getMelMethods(className)
            for clsName, apiClsName in getClassHierarchy(className):
                if apiClsName and apiClsName not in ['list']:
                    if clsName not in self.classFrames:
                        frame = ClassFrame( self, clsName, apiClsName)
                        self.classFrames[clsName] = frame 
                    self.classFrames[clsName].updateMelNames( melMethods )
                 
    def buildClassColumn(self, className ):
        """
        Build an info column for a class.  This column will include processed `ClassFrame`s for it and its parent classes
        """
        setParent(self.apiMethodCol)
        self.apiMethodCol.clear()
        
        self.unassignedMelMethodLister.removeAll()
        self.assignedMelMethodLister.removeAll()
        
        melMethods = self.getMelMethods(className) 
        self.unassignedMelMethodLister.extend( melMethods )
        
        filter = set( ['double', 'MVector'] )
        
        for clsName, apiClsName in getClassHierarchy(className):
            if apiClsName:
                #print cls
                try:
                    self.classFrames[clsName].buildUI(filter)
                    #if i != len(mro)-1:
                    #    frame.setCollapse(True)  
                except KeyError:
                    print "skipping", clsName
                    
        self.classFrames[className].frame.setCollapse(False)     
                

        
class ClassFrame(object):
    def __init__(self, parent, className, apiClassName ):


        self.parent = parent
        self.className = className
        self.apiClassName = apiClassName
        self.rows = {}
        self.classInfo = api.apiClassInfo[apiClassName]['methods']
        
        for method in self.classInfo.keys():
            row = MethodRow( self, self.className, self.apiClassName, method, self.classInfo[method] )

            self.rows[method] = row
        
        
    def updateMelNames(self, melMethods):
        for rowName, row in self.rows.items():
            row.updateMelNames( melMethods )
            
    def buildUI(self, filter=None):
        
        count = 0
        #self.form = formLayout()
        self.frame = frameLayout(collapsable=True, label='%s (%s)' % (self.className, self.apiClassName),
                            width = frame_width,
                            labelAlign='top')
        
        col = columnLayout(visible=False )
        
        invertibles = api.apiClassInfo[self.apiClassName]['invertibles']
        usedMethods = []
        
        for setMethod, getMethod in invertibles:
            frame = frameLayout(labelVisible=False, collapsable=False, width = frame_width)
            col2 = columnLayout()
            pairCount = 0
            pairCount += self.rows[setMethod].buildUI(filter)
            pairCount += self.rows[getMethod].buildUI(filter)
            usedMethods += [setMethod, getMethod]
            if pairCount == 0:
                #deleteUI(col2)
                frame.setVisible(False)
                frame.setHeight(1)
            setParent('..') # frame 
            setParent('..') # column
            count += pairCount
        
        for methodName in sorted( self.classInfo.keys() ):
            if methodName not in usedMethods: 
                count += self.rows[methodName].buildUI(filter)
        
        #self.form.attachForm( self.frame, 'left', 2)
        #self.form.attachForm( self.frame, 'right', 2)
        #self.form.attachForm( self.frame, 'top', 2)
        #self.form.attachForm( self.frame, 'bottom', 2)
        col.setVisible(True)
        setParent('..') # column
        setParent('..') # frame
        #setParent('..') # form
        return count
    

class MethodRow(object):
    def __init__(self, parent, className, apiClassName, apiMethodName, methodInfoList):
    
        
        self.parent = parent
        self.className = className
        self.methodName = methodInfoList[0].get('pymelName', apiMethodName)
        self.apiClassName = apiClassName
        self.apiMethodName = apiMethodName
        self.methodInfoList = methodInfoList
        self.data = factories.apiToMelData[ (self.className, self.methodName ) ]
        self.classInfo = api.apiClassInfo[self.apiClassName]['methods'][self.apiMethodName]
        enabledArray = self.getEnabledArray()
        # DEFAULT VALUES
        


        # enabled
        if not self.data.has_key( 'enabled' ):
            self.data['enabled'] = True
         
        if self.methodName in factories.EXCLUDE_METHODS or sum(enabledArray) == 0:
            self.data['enabled']  = False
        
        
        # useName mode
        if not self.data.has_key( 'useName' ):
            self.data['useName'] = 'API'
        else:
            # correct old values
            useNameVal = self.data['useName']
            if useNameVal == True:
                self.data['useName'] = 'API'
            elif useNameVal == False:
                self.data['useName'] = 'MEL'  
            elif useNameVal not in ['MEL', 'API']:
                self.data['useName'] = str(useNameVal)
        
        # correct old values
        if self.data.has_key('overloadPrecedence'):
            self.data['overloadIndex'] = self.data.pop('overloadPrecedence')
        
        # correct old values
        if self.data.has_key('melName'):
            self.data['melName'] = str(self.data['melName'])
            
                        
        val = self.data.get('overloadIndex', 0)
        # ensure we don't use a value that is not valid
        for val in range(val, len(enabledArray)+1):
            try:
                if enabledArray[val]:
                    break
            except IndexError: # went too far, so none are valid
                val = None
        if val is None:
            # nothing valid
            self.data.pop('overloadIndex', None)
        else:
            self.data['overloadIndex'] = val
 
    def crossReference(self, melName):
        """ create an entry for the melName which points to the data being tracked for the api name"""
        
        factories.apiToMelData[ (self.className, melName ) ] = self.data
        
    def uncrossReference(self, melName):
        factories.apiToMelData.pop( (self.className, melName ) )
          
    def updateMelNames(self, melMethods): 
        # melName   
        if not self.data.has_key( 'melName' ):
            match = None
            for method in melMethods:
                methreg = method.replace('*', '.{0,1}') + '$'
                #print self.methodName, methreg
                if re.match( methreg, self.methodName ):
                    match = str(method)
                    break
            if match:
                self.data['melName'] = match
                self.crossReference( match )
            
    def buildUI(self, filter=None):
        
        if filter:
            match = False
            for info in self.methodInfoList:
                argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, info )
                if filter.intersection( argUtil.getInputTypes() + argUtil.getOutputTypes() ):
                    match = True
                    break
            if match == False:
                return False
            
        #print className, self.methodName, melMethods
        isOverloaded = len(self.methodInfoList)>1
        self.frame = frameLayout(w=frame_width, labelVisible=False, collapsable=False)
        columnLayout()
        enabledArray = []
        self.rows = []
        self.overloadPrecedenceColl = None
        self.enabledChBx = checkBox(label=self.methodName, 
                    changeCommand=CallbackWithArgs( MethodRow.enableCB, self ) )
        
        if isOverloaded:
            rowSpacing = [180, 20, 400]
            self.overloadPrecedenceColl = radioCollection() 
            for i in range(0, len(self.methodInfoList) ) :
                row = rowLayout( '%s_rowMain%s' % (self.methodName,i), nc=3, cw3=rowSpacing )
                self.rows.append(row)
                text(label='')
                self.createAnnotation(i)
                
                setParent('..') 
        else:
            row = rowLayout( self.methodName + '_rowMain', nc=2, cw2=[200, 400] )
            #self.enabledChBx = checkBox(label=self.methodName, changeCommand=CallbackWithArgs( MethodRow.enableCB, self ) )
            text(label='')
            self.createAnnotation(0)
            setParent('..')  
        
        separator(w=800, h=24) 
        
          
        #self.row = rowLayout( self.methodName + '_rowSettings', nc=4, cw4=[200, 160, 180, 160] )
        #self.rows.append(row)
        layout = { 'columnAlign'  : [1,'right'], 
                   'columnAttach' : [1,'right',5] }
        self.row = rowLayout( self.methodName + '_rowSettings', nc=2, cw2=[200, 220], **layout )
        self.rows.append(self.row)
        
        # create ui elements
        text(label='Mel Equivalent')

        self.melNameTextField = textField(w=170, editable=False)
        self.melNameOptMenu = popupMenu(parent=self.melNameTextField, 
                                        button=1,
                                        postMenuCommand=Callback( MethodRow.populateMelNameMenu, self ) )
        setParent('..')
        
        self.row2 = rowLayout( self.methodName + '_rowSettings2', nc=3, cw3=[200, 180, 240], **layout )
        self.rows.append(self.row2)

        text(label='Use Name')
        self.nameMode = radioButtonGrp(label='', nrb=3, cw4=[1,50,50,50], labelArray3=['api', 'mel', 'other'] )
        self.altNameText = textField(w=170, enable=False)
        self.altNameText.changeCommand( CallbackWithArgs( MethodRow.alternateNameCB, self ) )
        self.nameMode.onCommand( Callback( MethodRow.nameTypeCB, self ) ) 
        
        
        # UI SETUP
 
        melName = self.data.get('melName', '')
        try:
            #self.melNameOptMenu.setValue( melName )
            self.melNameTextField.setText(melName)
            if melName != '':
                self.parent.parent.assignMelMethod( melName )
                
        except RuntimeError:
            # it is possible for a method name to be listed here that was set from a different view, 
            # where this class was a super class and more mel commands were available.  expand the option list,
            # and make this frame read-only
            menuItem( label=melName, parent=self.melNameOptMenu )
            self.melNameOptMenu.setValue( melName )
            self.frame.setEnable(False)
        
        self.enabledChBx.setValue( self.data['enabled'] )
        self.row.setEnable( self.data['enabled'] )
        self.row2.setEnable( self.data['enabled'] )
        
        name = self.data['useName']
        if name == 'API' :
            self.nameMode.setSelect( 1 )
            self.altNameText.setEnable(False)
        elif name == 'MEL' :
            self.nameMode.setSelect( 2 )
            self.altNameText.setEnable(False)
        else :
            self.nameMode.setSelect( 3 )
            self.altNameText.setText(name)
            self.altNameText.setEnable(True)
 
        
        if self.overloadPrecedenceColl:
            items = self.overloadPrecedenceColl.getCollectionItemArray()
            try:
                val = self.data['overloadIndex']
                self.overloadPrecedenceColl.setSelect( items[ val ] ) 
            except:
                pass
            
#            # ensure we don't use a value that is not valid
#            for val in range(val, len(enabledArray)+1):
#                try:
#                    if enabledArray[val]:
#                        break
#                except IndexError:
#                    val = None
#            if val is not None:
#                self.overloadPrecedenceColl.setSelect( items[ val ] )  
            
        setParent('..')
        
        setParent('..') # frame
        setParent('..') # column
    
        return True
        
    def enableCB(self, *args ):
        self.data['enabled'] = args[0]
        self.row.setEnable( args[0] )

    def nameTypeCB(self ):
        selected = self.nameMode.getSelect()
        if selected == 1:
            val = 'API'
            self.altNameText.setEnable(False)
        elif selected == 2:
            val = 'MEL'
            self.altNameText.setEnable(False)
        else:
            val = str(self.altNameText.getText())
            self.altNameText.setEnable(True)
            
        self.data['useName'] = val
        
    def alternateNameCB(self, *args ):
        self.data['useName'] = str(args[0])
        
#    def formatAnnotation(self, apiClassName, methodName ):
#        defs = []
#        try:
#            for methodInfo in api.apiClassInfo[apiClassName]['methods'][methodName] :
#                args = ', '.join( [ '%s %s' % (x[1],x[0]) for x in methodInfo['args'] ] )
#                defs.append( '%s( %s )' % ( methodName, args ) )
#            return '\n'.join( defs )
#        except KeyError:
#            print "could not find documentation for", apiClassName, methodName
    
    def overloadPrecedenceCB(self, i):
        if i == 0: # no precedence
            self.data.pop('overloadIndex',None)
        else:
            self.data['overloadIndex'] = i
    
    def melNameCB(self, newMelName):
        oldMelName = str(self.melNameTextField.getText())
        if oldMelName:
            self.uncrossReference( oldMelName )
        if newMelName == '[None]':
            self.data.pop('melName',None)
            self.parent.parent.unassignMelMethod( oldMelName )
            self.melNameTextField.setText('')
        else:
            self.crossReference( newMelName )
            self.data['melName'] = newMelName
            self.parent.parent.assignMelMethod( newMelName )
            self.melNameTextField.setText(newMelName)
            
    def populateMelNameMenu(self):
        self.melNameOptMenu.deleteAllItems()

        menuItem(parent=self.melNameOptMenu, label='[None]', command=Callback( MethodRow.melNameCB, self, '[None]' ))
        for method in self.parent.parent.unassignedMelMethodLister.getAllItems():
            menuItem(parent=self.melNameOptMenu, label=method, command=Callback( MethodRow.melNameCB, self, str(method) ))
    
    def getEnabledArray(self):
        """returns an array of booleans that correspond to each method and whether they can be wrapped"""
        array = []
        for info in self.methodInfoList:
            argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, info )
            array.append( argUtil.canBeWrapped() )
        return array
            
    def createAnnotation(self, i ):
        defs = []
        #try:
        argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, i )
        proto = argUtil.getPrototype( className=False, outputs=True, defaults=False )

        enable = argUtil.canBeWrapped()
        if self.overloadPrecedenceColl is not None:
            radioButton(label='', collection=self.overloadPrecedenceColl,
                                enable = enable,
                                onCommand=Callback( MethodRow.overloadPrecedenceCB, self, i ))
        text(   l=proto, 
                annotation = self.methodInfoList[i]['doc'],
                enable = enable)
        return enable      
#            methodInfo = api.apiClassInfo[self.apiClassName]['methods'][self.apiMethodName][overloadNum] 
#            args = ', '.join( [ '%s %s' % (x[1],x[0]) for x in methodInfo['args'] ] )
#            return  '( %s ) --> ' % ( args )
        #except:
        #    print "could not find documentation for", apiClassName, methodName
                

def getClassHierarchy( className):
    try:
        pymelClass = getattr(core.general, className)
    except AttributeError:
        print "could not find class", className
        pass
    else:
            
        mro = list( inspect.getmro(pymelClass) )
        mro.reverse()
        
    
        for i, cls in enumerate(mro):
            #if cls.__name__ not in ['object']:             
            try:
                apiClass = cls.__dict__[ '__apicls__']
                apiClassName = apiClass.__name__   
            except KeyError:
                try:
                    apiClass = cls.__dict__[ 'apicls']
                    apiClassName = apiClass.__name__   
                except KeyError:
                    #print "could not determine api class for", cls.__name__
                    apiClassName = None
                    
            yield cls.__name__, apiClassName    

        
        

        
def cacheResults():
    res = confirmDialog( title='Cache Results?',
                         message="Would you like to write your changes to disk? If you choose 'No' your changes will be lost when you restart Maya.",
                        button=['Yes','No'],
                        cancelButton='No',
                        defaultButton='Yes')
    print res
    if res == 'Yes':
        print "---"
        factories.saveApiToMelBridge()
        print "---"
