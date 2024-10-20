#!/usr/bin/env bash

# exit on any error
set -e

BUILD_TYPE=source
if [[ "$#" -eq 1 ]]; then
    BUILD_TYPE=$1
fi

PACKAGE_NAME=smartmeter-datacollector
PACKAGE_VERSION=$(poetry version -s)

CWD=$PWD
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORK_DIR=${SCRIPT_DIR}/..

OUTPUT_DIR=${WORK_DIR}/deb_dist
DIST_DIR=${WORK_DIR}/dist

# Delete previously built Debian distribution
echo -n "Cleaning up from previous builds.."
rm -rf ${OUTPUT_DIR} ${DIST_DIR}

# remove the source Debian package from the root folder
rm -f ${WORK_DIR}/${PACKAGE_NAME}-*.tar.gz
echo "..done"

# build the Python source distribution package
echo -n "Building Python source distribution package.."
poetry build --format=sdist --output=${DIST_DIR}
echo "..done"

# prepare the output directory
mkdir -p ${OUTPUT_DIR}/${PACKAGE_NAME}

# get and extract the Python source distribution package
echo -n "Extracting the Python source distribution package.."
cp ${DIST_DIR}/*.tar.gz ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz
tar -xf ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz -C ${OUTPUT_DIR}/${PACKAGE_NAME} --strip-components=1
echo "..done"

PACKAGE_DIR=${OUTPUT_DIR}/${PACKAGE_NAME}

# go into the package directory
cd ${PACKAGE_DIR}

echo "Preparing the Debian source package.."
echo "creating debian/ files"
# create the debian directory
DEBFULLNAME="Supercomputing Systems AG" \
DEBEMAIL=info@scs.ch \
dh_make -y --python --createorig --templates ${WORK_DIR}/debian-tmpl --packagename "smartmeter-datacollector_${PACKAGE_VERSION}"

# # create Python requirements.txt which is read in postinst script
# echo "Adding Python dependencies file 'requirements.txt' to debian/ dir"
# poetry export -f requirements.txt > debian/requirements.txt

# copy the systemd unit file to the generated debian directory
echo "copying systemd service file to debian/ dir"
cp ${WORK_DIR}/${PACKAGE_NAME}.service debian/python3-${PACKAGE_NAME}.service
echo "..done"

# build the Debian source package
echo -n "Building the Debian package (${BUILD_TYPE}).."
dpkg-buildpackage --build=${BUILD_TYPE} -rfakeroot -sa -us -uc
echo "..done"

cd ${CWD}

echo "SUCCESS: Debian package (${BUILD_TYPE}) has been successfully built at ${OUTPUT_DIR}/"
