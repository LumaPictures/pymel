import sys
import pmcmds as cmds
import pymel.util as util
import factories as _factories
from factories import MetaMayaUIWrapper
from system import Path
import pymel.mayahook.plogging as plogging
_logger = plogging.getLogger(__name__)

class UI(unicode):
    def __new__(cls, name=None, create=False, **kwargs):
        """
        Provides the ability to create the UI Element when creating a class
        
            >>> n = pm.Window("myWindow",create=True)
            >>> n.__repr__()
            # Result: Window('myWindow')
        """
        slc = kwargs.pop("slc",kwargs.pop("defer",kwargs.get('childCreators')))

        if slc:
            self = unicode.__new__(cls,name)
            postFunc = kwargs.pop('postFunc',None)
            childCreators = kwargs.pop('childCreators',None)
            self.slc = SmartLayoutCreator(
                            name, 
                            cls, 
                            kwargs, postFunc, childCreators)
            self.create = self.slc.create
            return self
        else:
            if cls._isBeingCreated(name, create, kwargs):
                name = cls.__melcmd__(name, **kwargs)
                _logger.debug("UI: created... %s" % name)
            return unicode.__new__(cls,name)

    @staticmethod
    def _isBeingCreated( name, create, kwargs):
        """
        create a new node when any of these conditions occur:
           name is None
           create is True
           parent flag is set
        """
        return not name or create or kwargs.get( 'parent', kwargs.get('p', None))
        
#    def exists():
#        try: return cls.__melcmd__(name, ex=1)
#        except: pass
        
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)
    def getChildren(self, **kwargs):
        kwargs['long'] = True
        return [ x for x in lsUI(**kwargs) if x.startswith(self+'|')]
    def getParent(self):
        return UI( '|'.join( unicode(self).split('|')[:-1] ) )
    def type(self):
        return cmds.objectTypeUI(self)
    def shortName(self):
        return unicode(self).split('|')[-1]
    def name(self):
        return unicode(self)
    
    delete = _factories.functionFactory( 'deleteUI', rename='delete' )
    rename = _factories.functionFactory( 'renameUI', rename='rename' )
    type = _factories.functionFactory( 'objectTypeUI', rename='type' )
     
# customized ui classes                            
class Window(UI):
    """pymel window class"""
    __metaclass__ = MetaMayaUIWrapper                        
    def show(self):
        cmds.showWindow(self)
    def delete(self):
        cmds.deleteUI(self, window=True)
    def __aftercreate__(self):
        self.show()

class FormLayout(UI):
    __metaclass__ = MetaMayaUIWrapper
    def attachForm(self, *args):
        kwargs = {'edit':True}
        kwargs['attachForm'] = [args]
        cmds.formLayout(self,**kwargs)
        
    def attachControl(self, *args):
        kwargs = {'edit':True}
        kwargs['attachControl'] = [args]
        cmds.formLayout(self,**kwargs)        
        
    def attachNone(self, *args):
        kwargs = {'edit':True}
        kwargs['attachNone'] = [args]
        cmds.formLayout(self,**kwargs)    
        
    def attachPosition(self, *args):
        kwargs = {'edit':True}
        kwargs['attachPosition'] = [args]
        cmds.formLayout(self,**kwargs)
        

    """ 
    Automatically distributes child controls in either a
    horizontal or vertical layout. Call 'redistribute' once done
    adding child controls.
    """
    enumOrientation = util.enum.Enum( 'Orientation', ['HORIZONTAL', 'VERTICAL'] )
    HORIZONTAL = enumOrientation.HORIZONTAL
    VERTICAL = enumOrientation.VERTICAL
    
    def __new__(cls, name=None, **kwargs):
        if not 'slc' in kwargs:
            kw = dict((k,kwargs.pop(k)) for k in ['orientation', 'ratios', 'reversed', 'spacing'] if k in kwargs)
        else:
            kw = {}
        self = UI.__new__(cls, name, **kwargs)
        kwargs.update(kw)
        cls.__init__(self, name, **kwargs)
        return self
        

    def __init__(self, name=None, orientation='VERTICAL', spacing=2, reversed=False, ratios=None, **kwargs):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        UI.__init__(self, **kwargs)
        self.spacing = spacing
        self.ori = self.enumOrientation.getIndex(orientation)
        self.reversed = reversed
        self.ratios = ratios and list(ratios) or []
    
    def flip(self):
        """Flip the orientation of the layout """
        self.ori = 1-self.ori
        self.redistribute(*self.ratios)
    
    def reverse(self):
        """Reverse the children order """
        self.reversed = not self.reversed
        self.ratios.reverse()
        self.redistribute(*self.ratios)
        
    def reset(self):
        self.ratios = []
        self.reversed = False
        self.redistribute()
        
    sides = [["top","bottom"],["left","right"]]
    def redistribute(self,*ratios):
        """ Redistribute the child controls based on the given ratios.
            If not ratios are given (or not enough), 1 will be used 
        """
        
        children = self.getChildArray()
        if not children:
            return
        if self.reversed: children.reverse()
        
        ratios = list(ratios) or self.ratios or []
        ratios += [1]*(len(children)-len(ratios))
        self.ratios = ratios
        total = sum(ratios)       
         
        for i in range(len(children)):
            child = children[i]
            for side in self.sides[self.ori]:
                self.attachForm(child,side,self.spacing)

            if i==0:
                self.attachForm(child,
                    self.sides[1-self.ori][0],
                    self.spacing)
            else:
                self.attachControl(child,
                    self.sides[1-self.ori][0],
                    self.spacing,
                    children[i-1])
            
            if ratios[i]:
                self.attachPosition(children[i],
                    self.sides[1-self.ori][1],
                    self.spacing,
                    float(sum(ratios[:i+1]))/float(total)*100)
            else:
                self.attachNone(children[i],
                    self.sides[1-self.ori][1])
                
    def __aftercreate__(self, *args, **kwargs):
        self.redistribute()
    
    def vDistribute(self,*ratios):
        self.ori = VERTICAL.index
        self.redistribute(*ratios)
        
    def hDistribute(self,*ratios):
        self.ori = HORIZONTAL.index
        self.redistribute(*ratios)

# for backwards compatiblity
AutoLayout = FormLayout        

    
class TextScrollList(UI):
    __metaclass__ = MetaMayaUIWrapper
    def extend( self, appendList ):
        """ append a list of strings"""
        
        for x in appendList:
            self.append(x)
            
    def selectIndexedItems( self, selectList ):
        """select a list of indices"""
        for x in selectList:
            self.selectIndexedItem(x)

    def removeIndexedItems( self, removeList ):
        """remove a list of indices"""
        for x in removeList:
            self.removeIndexedItem(x)
                
    def selectAll(self):
        """select all items"""
        numberOfItems = self.getNumberOfItems()
        self.selectIndexedItems(range(1,numberOfItems+1))

class OptionMenu(UI):
    __metaclass__ = MetaMayaUIWrapper
    def addMenuItems( self, items, title=None):
        """ Add the specified item list to the OptionMenu, with an optional 'title' item """ 
        if title:
            cmds.menuItem(l=title, en=0, parent=self)
        for item in items:
            cmds.menuItem(l=item, parent=self)
            
    def clear(self):  
        """ Clear all menu items from this OptionMenu """
        for t in self.getItemListLong() or []:
            cmds.deleteUI(t)
    addItems = addMenuItems

       


dynModule = util.LazyLoadModule(__name__, globals())

def _createUIClasses():

    for funcName in _factories.uiClassList:
        # Create Class
        classname = util.capitalize(funcName)
        try:
            cls = dynModule[classname]
        except KeyError:
            #uitypes._addattr(classname, MetaMayaUIWrapper, classname, (uitypes.UI,), {})
            dynModule[classname] = (MetaMayaUIWrapper, (classname, (UI,), {}) )

_createUIClasses()
          
class VectorFieldGrp( dynModule.FloatFieldGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        if create:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = 3
            name = cmds.floatFieldGrp( name, *args, **kwargs)

        return dynModule.FloatFieldGrp.__new__( cls, name, create=False, *args, **kwargs )
        
    def getVector(self):
        import datatypes
        x = cmds.floatFieldGrp( self, q=1, v1=True )
        y = cmds.floatFieldGrp( self, q=1, v2=True )
        z = cmds.floatFieldGrp( self, q=1, v3=True )
        return datatypes.Vector( [x,y,z] )
    
    def setVector(self, vec):
        cmds.floatFieldGrp( self, e=1, v1=vec[0], v2=vec[1], v3=vec[2] )


class TextLayout( dynModule.FrameLayout ):
    """A frame-layout with a textfield inside, used by the 'textWindow' function"""
    
    def __new__(cls, name=None, parent=None, text=None):
        self = cmds.frameLayout(labelVisible=bool(name), label=name or "Text Window", parent=parent)
        return dynModule.FrameLayout.__new__(cls, self)

    def __init__(self, parent, text=None):
        import windows
        windows.SLC("topForm", windows.verticalLayout, dict(), AutoLayout.redistribute, [
            windows.SLC("txtInfo", windows.scrollField, {"editable":False}),
        ]).create(self.__dict__, parent=self, debug=False)
        self.setText(text)
        
    def setText(self, text=""):
        from pprint import pformat
        if not isinstance(text, basestring):
            text = pformat(text)
        self.txtInfo.setText(text)
        self.txtInfo.setInsertionPosition(1)

class PathButtonGrp( dynModule.TextFieldButtonGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        
        if create:
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)
            
            def setPathCB(name):
                f = promptForPath()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f)
            
            import windows
            cb = windows.Callback( setPathCB, name ) 
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )
            
        return dynModule.TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )
        
    def setPath(self, path):
        self.setText( path )
       
    def getPath(self):
        return Path( self.getText() )

dynModule._updateLazyModule(globals())
sys.modules[__name__] = dynModule

