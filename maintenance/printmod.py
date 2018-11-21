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

DEFAULT_MODULES = (
    # core / class modules
    'nodetypes',
    'uitypes',
    'datatypes',
    'general',
    # mostly function wrap modules
    'animation',
    'context',
    'effects',
    'language',
    'modeling',
    'other',
    'rendering',
    #'runtime',
    'system',
    'windows',
)

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

def printobj(name, obj, prefix='', inherited=False, depth=0, file=sys.stdout):
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        beforeDeprecation = getattr(obj, '_func_before_deprecation', None)
        if beforeDeprecation is not None:
            obj = beforeDeprecation
        try:
            spec = inspect.getargspec(obj)
            sig = inspect.formatargspec(*spec)
        except Exception:
            sig = '(<error>)'
        if beforeDeprecation is not None:
            sig = '{} <deprecated>'.format(sig)
    elif inspect.isclass(obj):
        if depth > 1 and name in ('__metaclass__', '__class__', '__apicls__',
                                  'apicls'):
            sig = ' = {}'.format(obj.__name__)
        else:
            sig = '({})'.format(', '.join(x.__name__ for x in obj.__bases__))
    else:
        sig = ''
    if inherited:
        sig += ' <inherited>'

    # file.write((' ' * (depth * INDENT)) + name + sig + '\n')
    file.write(prefix + name + sig + '\n')

    # print depth, isinstance(obj, (type, types.ModuleType))

    # we DON'T want to recurse LazyLoadModule class objects, because we don't
    # want to have BOTH of these (now that we've fixed the dir for
    # LazyLoadModule) :
    #    pymel.core.nodetypes.SomePluginNode
    #    pymel.core.nodetypes.NodetypesLazyLoadModule.SomePluginNode
    if (
            (depth < 2 and isinstance(obj, type)
                and not issubclass(obj, types.ModuleType))
            or (depth == 0 and isinstance(obj, types.ModuleType))
    ):
        childprefix = prefix + name + '.'

        def iterChildren():
            '''Yields (childname, inherited) tuples'''

            # have an exception for modules, both because they don't
            # have inheritance, and because LazyLoadModule has a bunch
            # of stuff that doesn't show up in __dict__, but does in
            # dir()
            if isinstance(obj, types.ModuleType):
                for child in sorted(dir(obj)):
                    yield child, False
                return

            # we used to sort such that all non-inherited members came before
            # all inherited members. While this makes for a nicer readable
            # grouping for humans (we'll mostly be interested in see the
            # non-inherited members first), the different orderings makes it
            # harder for automated comparison, when you want to filter out
            # certain items where you don't care if they're inherited or not
            # (ie, when using filters in the meld merge tool)
            if hasattr(obj, '__dict__'):
                directChildren = set(obj.__dict__)
            else:
                directChildren = set()

            for child in sorted(dir(obj)):
                yield child, child not in directChildren

        for childname, inherited in iterChildren():
            try:
                child = getattr(obj, childname)
            except AttributeError:
                # some things may be returned in dir, but not be accessible -
                # one example is any abstract base class (__metaclass__ =
                # ABCMeta), which will have an __abstractmethods__ slot, but it
                # may not actually be filled. We ignore any getattr errors.
                continue
            printobj(childname, child, prefix=childprefix, inherited=inherited,
                     depth=depth + 1, file=file)

def writemods(branch, output, modules=None):
    import linecache

    git(['checkout', branch])
    hash = githash()
    if hash != branch:
        commit = '{}@{}'.format(branch, hash)
    else:
        commit = hash
    outpath = os.path.join(output, commit)
    if not os.path.isdir(outpath):
        os.makedirs(outpath)
    if not modules:
        modules = DEFAULT_MODULES

    # now that we've done a git checkout, need to make sure reload all the
    # modules, and any parent packages - ie, pymel, pymel.core,
    # pymel.core.nodetypes, ...
    toReload = set()
    for modname in modules:
        splitname = modname.split('.')
        for i in xrange(1, len(splitname) + 1):
            toReload.add('.'.join(splitname[:i]))

    for mod in list(sys.modules):
        if mod in toReload:
            del sys.modules[mod]
    linecache.clearcache()

    for modname in modules:
        fullnames = (modname, 'pymel.core.' + modname)
        for fullname in fullnames:
            try:
                mod = __import__(fullname, globals(), locals(), [''])
                break
            except Exception:
                pass
        else:
            raise RuntimeError("failed to import module {!r} or {!r}"
                               .format(*fullnames))
        __import__(fullname)
        # instead of using result returned from __import__, we grab the module
        # from sys.modules - this is because of LazyLoadModule shenannigans -
        # __import__ will return the original module, while we want the
        # LazyLoadModule that replaces it
        mod = sys.modules[fullname]
        print mod
        path = os.path.join(outpath, '{}.txt'.format(fullname))
        with open(path, 'w') as f:
            printobj(fullname, mod, file=f)

def getparser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-b', '--branch', default='master',
        help='git branch to checkout')
    parser.add_argument('-o', '--output-dir', default='pymel_modules',
        help="Directory to which to write out pymel module information")
    parser.add_argument('-m', '--module', dest='modules', action='append',
        help="What pymel modules to print out; may be specified multiple times"
             " to specify multiple modules; modules should be specified using"
             " the import name (ie, 'pymel.core.nodetypes'); if a module fails"
             " to import, it will assume it is in 'pymel.core' (so you may just"
             " use 'nodetypes'); if not given at all, the default set of"
             " modules is: {}".format(', '.join(DEFAULT_MODULES)))
    parser.add_argument('--traceback', action='store_true',
        help="If given, will print full tracebacks on errors")
    parser.add_argument('--no-gui', action='store_true',
        help="By default, will run under a gui maya session, to get all"
             " commands / etc.  Use this flag to disable this.")
    return parser

def main(argv=None):
    sys.path.insert(0, PYMEL_ROOT)

    if argv is None:
        argv = sys.argv[1:]
    parser = getparser()
    args = parser.parse_args(argv)

    if not args.no_gui:
        import subprocess

        newArgs = list(argv)
        newArgs.insert(0, '--no-gui')

        # assume that sys.executable is mayapy, and look for maya(.exe) relative to it
        mayaBinDir = os.path.dirname(sys.executable)
        mayaBin = os.path.join(mayaBinDir, 'maya')
        if os.name == 'nt':
            mayaBin += '.exe'
        newArgs.insert(0, mayaBin)

        pyCmd = 'import sys; sys.argv = {!r}; execfile({!r})'.format(newArgs,
                                                                     THIS_FILE)
        melCmd = 'python("{}")'.format(pyCmd.replace('\\', '\\\\')
                                       .replace('"', r'\"'))
        mayaArgs = [mayaBin, '-command', melCmd]
        sys.exit(subprocess.call(mayaArgs))

    try:
        writemods(args.branch, args.output_dir, modules=args.modules)
    except Exception as e:
        if args.traceback:
            raise
        print e
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())