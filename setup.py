#!/usr/bin/env mayapy
import sys
import re
import os
import platform
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
import setuptools.command.easy_install

try:
    system = platform.system()
except:
    system = None

def get_maya_version():

    # problem with service packs addition, must be able to match things such as :
    # '2008 Service Pack 1 x64', '2008x64', '2008', '8.5'

    try:
        versionStr = os.path.dirname( os.path.dirname( sys.executable ) )
        m = re.search( "((?:maya)?(?P<base>[\d.]{3,})(?:(?:[ ].*[ ])|(?:-))?(?P<ext>x[\d.]+)?)", versionStr)
        version = m.group('base')
        return version
    except:
        pass

def get_ply_version():
    if sys.version_info >= (2,6):
        return 'ply >2.0'
    return 'ply >2.0, <3.0'

def get_data_files():
    if get_maya_version() in ['2010'] and system == 'Darwin':
        return [('', ['extras/2010/osx/readline.so'])]
    return []

def get_mayapy_executable():   
    if os.name == 'posix':
        try:
            mayapy_bin = re.match('.*/bin/', sys.executable ).group(0) + 'mayapy'
            return mayapy_bin
        except:
            pass    
    return os.path.normpath( sys.executable )

def get_maya_bin_dir():
    return os.path.split( get_mayapy_executable() )[0]

# overwrite setuptools.command.easy_install.get_script_args
# it's the only way to change the executable for ipymel
orig_script_args = setuptools.command.easy_install.get_script_args
orig_nt_quote_arg = setuptools.command.easy_install.nt_quote_arg

if system == 'Darwin':
    # on osx we need to use '/usr/bin/env /Applications....mayapy', but setuptools tries to wrap this in quotes
    # because it has a space in it. disable this behavior
    def nt_quote_arg(arg):
        return arg
    setuptools.command.easy_install.nt_quote_arg = nt_quote_arg
    
    # set default script installation directory
    # on osx the python binary is deep within the frameworks directory,
    # so the binaries get installed there.  would be better to have them in the maya bin directory
    args = list(sys.argv)
    is_set = False
    # looking for a line like:  '--install-scripts=/Applications/Autodesk/maya2010/Maya.app/Contents/bin'
    for arg in args[1:]:
        if arg.split('=')[0] in [ '--install-scripts', '--install-dir' ]:
            is_set = True
            break
    if not is_set:
        args.append( '--install-scripts=' + get_maya_bin_dir() )
        sys.argv = args
        
    
    
def get_script_args(dist, executable=None, wininst=False):
    executable = get_mayapy_executable()  
    if system == 'Darwin':
        executable = '/usr/bin/env ' + executable
    return orig_script_args(dist, executable, wininst)

setuptools.command.easy_install.get_script_args = get_script_args

try:
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
          entry_points = {'console_scripts' : 'ipymel = pymel.tools.ipymel:main' },
          package_data={'pymel': ['*.bin', '*.conf' ] },
          install_requires=['BeautifulSoup >3.0', get_ply_version(), 'ipython'],
          tests_require=['nose'],
          test_suite = 'nose.collector',
          data_files = get_data_files()
         )
finally:
    # restore
    setuptools.command.easy_install.get_script_args = orig_script_args
    setuptools.command.easy_install.nt_quote_arg = orig_nt_quote_arg

      
