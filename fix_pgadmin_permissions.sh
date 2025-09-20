#!/bin/bash
# File: fix_pgadmin_permissions.sh

# Ask for your password
read -s -p "Enter your password for sudo: " SUDO_PASS
echo

# Folder path
PGADMIN_PATH="./pgadmin"

# Create folder if it doesn't exist
mkdir -p "$PGADMIN_PATH"

# Change ownership to 5050:5050 for PGAdmin container
echo "$SUDO_PASS" | sudo -S chown -R 5050:5050 "$PGADMIN_PATH"

echo "Permissions fixed for $PGADMIN_PATH"
