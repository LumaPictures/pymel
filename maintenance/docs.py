import sys
import os, glob, shutil
from sphinx import main as sphinx_build
from sphinx.ext.autosummary.generate import main as sphinx_autogen

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
BUILD = os.path.join('build', version)

from pymel.internal.cmdcache import fixCodeExamples

def generate():
    "delete build and generated directories and generate a top-level documentation source file for each module."

    clean_build()
    clean_generated()
    os.chdir( os.path.join(docsdir,SOURCE) )

    sphinx_autogen( [''] + '--templates ../templates index.rst'.split() )
    sphinx_autogen( [''] + '--templates ../templates'.split() + glob.glob('generated/pymel.*.rst') )

def clean_build():
    "delete existing build directory"
    builddir = os.path.join(docsdir, BUILD)
    if os.path.exists(builddir):
        print "removing", builddir
        shutil.rmtree(builddir)

def clean_generated():
    "delete existing generated directory"
    gendir = os.path.join(docsdir,SOURCE, 'generated')
    if os.path.exists(gendir):
        print "removing", gendir
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
    raise TypeError('cannot find graphiz dot executable in the path')

def build(clean=True, **kwargs):
    os.chdir( docsdir )
    if clean:
        clean_generated()
        clean_build()

    #mkdir -p build/html build/doctrees

    #import pymel.internal.cmdcache as cmdcache
    #cmdcache.fixCodeExamples()
    opts = ['']
    opts += '-b html -d build/doctrees'.split()

    # set some defaults
    if 'graphviz_dot' not in kwargs:
        kwargs['graphviz_dot'] = find_dot()

    for key, value in kwargs.iteritems():
        opts.append('-D')
        opts.append( key.strip() + '=' + value.strip() )
    opts.append('-P')
    opts.append(SOURCE)
    opts.append(BUILD)
    sphinx_build(opts)
