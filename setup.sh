#!/bin/bash
set -e

echo "Starting Omnigent VPS Setup..."

# Ensure python3-venv, docker, and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose could not be found. Please install docker-compose."
    exit 1
fi

echo "Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Requirements..."
pip install -r requirements.txt

echo "Setting up Environment Variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example. PLEASE EDIT .env TO ADD YOUR GEMINI_API_KEY."
fi

echo "Starting Docker Compose Infrastructure (Postgres, RabbitMQ, Redis)..."
docker-compose up -d

echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo "Running Django Migrations..."
cd backend
python manage.py migrate

echo "Setup Complete!"
echo "--------------------------------------------------------"
echo "To start the Celery Worker, run in a new terminal:"
echo "  source venv/bin/activate && cd backend && celery -A og_broker worker -l info"
echo ""
echo "To start the Django ASGI server (for WebSockets), run:"
echo "  source venv/bin/activate && cd backend && daphne -b 0.0.0.0 -p 8000 og_broker.asgi:application"
echo ""
echo "To run the TUI Dashboard, run:"
echo "  source venv/bin/activate && python -m cli.main top"
echo "--------------------------------------------------------"
