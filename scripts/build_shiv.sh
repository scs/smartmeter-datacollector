#!/usr/bin/env bash

# exit on any error
set -e

PACKAGE_NAME=smartmeter-datacollector
PACKAGE_VERSION=$(poetry version -s)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORK_DIR="${SCRIPT_DIR}/.."

PY_DIST_DIR="${WORK_DIR}/dist"

# delete previously built artifacts
echo -n "Cleaning up from previous builds.."
rm -rf "${PY_DIST_DIR}"
echo "..done"

# build the Python package
( bash "${SCRIPT_DIR}"/build_py.sh ) || { echo "Failed to build Python package. Exiting.."; exit 1; }

# build self-contained Python zip app with shiv
echo "Building self-contained Python zip package with shiv.."
SHIV_PACKAGE="${PY_DIST_DIR}/${PACKAGE_NAME}_${PACKAGE_VERSION}.pyz"
poetry run -- shiv -c smartmeter-datacollector -o "${SHIV_PACKAGE}" "${PY_DIST_DIR}/smartmeter_datacollector-${PACKAGE_VERSION}-"*.whl
echo "..done"

echo "SUCCESS: Shiv package has been successfully built at '${PY_DIST_DIR}/'"
