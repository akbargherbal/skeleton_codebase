#!/usr/bin/env python3
"""
Test module: test_skeleton_generator
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import SkeletonGenerator, Config


class TestSkeletonGenerator:
    """Test SkeletonGenerator main orchestration."""

    def test_generator_initialization(self, mock_codebase, default_config):
        """Test SkeletonGenerator initializes correctly."""
        generator = SkeletonGenerator(mock_codebase, default_config)
        assert generator.root == mock_codebase
        assert generator.config == default_config
        assert generator.stats["files_processed"] == 0

    @pytest.mark.parametrize(
        "path_str, expected",
        [
            ("node_modules/lib/index.js", True),
            ("src/main.pyc", True),
            ("tests/test_app.py", True),
            ("src/main.py", False),
            ("README.md", False),
        ],
    )
    def test_should_exclude(self, mock_codebase, default_config, path_str, expected):
        """Test default exclusion patterns work."""
        generator = SkeletonGenerator(mock_codebase, default_config)
        # Create a dummy file to have a concrete Path object
        file_path = mock_codebase / Path(path_str)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        assert generator.should_exclude(file_path) == expected

    @pytest.mark.parametrize(
        "path_str, expected",
        [
            ("README.md", True),
            ("requirements.txt", True),
            ("src/main.py", False),
        ],
    )
    def test_should_full_content_default_patterns(
        self, mock_codebase, default_config, path_str, expected
    ):
        """Test default full-content files (README.md, etc)."""
        generator = SkeletonGenerator(mock_codebase, default_config)
        path = mock_codebase / path_str
        assert generator.should_full_content(path) == expected

    def test_should_full_content_explicit_includes(self, mock_codebase):
        """Test explicit include_full list."""
        config = Config(include_full={"src/main.py"})
        generator = SkeletonGenerator(mock_codebase, config)
        path = mock_codebase / "src/main.py"
        assert generator.should_full_content(path) is True


class TestSkeletonGeneratorGenerate:
    """Test the main generate() method."""

    def test_generate_skeleton_mode(self, mock_codebase, default_config):
        """Test generate() in skeleton mode."""
        generator = SkeletonGenerator(mock_codebase, default_config)
        output = generator.generate()

        assert "<codebase project=" in output
        assert "<full-content>" in output
        assert "<file path='README.md'" in output
        assert "<skeleton>" in output
        assert "<file path='src/main.py'" in output
        assert "# [Implementation hidden]" in output
        # Removed: assert "<excluded>" in output
        # Removed: assert "<directory path='tests' files='1'/>" in output
        # Instead verify via stats
        assert generator.stats["full_content"] > 0
        assert generator.stats["skeleton"] > 0
        assert generator.stats["excluded"] > 0

    def test_generate_overview_mode(self, mock_codebase):
        """Test generate() in overview mode."""
        config = Config(mode="overview")
        generator = SkeletonGenerator(mock_codebase, config)
        output = generator.generate()

        assert "<full-content>" not in output
        assert "<skeleton>" not in output
        assert "<tree>" in output
        assert "<stats>" in output
        # Removed: assert "<excluded>" in output
        # Verify exclusions happened via stats instead
        assert generator.stats["excluded"] > 0

    def test_generate_updates_stats_counters(self, mock_codebase, default_config):
        """Test that stats counters are updated correctly."""
        generator = SkeletonGenerator(mock_codebase, default_config)
        generator.generate()
        stats = generator.stats

        # Based on mock_codebase:
        # Full: README.md, requirements.txt, .gitignore (3)
        # Skeleton: src/main.py, src/utils.js (2)
        # Excluded: tests/test_main.py, node_modules/some_lib.js (2)
        # Total processed = 3 + 2 = 5
        assert stats["files_processed"] == 5
        assert stats["full_content"] == 3
        assert stats["skeleton"] == 2
        assert stats["excluded"] == 2
        assert stats["total_tokens"] > 0

    def test_generate_file_read_error(self, mock_codebase, default_config, capsys):
        """Test generation continues on file read errors."""

        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if self.name == "main.py":
                raise IOError("mock read error")
            return original_read_text(self, *args, **kwargs)

        with patch("pathlib.Path.read_text", mock_read_text):
            generator = SkeletonGenerator(mock_codebase, default_config)
            output = generator.generate()

            # main.py will still appear in the tree section, but not in skeleton/full-content
            # Check that main.py doesn't appear in the skeleton section
            skeleton_section_start = output.find("<skeleton>")
            skeleton_section_end = output.find("</skeleton>")
            if skeleton_section_start != -1 and skeleton_section_end != -1:
                skeleton_section = output[skeleton_section_start:skeleton_section_end]
                assert (
                    "main.py" not in skeleton_section
                ), "main.py should not appear in skeleton section"

            # Also check that it doesn't appear in full-content section
            full_content_start = output.find("<full-content>")
            full_content_end = output.find("</full-content>")
            if full_content_start != -1 and full_content_end != -1:
                full_content_section = output[full_content_start:full_content_end]
                assert (
                    "main.py" not in full_content_section
                ), "main.py should not appear in full-content section"

        captured = capsys.readouterr()
        assert "Warning: Could not read" in captured.err
        assert "main.py" in captured.err

    def test_generate_show_excluded_flag(self, mock_codebase):
        """Test that show_excluded flag controls excluded section visibility."""
        # Test with show_excluded=False (default)
        config_default = Config()
        generator_default = SkeletonGenerator(mock_codebase, config_default)
        output_default = generator_default.generate()

        assert "<excluded>" not in output_default
        assert generator_default.stats["excluded"] > 0

        # Test with show_excluded=True
        config_with_flag = Config(show_excluded=True)
        generator_with_flag = SkeletonGenerator(mock_codebase, config_with_flag)
        output_with_flag = generator_with_flag.generate()

        assert "<excluded>" in output_with_flag
        assert "<directory path='tests' files='1'/>" in output_with_flag
