#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip and setuptools to avoid dependency issues
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Run Django commands
python manage.py collectstatic --no-input
python manage.py migrate