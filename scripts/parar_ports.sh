#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/lib/demo-config.sh"

stop_demo_ports

echo "Port-forwards detenidos."
