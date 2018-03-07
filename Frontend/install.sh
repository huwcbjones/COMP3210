#!/bin/bash
set -o errexit
python3 -m ensurepip
python3 -m pip install pipenv
pipenv --three install
