#!/bin/bash

settings_dir=~/maya_pymel_test

#if [[ -d "$settings_dir" ]]; then
#    rm -rf "$settings_dir"
#fi
mkdir -p $settings_dir

this_script=$(python -c "import os; import posixpath; print os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath('''$0''')))).replace(os.sep, posixpath.sep)")
echo "$this_script"

print_python_module_dir() {
    module="$1"
    python -c '
try:
    import '$module' as test_mod
except ImportError:
    # print nothing
    pass
else:
    import os
    import inspect
    mod_path = inspect.getsourcefile(test_mod)
    mod_dir = os.path.dirname(mod_path)
    if os.path.basename(os.path.splitext(mod_path)[0]) == "__init__":
        mod_dir = os.path.dirname(mod_dir)
    print mod_dir
'
}
this_dir=$(dirname "$this_script")
echo "$this_dir"
pymel_dir=$(dirname "$this_dir")
pytest_dir=$(print_python_module_dir pytest)
pkg_resources_dir=$(print_python_module_dir pkg_resources)
nose_dir=$(print_python_module_dir nose)
unittest2_dir=$(print_python_module_dir pytest)

mayapy_dir=$(dirname "$(which mayapy)")

THE_CMD="export DISPLAY=:0.0;export HOME=$HOME;export TERM=$TERM;export SHELL=$SHELL;export USER=$USER;export PATH="'$PATH'":$mayapy_dir;export PYTHONPATH='$pymel_dir:$pytest_dir:$pkg_resources_dir:$nose_dir:$unittest2_dir';${this_dir}/pymel_test.py --gui-stdout --app-dir='$settings_dir' $@"

echo $THE_CMD

# for some reason, just doing:
#    env -i "$bash_cmd" -c "$THE_CMD"
# ...doesn't work in cygwin
bash_cmd=$(which bash)
env -i "$bash_cmd" -c "$THE_CMD"
