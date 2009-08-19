#!/usr/bin/env mayapy
import sys
import re
import os
import platform
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup


if sys.version_info >= (2,6):
    ply_version = 'ply >2.0'
else:
    ply_version = 'ply >2.0, <3.0'


def getMayaVersion():

    # problem with service packs addition, must be able to match things such as :
    # '2008 Service Pack 1 x64', '2008x64', '2008', '8.5'

    # NOTE: we're using the same regular expression (parseVersionStr) to parse both the crazy human readable
    # maya versions as returned by about, and the maya location directory.  to handle both of these i'm afraid 
    # the regular expression might be getting unwieldy
    try:
        if platform.system() == 'Darwin':
            versionStr = os.path.dirname( os.path.dirname( sys.executable ) )
            m = re.search( "((?:maya)?(?P<base>[\d.]{3,})(?:(?:[ ].*[ ])|(?:-))?(?P<ext>x[\d.]+)?)", versionStr)
            version = m.group('base')
            return version

    except:
        pass

if getMayaVersion() == '2010':
    data_files=[('', ['extra/2010/osx/readline.so'])]
else:
    data_files = []
    
setup(name='pymel',
      version='0.9.2',
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
      entry_points = {'console_scripts' : 'ipymel = pymel.tools.ipymel:main [ipymel]' },
      package_data={'pymel': ['*.bin', '*.conf' ] },
      install_requires=['BeautifulSoup >3.0', ply_version],
      extras_require= { 'ipymel' : 'ipython' },
      tests_require=['nose'],
      test_suite = 'nose.collector',
      data_files = data_files
     )

      
