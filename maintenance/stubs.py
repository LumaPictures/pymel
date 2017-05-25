#!/usr/bin/env python

from pydoc import *         #@UnusedWildImport
import pydoc, sys, pprint   #@Reimport
import __builtin__
import os                   #@Reimport
import pkgutil              #@Reimport
import collections
import inspect
import ast
import keyword
import re
import types
import json

OBJ = 0
OBJTYPE = 1
SOURCEMOD = 2
NAMES = 3

PYTHON_OBJECT_RE = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*(?:\.[a-zA-Z_][a-zA-Z_0-9]*)*(?:\(.*\))?$')

builtins = set(__builtin__.__dict__.values())

# some basic data types which may not exist...
if 'bytes' not in globals():
    bytes = str
if 'basestring' not in globals():
    basestring = str

verbose = False


# def classify_class_attrs(object):
#     """Wrap inspect.classify_class_attrs, with fixup for data descriptors."""
#     def fixup(data):
#         name, kind, cls, value = data
#         if inspect.isdatadescriptor(value):
#             if kind == 'property':
#                 print name, value, cls
#             kind = 'data descriptor'
#         return name, kind, cls, value
#     return map(fixup, inspect.classify_class_attrs(object))


def walk_packages(path=None, prefix='', onerror=None, skip_regex=None):
    """Yields (module_loader, name, ispkg) for all modules recursively
    on path, or, if path is None, all accessible modules.

    'path' should be either None or a list of paths to look for
    modules in.

    'prefix' is a string to output on the front of every module name
    on output.

    Note that this function must import all *packages* (NOT all
    modules!) on the given path, in order to access the __path__
    attribute to find submodules.

    'onerror' is a function which gets called with one argument (the
    name of the package which was being imported) if any exception
    occurs while trying to import a package.  If no onerror function is
    supplied, ImportErrors are caught and ignored, while all other
    exceptions are propagated, terminating the search.

    Examples:

    # list all modules python can access
    walk_packages()

    # list all submodules of ctypes
    walk_packages(ctypes.__path__, ctypes.__name__+'.')
    """

    def seen(p, m={}):
        if p in m:
            return True
        m[p] = True

    for importer, name, ispkg in pkgutil.iter_modules(path, prefix):

        if skip_regex and re.match(skip_regex, name):
            if verbose:
                print("skipping %s %s" % (name, skip_regex))
            continue

        yield importer, name, ispkg

        if ispkg:
            try:
                mod = __import__(name)
            except ImportError:
                if onerror is not None:
                    onerror(name)
            except Exception:
                if onerror is not None:
                    onerror(name)
                else:
                    raise
            else:
                path = getattr(sys.modules[name], '__path__', None) or []

                # don't traverse path items we've seen before
                path = [p for p in path if not seen(p)]

                for item in walk_packages(path, name+'.', onerror, skip_regex):
                    yield item


def subpackages(packagemod, skip_regex=None):
    """
    Given a module object, returns an iterator which yields a tuple
    (modulename, moduleobject, ispkg)
    for the given module and all it's submodules/subpackages.
    """
    if hasattr(packagemod, '__path__'):
        yield packagemod.__name__, packagemod, True
        for importer, modname, ispkg in walk_packages(
                packagemod.__path__, packagemod.__name__ + '.',
                skip_regex=skip_regex):
            # if skip_regex and re.match(skip_regex, modname):
            #     print("skipping %s %s" % (modname, skip_regex))
            #     mod = None
            # else:
            if modname not in sys.modules:
                if verbose:
                    print("importing %s" % (modname,))
                try:
                    mod = importer.find_module(modname).load_module(modname)
                except Exception, e:
                    print "error importing %s: %s" % (modname, e)
                    mod = None
            else:
                mod = sys.modules[modname]
            yield modname, mod, ispkg
    else:
        yield packagemod.__name__, packagemod, False


def get_source_module(obj, default):
    mod = inspect.getmodule(obj)
    if mod == __builtin__ and obj in builtins:
        return mod
    if (not mod or inspect.isbuiltin(obj) or isdata(obj)
        or not mod.__name__ or mod.__name__.startswith('_')):
        mod = default
    return mod


def get_unique_name(basename=None, all_names=()):
    if basename is None:
        basename = '_unknown'
    elif not basename.startswith('_'):
        # we only use this in cases where the name wasn't orignally
        # found in the module - ie, we're just trying to add in
        # something that isn't really supposed to be in the module, but
        # we need it there to refer to it...
        # ...therefore, we want to make sure the name is at least
        # hidden...
        basename = '_' + basename
    name = basename
    num = 2
    while name in all_names:
        name = '%s%s' % (basename, num)
        num += 1
    return name


def get_class(obj):
    '''Retrieves the class of the given object.

    unfortunately, it seems there's no single way to query class that works in
    all cases - `.__class__` doesn't work on some builtin-types, like
    `re._pattern_type` instances, and type() doesn't work on old-style
    classes...
    '''
    cls = type(obj)
    if cls == types.InstanceType:
        cls = obj.__class__
    return cls


def has_default_constructor(cls):
    '''Returns true if it's possible to make an instance of the class with no args.
    '''
    # these classes's __init__/__new__ are slot_wrapper objects, which we can't
    # query... but we know that they are ok...
    if is_named_tuple(cls):
        return False

    safe_methods = set()
    for safe_cls in (object, list, dict, tuple, set, frozenset, str, unicode):
        safe_methods.add(safe_cls.__init__)
        safe_methods.add(safe_cls.__new__)

    for method in (getattr(cls, '__init__', None),
                   getattr(cls, '__new__', None)):
        if method in safe_methods:
            continue
        if method is None:
            # we got an old-style class that didn't define an __init__ or __new__...
            # it's ok..
            continue

        try:
            args, _, _, defaults = inspect.getargspec(method)
        except TypeError:
            # sometimes we get 'slot_wrapper' objects, which we can't query...
            # assume these are bad...
            return False
        if defaults is None:
            numDefaults = 0
        else:
            numDefaults = len(defaults)
        # there can be one 'mandatory' arg - which will be cls or self
        if len(args) > numDefaults + 1:
            return False
    return True


def is_dict_like(obj):
    '''Test whether the object is "similar" to a dict
    '''
    if isinstance(obj, collections.Mapping):
        return True
    for method in ('__getitem__', '__setitem__', 'keys'):
        if not inspect.ismethod(getattr(obj, method, None)):
            return False
    return True

def is_named_tuple(cls):
    '''Detect whether we think a class is the result of a namedtuple call'''
    if not inspect.isclass(cls):
        raise ValueError('is_named_tuple must be passed class objects - got '
                         '{!r}'.format(cls))

    if not isinstance(cls, type):
        # print "old-style class"
        return False

    if cls.__bases__ != (tuple,):
        # print "wrong bases"
        return False

    if cls.__dict__.get('__slots__') != ():
        # print "no slots"
        return False

    fields = cls.__dict__.get('_fields')
    if not isinstance(fields, tuple):
        # print "no fields"
        return False
    if not all(isinstance(f, basestring) for f in fields):
        # print "non-string fields"
        return False

    if not isinstance(cls.__dict__.get('_make'), classmethod):
        # print "no _make"
        return False
    if not isinstance(cls.__dict__.get('_asdict'), types.FunctionType):
        # print "no _asdict"
        return False
    if not isinstance(cls.__dict__.get('_replace'), types.FunctionType):
        # print "no _replace"
        return False

    return True


class ModuleNamesVisitor(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit(self, node):
        # if we have the module, recurse
        if isinstance(node, ast.Module):
            self.generic_visit(node)

        # we are looking for statements which could define a new name...
        elif isinstance(node,
                        (ast.Assign,
                         ast.ClassDef,
                         ast.FunctionDef,
                         ast.Import,
                         ast.ImportFrom,
                         ast.For,
                         ast.With,
                         ast.TryExcept,
                        )):
            self.add_names(node)

    def add_names(self, obj):
        # print "add_names: %r" % obj
        # string... add it!
        if isinstance(obj, basestring):
            self.names.add(obj)

        # A name node... add if the context is right
        elif isinstance(obj, ast.Name):
            if isinstance(obj.ctx, (ast.Store, ast.AugStore, ast.Param)):
                self.add_names(obj.id)

        # An alias... check for 'foo as bar'
        elif isinstance(obj, ast.alias):
            if obj.asname:
                name = obj.asname
            else:
                name = obj.name
            if name != '*':
                self.add_names(name)

        # list/tuple.. iterate...
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self.add_names(item)
        elif isinstance(obj, (ast.Tuple, ast.List)):
            self.add_names(obj.elts)

        # Statements (or subparts)...
        elif isinstance(obj, ast.Assign):
            self.add_names(obj.targets)
        elif isinstance(obj, ast.ClassDef):
            self.add_names(obj.name)
        elif isinstance(obj, ast.FunctionDef):
            self.add_names(obj.name)
        elif isinstance(obj, ast.Import):
            self.add_names(obj.names)
        elif isinstance(obj, ast.ImportFrom):
            self.add_names(obj.names)
        elif isinstance(obj, ast.For):
            self.add_names(obj.target)
        elif isinstance(obj, ast.With):
            self.add_names(obj.optional_vars)
        elif isinstance(obj, ast.TryExcept):
            self.add_names(obj.handlers)
        elif isinstance(obj, ast.ExceptHandler):
            self.add_names(obj.name)


def get_static_module_names(module):
    '''Given a module object, tries to do static code analysis to find the names
    that will be defined at module level.
    '''
    path = module.__file__
    if path.endswith(('.pyc', '.pyo')):
        path = path[:-1]
    with open(path, 'r') as f:
        text = f.read()
    if not text.endswith('\n'):
        # for some reason, the parser requires the text end with a newline...
        text += '\n'
    moduleAst = ast.parse(text, path)
    visitor = ModuleNamesVisitor()
    visitor.visit(moduleAst)
    return visitor.names


def have_id_name(id_to_data, id_obj, name):
    "return if the id_object has the passed name"
    data = id_to_data.get(id_obj, None)
    if data is None:
        return False
    return name in data[NAMES]


def get_importall_modules(id_to_data, other_module_names):
    importall_modules = []
    for other_mod, other_id_names in other_module_names.iteritems():
        other_all = getattr(other_mod, '__all__', None)
        visible_other = 0
        in_this = []
        for id_obj, other_names in other_id_names.iteritems():
            for other_name in other_names:
                if not visiblename(other_name, other_all):
                    continue
                visible_other += 1
                if have_id_name(id_to_data, id_obj, other_name):
                    in_this.append((id_obj, other_name))
        # rough heuristic - if 90% of the objects can be found in this
        # module, we assume an import all was done... note that we're not
        # even checking if they're present in this module with the same
        # name... it's a rough heuristic anyway...

        # chose .85 just because core.language gets .87 in pymel.core
        if float(len(in_this)) / visible_other > .85:
            importall_modules.append(other_mod)
            # go through and REMOVE all the in_this entries from
            # id_to_data...
            for id_obj, other_name in in_this:
                data = id_to_data[id_obj]
                data[NAMES].remove(other_name)
                if not data[NAMES]:
                    del id_to_data[id_obj]
    return importall_modules


class NoUnicodeTextRepr(TextRepr):
    '''PyDev barfs when a unicode literal (ie, u'something') is in a pypredef
    file; use this repr to make sure they don't show up.
    '''
    def __init__(self):
        self.maxlevel = 6
        self.maxtuple = 100000
        self.maxlist = 100000
        self.maxarray = 100000
        self.maxdict = 100000
        self.maxset = 100000
        self.maxfrozenset = 100000
        self.maxdeque = 100000
        self.maxstring = 100000
        self.maxlong = 100000
        self.maxother = 100000

    def repr_unicode(self, uStr, level):
        return self.repr_string(str(uStr), level)

    def repr1(self, x, level):
        # believe it or not there are cases where split(s) fails and s.split()
        # succeeds.  specifically, I'm seeing this error with a PySide object:
        # SystemError: Objects/longobject.c:244: bad argument to internal
        # function so this is a slight edit of TextRepr.repr1
        if hasattr(type(x), '__name__'):
            methodname = 'repr_' + join(type(x).__name__.split(), '_')
            if hasattr(self, methodname):
                return getattr(self, methodname)(x, level)
        return cram(stripid(repr(x)), self.maxother)


class StubDoc(Doc):
    """Formatter class for text documentation."""

    # ------------------------------------------- text formatting utilities
    _repr_instance = NoUnicodeTextRepr()
    # We don't care if it's compact, we just want it to parse right...
    repr = _repr_instance.repr

    ALLOWABLE_DOUBLE_UNDER_ATTRS = (
        '__version__', '__author__', '__date__', '__credits__')

    SIMPLE_TYPES = (basestring, bytes, bool, int, long, float, complex)
    PASS = 'pass'
    UNKNOWN_SIGNATURE = '(*args, **kwargs)'

    def __init__(self, import_exclusions=None, import_substitutions=None,
                 import_filter=None, debugmodules=None, skipdocs=False,
                 type_data=None, imports_precede_classes=True):
        self.missing_modules = set([])
        self.module_map = {}
        # Mapping of (module, dontImportThese)
        self.module_excludes = import_exclusions or {}
        self.import_substitutions = import_substitutions or {}
        self.import_filter = import_filter
        self.debugmodules = debugmodules or ()
        self.skipdocs = skipdocs

        self.id_map = {}
        self.static_module_names = {}
        self.safe_constructor_classes = set()

        self.type_data = type_data
        # a hack to avoid cyclical imports that doesn't always work
        self.imports_precede_classes = imports_precede_classes

        if hasattr(Doc, '__init__'):
            Doc.__init__(self)

    # def bold(self, text):
    #     """Format a string in bold by overstriking."""
    #     return join(map(lambda ch: ch + '\b' + ch, text), '')

    def indent(self, text, prefix='    '):
        """Indent text by prepending a given prefix to each line."""
        if not text:
            return ''
        lines = split(text, '\n')
        lines = map(lambda line, prefix=prefix: prefix + line, lines)
        if lines:
            lines[-1] = rstrip(lines[-1])
        return join(lines, '\n')

    # def section(self, title, contents):
    #     """Format a section with a given heading."""
    #     quotes = "'''" if '"""' in contents else '"""'
    #     return rstrip(self.indent( quotes +'\n' + contents + '\n' + quotes)) + '\n\n'

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
                result = result + prefix + self.classname(c, modname)
                if bases and bases != (parent,):
                    parents = map(lambda c, m=modname: self.classname(c, m), bases)
                    result = result + '(%s)' % join(parents, ', ')
                result = result + '\n'
            elif type(entry) is type([]):
                result = result + self.formattree(
                    entry, modname, c, prefix + '    ')
        return result

    def docmodule_add_parent_classes(self, this_module, id_to_data, class_parents, all_names):
        def is_module_added(parent_mod):
            found_parent_mod = False
            if parent_mod:
                if id(parent_mod) in id_to_data:
                    return True
                else:
                    mod_name = parent_mod.__name__
                    mod_name_split = mod_name.split('.')
                    while mod_name_split:
                        mod_name_split.pop()
                        mod_name = '.'.join(mod_name_split)
                        parent_mod = sys.modules.get(mod_name, None)
                        if parent_mod is not None and id(
                                parent_mod) in id_to_data:
                            return True
            return False

            def handle_named_tuple(cls):
                if is_named_tuple(cls):
                    add_obj(collections.namedtuple, source_module=collections)
                    # note that even though we may be adding a new object to the
                    # module namespace, we don't have to worry about incrementing
                    # new_to_this_module, as that's only used to signal whether
                    # we need to continue looking for new parent classes, etc -
                    # namedtuple is essentially a builtin that we don't need
                    # to inspect further
                    return True
                return False

        # deal with the classes - for classes in this module, we need to
        # find their base classes, and make sure they are also defined, or
        # imported
        untraversed_classes = list(obj for (obj, objtype, source_module, names)
                                   in id_to_data.itervalues()
                                   if objtype == 'class'
                                   and source_module == this_module
                                   and id(obj) not in class_parents)
        new_to_this_module = 0
        while untraversed_classes:
            child_class = untraversed_classes.pop()
            if handle_named_tuple(child_class):
                continue
            try:
                parents = [x for x in child_class.__bases__]
            except Exception:
                print "problem iterating %s.__bases__" % child_class
                parents = (object,)
            class_parents[id(child_class)] = parents

            for parent_class in parents:
                # note that even if the parent class is a named tuple,
                # we will still need to process it to add it to the module
                handle_named_tuple(parent_class)
                id_parent = id(parent_class)
                parent_mod = inspect.getmodule(parent_class)
                if id_parent not in id_to_data:
                    if parent_class in builtins:
                        continue

                    # We've found a class that's not in this namespace...
                    # ...but perhaps it's parent module is?
                    if parent_mod and parent_mod is not this_module \
                            and is_module_added(parent_mod):
                        # the parent module was there... skip this parent
                        # class..
                        continue

                    # we've found a new class... add it...
                    new_to_this_module += 1
                    self.docmodule_add_obj(parent_class, this_module,
                                           id_to_data, all_names)
                    source_module = id_to_data[id_parent][SOURCEMOD]
                    if source_module == this_module:
                        untraversed_classes.append(parent_class)
                else:
                    # make sure that the class's module exists in the
                    # current namespace
                    if parent_mod is not None and not \
                            is_module_added(parent_class):
                        # perhaps this logic should be handled in docmodule_add_obj.
                        # we privatize this because we're adding an object which
                        # did not exist in the original namespace (not in id_to_data)
                        # so we don't want to cause any conflicts
                        self.docmodule_add_obj(
                            parent_mod, this_module, id_to_data, all_names,
                            name='_' + parent_mod.__name__.split('.')[-1])

        return new_to_this_module

    def docmodule_add_obj(self, obj, this_module, id_to_data, all_names,
                          name=None, source_module=None):
        id_obj = id(obj)
        if id_obj in id_to_data:
            # the object was already known - check that the source_module
            # is consistent, and add the name if needed
            objtype, old_source_module, names = id_to_data[id_obj][OBJTYPE:]

            if source_module is None:
                # use the old source module..
                source_module = old_source_module
            # if the source modules are different, but the 'new' module
            # is this module, we're okay - we couldn't find the object
            # in the desired source_module, so we're just moving it
            # into this one...
            elif (source_module != old_source_module
                  and source_module != this_module):
                # ...otherwise, something weird is going on...
                raise RuntimeError(
                    "got conflicting source modules for %s" % obj)

            # If we don't know the name, and the object already exists in
            # the module, then we don't need to do anything... we can just
            # use one of the names already assigned to the object...
            if name is not None:
                # ...otherwise, we need to add the name to list of
                # aliases for the object in this module...
                if name not in names:
                    # if __name__ matches name, put the name at the
                    # front of the list of names, to make it the
                    # 'default' name...
                    if getattr(obj, '__name__', None) == name:
                        names.insert(0, name)
                    else:
                        names.append(name)
        else:
            # the object wasn't known... generate it's info...
            if name is None:
                # we didn't know the name - generate a unique one, hopefully
                # based off the object's name...
                name = get_unique_name(getattr(obj, '__name__', None),
                                       all_names=all_names)
            if source_module is None:
                source_module = get_source_module(obj, this_module)

            # now find the objtype...
            if inspect.ismodule(obj):
                objtype = 'module'
            elif inspect.isclass(obj):
                objtype = 'class'
            elif inspect.isroutine(obj):
                objtype = 'func'
            else:
                objtype = 'data'
            names = [name]
        id_to_data[id_obj] = (obj, objtype, source_module, names)

    def docmodule(self, this_module, name=None, mod=None, stubmodules=None):
        """Produce text documentation for a given module object."""

        this_name = this_module.__name__  # ignore the passed-in name
        desc = splitdoc(getdoc(this_module))[1]
        self.contents = []
        self.module_map = {}
        self.id_map = {}
        self.missing_modules = set([])
        self.safe_constructor_classes = set()
        all = getattr(this_module, '__all__', None)
        if stubmodules is None:
            self.stubmodules = set([this_name])
        else:
            self.stubmodules = set(stubmodules)

        if desc:
            self.contents.extend(self.docstring(desc).split('\n'))

        # set of all names in this module
        all_names = set()

        # these are all dicts that key off the object id...
        # we index by obj-id, instead of obj, because not all objects are
        # hashable, and we really only care about 'is' comparisons, not
        # equality comparisons...

        # this is a dict that maps from object id to a tuple
        #   (obj, objtype, source_module, names)
        # where obj is the object itself, objtype is one of the strings
        # module/class/func/data, and names is a list of the names/aliases under
        # which the object can be found in this module.
        id_to_data = {}

        # add all the objects that we have names for / should be in this
        # module
        for name, obj in inspect.getmembers(this_module):
            if (name.startswith('__') and name.endswith('__')
                    and name not in self.ALLOWABLE_DOUBLE_UNDER_ATTRS):
                continue
            self.docmodule_add_obj(obj, this_module, id_to_data, all_names,
                                   name=name)

        # We now need to do two things:
        #  1) find the parent classes for any classes we will define in this
        #     module, and make sure that they are accessible under some name
        #     from within this module
        #  2) for all objects we will be importing from other modules, make
        #     sure we can actually find them under some name in that module;
        #     if not, change their source_module to THIS module (ie, so we
        #     define a dummy placeholder for it in this module)

        # Since both of these can end up adding new objects to the list of
        # objects defined in this module (ie, whose
        # source_module == this_module), which can then cause the need to check
        # for updates on the other, we run both in a loop until neither task
        # finds any new things added to this module's namespace

        # maps from the id of a class to it's parent classes, for classes
        # which we will define in this module...
        class_parents = {}

        # maps from an id_obj to its ('default') name in the source module
        import_other_name = {}
        # maps from module to a dict, mapping from id to names within that
        # module
        other_module_names = {}

        def find_import_data():
            unknown_import_objs = list(
                (obj, source_module) for (obj, objtype, source_module, names)
                in id_to_data.itervalues() if
                objtype != 'module' and source_module != this_module
                and id(obj) not in import_other_name)
            new_to_this_module = 0
            for obj, source_module in unknown_import_objs:
                id_obj = id(obj)
                other_id_names = other_module_names.get(source_module, None)
                if other_id_names is None:
                    other_id_names = {}
                    for other_name, other_obj in inspect.getmembers(source_module):
                        id_other = id(other_obj)
                        other_id_names.setdefault(id_other, []).append(other_name)
                    other_module_names[source_module] = other_id_names
                other_names = other_id_names.get(id_obj, None)
                if not other_names:
                    # we couldn't find obj in the desired module - we'll
                    # have to move it to this_module...
                    new_to_this_module += 1
                    # calling docmodule_add_obj with the same obj but module as
                    # this_module will update it...
                    self.docmodule_add_obj(obj, this_module, id_to_data,
                                           all_names, source_module=this_module)
                else:
                    # check to see if we've already found the object
                    # in the module - if so, only update the name if it's the
                    # __name__ of the object
                    name = getattr(obj, '__name__', None)
                    if name is None or name not in other_names:
                        name = other_names[0]
                    import_other_name[id_obj] = name

            return new_to_this_module

        new_to_this_module = 1
        while new_to_this_module:
            new_to_this_module = self.docmodule_add_parent_classes(
                this_module, id_to_data, class_parents, all_names) + find_import_data()

        # check the other modules for possible "from mod import *" action...
        importall_modules = get_importall_modules(id_to_data, other_module_names)

        # We finally have all the objects that will be added to this module
        # (with their names in this module), all the parent clases for classes
        # defined here, and all the import names for objects being imported...

        # Now, sort them all into lists by type for objects defined in in
        # this module, and a list of imported for things in other modules...

        modules = []
        classes = []
        funcs = []
        data = []
        imported = []

        bins = {
            'module': modules,
            'class': classes,
            'func': funcs,
            'data': data
        }
        for id_obj, (obj, objtype, source_module, names) in id_to_data.iteritems():
            if source_module == this_module or objtype == 'module':
                bins[objtype].append((obj, names))
            else:
                imported.append((obj, names, source_module))

        # Before adding things, prepopulate our module_map and id_map

        # these are modules which may or may not be used.  if we add an import
        # line it should be as close to possible to where it is used to avoid
        # circular imports
        self.maybe_modules = {}

        for obj, names in modules:
            self.add_to_module_map(obj.__name__, names[0])

        for mod in importall_modules:
            self.add_to_module_map(mod.__name__, '')

        # eventually, might want to replace module_map and id_map
        # with id_to_data...
        for id_obj, (obj, objtype, source_module, names) in id_to_data.iteritems():
            if objtype == 'module':
                continue
            self.id_map[id_obj] = names[0]

        # Finally, go through and start writing stuff out! Go though by type:
        #
        #    1) module imports
        #    2) from MODULE import *
        #    3) from MODULE import OBJ
        #    4) class definitions
        #    5) func defs
        #    6) data

        if modules:  # module imports
            for obj, names in modules:
                for import_name in names:
                    realname = getattr(obj, '__name__', None)
                    if not realname:
                        print "Warning - could not get a name for module %s" % obj
                        continue
                    if realname == this_name:
                        continue
                    import_text = self.import_mod_text(this_module, realname, import_name)
                    if import_text:
                        self.maybe_modules[import_name] = import_text

        if self.import_filter:
            modules, imported, importall_modules = self.import_filter(
                this_name, modules, imported, importall_modules)

        if importall_modules:  # from MODULE import *
            for mod in importall_modules:
                import_text = self.import_mod_text(this_module, mod.__name__, '*')
                if import_text:
                    self.contents.append(import_text)
            self.contents.extend(['', ''])

        if imported:  # from MODULE import OBJ
            for obj, names, source_module in imported:
                for name in names:
                    import_text = self.import_obj_text(source_module.__name__,
                                                       import_other_name[id(obj)],
                                                       name)
                    if import_text:
                        self.contents.append(import_text)
            self.contents.extend(['', ''])

        if classes:
            # sort in order of resolution
            def nonconflicting(classlist):
                for cls in classlist:
                    ancestors = set(inspect.getmro(cls)[1:])
                    if not ancestors.intersection(classlist):
                        yield cls

            sorted = []
            unsorted = set([x[0] for x in classes])

            while unsorted:
                for cls in nonconflicting(unsorted):
                    sorted.append(cls)
                unsorted.difference_update(sorted)

            contents = []
            classes = dict(classes)
            for cls in sorted:
                names = classes[cls]
                name = names[0]
                contents.append(self.document(cls, name, this_name))
                for alias in names[1:]:
                    contents.append('%s = %s' % (alias, name))
                # check if it has a default constructor... if so, add to the
                # list of classes that it is safe to create...
                if has_default_constructor(cls):
                    self.safe_constructor_classes.add(id(cls))

            classres = join(contents, '\n').split('\n')

            for i, line in enumerate(classres):
                if u'\xa0' in line:
                    print "bad char"
                    for j in range(max(i-10, 0), min(i+10, len(classres))):
                        if j == i:
                            print '-'*80
                        print classres[j]
                        if j == i:
                            print '-'*80
                    classres[i] = ''.join(line.split(u'\xa0'))

            self.contents.extend(classres)
            self.contents.extend(['', ''])

        if funcs:
            contents = []
            for obj, names in funcs:
                name = names[0]
                contents.append(self.document(obj, name, this_name))
            for alias in names[1:]:
                contents.append('%s = %s' % (alias, name))
            self.contents.extend(contents)
            self.contents.extend(['', ''])

        if data:
            contents = []
            for obj, names in data:
                name = names[0]
                contents.append(self.docother(obj, name, this_name, maxlen=70))
            for alias in names[1:]:
                contents.append('%s = %s' % (alias, name))
            self.contents.extend(contents)
            self.contents.extend(['', ''])

#        if hasattr(this_module, '__version__'):
#            version = str(this_module.__version__)
#            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
#                version = strip(version[11:-1])
#            result = result + self.section('VERSION', version) + '\n\n'
#        if hasattr(this_module, '__date__'):
#            result = result + self.section('DATE', str(this_module.__date__)) + '\n\n'
#        if hasattr(this_module, '__author__'):
#            result = result + self.section('AUTHOR', str(this_module.__author__)) + '\n\n'
#        if hasattr(this_module, '__credits__'):
#            result = result + self.section('CREDITS', str(this_module.__credits__)) + '\n\n'

        missing = [self.import_mod_text(this_module, mod, '')
                   for mod in self.missing_modules]
        missing += self.maybe_modules.values()
        if missing:
            contents = []
            for import_text in missing:
                if import_text:
                    contents.append(import_text)
            self.contents = contents + ['', ''] + self.contents
        result = join(self.contents, '\n')
        self.safe_constructor_classes = set()
        return result

    def add_to_module_map(self, realname, newname):
        oldname = self.module_map.get(realname, None)
        if oldname is None:
            self.module_map[realname] = newname
            return
        else:
            # if either old or new is a 'from realname import *', that's the
            # best possible outcome...
            if not oldname or not newname:
                self.module_map[realname] = ''
                return
            # otherwise, check to see if one of the names matches the last
            # part of realname...
            final_name = realname.split('.')[-1]
            if final_name in (oldname, newname):
                self.module_map[realname] = final_name
                return

            # otherwise, just take whatever one has the shorter number of
            # parts, with tie going to the old_val...
            oldnum = len(oldname.split('.'))
            newnum = len(newname.split('.'))

            if oldnum < newnum:
                self.module_map[realname] = oldname
            elif oldnum > newnum:
                self.module_map[realname] = newname
            # tie, do nothing...
            return

    def _module_has_static_name(self, module, name):
        if isinstance(module, basestring):
            module = sys.modules[module]
        elif not isinstance(module, types.ModuleType):
            raise TypeError(module)

        if module not in self.static_module_names:
            self.static_module_names[module] = get_static_module_names(module)
        return name in self.static_module_names[module]

    def classname(self, klass, modname, realmodule=None, consume_import=False):
        """Get a class name and qualify it with a module name if necessary."""
        if id(klass) in self.id_map:
            result = self.id_map[id(klass)]
            if consume_import:
                return result, None
            else:
                return result
        if realmodule is None:
            realmodule = klass.__module__
        return self._classname(klass.__name__, modname, realmodule, klass,
                               consume_import=consume_import)

    def _classname(self, realname, modname, realmodule, klass=None,
                   consume_import=False):
        import_text = None
        missing = None
        # first, see if the object's module is THIS module...
        if realmodule not in [modname, '__builtin__']:
            # next, check if the module is in map of 'known' modules...
            if realmodule in self.module_map:
                newmodname = self.module_map[realmodule]
            else:
                newmodname = None
                missing = False
                if klass is not None:
                    # check all known modules... see if any of them have this
                    # class in their contents...
                    for m in self.module_map.keys():
                        try:
                            mod = sys.modules[m]
                        except KeyError:
                            continue
                        else:
                            # print '\t', m, mod
                            if klass in mod.__dict__.values():
                                # print '\tfound'
                                newmodname = self.module_map[m]
                                break
                if not newmodname:
                    # try to see if any parent modules are known...
                    mod_parts = realmodule.split('.')
                    sub_parts = []
                    while mod_parts:
                        parentmod = '.'.join(mod_parts)
                        parentmodName = self.module_map.get(parentmod)
                        if parentmodName is not None:
                            # we have a parent module - so, ie,
                            # our class is xml.sax.handler.ErrorHandler,
                            # and we found the parent class xml.sax
                            # then our sub_parts will be ['handler']
                            # so we want to set modname to
                            #    (module_map['xml.sax']).handler...
                            newmodname = '.'.join([parentmodName] + sub_parts)

                            # check to see if the parentmod is in maybe_modules
                            # if so, we will need to make sure it is imported
                            # now
                            if consume_import:
                                import_text = self.maybe_modules.pop(parentmodName, None)

                            # we still need to make sure that the module gets
                            # imported, so that the parent module has the
                            # correct attributes on it - ie, if xml.sax exists,
                            # but we've never imported xml.sax.handler, the
                            # 'handler' attribute will not be on xml.sax
                            if sub_parts:
                                missing = True

                            # ...though we can add an entry to the module map

                            self.add_to_module_map(realmodule, newmodname)
                            break

                        sub_parts.insert(0, mod_parts.pop())

                if not newmodname:
                    missing = True
                    newmodname = realmodule
                elif verbose:
                    print "newmodname", newmodname, realmodule, self.maybe_modules
                if missing:
                    self.missing_modules.add(realmodule)
                    self.add_to_module_map(realmodule, realmodule)
            if newmodname:
                realname = newmodname + '.' + realname
                if consume_import and not import_text:
                    import_text = self.maybe_modules.pop(newmodname, None)
        if consume_import:
            return realname, import_text
        else:
            return realname

    def docclass(self, object, name=None, mod=None):
        """Produce text documentation for a given class object."""
        # print "docclass", name, object
        realname = object.__name__
        name = name or realname

        if is_named_tuple(object):
            title = '{name} = {namedtuple}({realname!r}, {fields!r})'.format(
                name=name, namedtuple=self.id_map[id(collections.namedtuple)],
                realname=realname, fields=object._fields)
            contents = []
        else:
            title, contents = self._docclass(object, name, mod=mod)
        contents = '\n'.join(contents)

        return title + self.indent(rstrip(contents), '    ') + '\n\n'

    def _docclass(self, object, name, mod=None):
        bases = object.__bases__
        full_name = mod + '.' + name

        title = 'class ' + name

        if bases:
            data = [self.classname(c, mod, consume_import=self.imports_precede_classes)
                    for c in bases]
            if self.imports_precede_classes:
                parents = [d[0] for d in data]
                imports = [d[1] for d in data if d[1] is not None]
            else:
                parents = data
                imports = []

            title = title + '(%s)' % join(parents, ', ')
            if imports:
                imports = '\n'.join(imports)
                title = imports + '\n\n' + title
        title += ':\n'

        doc = getdoc(object)
        contents = doc and [self.docstring(doc) + '\n'] or []
        push = contents.append

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:
                    # docroutine
                    push(self.document(getattr(object, name),
                                       name, full_name, object, kind))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, full_name))
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
                                       name, full_name, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = filter(lambda data: visiblename(data[0]),
                       inspect.classify_class_attrs(object))

        thisclass = object
        attrs, inherited = pydoc._split_list(attrs, lambda t: t[2] is thisclass)

        if thisclass is not __builtin__.object:
            if attrs:
                # Sort attrs by name.
                attrs.sort()

                # Pump out the attrs, segregated by kind.
                attrs = spill("Methods", attrs,
                              lambda t: t[1] == 'method')
                attrs = spill("Class methods", attrs,
                              lambda t: t[1] == 'class method')
                attrs = spill("Static methods", attrs,
                              lambda t: t[1] == 'static method')
                attrs = spill("Properties", attrs,
                              lambda t: t[1] == 'property')
                attrs = spilldescriptors("Data descriptors", attrs,
                                         lambda t: t[1] == 'data descriptor')
                attrs = spilldata("Data and other attributes", attrs,
                                  lambda t: t[1] == 'data')
            else:
                contents.append('pass')

        return title, contents

    def formatvalue(self, object):
        """Format an argument default value as text."""
        # check if the object is os.environ...
        isEnviron = False
        # os.environ is an old-style class, can't use isinstance on it!
        if object is os.environ or object.__class__ == os.environ.__class__:
            isEnviron = True
        if isinstance(object, dict):
            if object == os.environ:
                isEnviron = True
            elif len(set(object) & set(os.environ)) > (len(object) * 0.9):
                # If over 90% of the keys are in os.environ, assume it's os.environ
                isEnviron = True
        if isEnviron:
            objRepr = repr({'PROXY_FOR': 'os.environ'})
        else:
            if isinstance(object, unicode):
                # pydev can't handle unicode literals - ie, u'stuff' - so
                # convert to normal strings
                object = str(object)

            objRepr = self.repr(object)
            isPythonNameRepr = None

            if objRepr[0] == '<' and objRepr[-1] == '>':
                # representation needs to be converted to a string
                objRepr = repr(objRepr)
                realmodule = None
            # get the object's module
            elif hasattr(object, '__module__'):
                realmodule = object.__module__
            elif PYTHON_OBJECT_RE.match(objRepr):
                # it's a standard instance repr: e.g. foo.Bar('spangle')
                # ...or a constant, like PySide2.QtGui.QPalette.ColorRole.NoRole
                # see if we know the module
                realmodule = None
                name = objRepr
                while True:
                    parts = name.rsplit('.', 1)
                    if len(parts) == 1:
                        # done splitting
                        break
                    name = parts[0]
                    if name in self.module_map or name in sys.modules:
                        realmodule = name
                        break
            else:
                isPythonNameRepr = False
                realmodule = None

            foundSafeRepr = False

            if realmodule:
                # this code was added to handle PySide objects used as defaults
                # specifically maya.app.renderSetup.views.lightEditor.itemModel
                if objRepr.startswith(realmodule + '.'):
                    newObjRepr = objRepr[len(realmodule) + 1:]
                else:
                    newObjRepr = objRepr
                try:
                    modname = self.module_map[realmodule]
                except KeyError:
                    # check to see if it's an attribute on an object we're
                    # bringing in already - ie, PySide2.QtGui.QPalette.ColorRole.NoRole
                    # if we're already doing "from PySide2.QtGui import QPalette"
                    currentObj = sys.modules.get(realmodule)
                    foundObj = False

                    # check to see if the module this object is in is one that
                    # we're making a stub for; if so, it's highly likely that
                    # even if we can drill all the way down to get the object
                    # off the "real" thing, we may not be able to do so off the
                    # stub-object.  ie, if we do:
                    #    from PySide2.QtGui import QPalette
                    # and PySide2 is the "real" module, then we can do:
                    #    QPalette.ColorRole.NoRole
                    # safely. However, if we're stubbing all of PySide2, then
                    # PySide2.QtGui will be a stub module, and QPalette.ColorRole
                    # will be None.
                    # So it's not safe to use the "real name" if we have a stub
                    # module...
                    if realmodule in self.stubmodules or any(
                            realmodule.startswith(stubmod + '.') for stubmod in
                            self.stubmodules):
                        currentObj = None

                    if currentObj is not None:
                        if not newObjRepr:
                            remainingPieces = []
                        else:
                            remainingPieces = newObjRepr.split('.')
                            # reverse so we can pop off the end for efficiency...
                            remainingPieces.reverse()
                        finalNamePieces = []
                        while True:
                            if not finalNamePieces:
                                importedObjName = self.id_map.get(id(currentObj))
                                if importedObjName is not None:
                                    # we found an object that was already imported into
                                    # the namespace - ie, we got QPallete - but we need
                                    # to see if we can drill down to the desired object
                                    # - ie, QPalette.ColorRole.NoRole - so keep going
                                    finalNamePieces.append(importedObjName)
                            if not remainingPieces:
                                if finalNamePieces:
                                    # if we found an imported object, and we have no
                                    # more pieces, we successfully drilled down all
                                    # the way!
                                    foundObj = True
                                    objRepr = '.'.join(finalNamePieces)
                                break
                            nextPiece = remainingPieces.pop()
                            if not hasattr(currentObj, nextPiece):
                                # we got to a part of the name we couldn't retrieve,
                                # abort
                                break
                            if finalNamePieces:
                                finalNamePieces.append(nextPiece)
                            currentObj = getattr(currentObj, nextPiece)
                    if not foundObj:
                        print "WARNING: Not a known module: %r" % realmodule
                else:
                    if modname:
                        # it's possible that we got a module, but that the repr
                        # we have isn't a python name - ie, our module might be
                        # "os", and our repr is '{"dict": "wrapper"}', but we don't
                        # want to end up with 'os.{"dict": "wrapper"}'
                        if isPythonNameRepr is None:
                            isPythonNameRepr = bool(
                                PYTHON_OBJECT_RE.match(objRepr))
                        if isPythonNameRepr:
                            objRepr = modname + '.' + newObjRepr
            if not foundSafeRepr:
                # turn the object into a string - this is guaranteed
                # safe, and is still more informative than using None
                objRepr = repr(objRepr)
        return '=' + objRepr

    def docroutine_getspec(self, obj, parent=None, kind=None, signature_data=None):
        if inspect.isfunction(obj):
            args, varargs, varkw, defaults = inspect.getargspec(obj)
            return inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)
        else:
            return self.UNKNOWN_SIGNATURE

    def _add_docs(self, obj, decl, skipdocs):
        if skipdocs:
            doc = ''
        else:
            doc = getdoc(obj) or ''
        if doc:
            doc = rstrip(self.indent(self.docstring(doc)))
            return decl + '\n' + doc + '\n' + self.indent(self.PASS)
        else:
            return decl + ' ' + self.PASS

    def docroutine(self, obj, name=None, parent=None, parent_cls=None, kind=None, signature_data=None):
        """Produce text documentation for a function or method object."""
        realname = obj.__name__
        name = name or realname
        if name in keyword.kwlist:
            name += '_'

        if inspect.ismethod(obj):
            method = obj
            obj = obj.im_func
        else:
            method = None

        title = name

        decl = 'def ' + title + self.docroutine_getspec(obj, parent, kind, signature_data) + ':'

        if kind == 'static method' or isinstance(obj, staticmethod):
            decl = '@staticmethod\n' + decl
        elif kind == 'class method' or isinstance(obj, classmethod):
            decl = '@classmethod\n' + decl

        if (realname == '__getattr__' and method and
                    method.im_class.__name__ == 'Mel'):
            # special case handling for pymel.core.language.Mel.__getattr__,
            # so that if you do pm.mel.someMelFunction, it thinks it's valid
            return decl + '\n' + self.indent('return lambda *args: None') + '\n\n'
        else:
            return self._add_docs(obj, decl, self.skipdocs)

    def _docdescriptor(self, name, obj, mod):
        results = []
        push = results.append

        if name:
            push(name + ' = None')
            push('\n')
        return ''.join(results)

    def docproperty(self, obj, name=None, mod=None, klass=None, kind=None):
        """Produce text documentation for a property."""
        # print "docproperty", name, obj, mod, kind
        decl = '@property\ndef %s(self):' % (name,)
        return self._add_docs(obj, decl, self.skipdocs)

    def docdata(self, obj, name=None, mod=None, klass=None):
        """Produce text documentation for a data descriptor."""
        # print "docdata", name, object
        return self._docdescriptor(name, obj, mod)

    def docother_data_repr(self, obj):
        """Get string representation for a value"""
        try:
            for simple_type in self.SIMPLE_TYPES:
                if isinstance(obj, simple_type):
                    return self.repr(simple_type(obj))
            if is_dict_like(obj):
                value = '{}'
            elif isinstance(obj, tuple):
                value = '()'
            elif isinstance(obj, collections.Sequence):
                value = '[]'
            elif isinstance(obj, frozenset):
                value = 'frozenset()'
            elif isinstance(obj, collections.Set):
                value = 'set()'
            else:
                value = 'None'
        except NameError:
            # doing 'isinstance(object, collections.Mapping)' can cause:
            # NameError: Unknown C global variable
            # in some situations... ie, maya.OpenMaya.cvar...
            # ...some sort of swig error?
            value = 'None'
        return value

    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        # print "docother", name, object
        if name in ['__metaclass__']:
            return ''

        if name == '__all__':
            value = pprint.pformat(object)
        elif id(get_class(object)) in self.safe_constructor_classes:
            cls_name = self.id_map[id(get_class(object))]
            value = '%s()' % cls_name
        else:
            value = self.docother_data_repr(object)
        assert name is not None, "Name of object %r is None" % object
        if name == 'None':
            # special case exception for None, which is syntactically invalid
            # to assign to but can still be used as an attribute
            name = "locals()['None']"
        line = (name and name + ' = ' or '') + value + '\n'
        return line

    def import_mod_text(self, currmodule, importmodule, asname):
        # unfortunately, we need to use relative imports to avoid circular
        # import issues...
        ispkg = hasattr(currmodule, '__path__')
        currname = currmodule.__name__

        if importmodule in self.module_excludes.get(currname, ()):
            print "%s had %s in module_excludes" % (currname, importmodule)
            return ''

        if asname == '*':
            if importmodule in self.import_substitutions:
                return self.import_substitutions[importmodule]
            else:
                self.add_to_module_map(importmodule, '')
                return 'from ' + importmodule + ' import *'
        else:
            realname = importmodule

            realparts = realname.split('.')
            currparts = currname.split('.')
            importname = realname
            fromname = ''
            if currname in self.debugmodules:
                print '\t %-30s %-30s %s' % (realname, importname, asname)

            # test for siblings - needed to avoid circular imports
            if len(realparts) == len(currparts):
                if realparts[:-1] == currparts[:-1] and not ispkg:
                    if currname in self.debugmodules:
                        print "\t\tsibling"
                    fromname = '.'
                    importname = realparts[-1]
            # test if importing a child - ie, pymel may have a .core attribute,
            # simply because at some point we imported pymel.core, but we don't
            # need / want an explicit import statement
            elif len(realparts) > len(currparts):
                if realparts[:len(currparts)] == currparts:
                    # Check that asname matches realname, so that if we do
                    #     import pymel.core.nt as nt
                    # from inside pymel.core, we still get the nt showing up
                    if asname == realparts[-1]:
                        # Ok, we have a child module, with the standard name,
                        # inside the parent module... it's still possible the
                        # parent module explicitly imported the child... so
                        # use the static code analysis of the module to see if
                        # this name is in the expected module names...
                        if not self._module_has_static_name(currmodule, asname):
                            if currname in self.debugmodules:
                                print "\t\tparent, and not in static module names - no import"
                            return ''

                    # if we're doing a renamed parent import, we want to make it
                    # relative to avoid circular imports
                    fromname = '.'
                    importname = '.'.join(realparts[len(currparts):])

            if verbose:
                print "adding", realname, asname, importname

            self.add_to_module_map(realname, asname if asname else importname)
            if importname in self.import_substitutions:
                return '%s = None' % asname
            else:
                result = 'import ' + importname
                if importname != asname and asname:
                    result += ' as ' + asname
                if fromname:
                    result = 'from ' + fromname + ' ' + result
                return result

    def import_obj_text(self, importmodule, importname, asname):
        result = 'from %s import %s' % (importmodule, importname)
        if asname and asname != importname:
            result += (' as ' + asname)
        return result


class PEP484StubDoc(StubDoc):
    PASS = '...'
    UNKNOWN_SIGNATURE = '(...)'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('imports_precede_classes', False)
        StubDoc.__init__(self, *args, **kwargs)

    def docmodule(self, *args, **kwargs):
        result = StubDoc.docmodule(self, *args, **kwargs)
        result = 'from typing import Any, Container, Dict, Generic, Iterable, Iterator, List, Optional, Set, Tuple, TypeVar, Union\n' + result
        return result

    def docother(self, obj, name=None, mod=None, parent=None, maxlen=None,
                 doc=None):
        """Produce text documentation for a data object."""
        # print "docother", name, object
        if name in ['__metaclass__']:
            return ''

        if name == '__all__':
            value = pprint.pformat(obj)
            typ = None
        else:
            # value = self.docother_data_repr(obj)
            value = None
            if inspect.isclass(obj):
                typ = 'Type[%s]' % self.classname(obj, modname=mod)
            else:
                typ = self.classname(obj.__class__, modname=mod)

        assert name is not None, "Name of object %r is None" % obj
        if name == 'None':
            # special case exception for None, which is syntactically invalid
            # to assign to but can still be used as an attribute
            name = "locals()['None']"
        if typ is not None:
            line = name + ' : ' + typ
        else:
            line = name
        if value is not None:
            line += ' = ' + value
        # line += '\n'
        return line

    def docroutine_getspec(self, obj, parent=None, method_kind=None,
                           signature_data=None):
        if signature_data is None:
            return StubDoc.docroutine_getspec(self, obj, parent, method_kind)

        # NOTE: parent is the complete dotted path of the parent, including
        # e.g. the class
        IDENTIFIER = r'([a-zA-Z_][a-zA-Z0-9_.]*)'

        if method_kind is not None:
            # remove the class
            module = parent.rsplit('.', 1)[0]
        else:
            module = parent

        def get_id(typestr):
            parts = typestr.rsplit('.', 1)
            if len(parts) == 2 and module == parts[0]:
                # the type is from the same module.  remove the module name, but
                # also wrap the name in quotes.  types specified as strings are
                # forward-references and are perfectly valid.  the only
                # alternative to this is trying to order definitions based on
                # their types, which would be very hard, and would still require
                # forward references in some cases.
                return str(repr(parts[1]))
            elif len(parts) == 1:
                # not an identifier
                return typestr
            else:
                # typ = pydoc.locate(typestr)
                # if typ is not None:
                #     print "located", `typestr`, module
                #     return self.classname(typ, module)[0]
                # else:
                #     print "could not import", `typestr`, module
                #     return typestr
                id = self._classname(parts[1], modname=module,
                                     realmodule=parts[0])
                return id

        def make_annotation(typestr):
            # FIXME: being lazy here: we should only pass the parts of the
            # result that matched the IDENTIFER regex to get_id()
            return ''.join([get_id(x)
                            for x in re.split(IDENTIFIER, str(typestr))])

        # def make_annotation(typestr):
        #     typ = pydoc.locate(typestr)
        #     if typ:
        #         return self.classname(typ, parent)
        #     else:
        #         print "could not locate", typestr
        #         return typestr

        args = []
        if method_kind == 'method':
            args.append('self')
        elif method_kind == 'class method':
            args.append('cls')
        for arg in signature_data['args']:
            argdef = arg['name'] + ': ' + make_annotation(arg['type'])
            default = arg.get('default')
            if default:
                # argdef += ' = ' + default
                argdef += ' = ...'
            args.append(argdef)
        signature = '(' + ', '.join(args) + ')'
        signature += ' -> ' + make_annotation(signature_data['result'])
        return signature

    def _get_type_data(self, pathparts):
        if self.type_data is None:
            return None
        doc = self.type_data
        for i, p in enumerate(pathparts):
            if i != 0:
                doc = doc['members']
            try:
                doc = doc[p]
            except KeyError as err:
                return None
        return doc

    def docroutine(self, obj, name=None, parent=None, parent_cls=None,
                   kind=None, signature_data=None):
        parents = parent.split('.')
        doc = self._get_type_data(parents + [name])
        sigs = None
        CMP = {
            'args': [
                {
                    'name': 'other',
                    'type': 'Any'
                }
            ],
            'result': 'bool'
        }
        special = {
            '__eq__': CMP,
            '__ne__': CMP,
            '__ge__': CMP,
            '__le__': CMP,
            '__gt__': CMP,
            '__lt__': CMP,
            '__len__': {'args': [], 'result': 'int'},
            '__str__': {'args': [], 'result': 'str'},
            '__repr__': {'args': [], 'result': 'str'},
            '__nonzero__': {'args': [], 'result': 'bool'},
        }
        if name in special:
            doc = {'signatures': [special[name]]}

        if doc is not None:
            try:
                sigs = doc['signatures']
            except KeyError:
                print("Document missing 'signature' entry %s" % '.'.join(
                      parents + [name]))
                print(doc)
                sigs = None

        if sigs is None or len(sigs) == 1:
            if sigs is None:
                sig = None
            else:
                try:
                    sig = sigs[0]
                except IndexError:
                    print("Could not extract signature from %s" % '.'.join(parents + [name]))
                    print(doc)
                    raise
            return StubDoc.docroutine(self, obj, name, parent, parent_cls,
                                      kind, sig)
        else:
            defs = []
            for signature_data in sigs:
                defs.append('@override')
                defs.append(StubDoc.docroutine(self, obj, name, parent,
                                               parent_cls, kind, signature_data))
            return '\n'.join(defs)

    def docproperty_get_sig(self, obj, name, parent, doc, propkind):
        parents = parent.split('.')
        if doc is None:
            # foo -> Foo
            altname = name[0].upper() + name[1:]
            doc = self._get_type_data(parents + [altname])
            if doc is None:
                # foo ->  GetFoo
                altname = propkind.capitalize() + altname
                doc = self._get_type_data(parents + [altname])
                if doc is None and propkind == 'get':
                    # foo ->  IsFoo
                    altname = 'Is' + name[0].upper() + name[1:]
                    doc = self._get_type_data(parents + [altname])
        if doc:
            signature = self.docroutine_getspec(obj, parent=parent,
                                                method_kind='method',
                                                signature_data=doc['signatures'][0])
        else:
            signature = '(self)' if propkind == 'get' else '(self, value)'
        return signature

    def docproperty(self, obj, name=None, parent=None, klass=None, kind=None):
        """Produce text documentation for a property."""
        # print "docproperty", name, obj, mod, kind
        parents = parent.split('.')
        doc = self._get_type_data(parents + [name])
        signature = self.docproperty_get_sig(obj, name, parent, doc, 'get')
        decl = '@property\ndef %s%s:' % (name, signature)
        result = self._add_docs(obj, decl, self.skipdocs)
        if obj.fset is not None:
            signature = self.docproperty_get_sig(obj, name, parent, doc, 'set')
            decl = '@%s.setter\ndef %s%s:' % (name, name, signature)
            result += '\n' + self._add_docs(obj, decl, skipdocs=True)
        return result


def packagestubs(packagename, outputdir='', extensions=('py', 'pypredef', 'pi'),
                 skip_module_regex=None, import_exclusions=None, import_filter=None,
                 debugmodules=None, type_data=None, stubmodules=None):

    def get_python_file(modname, extension, ispkg):
        basedir = os.path.join(outputdir, extension)
        if extension == 'pypredef':
            curfile = os.path.join(basedir, modname)
        else:
            curfile = os.path.join(basedir, *modname.split('.'))
            if ispkg:
                curfile = os.path.join(curfile, '__init__')

        curfile = curfile + os.extsep + extension
        return curfile

    packagemod = __import__(packagename, globals(), locals(), ['dummy'], -1)
    # first, check to see if the given package is not a 'top level' module...and
    # if so, create any parent package dirs/__init__.py
    if '.' in packagename:
        for extension in extensions:
            if extension == 'pypredef':
                # pypredefs don't make directories / __init__.py
                continue
            parts = packagename.split('.')
            # if our packagename is 'my.long.sub.package', this will give us
            #   my
            #   my.long
            #   my.long.sub
            for i in xrange(1, len(parts)):
                parent_package = '.'.join(parts[:i])
                parent_file = get_python_file(parent_package, extension, True)
                parent_dir = os.path.dirname(parent_file)
                if not os.path.isdir(parent_dir):
                    os.makedirs(parent_dir)
                if not os.path.isfile(parent_file):
                    print "making empty %s" % parent_file
                    # this will "touch" the file - ie, create an empty one
                    with open(parent_file, 'a'):
                        pass

    if isinstance(type_data, str):
        with open(type_data) as f:
            type_data = json.load(f)

    for modname, mod, ispkg in subpackages(packagemod, skip_module_regex):
        if mod is None:
            # failed to import or skipped
            continue

        if verbose:
            print modname, ": starting"

        for extension in extensions:
            stub_class = PEP484StubDoc if extension == 'pyi' else StubDoc
            stubgen = stub_class(
                import_exclusions=import_exclusions,
                import_filter=import_filter,
                debugmodules=debugmodules,
                type_data=type_data)

            contents = stubgen.docmodule(mod, stubmodules=stubmodules)

            basedir = os.path.join(outputdir, extension)
            if extension == 'pypredef':
                curfile = os.path.join(basedir, modname)
            else:
                curfile = os.path.join(basedir, *modname.split('.'))
                if ispkg:
                    curfile = os.path.join(curfile, '__init__')

            curfile = curfile + os.extsep + extension

            curdir = os.path.dirname(curfile)
            if not os.path.isdir(curdir):
                os.makedirs(curdir)
            print "\t ...writing %s" % curfile
            with open(curfile, 'w') as f:
                f.write(contents)

        if verbose:
            print modname, ": done"
    if verbose:
        print "done"


def pymelstubs(extensions=('py', 'pypredef', 'pi'),
               modules=('pymel', 'maya', 'PySide2', 'shiboken2', 'flux'),
               skip_module_regex=None,
               pyRealUtil=False):
    """ Builds pymel stub files for autocompletion.

    Can build Python Interface files (pi) with extension='pi' for IDEs like wing."""
    
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
                    if not getattr(x, '__name__', 'pymel.core').startswith('pymel.core')]
                imported = [(obj, names, source_module)
                            for obj, names, source_module in imported
                            if not getattr(source_module, '__name__', 'pymel.core').startswith('pymel.core')]
                if not any(x.__name__ == 'maya.cmds' for x in importall_modules):
                    import maya.cmds
                    importall_modules.append(maya.cmds)

        return modules, imported, importall_modules

    for modulename in modules:
        try:
            print "making stubs for: %s" % modulename
            packagestubs(modulename, outputdir=outputdir, extensions=extensions,
                         skip_module_regex=skip_module_regex, import_exclusions=importExclusions,
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


# don't start name with test - don't want it automatically run by nose
def stubstest(pystubdir, extensions, doprint=True):
    '''Test the stubs modules.

    Don't call this from 'inside maya', as we've probably already loaded all
    the various 'real' modules, which can give problems.
    '''
    def importError(modname):
        print 'error importing %s:' % modname
        import traceback
        bad.append((modname, traceback.format_exc()))

    bad = []
    for ext in extensions:
        stubdir = os.path.realpath(os.path.join(pystubdir, ext))
        print "Testing all modules in: %s" % stubdir
        sys.path.insert(0, stubdir)
        try:
            for importer, modname, ispkg in \
                    pkgutil.walk_packages(path=[stubdir],
                                          onerror=importError):
                if verbose:
                    print 'testing %s' % modname
                try:
                    # Don't use the importer returned by walk_packages, as it
                    # doesn't always properly update parent packages's dictionary
                    # with submodule name - ie, you would do:
                    # import pymel.all
                    # print pymel.all
                    # ...and find that pymel had no attribute 'all'
                    #importer.find_module(modname).load_module(modname)
                    mod = __import__(modname, globals(), locals(), [])
                except Exception, error:
                    print 'Error: found bad module: %s - %s' % (modname, error)
                    importError(modname)
                else:
                    modfile = os.path.dirname(os.path.realpath(mod.__file__))
                    if not modfile.startswith(stubdir):
                        print("Warning: Imported module does not appear to be in "
                              "stub dir:\n   %s\n   %s" % (modfile, stubdir))
        finally:
            sys.path.pop(0)
    print 'done walking modules'
    if doprint:
        for modname, error in bad:
            print '*' * 60
            print 'could not import %s:\n%s' % (modname, error)
    return bad


def get_parser():
    import argparse
    # NOTE: it is important that the first line of the description is a
    # brief sentence, usually starting with a verb (Get, Download, Run),
    # optionally followed by two newlines and a more detailed description.
    # This ensure that it is parsed by our documentation generator.
    parser = argparse.ArgumentParser(
        description='Generate stub files')
    parser.add_argument('modules', nargs='+')

    parser.add_argument('--skip-module-regex', '-s', dest='skip_module_regex',
                        metavar='REGEX',
                        help='Reg'
                             'ular expression for modules which should not'
                             'be inspected')
    parser.add_argument('--extensions', metavar='EXT1,EXT2',
                        default='py', help='Comma setparated file extension')
    parser.add_argument('--test', action='store_true',
                        default=False, help='Test the stubs in output-dir')
    parser.add_argument('--verbose', action='store_true',
                        default=False, help='Verbose feedback')
    parser.add_argument('--output-dir', '-o', dest='outputdir', default='.',
                        help='Output directory')
    return parser


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = get_parser()
    args = parser.parse_args(argv)
    outputdir = os.path.abspath(args.outputdir)
    extensions = [x.strip() for x in args.extensions.split(',')]
    globals()['verbose'] = args.verbose
    if args.test:
        sys.exit(int(bool(stubstest(outputdir, extensions))))
    else:
        for module in args.modules:
            packagestubs(module, extensions=extensions,
                         skip_module_regex=args.skip_module_regex,
                         outputdir=outputdir)

if __name__ == '__main__':
    main()
