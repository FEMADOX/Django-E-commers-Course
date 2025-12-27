#!/bin/bash

echo "Building the project..."

# 1. Install dependencies
# Note: When using a custom buildCommand, Vercel doesn't install requirements.txt automatically, we must do it explicitly.
python3 -m pip install uv
python3 -m uv sync

echo "Dependencies installed."
python3 -m uv pip list

# 2. Collect static files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Build Process Completed!"
