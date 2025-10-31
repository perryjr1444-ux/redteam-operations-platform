#!/usr/bin/env bash
#
# Build frontend islands
#

set -e

echo "Building frontend islands..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Build with Vite
echo "Running Vite build..."
npm run build

echo "✓ Frontend build complete!"
echo "Output: static/dist/islands.js"
