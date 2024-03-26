#!/bin/bash

# Set up virtual environment
python3.9 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install pip (optional, venv already includes pip)
# python3.9 -m ensurepip

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput


