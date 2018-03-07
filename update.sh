#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]
  then echo "This script requires root"
  exit
fi

cd /opt/COMP3210/Backend-API
./update.sh

cd /opt/COMP3210/Frontend
./update.sh

systemctl restart