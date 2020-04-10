from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from future.utils import PY2

def trystr(input):
    '''If the input is unicode, but just holds normal ascii, convert to str'''
    if PY2:
        if isinstance(input, unicode):
            try:
                return str(input)
            except UnicodeEncodeError:
                pass
    return input