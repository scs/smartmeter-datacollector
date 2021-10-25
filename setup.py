#!/usr/bin/env python3
#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from os import path

from setuptools import find_packages, setup

from smartmeter_datacollector.__version__ import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="smartmeter-datacollector",
    version=__version__,
    description="Smart Meter Data Collector",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scs/smartmeter-datacollector",
    project_urls={
        "Source": "https://github.com/scs/smartmeter-datacollector",
        "Bug Reports": "https://github.com/scs/smartmeter-datacollector/issues",
        "Pull Requests": "https://github.com/scs/smartmeter-datacollector/pulls",
        "SCS": "https://www.scs.ch",
    },
    author="Supercomputing Systems AG",
    author_email="info@scs.ch",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Typing :: Typed",
    ],
    license="GPLv2",
    python_requires=">=3.7",
    packages=find_packages(
        exclude=["contrib", "doc", "LICENSES", "scripts", "tests", "tests."]
    ),
    include_package_data=True,
    install_requires=[
        "aioserial==1.3.0",
        "asyncio-mqtt==0.10.0",
        "gurux-dlms==1.0.107",
        "paho-mqtt==1.5.1",
        "pyserial==3.5",
    ],
    scripts=["bin/smartmeter-datacollector"],
    zip_safe=True,
    dependency_links=[],
)
