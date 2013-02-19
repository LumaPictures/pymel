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

    # downloads distribute (setuptools)
    curl -O http://python-distribute.org/distribute_setup.py
    mayapy ./distribute_setup.py
 
    # easy_install is not installed to $MAYA_LOCATION/bin on osx, so it's not on the PATH yet.
    # it's easier to mimic easy_install with mayapy than to try to find the executable
    #mayapy `which easy_install` nose
    #mayapy `which easy_install` sphinx

    mayapy -c "from setuptools.command.easy_install import main;main(['nose'])"
    mayapy -c "from setuptools.command.easy_install import main;main(['sphinx'])"

fi


