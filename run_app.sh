#!/bin/bash
# Script to run the GenerateCarouselGcode application
# This activates the virtual environment and runs the Python script

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$DIR"

# Activate the virtual environment
source venv/bin/activate

# Run the Python application
python GenerateCarouselGcode.py

# Deactivate the virtual environment when done
deactivate
