#!/usr/bin/env python

# Ideally this should use the python interpreter used by mayapy, but without LD_LIBRARY_PATH or PYTHONHOME set

import argparse
import re
import sys
import zipfile
import os
from shutil import rmtree, copytree
from os.path import join, dirname, exists
from subprocess import check_output, check_call

def main(this_dir, full_ver):
    baseVer = re.split('[a-z]', full_ver)[0]
    print "Release version is %r" % full_ver
    print "Release base version is %r" % baseVer

    mtnc=`pwd`

    release_dir = join(mtnc, 'release', 'pymel-' + full_ver)
    release_zip = release_dir + '.zip'
    print "release directory:", release_dir
    src_root = dirname(mtnc)

    # print "looking for mayapy..."
    # pybin=`which mayapy 2> /dev/null`
    # if [ -z "$pybin" ]; then
    #     print "couldn't find mayapy."
    #     print "looking for python..."
    #     pybin="$(which python 2> /dev/null)"
    #     if [ -z "$pybin" ]; then
    #         print "ERROR: couldn't find a python executable!"
    #         exit 1
    #     else
    #         print "found $pybin"
    #     fi
    # else
    #     print "found $pybin"
    # fi


    # run in root of pymel dev
    # cd ../ && "$pybin" -c 'import pymel
    import pymel
    print "current pymel version is: %r" % pymel.__version__
    assert pymel.__version__ == baseVer

    cd "$mtnc"

    # FIXME: need to purge original import or call a subprocess
    print "checking completion stubs"
    # cd "$mtnc/../extras/completion/py" && python -c 'import re
    import pymel
    print "current stub version is: %r" % pymel.__version__
    assert pymel.__version__ == baseVer

    # clean out git stuff

    for root, dirs, files in os.walk(join(src_root, 'extras')):
        for name in files:
            if name.endswith('.pyc'):
                os.remove(join(root, name))

    #if [ ! -d ../extras/completion/pi ]; then
    #   print "ERROR: wing completion stubs do not exist"
    #fi

    if exists(release_dir):
        print "removing existing folder"
        rmtree(release_dir)

    if exists(release_zip):
        print "removing existing zip"
        os.remove(release_zip)

    check_call(['git', 'clone', '--shared', src_root, release_dir])

    rmtree(join(release_dir, '.git'))
    # FIXME: also .git*
    rmtree(join(release_dir, 'maintenance'))

    print "copying docs"
    rmtree(join(release_dir, 'docs'))
    copytree(join(src_root, 'docs', 'build', '1.0'),
             join(release_dir, 'docs'))

    print "copying stubs"
    copytree(join(src_root, 'extras', 'completion'),
             join(release_dir, 'extras', 'completion'))

    git_rev = check_output(['git', 'rev-parse', 'HEAD'])

    with open(join(release_dir, 'README'), 'a') as f:
        print "adding version info"
        f.write("\n")
        f.write("Release ver: %s\n" % full_ver)
        f.write("Pymel ver: %s\n" % baseVer)
        f.write("Git commit: %s\n" % git_rev)

    print "zipping"
    with zipfile.ZipFile(release_zip) as f:
        for root, dirs, files in os.walk(path):
            for name in files:
                f.write(join(root, name))
    # zip -rq "$release_dir.zip" "$release_dir"
    #rm -rfd pymel

