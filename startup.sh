#!/bin/bash
# run_all.sh
# Script to run gmail_main.py, sub.py, and then FastAPI server

# Set the port for uvicorn
PORT=8000

# Activate virtual environment if needed
# source /path/to/your/venv/bin/activate

echo "Starting gmail_main.py..."
python3 gmail_main.py &
GMAIL_PID=$!

echo "Starting sub.py..."
python3 sub.py &
SUB_PID=$!

# Wait a little to ensure scripts are running
sleep 2

echo "Starting FastAPI server on port $PORT..."
uvicorn server:app --reload --port $PORT

# Optional: kill background scripts when uvicorn stops
kill $GMAIL_PID $SUB_PID
