#!/bin/bash

# this script should be run with sudo, which usually means that the PATH will be different
# from the current user.  as such, the most common use will be
#    install_dependencies $MAYA_LOCATION
#
if [ -z "$1" ]; then
    echo "please provide MAYA_LOCATION"
else
    export PATH=$1/bin:$PATH

    # ensures that other eggs are not found
    export PYTHONPATH=''

    # downloads setuptools
    mayapy -c "import ez_setup; ez_setup.use_setuptools(); import setuptools.command.easy_install"
    # setuptools is hardwired to look for "python2.6" on PATH
    ln -s "$1/bin/mayapy" "$1/bin/python2.6"
    sh setuptools-*-py2.6.egg
    rm "$1/bin/python2.6"

    mayapy `which easy_install` nose
    mayapy `which easy_install` sphinx
fi


