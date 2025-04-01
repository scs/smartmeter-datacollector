#!/usr/bin/env bash

# exit on any error
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORK_DIR="${SCRIPT_DIR}/.."

PY_DIST_DIR="${WORK_DIR}/dist"

# delete previously built artifacts
echo -n "Cleaning up from previous builds.."
rm -rf "${PY_DIST_DIR}"
echo "..done"

# build the Python package
echo "Building Python source package.."
poetry build --format=sdist --output="${PY_DIST_DIR}"
echo "..done"

echo "Building Python wheel.."
poetry build --format=wheel --output="${PY_DIST_DIR}"
echo "..done"

echo "SUCCESS: Python source package and wheel have been successfully built at '${PY_DIST_DIR}/'"
