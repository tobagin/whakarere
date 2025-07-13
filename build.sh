#!/bin/bash

# Karere Flatpak Build Script
# Usage: ./build.sh [--dev] [--install] [--force-clean]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
PACKAGING_DIR="$PROJECT_ROOT/packaging"

# Default values
DEV_MODE=false
INSTALL_FLAG=""
FORCE_CLEAN_FLAG=""
BUILD_DIR="flatpak-build"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --install)
            INSTALL_FLAG="--install"
            shift
            ;;
        --force-clean)
            FORCE_CLEAN_FLAG="--force-clean"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dev] [--install] [--force-clean]"
            echo "  --dev         Build from local sources (development mode)"
            echo "  --install     Install the built application"
            echo "  --force-clean Force clean build directory"
            exit 1
            ;;
    esac
done

# Determine which manifest to use
if [ "$DEV_MODE" = true ]; then
    MANIFEST="$PACKAGING_DIR/io.github.tobagin.karere-dev.yml"
    echo "🔧 Building Karere in DEVELOPMENT mode (local sources)"
else
    MANIFEST="$PACKAGING_DIR/io.github.tobagin.karere.yml"
    echo "🚀 Building Karere in PRODUCTION mode (git sources)"
fi

# Check if manifest exists
if [ ! -f "$MANIFEST" ]; then
    echo "❌ Error: Manifest file not found: $MANIFEST"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Build command
echo "📦 Building Flatpak..."
echo "   Manifest: $(basename "$MANIFEST")"
echo "   Build directory: $BUILD_DIR"
echo ""

flatpak-builder \
    --user \
    $INSTALL_FLAG \
    $FORCE_CLEAN_FLAG \
    "$BUILD_DIR" \
    "$MANIFEST"

echo ""
if [ "$INSTALL_FLAG" = "--install" ]; then
    echo "✅ Karere built and installed successfully!"
    echo "🎯 Run with: flatpak run io.github.tobagin.karere"
else
    echo "✅ Karere built successfully!"
    echo "💡 Add --install flag to install the application"
fi