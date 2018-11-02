#!/usr/bin/env mayapy
'''Print out a contents of the core pymel modules in a text format that can be diffed
'''

import sys
import pydoc
import types
import inspect
import os
import argparse
import subprocess

INDENT = 4

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)
PYMEL_ROOT = os.path.dirname(THIS_DIR)

def git(arg, output=False):
    if isinstance(arg, basestring):
        args = arg.split()
    else:
        args = arg
    if output:
        func = subprocess.check_output
    else:
        func = subprocess.check_call
    return func(['git'] + list(args), cwd=PYMEL_ROOT)

def gitout(arg):
    return git(arg, output=True).rstrip()

def githash(branch='HEAD'):
    return gitout(['show', '-s', '--format=%H', branch])

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

def writemods(branch, output):
    git(['checkout', branch])
    hash = githash()
    if hash != branch:
        commit = '{}-{}'.format(branch, hash)
    else:
        commit = hash
    if not os.path.isdir(output):
        os.makedirs(output)
    for modname in ['nodetypes', 'uitypes', 'datatypes', 'general']:
        fullname = 'pymel.core.' + modname
        mod = __import__(fullname, globals(), locals(), [''])
        print mod
        path = os.path.join(output, '%s@%s.txt' % (fullname, commit))
        with open(path, 'w') as f:
            printobj(fullname, mod, file=f)

def getparser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-b', '--branch', default='master',
        help='git branch to checkout (and add to output filenames)')
    parser.add_argument('-o', '--output-dir', default='pymel_modules',
        help="Directory to which to write out pymel module information")
    return parser

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = getparser()
    args = parser.parse_args(argv)
    writemods(args.branch, args.output_dir)

if __name__ == '__main__':
    main()