#!/bin/zsh

pkill -f "port-forward -n trendo-demo service/backend-service" 2>/dev/null || true
pkill -f "port-forward -n trendo-demo service/frontend-service" 2>/dev/null || true

echo "Port-forwards detenidos."
