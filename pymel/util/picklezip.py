import gzip
try:
    import cPickle as pickle
except:
    import pickle

def dump(object, filename, protocol=-1):
    """
    Save an compressed pickle to disk.
    """
    file = gzip.GzipFile(filename, 'wb')
    try:
        pickle.dump(object, file, protocol)
    finally:
        file.close()

def load(filename):
    """
    Load a compressed pickle from disk
    """
    file = gzip.GzipFile(filename, 'rb')
    try:
        buffer = ""
        while 1:
            data = file.read()
            if data == "":
                break
            buffer += data
        object = pickle.loads(buffer)
        return object
    finally:
        file.close()