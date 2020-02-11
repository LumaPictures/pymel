from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import *
def __getattribute__(self, name):
    if name in {{ method.removeAttrs }} and name not in _f.EXCLUDE_METHODS:  # tmp fix
        raise AttributeError("'{{ classname }}' object has no attribute '" + name + "'")
    return super({{ classname }}, self).__getattribute__(name)