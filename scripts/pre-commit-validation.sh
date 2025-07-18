#!/bin/bash
# Pre-commit hook script for version validation
# This script runs version validation before allowing commits

set -e

echo "Running pre-commit version validation..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Run version consistency test
echo "Checking version consistency..."
python3 scripts/test_version_consistency.py

# Run build validation
echo "Checking build validation..."
python3 scripts/validate_build_version.py

echo "✅ All validation checks passed!"
echo "Commit can proceed."