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
    --no-python2-scripts=true \
    --with-dh-systemd \
    --compat=10 \
    --build-depends="dh-systemd (>= 1.5)"

# add Pre-Depends to debian/control for python3-pip
sed -i 's/^\(Depends: \)/Pre-Depends: python3-pip\n\1/' debian/control

# replace "${python3:Depends}" with "python3:any" because we install all dependencies using pip
sed -i 's/${python3:Depends}/python3:any/' debian/control

# fix the debhelper compatibility level in debian/control
sed -i 's/>= 9/>= 10/' debian/control

PIP_REQUIREMENTS=$(pipenv lock -r)

# write the debian/postinst file
cat <<EOT >> debian/postinst
#!/bin/sh
# postinst script for python3-smartmeter-datacollector
#
# see: dh_installdeb(1)

# exit on any error
set -e

USERNAME=smartmeter
GROUP=dialout

# make sure the dialout group already exists
if ! getent group | grep -q "^\${GROUP}:"; then
    >&2 echo "Expected group \"\${GROUP}\" doesn't exist!"
    exit 1
fi

# add new group "smartmeter" if it doesn't already exist
if ! getent group | grep -q "^\${USERNAME}:"; then
    echo -n "Adding group \${USERNAME}.."
    addgroup --quiet --system \${USERNAME} 2>/dev/null || true
    echo "..done"
fi

# add new user "smartmeter" if it doesn't already exist
if ! getent passwd | grep -q "^\${USERNAME}:"; then
    echo -n "Adding system user \${USERNAME}.."
    adduser --quiet \\
            --system \\
            --ingroup \${USERNAME} \\
            --no-create-home \\
            --disabled-login \\
            --disabled-password \\
            \${USERNAME} 2>/dev/null || true
    echo "..done"
fi

# add the new user "smartmeter" to the dialout group
if ! groups \${USERNAME} | cut -d: -f2 | grep -qw \${GROUP}; then
    adduser \${USERNAME} \${GROUP} > /dev/null 2>&1
fi

echo -n "Installing dependencies using pip.."
# write a pip requirements.txt for automatic dependency installation
echo "${PIP_REQUIREMENTS}" > /tmp/requirements.txt
# install all required dependencies
python3 -m pip install -r /tmp/requirements.txt > /dev/null 2>&1
rm /tmp/requirements.txt
echo "..done"

#DEBHELPER#

exit 0
EOT

# copy the systemd unit file to the generated debian directory
SYSTEMD_UNIT_FILE=$(find . -maxdepth 1 -type f -name '*.service' | cut -c 3-)
cp ${SYSTEMD_UNIT_FILE} debian/python3-${SYSTEMD_UNIT_FILE}

echo "SUCCESS: Project has been successfully debianized at debian/"
