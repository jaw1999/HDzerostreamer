#!/bin/bash

# Pull latest changes
git pull

# Install/update dependencies
pip3 install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart tbs-control

echo "Update complete!" 