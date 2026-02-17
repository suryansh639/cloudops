#!/bin/bash
# Build CloudOps binary using PyInstaller

set -e

echo "=== CloudOps Binary Build Script ==="
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Create binary
echo "Building binary..."
pyinstaller --onefile \
    --name cloudops \
    --add-data "cloudops:cloudops" \
    --hidden-import anthropic \
    --hidden-import boto3 \
    --hidden-import kubernetes \
    --hidden-import pydantic \
    --hidden-import yaml \
    --hidden-import click \
    --hidden-import rich \
    cloudops-cli

echo ""
echo "=== Build Complete ==="
echo ""
echo "Binary location: dist/cloudops"
echo ""
echo "Test it:"
echo "  ./dist/cloudops --version"
echo "  ./dist/cloudops --help"
echo ""
echo "Install it:"
echo "  sudo cp dist/cloudops /usr/local/bin/"
