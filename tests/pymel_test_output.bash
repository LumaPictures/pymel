#!/bin/bash

settings_dir=~/maya_pymel_test

#if [[ -d "$settings_dir" ]]; then
#    rm -rf "$settings_dir"
#fi
mkdir -p $settings_dir

this_script=$(python -c "import os; import posixpath; print os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath('''$0''')))).replace(os.sep, posixpath.sep)")
echo "$this_script"

this_dir=$(dirname "$this_script")
echo "$this_dir"
pymel_dir=$(dirname "$this_dir")
nose_dir=$(dirname "$(dirname "$(python -c 'import nose; print nose.__file__')")")
unittest2_dir=$(dirname "$(dirname "$(python -c '''
try:
    import unittest2
except ImportError:
    pass
else:
    print unittest2.__file__''')")")
    
mayapy_dir=$(dirname "$(which mayapy)")


THE_CMD="export DISPLAY=:0.0;export HOME=$HOME;export TERM=$TERM;export SHELL=$SHELL;export USER=$USER;export PATH="'$PATH'":$mayapy_dir;export PYTHONPATH='$pymel_dir:$nose_dir:$unittest2_dir';${this_dir}/pymel_test.py --app-dir='$settings_dir' $@ 2>&1 | tee pymelTestOut.txt"

echo $THE_CMD

# for some reason, just doing:
#    env -i "$bash_cmd" -c "$THE_CMD"
# ...doesn't work in cygwin
bash_cmd=$(which bash)
env -i "$bash_cmd" -c "$THE_CMD"
