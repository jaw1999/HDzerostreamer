#!/bin/bash

# Install system dependencies
sudo apt update
sudo apt install -y python3-flask python3-pymavlink python3-psutil

# Install pip packages globally
sudo pip3 install flask psutil pymavlink asyncio

# Create log files if they don't exist
sudo touch /var/log/tbs-control.log /var/log/tbs-control.error.log

# Set correct ownership and permissions
sudo chown user:user /var/log/tbs-control.log /var/log/tbs-control.error.log
sudo chmod 644 /var/log/tbs-control.log /var/log/tbs-control.error.log

# Make scripts executable
chmod +x scripts/install.sh scripts/update.sh

# Install service
sudo cp services/tbs-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tbs-control
sudo systemctl restart tbs-control

echo "Service installed and started. Check status with: sudo systemctl status tbs-control" 