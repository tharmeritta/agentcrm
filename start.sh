#!/bin/bash

# Make sure we're in the right directory
cd /app

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}