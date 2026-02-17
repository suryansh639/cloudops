#!/bin/bash
# Quick test script for CloudOps MVP

set -e

echo "=== CloudOps MVP Test ==="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "2. Installing dependencies..."
cd /home/suryanshg.jiit/cloudops
pip install -q -r requirements.txt

# Test CLI help
echo ""
echo "3. Testing CLI help..."
python -m cloudops --help

# Test init command (dry run)
echo ""
echo "4. Testing init command..."
python -m cloudops --version

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Set your API key: export ANTHROPIC_API_KEY='your-key'"
echo "2. Initialize config: python -m cloudops init"
echo "3. Run investigation: python -m cloudops investigate 'high cpu on prod cluster'"
echo ""
echo "See EXAMPLES.md for more usage examples."
