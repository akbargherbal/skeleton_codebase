#!/usr/bin/env python3
"""
Test module: test_config
"""
import sys
from pathlib import Path
import pytest

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import Config


class TestConfig:
    """Test Config dataclass and its defaults."""

    def test_config_default_initialization(self):
        """Test Config creates with default values."""
        config = Config()
        assert config.mode == "skeleton"
        assert config.max_tokens == 50000
        assert not config.show_deps
        assert config.output is None
        assert isinstance(config.include_full, set)
        assert isinstance(config.exclude, set)

    def test_config_custom_mode(self):
        """Test Config with custom mode setting."""
        config = Config(mode="overview")
        assert config.mode == "overview"

    def test_config_include_full_set(self):
        """Test include_full as a set of paths."""
        config = Config(include_full={"a.py", "b.txt"})
        assert config.include_full == {"a.py", "b.txt"}

    def test_config_include_patterns_set(self):
        """Test include_patterns as a set of glob patterns."""
        config = Config(include_patterns={"*.py", "*.js"})
        assert config.include_patterns == {"*.py", "*.js"}

    def test_config_skeleton_only_set(self):
        """Test skeleton_only as a set of directory patterns."""
        config = Config(skeleton_only={"src/"})
        assert config.skeleton_only == {"src/"}

    def test_config_exclude_set(self):
        """Test exclude as a set of patterns."""
        config = Config(exclude={"node_modules/"})
        assert config.exclude == {"node_modules/"}

    def test_config_max_tokens_setting(self):
        """Test max_tokens configuration."""
        config = Config(max_tokens=100)
        assert config.max_tokens == 100

    def test_config_show_deps_flag(self):
        """Test show_deps boolean flag."""
        config = Config(show_deps=True)
        assert config.show_deps

    def test_config_output_path(self):
        """Test output file path configuration."""
        config = Config(output="/tmp/out.txt")
        assert config.output == "/tmp/out.txt"

    def test_default_full_patterns_content(self):
        """Test DEFAULT_FULL_PATTERNS contains expected files."""
        assert "README.md" in Config.DEFAULT_FULL_PATTERNS
        assert "package.json" in Config.DEFAULT_FULL_PATTERNS
        assert "requirements.txt" in Config.DEFAULT_FULL_PATTERNS

    def test_default_exclude_patterns_content(self):
        """Test DEFAULT_EXCLUDE_PATTERNS contains common exclusions."""
        assert "node_modules" in Config.DEFAULT_EXCLUDE_PATTERNS
        assert ".git" in Config.DEFAULT_EXCLUDE_PATTERNS
        assert "__pycache__" in Config.DEFAULT_EXCLUDE_PATTERNS
        assert "*.pyc" in Config.DEFAULT_EXCLUDE_PATTERNS

    def test_exclude_dirs_content(self):
        """Test EXCLUDE_DIRS contains test/migration directories."""
        assert "tests" in Config.EXCLUDE_DIRS
        assert "migrations" in Config.EXCLUDE_DIRS
        assert "static" in Config.EXCLUDE_DIRS
