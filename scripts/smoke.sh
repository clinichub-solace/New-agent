#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-http://127.0.0.1:${PUBLISHED_BACKEND_PORT:-8080}}"

echo "🩺 Health..."
curl -fsS -i "$HOST/health" | sed -n '1,3p'

echo "🔐 Login (expect 200 or 401, but NOT 500)..."
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$HOST/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"wrong-or-real"}'

echo "🧾 Check for Mongo auth failures in logs..."
docker compose logs backend | grep -i "Authentication failed" && {
  echo "❌ Found Mongo auth failures"
  exit 1
} || echo "✅ No auth failures"