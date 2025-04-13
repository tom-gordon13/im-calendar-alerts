#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists, create it if it doesn't
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $SCRIPT_DIR/venv
fi

# Activate virtual environment
source $SCRIPT_DIR/venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install requests PyPDF2 python-dotenv pandas tabula-py

# Run the Python script
python3 $SCRIPT_DIR/main.py

# Deactivate virtual environment
deactivate

# Log the execution time
echo "Script executed at $(date)" >> $SCRIPT_DIR/execution_log.txt
