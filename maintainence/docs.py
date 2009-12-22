import sys
#assert 'pymel' not in sys.modules, "in order to generate docs properly pymel cannot
import os, glob, shutil
os.environ['PYMEL_INCLUDE_EXAMPLES'] = 'True'
import pymel
# make sure dynamic modules are fully loaded
from pymel.core.uitypes import *
from pymel.core.nodetypes import *

docsdir = os.path.join( os.path.dirname(os.path.dirname( pymel.__file__)), 'docs') 
              
def generate():
    from sphinx.ext.autosummary.generate import main
    os.chdir( os.path.join(docsdir,'source') )
    if os.path.exists('generated'):
        shutil.rmtree('generated')
    main( [''] + '--templates _templates index.rst'.split() )
    main( [''] + '--templates _templates'.split() + glob.glob('generated/pymel.*.rst') )
    
def build():
    from sphinx import main
    os.chdir( docsdir )
    #mkdir -p build/html build/doctrees
    main( [''] + '-b html -d build/doctrees source build/html'.split() )
