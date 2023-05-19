# Smart Meter Data Collector

<p align="center">
    <a href="LICENSE"><img alt="License: GPL-2.0-only" src="https://img.shields.io/badge/license-GPLv2-blue.svg"></a> <a href="https://github.com/scs/smartmeter-datacollector/pulls"><img alt="Pull Requests Welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a> <a href="https://github.com/scs/smartmeter-datacollector/pulls"><img alt="Contributions Welcome" src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg"></a>
    <br />
    <img alt="Python Code Checks" src="https://github.com/scs/smartmeter-datacollector/actions/workflows/python-code-checks.yml/badge.svg?branch=master"> <a href="https://pypi.org/project/smartmeter-datacollector/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/smartmeter-datacollector"></a>
    <br />
    <img src='ekz_logo.png' width="100">
</p>

---

The `smartmeter-datacollector` tool is a Python3 software which allows you to continuously retrieve data from supported smart meters (listed below).
The acquired values can be forwarded to one or more data sinks like a MQTT broker or logger.

This tool is an open source software funded by **[EKZ (Elektrizitätswerke des Kantons Zürich)](https://www.ekz.ch)** and developed by **[Supercomputing Systems AG](https://www.scs.ch)**. The goal of this voluntary initiative is to create a tool that can read, decode and decrypt data (if necessary) from the local interface of various smart meters and convert it into human-readable and simple formats. This should eliminate the complexity of decoding DLMS and similar protocols for the user. The user has the data in a format, which he can easily use in various use-cases ranging from simple visualization (see [Method 1: Raspberry Pi image with demo](#method-1-raspberry-pi-image-with-demo)) to integration into energy management algorithms or into custom home automation software. 

The following smart meters are supported (see [Wiki/Home](https://github.com/scs/smartmeter-datacollector/wiki/Home) for detailed information).

* Landis+Gyr E450: \
  Data pushed by smart meter over CII interface (wired M-Bus, HDLC, DLMS/COSEM).
* Landis+Gyr E360: \
  Data pushed by smart meter over P1 interface (HDLC, DLMS/COSEM only, no DSMR).
* Iskraemeco AM550: \
  Data pushed by smart meter over P1 interface (HDLC, DLMS/COSEM only, no DSMR).
* Kamstrup OMNIPOWER with HAN-NVE: \
  Data pushed by smart meter over inserted [HAN-NVE module](https://www.kamstrup.com/en-en/electricity-solutions/meters-devices/modules/hannve) (wired M-Bus, HDLC, DLMS/COSEM).

Note: All smart meters integrated so far push binary data encoded with HDLC (IEC 62056-46) and DLMS/COSEM. Both unencrypted and encrypted DLMS messages are accepted by the software.

The following data sinks are implemented:
* MQTT (v3.1.1):
  * Encryption
    * Unencrypted connection
    * Encrypted connection
      * TLS
      * optional custom CA certificate
  * Authentication
    * Unauthenticated
    * Authenticated with username / password
    * Authenticated with client certificate
* Logger to `stdout`

`smartmeter-datacollector` is fully configurable through a `.ini` configuration file. The [`smartmeter-datacollector-configurator`](https://github.com/scs/smartmeter-datacollector-configurator) webinterface can help to create and modify the configuration.

---

- [Smart Meter Data Collector](#smart-meter-data-collector)
- [How to install](#how-to-install)
  - [Method 1: Raspberry Pi image with demo](#method-1-raspberry-pi-image-with-demo)
  - [Method 2: Python package](#method-2-python-package)
    - [Python Requirements](#python-requirements)
    - [Installation](#installation)
  - [Method 3: Debian package](#method-3-debian-package)
    - [Debian Requirements](#debian-requirements)
    - [Installation](#installation-1)
- [How to use](#how-to-use)
  - [Configuration](#configuration)
    - [Specification](#specification)
    - [smartmeter-datacollector-configurator](#smartmeter-datacollector-configurator)
  - [Run manually](#run-manually)
    - [Configuration](#configuration-1)
  - [Run as a systemd service](#run-as-a-systemd-service)
    - [Configuration](#configuration-2)
- [How to develop](#how-to-develop)
  - [Development Requirements](#development-requirements)
  - [Installation](#installation-2)
    - [Debian / Ubuntu](#debian--ubuntu)
  - [Checkout the code](#checkout-the-code)
  - [Setup Development Environment](#setup-development-environment)
  - [Custom Commands / Workflows](#custom-commands--workflows)
- [Acknowledgements](#acknowledgements)

# How to install

There are different methods how to use `smartmeter-datacollector`.

1. Raspberry Pi image with demo
2. Python package
3. Debian package

## Method 1: Raspberry Pi image with demo

For a very easy first time usage of `smartmeter-datacollector` we provide a [Raspberry Pi image](https://github.com/scs/smartmeter-datacollector/releases) (based on Raspberry Pi OS) which contains the following parts:
* `smartmeter-datacollector` as a systemd service
* `smartmeter-datacollector-configurator` webinterface
* demo
  * [mosquiotto](https://mosquitto.org/) as a local MQTT broker to publish the measurements from `smartmeter-datacollector`
  * [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) to collect measurements published by `smartmeter-datacollector` over MQTT and store them in InfluxDB
  * [InfluxDB](https://www.influxdata.com/) to store the measurements
  * [Grafana](https://grafana.com/) to visualize the measurements

See [Wiki/Demo](https://github.com/scs/smartmeter-datacollector/wiki/Demo-(Raspberry-Pi-Image)) for detailed setup instructions.

## Method 2: Python package

`smartmeter-datacollector` can be installed as a Python3 package either from [PyPi](https://pypi.org/project/smartmeter-datacollector/) or manually using a [released wheel](https://github.com/scs/smartmeter-datacollector/releases).

The Python3 package does not contain any infrastructure to run `smartmeter-datacollector` in the background or to automatically start it during a boot sequence. If such infrastructure is required either see [Method 3: Debian package](#method-3-debian-package) or provide it yourself.

### Python Requirements

* Python >= 3.7 (tested with 3.8)

### Installation

Install the package either as global Python package or in a virtualenv with

```bash
python3 -m pip install smartmeter-datacollector
```

Similarly the [`smartmeter-datacollector-configurator`](https://github.com/scs/smartmeter-datacollector-configurator) webinterface can be installed with

```bash
python3 -m pip install smartmeter-datacollector-configurator
```

## Method 3: Debian package

`smartmeter-datacollector` is also available as a Debian (`.deb`) package from the [releases](https://github.com/scs/smartmeter-datacollector/releases) which installs it system wide. The Debian package includes a systemd service file which enables `smartmeter-datacollector` to automatically start after booting the system.

### Debian Requirements

* Distribution
  * Debian
* Release
  * Bullseye
* CPU architecture
  * amd64
  * armhf

### Installation

Download the Debian package from [releases](https://github.com/scs/smartmeter-datacollector/releases) and install it with

```bash
sudo apt install ./python3-smartmeter-datacollector_*.deb
```

Similarly the [`smartmeter-datacollector-configurator`](https://github.com/scs/smartmeter-datacollector-configurator) webinterface can be installed with a Debian package from its [releases](https://github.com/scs/smartmeter-datacollector-configurator/releases) with

```bash
sudo apt install ./python3-smartmeter-datacollector-configurator_*.deb
```

# How to use

The usage of `smartmeter-datacollector` depends on the installation method. Independent of the installation method a `.ini` configuration file is required to properly run `smartmeter-datacollector`.

## Configuration

### Manually create configuration

See [Wiki/Configuration](https://github.com/scs/smartmeter-datacollector/wiki/Configuration#manually-write-configuration) for more details on the available configuration options.

### smartmeter-datacollector-configurator

To simplify the process of generating a valid `.ini` configuration for `smartmeter-datacollector` the companion [`smartmeter-datacollector-configurator`](https://github.com/scs/smartmeter-datacollector-configurator) webinterface can be used. It supports
* a graphical approach to manage the configuration
* input validation to avoid invalid configurations
* loading / saving / discarding a configuration
* restarting `smartmeter-datacollector` (only if installed as a Debian package)

See [Wiki/smartmeter-datacollector-configurator](https://github.com/scs/smartmeter-datacollector/wiki/smartmeter-datacollector-configurator) for more details on the webinterface and the configuration possibilities.

## Run manually

Run `smartmeter-datacollector` with the following command:

```
smartmeter-datacollector --config datacollector.ini
```

The following command line arguments are supported:
* `-h, --help`: Shows the help output of `smartmeter-datacollector`.
* `-c, --config CONFIG`: Path to the `.ini` configuration file.
* `-s,--saveconfig`: Create a default `.ini` configuration file.
* `-d, --dev`: Enable development mode.

### Configuration

The configuration file can be located anywhere and use any filename. If no `.ini` configuration file is specified a default configuration with the following options is used:
* Landys+Gyr E450 smart meter in unencrypted mode connected to `/dev/ttyUSB0`
* `LOGGER` sink
* `MQTT` sink connected to a local broker without encryption or authentication

## Run as a systemd service

When `smartmeter-datacollector` has been installed as a Debian package it provides a systemd .service file named `python3-smartmeter-datacollector.service`. Therefore the service can be managed using the `systemctl` command. See [Run as a systemd service](https://github.com/scs/smartmeter-datacollector/wiki/How-to-use#run-as-a-systemd-service) for possible commands.


# How to develop

Help from the community for the `smartmeter-datacollector` project is always welcome. Please follow the next few chapters to setup a working development environment.

## Development Requirements

* Python >= 3.8, <= 3.10
* [`pipenv`](https://pipenv.pypa.io/en/latest/)
* Optional software packages (Debian bullseye/ Ubuntu 22.04)
  * python3-all
  * debhelper
  * dh-python

## Installation

### Debian / Ubuntu

To install the listed minimal requirements run the following command:

```
sudo apt install git python3 pipenv
```

To install the optional requirements also run the following command:

```
sudo apt install python3-all debhelper dh-python
```

## Checkout the code

Use `git` to clone / checkout `smartmeter-datacollector` from GitHub using

```
git clone https://github.com/scs/smartmeter-datacollector.git
```

## Setup Development Environment

`smartmeter-datacollector` uses [`pipenv`](https://pipenv.pypa.io/en/latest/) to manage its dependencies and setup a virtual environment. Run the following command to setup the initial development environment:

```
pipenv install --dev
```

This will install all runtime and development dependencies for `smartmeter-datacollector` in a new virtual environment. Now you are ready to start working on `smartmeter-datacollector`.

## Custom Commands / Workflows

`smartmeter-datacollector` offers a few custom `pipenv run` commands to simplify certain development workflows:
* `build_check` uses `twine` to check if the built Python package will be accepted by `PiPI`.
* `build_deb` builds a Debian package for the current development platform.
* `build_srcdeb` builds a Debian source package which can be used to build a Debian (binary) package for any platform (e.g. using [`pbuilder`](https://pbuilder-docs.readthedocs.io/en/latest/usage.html))
* `build` builds a Python package which can be uploaded to [`PyPI`](https://pypi.org/project/smartmeter-datacollector/) using `twine`.
* `debianize` creates a `debian/` directory used to build Debian source / binary packages.
* `format_check` checks if the code follows the [`autopep8`](https://pypi.org/project/autopep8/) code formatting rules.
* `format` automatically adjusts the code to follow the `autopep8` code formatting rules.
* `isort_check` checks if the order of the import statements is correct using [`isort`](https://pycqa.github.io/isort/).
* `isort` automatically re-orders the import statements using `isort`.
* `license` makes sure every Python (`*.py`) file contains the proper license header.
* `lint_check` checks if the code follows the [`pylint`](https://pypi.org/project/pylint/) rules defined in `pyproject.toml`.
* `lint` automatically adjust the code to follow the `pylint` rules defined in `pyproject.toml`.
* `setup_check` checks whether the dependencies defined in `Pipfile` / `Pipfile.lock` are in sync with `setup.py`.
* `setup` synchronizes the dependencies defined in `Pipfile` / `Pipfile.lock` with `setup.py`.

Make sure to run `format_check` / `format`, `isort_check` / `isort`, `lint_check` / `lint`, `license`, `setup_check` / `setup` before committing changes to the repository to avoid unnecessary development cycles. `smartmeter-datacollector` uses [GitHub Actions](https://github.com/scs/smartmeter-datacollector/actions) to check if these rules apply.

# Acknowledgements
`smartmeter-datacollector` and its companion project [`smartmeter-datacollector-configurator`](https://github.com/scs/smartmeter-datacollector-configurator) have been developed by **[Supercomputing Systems AG](https://www.scs.ch)** on behalf of and funded by **[EKZ](https://www.ekz.ch/)**.
