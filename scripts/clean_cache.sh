#!/bin/bash

# Clean Python cache script
echo "🧹 Cleaning Python cache files..."

# Remove __pycache__ directories
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
echo "Removing .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove .pyo files (if any)
echo "Removing .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null || true

echo "✅ Python cache cleanup complete!" 
