import os
import os.path
import sys
from maintenance.stubs import packagestubs


def pymelstubs(extensions=('py', 'pypredef', 'pi'),
               modules=('pymel', 'maya', 'PySide2', 'shiboken2'),
               skip_module_regex=None,
               pyRealUtil=False):
    """ Builds pymel stub files for autocompletion.

    Can build Python Interface files (pi) with extension='pi' for IDEs like 
    wing.
    """

    buildFailures = []
    pymeldir = os.path.dirname(os.path.dirname(sys.modules[__name__].__file__))
    outputdir = os.path.join(pymeldir, 'extras', 'completion')
    print "Stub output dir:", outputdir
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    importExclusions = {
        'pymel.api': set(['pymel.internal.apicache']),
        'pymel': set(['pymel.all']),
        'maya.precomp': set(['precompmodule']),
    }

    def filterImports(current, modules, imported, importall_modules):
        if importall_modules:  # from MODULE import *
            # special-case handling for pymel.internal.pmcmds, which ends up
            # with a bunch of 'from pymel.core.X import *' commands
            if current == 'pymel.internal.pmcmds':
                importall_modules = [
                    x for x in importall_modules
                    if not getattr(x, '__name__', 'pymel.core').startswith
                        ('pymel.core')]
                imported = [(obj, names, source_module)
                            for obj, names, source_module in imported
                            if not getattr(source_module, '__name__',
                                           'pymel.core').startswith
                        ('pymel.core')]
                if not any(x.__name__ == 'maya.cmds' for x in
                           importall_modules):
                    import maya.cmds
                    importall_modules.append(maya.cmds)

        return modules, imported, importall_modules

    for modulename in modules:
        try:
            print "making stubs for: %s" % modulename
            packagestubs(modulename, outputdir=outputdir, extensions=extensions,
                         skip_module_regex=skip_module_regex,
                         import_exclusions=importExclusions,
                         import_filter=filterImports,
                         debugmodules={'pymel.core'}, stubmodules=modules)

        except Exception as err:
            import traceback
            buildFailures.append((modulename, err, traceback.format_exc()))

    if pyRealUtil:
        # build a copy of 'py' stubs, that have a REAL copy of pymel.util...
        # useful to put on the path of non-maya python interpreters, in
        # situations where you want to be able to import the "dummy" maya/pymel
        # stubs, but still have acces to the handy non-maya-required pymel.util
        def copyDir(src, dest):
            # ignore if the source dir doesn't exist...
            if os.path.isdir(src):
                import shutil
                if os.path.isdir(dest):
                    shutil.rmtree(dest)
                elif os.path.isfile(dest):
                    raise RuntimeError(
                        "A file called %s existed (expected a dir "
                        "or nothing)" % dest)
                shutil.copytree(src, dest)
            elif os.path.isfile(src):
                raise RuntimeError(
                    "A file called %s existed (expected a dir "
                    "or nothing)" % src)

        pyDir = os.path.join(outputdir, 'py')
        pyRealUtilDir = os.path.join(outputdir, 'pyRealUtil')
        print "creating %s" % pyRealUtilDir
        copyDir(pyDir, pyRealUtilDir)

        srcUtilDir = os.path.join(pymeldir, 'pymel', 'util')
        destUtilDir = os.path.join(pyRealUtilDir, 'pymel', 'util')
        copyDir(srcUtilDir, destUtilDir)

    if buildFailures:
        indent = '   '
        print "WARNING! Module specified failed to build :"
        for failedModule, err, traceStr in buildFailures:
            print "{}{} - {}".format(indent, failedModule, err)
            print indent * 2 + traceStr.replace('\n', '\n' + indent * 2)
        print "(Try specify different list of modules for 'modules' keyword " \
              "argument)"

    return outputdir
