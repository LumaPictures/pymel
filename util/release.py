from common import *

def release( username=None, password = None):
    
    # check that everything is importing ok
    import pymel.external.ply.lex as lex
    import pymel.examples.example1
    import pymel.examples.example2
    from pymel.types.path import path
        
    baseDir = moduleDir()
    tmpDir = baseDir.parent / "release" / str(pymel.__version__)
    if not tmpDir.exists():
        tmpDir.makedirs()
        
    releaseDir = tmpDir / "pymel"
    if releaseDir.exists():
        releaseDir.rmtree()
    print "copying to release directory", tmpDir
    baseDir.copytree( tmpDir / "pymel" )
    baseDir = tmpDir
    
    print "cleaning up"

    svndirs = [d for d in baseDir.walkdirs( '.*' )]
    for d in svndirs:
        print "removing", d
        d.rmtree()    
    for f in baseDir.walkfiles( '*.pyc' ):
        print "removing", f
        f.remove()
    for f in baseDir.walkfiles( '._*' ):
        print "removing", f    
        f.remove()    
        
    print "done"
    
    return

    #zipFile = baseDir.parent / 'pymel-%s.zip' % str(pymel.__version__)
    zipFile = baseDir.parent / 'pymel.zip'
    print "zipping up %s into %s" % (baseDir, zipFile)
    toZip(     baseDir, zipFile )

    import googlecode    
    if username and password:
        print "uploading to googlecode"
        googlecode.upload(zipFile, 'pymel', username, password, 'pymel ' + str(pymel.__version__), 'Featured')
        print "done"
