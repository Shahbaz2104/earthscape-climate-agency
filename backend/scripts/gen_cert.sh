#!/bin/bash
# Generate a self-signed TLS certificate for HTTPS deployment.
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$DIR/data/certs"
mkdir -p "$CERT_DIR"
openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" \
  -days 365 -nodes -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" 2>/dev/null
echo "Certificate created at $CERT_DIR"
echo
echo "Run the API over HTTPS:"
echo "  cd backend && .venv/bin/uvicorn app.main:app --port 8443 \\"
echo "    --ssl-keyfile $CERT_DIR/key.pem --ssl-certfile $CERT_DIR/cert.pem"
echo
echo "Point the frontend at it: VITE_API_URL=https://localhost:8443 npm run dev"