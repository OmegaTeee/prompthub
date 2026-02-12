#!/bin/bash
# cleanup-temp-files.sh

echo "🧹 Cleaning up temporary and cache files..."

# Python cache
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# macOS metadata
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null

# Temporary logs
echo "Removing temporary logs..."
rm -f /tmp/agenthub-router.log

# Node module logs
echo "Removing node module setup logs..."
find mcps/node_modules -name "setup.log" -delete 2>/dev/null

echo "✅ Cleanup complete!"
echo ""
echo "Space saved:"
du -sh ~/.Trash/ 2>/dev/null | tail -1