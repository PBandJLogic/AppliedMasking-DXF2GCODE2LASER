#!/bin/bash
# Run adjust_and_run_gcode.py with venv activated

cd "$(dirname "$0")"
source venv/bin/activate
python adjust_and_run_gcode.py

