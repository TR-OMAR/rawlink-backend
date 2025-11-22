#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip, setuptools, and wheel to the latest versions
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate