# Claude Code memorydecay

Human-like memory decay for Claude Code. Important things stick, noise fades.

## Features

- **Decay-aware search**: Retrieve memories ranked by relevance and freshness
- **Automatic lifecycle**: Server starts/stops automatically
- **Shared database**: Works alongside OpenClaw plugin using same memory store
- **Migration tool**: Import existing Claude Code memories
- **Hook integration**: Automatic decay on context compaction and session end

## Installation

### Prerequisites

- Python 3.10+
- [memory-decay-core](https://github.com/memory-decay/memory-decay-core) cloned locally

### Install

```bash
# Clone this repository
git clone <repo-url>
cd claude-code-memorydecay

# Install in editable mode
pip install -e .

# Or install dependencies only
pip install click requests
```

### Configure Claude Code

1. Copy/link skills to your Claude Code directory:
```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/memorydecay ~/.claude/skills/
```

2. Copy hooks:
```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/pre-compact ~/.claude/hooks/
cp .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/*
```

3. Set environment variables (optional):
```bash
export MEMORYDECAY_CORE_PATH=/path/to/memory-decay-core
export MEMORYDECAY_DB_PATH=~/.memorydecay/memories.db
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

### Search memories
```bash
memorydecay search "API design decisions"
```

### Store a memory
```bash
memorydecay store "User prefers dark mode" --importance 0.8 --category preference
```

### Check status
```bash
memorydecay server status
```

### Migrate existing memories
```bash
memorydecay migrate --from ~/.claude/memory
```

## How It Works

1. **SKILL.md** instructs the agent to use `memorydecay` commands
2. **CLI** wraps HTTP calls to memory-decay-core server
3. **Server Manager** handles PID file and lifecycle
4. **Hooks** trigger automatic decay at key moments
5. **Shared database** with OpenClaw ensures consistency

## Architecture

```
Claude Code Agent
    ↓ (reads SKILL.md)
    ↓ (runs commands)
memorydecay CLI
    ↓ (HTTP)
memory-decay-core (shared with OpenClaw)
    ↓
SQLite + Vector DB (~/.memorydecay/memories.db)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src tests
ruff check src tests
```

## License

MIT
