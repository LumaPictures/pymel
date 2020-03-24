"""
pymel ipython configuration

Current Features
----------------

tab completion of depend nodes, dag nodes, and attributes
automatic import of pymel

Future Features
---------------

- tab completion of PyNode attributes
- color coding of tab complete options
    - to differentiate between methods and attributes
    - dag nodes vs depend nodes
    - shortNames vs longNames
- magic commands
- bookmarking of maya's recent project and files

To Use
------

place in your PYTHONPATH
add the following line to the 'main' function of $HOME/.ipython/ipy_user_conf.py::

    import ipymel

Author: Chad Dombrova
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from past.builtins import basestring
from builtins import object
from optparse import OptionParser
try:
    import maya
except ImportError as e:
    print("ipymel can only be setup if the maya package can be imported")
    raise e


import IPython

ipy_ver = IPython.__version__.split('.')
ipy_ver = [int(x) if x.isdigit() else x for x in ipy_ver]

if ipy_ver < [0, 11]:
    def get_ipython():
        import IPython.ipapi
        return IPython.ipapi.get()

    IPython.ipapi.IPApi.define_magic = IPython.ipapi.IPApi.expose_magic
    import IPython.ColorANSI as coloransi
    from IPython.genutils import page
    from IPython.ipapi import UsageError
    import IPython.Extensions.ipy_completers

    def get_colors(obj):
        return color_table[obj.rc.colors].colors
else:  # >= [0, 11]
    import IPython.utils.coloransi as coloransi
    from IPython.core.page import page
    from IPython.core.error import UsageError

    def get_colors(obj):
        return color_table[ip.colors].colors

if ipy_ver >= [0, 13]:
    def define_magic(interpreter, function):
        def get_ipython():
            return interpreter
        from IPython.core.magic import register_line_magic
        register_line_magic(function)
else:
    def define_magic(interpreter, function):
        interpreter.define_magic(function.__name__, function)

try:
    from IPython.core.error import TryNext
except ImportError:
    from IPython.ipapi import TryNext


Colors = coloransi.TermColors
ColorScheme = coloransi.ColorScheme
ColorSchemeTable = coloransi.ColorSchemeTable

ip = None

try:
    import readline
except ImportError:
    import pyreadline as readline
delim = readline.get_completer_delims()
delim = delim.replace('|', '')  # remove pipes
delim = delim.replace(':', '')  # remove colon
# delim = delim.replace("'", '') # remove quotes
# delim = delim.replace('"', '') # remove quotes
readline.set_completer_delims(delim)

import inspect
import re
import glob
import os
import shlex
import sys

# don't import pymel here, as this will trigger loading of maya/pymel
# immediately, and things in the userSetup.py won't get properly entered into
# the ipython shell's namespace... we need the startup of maya to happen
# from "within" ipython, ie, when we do:
#   ip.ex("from pymel.core import *")
# from pymel import core

# we also can't even use maya.cmds, because it doesn't work in anything other
# than the main thread... and most of the tab-completion stuff runs in a
# subthread... so api it is!
# Use api2 because it's faster...
import maya.api.OpenMaya as om

_scheme_default = 'Linux'

# Build a few color schemes
NoColor = ColorScheme(
    'NoColor', {
        'instance': Colors.NoColor,
        'collapsed': Colors.NoColor,
        'tree': Colors.NoColor,
        'transform': Colors.NoColor,
        'shape': Colors.NoColor,
        'nonunique': Colors.NoColor,
        'nonunique_transform': Colors.NoColor,

        'normal': Colors.NoColor  # color off (usu. Colors.Normal)
    })

LinuxColors = ColorScheme(
    'Linux', {
        'instance': Colors.LightCyan,
        'collapsed': Colors.Yellow,
        'tree': Colors.Green,
        'transform': Colors.White,
        'shape': Colors.LightGray,
        'nonunique': Colors.Red,
        'nonunique_transform': Colors.LightRed,

        'normal': Colors.Normal  # color off (usu. Colors.Normal)
    })

LightBGColors = ColorScheme(
    'LightBG', {
        'instance': Colors.Cyan,
        'collapsed': Colors.LightGreen,
        'tree': Colors.Blue,
        'transform': Colors.DarkGray,
        'shape': Colors.Black,
        'nonunique': Colors.Red,
        'nonunique_transform': Colors.LightRed,

        'normal': Colors.Normal  # color off (usu. Colors.Normal)
    })

# Build table of color schemes (needed by the dag_parser)
color_table = ColorSchemeTable([NoColor, LinuxColors, LightBGColors],
                               _scheme_default)
color_table['Neutral'] = LightBGColors


def splitDag(obj):
    buf = obj.split('|')
    tail = buf[-1]
    path = '|'.join(buf[:-1])
    return path, tail


def expand(obj):
    """
    allows for completion of objects that reside within a namespace. for example,
    ``tra*`` will match ``trak:camera`` and ``tram``

    for now, we will hardwire the search to a depth of three recursive namespaces.
    TODO:
    add some code to determine how deep we should go

    """
    return (obj + '*', obj + '*:*', obj + '*:*:*')


def api_ls(args, dagOnly, long=False):
    '''Because the tab completer runs in a subthread, and cmds.ls doesn't
    seem to work very well from a subthread, use maya.api.OpenMaya'''
    sel = om.MSelectionList()

    if isinstance(args, basestring):
        args = [args]

    for arg in args:
        # if it doesn't exist, MSelectionList.add will raise an error -
        # ignore that
        try:
            sel.add(arg)
        except Exception:
            pass
    if not long and not dagOnly:
        return list(sel.getSelectionStrings())

    # long is only used when getting nodes, not plugs, so ignore that case
    # for now...
    results = []
    mfnDep = om.MFnDependencyNode()
    for i in range(sel.length()):
        try:
            dagPath = sel.getDagPath(i)
        except TypeError:
            if dagOnly:
                continue
            mobj = sel.getDependNode(i)
            mfnDep.setObject(mobj)
            results.append(mfnDep.name())
        else:
            if long:
                results.append(dagPath.fullPathName())
            else:
                results.append(dagPath.partialPathName())
    return results


def api_children(path):
    sel = om.MSelectionList()
    try:
        sel.add(path)
    except RuntimeError:
        return []
    if not sel.length():
        return []
    try:
        dagPath = sel.getDagPath(0)
    except TypeError:
        return []
    return [om.MFnDagNode(dagPath.child(i)).fullPathName()
            for i in range(dagPath.childCount())]


def api_listAttr(path, shortNames=False):
    sel = om.MSelectionList()
    try:
        sel.add(path)
    except RuntimeError:
        return []
    if not sel.length():
        return []
    try:
        plug = sel.getPlug(0)
    except TypeError:
        try:
            node = om.MFnDependencyNode(sel.getDependNode(0))
        except RuntimeWarning:
            return []
        attrs = [om.MFnAttribute(node.attribute(i))
                 for i in range(node.attributeCount())]
        if shortNames:
            return [x.shortName for x in attrs]
        else:
            return [x.name for x in attrs]
    else:
        return [plug.child(i).partialName(useLongNames=not shortNames)
                for i in range(plug.numChildren())]


def complete_node_with_attr(node, attr):
    # print "noe_with_attr", node, attr
    long_attrs = api_listAttr(node)
    short_attrs = api_listAttr(node, shortNames=1)
    # if node is a plug  ( 'persp.t' ), the first result will be the passed plug
    if '.' in node:
        attrs = long_attrs[1:] + short_attrs[1:]
    else:
        attrs = long_attrs + short_attrs
    return [u'%s.%s' % (node, a) for a in attrs if a.startswith(attr)]


def pymel_dag_completer(self, event):
    return pymel_name_completer(self, event, dagOnly=True)


def pymel_name_completer(self, event, dagOnly=False):
    def get_children(obj, dagOnly):
        path, partialObj = splitDag(obj)
        # print "getting children", repr(path), repr(partialObj)

        # try:
        if True:
            fullpaths = api_ls(path, dagOnly, long=True)
            if not fullpaths or not fullpaths[0]:
                return []
            fullpath = fullpaths[0]
            children = api_children(fullpath)
            if not children:
                return []
        # except Exception:
        #     return []

        matchStr = fullpath + '|' + partialObj
        matches = [x.replace(fullpath, path, 1) for x in children if x.startswith(matchStr)]
        return matches

    # print "\nnode", repr(event.symbol), repr(event.line)
    # print "\nbegin"

    # note that the NAME_COMPLETER_RE also works for DAG_MAGIC_COMPLETER_RE
    # and DAG_COMPLETER_RE, since those are simply more restrictive versions,
    # which set "dagOnly"
    # print "text_until_cursor: {}".format(event.text_until_cursor)
    # print "symbol: {}".format(event.symbol)
    linematch = NAME_COMPLETER_RE.match(event.text_until_cursor)
    # print "linematch: {}".format(linematch.group(0))
    nametext = linematch.group('namematch')
    # print "nametext: {}".format(nametext)

    matches = None

    #--------------
    # Attributes
    #--------------
    if not dagOnly:
        attr_match = ATTR_RE.match(nametext)
    else:
        attr_match = None
    if attr_match:
        node, attr = attr_match.groups()
        if node == 'SCENE':
            res = api_ls(attr + '*', dagOnly)
            if res:
                matches = ['SCENE.' + x for x in res if '|' not in x]
        elif node.startswith('SCENE.'):
            node = node.replace('SCENE.', '')
            matches = ['SCENE.' + x for x in complete_node_with_attr(node, attr) if '|' not in x]
        else:
            matches = complete_node_with_attr(node, attr)

    #--------------
    # Nodes
    #--------------
    else:
        # we don't yet have a full node
        if '|' not in nametext or (nametext.startswith('|') and nametext.count('|') == 1):
            # print "partial node"
            kwargs = {}
            if nametext.startswith('|'):
                kwargs['long'] = True
            matches = api_ls(expand(nametext), dagOnly, **kwargs)

        # we have a full node, get it's children
        else:
            matches = get_children(nametext, dagOnly)

    if not matches:
        raise TryNext

    # if we have only one match, get the children as well
    if len(matches) == 1 and not attr_match:
        res = get_children(matches[0] + '|', dagOnly)
        matches += res

    if event.symbol != nametext:
        # in some situations, the event.symbol will only have incomplete
        # information - ie, if we are completing "persp|p", then the symbol will
        # be "p" - nametext will give us the full "persp|p", which we need so we
        # know we're checking for children of "persp". In these situations, we
        # need to STRIP the leading non-symbol portion, so we don't end up with
        # "persp|persp|perspShape" after completion.
        if nametext.endswith(event.symbol):
            if not event.symbol:
                preSymbol = nametext
            else:
                preSymbol = nametext[:-len(event.symbol)]
            matches = [x[len(preSymbol):] if x.startswith(preSymbol) else x
                       for x in matches]
        # HOWEVER - in other situations, the symbol will contain too much
        # information - ie, stuff that isn't strictly speaking a node name - such
        # as when we complete "SCENE.p".  In this case, the symbol is "SCENE.p",
        # whereas nametext is simply "p". In such cases, we need to PREPEND the
        # extra "SCENE." to the result, or else ipython will think our matches
        # are not actually matches...
        elif event.symbol.endswith(nametext):
            if not nametext:
                symbolPrefix = event.symbol
            else:
                symbolPrefix = event.symbol[:-len(nametext)]
            matches = [symbolPrefix + x for x in matches]
    return matches


PYTHON_TOKEN_RE = re.compile(r"(\S+(\.\w+)*)\.(\w*)$")


def pymel_python_completer(self, event):
    """Match attributes or global python names"""
    import pymel.core as pm

    # print "python_matches"
    text = event.symbol
    # print repr(text)
    # Another option, seems to work great. Catches things like ''.<tab>
    m = PYTHON_TOKEN_RE.match(text)

    if not m:
        raise TryNext

    expr, attr = m.group(1, 3)
    # print type(self.Completer), dir(self.Completer)
    # print self.Completer.namespace
    # print self.Completer.global_namespace
    try:
        # print "first"
        obj = eval(expr, self.Completer.namespace)
    except Exception:
        try:
            # print "second"
            obj = eval(expr, self.Completer.global_namespace)
        except Exception:
            raise TryNext
    # print "complete"
    if isinstance(obj, (pm.nt.DependNode, pm.Attribute)):
        # print "isinstance"
        node = str(obj)
        long_attrs = api_listAttr(node)
        short_attrs = api_listAttr(node, shortNames=1)

        matches = []
        matches = self.Completer.python_matches(text)
        # print "here"
        # if node is a plug  ( 'persp.t' ), the first result will be the passed plug
        if '.' in node:
            attrs = long_attrs[1:] + short_attrs[1:]
        else:
            attrs = long_attrs + short_attrs
        # print "returning"
        matches += [expr + '.' + at for at in attrs]
        #import colorize
        #matches = [ colorize.colorize(x,'magenta') for x in matches ]
        return matches

    raise TryNext


def buildRecentFileMenu():
    import pymel.core as pm

    if "RecentFilesList" not in pm.optionVar:
        return

    # get the list
    RecentFilesList = pm.optionVar["RecentFilesList"]
    nNumItems = len(RecentFilesList)
    RecentFilesMaxSize = pm.optionVar["RecentFilesMaxSize"]

#        # check if there are too many items in the list
#        if (RecentFilesMaxSize < nNumItems):
#
#            #if so, truncate the list
#            nNumItemsToBeRemoved = nNumItems - RecentFilesMaxSize
#
#            #Begin removing items from the head of the array (least recent file in the list)
#            for ($i = 0; $i < $nNumItemsToBeRemoved; $i++):
#
#                core.optionVar -removeFromArray "RecentFilesList" 0;
#
#            RecentFilesList = core.optionVar["RecentFilesList"]
#            nNumItems = len($RecentFilesList);

    # The RecentFilesTypeList optionVar may not exist since it was
    # added after the RecentFilesList optionVar. If it doesn't exist,
    # we create it and initialize it with a guess at the file type
    if nNumItems > 0:
        if "RecentFilesTypeList" not in pm.optionVar:
            pm.mel.initRecentFilesTypeList(RecentFilesList)

        RecentFilesTypeList = pm.optionVar["RecentFilesTypeList"]

    # toNativePath
    # first, check if we are the same.


def open_completer(self, event):
    relpath = event.symbol
    # print event # dbg
    if '-b' in event.line:
        # return only bookmark completions
        bkms = self.db.get('bookmarks', {})
        return list(bkms.keys())

    if event.symbol == '-':
        width_dh = str(len(str(len(ip.user_ns['_sh']) + 1)))
        # jump in directory history by number
        fmt = '-%0' + width_dh + 'd [%s]'
        ents = [fmt % (i, s) for i, s in enumerate(ip.user_ns['_sh'])]
        if len(ents) > 1:
            return ents
        return []

    raise TryNext


class TreePager(object):

    def __init__(self, colors, options):
        self.colors = colors
        self.options = options

    # print options.depth
    def do_level(self, obj, depth, isLast):
        if isLast[-1]:
            sep = '`-- '
        else:
            sep = '|-- '
        #sep = '|__ '
        depth += 1
        branch = ''
        for x in isLast[:-1]:
            if x:
                branch += '    '
            else:
                branch += '|   '
        branch = self.colors['tree'] + branch + sep + self.colors['normal']

        children = self.getChildren(obj)
        name = self.getName(obj)

        num = len(children) - 1

        if children:
            if self.options.maxdepth and depth >= self.options.maxdepth:
                state = '+'
            else:
                state = '-'
            pre = self.colors['collapsed'] + state + ' '
        else:
            pre = '  '

        yield pre + branch + name + self.colors['normal'] + '\n'
        # yield  Colors.Yellow + branch + sep + Colors.Normal+ name + '\n'

        if not self.options.maxdepth or depth < self.options.maxdepth:
            for i, x in enumerate(children):
                for line in self.do_level(x, depth, isLast + [i == num]):
                    yield line

    def make_tree(self, roots):
        num = len(roots) - 1
        tree = ''
        for i, x in enumerate(roots):
            for line in self.do_level(x, 0, [i == num]):
                tree += line
        return tree


class DagTree(TreePager):

    def getChildren(self, obj):
        if self.options.shapes:
            return obj.getChildren()
        else:
            return obj.getChildren(type='transform')

    def getName(self, obj):
        import pymel.core as pm
        name = obj.nodeName()

        if obj.isInstanced():
            if isinstance(obj, pm.nt.Transform):
                # keep transforms bolded
                color = self.colors['nonunique_transform']
            else:
                color = self.colors['nonunique']
            id = obj.instanceNumber()
            if id != 0:
                source = ' -> %s' % obj.getOtherInstances()[0]
            else:
                source = ''
            name = color + name + self.colors['instance'] + ' [' + str(id) + ']' + source
        elif not obj.isUniquelyNamed():
            if isinstance(obj, pm.nt.Transform):
                # keep transforms bolded
                color = self.colors['nonunique_transform']
            else:
                color = self.colors['nonunique']
            name = color + name
        elif isinstance(obj, pm.nt.Transform):
            # bold
            name = self.colors['transform'] + name
        else:
            name = self.colors['shape'] + name

        return name

# formerly: magic_dag
dag_parser = OptionParser()
dag_parser.add_option("-d", type="int", dest="maxdepth")
dag_parser.add_option("-t", action="store_false", dest="shapes", default=True)
dag_parser.add_option("-s", action="store_true", dest="shapes")


def dag(self, parameter_s=''):
    import pymel.core as pm

    options, args = dag_parser.parse_args(parameter_s.split())
    colors = get_colors(self)
    dagtree = DagTree(colors, options)
    if args:
        roots = [pm.PyNode(args[0])]
    else:
        roots = pm.ls(assemblies=1)
    page(dagtree.make_tree(roots))


class DGHistoryTree(TreePager):

    def getChildren(self, obj):
        source, dest = obj
        return source.node().listConnections(plugs=True, connections=True, source=True, destination=False, sourceFirst=True)

    def getName(self, obj):
        source, dest = obj
        name = "%s -> %s" % (source, dest)
        return name

    def make_tree(self, root):
        import pymel.core as pm
        roots = pm.listConnections(root, plugs=True, connections=True, source=True, destination=False, sourceFirst=True)
        return TreePager.make_tree(self, roots)

# formerly: magic_dghist
dg_parser = OptionParser()
dg_parser.add_option("-d", type="int", dest="maxdepth")
dg_parser.add_option("-t", action="store_false", dest="shapes", default=True)
dg_parser.add_option("-s", action="store_true", dest="shapes")


def dghist(self, parameter_s=''):
    """

    """
    import pymel.core as pm

    options, args = dg_parser.parse_args(parameter_s.split())
    if not args:
        print("must pass in nodes to display the history of")
        return

    colors = get_colors(self)
    dgtree = DGHistoryTree(colors, options)

    roots = [pm.PyNode(args[0])]

    page(dgtree.make_tree(roots))

# formerly: magic_open


def openf(self, parameter_s=''):
    """Change the current working directory.

    This command automatically maintains an internal list of directories
    you visit during your IPython session, in the variable _sh. The
    command %dhist shows this history nicely formatted. You can also
    do 'cd -<tab>' to see directory history conveniently.

    Usage:

      openFile 'dir': changes to directory 'dir'.

      openFile -: changes to the last visited directory.

      openFile -<n>: changes to the n-th directory in the directory history.

      openFile --foo: change to directory that matches 'foo' in history

      openFile -b <bookmark_name>: jump to a bookmark set by %bookmark
         (note: cd <bookmark_name> is enough if there is no
          directory <bookmark_name>, but a bookmark with the name exists.)
          'cd -b <tab>' allows you to tab-complete bookmark names.

    Options:

    -q: quiet.  Do not print the working directory after the cd command is
    executed.  By default IPython's cd command does print this directory,
    since the default prompts do not display path information.

    Note that !cd doesn't work for this purpose because the shell where
    !command runs is immediately discarded after executing 'command'."""

    parameter_s = parameter_s.strip()
    #bkms = self.shell.persist.get("bookmarks",{})

    oldcwd = os.getcwd()
    numcd = re.match(r'(-)(\d+)$', parameter_s)
    # jump in directory history by number
    if numcd:
        nn = int(numcd.group(2))
        try:
            ps = ip.ev('_sh[%d]' % nn)
        except IndexError:
            print('The requested directory does not exist in history.')
            return
        else:
            opts = {}
#        elif parameter_s.startswith('--'):
#            ps = None
#            fallback = None
#            pat = parameter_s[2:]
#            dh = self.shell.user_ns['_sh']
#            # first search only by basename (last component)
#            for ent in reversed(dh):
#                if pat in os.path.basename(ent) and os.path.isdir(ent):
#                    ps = ent
#                    break
#
#                if fallback is None and pat in ent and os.path.isdir(ent):
#                    fallback = ent
#
#            # if we have no last part match, pick the first full path match
#            if ps is None:
#                ps = fallback
#
#            if ps is None:
#                print "No matching entry in directory history"
#                return
#            else:
#                opts = {}

    else:
        # turn all non-space-escaping backslashes to slashes,
        # for c:\windows\directory\names\
        parameter_s = re.sub(r'\\(?! )', '/', parameter_s)
        opts, ps = self.parse_options(parameter_s, 'qb', mode='string')

    # jump to previous
    if ps == '-':
        try:
            ps = ip.ev('_sh[-2]' % nn)
        except IndexError:
            raise UsageError('%cd -: No previous directory to change to.')
#        # jump to bookmark if needed
#        else:
#            if not os.path.exists(ps) or opts.has_key('b'):
#                bkms = self.db.get('bookmarks', {})
#
#                if bkms.has_key(ps):
#                    target = bkms[ps]
#                    print '(bookmark:%s) -> %s' % (ps,target)
#                    ps = target
#                else:
#                    if opts.has_key('b'):
#                        raise UsageError("Bookmark '%s' not found.  "
#                              "Use '%%bookmark -l' to see your bookmarks." % ps)

    # at this point ps should point to the target dir
    if ps:
        ip.ex('openFile("%s", f=1)' % ps)
#            try:
#                os.chdir(os.path.expanduser(ps))
#                if self.shell.rc.term_title:
#                    #print 'set term title:',self.shell.rc.term_title  # dbg
#                    platutils.set_term_title('IPy ' + abbrev_cwd())
#            except OSError:
#                print sys.exc_info()[1]
#            else:
#                cwd = os.getcwd()
#                dhist = self.shell.user_ns['_sh']
#                if oldcwd != cwd:
#                    dhist.append(cwd)
#                    self.db['dhist'] = compress_dhist(dhist)[-100:]

#        else:
#            os.chdir(self.shell.home_dir)
#            if self.shell.rc.term_title:
#                platutils.set_term_title("IPy ~")
#            cwd = os.getcwd()
#            dhist = self.shell.user_ns['_sh']
#
#            if oldcwd != cwd:
#                dhist.append(cwd)
#                self.db['dhist'] = compress_dhist(dhist)[-100:]
#        if not 'q' in opts and self.shell.user_ns['_sh']:
#            print self.shell.user_ns['_sh'][-1]

# maya sets a sigint / ctrl-c / KeyboardInterrupt handler that quits maya -
# want to override this to get "normal" python interpreter behavior, where it
# interrupts the current python command, but doesn't exit the interpreter


def ipymel_sigint_handler(signal, frame):
    raise KeyboardInterrupt


def install_sigint_handler(force=False):
    import signal
    if force or signal.getsignal(signal.SIGINT) == ipymel_sigint_handler:
        signal.signal(signal.SIGINT, ipymel_sigint_handler)

# unfortunately, it seems maya overrides the SIGINT hook whenever a plugin is
# loaded...


def sigint_plugin_loaded_callback(*args):
    # from the docs, as of 2015 the args are:
    #   ( [ pathToPlugin, pluginName ], clientData )
    install_sigint_handler()

sigint_plugin_loaded_callback_id = None

DAG_MAGIC_COMPLETER_RE = re.compile(r"(?P<preamble>%dag\s+)(?P<namematch>(?P<previous_parts>([a-zA-Z0-9:_]*\|)*)(?P<current_part>[a-zA-Z0-9:_]*))$")
DAG_COMPLETER_RE = re.compile(r"(?P<preamble>((.+(\s+|\())|(SCENE\.))[^\w|:._]*)(?P<namematch>(?P<previous_parts>([a-zA-Z0-9:_]*\|)+)(?P<current_part>[a-zA-Z0-9:_]*))$")
NAME_COMPLETER_RE = re.compile(r"(?P<preamble>((.+(\s+|\())|(SCENE\.))[^\w|:._]*)(?P<namematch>(?P<previous_parts>([a-zA-Z0-9:_.]*(\.|\|))*)(?P<current_part>[a-zA-Z0-9:_]*))$")
ATTR_RE = re.compile(r"""(?P<prefix>[a-zA-Z_0-9|:.]+)\.(?P<partial_attr>\w*)$""")


def setup(shell):
    global ip
    if hasattr(shell, 'get_ipython'):
        ip = shell.get_ipython()
    else:
        ip = get_ipython()

    ip.set_hook('complete_command', pymel_python_completer, re_key="(?!{})".format(NAME_COMPLETER_RE.pattern))
    ip.set_hook('complete_command', pymel_dag_completer, re_key=DAG_MAGIC_COMPLETER_RE.pattern)
    ip.set_hook('complete_command', pymel_dag_completer, re_key=DAG_COMPLETER_RE.pattern)
    ip.set_hook('complete_command', pymel_name_completer, re_key=NAME_COMPLETER_RE.pattern)
    ip.set_hook('complete_command', open_completer, str_key="openf")

    ip.ex("from pymel.core import *")
    # stuff in __main__ is not necessarily in ipython's 'main' namespace... so
    # if the user has something in userSetup.py that he wants put in the
    # "interactive" namespace, it won't be - unless we do this:
    ip.ex('from __main__ import *')
    # if you don't want pymel imported into the main namespace, you can replace the above with something like:
    #ip.ex("import pymel as pm")

    define_magic(ip, openf)
    define_magic(ip, dag)
    define_magic(ip, dghist)

    # add projects
    ip.ex("""
import os.path
for _mayaproj in optionVar.get('RecentProjectsList', []):
    _mayaproj = os.path.join( _mayaproj, 'scenes' )
    if _mayaproj not in _dh:
        _dh.append(_mayaproj)""")

    # add files
    ip.ex("""
import os.path
_sh=[]
for _mayaproj in optionVar.get('RecentFilesList', []):
    if _mayaproj not in _sh:
        _sh.append(_mayaproj)""")

    # setup a handler for ctrl-c / SIGINT / KeyboardInterrupt, so maya / ipymel
    # doesn't quit
    install_sigint_handler(force=True)
    # unfortunately, when Mental Ray loads, it installs a new SIGINT handler
    # which restores the old "bad" behavior... need to install a plugin callback
    # to restore ours...
    global sigint_plugin_loaded_callback_id
    import pymel.core as pm
    if sigint_plugin_loaded_callback_id is None:
        sigint_plugin_loaded_callback_id = pm.api.MSceneMessage.addStringArrayCallback(
            pm.api.MSceneMessage.kAfterPluginLoad,
            sigint_plugin_loaded_callback)


def main():
    import IPython

    ipy_ver = IPython.__version__.split('.')
    ipy_ver = [int(x) if x.isdigit() else x for x in ipy_ver]

    if ipy_ver >= [1, 0]:
        import IPython.terminal.ipapp
        app = IPython.terminal.ipapp.TerminalIPythonApp.instance()
        app.initialize()
        setup(app.shell)
        app.start()
    elif ipy_ver >= [0, 11]:
        import IPython.frontend.terminal.ipapp
        app = IPython.frontend.terminal.ipapp.TerminalIPythonApp.instance()
        app.initialize()
        setup(app.shell)
        app.start()
    else:
        import IPython.Shell

        shell = IPython.Shell.start()
        setup(shell)
        shell.mainloop()

if __name__ == '__main__':
    main()
