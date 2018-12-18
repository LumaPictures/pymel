#!/usr/bin/env python

'''Package up a pymel release.'''

# Ideally this should use the python interpreter used by mayapy, but without LD_LIBRARY_PATH or PYTHONHOME set

import argparse
import inspect
import re
import subprocess
import sys
import zipfile
import os
from shutil import rmtree, copytree
from os.path import join, dirname, exists
from subprocess import check_output, check_call


THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = dirname(THIS_FILE)


if os.name == 'nt':
    def which(executable):
        output = check_output(["where", executable])
        # where returns multiple results, one per line, in the order it
        # finds them - we only want the first
        return output.strip().split('\n')[0].strip()
else:
    def which(executable):
        return check_output(["which", executable]).strip()


def unload_pymel_modules():
    import linecache

    for name in list(sys.modules):
        splitname = name.split('.')
        if splitname[0] in 'pymel':
            del sys.modules[name]
            assert name not in sys.modules
    linecache.clearcache()


def make_new_caches(release_dir, new_ext=".pyc.zip"):
    # need to run in a subprocess, so we can use mayapy
    print "looking for mayapy..."
    mayapy = which("mayapy")
    if not mayapy:
        msg = "ERROR: couldn't find a mayapy executable!"
        raise RuntimeError(msg)
    print "found mayapy: {}".format(mayapy)

    cmd = '''import maintenance.makerelease
maintenance.makerelease._make_new_caches({!r}, new_ext={!r})'''.format(
        release_dir, new_ext)
    environ = dict(os.environ)
    pypath = environ.get('PYTHONPATH')
    if not pypath:
        pypath = release_dir
    else:
        pypath = os.pathsep.join(release_dir, pypath)
    environ['PYTHONPATH'] = pypath
    args = [mayapy, "-c", cmd]
    print "running: {!r}".format(args)
    check_call(args, cwd=release_dir, env=environ)


def _make_new_caches(release_dir, new_ext=".py.zip"):
    import pymel.internal.apicache as apicache
    import pymel.internal.cmdcache as cmdcache
    def assert_src(module):
        abs_module = os.path.normpath(os.path.abspath(module.__file__))
        if not abs_module.startswith(release_dir):
            raise RuntimeError("{} must be loaded from {} - instead from: {}"
                               .format(module.__name__, src_root,
                                       abs_module))
    assert_src(apicache)
    assert_src(cmdcache)

    release_cache_dir = join(release_dir, "pymel", "cache")

    all_versions = apicache.ApiCache.allVersions()
    caches = (apicache.ApiCache, apicache.ApiMelBridgeCache, cmdcache.CmdCache,
              cmdcache.CmdExamplesCache, cmdcache.CmdDocsCache)
    caches_by_name = {cache_type.NAME: cache_type for cache_type in caches}
    found_caches = {}

    for cachename in os.listdir(release_cache_dir):
        fullcache = os.path.join(release_cache_dir, cachename)
        for format in apicache.ApiCache.FORMATS:
            if cachename.endswith(format.ext):
                ext = format.ext
                cachebase = cachename[:-len(ext)]
                break
        else:
            raise RuntimeError("unrecognized extension for cache: {}"
                               .format(fullcache))
        for version in all_versions:
            if cachebase.endswith(version):
                cachebase = cachebase[:-len(version)]
                break
        else:
            version = None

        cache_type = caches_by_name[cachebase]
        if version is None:
            if cache_type.USE_VERSION:
                raise RuntimeError("Caches of type {} should have a version -"
                                   " found versionless cache: {}"
                                   .format(cachebase, fullcache))
        else:
            if not cache_type.USE_VERSION:
                raise RuntimeError("Caches of type {} should not have a version"
                                   " - found versioned cache: {}"
                                   .format(cachebase, fullcache))
        cachekey = (cachebase, version)
        existing = found_caches.get(cachekey)
        if existing:
            raise RuntimeError("More than one cache of the same type / version;"
                               " remove one from the repository: {} - {}"
                               .format(cachename, existing))
        found_caches[cachekey] = cachename

        cache_obj = cache_type()
        if version is not None:
            cache_obj.version = version
        data = cache_obj.read()
        print "Writing out {} as {}...".format(cachename, new_ext)
        cache_obj.write(data, ext=new_ext)
        if (not os.path.isfile(cache_obj._lastWritePath)
                or not cache_obj._lastWritePath.endswith(new_ext)):
            raise RuntimeError("error writing out {} as a {} cache"
                               .format(fullcache, new_ext))
        os.remove(fullcache)
        print "...success, removed {}".format(fullcache)


def makerelease(full_ver, maintenance=THIS_DIR):
    baseVer = re.split('[a-zA-Z]', full_ver)[0]
    print "Release version is %r" % full_ver
    print "Release base version is %r" % baseVer

    os.chdir(maintenance)

    src_root = dirname(maintenance)
    extras_dir = join(src_root, "extras")
    completion_dir = join(extras_dir, "completion")
    completion_py_dir = join(completion_dir, "py")
    release_base = join(maintenance, "release")
    release_dir = join(release_base, "pymel-{}".format(full_ver))
    release_zip = release_dir + '.zip'

    print "release directory:", release_dir

    if not os.path.isdir(release_base):
        os.mkdir(release_base)

    sys.path.insert(0, src_root)

    import pymel
    print "current pymel version is: %r" % pymel.__version__
    assert pymel.__file__.startswith(src_root)
    if pymel.__version__ != baseVer:
        raise RuntimeError("current pymel version {} does not match release"
                           " version {}".format(pymel.__version__, baseVer))
    assert pymel.__version__ == baseVer
    unload_pymel_modules()

    print "checking completion stubs"
    assert os.path.isdir(completion_py_dir)
    sys.path.insert(0, completion_py_dir)
    try:
        import pymel
        assert pymel.__file__.startswith(completion_py_dir)
        print "current stub version is: %r" % pymel.__version__
        if pymel.__version__ != baseVer:
            raise RuntimeError("current pymel stub version {} does not match"
                               " release version {}".format(pymel.__version__,
                                                            baseVer))
        unload_pymel_modules()
    finally:
        sys.path.pop(0)

    try:
        check_call(["python", "-m", "maintenance.stubs", "-o",
                    completion_dir, "--test"],
                   cwd=src_root)
    except subprocess.CalledProcessError as e:
        import traceback
        raise RuntimeError("ERROR: completion stubs are not working: {}"
                           .format(e))

    # clean out git stuff

    for root, dirs, files in os.walk(extras_dir):
        for name in files:
            if name.endswith('.pyc'):
                os.remove(join(root, name))

    #if [ ! -d ../extras/completion/pi ]; then
    #   print "ERROR: wing completion stubs do not exist"
    #fi

    if exists(release_dir):
        print "removing existing folder"
        rmtree(release_dir)

    if exists(release_zip):
        print "removing existing zip"
        os.remove(release_zip)

    args = ['git', 'clone', '--shared', src_root, release_dir]
    print args
    check_call(args)
    assert os.path.isdir(release_dir)

    sys.path.insert(0, release_dir)
    try:
        import pymel
        try:
            print "release pymel version is: %r" % pymel.__version__
            assert pymel.__file__.startswith(src_root)
            if pymel.__version__ != baseVer:
                raise RuntimeError("current release version {} does not match release"
                                   " version {}".format(pymel.__version__, baseVer))
            assert pymel.__version__ == baseVer
        finally:
            unload_pymel_modules()
    finally:
        sys.path.pop(0)


    def rmprefix(folder, prefix):
        for item in os.listdir(folder):
            if item.startswith(prefix):
                fullitem = join(release_dir, item)
                if os.path.isdir(fullitem):
                    print "removing dir: {}".format(fullitem)
                    rmtree(fullitem)
                else:
                    print "removing file: {}".format(fullitem)
                    os.remove(fullitem)

    rmprefix(release_dir, '.git')

    # make .pyc.zip versions of caches
    make_new_caches(release_dir, src_root)

    rmtree(join(release_dir, "maintenance"))

    print "copying docs"
    rmtree(join(release_dir, 'docs'))
    copytree(join(src_root, 'docs', 'build', '1.0'),
             join(release_dir, 'docs'))

    print "copying stubs"
    copytree(join(src_root, 'extras', 'completion'),
             join(release_dir, 'extras', 'completion'))

    git_rev = check_output(['git', 'rev-parse', 'HEAD'])

    with open(join(release_dir, 'README'), 'a') as f:
        print "adding version info"
        f.write("\n")
        f.write("Release ver: %s\n" % full_ver)
        f.write("Pymel ver: %s\n" % baseVer)
        f.write("Git commit: %s\n" % git_rev)

    print "zipping"
    with zipfile.ZipFile(release_zip, "w") as f:
        for root, dirs, files in os.walk(release_dir):
            for name in files:
                f.write(join(root, name))


def get_parser():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('fullVersion', help="the full pymel release version")
    return parser


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(argv)
    makerelease(args.fullVersion)


if __name__ == '__main__':
    main()
