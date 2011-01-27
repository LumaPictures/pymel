from pydoc import *         #@UnusedWildImport
import pydoc, sys, pprint   #@Reimport
import __builtin__
import os                   #@Reimport
import pkgutil              #@Reimport

# for the sake of stubtest, don't importy anything pymel/maya at module level 
#import pymel.util as util

class StubDoc(Doc):
    """Formatter class for text documentation."""

    # ------------------------------------------- text formatting utilities
    module_map = {}
    _repr_instance = TextRepr()
    # We don't care if it's compact, we just want it to parse right...
    _repr_instance.maxlist = _repr_instance.maxtuple = _repr_instance.maxdict\
        = _repr_instance.maxstring = _repr_instance.maxother = 100000
    repr = _repr_instance.repr
    missing_modules = set([])
    def bold(self, text):
        """Format a string in bold by overstriking."""
        return join(map(lambda ch: ch + '\b' + ch, text), '')

    def indent(self, text, prefix='    '):
        """Indent text by prepending a given prefix to each line."""
        if not text: return ''
        lines = split(text, '\n')
        lines = map(lambda line, prefix=prefix: prefix + line, lines)
        if lines: lines[-1] = rstrip(lines[-1])
        return join(lines, '\n')

    def section(self, title, contents):
        """Format a section with a given heading."""
        quotes = "'''" if '"""' in contents else '"""'
        return rstrip(self.indent( quotes +'\n' + contents + '\n' + quotes)) + '\n\n'

    def docstring(self, contents):
        """Format a section with a given heading."""
        quotes = "'''" if '"""' in contents else '"""'
        return quotes + '\n' + contents + '\n' + quotes + '\n\n'
    
    # ---------------------------------------------- type-specific routines

    def formattree(self, tree, modname, parent=None, prefix=''):
        """Render in text a class tree as returned by inspect.getclasstree()."""
        result = ''
        for entry in tree:
            if type(entry) is type(()):
                c, bases = entry
                result = result + prefix + classname(c, modname)
                if bases and bases != (parent,):
                    parents = map(lambda c, m=modname: classname(c, m), bases)
                    result = result + '(%s)' % join(parents, ', ')
                result = result + '\n'
            elif type(entry) is type([]):
                result = result + self.formattree(
                    entry, modname, c, prefix + '    ')
        return result
    
    importSubstitutions = {'pymel.util.objectParser':'''
class ProxyUni(object): pass
class Parsed(ProxyUni): pass
''',
                           'precompmodule':''}

    def docmodule(self, object, name=None, mod=None):
        """Produce text documentation for a given module object."""
        debugmodule = 'pymel.api'
        
        name = object.__name__ # ignore the passed-in name
        desc = splitdoc(getdoc(object))[1]
        result = ''
        self.module_map = {}
        self.missing_modules = set([])
        try:
            all = object.__all__
        except AttributeError:
            all = None
        
        ispkg = hasattr(object, '__path__')
#        try:
#            file = inspect.getabsfile(object)
#        except TypeError:
#            file = '(built-in)'
#        result = result + self.section('FILE', file)
#
#        docloc = self.getdocloc(object)
#        if docloc is not None:
#            result = result + self.section('MODULE DOCS', docloc)

        if desc:
            result += result + self.docstring(desc)

        untraversedClasses = []
        for key, value in inspect.getmembers(object, inspect.isclass):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None
                or (inspect.getmodule(value) or object) is object):
                if visiblename(key, all):
                    untraversedClasses.append((key, value))
        # A visible class may have a non-visible baseClass from this module,
        # which will still need to be included if the module is to import
        # correctly - ie,
        # class _AbstractClass(object): pass
        # class InheritedClass(_AbstractClass): pass
        classes = []
        while untraversedClasses:
            key, childClass = untraversedClasses.pop()
            classes.append( (key, childClass) )
            for parentClass in childClass.__bases__:
                if (inspect.getmodule(parentClass) or object) is object:
                    newTuple = (parentClass.__name__, parentClass)
                    if newTuple not in classes and newTuple not in untraversedClasses:
                        untraversedClasses.append( newTuple )
                    
        funcs = []
        for key, value in inspect.getmembers(object, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None or
                inspect.isbuiltin(value) or inspect.getmodule(value) is object):
                if visiblename(key, all):
                    funcs.append((key, value))
        data = []
        for key, value in inspect.getmembers(object, isdata):
            if visiblename(key, all):
                data.append((key, value))

        modules = []
        for key, value in inspect.getmembers(object, inspect.ismodule):
            modules.append((key, value))
        
        fromall_modules = set([])
        for key, value in inspect.getmembers(object, lambda x: not inspect.ismodule(x) ):
            if hasattr(value, '__module__') and value.__module__ not in [None, object.__name__] and not value.__module__.startswith('_'):
                if object.__name__ == debugmodule and value.__module__ == 'pymel.internal.apicache':
                    print "import* %r" % value
                fromall_modules.add( value.__module__ )

        if modules:
            contents = []
            #print "modules", object
            for key, value in modules:
                realname = value.__name__
                if realname == name:
                    continue
                realparts = realname.split('.')
                currparts = name.split('.')
                importname = realname
                if len(realparts) == len(currparts): #test for siblings
                    if realparts[:-1] == currparts[:-1] and not ispkg:
                        if object.__name__ == debugmodule: print "sibling"
                        importname = realparts[-1]
                elif len(realparts) > len(currparts): #test if current is parent
                    if realparts[:len(currparts)] == currparts:
                        if object.__name__ == debugmodule: print "parent"
                        importname = '.'.join(realparts[len(currparts):])
                self.module_map[realname] = key if importname != key else importname
                if object.__name__ == debugmodule:
                    print '\t %-30s %-30s %s' % ( realname, importname, key )
                if importname in self.importSubstitutions:
                    if importname != key:
                        importname = key
                    contents.append('%s = None' % importname)
                else:
                    contents.append( 'import ' + importname + ( ( ' as ' + key ) if importname != key else '') )
            result = result + join(contents, '\n') + '\n\n'
        if fromall_modules:
            # special-case handling for pymel.internal.pmcmds, which ends up
            # with a bunch of 'from pymel.core.X import *' commands
            if name == 'pymel.internal.pmcmds':
                fromall_modules = [x for x in fromall_modules if not x.startswith('pymel.core')]
                fromall_modules.append('maya.cmds')
            contents = []
            for modname in fromall_modules:
                if modname in self.importSubstitutions:
                    contents.append(self.importSubstitutions[modname])
                else:
                    contents.append( 'from ' + modname + ' import *' )
                self.module_map[modname] = ''
            result = result + join(contents, '\n') + '\n\n'
                
        if classes:
            # sort in order of resolution
            def nonconflicting(classlist):
                for cls in classlist:
                    mro = set(inspect.getmro(cls)[1:])
                    if not mro.intersection(classlist):
                        yield cls
            
            inspect.getmro(str)
            sorted = []
            unsorted = set([x[1] for x in classes])
            
            while unsorted:
                for cls in nonconflicting(unsorted):
                    sorted.append(cls)
                unsorted.difference_update(sorted)
                        
#            classlist = map(lambda key_value: key_value[1], classes)
#            contents = [self.formattree(
#                inspect.getclasstree(classlist, 1), name)]
            contents = []
            classes = dict([ (x[1], x[0]) for x in classes])
            for key in sorted:
                contents.append(self.document(key, classes[key], name))
            
            classres = join(contents, '\n').split('\n')
            
            for i, line in enumerate(classres):
                if u'\xa0' in line:
                    print "bad char"
                    for j in range( max(i-10,0), min(i+10,len(classres)) ):
                        if j == i:
                            print '-'*80
                        print classres[j]
                        if j == i:
                            print '-'*80
                    classres[i] = ''.join(line.split( u'\xa0'))
                        
            result = result + join(classres, '\n')

        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name))
            result = result + join(contents, '\n')

        if data:
            contents = []
            for key, value in data:
                contents.append(self.docother(value, key, name, maxlen=70))
            result = result + join(contents, '\n')

#        if hasattr(object, '__version__'):
#            version = str(object.__version__)
#            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
#                version = strip(version[11:-1])
#            result = result + self.section('VERSION', version)
#        if hasattr(object, '__date__'):
#            result = result + self.section('DATE', str(object.__date__))
#        if hasattr(object, '__author__'):
#            result = result + self.section('AUTHOR', str(object.__author__))
#        if hasattr(object, '__credits__'):
#            result = result + self.section('CREDITS', str(object.__credits__))
        if self.missing_modules:
            contents = []
            for mod in self.missing_modules:
                contents.append( 'import ' + mod)
            result = join(contents, '\n') + '\n\n'  + result
        return result

    def classname(self, object, modname):
        """Get a class name and qualify it with a module name if necessary."""
        name = object.__name__
        if object.__module__ not in [ modname,'__builtin__']:
            #print object
            try:
                newmodname = self.module_map[object.__module__]
                #print "from map", object.__module__, repr(modname)
            except KeyError:
                newmodname = None
                for m in self.module_map.keys():
                    mod = sys.modules[m]
                    #print '\t', m, mod
                    if object in mod.__dict__.values():
                        #print '\tfound'
                        newmodname = self.module_map[m]
                        break
                if not newmodname:
                    #print "missing"
                    self.missing_modules.add(object.__module__)
            if newmodname:
                name = newmodname + '.' + name
        return name

    def docclass(self, object, name=None, mod=None):
        """Produce text documentation for a given class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        def makename(c, m=object.__module__):
            return self.classname(c, m)

        title = 'class ' + name

        if bases:
            parents = map(makename, bases)
            title = title + '(%s)' % join(parents, ', ')
        title += ':\n'
        
        doc = getdoc(object)
        contents = doc and [self.docstring(doc) + '\n'] or []
        push = contents.append

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:       #@UnusedVariable
                    push(self.document(getattr(object, name),
                                       name, mod, object))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:       #@UnusedVariable
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:       #@UnusedVariable
                    if (hasattr(value, '__call__') or
                            inspect.isdatadescriptor(value)):
                        doc = getdoc(value)
                    else:
                        doc = None
                    push(self.docother(getattr(object, name),
                                       name, mod, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = filter(lambda data: visiblename(data[0]),
                       classify_class_attrs(object))

        thisclass = object
        attrs, inherited = pydoc._split_list(attrs, lambda t: t[2] is thisclass)

        if thisclass is __builtin__.object:
            attrs = inherited
        else:
            if attrs:
                tag = None
        
                # Sort attrs by name.
                attrs.sort()
        
                # Pump out the attrs, segregated by kind.
                attrs = spill("Methods %s:\n" % tag, attrs,
                              lambda t: t[1] == 'method')
                attrs = spill("Class methods %s:\n" % tag, attrs,
                              lambda t: t[1] == 'class method')
                attrs = spill("Static methods %s:\n" % tag, attrs,
                              lambda t: t[1] == 'static method')
                attrs = spilldescriptors("Data descriptors %s:\n" % tag, attrs,
                                         lambda t: t[1] == 'data descriptor')
                attrs = spilldata("Data and other attributes %s:\n" % tag, attrs,
                                  lambda t: t[1] == 'data')
            else:
                contents.append('pass')

        contents = '\n'.join(contents)
        
        return title + self.indent(rstrip(contents), '    ') + '\n\n'

    def formatvalue(self, object):
        """Format an argument default value as text."""
        # check if the object is os.environ...
        isEnviron = False
        if object == os.environ:
            isEnviron = True
        elif isinstance(object, dict):
            # If over 90% of the keys are in os.environ, assume it's os.environ
            if len(set(object) & set(os.environ)) > (len(object) * 0.9):
                isEnviron = True
        if isEnviron:
            objRepr = repr({'PROXY_FOR':'os.environ'})
        else:
            objRepr = self.repr(object)
            if objRepr[0] == '<' and objRepr[-1] == '>':
                objRepr = repr(objRepr)
        return '=' + objRepr

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        skipdocs = 0
        if inspect.ismethod(object):
            object = object.im_func
        
        title = name
        if inspect.isfunction(object):
            args, varargs, varkw, defaults = inspect.getargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)
        else:
            argspec = '(*args, **kwargs)'
        decl = 'def ' + title + argspec + ':'
        
        if isinstance(object, staticmethod):
            decl = '@staticmethod\n' + decl
        elif isinstance(object, classmethod):
            decl = '@classmethod\n' + decl

        if skipdocs:
            return decl + 'pass\n'
        else:
            doc = getdoc(object) or ''
            return decl + '\n' + (doc and rstrip(self.indent(self.docstring(doc))) + '\n\n') + self.indent('pass') + '\n\n'

    def _docdescriptor(self, name, value, mod):
        results = []
        push = results.append

        if name:
            push(name + ' = None')
            push('\n')
        return ''.join(results)

    def docproperty(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a property."""
        return self._docdescriptor(name, object, mod)

    def docdata(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a data descriptor."""
        return self._docdescriptor(name, object, mod)

    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        if name in ['__metaclass__']:
            return ''
        if name == '__all__':
            value = pprint.pformat(object)
        else:
            value = 'None' 
        line = (name and name + ' = ' or '') + value + '\n'
        return line

stubs = StubDoc()

def packagestubs(packagename, outputdir='', extensions=('py', 'pypredef', 'pi'), exclude=None):
    import pymel.util as util
    
    packagemod = __import__(packagename, globals(), locals(), [], -1)
    for modname, mod, ispkg in util.subpackages(packagemod):
        contents = stubs.docmodule(mod)
        for extension in extensions:
            basedir = os.path.join(outputdir, extension)
            if extension == 'pypredef':
                curfile = os.path.join(basedir, modname)
            else:
                curfile = os.path.join(basedir, *modname.split('.') )
                if ispkg:
                    curfile = os.path.join(curfile, '__init__' )

            curfile = curfile + os.extsep + extension
            
            curdir = os.path.dirname(curfile)
            if not os.path.isdir(curdir):
                os.makedirs(curdir)
            print modname, curfile
            f = open( curfile, 'w' )
            if not exclude or not re.match( exclude, modname ):
                f.write( contents )
            f.close()
    

def pymelstubs(extensions=('py', 'pypredef', 'pi')):
    """ Builds pymel stub files for autocompletion.
    
    Can build Python Interface files (pi) with extension='pi' for IDEs like wing."""
    
    pymeldir = os.path.dirname( os.path.dirname( sys.modules[__name__].__file__) )
    outputdir = os.path.join(pymeldir, 'extras', 'completion')
    print outputdir
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    
    packagestubs( 'pymel', 
                  outputdir=outputdir, 
                  extensions=extensions,
                  exclude='pymel\.util\.scanf|pymel\.util\.objectParser|pymel\.tools\.ipymel')

    packagestubs( 'maya', outputdir=outputdir,extensions=extensions )
    
    return outputdir

# don't start name with test - don't want it automatically run by nose
def stubstest(pystubdir, doprint=True):
    '''Test the stubs modules.
    
    Don't call this from 'inside maya', as we've probably already loaded all
    the various 'real' modules, which can give problems.
    '''
    def importError(modname):
        print 'error importing %s:' % modname
        import traceback
        bad.append( (modname, traceback.format_exc()) )
        
    bad = []
    print "Testing all modules in: %s" % pystubdir
    sys.path.insert(0, pystubdir)
    try:
        for importer, modname, ispkg in \
                pkgutil.walk_packages(path=[pystubdir],onerror=importError):
            print 'testing %s' % modname
            try:
                # Don't use the importer returned by walk_packages, as it
                # doesn't always properly update parent packages's dictionary
                # with submodule name - ie, you would do:
                # import pymel.all
                # print pymel.all
                # ...and find that pymel had no attribute 'all'
                #importer.find_module(modname).load_module(modname)
                __import__(modname, globals(), locals(), [])
            except Exception, error:
                print 'found bad module: %s - %s' % (modname, error)
                importError(modname)
    finally:
        sys.path.pop(0)
    print 'done walking modules'
    if doprint:
        for modname, error in bad:
            print '*' * 60
            print 'could not import %s:\n%s' % (modname, error)
    return bad