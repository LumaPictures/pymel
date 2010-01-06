#!/usr/bin/env python

#TODO: support OS's other than OSX. revert to default prefs

import sys, os
versions = '2008 2009 2010 2011'.split()

pymeldir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
os.chdir(pymeldir)
mayapy = '/Applications/Autodesk/maya%(version)s/Maya.app/Contents/bin/mayapy'

def rebuild():
    for version in versions:
        print "rebuilding ", version
        os.system( 'cd ' + pymeldir + ';' + mayapy % locals() + ' ' + sys.argv[0] + ' test' )

def delete(caches):
    for version in versions:
        for cache in caches:
            if not cache.startswith('maya'):
                cache = 'maya' + cache[0].upper() + cache[1:]
            cachefile = os.path.join( pymeldir, 'pymel', 'cache', cache + version + '.zip')
            if os.path.exists(cachefile):
                print "removing", cachefile
                os.remove( cachefile )
            else:
                print "does not exist", cachefile
            
def load():
    sys.path.insert(0,pymeldir)
    #for x in sys.path:
    #    print x
    import pymel.core

if __name__ == '__main__':
    args = sys.argv[1:]
    assert args, 'no caches passed to rebuild'

    if args[0]=='test':
        load()
    else:
        delete(args)
        rebuild()