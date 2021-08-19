#!/usr/bin/env bash

# exit on any error
set -e

# Delete previously built distribution
rm -rf build/* dist/*

# fail if setup.py is not up-to-date
echo -n "Checking whether Pipfile and setup.py are synchronized..."
pipenv-setup check > /dev/null 2>&1 || {
    echo "FAILED"
    echo ""
    echo "Pipfile and setup.py are out of sync!"
    echo "Run \"pipenv run setup\" to fix this."
    exit 1
}
echo "OK"
echo ""

# build the source distribution and binary distribution wheel
python setup.py -q sdist bdist_wheel

echo "SUCCESS: Packages have been successfully built at dist/"
