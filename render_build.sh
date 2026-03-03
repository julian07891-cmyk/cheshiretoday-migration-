#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing backend Python deps"
python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt

echo "==> Building frontend"
cd frontend
npm ci
npm run build
cd ..

echo "==> Copying frontend build into backend/frontend_build"
rm -rf backend/frontend_build
mkdir -p backend/frontend_build
cp -R frontend/build/. backend/frontend_build/

echo "==> Done"
