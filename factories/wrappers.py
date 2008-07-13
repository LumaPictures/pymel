
from pymel.util.arrays import *

class MetaMayaTypeWrapper(metaReadOnlyAttr) :
    """ A metaclass to wrap Maya api types, with support for class constants """ 

    class ClassConstant(object):
        """ A data descriptor for user defined constants on the class """
        def __init__(self, value):
            self.value = value
        def __get__(self, instance, owner):
            # purposedly authorize notation MColor.blue but not MColor().blue,
            # the constants are a class property and are not defined on instances
            if instance is None :
                return owner(self.value)
            else :
                raise AttributeError, "Class constants on %s are only defined on the class" % (owner.__name__)
        def __set__(self, instance, value):
            raise AttributeError, "class constant cannot be set"
        def __delete__(self, instance):
            raise AttributeError, "class constant cannot be deleted"
          
    def __new__(mcl, classname, bases, classdict):
        """ Create a new class of metaClassConstants type """
         
        # define __slots__ if not defined
        if '__slots__' not in classdict :
            classdict['__slots__'] = ()
        if 'apicls' in classdict and not classdict['apicls'] in bases :
            # if not in bases, add to it
            bases = bases + (classdict['apicls'],)
            
        # create the new class   
        newcls = super(MetaMayaTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)
            
        # if hasattr(newcls, 'stype') :
        if hasattr(newcls, 'apicls') :
            # type (api type) used for the storage of data
            apicls  = newcls.apicls
            
            

            # build the data property
            #            def setdata(self, data):
            #                self._data = self.__class__.apicls(data)
            #            def getdata(self):
            #                return self._data
            #            p = property(getdata, setdata, None, "One %s" % apicls.__name__)
            #            type.__setattr__(newcls, 'data', p) 
            
            #    def _getdata(self):
            #        return list(self.get())
            #    def _setdata(self, data):
            #        mat = api.MMatrix()
            #        api.MScriptUtil.createMatrixFromList ( list(data), mat)
            #        self = self.__class__(mat) 
            #    def _deldata(self):
            #        del self     
            #    data = property(_getdata, _setdata, _deldata, "The nested list storage for the Array data")              
                                     
            # build some constants on the class            
            constant = {}
            # constants in class definition will be converted from api class to created class
            for name, attr in newcls.__dict__.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaTypeWrapper.ClassConstant(attr)                          
            # we'll need the api clas dict to automate some of the wrapping
            # can't get argspec on SWIG creation function of type built-in or we could automate more of the wrapping 
            apiDict = dict(inspect.getmembers(apicls))            
            # defining class properties on the created class                 
            for name, attr in apiDict.iteritems() :
                # to add the wrapped api class constants as attributes on the wrapping class,
                # convert them to own class         
                if isinstance(attr, apicls) :
                    if name not in constant :
                        constant[name] = MetaMayaTypeWrapper.ClassConstant(attr)
            # update the constant dict with herited constants
            mro = inspect.getmro(newcls)            
            for cls in mro :
                if isinstance(cls, MetaMayaTypeWrapper) :
                    for name, attr in cls.__dict__.iteritems() :
                        if isinstance(attr, MetaMayaTypeWrapper.ClassConstant) :
                            if not name in constant :
                                constant[name] = MetaMayaTypeWrapper.ClassConstant(attr.value)
            
            # build the protected list to make some class ifo and the constants read only class attributes
            # new.__slots__ = ['_data', '_shape', '_ndim', '_size']
            # type.__setattr__(newcls, '__slots__', slots) 
            
            # set class constants as readonly 
            readonly = newcls.__readonly__
            if 'stype' not in readonly :
                readonly['stype'] = None
            if 'apicls' not in readonly :
                readonly['apicls'] = None 
            for c in constant.keys() :
                readonly[c] = None          
            type.__setattr__(newcls, '__readonly__', readonly)          
            # store constants as class attributes
            for name, attr in constant.iteritems() :
                type.__setattr__(newcls, name, attr)
                                           
        else :
            raise TypeError, "must define 'apicls' in the class definition (which Maya API class to wrap)"
        
        return newcls 


# the meta class of metaMayaWrapper
class MetaMayaArrayTypeWrapper(MetaMayaTypeWrapper) :
    """ A metaclass to wrap Maya array type classes such as MVector, MMatrix """ 
             
    def __new__(mcl, classname, bases, classdict):
        """ Create a new wrapping class for a Maya api type, such as MVector or MMatrix """
            
        if 'shape' in classdict :
            # fixed shape means also fixed ndim and size
            shape = classdict['shape']
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            if 'ndim' not in classdict :
                classdict['ndim'] = ndim
            elif classdict['ndim'] != ndim :
                raise ValueError, "class %s shape definition %s and number of dimensions definition %s do not match" % (classname, shape, ndim)
            if 'size' not in classdict :
                classdict['size'] = size
            elif classdict['size'] != size :
                raise ValueError, "class %s shape definition %s and size definition %s do not match" % (classname, shape, size)
                                          
        # create the new class   
        newcls = super(MetaMayaArrayTypeWrapper, mcl).__new__(mcl, classname, bases, classdict)

        try :
            apicls = newcls.apicls 
        except :
            apicls = None        
        try :
            shape = newcls.shape 
        except :
            shape = None
        try :
            cnames = newcls.cnames
        except :
            cnames = ()
            
        if shape is not None :
            # fixed shape means also fixed ndim and size
            ndim = len(shape)
            size = reduce(operator.mul, shape, 1)
            
            if cnames :
                # definition for component names
                type.__setattr__(newcls, 'cnames', cnames ) 
                subsizes = [reduce(operator.mul, shape[i+1:], 1) for i in xrange(ndim)]
                for index, compname in enumerate(cnames) :
                    coords = []
                    for i in xrange(ndim) :
                        c = index//subsizes[i]
                        index -= c*subsizes[i]
                        coords.append(c)
                    if len(coords) == 1 :
                        coords = coords[0]
                    else :
                        coords = tuple(coords)
                    p = eval("property( lambda self: self.__getitem__(%s) ,  lambda self, val: self.__setitem__(%s,val) )" % (coords, coords))
                    if compname not in classdict :
                        type.__setattr__(newcls, compname, p)
                    else :
                        raise AttributeError, "component name %s clashes with class method %r" % (compname, classdict[compname])                 
        elif cnames :
            raise ValueError, "can only define component names for classes with a fixed shape/size"
         
        # constants for shape, ndim, size
        if shape is not None :
            type.__setattr__(newcls, 'shape', shape)
        if ndim is not None :
            type.__setattr__(newcls, 'ndim', ndim)
        if size is not None :
            type.__setattr__(newcls, 'size', size)                        
        #__slots__ = ['_data', '_shape', '_size']    
        # add component names to read-only list
        readonly = newcls.__readonly__
        if hasattr(newcls, 'shape') :
            readonly['shape'] = None 
        if hasattr(newcls, 'ndim') :
            readonly['ndim'] = None  
        if hasattr(newcls, 'size') :
            readonly['size'] = None                                 
        if 'cnames' not in readonly :
            readonly['cnames'] = None
        type.__setattr__(newcls, '__readonly__', readonly)      

        print "created class", newcls
        print "bases", newcls.__bases__
        print "readonly", newcls.__readonly__
        print "slots", newcls.__slots__
        return newcls  