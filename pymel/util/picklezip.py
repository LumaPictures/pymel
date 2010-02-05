import gzip
try:
    import cPickle as pickle
except:
    import pickle

__all__ = ['dump', 'load']

def dump(object, filename, protocol=-1):
    """
    Save an compressed pickle to disk.
    """
    file = gzip.GzipFile(filename, 'wb')
    try:
        pickle.dump(object, file, protocol)
    finally:
        file.close()


def _loads(filename):
    """
    Load a compressed pickle from disk to an upicklable string
    """
    file = gzip.GzipFile(filename, 'rb')
    try:
        buffer = ""
        while 1:
            data = file.read()
            if data == "":
                break
            buffer += data
        return buffer
    finally:
        file.close()

def load(filename):
    """
    Load a compressed pickle from disk
    """
    return pickle.loads(_loads(filename))
