#!/bin/bash
set -e

echo "Installing Claude Code memorydecay plugin..."
echo ""

# Check for uv
if command -v uv &> /dev/null; then
    echo "✓ uv found, using uv for installation"
    INSTALLER="uv pip"
else
    echo "⚠ uv not found, falling back to pip"
    echo "  Consider installing uv: https://github.com/astral-sh/uv"
    INSTALLER="pip"
fi

# Check Python version
python_version=$($INSTALLER --version 2>&1 | head -1)
echo "Installer: $python_version"
echo ""

# Install package
echo "Installing package..."
$INSTALLER install -e .

# Create directories
echo ""
echo "Creating directories..."
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/hooks
mkdir -p ~/.memorydecay

# Copy skills
echo "Installing Claude Code skill..."
cp -r .claude/skills/memorydecay ~/.claude/skills/

# Copy hooks
echo "Installing hooks..."
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact
chmod +x ~/.claude/hooks/session-end

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Set MEMORYDECAY_CORE_PATH environment variable:"
echo "   export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core"
echo "   (Add this to your ~/.bashrc or ~/.zshrc)"
echo ""
echo "2. Verify installation:"
echo "   memorydecay --version"
echo ""
echo "3. (Optional) Migrate existing memories:"
echo "   memorydecay migrate --from ~/.claude/memory"
echo ""
echo "The skill will be automatically loaded by Claude Code."
