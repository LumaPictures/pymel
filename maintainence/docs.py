import sys
#assert 'pymel' not in sys.modules, "in order to generate docs properly pymel cannot
import os, glob, shutil
os.environ['PYMEL_INCLUDE_EXAMPLES'] = 'True'
import pymel
# make sure dynamic modules are fully loaded
from pymel.core.uitypes import *
from pymel.core.nodetypes import *

docsdir = os.path.join( os.path.dirname(os.path.dirname( pymel.__file__)), 'docs')

version = pymel.__version__.rsplit('.',1)[0]
SOURCE = 'source'
BUILD = 'build/' + version

def generate():
    from sphinx.ext.autosummary.generate import main

    os.chdir( os.path.join(docsdir) )
    if os.path.exists(BUILD):
        print "removing", os.path.join(docsdir,BUILD)
        shutil.rmtree(BUILD)

    os.chdir( os.path.join(docsdir,SOURCE) )
    if os.path.exists('generated'):
        print "removing", os.path.join(docsdir,SOURCE,BUILD)
        shutil.rmtree('generated')

    main( [''] + '--templates ../templates index.rst'.split() )
    main( [''] + '--templates ../templates'.split() + glob.glob('generated/pymel.*.rst') )

def build(**kwargs):
    from sphinx import main
    os.chdir( docsdir )
    #mkdir -p build/html build/doctrees

    opts = ['']
    opts += '-b html -d build/doctrees'.split()
    for key, value in kwargs.iteritems():
        opts.append('-D')
        opts.append( key.strip() + '=' + value.strip() )
    opts.append(SOURCE)
    opts.append( BUILD )
    main(opts)
