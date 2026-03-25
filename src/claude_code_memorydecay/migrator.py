# src/claude_code_memorydecay/migrator.py
"""Migration tool for existing Claude Code memories."""

import re
from pathlib import Path
from typing import List

from .client import MemoryDecayClient


def parse_markdown_file(file_path: Path) -> List[str]:
    """Parse a markdown file into chunks.
    
    Splits by headers (# ## ###) if present, otherwise returns whole file.
    """
    content = file_path.read_text(encoding='utf-8')
    
    # If no headers, return whole content as single chunk
    if not re.search(r'^#{1,6}\s', content, re.MULTILINE):
        return [content.strip()]
    
    # Split by headers
    chunks = []
    current_chunk = []
    current_header = None
    
    for line in content.split('\n'):
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        
        if header_match:
            # Save previous chunk if exists
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
            
            # Start new chunk with header
            current_header = header_match.group(2)
            current_chunk = [line]
        else:
            if current_chunk:
                current_chunk.append(line)
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)
    
    return chunks


def determine_importance(file_path: Path) -> float:
    """Determine importance based on file type."""
    filename = file_path.name.lower()
    
    # User-created MEMORY.md - high importance
    if filename == 'memory.md':
        return 0.8
    
    # Date-based logs - lower importance
    if re.match(r'^\d{4}-\d{2}-\d{2}.*\.md$', filename):
        return 0.4
    
    # Everything else - medium
    return 0.5


def determine_category(file_path: Path) -> str:
    """Determine category based on content hints."""
    filename = file_path.name.lower()
    
    if 'preference' in filename or 'user' in filename:
        return 'preference'
    elif 'decision' in filename:
        return 'decision'
    elif re.match(r'^\d{4}-\d{2}-\d{2}', filename):
        return 'episode'
    else:
        return 'fact'


def migrate_memories(client: MemoryDecayClient, from_path: Path) -> int:
    """Migrate memories from files to memory-decay-core.
    
    Args:
        client: MemoryDecayClient instance
        from_path: Path to directory or file containing memories
        
    Returns:
        Number of memories migrated
    """
    count = 0
    
    if from_path.is_file():
        files = [from_path]
    else:
        files = list(from_path.glob('*.md'))
    
    for file_path in files:
        try:
            chunks = parse_markdown_file(file_path)
            importance = determine_importance(file_path)
            category = determine_category(file_path)
            
            for chunk in chunks:
                # Skip very short chunks
                if len(chunk) < 50:
                    continue
                
                # Split long chunks
                if len(chunk) > 1000:
                    sub_chunks = _split_long_chunk(chunk)
                else:
                    sub_chunks = [chunk]
                
                for sub_chunk in sub_chunks:
                    try:
                        client.store(
                            text=sub_chunk,
                            importance=importance,
                            category=category,
                            mtype='episode' if category == 'episode' else 'fact'
                        )
                        count += 1
                    except Exception as e:
                        print(f"Warning: Failed to store chunk from {file_path}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}")
            continue
    
    return count


def _split_long_chunk(chunk: str, max_length: int = 1000) -> List[str]:
    """Split a long chunk into smaller pieces."""
    chunks = []
    paragraphs = chunk.split('\n\n')
    
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_length:
            if current:
                current += '\n\n'
            current += para
        else:
            if current:
                chunks.append(current)
            current = para
    
    if current:
        chunks.append(current)
    
    return chunks if chunks else [chunk[:max_length]]
