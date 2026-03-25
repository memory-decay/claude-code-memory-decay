#!/bin/bash
# Install script for claude-code-memorydecay plugin
# This is called by `claude plugin install` after the repo is cloned

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Claude Code memorydecay plugin..."
echo ""

# Check for uv
if command -v uv &> /dev/null; then
    echo "✓ uv found, using uv for installation"
    INSTALL_CMD="uv pip install"
else
    echo "⚠ uv not found, falling back to pip"
    echo "  Consider installing uv: https://github.com/astral-sh/uv"
    INSTALL_CMD="pip install"
fi

# Install Python package
echo ""
echo "Installing Python package..."
cd "$SCRIPT_DIR"
$INSTALL_CMD -e .

# Create directories
echo ""
echo "Setting up Claude Code directories..."
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/hooks
mkdir -p ~/.memorydecay

# Copy skill
echo "Installing skill..."
if [ -d "$SCRIPT_DIR/.claude/skills/memorydecay" ]; then
    cp -r "$SCRIPT_DIR/.claude/skills/memorydecay" ~/.claude/skills/
    echo "  ✓ Skill installed to ~/.claude/skills/memorydecay/"
else
    echo "  ✗ Skill directory not found"
    exit 1
fi

# Copy hooks
echo "Installing hooks..."
if [ -f "$SCRIPT_DIR/.claude/hooks/pre-compact" ]; then
    cp "$SCRIPT_DIR/.claude/hooks/pre-compact" ~/.claude/hooks/
    chmod +x ~/.claude/hooks/pre-compact
    echo "  ✓ pre-compact hook installed"
else
    echo "  ✗ pre-compact hook not found"
fi

if [ -f "$SCRIPT_DIR/.claude/hooks/session-end" ]; then
    cp "$SCRIPT_DIR/.claude/hooks/session-end" ~/.claude/hooks/
    chmod +x ~/.claude/hooks/session-end
    echo "  ✓ session-end hook installed"
else
    echo "  ✗ session-end hook not found"
fi

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "Required: Set MEMORYDECAY_CORE_PATH"
echo ""
echo "  export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core"
echo ""
echo "Add this to your ~/.bashrc or ~/.zshrc to make it permanent."
echo ""
echo "Verify installation:"
echo "  memorydecay --version"
echo ""
