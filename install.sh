#!/bin/bash
set -e

echo "Installing Claude Code memorydecay plugin..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install package
echo "Installing package..."
pip install -e .

# Create directories
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/hooks
mkdir -p ~/.memorydecay

# Copy skills
echo "Installing skills..."
cp -r .claude/skills/memorydecay ~/.claude/skills/

# Copy hooks
echo "Installing hooks..."
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact
chmod +x ~/.claude/hooks/session-end

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set MEMORYDECAY_CORE_PATH environment variable to your memory-decay-core directory"
echo "2. Run 'memorydecay server start' to verify installation"
echo "3. Run 'memorydecay migrate --from ~/.claude/memory' to import existing memories"
