from pydoc import *
import pydoc, pkgutil, sys, pprint
import __builtin__

class StubDoc(Doc):
    """Formatter class for text documentation."""

    # ------------------------------------------- text formatting utilities
    module_map = {}
    _repr_instance = TextRepr()
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
        return rstrip(self.indent( '"""\n' + contents + '\n"""')) + '\n\n'

    def docstring(self, contents):
        """Format a section with a given heading."""
        return '"""\n' + contents + '\n"""' + '\n\n'
    
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

    def docmodule(self, object, name=None, mod=None):
        """Produce text documentation for a given module object."""
        name = object.__name__ # ignore the passed-in name
        synop, desc = splitdoc(getdoc(object))
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

        classes = []
        for key, value in inspect.getmembers(object, inspect.isclass):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None
                or (inspect.getmodule(value) or object) is object):
                if visiblename(key, all):
                    classes.append((key, value))
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
        
        allmodules = set([])
        for key, value in inspect.getmembers(object, lambda x: not inspect.ismodule(x) ):
            if hasattr(value, '__module__') and value.__module__ not in [None, object.__name__] and not value.__module__.startswith('_'):
                allmodules.add( value.__module__ )
            
#        modpkgs = []
#        modpkgs_names = set()
#        if hasattr(object, '__path__'):
#            for importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
#                modpkgs_names.add(modname)
#                if ispkg:
#                    modpkgs.append(modname + ' (package)')
#                else:
#                    modpkgs.append(modname)
#
#            modpkgs.sort()
#            result = result + self.section(
#                'PACKAGE CONTENTS', join(modpkgs, '\n'))
#
#        # Detect submodules as sometimes created by C extensions
#        submodules = []
#        for key, value in inspect.getmembers(object, inspect.ismodule):
#            if value.__name__.startswith(name + '.') and key not in modpkgs_names:
#                submodules.append(key)
#        if submodules:
#            submodules.sort()
#            result = result + self.section(
#                'SUBMODULES', join(submodules, '\n'))
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
                        if object.__name__ == 'pymel.internal': print "sibling"
                        importname = realparts[-1]
                elif len(realparts) > len(currparts): #test if current is parent
                    if realparts[:len(currparts)] == currparts:
                        if object.__name__ == 'pymel.internal': print "parent"
                        importname = '.'.join(realparts[len(currparts):])
                self.module_map[realname] = key if importname != key else importname
                if object.__name__ == 'pymel.internal':
                    print '\t %-30s %-30s %s' % ( realname, importname, key )
                contents.append( 'import ' + importname + ( ( ' as ' + key ) if importname != key else '') )
            result = result + join(contents, '\n') + '\n\n'
        if allmodules:
            contents = []
            for modname in allmodules:
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

#        # List the mro, if non-trivial.
        mro = deque(inspect.getmro(object))
#        if len(mro) > 2:
#            push("Method resolution order:")
#            for base in mro:
#                push('    ' + makename(base))
#            push('')

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:
                    push(self.document(getattr(object, name),
                                       name, mod, object))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:
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
        return '=' + self.repr(object)

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        if inspect.ismethod(object):
            imclass = object.im_class
#            if cl:
#                if imclass is not cl:
#                    note = ' from ' + classname(imclass, mod)
#            else:
#                if object.im_self is not None:
#                    note = ' method of %s instance' % classname(
#                        object.im_self.__class__, mod)
#                else:
#                    note = ' unbound %s method' % classname(imclass,mod)
            object = object.im_func
        
        title = name
#        if name == realname:
#            title = realname
#        else:
#            if (cl and realname in cl.__dict__ and
#                cl.__dict__[realname] is object):
#                skipdocs = 1
#            title = name + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults = inspect.getargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)
            argspec = argspec.replace('<', '"')
            argspec = argspec.replace('>', '"')
#            if realname == '<lambda>':
#                title = name
        else:
            argspec = '(*ags, **kwargs)'
        decl = 'def ' + title + argspec + ':'

        if skipdocs:
            return decl + 'pass\n'
        else:
            doc = getdoc(object) or ''
            return decl + '\n' + (doc and rstrip(self.indent(self.docstring(doc))) + '\n\n') + self.indent('pass') + '\n\n'

    def _docdescriptor(self, name, value, mod):
        results = []
        push = results.append

#        doc = getdoc(value) or ''
#        if doc:
#            push( '# ' + self.indent(doc))
#            push('\n')
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
#        if doc is not None:
#            line += '\n' + self.indent(str(doc))
        return line

stubs = StubDoc()

def _subpackages(packagemod):
    modpkgs = []
    modpkgs_names = set()
    if hasattr(packagemod, '__path__'):
        yield packagemod.__name__, packagemod, True
        for importer, modname, ispkg in pkgutil.walk_packages(packagemod.__path__, packagemod.__name__+'.'):
            if modname not in sys.modules:  
                try:
                    mod = importer.find_module(modname).load_module(modname)
                    yield modname, mod, ispkg
                except Exception, e:
                    print "error importing %s: %s" %  ( modname, e)
            else:
                mod = sys.modules[modname]
                yield modname, mod, ispkg

def packagestubs(packagemod, outputdir='', exclude=None):
    for modname, mod, ispkg in _subpackages(packagemod):
        curpath = os.path.join(outputdir, *modname.split('.') )
        
        if ispkg:
            if not os.path.exists(curpath):
                os.mkdir(curpath)
            curfile = os.path.join(curpath, '__init__.py' )
        else:
            curfile = curpath + '.py'
        print modname, curfile
        f = open( curfile, 'w' )
        if not exclude or not re.match( exclude, modname ):
            f.write( stubs.docmodule(mod) )
        f.close()

def pymelstubs():
    pymeldir = os.path.dirname( os.path.dirname( sys.modules[__name__].__file__) )
    outputdir = os.path.join(pymeldir, 'extras', 'completion' )
    print outputdir
    import pymel.all
    packagestubs( pymel, outputdir=outputdir, exclude='(pymel\.util\.scanf)|(pymel\.util\.objectParser)')

    # fix pmcmds:
    f = open( os.path.join(outputdir,'pymel','internal','pmcmds.py'), 'w' )
    f.write( 'from maya.cmds import *\n' )
    f.close()
    