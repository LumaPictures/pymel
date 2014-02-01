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

    # Note that sphinx-1.1.3, 1.2.1, and the latest source stable commit in the
    # repo, as of 2014-01-31, all seem to have problems.  1.1.3 seemed to have
    # some sort of error when interfacing with graphviz (to generate the class
    # graphs), and the later versions seem to currently have a bug that causes
    # it to generate way-too-verbose summaries - for instance, the entry for
    # animCurveEditor in docs\build\1.0\generated\pymel.core.windows.html had
    # garbage from it's flag's in it's one-line summary.
    # I found the problem, and will submit a bug fix, so hopefully future
    # versions will be ok...

    mayapy -c "from setuptools.command.easy_install import main;main(['sphinx'])"
    mayapy -c "from setuptools.command.easy_install import main;main(['numpydoc'])"

fi


