#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

def getInput():
    res = raw_input( '> install ipymel, customized ipython interpreter (y/N) [n]:' )
    if res.lower() in ['n', 'no']:
        return False
    elif res.lower() in ['y', 'yes']:
        return True
    else:
        print "* Please enter either 'y' or 'n'."
        return getInput()

requires = ['BeautifulSoup >3.0', 'ply >2.0, <3.0' ]
entry_points = {}
install_ipymel = False
try:
    import IPython
    install_ipymel = True
except ImportError:
    if getInput():
        install_ipymel = True
        requires.append( 'ipython' )

if install_ipymel:
    entry_points['console_scripts'] = ['ipymel = pymel.tools.ipymel:main [ipymel]']


setup(name='pymel',
      version='0.9.1',
      description='Python in Maya Done Right',
      long_description = """
PyMEL makes python scripting with Maya work the way it should. Maya's command module is a direct translation
of mel commands into python commands. The result is a very awkward and unpythonic syntax which does not take 
advantage of python's strengths -- particulary, a flexible, object-oriented design. PyMEL builds on the cmds 
module by organizing many of its commands into a class hierarchy, and by customizing them to operate in a more 
succinct and intuitive way. """,
      author='Chad Dombrova',
      author_email='chadrik@gmail.com',
      url='http://code.google.com/p/pymel/',
      packages=['pymel','pymel.api', 'pymel.core', 'pymel.mayahook', 'pymel.tools', 'pymel.tools.mel2py', 'pymel.util' ],
      #package_dir={'':'pymel'},
      #packages=find_packages('pymel'),
      #scripts=['scripts/ipymel'],
      entry_points = entry_points,
      package_data={'pymel': ['*.bin', '*.conf' ] },
      install_requires=requires,
      extras_require= { 'ipymel' : 'ipython' },
      tests_require=['nose'],
      test_suite = 'nose.collector',
     )
