#!/bin/bash

DIRNAME=`dirname $0`
cd `dirname $DIRNAME`

futurize -w -2 --no-diff -n -a pymel/core pymel/api pymel/internal/ pymel/tools/ pymel/util/ pymel/*.py examples/ maintenance/ tests/ setup.py
