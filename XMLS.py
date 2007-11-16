#!/usr/bin/env python

"""
XMLS.py
Authors: cdh

Packs and unpacks objects to and from xml strings.
 Supported Types:
  str
  int
  float
  list
  dict
  classes using above types (nesting supported)

"""
from xml.etree import ElementTree as et
import sys;

__all__ = ["Pack","Unpack"]


def Pack(obj):
    """
    Packs an object into an xml string.
    """
    return et.tostring(__pack_obj__(obj))
        
def Unpack(xml_string):
    """
    Unpacks an object from an xml string.
    """
    obj_name, obj = __unpack_obj__(et.fromstring(xml_string))
    return obj
        
def __pack_obj__(obj,obj_name = None, parent = None):
    """
    Packs an object into an xml node.
    """
    if obj is None:
        return __pack_none__(obj_name,parent)
    if obj is True or obj is False:
        return __pack_bool__(obj,obj_name,parent)
    if isinstance(obj,str):
        return __pack_str__(obj,obj_name,parent)
    elif isinstance(obj,int):
        return __pack_int__(obj,obj_name,parent)
    elif isinstance(obj,float):
        return __pack_float__(obj,obj_name,parent)
    elif isinstance(obj,list):
        return __pack_list__(obj,obj_name,parent)
    elif isinstance(obj,dict):
        return __pack_dict__(obj,obj_name,parent)
    else:
        obj_type =  obj.__class__.__name__
        obj_mod  =  obj.__class__.__module__
        if obj_name == None:
            obj_name = obj_type + "_obj"
        if parent == None:
            node = et.Element(obj_name,otype=obj_type, omodule = obj_mod)
        else:
            node = et.SubElement(parent,obj_name,otype=obj_type, omodule = obj_mod)
        try:
            ignore = obj._xmls_ignore_
        except:
            ignore = None
        for k,v in obj.__dict__.items():
            if ignore is None:
                __pack_obj__(v,k,node)
            elif not k in ignore:
                __pack_obj__(v,k,node)
        return node

def __unpack_obj__(node):
    """
    Unpacks an object from an xml node.
    """
    obj_type = node.attrib["otype"]
    if obj_type =="none":
        return __unpack_none__(node)
    if obj_type =="boolean":
        return __unpack_bool__(node)
    if obj_type == "str":
        return __unpack_str__(node)
    elif obj_type == "int":
        return __unpack_str__(node)
    elif obj_type == "float":
        return __unpack_float__(node)
    elif obj_type == "list":
        return __unpack_list__(node)
    elif obj_type == "dict":
        return __unpack_dict__(node)
    else:
        obj_name = node.tag
        obj_mod  = node.attrib["omodule"]
        obj = __inst_class__(obj_mod,obj_type)
    for n in node:
        k,v = __unpack_obj__(n)
        obj.__dict__[k]= v
    return  obj_name,obj


def __pack_none__(obj_name = None, parent = None):
    """
    Creates a node that points to None.
    """
    if obj_name == None:
        obj_name = "none_obj"
    if parent == None:
        node = et.Element(obj_name,otype="none")
    else:
        node = et.SubElement(parent,obj_name,otype="none")
    return node

def __unpack_none__(node):
    """
    Unpacks a reference to None.
    """
    return node.tag, None
    
def __pack_bool__(obj,obj_name = None, parent = None):
    """
    Packs a boolean into an xml node.
    """
    if obj_name == None:
        obj_name = "bool_obj"
    if parent == None:
        node = et.Element(obj_name,otype="bool")
    else:
        node = et.SubElement(parent,obj_name,otype="bool")
    if obj is True:
        node.text = "True"
    else:
        node.text = "False"
    return node

def __unpack_bool__(node):
    """
    Unpacks a boolan from an xml node.
    """
    if node.txt == "True":
        res = True
    else:
        res = False
    return node.tag, res

def __pack_str__(obj,obj_name = None,parent = None):
    """
    Packs a string into an xml node.
    """
    if obj_name == None:
        obj_name = "string_obj"
    if parent == None:
        node = et.Element(obj_name,otype="str")
    else:
        node = et.SubElement(parent,obj_name,otype="str")
    node.text = obj
    return node

def __unpack_str__(node):
    """
    Unpacks a string from an xml node.
    """
    return node.tag, node.text

def __pack_int__(obj,obj_name = None,parent = None):
    """
    Packs an integer into an xml node.
    """
    if obj_name == None:
        obj_name = "integer_obj"
    if parent == None:
        node = et.Element(obj_name,otype="int")
    else:
        node = et.SubElement(parent,obj_name,otype="int")
    node.text = str(obj)
    return node

def __unpack_int__(node):
    """
    Unpacks an integer from an xml node.
    """
    return node.tag, int(node.text)
        
def __pack_float__(obj,obj_name = None,parent = None):
    """
    Packs a float into an xml node.
    """
    if obj_name == None:
        obj_name = "float_obj"
    if parent == None:
        node = et.Element(obj_name,otype="float")
    else:
        node = et.SubElement(parent,obj_name,otype="float")
    node.text = str(obj);
    return node
        
def __unpack_float__(node):
    """
    Unpacks a float from an xml node.
    """
    return node.tag, float(node.text)

def __pack_list__(obj,obj_name = None,parent = None):
    """
    Packs a list into an xml node.
    """
    if obj_name == None:
        obj_name = "list_obj"
    if parent == None:
        node = et.Element(obj_name,otype="list")
    else:
        node = et.SubElement(parent,obj_name,otype="list")
    for itm in obj:
        __pack_obj__(itm, parent = node)
    return node
        
def __unpack_list__(node):
    """
    Unpacks a list from an xml node.
    """
    res = [];
    for n in node:
        obj_name , obj = __unpack_obj__(n)
        res.append(obj)
    return node.tag, res

def __pack_dict__(obj,obj_name = None,parent = None):
    """
    Packs a dictonary into an xml node.
    """
    if obj_name == None:
        obj_name = "dict_obj"
    if parent == None:
        node = et.Element(obj_name,otype="dict")
    else:
        node = et.SubElement(parent,obj_name,otype="dict")
    for key, itm in obj.items():
        __pack_obj__(itm, key, parent = node)
    return node
        
def __unpack_dict__(node):
    """
    Unpacks a dictonary from an xml node.
    """
    res = {};
    for n in node:
        obj_name, obj = __unpack_obj__(n)
        res[obj_name] = obj
    return node.tag, res

def __inst_class__(module,name):
    """
    Creates an instance of a class, given a module and class name.
    """
    __import__(module)
    omod = sys.modules[module]
    oclass = getattr(omod, name)
    return oclass()

if __name__ == '__main__':
    print "<Common::XMLS>"