import sys
import pydoc
import types
import inspect
import os

INDENT = 4

def printobj(name, obj, prefix='', depth=0, file=sys.stdout):
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        try:
            spec = inspect.getargspec(obj)
            sig = inspect.formatargspec(*spec)
        except:
            sig = '(<error>)'
        # file.write((' ' * (depth * INDENT)) + name + sig + '\n')
        file.write(prefix + name + sig + '\n')
    else:
        # file.write((' ' * (depth * INDENT)) + name + '\n')
        file.write(prefix + name + '\n')

    # print depth, isinstance(obj, (type, types.ModuleType))
    if (depth < 2 and isinstance(obj, type)) or (depth == 0 and isinstance(obj, types.ModuleType)):
        childprefix = prefix + name + '.'
        for childname in sorted(dir(obj)):
            try:
                child = getattr(obj, childname)
            except:
                child = None
            printobj(childname, child, prefix=childprefix, depth=depth + 1, file=file)


def main(objname):
    obj = pydoc.locate(objname)
    printobj(objname, obj)


def writemods(branch, output):
    for modname in ['nodetypes', 'uitypes', 'datatypes', 'general']:
        fullname = 'pymel.core.' + modname
        mod = __import__(fullname, globals(), locals(), [''])
        print mod
        path = os.path.join(output, '%s@%s.txt' % (fullname, branch))
        with open(path, 'w') as f:
            printobj(fullname, mod, file=f)
