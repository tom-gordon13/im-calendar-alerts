#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if you're using one (uncomment if needed)
source $SCRIPT_DIR/venv/bin/activate

# Run the Python script
python3 $SCRIPT_DIR/main.py

# Deactivate virtual environment if you activated it (uncomment if needed)
deactivate

# Log the execution time
echo "Script executed at $(date)" >> $SCRIPT_DIR/execution_log.txt
