# Claude Code memorydecay Plugin Design

## Overview

A Claude Code plugin that integrates `memory-decay-core` to provide human-like memory decay capabilities. The plugin automatically manages the Python server's lifecycle and exposes memory operations via CLI commands that the agent invokes through SKILL.md instructions.

## Goals

- Provide long-term memory with decay for Claude Code agents
- Automatic server lifecycle management (start/stop)
- Minimal configuration required
- Support migration from existing Claude Code memory files

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   Claude Code   │ ───► │  memorydecay CLI │ ───► │ memory-decay-core   │
│   Agent         │      │  (Python wrapper)│      │  (FastAPI server)   │
│                 │      │                  │      │  Port 8100          │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
        │                          │                          │
        │ SKILL.md 지시            │ 서버 생명주기 관리        │ SQLite + Vector DB
        │ • memory_search          │ • start (lazy)           │
        │ • memory_store           │ • stop (session_end)     │
        │ • memory_migrate         │ • health check           │
        │                          │                          │
        ▼                          ▼                          ▼
   .claude/skills/          Hook commands              Data persistence
   memorydecay/
```

## Components

### 1. CLI (`memory_decay/cli.py`)

Python CLI tool that wraps the HTTP API and manages server lifecycle.

**Commands:**

| Command | Description |
|---------|-------------|
| `memorydecay server start` | Start background server if not running |
| `memorydecay server stop` | Stop the server |
| `memorydecay server status` | Check server health |
| `memorydecay search <query>` | Search memories with decay-aware ranking |
| `memorydecay store <text>` | Store a memory |
| `memorydecay tick` | Apply time-based decay (auto-tick) |
| `memorydecay migrate [--from PATH]` | Migrate existing memories |

**Server Lifecycle:**
- **Lazy Start**: Server starts on first command invocation if not already running
- **PID File**: Tracks running server at `~/.memorydecay/server.pid`
- **Health Check**: Validates server is responsive before operations
- **Auto-Stop**: Optional cleanup on session end

### 2. SKILL.md (`.claude/skills/memorydecay/SKILL.md`)

Agent instructions for using memory operations.

**Sections:**

1. **Session Start Protocol**
   - Check server status, start if needed
   - No automatic memory loading (decay system uses search)

2. **Memory Store**
   - When to store: important facts, decisions, user preferences
   - Importance levels: 0.9 (user explicit), 0.8 (agent proactive), 0.3 (auto-save if enabled)
   - Categories: fact, episode, preference, decision

3. **Memory Search**
   - Always search before answering if past context might help
   - Results include freshness indicators (fresh/normal/stale)
   - Interpret freshness: stale memories may be outdated

4. **Migration**
   - One-time operation to import existing memories
   - Preserves importance heuristics from source

### 3. Hooks (`.claude/hooks/`)

**PreCompact Hook** (`pre-compact`):
```bash
#!/bin/bash
memorydecay tick
```
- Triggered before context compaction
- Applies time-based decay to all memories

**Session End Hook** (`session-end`):
```bash
#!/bin/bash
memorydecay tick
# Optional: memorydecay server stop
```
- Triggered on session end
- Applies decay for elapsed time

### 4. Migration Tool (`memory_decay/migrator.py`)

Imports existing Claude Code memory files into memory-decay-core.

**Supported Sources:**
- `~/.claude/memory/*.md` - Markdown memory files
- `MEMORY.md` - Project-level memory file
- `CLAUDE.md` memory sections (if separable)

**Importance Heuristics:**
| Source | Importance |
|--------|------------|
| User-created MEMORY.md | 0.8 |
| Date-based logs (YYYY-MM-DD.md) | 0.4 |
| Other files | 0.5 |

**Chunking Strategy:**
- Split by markdown headers
- Max chunk size: 1000 characters
- Min chunk size: 100 characters

## Data Flow

### Session Lifecycle

```
[Session Start]
  ├─> Agent reads SKILL.md (automatic by Claude Code)
  ├─> First memory command triggers server start
  ├─> CLI checks for existing server (shared with OpenClaw)
  └─> Server health check confirms readiness

[During Conversation]
  ├─> Agent detects important information
  ├─> Executes: memorydecay store "content" --importance 0.8
  ├─> CLI connects to shared server (starts if needed)
  └─> HTTP POST /store to localhost:8100
  └─> Memories stored in shared database (visible to OpenClaw)

[Before Context Compaction]
  ├─> PreCompact hook fires
  ├─> Executes: memorydecay tick
  └─> HTTP POST /auto-tick to apply decay
  └─> Decay applied to all memories (shared with OpenClaw sessions)

[Session End]
  ├─> Session end hook fires
  ├─> Executes: memorydecay tick
  └─> Server keeps running (other clients may be using it)
```

### Memory Operations

**Store Flow:**
```
Agent decision → CLI store → HTTP POST /store → SQLite + Vector DB
```

**Search Flow:**
```
Agent query → CLI search → HTTP POST /search → Hybrid search (vector + BM25)
                                    ↓
                              Return ranked results with freshness
```

**Decay Flow:**
```
Hook trigger → CLI tick → HTTP POST /auto-tick → Calculate elapsed time
                                               → Apply decay to all memories
```

## Shared Database with OpenClaw

A key design requirement: **Claude Code and OpenClaw plugins must share the same database**. Both plugins use `memory-decay-core` and should access the same memory store.

**Shared Configuration:**

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORYDECAY_PORT` | 8100 | Server port (must match OpenClaw config) |
| `MEMORYDECAY_DB_PATH` | `~/.memorydecay/memories.db` | Shared SQLite database |
| `MEMORYDECAY_PYTHON` | `python3` | Python interpreter path |
| `MEMORYDECAY_CORE_PATH` | (auto-detect) | Path to memory-decay-core |

**Database Location Consistency:**
- OpenClaw plugin default: `~/.openclaw/memory-decay-data/memories.db`
- Claude Code plugin default: `~/.memorydecay/memories.db`
- **Resolution**: Use `~/.memorydecay/memories.db` as canonical path
- OpenClaw config should override: `"dbPath": "~/.memorydecay/memories.db"`

**Single Server Instance:**
- Only one server process should run at a time
- PID file at `~/.memorydecay/server.pid` prevents duplicate instances
- If OpenClaw started the server, Claude Code CLI connects to existing instance
- If Claude Code CLI started the server, OpenClaw plugin connects to existing instance
- Server stops when last client disconnects (configurable timeout)

**Auto-Detection:**
- CLI attempts to find memory-decay-core in:
  1. Same parent directory as claude-code-memory-decay
  2. `MEMORYDECAY_CORE_PATH` environment variable
  3. `pip show memory-decay-core` if installed as package

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Server start fails | CLI returns error with helpful message |
| Server unreachable | Attempt restart once, then fail with instructions |
| Store/search timeout | Retry once, then return error |
| Migration failure | Continue with partial import, log skipped items |
| Concurrent server start | Use file locking, second process waits |

## Security Considerations

- Server binds to `127.0.0.1` only (no external access)
- No authentication required (local-only)
- Database file permissions: 600 (user read/write only)
- PID file permissions: 644

## Testing Strategy

**Unit Tests:**
- CLI command parsing
- Server lifecycle (mock subprocess)
- HTTP client error handling

**Integration Tests:**
- End-to-end: store → search → tick → search
- Migration from sample files
- Hook execution simulation

**Manual Tests:**
- Claude Code session with plugin installed
- Long-running session decay verification
- Concurrent access scenarios

## Dependencies

**Runtime:**
- Python 3.10+
- memory-decay-core (local path or installed)
- click (CLI framework)
- requests (HTTP client)

**Development:**
- pytest
- pytest-asyncio
- black, ruff

## Future Enhancements

1. **Auto-save mode**: Optional per-turn automatic storage
2. **Memory visualization**: `memorydecay stats` command
3. **Importance auto-detection**: LLM-based importance scoring
4. **Memory pruning**: Explicit low-activation cleanup
5. **Multi-workspace**: Per-project isolated memory databases

## References

- [memory-decay-core](../../../memory-decay-core/README.md)
- [openclaw-memory-decay](../../../openclaw-memory-decay/README.md)
- [hipocampus](https://github.com/kevin-hs-sohn/hipocampus)
