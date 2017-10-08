import os
import sys
import inspect

THIS_FILE = os.path.abspath(inspect.getsourcefile(lambda: None))
THIS_DIR = os.path.dirname(THIS_FILE)

try:
    import pymel_test
except ImportError:
    if THIS_DIR not in sys.path:
        sys.path.append(THIS_DIR)
    import pymel_test

# wanted to use pytest_ignore_collect, but couldn't get that to work - it was never invoked...?
def pytest_collection_modifyitems(session, config, items):
    # iterate in reverse order, so indices stay good even if removed...
    origlen = len(items)
    for i in xrange(len(items) - 1 , -1 , -1):
        item = items[i]
        if item.name in pymel_test.EXCLUDE_TEST_NAMES:
            del items[i]
            continue
    newlen = len(items)
    if newlen != origlen:
        print "Deleted {} items - {} items left".format(origlen - newlen,
                                                        newlen)