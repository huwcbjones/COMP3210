#!/usr/bin/env bash

set -o errexit

if [ "$EUID" -ne 0 ]
  then echo "This script requires root"
  exit
fi

if id comp3210 >/dev/null 2>&1; then
    echo "Not creating user as it already exists"
else
    echo "Creating user comp3210"
    useradd -r -U comp3210
fi

echo "Cloning repo..."
cd /opt/
git clone git@github.com:huwcbjones/COMP3210.git

echo "Setting permissions"
chown -R comp3210:comp3210 COMP3210
cd COMP3210

echo "Installing backend API"
cd /opt/COMP3210/Backend-API
. ./install.sh

echo "Installing frontend"
cd /opt/COMP3210/Frontend
. ./install.sh
