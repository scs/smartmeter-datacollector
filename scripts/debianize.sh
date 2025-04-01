#!/usr/bin/env bash

# exit on any error
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORK_DIR=${SCRIPT_DIR}/..

echo "Delete previous debian files"
rm -rf "${WORK_DIR}/debian"

PKGNAME=smartmeter-datacollector
PKGVERSION=$(poetry version -s)

echo "Creating debian/ files for \"$PKGNAME\" version \"$PKGVERSION\""

# (re)create the debian directory
DEBFULLNAME="Supercomputing Systems AG" \
DEBEMAIL="info@scs.ch" \
dh_make -y --single --createorig --templates "${WORK_DIR}/debian-tmpl" --copyright gpl2 --packagename "${PKGNAME}_${PKGVERSION}"

echo "Remove all unnecessary example files"
rm "${WORK_DIR}"/debian/{*.ex,README.*,*.docs}

echo "SUCCESS: Project has been debianized at '${WORK_DIR}/debian/'"
