#!/bin/bash

settings_dir=~/maya_pymel_test

#if [[ -d "$settings_dir" ]]; then
#    rm -rf "$settings_dir"
#fi
mkdir -p $settings_dir

this_script=$(python -c "import os; print os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath('''$0'''))))")
this_dir=$(dirname "$this_script")

pymel_dir=$(dirname $this_dir)
nose_dir=$(dirname $(dirname $(python -c "import nose; print nose.__file__")))
mayapy_dir=$(dirname $(which mayapy))


THE_CMD="export DISPLAY=:0.0;export HOME=$HOME;export TERM=$TERM;export SHELL=$SHELL;export USER=$USER;export MAYA_APP_DIR="'"'"$settings_dir"'"'";export PATH="'$PATH'":$mayapy_dir;export PYTHONPATH=$pymel_dir:"'$PYTHONPATH'":$nose_dir;${this_dir}/pymel_test.py $@ 2>&1 | tee pymelTestOut.txt"

echo $THE_CMD
env -i bash -c "$THE_CMD"
