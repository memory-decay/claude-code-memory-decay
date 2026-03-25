# Claude Code memorydecay

Human-like memory decay for Claude Code. Important things stick, noise fades.

## Features

- **Decay-aware search**: Retrieve memories ranked by relevance and freshness
- **Automatic lifecycle**: Server starts/stops automatically
- **Shared database**: Works alongside OpenClaw plugin using same memory store
- **Migration tool**: Import existing Claude Code memories
- **Hook integration**: Automatic decay on context compaction and session end

## Quick Start

```bash
# 1. Clone
git clone https://github.com/memory-decay/claude-code-memory-decay.git
cd claude-code-memory-decay

# 2. Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

# 3. Install Claude Code skill
mkdir -p ~/.claude/skills
cp -r .claude/skills/memorydecay ~/.claude/skills/

# 4. Install hooks
mkdir -p ~/.claude/hooks
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/*

# 5. Set environment variable (required)
export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core

# 6. Verify installation
memorydecay --version
```

### Prerequisites

- [uv](https://github.com/astral-sh/uv) or Python 3.10+ with pip
- [memory-decay-core](https://github.com/memory-decay/memory-decay-core) cloned locally
- Claude Code CLI installed

## Claude Code Skill Setup

The plugin provides a skill that teaches Claude Code how to use the memory system.

### Manual Skill Installation

```bash
# Copy skill to Claude Code directory
mkdir -p ~/.claude/skills
cp -r .claude/skills/memorydecay ~/.claude/skills/
```

The skill file (`.claude/skills/memorydecay/SKILL.md`) instructs Claude Code to:
- Search memories before answering (`memorydecay search`)
- Store important facts proactively (`memorydecay store`)
- Understand freshness indicators (FRESH/NORMAL/STALE)

### Hook Installation

Hooks enable automatic memory decay at key moments:

```bash
# Copy hooks
mkdir -p ~/.claude/hooks
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/*
```

| Hook | When It Runs | What It Does |
|------|--------------|--------------|
| `pre-compact` | Before context compaction | Applies time-based decay |
| `session-end` | On session end | Applies final decay |

## Configuration

### Environment Variables

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# Required: Path to memory-decay-core repository
export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core

# Optional: Database location (default: ~/.memorydecay/memories.db)
export MEMORYDECAY_DB_PATH=~/.memorydecay/memories.db

# Optional: Server port (default: 8100)
export MEMORYDECAY_PORT=8100
```

### Shared Database with OpenClaw

To share the same database with OpenClaw:

1. Update your OpenClaw config (`~/.openclaw/openclaw.json`):
```json
{
  "plugins": {
    "entries": {
      "memory-decay": {
        "enabled": true,
        "config": {
          "dbPath": "~/.memorydecay/memories.db",
          "serverPort": 8100
        }
      }
    }
  }
}
```

2. Both plugins now use the same database at `~/.memorydecay/memories.db`

## Usage

Once installed, Claude Code will automatically read the SKILL.md and use memory commands.

### Manual Commands

You can also run commands directly:

```bash
# Search memories
memorydecay search "API design decisions"

# Store a memory
memorydecay store "User prefers dark mode" --importance 0.8 --category preference

# Check server status
memorydecay server status

# Migrate existing memories from files
memorydecay migrate --from ~/.claude/memory

# Apply time-based decay manually
memorydecay tick
```

### Agent Memory Workflow

1. **At session start**: Agent reads SKILL.md (automatic)
2. **During conversation**: Agent stores important facts via `memorydecay store`
3. **Before compaction**: Hook applies decay automatically
4. **On recall**: Agent searches via `memorydecay search` and sees freshness

## How It Works

```
Claude Code Agent
    ↓ reads SKILL.md (auto-loaded each session)
    ↓ runs memorydecay commands
memorydecay CLI (Python/Click)
    ↓ HTTP API
memory-decay-core (FastAPI server)
    ↓
SQLite + Vector DB (~/.memorydecay/memories.db)
```

## Development

```bash
# Install dev dependencies with uv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src tests
ruff check src tests

# Validate plugin
claude plugin validate .
```

## Project Structure

```
claude-code-memory-decay/
├── .claude/
│   ├── hooks/              # Claude Code hooks
│   │   ├── pre-compact
│   │   └── session-end
│   └── skills/
│       └── memorydecay/
│           └── SKILL.md    # Agent instructions
├── src/
│   └── claude_code_memorydecay/
│       ├── cli.py          # CLI commands
│       ├── client.py       # HTTP client
│       ├── server_manager.py
│       └── migrator.py
└── tests/
```

## License

MIT
