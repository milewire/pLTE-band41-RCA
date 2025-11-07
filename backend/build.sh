#!/bin/bash
set -e

echo "=== Railway Build Script ==="
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la)"
echo "Parent directory contents: $(ls -la .. 2>/dev/null || echo 'Cannot access parent')"

# Copy engine and ai directories
# If running from repo root, copy from current directory
# If running from backend/, copy from parent directory
if [ -d "engine" ] && [ -d "ai" ]; then
  echo "✓ Engine and AI directories already in current directory"
elif [ -d "../engine" ] && [ -d "../ai" ]; then
  echo "✓ Found ../engine, copying..."
  cp -r ../engine .
  echo "✓ Engine copied successfully"
else
  echo "✗ ../engine not found"
  # Try alternative paths
  if [ -d "../../engine" ]; then
    echo "✓ Found ../../engine, copying..."
    cp -r ../../engine .
    echo "✓ Engine copied successfully"
  else
    echo "✗ ../../engine not found either"
    exit 1
  fi
fi

if [ -d "../ai" ]; then
  echo "✓ Found ../ai, copying..."
  cp -r ../ai .
  echo "✓ AI copied successfully"
else
  echo "✗ ../ai not found"
  # Try alternative paths
  if [ -d "../../ai" ]; then
    echo "✓ Found ../../ai, copying..."
    cp -r ../../ai .
    echo "✓ AI copied successfully"
  else
    echo "✗ ../../ai not found either"
    exit 1
  fi
fi

# Verify copies
if [ ! -d "engine" ] || [ ! -d "ai" ]; then
  echo "✗ ERROR: Failed to copy engine or ai directories"
  exit 1
fi

echo "✓ Verified: engine and ai directories exist"
echo "Engine contents: $(ls engine/ || echo 'empty')"
echo "AI contents: $(ls ai/ || echo 'empty')"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "=== Build completed successfully! ==="

