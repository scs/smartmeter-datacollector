#!/usr/bin/env bash

# exit on any error
set -e

# delete previously generated debian directory
rm -rf debian

# create the debian directory
python setup.py \
    --command-packages=stdeb.command debianize \
    --with-python2=false \
    --with-python3=true \
    --no-python2-scripts=true

echo "SUCCESS: Project has been successfully debianized at debian/"
