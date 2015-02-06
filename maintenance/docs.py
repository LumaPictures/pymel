import sys
import os
import glob
import shutil
import datetime

assert 'pymel' not in sys.modules or 'PYMEL_INCLUDE_EXAMPLES' in os.environ, "to generate docs PYMEL_INCLUDE_EXAMPLES env var must be set before pymel is imported"

# remember, the processed command examples are not version specific. you must
# run cmdcache.fixCodeExamples() to bring processed examples in from the raw
# version-specific example caches
os.environ['PYMEL_INCLUDE_EXAMPLES'] = 'True'

pymel_root = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))
docsdir = os.path.join(pymel_root, 'docs')
stubdir = os.path.join(pymel_root, 'extras', 'completion', 'py')

useStubs = False

if useStubs:
    sys.path.insert(0, stubdir)
    import pymel
    print pymel.__file__
else:
    import pymel
    # make sure dynamic modules are fully loaded
    from pymel.core.uitypes import *
    from pymel.core.nodetypes import *

version = pymel.__version__.rsplit('.',1)[0]
SOURCE = 'source'
BUILD_ROOT = 'build'
BUILD = os.path.join(BUILD_ROOT, version)
sourcedir = os.path.join(docsdir, SOURCE)
gendir = os.path.join(sourcedir, 'generated')
buildrootdir = os.path.join(docsdir, BUILD_ROOT)
builddir = os.path.join(docsdir, BUILD)

from pymel.internal.cmdcache import fixCodeExamples

def generate(clean=True):
    "delete build and generated directories and generate a top-level documentation source file for each module."
    print "generating %s - %s" % (docsdir, datetime.datetime.now())
    from sphinx.ext.autosummary.generate import main as sphinx_autogen

    if clean:
        clean_build()
        clean_generated()
    os.chdir(sourcedir)

    sphinx_autogen( [''] + '--templates ../templates index.rst'.split() )
    sphinx_autogen( [''] + '--templates ../templates'.split() + glob.glob('generated/pymel.*.rst') )
    print "...done generating %s - %s" % (docsdir, datetime.datetime.now())

def clean_build():
    "delete existing build directory"
    if os.path.exists(buildrootdir):
        print "removing %s - %s" % (buildrootdir, datetime.datetime.now())
        shutil.rmtree(buildrootdir)

def clean_generated():
    "delete existing generated directory"
    if os.path.exists(gendir):
        print "removing %s - %s" % (gendir, datetime.datetime.now())
        shutil.rmtree(gendir)

def find_dot():
    if os.name == 'posix':
        dot_bin = 'dot'
    else:
        dot_bin = 'dot.exe'

    for p in os.environ['PATH'].split(os.pathsep):
        d = os.path.join(p, dot_bin)
        if os.path.exists(d):
            return d
    raise TypeError('cannot find graphiz dot executable in the path (%s)' % os.environ['PATH'])

def copy_changelog():
    changelog = os.path.join(pymel_root, 'CHANGELOG.rst')
    whatsnew = os.path.join(pymel_root, 'docs', 'source', 'whats_new.rst')
    shutil.copy2(changelog, whatsnew)

def build(clean=True, **kwargs):
    from sphinx import main as sphinx_build
    print "building %s - %s" % (docsdir, datetime.datetime.now())

    if not os.path.isdir(gendir):
        generate()

    os.chdir( docsdir )
    if clean:
        clean_build()

    copy_changelog()

    #mkdir -p build/html build/doctrees

    #import pymel.internal.cmdcache as cmdcache
    #cmdcache.fixCodeExamples()
    opts = ['']
    opts += '-b html -d build/doctrees'.split()

    # set some defaults
    if not kwargs.get('graphviz_dot', None):
        kwargs['graphviz_dot'] = find_dot()

    for key, value in kwargs.iteritems():
        opts.append('-D')
        opts.append( key.strip() + '=' + value.strip() )
    opts.append('-P')
    opts.append(SOURCE)
    opts.append(BUILD)
    sphinx_build(opts)
    print "...done building %s - %s" % (docsdir, datetime.datetime.now())

