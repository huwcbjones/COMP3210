#!/bin/bash
python3 -m ensurepip
python3 -m pip install pipenv
pipenv --three install

ln -s COMP3210-Backend.service /etc/systemd/system/
systemctl daemon-reload