#!/bin/bash

CURRENT_DIR="$(cd "$(dirname "$BASH_SOURCE")"; pwd)"

cd $CURRENT_DIR/..
echo `pwd`
# remove existing stubs
# stubgen causes problems when writing over top of existing .pyi files that live
# in the source (it produces pyi files for packages, e.g. pymel/core.pyi)
find pymel/ -name '*.py' -exec rm -f "{}i" \;
# build the stubs
#python3 -m mypy --version

#python3 -c "import mypy.stubgen;mypy.stubgen.main()" --no-import -o ./ pymel/*.py pymel/api pymel/core pymel/internal pymel/util

#stubgen --no-import -o ./ pymel/core
python3 -m maintenance.buildstubs --no-import -o ./ pymel/core pymel/util pymel/all.py pymel/versions.py pymel/mayautils.py
