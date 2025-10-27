#!/bin/bash
# Script to run CircumferenceClean application
# This activates the virtual environment and runs the Python script

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$DIR"

echo "Starting CircumferenceClean..."
echo "Note: First run may be slow due to iCloud sync. Please wait..."

# Activate the virtual environment
source venv/bin/activate

# Run the Python application
python CircumferenceClean.py

# Deactivate the virtual environment when done
deactivate

