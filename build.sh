#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip to handle dependency resolution better
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate