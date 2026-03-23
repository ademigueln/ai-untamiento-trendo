#!/bin/zsh

NAMESPACE="trendo-demo"
TMP_FILE="/tmp/eicar.txt"

pkill -f "port-forward -n $NAMESPACE service/backend-service" 2>/dev/null || true
sleep 1

nohup kubectl port-forward -n "$NAMESPACE" service/backend-service 9000:8007 >/tmp/trendo-backend-portforward.log 2>&1 &
sleep 2

cat > "$TMP_FILE" <<'EOF'
X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
EOF

echo "Probando File Security..."
curl -s -X POST "http://127.0.0.1:9000/api/files/upload" \
  -F "file=@${TMP_FILE}"

echo ""
echo ""
echo "Logs backend:"
kubectl logs deployment/backend -n "$NAMESPACE" --tail=120
