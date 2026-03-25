#!/bin/bash
# Validation script for claude-code-memorydecay plugin

set -e

echo "========================================="
echo "Claude Code memorydecay Plugin Validator"
echo "========================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "1. Python Package Structure"
echo "---------------------------"

# Check Python package
if [ -f "src/claude_code_memorydecay/__init__.py" ]; then
    check_pass "Package __init__.py exists"
else
    check_fail "Package __init__.py missing"
fi

if [ -f "src/claude_code_memorydecay/cli.py" ]; then
    check_pass "CLI module exists"
else
    check_fail "CLI module missing"
fi

if [ -f "src/claude_code_memorydecay/client.py" ]; then
    check_pass "Client module exists"
else
    check_fail "Client module missing"
fi

if [ -f "src/claude_code_memorydecay/server_manager.py" ]; then
    check_pass "Server manager exists"
else
    check_fail "Server manager missing"
fi

if [ -f "src/claude_code_memorydecay/migrator.py" ]; then
    check_pass "Migrator module exists"
else
    check_fail "Migrator module missing"
fi

echo ""
echo "2. CLI Installation"
echo "-------------------"

# Check if CLI is available
if command -v memorydecay &> /dev/null; then
    check_pass "memorydecay CLI is in PATH"
    VERSION=$(memorydecay --version 2>&1 || echo "unknown")
    echo "  Version: $VERSION"
else
    check_fail "memorydecay CLI not found in PATH"
    echo "  Run: pip install -e ."
fi

# Check CLI commands
if memorydecay --help &> /dev/null; then
    check_pass "CLI help works"
else
    check_fail "CLI help failed"
fi

echo ""
echo "3. SKILL.md"
echo "-----------"

if [ -f ".claude/skills/memorydecay/SKILL.md" ]; then
    check_pass "SKILL.md exists"
    
    # Check required sections
    if grep -q "memorydecay search" .claude/skills/memorydecay/SKILL.md; then
        check_pass "SKILL.md documents search command"
    else
        check_warn "SKILL.md missing search documentation"
    fi
    
    if grep -q "memorydecay store" .claude/skills/memorydecay/SKILL.md; then
        check_pass "SKILL.md documents store command"
    else
        check_warn "SKILL.md missing store documentation"
    fi
    
    if grep -q "FRESH\|STALE\|NORMAL" .claude/skills/memorydecay/SKILL.md; then
        check_pass "SKILL.md documents freshness indicators"
    else
        check_warn "SKILL.md missing freshness documentation"
    fi
else
    check_fail "SKILL.md missing at .claude/skills/memorydecay/SKILL.md"
fi

echo ""
echo "4. Hooks"
echo "--------"

if [ -f ".claude/hooks/pre-compact" ]; then
    check_pass "pre-compact hook exists"
    if [ -x ".claude/hooks/pre-compact" ]; then
        check_pass "pre-compact hook is executable"
    else
        check_warn "pre-compact hook is not executable"
    fi
else
    check_fail "pre-compact hook missing"
fi

if [ -f ".claude/hooks/session-end" ]; then
    check_pass "session-end hook exists"
    if [ -x ".claude/hooks/session-end" ]; then
        check_pass "session-end hook is executable"
    else
        check_warn "session-end hook is not executable"
    fi
else
    check_fail "session-end hook missing"
fi

echo ""
echo "5. Tests"
echo "--------"

if [ -d "tests" ]; then
    check_pass "Tests directory exists"
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    echo "  Found $TEST_COUNT test files"
    
    # Run tests
    if python3 -m pytest tests/ -v --tb=short &> /tmp/test_output.txt; then
        check_pass "All tests pass"
        PASSED=$(grep -oP '\d+(?= passed)' /tmp/test_output.txt | tail -1 || echo "?")
        echo "  Tests passed: $PASSED"
    else
        check_fail "Some tests failed"
        echo "  See /tmp/test_output.txt for details"
    fi
else
    check_fail "Tests directory missing"
fi

echo ""
echo "6. Dependencies"
echo "---------------"

python3 -c "import click" 2>/dev/null && check_pass "click installed" || check_fail "click not installed"
python3 -c "import requests" 2>/dev/null && check_pass "requests installed" || check_fail "requests not installed"

echo ""
echo "7. Documentation"
echo "----------------"

if [ -f "README.md" ]; then
    check_pass "README.md exists"
else
    check_fail "README.md missing"
fi

if [ -f "install.sh" ]; then
    check_pass "install.sh exists"
    if [ -x "install.sh" ]; then
        check_pass "install.sh is executable"
    else
        check_warn "install.sh is not executable"
    fi
else
    check_fail "install.sh missing"
fi

echo ""
echo "8. Configuration Files"
echo "----------------------"

if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
else
    check_fail "pyproject.toml missing"
fi

echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Plugin is valid and ready to use!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Plugin has errors that need to be fixed.${NC}"
    exit 1
fi
