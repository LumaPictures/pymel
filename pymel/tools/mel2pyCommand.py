#!/usr/bin/env mayapy
"""
version of mel2py which is intended to be used as a command-line script.

Symbolic link it to an easier-to-type name (ie, 'mel2py') in a directory on your path
"""

# Can't be a submodule of mel2py, because we wish to avoid importing mel2py (which
# triggers the entire maya-initialization process) if we're just printing usage,
# or there's an error processing command-line arguments.


class Options(dict):
    """
    Wrap of a dictionary object to get options parsed from OptionParser into a dict.
    """
    def __setattr__(self, name, value):
        if hasattr(self, name):
            super(self, Options).__setattr__(name, value)
        else:
            self[name] = value

def main():
    from optparse import OptionParser
    import sys
    
    usage = """%prog [options] input (outputDir)
Arguments:
  input
    May be a directory, a list of directories,
    the name of a mel file, a comma-separated list
    of mel files, or the name of a sourced procedure.
    If only the name of the mel file is passed,
    mel2py will attempt to determine the location 
    of the file using the 'whatIs' mel command, which relies
    on the script already being sourced by maya."""
    parser = OptionParser(usage=usage)
    opts = Options()


    parser.add_option("-o", "--outputDir",
                      help="""Directory where resulting python files will be written to""")
    parser.add_option("-n", "--pymelNamespace",
                      help="the namespace into which pymel will be imported.  the default is '', which means ``from pymel.all import *``")
    parser.add_option("-c", "--forceCompatibility", action="store_true",
                      help="""If True, the translator will attempt to use non-standard python types in order to produce
python code which more exactly reproduces the behavior of the original mel file, but which
will produce "uglier" code.  Use this option if you wish to produce the most reliable code
without any manual cleanup.""")
    parser.add_option("-v", "--verbosity", type="int",
                      help="""Set to non-zero for a *lot* of feedback""")
    parser.add_option("-t", "--test", action="store_true",
                      help="""After translation, attempt to import the modules to test for errors""")
    parser.add_option("-r", "--recurse", action="store_true",
                      help="""If the input is a directory, whether or not to recursively search subdirectories as well""")
    parser.add_option("-e", "--exclude",
                      help="""A comma-separated list of files/directories to exclude from processing, if input is a directory.""")
    parser.add_option("-p", "--melPathOnly", action="store_true",
                      help="""If true, will only translate mel files found on the mel script path.""")
    parser.add_option("-b", "--basePackage",
                      help="""Gives the package that all translated modules will be a part of; if None or an empty string, all translated modules are assumed to have no base package.""")
                
    parser.set_defaults(outputDir=None,
            pymelNamespace='', forceCompatibility=False,
            verbosity=0 , test=False,
            recurse=False, exclude=(), melPathOnly=False)
    options, args = parser.parse_args(values=opts)
    if len(args) < 1:
        print "input argument is required!"
        parser.print_help()
        return
    elif len(args) > 2:
        print "mel2py supports at most 2 args - input, outputDir"
        parser.print_help()
        return
    exclude = options.get('exclude', False)
    if exclude:
        options['exclude'] = exclude.split(',')
    from pymel.tools.mel2py import mel2py
    if args and ',' in args[0]:
        args[0] = args[0].split(',')
    mel2py(*args, **options)
    
if __name__ == '__main__':
    main()