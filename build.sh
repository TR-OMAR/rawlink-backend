#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip to handle modern dependency resolution
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate