#!/usr/bin/env bash
# Canlıya alma: frontend build, konteynerleri yeniden kur. Sadece sahibi onaylayınca çalıştır.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env.prod ] || { echo ".env.prod yok"; exit 1; }
(cd frontend && npm ci && npm run build)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
echo "Tamam: https://mektep.woclex.com"
