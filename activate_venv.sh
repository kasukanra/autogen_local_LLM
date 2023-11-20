#!/bin/bash
# activate_venv.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment 'venv' activated."
else
    echo "Virtual environment 'venv' does not exist."
fi