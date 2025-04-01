#!/usr/bin/env bash

# exit on any error
set -e

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

# build the Python shiv package
( bash "${SCRIPT_DIR}/build_shiv.sh" ) || { echo "Failed to build shiv bundle. Exiting.."; exit 1; }

# prepare the output directory

mkdir -p "${PACKAGE_DIR}"

# get and extract the Python source distribution package
echo -n "Extracting the Python source distribution package.."
cp "${PY_DIST_DIR}"/*.tar.gz "${OUTPUT_DIR}/${PACKAGE_NAME}".tar.gz
tar -xf "${OUTPUT_DIR}/${PACKAGE_NAME}".tar.gz -C "${PACKAGE_DIR}" --strip-components=1
echo "..done"

cd "${PACKAGE_DIR}"

# copy the systemd unit file to the generated debian directory
echo "Copying & rename systemd service file to package dir"
cp ${WORK_DIR}/${PACKAGE_NAME}.service ./python3-${PACKAGE_NAME}.service
echo "..done"

echo "Preparing the Debian source package.."
echo "creating debian/ files"
# create the debian directory from templates
DEBFULLNAME="Supercomputing Systems AG" \
DEBEMAIL=info@scs.ch \
dh_make -y --single --createorig --templates "${WORK_DIR}/debian-tmpl" --copyright gpl2 --packagename "${PACKAGE_NAME}_${PACKAGE_VERSION}"
echo "remove all unnecessary example files"
rm "${PACKAGE_DIR}"/debian/{*.ex,README.*,*.docs}

# build the Debian source package
echo -n "Building the Debian source package.."
dpkg-buildpackage --build=full -rfakeroot -sa -us -uc
echo "..done"

cd ${CWD}
echo "SUCCESS: Debian source package has been successfully built at '${OUTPUT_DIR}'/"
