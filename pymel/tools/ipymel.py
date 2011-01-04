"""
prototype for a pymel ipython configuration

Current Features:
    tab completion of depend nodes, dag nodes, and attributes
    automatic import of pymel

Future Features:
    tab completion of PyNode attributes
    color coding of tab complete options:
        - to differentiate between methods and attributes
        - dag nodes vs depend nodes
        - shortNames vs longNames
    magic commands
    bookmarking of maya's recent project and files

To Use:
    place in your PYTHONPATH
    add the following line to the 'main' function of $HOME/.ipython/ipy_user_conf.py::

        import ipymel

Author: Chad Dombrova
Version: 0.1
"""
from optparse import OptionParser
try:
    import maya
except ImportError, e:
    print( "ipymel can only be setup if the maya package can be imported" )
    raise e

import IPython.ipapi
ip = IPython.ipapi.get()

from IPython.ColorANSI import TermColors, ColorScheme, ColorSchemeTable
from IPython.genutils import page

try:
    import readline
except ImportError:
    import pyreadline as readline
delim = readline.get_completer_delims()
delim = delim.replace('|', '') # remove pipes
delim = delim.replace(':', '') # remove colon
#delim = delim.replace("'", '') # remove quotes
#delim = delim.replace('"', '') # remove quotes
readline.set_completer_delims(delim)

import inspect, re, glob,os,shlex,sys
from pymel import core
import maya.cmds as cmds

import IPython.Extensions.ipy_completers

_scheme_default = 'Linux'

Colors = TermColors  # just a shorthand

# Build a few color schemes
NoColor = ColorScheme(
    'NoColor',{
    'instance'              : Colors.NoColor,
    'collapsed'             : Colors.NoColor,
    'tree'                  : Colors.NoColor,
    'transform'             : Colors.NoColor,
    'shape'                 : Colors.NoColor,
    'nonunique'             : Colors.NoColor,
    'nonunique_transform'   : Colors.NoColor,

    'normal'                : Colors.NoColor  # color off (usu. Colors.Normal)
    } )

LinuxColors = ColorScheme(
    'Linux',{
    'instance'              : Colors.LightCyan,
    'collapsed'             : Colors.Yellow,
    'tree'                  : Colors.Green,
    'transform'             : Colors.White,
    'shape'                 : Colors.LightGray,
    'nonunique'             : Colors.Red,
    'nonunique_transform'   : Colors.LightRed,

    'normal'                : Colors.Normal  # color off (usu. Colors.Normal)
    } )

LightBGColors = ColorScheme(
    'LightBG',{
    'instance'              : Colors.Cyan,
    'collapsed'             : Colors.LightGreen,
    'tree'                  : Colors.Blue,
    'transform'             : Colors.DarkGray,
    'shape'                 : Colors.Black,
    'nonunique'             : Colors.Red,
    'nonunique_transform'   : Colors.LightRed,

    'normal'                : Colors.Normal  # color off (usu. Colors.Normal)
    } )

# Build table of color schemes (needed by the dag_parser)
color_table = ColorSchemeTable([NoColor,LinuxColors,LightBGColors],
                                  _scheme_default)


def finalPipe(obj):
    """
    DAG nodes with children should end in a pipe (|), so that each successive pressing
    of TAB will take you further down the DAG hierarchy.  this is analagous to TAB
    completion of directories, which always places a final slash (/) after a directory.
    """

    if cmds.listRelatives( obj ):
        return obj + "|"
    return obj

def splitDag(obj):
    buf = obj.split('|')
    tail = buf[-1]
    path = '|'.join( buf[:-1] )
    return path, tail

def expand( obj ):
    """
    allows for completion of objects that reside within a namespace. for example,
    ``tra*`` will match ``trak:camera`` and ``tram``

    for now, we will hardwire the search to a depth of three recursive namespaces.
    TODO:
    add some code to determine how deep we should go

    """
    return (obj + '*', obj + '*:*', obj + '*:*:*')

def complete_node_with_no_path( node ):
    tmpres = cmds.ls( expand(node) )
    #print "node_with_no_path", tmpres, node, expand(node)
    res = []
    for x in tmpres:
        x =  finalPipe(x.split('|')[-1])
        #x = finalPipe(x)
        if x not in res:
            res.append( x )
    #print res
    return res

def complete_node_with_attr( node, attr ):
    #print "noe_with_attr", node, attr
    long_attrs = cmds.listAttr( node )
    short_attrs = cmds.listAttr( node , shortNames=1)
    # if node is a plug  ( 'persp.t' ), the first result will be the passed plug
    if '.' in node:
        attrs = long_attrs[1:] + short_attrs[1:]
    else:
        attrs = long_attrs + short_attrs
    return [ u'%s.%s' % ( node, a) for a in attrs if a.startswith(attr) ]

def pymel_name_completer(self, event):

    def get_children(obj):
        path, partialObj = splitDag(obj)
        #print "getting children", repr(path), repr(partialObj)

        try:
            fullpath = cmds.ls( path, l=1 )[0]
            if not fullpath: return []
            children = cmds.listRelatives( fullpath , f=1, c=1)
            if not children: return []
        except:
            return []

        matchStr = fullpath + '|' + partialObj
        #print "children", children
        #print matchStr, fullpath, path
        matches = [ x.replace( fullpath, path, 1) for x in children if x.startswith( matchStr ) ]
        #print matches
        return matches

    #print "\nnode", repr(event.symbol), repr(event.line)
    #print "\nbegin"
    line = event.symbol

    matches = None

    #--------------
    # Attributes
    #--------------
    m = re.match( r"""([a-zA-Z_0-9|:.]+)\.(\w*)$""", line)
    if m:
        node, attr = m.groups()
        if node == 'SCENE':
            res = cmds.ls( attr + '*' )
            if res:
                matches = ['SCENE.' + x for x in res if '|' not in x ]
        elif node.startswith('SCENE.'):
            node = node.replace('SCENE.', '')
            matches = ['SCENE.' + x for x in complete_node_with_attr(node, attr) if '|' not in x ]
        else:
            matches = complete_node_with_attr(node, attr)

    #--------------
    # Nodes
    #--------------

    else:
        # we don't yet have a full node
        if '|' not in line or (line.startswith('|') and line.count('|') == 1):
            #print "partial node"
            kwargs = {}
            if line.startswith('|'):
                kwargs['l'] = True
            matches = cmds.ls( expand(line), **kwargs )

        # we have a full node, get it's children
        else:
            matches = get_children(line)

    if not matches:
        raise IPython.ipapi.TryNext

    # if we have only one match, get the children as well
    if len(matches)==1:
        res = get_children(matches[0] + '|')
        matches += res
    return matches


def pymel_python_completer(self,event):
    """Match attributes or global python names"""
    #print "python_matches"
    text = event.symbol
    #print repr(text)
    # Another option, seems to work great. Catches things like ''.<tab>
    m = re.match(r"(\S+(\.\w+)*)\.(\w*)$", text)

    if not m:
        raise IPython.ipapi.TryNext

    expr, attr = m.group(1, 3)
    #print type(self.Completer), dir(self.Completer)
    #print self.Completer.namespace
    #print self.Completer.global_namespace
    try:
        #print "first"
        obj = eval(expr, self.Completer.namespace)
    except:
        try:
            #print "second"
            obj = eval(expr, self.Completer.global_namespace)
        except:
            raise IPython.ipapi.TryNext
    #print "complete"
    if isinstance(obj, (core.nt.DependNode, core.Attribute) ):
        #print "isinstance"
        node = unicode(obj)
        long_attrs = cmds.listAttr( node )
        short_attrs = cmds.listAttr( node , shortNames=1)

        matches = []
        matches = self.Completer.python_matches(text)
        #print "here"
        # if node is a plug  ( 'persp.t' ), the first result will be the passed plug
        if '.' in node:
            attrs = long_attrs[1:] + short_attrs[1:]
        else:
            attrs = long_attrs + short_attrs
        #print "returning"
        matches += [ expr + '.' + at for at in attrs ]
        #import colorize
        #matches = [ colorize.colorize(x,'magenta') for x in matches ]
        return matches

    raise IPython.ipapi.TryNext

def buildRecentFileMenu():

    if "RecentFilesList" not in core.optionVar:
        return

    # get the list
    RecentFilesList = core.optionVar["RecentFilesList"]
    nNumItems = len(RecentFilesList)
    RecentFilesMaxSize = core.optionVar["RecentFilesMaxSize"]

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
    if nNumItems > 0 :
        if "RecentFilesTypeList" not in core.optionVar:
            core.mel.initRecentFilesTypeList( RecentFilesList )

        RecentFilesTypeList = core.optionVar["RecentFilesTypeList"]


    #toNativePath
    # first, check if we are the same.

def open_completer(self, event):
    relpath = event.symbol
    #print event # dbg
    if '-b' in event.line:
        # return only bookmark completions
        bkms = self.db.get('bookmarks',{})
        return bkms.keys()


    if event.symbol == '-':
        print "completer"
        width_dh = str(len(str(len(ip.user_ns['_sh']) + 1)))
        print width_dh
        # jump in directory history by number
        fmt = '-%0' + width_dh +'d [%s]'
        ents = [ fmt % (i,s) for i,s in enumerate(ip.user_ns['_sh'])]
        if len(ents) > 1:
            return ents
        return []

    raise IPython.ipapi.TryNext

class TreePager(object):
    def __init__(self, colors, options):
        self.colors = colors
        self.options = options

    #print options.depth
    def do_level(self, obj, depth, isLast ):
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

        num = len(children)-1

        if children:
            if self.options.maxdepth and depth >= self.options.maxdepth:
                state = '+'
            else:
                state = '-'
            pre = self.colors['collapsed'] + state + ' '
        else:
            pre = '  '

        yield  pre + branch + name + self.colors['normal'] + '\n'
        #yield  Colors.Yellow + branch + sep + Colors.Normal+ name + '\n'

        if not self.options.maxdepth or depth < self.options.maxdepth:
            for i, x in enumerate(children):
                for line in self.do_level(x, depth, isLast+[i==num]):
                    yield line

    def make_tree(self, roots):
        num = len(roots)-1
        tree = ''
        for i, x in enumerate(roots):
            for line in self.do_level(x, 0, [i==num]):
                tree += line
        return tree

class DagTree(TreePager):
    def getChildren(self, obj):
        if self.options.shapes:
            return obj.getChildren()
        else:
            return obj.getChildren(type='transform')

    def getName(self, obj):
        name = obj.nodeName()

        if obj.isInstanced():
            if isinstance(obj, core.nt.Transform):
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
            if isinstance(obj, core.nt.Transform):
                # keep transforms bolded
                color = self.colors['nonunique_transform']
            else:
                color = self.colors['nonunique']
            name = color + name
        elif isinstance(obj, core.nt.Transform):
            # bold
            name = self.colors['transform'] + name
        else:
            name = self.colors['shape'] + name

        return name

dag_parser = OptionParser()
dag_parser.add_option("-d", type="int", dest="maxdepth")
dag_parser.add_option("-t", action="store_false", dest="shapes", default=True)
dag_parser.add_option("-s", action="store_true", dest="shapes" )
def magic_dag(self, parameter_s=''):
    """

    """
    options, args = dag_parser.parse_args(parameter_s.split())
    colors = color_table[self.rc.colors].colors
    dagtree = DagTree(colors, options)
    if args:
        roots = [core.PyNode(args[0])]
    else:
        roots = core.ls(assemblies=1)
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
        roots = core.listConnections(root, plugs=True, connections=True, source=True, destination=False, sourceFirst=True)
        return TreePager.make_tree(self,roots)

dg_parser = OptionParser()
dg_parser.add_option("-d", type="int", dest="maxdepth")
dg_parser.add_option("-t", action="store_false", dest="shapes", default=True)
dg_parser.add_option("-s", action="store_true", dest="shapes" )
def magic_dghist(self, parameter_s=''):
    """

    """
    options, args = dg_parser.parse_args(parameter_s.split())
    colors = color_table[self.rc.colors].colors
    dgtree = DGHistoryTree(colors, options)

    roots = [core.PyNode(args[0])]

    page(dgtree.make_tree(roots))

def magic_open(self, parameter_s=''):
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
    numcd = re.match(r'(-)(\d+)$',parameter_s)
    # jump in directory history by number
    if numcd:
        nn = int(numcd.group(2))
        try:
            ps = ip.ev('_sh[%d]' % nn )
        except IndexError:
            print 'The requested directory does not exist in history.'
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
        #turn all non-space-escaping backslashes to slashes,
        # for c:\windows\directory\names\
        parameter_s = re.sub(r'\\(?! )','/', parameter_s)
        opts,ps = self.parse_options(parameter_s,'qb',mode='string')

    # jump to previous
    if ps == '-':
        try:
            ps = ip.ev('_sh[-2]' % nn )
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
        ip.ex( 'openFile("%s", f=1)' % ps )
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

def setup():
    ip = IPython.ipapi.get()

    ip.set_hook('complete_command', pymel_python_completer , re_key = ".*" )
    ip.set_hook('complete_command', pymel_name_completer , re_key = "(.+(\s+|\())|(SCENE\.)" )
    ip.set_hook('complete_command', open_completer , str_key = "openf" )

    ip.ex("from pymel.core import *")
    # if you don't want pymel imported into the main namespace, you can replace the above with something like:
    #ip.ex("import pymel as pm")

    ip.expose_magic('openf', magic_open)
    ip.expose_magic('dag', magic_dag)
    ip.expose_magic('dghist', magic_dghist)

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

def main():
    import IPython.Shell

    s = IPython.Shell.start()
    setup()
    s.mainloop()

if __name__ == '__main__':
    main()