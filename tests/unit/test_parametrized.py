#!/usr/bin/env python3
"""
Test module: test_parametrized
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import sys

# Import module under test
from codebase_skeleton import (
    Config,
    TokenCounter,
    TreeBuilder,
    CodeExtractor,
    SkeletonGenerator,
)


class TestParametrized:
    """Parametrized tests for multiple scenarios."""

    @pytest.mark.parametrize("mode", ["skeleton", "overview", "hybrid", "custom"])
    def test_all_modes_produce_output(self, mock_codebase, mode):
        """Test all modes produce non-empty output."""
        config = Config(mode=mode)
        generator = SkeletonGenerator(mock_codebase, config)
        output = generator.generate()

        assert output, f"Mode {mode} produced empty output"
        assert "<codebase" in output
        assert "</codebase>" in output
        assert f"project='{mock_codebase.name}'" in output

    @pytest.mark.parametrize("extension", [".py", ".js", ".ts", ".tsx", ".jsx"])
    def test_supported_extensions(self, temp_dir, extension):
        """Test extraction works for supported extensions."""
        # Create a test file with the extension
        test_file = temp_dir / f"test{extension}"

        # Write appropriate content based on extension
        if extension == ".py":
            content = "def test_func():\n    pass\n"
        else:
            content = "function testFunc() {\n    return true;\n}\n"

        test_file.write_text(content)

        # Test extraction
        extractor = CodeExtractor()
        result = extractor.extract_skeleton(test_file, content)

        assert result, f"Extraction failed for {extension}"
        assert "test" in result.lower() or "func" in result.lower()

    @pytest.mark.parametrize(
        "exclude_pattern", ["node_modules", "venv", "__pycache__", ".git", "*.pyc"]
    )
    def test_default_exclusions(self, mock_codebase, exclude_pattern):
        """Test default exclusion patterns work."""
        config = Config()
        generator = SkeletonGenerator(mock_codebase, config)

        # Create a path that should be excluded
        excluded_path = mock_codebase / exclude_pattern.replace("*", "test")

        assert generator.should_exclude(
            excluded_path
        ), f"Pattern {exclude_pattern} was not excluded"

    @pytest.mark.parametrize(
        "config_file",
        [
            "README.md",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Dockerfile",
        ],
    )
    def test_config_files_full_content(self, temp_dir, config_file):
        """Test config files get full content."""
        config = Config()
        generator = SkeletonGenerator(temp_dir, config)

        # Create the config file
        test_file = temp_dir / config_file
        test_file.write_text("# Test content")

        assert generator.should_full_content(
            test_file
        ), f"{config_file} should have full content"
