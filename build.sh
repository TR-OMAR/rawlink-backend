#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Upgrade pip
pip install --upgrade pip setuptools wheel

# 2. Install dependencies
pip install -r requirements.txt

# 3. Force creation of migrations for 'api' app if missing
# This fixes the "Dependency on app with no migrations" error
python manage.py makemigrations api
python manage.py makemigrations

# 4. Collect static files
python manage.py collectstatic --no-input

# 5. Run migrations
python manage.py migrate