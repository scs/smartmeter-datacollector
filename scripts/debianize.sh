#!/usr/bin/env bash

# exit on any error
set -e

echo "Delete previous debian dir & files"
rm -rf debian

PKGVERSION=$(poetry version -s)

echo "Creating debian/ files for smartmeter-datacollector version \"$PKGVERSION\""

# (re)create the debian directory
DEBFULLNAME="Supercomputing Systems AG" \
DEBEMAIL=info@scs.ch \
dh_make -y --python --createorig --templates ../debian-tmpl --packagename "smartmeter-datacollector_${PKGVERSION}"

# create Python requirements.txt which is read in postinst script
echo "Adding Python dependencies file 'requirements.txt' to debian/ dir"
poetry export -f requirements.txt > debian/requirements.txt

# copy the systemd unit file to the generated debian directory
echo "Copying systemd service file to debian/ dir"
SYSTEMD_UNIT_FILE=$(find . -maxdepth 1 -type f -name '*.service' | cut -c 3-)
cp ${SYSTEMD_UNIT_FILE} debian/python3-${SYSTEMD_UNIT_FILE}

echo "SUCCESS: Project has been debianized at debian/"
