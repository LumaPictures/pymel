import os, commands, pprint


def diff_caches():
    CACHES = [  ('mayaApi', True ),
                ('mayaApiMelBridge', False ) ]
    
    for cacheName, useVersion in CACHES:
        diff_cache( cacheName, useVersion )
        
def diff_cache( cacheName, useVersion ):
    import pymel
    
    if useVersion:
        cacheName += pymel.mayahook.getMayaVersion(extension=False)
    # do a comparison of current caches with those from last release
    
    if not os.path.exists( cacheName + '_old.bin' ):
        last_release = commands.getoutput( 'svn ls https://pymel.googlecode.com/svn/tags' ).split('\n')[-1].strip('/')
        #maya_ver = pymel.mayahook.getMayaVersion()
        print "checking out %s cache from svn" % last_release
        print commands.getoutput( 'svn export https://pymel.googlecode.com/svn/tags/%s/pymel/%s.bin %s_old.bin' % (last_release, cacheName,cacheName) )
    
    print 'writing ' + cacheName + '.txt'
    f = file( cacheName + '.txt', 'w' )
    pprint.pprint( pymel.mayahook.loadCache( cacheName, '', useVersion=False ), f )
    f.close()

    print 'writing ' + cacheName + '_old.txt'
    f = file( cacheName + '_old.txt', 'w' )
    pprint.pprint( pymel.mayahook.loadCache( cacheName + '_old', '', useVersion=False ), f )
    f.close()
    
    print "diffing cache", cacheName

    cmd = 'diff -u %s_old.txt %s.txt > %s.diff' % ( cacheName, cacheName, cacheName )
    print cmd
    commands.getoutput( cmd ) 
    #os.remove( cacheName + '_old.bin' )
    
if __name__ == '__main__' :
    diff_caches()
