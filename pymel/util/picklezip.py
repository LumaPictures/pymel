from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import gzip
try:
    import pickle as pickle
except:
    import pickle

__all__ = ['dump', 'load']


def dump(object, filename, protocol=-1):
    """
    Save an compressed pickle to disk.
    """
    with gzip.GzipFile(filename, 'wb') as f:
        pickle.dump(object, f, protocol)


def _loads(filename):
    """
    Load a compressed pickle from disk to an upicklable string
    """
    buffer = b""
    with gzip.GzipFile(filename, 'rb') as f:
        while 1:
            data = f.read()
            if data == b"":
                break
            buffer += data
    return buffer


def load(filename):
    """
    Load a compressed pickle from disk
    """
    return pickle.loads(_loads(filename))
