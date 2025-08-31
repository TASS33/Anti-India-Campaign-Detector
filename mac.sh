#!/bin/bash

echo "==================================================="
echo " Starting Full Project Setup (Backend & Frontend)"
echo "==================================================="
echo ""

# --- Step 1: Install Python Dependencies ---
echo "[1/2] Installing Python backend dependencies..."
echo "--------------------------------------------"
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Please install it to continue."
    exit 1
fi
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python packages. See errors above."
    exit 1
fi
echo "Python dependencies installed successfully."
echo ""


# --- Step 2: Install Node.js Dependencies ---
echo "[2/2] Installing Node.js frontend dependencies..."
echo "--------------------------------------------"
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed. Please install it to continue."
    exit 1
fi

# Assumes the frontend code is in a 'frontend' directory
# next to your 'backend' directory.
if [ ! -f "./webserver/frontend/package.json" ]; then
    echo "ERROR: Could not find 'package.json' in the './webserver/frontend' directory."
    echo "Please ensure your React app is located there."
    exit 1
fi
cd ./webserver/frontend
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Node.js packages. See errors above."
    cd ../..
    exit 1
fi
cd ../..
echo "Node.js dependencies installed successfully."
echo ""

echo "==================================================="
echo "  Project setup completed successfully!"
echo "==================================================="
echo ""
