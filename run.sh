#!/bin/bash
cd "$(dirname "$0")"
echo "Starting NIFTY Swing AI Assistant Web Dashboard..."
./venv/bin/streamlit run app.py --server.port 8501 --server.headless false
