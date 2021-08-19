#!/usr/bin/env bash

# exit on any error
set -e

# re-use build_srcdeb.sh
pipenv run build_srcdeb full
