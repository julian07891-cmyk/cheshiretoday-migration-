#!/usr/bin/env bash
set -euo pipefail

echo "==> Building frontend"
cd frontend
npm ci
npm run build
cd ..

echo "==> Copying frontend build into backend/frontend_build"
mkdir -p backend/frontend_build
rsync -a --delete frontend/build/ backend/frontend_build/

echo "==> Done"
