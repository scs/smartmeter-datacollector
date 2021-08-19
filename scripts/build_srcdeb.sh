#!/usr/bin/env bash

# exit on any error
set -e

BUILD_TYPE=source
if [[ "$#" -eq 1 ]]; then
    BUILD_TYPE=$1
fi

PACKAGE_NAME=smartmeter-datacollector

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
pipenv run build > /dev/null 2>&1
echo "..done"

# prepare the output directory
mkdir -p ${OUTPUT_DIR}

# get and extract the Python source distribution package
echo -n "Extracting the Python source distribution package.."
cp ${DIST_DIR}/${PACKAGE_NAME}-*.tar.gz ${OUTPUT_DIR}
tar -xf ${OUTPUT_DIR}/${PACKAGE_NAME}-*.tar.gz -C ${OUTPUT_DIR}
echo "..done"

PACKAGE_DIR=$(find ${OUTPUT_DIR} -type d -name "${PACKAGE_NAME}-*")

# go into the output directory
cd ${OUTPUT_DIR}

# rename <package name>-<version>.tar.gz to <package name>_<version>.orig.tar.gz
echo -n "Preparing the Debian source package.."
PACKAGE_FILENAME_FULL=$(find . -type f -name "${PACKAGE_NAME}-*.tar.gz")
PACKAGE_FILENAME="${PACKAGE_FILENAME_FULL%.tar.gz}"
PACKAGE_FILENAME=$(echo ${PACKAGE_FILENAME} | sed "s/${PACKAGE_NAME}-\(.*\)$/${PACKAGE_NAME}_\1/")
mv ${PACKAGE_FILENAME_FULL} ${PACKAGE_FILENAME}.orig.tar.gz

# copy the prepared "debian" directory
cp -R ${WORK_DIR}/debian ${PACKAGE_DIR}/
echo "..done"

# build the Debian source package
echo -n "Building the Debian package (${BUILD_TYPE}).."
cd ${PACKAGE_DIR}/
dpkg-buildpackage --build=${BUILD_TYPE} -rfakeroot -sa -us -uc > /dev/null 2>&1
echo "..done"

cd ${CWD}

echo "SUCCESS: Debian package (${BUILD_TYPE}) has been successfully built at ${OUTPUT_DIR}/"
