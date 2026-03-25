# tests/test_migrator.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from claude_code_memorydecay.migrator import migrate_memories, parse_markdown_file


class TestMigrator:
    def test_parse_markdown_file_with_headers(self, tmp_path):
        """Test parsing markdown file with headers."""
        md_file = tmp_path / "memory.md"
        md_file.write_text("""# Section 1
This is content for section 1.

# Section 2
This is content for section 2.
More content here.
""")
        
        chunks = parse_markdown_file(md_file)
        
        assert len(chunks) == 2
        assert "Section 1" in chunks[0]
        assert "section 1" in chunks[0]
        assert "Section 2" in chunks[1]

    def test_parse_markdown_file_no_headers(self, tmp_path):
        """Test parsing markdown file without headers."""
        md_file = tmp_path / "memory.md"
        md_file.write_text("This is just plain content without headers.")
        
        chunks = parse_markdown_file(md_file)
        
        assert len(chunks) == 1
        assert "plain content" in chunks[0]

    def test_migrate_memories_with_files(self, tmp_path):
        """Test migrating from directory with files."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        # Create test files with content longer than 50 characters
        (memory_dir / "2024-01-15.md").write_text("# Daily log\nSomething very interesting happened today that needs to be remembered.")
        (memory_dir / "MEMORY.md").write_text("# Important fact\nThis is very important information that should be stored in memory.")
        
        mock_client = Mock()
        mock_client.store.return_value = {"id": "mem-1"}
        
        count = migrate_memories(mock_client, memory_dir)
        
        assert count == 2
        assert mock_client.store.call_count == 2

    def test_migrate_skips_short_content(self, tmp_path):
        """Test that very short content is skipped."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        (memory_dir / "short.md").write_text("Hi")  # Too short
        
        mock_client = Mock()
        
        count = migrate_memories(mock_client, memory_dir)
        
        assert count == 0
        mock_client.store.assert_not_called()
