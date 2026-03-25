---
name: memorydecay
description: Human-like memory with decay for Claude Code
---

# Memory System (memorydecay)

You have access to a human-like memory system that decays naturally over time. Important memories persist longer; trivial ones fade away.

## Session Start

At the start of each session, the memory system is automatically available. No action needed - the server starts on first use.

## Commands

Use these commands to interact with your memory:

```bash
# Search for relevant memories
memorydecay search "your query here" [--top-k 5]

# Store an important memory
memorydecay store "memory content" [--importance 0.8] [--category fact]

# Apply time-based decay (called automatically by hooks)
memorydecay tick

# Check server status
memorydecay server status

# Migrate existing memories from files
memorydecay migrate [--from ~/.claude/memory]
```

## When to Store Memories

Proactively store information that will be useful later:

- **Facts** (importance: 0.8): API decisions, architectural patterns, domain knowledge
- **Preferences** (importance: 0.8): User likes/dislikes, style preferences, settings
- **Decisions** (importance: 0.8): Why something was done a certain way, tradeoffs considered
- **Episodes** (importance: 0.5): What was worked on, context for future reference

Store BEFORE context gets too long - don't wait until compaction.

## When to Search Memories

Always search before:
- Answering questions that might have been discussed before
- Making decisions that might have prior context
- Starting work on a topic that might have history

## Freshness Indicators

Search results include freshness:
- **FRESH** (>0.7): Recently recalled or high importance - reliable
- **NORMAL** (0.3-0.7): Moderate decay - probably accurate but verify if critical
- **STALE** (<0.3): Heavily decayed - may be outdated, use with caution

## Automatic Decay

Memories naturally fade over time based on:
- **Importance**: Higher = slower decay
- **Recalls**: Each recall strengthens the memory (testing effect)
- **Time**: Decay applies automatically via hooks on PreCompact and SessionEnd

You don't need to manually manage decay - the system handles it.

## Migration (One-Time)

If you have existing memories in `~/.claude/memory/` or `MEMORY.md`:

```bash
memorydecay migrate --from ~/.claude/memory
```

This imports them with appropriate importance levels based on file type.

## Best Practices

1. **Search first, then decide**: Always check if relevant context exists
2. **Store proactively**: Don't wait to be asked - if something seems worth remembering, store it
3. **Be specific**: Clear, concise memories are more retrievable
4. **Respect freshness**: Stale memories might be outdated - verify before relying on them
5. **Use categories**: Helps with future retrieval and organization

## Troubleshooting

If `memorydecay` commands fail:
1. Check server status: `memorydecay server status`
2. Start manually if needed: `memorydecay server start`
3. Verify memory-decay-core is available at `MEMORYDECAY_CORE_PATH`
