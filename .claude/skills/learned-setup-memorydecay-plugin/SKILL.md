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

### Step 1: Clone and install the backend server (memory-decay-core)

```bash
# Check if already cloned
ls ../memory-decay-core/src/memory_decay/server.py 2>/dev/null

# If not found, clone it
git clone https://github.com/memory-decay/memory-decay-core.git ../memory-decay-core

# Set up its virtualenv and install
cd ../memory-decay-core && uv venv && uv pip install -e . && cd -
```

Record the **absolute path** — you'll need it in Step 4:
```bash
realpath ../memory-decay-core
```

### Step 2: Install the memorydecay CLI

```bash
uv tool install --from . claude-code-memorydecay
```

Fallback if `uv tool` fails:
```bash
uv venv && uv pip install -e .
```

Verify: `memorydecay --version` should print `memorydecay, version 0.1.0`

### Step 3: Install skill and hooks

```bash
mkdir -p ~/.claude/skills ~/.claude/hooks ~/.memorydecay

# Skill (agent instructions)
cp -r .claude/skills/memorydecay ~/.claude/skills/

# Hooks (automatic decay triggers)
cp .claude/hooks/pre-compact .claude/hooks/session-end ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-compact ~/.claude/hooks/session-end
```

### Step 4: Configure environment — core path and server port

Set the required env var pointing to memory-decay-core:

```bash
# Add to shell profile (~/.zshrc or ~/.bashrc)
export MEMORYDECAY_CORE_PATH=$(realpath ../memory-decay-core)
```

The CLI auto-detects the venv python at `{core_path}/.venv/bin/python`. To override, set `MEMORYDECAY_PYTHON` explicitly.

**Server port** defaults to `8100`. To use a different port:

```bash
export MEMORYDECAY_PORT=8100  # change to desired port
```

All configurable env vars:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEMORYDECAY_CORE_PATH` | *(required)* | Absolute path to memory-decay-core repo |
| `MEMORYDECAY_PORT` | `8100` | Server port (health endpoint at `http://127.0.0.1:{port}/health`) |
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
1. Check core path exists: `ls $MEMORYDECAY_CORE_PATH/src/memory_decay/server.py`
2. Check port isn't taken: `lsof -i :${MEMORYDECAY_PORT:-8100}`
3. Try starting manually to see errors:
   ```bash
   cd $MEMORYDECAY_CORE_PATH
   PYTHONPATH=src python3 -m memory_decay.server --host 127.0.0.1 --port 8100 --db-path ~/.memorydecay/memories.db --embedding-provider local
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

- **Server fails with `ModuleNotFoundError: No module named 'sqlite_vec'`** — the CLI auto-detects `{core_path}/.venv/bin/python`, but if the venv doesn't exist, it falls back to system python. Fix: ensure `uv venv && uv pip install -e .` was run in memory-decay-core, or set `MEMORYDECAY_PYTHON` explicitly
- **First `store` call times out (~30-60s)** — the embedding model downloads/initializes on first use. Use `curl` with `--max-time 120` to warm it up, or just wait. Subsequent calls are fast.
- `uv pip install --system` fails on externally-managed Python environments — use `uv tool install` or a venv
- Marketplace install requires `.claude-plugin/marketplace.json` with plugin name matching the install command argument
- Server won't start if `MEMORYDECAY_CORE_PATH` is unset and `../memory-decay-core` doesn't exist as a sibling directory
- Port conflict: another process on port 8100 — change with `MEMORYDECAY_PORT`
- Stale PID file at `~/.memorydecay/server.pid` — delete it and restart if server status is inconsistent
