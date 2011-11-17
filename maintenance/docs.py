import sys
import os, glob, shutil
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
    from sphinx.ext.autosummary.generate import main

    os.chdir( os.path.join(docsdir) )
    if os.path.exists(BUILD):
        print "removing", os.path.join(docsdir, BUILD)
        shutil.rmtree(BUILD)

    os.chdir( os.path.join(docsdir,SOURCE) )
    if os.path.exists('generated'):
        print "removing", os.path.join(docsdir,SOURCE,'generated')
        shutil.rmtree('generated')

    main( [''] + '--templates ../templates index.rst'.split() )
    main( [''] + '--templates ../templates'.split() + glob.glob('generated/pymel.*.rst') )

def clean_build():
    builddir = os.path.join(docsdir, BUILD)
    if os.path.exists(builddir):
        print "removing", builddir
        shutil.rmtree(builddir)

def clean_generated():
    gendir = os.path.join(docsdir,SOURCE, 'generated')
    if os.path.exists(gendir):
        print "removing", gendir
        shutil.rmtree(gendir)

def build(clean=True,  **kwargs):
    from sphinx import main
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
        if os.name == 'posix':
            dots = ['/usr/local/bin/dot', '/usr/bin/dot']
        else:
            dots = ['C:\\graphviz\\bin\\dot.exe']
        dot = None
        for d in dots:
            if os.path.exists(d):
                dot = d
                break
        if not dot:
            raise TypeError( 'cannot find graphiz dot executable in the following locations: %s' % ', '.join(dots) )
        kwargs['graphviz_dot'] = dot
    
    for key, value in kwargs.iteritems():
        opts.append('-D')
        opts.append( key.strip() + '=' + value.strip() )
    opts.append(SOURCE)
    opts.append(BUILD)
    main(opts)
