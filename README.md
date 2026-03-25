# Claude Code memorydecay

Human-like memory decay for Claude Code. Important things stick, noise fades.

## Features

- **Decay-aware search**: Retrieve memories ranked by relevance and freshness
- **Automatic lifecycle**: Server starts/stops automatically
- **Migration tool**: Import existing Claude Code memories

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Search memories
memorydecay search "API design decisions"

# Store a memory
memorydecay store "User prefers dark mode" --importance 0.8

# Check status
memorydecay server status
```

## License

MIT
