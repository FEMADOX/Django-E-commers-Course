#!/bin/bash
# filepath: /home/fenyxz/CODING/Own Practice/Django-E-commers-Course/docker/start.sh

set -e

echo "🚀 Starting Django application..."

# Apply migrations
echo "📦 Applying migrations..."
uv run manage.py migrate

# Collect static files
echo "🎨 Collecting static files..."
uv run manage.py collectstatic --noinput

# Function to handle shutdown signals
cleanup() {
    echo "🛑 Shutting down processes..."
    kill $LIVERELOAD_PID $RUNSERVER_PID 2>/dev/null || true
    exit 0
}

# Configure trap for shutdown signals
trap cleanup SIGTERM SIGINT

echo "🔄 Starting livereload..."
uv run manage.py livereload &
LIVERELOAD_PID=$!

echo "🌐 Starting Django server..."
uv run manage.py runserver 0.0.0.0:8000 &
RUNSERVER_PID=$!

echo "✅ Services started:"
echo "  - LiveReload PID: $LIVERELOAD_PID"
echo "  - RunServer PID: $RUNSERVER_PID"
echo "  - Server available at: http://localhost:8000"

# Wait for processes to finish
wait