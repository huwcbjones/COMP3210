#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]
  then echo "This script requires root"
  exit
fi

useradd -r -U comp3210

cd /opt/
git clone git@github.com:huwcbjones/COMP3210.git

chown -r comp3210:comp3210 COMP3210
cd COMP3210

cd /opt/COMP3210/Backend-API
./install.sh

cd /opt/COMP3210/Frontend
./install.sh

ln -s /opt/COMP3210/COMP3210-Backend.service /etc/systemd/system/
systemctl daemon-reload