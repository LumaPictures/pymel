#!/bin/bash

CURRENT_DIR="$(cd "$(dirname "$BASH_SOURCE")"; pwd)"

cd $CURRENT_DIR/..
echo `pwd`
# remove existing stubs
# stubgen causes problems when writing over top of existing .pyi files that live
# in the source (it produces pyi files for packages, e.g. pymel/core.pyi)
find pymel/ -name '*.pyi' -exec rm -f {} \;
# build the stubs
mayapy -c "import mypy.stubgen;mypy.stubgen.main()" --no-import -o ./ pymel/*.py pymel/api pymel/core pymel/internal pymel/util
