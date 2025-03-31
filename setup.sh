#!/bin/bash

# Increase inotify watch limit
echo "Configuring system settings..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo privileges"
    exit 1
fi

# Increase inotify watch limit
echo "Increasing inotify watch limit..."
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Make sure the script is executable
chmod +x setup.sh

echo "Setup completed successfully!"
