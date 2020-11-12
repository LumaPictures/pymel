#!/bin/bash

# Will eventually feed the ouptut of pymel_test.bash through tee, to get
# file logging

# The reason for having separate `pymel_test.bash` and `pymel_test_output.bash`
# is that the extra tee was causing hangs with our CI, so we need a version
# without it; however, the file logging is handy when running interactively.

# Until we transition our CI to use `pymel_test.bash`, though, this script
# just calls `pymel_test_output.bash` with no changes.

CURRENT_DIR="$(cd "$(dirname "$BASH_SOURCE")"; pwd)"
"$CURRENT_DIR/pymel_test.bash" "$@"