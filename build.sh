#!/usr/bin/env bash
set -o errexit
set -o pipefail

# use explicit python3 binary (Render images commonly expose python3)
python3 -m pip install --upgrade pip setuptools wheel

# install deps (now pip is modern and will pick compatible wheels)
python3 -m pip install -r requirements.txt

# django steps
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
