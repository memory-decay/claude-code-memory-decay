---
name: learned-setup-memorydecay-plugin
description: Use when a user wants to install or set up the claude-code-memory-decay plugin, when marketplace install fails, or when the user says "install", "setup", or "configure" in this repository
---

# Setup memorydecay Plugin

## When to Use
- User asks to install, setup, or configure this plugin
- User runs `/plugin marketplace add` and it fails
- New contributor cloning this repo for the first time
- Server connection issues or port configuration needed

## Procedure

### Step 1: Install the backend engine (memory-decay)

```bash
pip install memory-decay

# Verify installation
pip show memory-decay | head -3
# Expected: Name: memory-decay, Version: 0.1.x
```

### Step 2: Install the memorydecay CLI

```bash
uv tool install --from . claude-code-memorydecay
```

Fallback if `uv tool` fails:
```bash
uv venv && uv pip install -e .
```

Verify: `memorydecay --version` should print `memorydecay, version 0.2.1`

### Step 3: Install skill and hooks

```bash
mkdir -p ~/.claude/skills ~/.claude/hooks ~/.memorydecay

# Skill (agent instructions)
cp -r .claude/skills/memorydecay ~/.claude/skills/

# Hooks (automatic decay triggers)
cp .claude/hooks/pre-compact .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact ~/.claude/hooks/session-end
```

### Step 4: Configure environment (optional)

The CLI auto-detects the `memory-decay` installation path via `pip show memory-decay`. Override with environment variables only if needed:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEMORYDECAY_PORT` | `8100` | Server port — health endpoint at `http://127.0.0.1:{port}/health` |
| `MEMORYDECAY_DB_PATH` | `~/.memorydecay/memories.db` | SQLite database location |
| `MEMORYDECAY_PYTHON` | `python3` | Python executable for running the server |

### Step 5: Start server and verify connection

```bash
# Start the backend server
memorydecay server start

# Check it's running — shows PID and current tick
memorydecay server status

# Verify the health endpoint directly
curl -s http://127.0.0.1:${MEMORYDECAY_PORT:-8100}/health
```

If `server start` fails:
1. Check memory-decay is installed: `pip show memory-decay`
2. Check port isn't taken: `lsof -i :${MEMORYDECAY_PORT:-8100}`
3. Try starting manually to see errors:
   ```bash
   python3 -m memory_decay.server --port 8100 --db-path ~/.memorydecay/memories.db
   ```

### Step 6: Test end-to-end

```bash
# Store a test memory
memorydecay store "Setup completed successfully" --importance 0.5 --category episode

# Search for it
memorydecay search "setup"

# Apply decay tick
memorydecay tick
```

## Known Failure Modes

- **`pip show memory-decay` returns nothing** — the package isn't installed. Run `pip install memory-decay`. If your Python is different from the one Claude Code uses, try `python3 -m pip install memory-decay`
- **First `store` call times out (~30-60s)** — the embedding model downloads/initializes on first use. Subsequent calls are fast.
- **`memorydecay` command not found** — the CLI wasn't installed. Check `pip show claude-code-memorydecay`, or run directly: `python3 -m claude_code_memorydecay.cli --help`
- `uv pip install --system` fails on externally-managed Python environments — use `uv tool install` or a venv
- Marketplace install requires `.claude-plugin/marketplace.json` with plugin name matching the install command argument
- Port conflict: another process on port 8100 — change with `MEMORYDECAY_PORT`
- Stale PID file at `~/.memorydecay/server.pid` — delete it and restart if server status is inconsistent
- **Embedding errors** — if local provider fails, either `pip install sentence-transformers` or switch to OpenAI: `export MD_EMBEDDING_PROVIDER=openai`
