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
try:
    import maya
except ImportError:
    import warnings
    warnings.warn( "ipymel can only be setup if the maya package can be imported" )
else:
        
    import IPython.ipapi
    ip = IPython.ipapi.get()
    
    import readline
    delim = readline.get_completer_delims()
    delim = delim.replace('|', '') # remove pipes
    delim = delim.replace(':', '') # remove colon
    #delim = delim.replace("'", '') # remove quotes
    #delim = delim.replace('"', '') # remove quotes
    readline.set_completer_delims(delim)
    
    import inspect, re, glob,os,shlex,sys
    import pymel
    
    import IPython.Extensions.ipy_completers
    
    def finalPipe(obj):
        """
        DAG nodes with children should end in a pipe (|), so that each successive pressing 
        of TAB will take you further down the DAG hierarchy.  this is analagous to TAB 
        completion of directories, which always places a final slash (/) after a directory.
        """
        
        if pymel.cmds.listRelatives( obj ):
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
        tmpres = pymel.cmds.ls( expand(node) )
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
        long_attrs = pymel.cmds.listAttr( node )
        short_attrs = pymel.cmds.listAttr( node , shortNames=1)
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
            
            fullpath = pymel.cmds.ls( path, l=1 )[0]
            if not fullpath: return []
            children = pymel.cmds.listRelatives( fullpath , f=1, c=1)
            if not children: return []
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
                res = pymel.cmds.ls( attr + '*' )
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
                matches = pymel.cmds.ls( expand(line), **kwargs )
            
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
#        tmp = matches[:]
#        for match in tmp:
#            res = pymel.cmds.listRelatives( match )
#            if res: matches.extend( [ match+ '|' + x for x in res ]  )
#        return matches
   
    def pymel_python_completer(self,event):
        """Match attributes or global python names"""
        #print "python_matches"
        import re
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
            obj = eval(expr, self.Completer.namespace)
        except:
            try:
                obj = eval(expr, self.Completer.global_namespace)
            except:
                raise IPython.ipapi.TryNext 
            
        if isinstance(obj, (pymel.DependNode, pymel.Attribute) ):

            node = unicode(obj)
            long_attrs = pymel.cmds.listAttr( node )
            short_attrs = pymel.cmds.listAttr( node , shortNames=1)
            
            matches = self.Completer.python_matches(text)
            
            # if node is a plug  ( 'persp.t' ), the first result will be the passed plug
            if '.' in node:
                attrs = long_attrs[1:] + short_attrs[1:]
            else:
                attrs = long_attrs + short_attrs
            return matches + [ expr + '.' + at for at in attrs ]    

        raise IPython.ipapi.TryNext 

    def buildRecentFileMenu():

        if "RecentFilesList" not in pymel.optionVar:
            return
    
        # get the list
        RecentFilesList = pymel.optionVar["RecentFilesList"]
        nNumItems = len(RecentFilesList)
        RecentFilesMaxSize = pymel.optionVar["RecentFilesMaxSize"]
    
#        # check if there are too many items in the list
#        if (RecentFilesMaxSize < nNumItems):
#            
#            #if so, truncate the list
#            nNumItemsToBeRemoved = nNumItems - RecentFilesMaxSize
#    
#            #Begin removing items from the head of the array (least recent file in the list)
#            for ($i = 0; $i < $nNumItemsToBeRemoved; $i++):
#
#                pymel.optionVar -removeFromArray "RecentFilesList" 0;
#
#            RecentFilesList = pymel.optionVar["RecentFilesList"]
#            nNumItems = len($RecentFilesList);

    
        # The RecentFilesTypeList optionVar may not exist since it was
        # added after the RecentFilesList optionVar. If it doesn't exist,
        # we create it and initialize it with a guess at the file type
        if nNumItems > 0 :
            if "RecentFilesTypeList" not in pymel.optionVar:
                pymel.mel.initRecentFilesTypeList( RecentFilesList )
                
            RecentFilesTypeList = pymel.optionVar["RecentFilesTypeList"]

            
        #toNativePath
        # first, check if we are the same.
    


    
    #ip.set_hook('complete_command', IPython.Extensions.ipy_cyeahompleters.cd_completer , re_key = regkey )
    #ip.set_hook('complete_command', filepath_completer , re_key = ".+(?:(?:\s+|\()'?)" )
    ip.set_hook('complete_command', pymel_python_completer , re_key = ".*" )
    ip.set_hook('complete_command', pymel_name_completer , re_key = "(.+(\s+|\())|(SCENE\.)" )
    
    
    ip.ex("from pymel import *")
    # if you don't want pymel imported into the main namespace, you can replace the above with something like:
    #ip.ex("import pymel as pm")
    
    ip.ex("""
import os.path
for _mayaproj in optionVar.get('RecentProjectsList', []):
    _mayaproj = os.path.join( _mayaproj, 'scenes' )
    if _mayaproj not in _dh:
        _dh.append(_mayaproj)""")

