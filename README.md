# Claude Code memorydecay

Human-like memory decay for Claude Code. Important things stick, noise fades.

Built on [memory-decay-core](https://github.com/memory-decay/memory-decay-core) — a mathematical memory model where activation decays over time, stability grows through recall, and retrieval consolidation reinforces what you actually use.

## Why

AI agents forget everything between sessions. The usual fix: dump everything into files and load it all back.

That works. Until it doesn't.

- 50 lines of memory → great. 500 lines → context pollution. 5000 lines → the agent stops attending to what matters.
- Everything is stored equally. A one-off joke about coffee has the same weight as your API architecture decisions.
- Retrieval is binary: either it's in the file or it isn't. No notion of "I think I remember this, but I'm not sure."

`memorydecay` solves this with **decay**:

- Memories have an activation score that decreases over time — like human forgetting
- Important memories decay slower; trivial ones fade fast
- When your agent recalls a memory, it gets reinforced — the testing effect
- Search results come with freshness indicators: `fresh`, `normal`, `stale`
- The result: your agent naturally retains what matters and loses what doesn't

## Install

### Guided Setup (Recommended)

If you have the repo cloned and Claude Code open, just ask:

```
setup memorydecay
```

Claude Code will use the built-in setup skill to walk you through the full installation — cloning dependencies, installing the CLI, copying skills and hooks, and setting environment variables.

### As a Claude Code Plugin

```bash
/plugin marketplace add memory-decay/claude-code-memory-decay
/plugin install memorydecay@claude-code-memory-decay
```

Then install the backend engine:

```bash
pip install memory-decay
```

The plugin automatically installs:
- Skills at `~/.claude/skills/memorydecay/SKILL.md`
- Hooks at `~/.claude/hooks/pre-compact` and `~/.claude/hooks/session-end`
- CLI command `memorydecay`

### Manual Installation (uv)

```bash
# 1. Clone this repo
git clone https://github.com/memory-decay/claude-code-memory-decay.git
cd claude-code-memory-decay

# 2. Install the backend engine
pip install memory-decay

# 3. Install the CLI
uv tool install --from . claude-code-memorydecay

# 4. Install skill and hooks
mkdir -p ~/.claude/skills ~/.claude/hooks ~/.memorydecay
cp -r .claude/skills/memorydecay ~/.claude/skills/
cp .claude/hooks/pre-compact .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact ~/.claude/hooks/session-end

# 5. Start the server and verify connection
memorydecay server start
memorydecay server status        # shows PID and current tick
curl -s http://127.0.0.1:8100/health  # direct health check
```

### Prerequisites

- [uv](https://github.com/astral-sh/uv) or Python 3.10+
- `memory-decay` Python package (`pip install memory-decay`)
- Claude Code CLI

## Configuration

The backend server (`memory-decay`) is installed via `pip install memory-decay`. The CLI auto-detects the installation path using `pip show memory-decay`.

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORYDECAY_PORT` | `8100` | Server port — health endpoint at `http://127.0.0.1:{port}/health` |
| `MEMORYDECAY_DB_PATH` | `~/.memorydecay/memories.db` | SQLite database location |
| `MEMORYDECAY_PYTHON` | `python3` | Python executable for running the server |

The backend server runs locally on `127.0.0.1:8100` by default. The CLI auto-starts the server on first use.

### Embedding Configuration

The default embedding provider is `local` (sentence-transformers), which requires no API key. To use cloud embedding providers instead:

```bash
# Choose a provider
export MD_EMBEDDING_PROVIDER=openai   # or: gemini, local

# Set API key (pick one — generic or provider-specific)
export MD_EMBEDDING_API_KEY=sk-...     # works with any provider
# OR
export OPENAI_API_KEY=sk-...          # auto-detected when provider=openai
export GEMINI_API_KEY=...             # auto-detected when provider=gemini

# Optional: override model or dimension
export MD_EMBEDDING_MODEL=text-embedding-3-small
export MD_EMBEDDING_DIM=1536
```

**Fallback order for API keys:** `MD_EMBEDDING_API_KEY` > provider-specific env var (`OPENAI_API_KEY` / `GEMINI_API_KEY`)

| Provider | Env var | No extra setup needed |
|----------|---------|----------------------|
| `local` | — | ✅ Uses sentence-transformers (pip install local extra) |
| `openai` | `OPENAI_API_KEY` | Requires OpenAI API access |
| `gemini` | `GEMINI_API_KEY` | Requires Google AI API access |

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

## How It Works

```
Claude Code Agent
    ↓ reads SKILL.md (auto-loaded each session)
    ↓ runs memorydecay commands
memorydecay CLI (Python/Click)
    ↓ HTTP API
memory-decay-core (FastAPI server, shared with OpenClaw)
    ↓
SQLite + Vector DB (~/.memorydecay/memories.db)
```

## Features

- **Decay-aware search**: Retrieve memories ranked by relevance and freshness
- **Automatic lifecycle**: Server starts/stops automatically via PID tracking
- **Shared database**: Works alongside OpenClaw plugin using same memory store
- **Migration tool**: Import existing Claude Code memories
- **Hook integration**: Automatic decay on context compaction and session end
- **Freshness indicators**: `fresh` / `normal` / `stale`

## CLI Commands

```bash
# Search memories
memorydecay search "API design decisions"

# Store with correct category and importance
memorydecay store "User prefers dark mode" --importance 0.9 --category preference
memorydecay store "Chose REST over GraphQL due to team familiarity" --importance 0.8 --category decision
memorydecay store "Auth service returns 401 on expired refresh tokens" --importance 0.8 --category fact
memorydecay store "Finished implementing login flow" --importance 0.5 --category episode

# Check server status
memorydecay server status

# Migrate existing memories from files
memorydecay migrate --from ~/.claude/memory

# Apply time-based decay manually
memorydecay tick
```

## Memory Categories

Not all memories are equal. The skill guides the agent to pick the right category and importance:

| Category | When | Importance | Example |
|----------|------|------------|---------|
| `preference` | User's role, style, habits, likes/dislikes | 0.8–1.0 | "User prefers Korean for conversation, English for code" |
| `decision` | Why X was chosen, tradeoffs, rejected alternatives | 0.8–0.9 | "Chose SQLite over Postgres — single-node, no ops overhead" |
| `fact` | Technical facts, API behaviors, architecture | 0.7–0.9 | "Auth service returns inconsistent 4xx on token expiry" |
| `episode` | What was worked on, session context | 0.3–0.6 | "Finished migrating auth middleware" |

The agent stores proactively — it doesn't wait for the user to say "remember this."

## Agent Memory Workflow

1. **At session start**: Agent reads SKILL.md → searches memories for relevant context
2. **During conversation**: Agent stores proactively — preferences, decisions, facts, episodes — with calibrated importance
3. **Before compaction**: Hook applies decay automatically
4. **On recall**: Agent searches and sees freshness indicators (`fresh` → act confidently, `stale` → verify first)

## Development

```bash
# Install dev dependencies with uv
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src tests
ruff check src tests

# Validate plugin
claude plugin validate .
```

## Architecture

| Component | File | Purpose |
|-----------|------|---------|
| CLI | `cli.py` | Click-based command interface |
| Client | `client.py` | HTTP client for memory-decay-core |
| Server Manager | `server_manager.py` | PID-based server lifecycle |
| Migrator | `migrator.py` | Import existing memories |
| Skill | `SKILL.md` | Agent instructions |
| Hooks | `pre-compact`, `session-end` | Automatic decay triggers |

## License

MIT
