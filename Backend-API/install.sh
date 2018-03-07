#!/bin/bash
set -o errexit

python3 -m ensurepip
python3 -m pip install pipenv
pipenv --three install

rm -f /etc/systemd/system/COMP3210-Backend.service
ln -s COMP3210-Backend.service /etc/systemd/system/
systemctl daemon-reload