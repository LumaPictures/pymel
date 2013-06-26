"""
UI for controlling how api classes and mel commands are combined into pymel classes.

This UI modifies factories.apiToMelData which is pickled out to apiMelBridge.

It controls:
    which mel methods correspond to api methods
    disabling of api methods
    preference for overloaded methods (since currently only one overloaded method is supported)
    renaming of apiMethod


"""
from __future__ import with_statement
import inspect, re, os
import pymel.core as pm
import pymel.internal.factories as factories
import logging
logger = logging.getLogger(__name__)
if logger.level == logging.NOTSET:
    logger.setLevel(logging.INFO)

FRAME_WIDTH = 800
VERBOSE = True

class PymelControlPanel(object):
    def __init__(self):
        # key is a tuple of (class, method)
        self.classList = sorted( list( set( [ key[0] for key in factories.apiToMelData.keys()] ) ) )
        self.classFrames={}
        self.processClassFrames()
        self.buildUI()


    def buildUI(self):
        self.win = pm.window(title='Pymel Control Panel')
        self.win.show()

        with pm.paneLayout(configuration='vertical3', paneSize=([1,20,100], [3,20,100]) ) as self.pane:
            # Lef Column: Api Classes
            self.classScrollList = pm.textScrollList('apiClassList')

        # Center Column: Api Methods

        # Would LIKE to do it like this, but there is currently a bug with
        # objectType UI, such that even if
        #     layout('window4|paneLayout5', q=1, exists=1) == True
        # when you run:
        #     objectTypeUI('window4|paneLayout5')
        # you will get an error:
        #     RuntimeError: objectTypeUI: Object 'window4|paneLayout5' not found.

#        with formLayout() as apiForm:
#            #with scrollLayout() as scroll:
#            with tabLayout('apiMethodCol') as self.apiMethodCol:
#                pass
#            status = helpLine(h=60)

        # So, instead, we do it old-school...
        apiForm = pm.formLayout()
        self.apiMethodCol = pm.tabLayout('apiMethodCol')
        pm.setParent(apiForm)
        status = pm.cmds.helpLine(h=60)
        pm.setParent(self.pane)

        apiForm.attachForm( self.apiMethodCol, 'top', 5 )
        apiForm.attachForm( self.apiMethodCol, 'left', 5 )
        apiForm.attachForm( self.apiMethodCol, 'right', 5 )
        apiForm.attachControl( self.apiMethodCol, 'bottom', 5, status )
        apiForm.attachPosition( status, 'bottom', 5, 20 )
        apiForm.attachForm( status, 'bottom', 5 )
        apiForm.attachForm( status, 'left', 5 )
        apiForm.attachForm( status, 'right', 5 )

        # Right Column: Mel Methods
        melForm = pm.formLayout()
        label1 = pm.text( label='Unassigned Mel Methods' )
        self.unassignedMelMethodLister = pm.textScrollList()

        label2 = pm.text( label='Assigned Mel Methods' )
        self.assignedMelMethodLister = pm.textScrollList()

        label3 = pm.text( label='Disabled Mel Methods' )
        self.disabledMelMethodLister = pm.textScrollList()
        pm.setParent(self.pane)

        melForm.attachForm( label1, 'top', 5 )
        melForm.attachForm( label1, 'left', 5 )
        melForm.attachForm( label1, 'right', 5 )

        melForm.attachControl( self.unassignedMelMethodLister, 'top', 0, label1 )
        melForm.attachForm( self.unassignedMelMethodLister, 'left', 5 )
        melForm.attachForm( self.unassignedMelMethodLister, 'right', 5 )
        melForm.attachPosition( self.unassignedMelMethodLister, 'bottom', 5, 33 )

        melForm.attachControl( label2, 'top', 5,  self.unassignedMelMethodLister)
        melForm.attachForm( label2, 'left', 5 )
        melForm.attachForm( label2, 'right', 5 )

        melForm.attachControl( self.assignedMelMethodLister, 'top', 0, label2 )
        melForm.attachForm( self.assignedMelMethodLister, 'left', 5 )
        melForm.attachForm( self.assignedMelMethodLister, 'right', 5 )
        melForm.attachPosition( self.assignedMelMethodLister, 'bottom', 5, 66 )


        melForm.attachControl( label3, 'top', 5,  self.assignedMelMethodLister)
        melForm.attachForm( label3, 'left', 5 )
        melForm.attachForm( label3, 'right', 5 )

        melForm.attachControl( self.disabledMelMethodLister, 'top', 0, label3 )
        melForm.attachForm( self.disabledMelMethodLister, 'left', 5 )
        melForm.attachForm( self.disabledMelMethodLister, 'right', 5 )
        melForm.attachForm( self.disabledMelMethodLister, 'bottom', 5 )

        pm.setParent('..')

        pm.popupMenu(parent=self.unassignedMelMethodLister, button=3  )
        pm.menuItem(l='disable', c=pm.Callback( PymelControlPanel.disableMelMethod, self, self.unassignedMelMethodLister ) )

        pm.popupMenu(parent=self.assignedMelMethodLister, button=3  )
        pm.menuItem(l='disable', c=pm.Callback( PymelControlPanel.disableMelMethod, self, self.assignedMelMethodLister ) )

        pm.popupMenu(parent=self.disabledMelMethodLister, button=3  )
        pm.menuItem(l='enable', c=pm.Callback( PymelControlPanel.enableMelMethod))

        self.classScrollList.extend( self.classList )
        self.classScrollList.selectCommand( lambda: self.apiClassList_selectCB() )

        pm.scriptJob(uiDeleted=[str(self.win),cacheResults])

        self.win.show()


    def disableMelMethod(self, menu):
        msel = menu.getSelectItem()
        csel = self.classScrollList.getSelectItem()
        if msel and csel:
            method = msel[0]
            clsname = csel[0]
            menu.removeItem(method)
            self.disabledMelMethodLister.append( method  )
            #print clsname, method, factories.apiToMelData[ (clsname, method) ]
            factories.apiToMelData[ (clsname, method) ]['melEnabled'] = False

    def enableMelMethod(self):
        menu = self.disabledMelMethodLister
        msel = menu.getSelectItem()
        csel = self.classScrollList.getSelectItem()
        if msel and csel:
            method = msel[0]
            clsname = csel[0]
            menu.removeItem(method)
            self.unassignedMelMethodLister.append( method  )
            #print clsname, method, factories.apiToMelData[ (clsname, method) ]
            factories.apiToMelData[ (clsname, method) ].pop('melEnabled')

    @staticmethod
    def getMelMethods(className):
        """get all mel-derived methods for this class"""
        reg = re.compile('(.*[a-z])([XYZ])$')
        newlist = []
        origlist = factories.classToMelMap[className]
        for method in origlist:
            m = reg.search(method)
            if m:
                # strip off the XYZ component and replace with *
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
        if method in pm.util.listForNone( self.unassignedMelMethodLister.getAllItems() ):
            self.unassignedMelMethodLister.removeItem(method)
            self.assignedMelMethodLister.append( method )

    def unassignMelMethod(self, method):
        #print "method %s is now unassigned" % method
        if method in pm.util.listForNone( self.assignedMelMethodLister.getAllItems() ):
            self.assignedMelMethodLister.removeItem(method)
            self.unassignedMelMethodLister.append( method )



    def processClassFrames(self):
        """
        This triggers the generation of all the defaults for `factories.apiToMelData`, but it does
        not create any UI elements.  It creates `ClassFrame` instances, which in turn create
        `MethodRow` instances, but the creation of UI elements is delayed until a particular
        configuration is requested via `buildClassColumn`.
        """
        logger.info( 'processing all classes...' )
        for className in self.classList:
            melMethods = self.getMelMethods(className)
            logger.debug( '%s: mel methods: %s' % (className, melMethods) )
            for clsName, apiClsName in getClassHierarchy(className):
                if apiClsName and apiClsName not in ['list']:
                    if clsName not in self.classFrames:
                        frame = ClassFrame( self, clsName, apiClsName)
                        self.classFrames[clsName] = frame
                    # temporarily disable the melName updating until we figure out how to deal
                    # with base classes that are the parents of many others, and which therefore end up with
                    # methods derived from many different mel commands, which are only applicable for the inherited classes
                    # not for the base class on its own.  ( see ObjectSet and Character, for an example, specifically 'getIntersection' method )
                    #self.classFrames[clsName].updateMelNames( melMethods )
        logger.info( 'done processing classes' )

    def buildClassColumn(self, className ):
        """
        Build an info column for a class.  This column will include processed `ClassFrame`s for it and its parent classes
        """
        pm.setParent(self.apiMethodCol)
        self.apiMethodCol.clear()

        self.unassignedMelMethodLister.removeAll()
        self.assignedMelMethodLister.removeAll()
        self.disabledMelMethodLister.removeAll()

        melMethods = self.getMelMethods(className)
        for method in melMethods:
            # fix
            if (className, method) in factories.apiToMelData and factories.apiToMelData[ (className, method) ] == {'enabled':False}:
                d = factories.apiToMelData.pop( (className, method) )
                d.pop('enabled')
                d['melEnabled'] = False

            if (className, method) in factories.apiToMelData and factories.apiToMelData[(className, method)].get('melEnabled',True) == False:
                self.disabledMelMethodLister.append( method )
            else:
                self.unassignedMelMethodLister.append( method )


        #filter = set( ['double', 'MVector'] )
        filter = []
        count = 0
        for clsName, apiClsName in getClassHierarchy(className):
            if apiClsName:
                #print cls
                if clsName in self.classFrames:
                    logger.debug( "building UI for %s", clsName )
                    frame = self.classFrames[clsName].buildUI(filter)
                    self.apiMethodCol.setTabLabel( [frame, clsName] )
                    count+=1
                        #frame.setVisible(False)
                    #if i != len(mro)-1:
                    #    frame.setCollapse(True)
                else:
                    logger.debug( "skipping %s", clsName )
        self.apiMethodCol.setSelectTabIndex(count)

        #self.classFrames[className].frame.setCollapse(False)



class ClassFrame(object):
    def __init__(self, parent, className, apiClassName ):


        self.parent = parent
        self.className = className
        self.apiClassName = apiClassName
        self.rows = {}
        self.classInfo = factories.apiClassInfo[apiClassName]['methods']

        for method in self.classInfo.keys():
            row = MethodRow( self, self.className, self.apiClassName, method, self.classInfo[method] )

            self.rows[method] = row


    def updateMelNames(self, melMethods):
        logger.debug( '%s: updating melNames' % self.className )
        for rowName, row in self.rows.items():
            row.updateMelNames( melMethods )

    def buildUI(self, filter=None):

        count = 0
        #self.form = formLayout()
        with pm.frameLayout(collapsable=False, label='%s (%s)' % (self.className, self.apiClassName),
                            width = FRAME_WIDTH) as self.frame:
                            #labelAlign='top')

            with pm.tabLayout() as tab:

                invertibles = factories.apiClassInfo[self.apiClassName]['invertibles']
                usedMethods = []
                with pm.formLayout() as pairdForm:
                    tab.setTabLabel( [pairdForm, 'Paired'] )
                    with pm.scrollLayout() as pairedScroll:
                        with pm.columnLayout(visible=False, adjustableColumn=True) as pairedCol:

                            for setMethod, getMethod in invertibles:
                                pm.setParent(pairedCol) # column
                                frame = pm.frameLayout(label = '%s / %s' % (setMethod, getMethod),
                                                    labelVisible=True, collapsable=True,
                                                    collapse=True, width = FRAME_WIDTH)
                                col2 = pm.columnLayout()
                                pairCount = 0
                                pairCount += self.rows[setMethod].buildUI(filter)
                                pairCount += self.rows[getMethod].buildUI(filter)
                                usedMethods += [setMethod, getMethod]
                                if pairCount == 0:
                                    #deleteUI(col2)
                                    frame.setVisible(False)
                                    frame.setHeight(1)
                                count += pairCount
                            pairedCol.setVisible(True)
                pairdForm.attachForm( pairedScroll, 'top', 5 )
                pairdForm.attachForm( pairedScroll, 'left', 5 )
                pairdForm.attachForm( pairedScroll, 'right', 5 )
                pairdForm.attachForm( pairedScroll, 'bottom', 5 )

                with pm.formLayout() as unpairedForm:
                    tab.setTabLabel( [unpairedForm, 'Unpaired'] )
                    with pm.scrollLayout() as unpairedScroll:
                        with pm.columnLayout(visible=False ) as unpairedCol:
                            # For some reason, on linux, the unpairedCol height is wrong...
                            # track + set it ourselves
                            unpairedHeight = 10 # a little extra buffer...
                            #rowSpace = unpairedCol.getRowSpacing()
                            for methodName in sorted( self.classInfo.keys() ):
                                pm.setParent(unpairedCol)
                                if methodName not in usedMethods:
                                    frame = pm.frameLayout(label = methodName,
                                                        labelVisible=True, collapsable=True,
                                                        collapse=True, width = FRAME_WIDTH)
                                    col2 = pm.columnLayout()
                                    count += self.rows[methodName].buildUI(filter)
                                    unpairedHeight += self.rows[methodName].frame.getHeight()# + rowSpace
                            unpairedCol.setHeight(unpairedHeight)

                            #self.form.attachForm( self.frame, 'left', 2)
                            #self.form.attachForm( self.frame, 'right', 2)
                            #self.form.attachForm( self.frame, 'top', 2)
                            #self.form.attachForm( self.frame, 'bottom', 2)
                            unpairedCol.setVisible(True)
                unpairedForm.attachForm( unpairedScroll, 'top', 5 )
                unpairedForm.attachForm( unpairedScroll, 'left', 5 )
                unpairedForm.attachForm( unpairedScroll, 'right', 5 )
                unpairedForm.attachForm( unpairedScroll, 'bottom', 5 )
        return self.frame


class MethodRow(object):
    def __init__(self, parent, className, apiClassName, apiMethodName, methodInfoList):


        self.parent = parent
        self.className = className
        self.methodName = methodInfoList[0].get('pymelName', apiMethodName)
        self.apiClassName = apiClassName
        self.apiMethodName = apiMethodName
        self.methodInfoList = methodInfoList
        self.data = factories._getApiOverrideNameAndData(self.className, self.methodName)[1]
        self.classInfo = factories.apiClassInfo[self.apiClassName]['methods'][self.apiMethodName]
        try:
            enabledArray = self.getEnabledArray()
        except:
            print self.apiClassName, self.apiMethodName
            raise
        # DEFAULT VALUES


        # correct old values
        # we no longer store positive values, only negative -- meaning methods will be enabled by default
#        if 'enabled' in self.data and ( self.data['enabled'] == True  or sum(enabledArray) == 0 ):
#            logger.debug( '%s.%s: enabled array: %s' % ( self.className, self.methodName, enabledArray ) )
#            logger.debug( '%s.%s: removing enabled entry' % ( self.className, self.methodName) )
#            self.data.pop('enabled', None)


        # enabled
#        if not self.data.has_key( 'enabled' ):
#            self.data['enabled'] = True

        if self.methodName in factories.EXCLUDE_METHODS : # or sum(enabledArray) == 0:
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
            #logger.debug( "correcting melName %s %s %s" % (self.className, self.methodName, str(self.data['melName']) ) )
            self.data['melName'] = str(self.data['melName'])


        overloadId = self.data.get('overloadIndex', 0)
        if overloadId is None:
            # in a previous test, it was determined there were no wrappable overload methods,
            # but there may be now.  try again.
            overloadId = 0

        # ensure we don't use a value that is not valid
        for i in range(overloadId, len(enabledArray)+1):
            try:
                if enabledArray[i]:
                    break
            except IndexError: # went too far, so none are valid
                overloadId = None
#        if val is None:
#            # nothing valid
#            self.data.pop('overloadIndex', None)
#        else:
        self.data['overloadIndex'] = overloadId

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
                methreg = re.compile(method.replace('*', '.{0,1}') + '$')
                #print self.methodName, methreg
                if methreg.match( self.methodName ):
                    match = str(method)
                    break
            if match:
                logger.debug( "%s.%s: adding melName %s" % ( self.className, self.methodName, match ) )
                self.data['melName'] = match
                self.crossReference( match )

    def buildUI(self, filter=None):

        if filter:
            match = False
            for i, info in enumerate( self.methodInfoList):
                argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, i )
                if filter.intersection( argUtil.getInputTypes() + argUtil.getOutputTypes() ):
                    match = True
                    break
            if match == False:
                return False

        self.layout = { 'columnAlign'  : [1,'right'],
                   'columnAttach' : [1,'right',8] }

        #print className, self.methodName, melMethods
        isOverloaded = len(self.methodInfoList)>1
        self.frame = pm.frameLayout( w=FRAME_WIDTH, labelVisible=False, collapsable=False)
        logger.debug("building row for %s - %s" % (self.methodName, self.frame))
        col = pm.columnLayout()

        enabledArray = []
        self.rows = []
        self.overloadPrecedenceColl = None
        self.enabledChBx = pm.checkBox(label=self.methodName,
                    changeCommand=pm.CallbackWithArgs( MethodRow.enableCB, self ) )

        if isOverloaded:

            self.overloadPrecedenceColl = pm.radioCollection()
            for i in range( len(self.methodInfoList) ) :

                self.createMethodInstance(i)

        else:
            #row = rowLayout( self.methodName + '_rowMain', nc=2, cw2=[200, 400] )
            #self.enabledChBx = checkBox(label=self.methodName, changeCommand=CallbackWithArgs( MethodRow.enableCB, self ) )
            #text(label='')
            self.createMethodInstance(0)
            #setParent('..')

        pm.setParent(col)
        pm.separator(w=800, h=6)


        #self.row = rowLayout( self.methodName + '_rowSettings', nc=4, cw4=[200, 160, 180, 160] )
        #self.rows.append(row)


        self.row = pm.rowLayout( self.methodName + '_rowSettings', nc=2, cw2=[200, 220], **self.layout )
        self.rows.append(self.row)

        # create ui elements
        pm.text(label='Mel Equivalent')

        self.melNameTextField = pm.textField(w=170, editable=False)
        self.melNameOptMenu = pm.popupMenu(parent=self.melNameTextField,
                                        button=1,
                                        postMenuCommand=pm.Callback( MethodRow.populateMelNameMenu, self ) )
        pm.setParent('..')

        self.row2 = pm.rowLayout( self.methodName + '_rowSettings2', nc=3, cw3=[200, 180, 240], **self.layout )
        self.rows.append(self.row2)

        pm.text(label='Use Name')
        self.nameMode = pm.radioButtonGrp(label='', nrb=3, cw4=[1,50,50,50], labelArray3=['api', 'mel', 'other'] )
        self.altNameText = pm.textField(w=170, enable=False)
        self.altNameText.changeCommand( pm.CallbackWithArgs( MethodRow.alternateNameCB, self ) )
        self.nameMode.onCommand( pm.Callback( MethodRow.nameTypeCB, self ) )

        isEnabled = self.data.get('enabled', True)

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
            pm.menuItem( label=melName, parent=self.melNameOptMenu )
            self.melNameOptMenu.setValue( melName )
            logger.debug( "making %s frame read-only" % self.methodName )
            self.frame.setEnable(False)


        self.enabledChBx.setValue( isEnabled )
        self.row.setEnable( isEnabled )
        self.row2.setEnable( isEnabled )

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

                if val is None:
                    logger.info( "no wrappable options for method %s" % self.methodName )
                    self.frame.setEnable( False )
                else:
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

        pm.setParent('..')

        pm.setParent('..') # frame
        pm.setParent('..') # column

        return True

    def enableCB(self, *args ):
        logger.debug( 'setting enabled to %s' % args[0] )
        if args[0] == False:
            self.data['enabled'] = False
        else:
            self.data.pop('enabled', None)
        self.row.setEnable( args[0] )

    def nameTypeCB(self ):
        logger.info( 'setting name type' )
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

        logger.debug( 'data %s' % self.data )
        self.data['useName'] = val

    def alternateNameCB(self, *args ):
        self.data['useName'] = str(args[0])

#    def formatAnnotation(self, apiClassName, methodName ):
#        defs = []
#        try:
#            for methodInfo in factories.apiClassInfo[apiClassName]['methods'][methodName] :
#                args = ', '.join( [ '%s %s' % (x[1],x[0]) for x in methodInfo['args'] ] )
#                defs.append( '%s( %s )' % ( methodName, args ) )
#            return '\n'.join( defs )
#        except KeyError:
#            print "could not find documentation for", apiClassName, methodName

    def overloadPrecedenceCB(self, i):
        logger.debug( 'overloadPrecedenceCB' )
        self.data['overloadIndex'] = i

    def melNameChangedCB(self, newMelName):
        oldMelName = str(self.melNameTextField.getText())
        if oldMelName:
            self.uncrossReference( oldMelName )
        if newMelName == '[None]':
            print "removing melName"
            self.data.pop('melName',None)
            self.parent.parent.unassignMelMethod( oldMelName )
            self.melNameTextField.setText('')
        else:
            print "adding melName", newMelName
            self.crossReference( newMelName )
            self.data['melName'] = newMelName
            self.parent.parent.assignMelMethod( newMelName )
            self.melNameTextField.setText(newMelName)

    def populateMelNameMenu(self):
        """called to populate the popup menu for choosing the mel equivalent to an api method"""
        self.melNameOptMenu.deleteAllItems()

        pm.menuItem(parent=self.melNameOptMenu, label='[None]', command=pm.Callback( MethodRow.melNameChangedCB, self, '[None]' ))
        # need to add a listForNone to this in windows
        items = self.parent.parent.unassignedMelMethodLister.getAllItems()
        if items:
            for method in items:
                pm.menuItem(parent=self.melNameOptMenu, label=method, command=pm.Callback( MethodRow.melNameChangedCB, self, str(method) ))

    def getEnabledArray(self):
        """returns an array of booleans that correspond to each override method and whether they can be wrapped"""
        array = []
        for i, info in enumerate( self.methodInfoList ):
            argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, i )
            array.append( argUtil.canBeWrapped() )
        return array


    def createMethodInstance(self, i ):

        #setUITemplate('attributeEditorTemplate', pushTemplate=1)

        rowSpacing = [30, 20, 400]

        defs = []
        #try:
        argUtil = factories.ApiArgUtil( self.apiClassName, self.apiMethodName, i )
        proto = argUtil.getPrototype( className=False, outputs=True, defaults=False )

        enable = argUtil.canBeWrapped()

        if argUtil.isDeprecated():
            pm.text(l='DEPRECATED')
        # main info row
        row = pm.rowLayout( '%s_rowMain%s' % (self.methodName,i), nc=3, cw3=rowSpacing, enable=enable )
        self.rows.append(row)
        pm.text(label='')

        if self.overloadPrecedenceColl is not None:
            # toggle for overloaded methods
            pm.radioButton(label='', collection=self.overloadPrecedenceColl,
                                enable = enable,
                                onCommand=pm.Callback( MethodRow.overloadPrecedenceCB, self, i ))
        pm.text(   l='', #l=proto,
                annotation = self.methodInfoList[i]['doc'],
                enable = enable)

        pm.setParent('..')

        try:
            argList = factories.apiClassOverrides[self.apiClassName]['methods'][self.apiMethodName][i]['args']
        except (KeyError, IndexError):
            argList = self.methodInfoList[i]['args']

        returnType =  self.methodInfoList[i]['returnType']
        types = self.methodInfoList[i]['types']
        args = []

        for arg , type, direction in argList:
            type = str(types[arg])
            assert arg != 'return'
            self._makeArgRow( i, type, arg, direction, self.methodInfoList[i]['argInfo'][arg]['doc'] )

        if returnType:
            self._makeArgRow( i, returnType, 'return', 'return', self.methodInfoList[i]['returnInfo']['doc'] )

        pm.separator(w=800, h=14)

        return enable
#            methodInfo = factories.apiClassInfo[self.apiClassName]['methods'][self.apiMethodName][overloadNum]
#            args = ', '.join( [ '%s %s' % (x[1],x[0]) for x in methodInfo['args'] ] )
#            return  '( %s ) --> ' % ( args )
        #except:
        #    print "could not find documentation for", apiClassName, methodName


    def setUnitType(self, methodIndex, argName, unitType ):

        if self.apiClassName not in factories.apiClassOverrides:
            factories.apiClassOverrides[self.apiClassName] = { 'methods' : {} }

        methodOverrides = factories.apiClassOverrides[self.apiClassName]['methods']

        if self.apiMethodName not in methodOverrides:
            methodOverrides[self.apiMethodName] = {}

        if argName == 'return':
            if methodIndex not in methodOverrides[self.apiMethodName]:
                methodOverrides[self.apiMethodName][methodIndex] = { 'returnInfo' : {} }

            methodOverrides[self.apiMethodName][methodIndex]['returnInfo']['unitType'] = unitType

        else:
            if methodIndex not in methodOverrides[self.apiMethodName]:
                methodOverrides[self.apiMethodName][methodIndex] = { 'argInfo' : {} }

            if argName not in methodOverrides[self.apiMethodName][methodIndex]['argInfo']:
                methodOverrides[self.apiMethodName][methodIndex]['argInfo'][argName] = {}

            methodOverrides[self.apiMethodName][methodIndex]['argInfo'][argName]['unitType'] = unitType

    def setDirection(self, methodIndex, argName, direction ):

        if self.apiClassName not in factories.apiClassOverrides:
            factories.apiClassOverrides[self.apiClassName] = { 'methods' : {} }

        methodOverrides = factories.apiClassOverrides[self.apiClassName]['methods']

        if self.apiMethodName not in methodOverrides:
            methodOverrides[self.apiMethodName] = {}

        if methodIndex not in methodOverrides[self.apiMethodName]:
            methodOverrides[self.apiMethodName][methodIndex] = { }

        try:
            argList = methodOverrides[self.apiMethodName][methodIndex]['args']

        except KeyError:
            argList = self.methodInfoList[methodIndex]['args']

        newArgList = []
        inArgs = []
        outArgs = []
        for i_argName, i_argType, i_direction in argList:
            if i_argName == argName:
                argInfo = ( i_argName, i_argType, direction )
            else:
                argInfo = ( i_argName, i_argType, i_direction )

            if argInfo[2] == 'in':
                inArgs.append( i_argName )
            else:
                outArgs.append( i_argName )
            newArgList.append( argInfo )

            methodOverrides[self.apiMethodName][methodIndex] = { }

        methodOverrides[self.apiMethodName][methodIndex]['args'] = newArgList
        methodOverrides[self.apiMethodName][methodIndex]['inArgs'] = inArgs
        methodOverrides[self.apiMethodName][methodIndex]['outArgs'] = outArgs

    def _makeArgRow(self, methodIndex, type, argName, direction, annotation=''):
        COL1_WIDTH = 260
        COL2_WIDTH = 120
        pm.rowLayout( nc=4, cw4=[COL1_WIDTH,COL2_WIDTH, 70, 150], **self.layout )

        label = str(type)

        pm.text( l=label, ann=annotation )
        pm.text( l=argName, ann=annotation )

        if direction == 'return':
            pm.text( l='(result)' )
        else:
            direction_om = pm.optionMenu(l='', w=60, ann=annotation, cc=pm.CallbackWithArgs( MethodRow.setDirection, self, methodIndex, argName ) )
            for unit in ['in', 'out']:
                pm.menuItem(l=unit)
            direction_om.setValue(direction)

        if self._isPotentialUnitType(type) :
            om = pm.optionMenu(l='', ann=annotation, cc=pm.CallbackWithArgs( MethodRow.setUnitType, self, methodIndex, argName ) )
            for unit in ['unitless', 'linear', 'angular', 'time']:
                pm.menuItem(l=unit)
            if argName == 'return':
                try:
                    value = factories.apiClassOverrides[self.apiClassName]['methods'][self.apiMethodName][methodIndex]['returnInfo']['unitType']
                except KeyError:
                    pass
            else:
                try:
                    value = factories.apiClassOverrides[self.apiClassName]['methods'][self.apiMethodName][methodIndex]['argInfo'][argName]['unitType']
                except KeyError:
                    pass
            try:
                om.setValue(value)
            except: pass

        else:
            pm.text( l='', ann=annotation )
        pm.setParent('..')

    def _isPotentialUnitType(self, type):
        type = str(type)
        return type == 'MVector' or type.startswith('double')

def _getClass(className):
    for module in [core.nodetypes, core.datatypes, core.general]:
        try:
            pymelClass = getattr(module, className)
            return pymelClass
        except AttributeError:
            pass

def getApiClassName( className ):
    pymelClass = _getClass(className)
    if pymelClass:

        apiClass = None
        apiClassName = None
        #if cls.__name__ not in ['object']:
        try:
            apiClass = pymelClass.__dict__[ '__apicls__']
            apiClassName = apiClass.__name__
        except KeyError:
            try:
                apiClass = pymelClass.__dict__[ 'apicls']
                apiClassName = apiClass.__name__
            except KeyError:
                #print "could not determine api class for", cls.__name__
                apiClassName = None
        return apiClassName
    else:
        logger.warning( "could not find class %s" % (className) )

def getClassHierarchy( className ):
    pymelClass = _getClass(className)
    if pymelClass:

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
    else:
        logger.warning( "could not find class %s" % (className) )



def setManualDefaults():
    # set some defaults
    # TODO : allow these defaults to be controlled via the UI
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnTransform', 'methods', 'setScalePivot', 0, 'defaults', 'balance' ), True )
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnTransform', 'methods', 'setRotatePivot', 0, 'defaults', 'balance' ), True )
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnTransform', 'methods', 'setRotateOrientation', 0, 'defaults', 'balance' ), True )
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnSet', 'methods', 'getMembers', 0, 'defaults', 'flatten' ), False )
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnDagNode', 'methods', 'instanceCount', 0, 'defaults', 'total' ), True )
    pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MFnMesh', 'methods', 'createColorSetWithName', 1, 'defaults', 'modifier' ), None )

    # add some manual invertibles: THESE MUST BE THE API NAMES
    invertibles = [ ('MPlug', 0, 'setCaching', 'isCachingFlagSet') ,
                    ('MPlug', 0, 'setChannelBox', 'isChannelBoxFlagSet'),
                    ('MFnTransform', 0, 'enableLimit', 'isLimited'),
                    ('MFnTransform', 0, 'setLimit', 'limitValue'),
                    ('MFnTransform', 0, 'set', 'transformation'),
                    ('MFnRadialField', 0, 'setType', 'radialType')
                     ]
    for className, methodIndex, setter, getter in invertibles:
        # append to the class-level invertibles list
        curr = pm.util.getCascadingDictItem( factories.apiClassInfo, (className, 'invertibles' ), [] )
        pair = (setter, getter)
        if pair not in curr:
            curr.append( pair )

        pm.util.setCascadingDictItem( factories.apiClassOverrides, (className, 'invertibles'), curr )

        # add the individual method entries
        pm.util.setCascadingDictItem( factories.apiClassOverrides, (className, 'methods', setter, methodIndex, 'inverse' ), (getter, True) )
        pm.util.setCascadingDictItem( factories.apiClassOverrides, (className, 'methods', getter, methodIndex, 'inverse' ), (setter, False) )

    nonInvertibles = [ ( 'MFnMesh', 0, 'setFaceVertexNormals', 'getFaceVertexNormals' ),
                        ( 'MFnMesh', 0, 'setFaceVertexNormal', 'getFaceVertexNormal' ) ]
    for className, methodIndex, setter, getter in nonInvertibles:
        pm.util.setCascadingDictItem( factories.apiClassOverrides, (className, 'methods', setter, methodIndex, 'inverse' ), None )
        pm.util.setCascadingDictItem( factories.apiClassOverrides, (className, 'methods', getter, methodIndex, 'inverse' ), None )
    fixSpace()

def fixSpace():
    "fix the Space enumerator"

    enum = pm.util.getCascadingDictItem( factories.apiClassInfo, ('MSpace', 'pymelEnums', 'Space') )
    keys = enum._keys.copy()
    #print keys
    val = keys.pop('postTransform', None)
    if val is not None:
        keys['object'] = val
        newEnum = pm.util.Enum( 'Space', keys )

        pm.util.setCascadingDictItem( factories.apiClassOverrides, ('MSpace', 'pymelEnums', 'Space'), newEnum )
    else:
        logger.warning( "could not fix Space")

def cacheResults():
    #return

    res = pm.confirmDialog( title='Cache Results?',
                         message="Would you like to write your changes to disk? If you choose 'No' your changes will be lost when you restart Maya.",
                        button=['Yes','No'],
                        cancelButton='No',
                        defaultButton='Yes')
    print res
    if res == 'Yes':
        doCacheResults()

def doCacheResults():
    print "---"
    print "adding manual defaults"
    setManualDefaults()
    print "merging dictionaries"
    # update apiClasIfno with the sparse data stored in apiClassOverrides
    factories.mergeApiClassOverrides()
    print "saving api cache"
    factories.saveApiCache()
    print "saving bridge"
    factories.saveApiMelBridgeCache()
    print "---"
