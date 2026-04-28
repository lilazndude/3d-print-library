#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$(realpath "$0")")"

echo ""
echo " 3D Print Library - First-Time Setup"
echo " ====================================="
echo ""

# ── Check Python 3 ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo " ERROR: Python 3 not found."
    echo ""
    echo " Install it with your package manager, e.g.:"
    echo "   sudo apt install python3 python3-venv   (Debian/Ubuntu)"
    echo "   sudo dnf install python3                (Fedora)"
    echo "   sudo pacman -S python                   (Arch)"
    echo ""
    exit 1
fi

PYVER=$(python3 --version 2>&1 | awk '{print $2}')
echo " Found Python $PYVER"
echo ""

# ── System dependencies ────────────────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    echo " Checking system libraries..."
    sudo apt-get install -y --no-install-recommends \
        python3-venv libglib2.0-0 2>/dev/null \
        && echo " System libraries OK." \
        || echo " Could not install system libraries — continuing anyway."
    echo ""
fi

# ── Virtual environment (venv_linux to avoid conflict with Windows venv) ───
if [ -f "_app/venv_linux/bin/python" ]; then
    echo " Virtual environment already exists. Re-installing dependencies..."
else
    echo " Creating virtual environment..."
    python3 -m venv _app/venv_linux || {
        echo ""
        echo " ERROR: Could not create virtual environment."
        echo " Try: sudo apt install python3-venv python3-full"
        exit 1
    }
fi
echo ""

# ── Python dependencies ────────────────────────────────────────────────────
echo " Installing dependencies - this may take a few minutes..."
echo " (Flask, Trimesh, NumPy, Matplotlib, SciPy, NetworkX)"
echo ""
_app/venv_linux/bin/pip install --upgrade pip -q
_app/venv_linux/bin/pip install -r _app/requirements.txt || {
    echo ""
    echo " ERROR: Dependency installation failed."
    echo " Check your internet connection and try again."
    exit 1
}

[ -f run.sh ] && chmod +x run.sh

echo ""
echo " ====================================="
echo "  Setup complete!"
echo "  Run './run.sh' to launch."
echo " ====================================="
echo ""
