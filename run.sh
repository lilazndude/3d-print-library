#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$(realpath "$0")")"

if [ ! -f "_app/venv_linux/bin/python" ]; then
    echo ""
    echo " Virtual environment not found."
    echo " Please run './install.sh' first."
    echo ""
    exit 1
fi

echo ""
echo " Starting 3D Print Library..."
echo " Opening http://localhost:5000"
echo ""
echo " Press Ctrl+C to stop."
echo ""

_app/venv_linux/bin/python _app/app.py
