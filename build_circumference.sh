#!/bin/bash

# Build script for CircumferenceClean standalone executable
# This script builds a standalone version using PyInstaller

echo "Building CircumferenceClean standalone executable..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if PyInstaller is installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -f CircumferenceClean.spec.bak

# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller CircumferenceClean.spec

# Check if build was successful
if [ -f "dist/CircumferenceClean" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Executable created: dist/CircumferenceClean"
    echo ""
    echo "To run the standalone version:"
    echo "  ./dist/CircumferenceClean"
    echo ""
    echo "To distribute:"
    echo "  Copy the entire 'dist' folder to the target machine"
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the output above for errors."
    exit 1
fi
