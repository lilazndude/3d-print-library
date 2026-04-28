#!/bin/bash
# Deploy / update 3D Print Library on CasaOS.
# Run from anywhere:
#   bash /media/CONFIG/3D_Printing/repo/_app/deploy-casaos.sh
# Or via SSH from your PC:
#   ssh casaos 'bash /media/CONFIG/3D_Printing/repo/_app/deploy-casaos.sh'

set -e

# Always work relative to this script's location
APP_DIR="$(cd "$(dirname "$(realpath "$0")")" && pwd)"
REPO_DIR="$(dirname "$APP_DIR")"

echo ""
echo " 3D Print Library - CasaOS Deploy"
echo " ==================================="
echo " App dir : $APP_DIR"
echo " Repo dir: $REPO_DIR"
echo ""

# ── Sanity check ───────────────────────────────────────────────────────────
if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
    echo " ERROR: docker-compose.yml not found in $APP_DIR"
    exit 1
fi

if [ ! -d "$REPO_DIR/models" ]; then
    echo " WARNING: models/ directory not found at $REPO_DIR"
    echo " It will be created automatically on first import."
    echo ""
fi

# ── Docker permission check ────────────────────────────────────────────────
DOCKER="docker"
if ! docker info &>/dev/null 2>&1; then
    if sudo docker info &>/dev/null 2>&1; then
        DOCKER="sudo docker"
    else
        echo " ERROR: Cannot connect to Docker. Make sure Docker is running."
        exit 1
    fi
fi

# ── Build & start ──────────────────────────────────────────────────────────
cd "$APP_DIR"

# Export repo path so docker-compose.yml uses the correct volume mount
export LIBRARY_HOST_PATH="$REPO_DIR"
echo " Library path: $LIBRARY_HOST_PATH"
echo ""

echo " Building image (--no-cache to pick up dependency changes)..."
$DOCKER compose build --no-cache

echo " Starting container..."
$DOCKER compose up -d

echo ""
echo " ==================================="
echo "  Done! Access the library at:"
HOSTNAME_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -n "$HOSTNAME_IP" ] && echo "   http://${HOSTNAME_IP}:5000"
echo "   http://$(hostname).local:5000"
echo " ==================================="
echo ""
