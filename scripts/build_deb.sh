#!/usr/bin/env bash

# exit on any error
set -e

# types are: full, source, binary, any, all
BUILD_TYPE=all
if [[ "$#" -eq 1 ]]; then
    BUILD_TYPE=$1
fi

PACKAGE_NAME=smartmeter-datacollector
PACKAGE_VERSION=$(poetry version -s)

CWD=$PWD
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORK_DIR="${SCRIPT_DIR}/.."

PY_DIST_DIR="${WORK_DIR}/dist"

OUTPUT_DIR="${WORK_DIR}/deb_dist"
PACKAGE_DIR="${OUTPUT_DIR}/${PACKAGE_NAME}"

# delete previously built artifacts
echo -n "Cleaning up from previous builds.."
rm -rf "${OUTPUT_DIR}"
echo "..done"

# build the Python package
( bash "${SCRIPT_DIR}"/build_py.sh ) || { echo "Failed to build Python package. Exiting.."; exit 1; }

# build self-contained Python zip app with shiv
echo "Building self-contained Python zip package with shiv.."
SHIV_PACKAGE="${PY_DIST_DIR}/${PACKAGE_NAME}_${PACKAGE_VERSION}.pyz"
poetry run -- shiv -c smartmeter-datacollector --root /var/lib/smartmeter-datacollector/.datacollector_cache --compile-pyc -o "${SHIV_PACKAGE}" "${PY_DIST_DIR}/smartmeter_datacollector-${PACKAGE_VERSION}-"*.whl
echo "..done"

# prepare the output directory

mkdir -p "${PACKAGE_DIR}"

echo -n "Copying the bundled shiv file.."
cp "${PY_DIST_DIR}"/*.pyz "${PACKAGE_DIR}/${PACKAGE_NAME}".pyz
echo "..done"

cd "${PACKAGE_DIR}"

echo "Preparing the Debian package.."
echo "creating debian/ files"
# create the debian directory from templates
DEBFULLNAME="Supercomputing Systems AG" \
DEBEMAIL="info@scs.ch" \
dh_make -y --single --createorig --templates "${WORK_DIR}/debian-tmpl" --copyright gpl2 --packagename "${PACKAGE_NAME}_${PACKAGE_VERSION}"
echo "remove all unnecessary example files"
rm "${PACKAGE_DIR}"/debian/{*.ex,README.*,*.docs}
echo "..done"

# copy the systemd unit file to the generated debian directory
echo "Adding systemd service file to debian dir.."
cp ${WORK_DIR}/${PACKAGE_NAME}.service ./debian/${PACKAGE_NAME}.service
echo "..done"

# build the Debian package
echo "Building the Debian package ${BUILD_TYPE}.."
dpkg-buildpackage --build=${BUILD_TYPE} -rfakeroot -sa -us -uc
echo "..done"

cd ${CWD}
echo "SUCCESS: Debian binary package has been successfully built at '${OUTPUT_DIR}'/"
