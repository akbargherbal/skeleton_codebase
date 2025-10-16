#!/usr/bin/env python3
"""
Test module: test_tree_builder
COMPLETE FILE - Replace your entire tests/unit/test_tree_builder.py with this
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import TreeBuilder, Config


class TestTreeBuilder:
    """Test TreeBuilder for directory tree generation."""

    @patch("codebase_skeleton.DisplayTree")
    def test_build_with_directory_tree_available(
        self,
        mock_display_tree,
        mock_codebase,
        default_config,
        mock_directory_tree_available,
    ):
        """Test tree building using directory_tree library."""
        mock_display_tree.return_value = "mocked tree"
        tree_str = TreeBuilder.build(mock_codebase, default_config)
        assert tree_str == "mocked tree"
        mock_display_tree.assert_called_once()

    @patch("codebase_skeleton.DisplayTree", side_effect=Exception("mock error"))
    def test_build_with_directory_tree_exception(
        self,
        mock_display_tree,
        mock_codebase,
        default_config,
        mock_directory_tree_available,
    ):
        """Test fallback when directory_tree raises exception."""
        tree_str = TreeBuilder.build(mock_codebase, default_config)
        assert "src/" in tree_str
        assert "README.md" in tree_str
        assert "node_modules" not in tree_str  # Should be ignored by fallback

    def test_build_with_fallback(
        self, mock_codebase, default_config, mock_directory_tree_unavailable
    ):
        """Test tree building with fallback ASCII tree."""
        tree_str = TreeBuilder.build(mock_codebase, default_config)
        assert mock_codebase.name in tree_str
        assert "src/" in tree_str
        assert "main.py" in tree_str
        assert "node_modules" not in tree_str

    def test_fallback_tree_basic_structure(
        self, mock_codebase, default_config, mock_directory_tree_unavailable
    ):
        """Test fallback tree generates correct structure."""
        tree_str = TreeBuilder.build(mock_codebase, default_config)
        lines = tree_str.strip().split("\n")
        assert f"{mock_codebase.name}/" in lines[0]
        assert any("├── .gitignore" in line for line in lines)
        assert any("└── src/" in line or "├── src/" in line for line in lines)
        # Check for main.py with proper tree characters (not literal 4 spaces)
        # The actual output uses box-drawing characters like "│   └── main.py"
        assert any(
            "main.py" in line and ("├──" in line or "└──" in line) for line in lines
        )

    def test_fallback_tree_respects_exclusions(
        self, mock_codebase, mock_directory_tree_unavailable
    ):
        """Test fallback tree excludes configured patterns."""
        custom_config = Config(exclude={"src"})
        tree_str = TreeBuilder.build(mock_codebase, custom_config)
        
        # When we exclude "src", the src/ directory should not appear
        assert "src/" not in tree_str
        
        # Check that files unique to src/ are not present
        # The mock_codebase fixture creates src/utils.js which only exists in src/
        assert "utils.js" not in tree_str, "Files in excluded src/ should not appear"
        
        # Verify that tests/ directory is still included (not excluded)
        assert "tests/" in tree_str, "tests/ directory should still be present"
        assert "test_main.py" in tree_str, "test files should still be present"

    def test_fallback_tree_depth_limit(
        self, temp_dir, default_config, mock_directory_tree_unavailable
    ):
        """Test fallback tree respects max depth of 5."""
        p = temp_dir
        for i in range(7):
            p = p / f"level_{i}"
            p.mkdir()
        (p / "file.txt").touch()

        tree_str = TreeBuilder.build(temp_dir, default_config)
        assert "level_5" not in tree_str
        assert "level_4" in tree_str

    def test_fallback_tree_permission_error(
        self, mock_codebase, default_config, mock_directory_tree_unavailable
    ):
        """Test fallback tree handles permission errors gracefully."""
        (mock_codebase / "no_access").mkdir(mode=0o000)
        try:
            tree_str = TreeBuilder.build(mock_codebase, default_config)
            assert "no_access" in tree_str  # The directory itself is listed
        finally:
            # Best effort to clean up, may fail on some systems
            try:
                (mock_codebase / "no_access").chmod(0o755)
                (mock_codebase / "no_access").rmdir()
            except OSError:
                pass

    def test_fallback_tree_empty_directory(
        self, temp_dir, default_config, mock_directory_tree_unavailable
    ):
        """Test fallback tree with empty directory."""
        tree_str = TreeBuilder.build(temp_dir, default_config)
        assert tree_str.strip() == f"{temp_dir.name}/"

    def test_fallback_tree_single_file(
        self, temp_dir, default_config, mock_directory_tree_unavailable
    ):
        """Test fallback tree with single file."""
        (temp_dir / "file.txt").touch()
        tree_str = TreeBuilder.build(temp_dir, default_config)
        assert "file.txt" in tree_str

    def test_should_ignore_node_modules(
        self, mock_codebase, default_config, mock_directory_tree_unavailable
    ):
        """Test that node_modules is ignored in tree."""
        tree_str = TreeBuilder.build(mock_codebase, default_config)
        assert "node_modules" not in tree_str

    def test_should_ignore_venv(
        self, temp_dir, default_config, mock_directory_tree_unavailable
    ):
        """Test that venv is ignored in tree."""
        (temp_dir / "venv").mkdir()
        tree_str = TreeBuilder.build(temp_dir, default_config)
        assert "venv" not in tree_str

    def test_should_ignore_git(
        self, temp_dir, default_config, mock_directory_tree_unavailable
    ):
        """Test that .git is ignored in tree."""
        (temp_dir / ".git").mkdir()
        tree_str = TreeBuilder.build(temp_dir, default_config)
        assert ".git" not in tree_str
