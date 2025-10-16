#!/usr/bin/env python3
"""
Pytest fixtures for test suite.
Shared fixtures available to all test modules.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Add project root to sys.path to allow importing codebase_skeleton
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import Config


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for tests to run in."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


@pytest.fixture
def mock_codebase(temp_dir):
    """Creates a mock codebase structure in the temp directory."""
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()
    (temp_dir / "node_modules").mkdir()

    (temp_dir / "README.md").write_text("# Mock Project")
    (temp_dir / "requirements.txt").write_text("pytest==6.2.5")
    (temp_dir / ".gitignore").write_text("node_modules/\n__pycache__/")

    (temp_dir / "src" / "main.py").write_text(
        """
import os

class Greeter:
    \"\"\"A simple greeter class.\"\"\"
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        \"\"\"Returns a greeting.\"\"\"
        print(f"Hello, {self.name}!")
        return f"Hello, {self.name}!"

def main(name: str = "World"):
    \"\"\"Main entry point.\"\"\"
    greeter = Greeter(name)
    greeter.greet()
"""
    )

    (temp_dir / "src" / "utils.js").write_text(
        """
export function helper(value) {
    // Some complex logic here
    return value * 2;
}
"""
    )

    (temp_dir / "tests" / "test_main.py").write_text(
        """
from src.main import Greeter

def test_greeter():
    g = Greeter("Test")
    assert g.greet() == "Hello, Test!"
"""
    )

    (temp_dir / "node_modules" / "some_lib.js").write_text("console.log('lib');")

    return temp_dir


@pytest.fixture
def default_config():
    """Returns a default Config instance."""
    return Config()


@pytest.fixture
def custom_config():
    """Returns a custom Config instance for testing specific features."""
    return Config(
        exclude={"*.js"},
        include_full={"src/main.py"},
    )


# Fixtures to mock availability of optional dependencies
@pytest.fixture
def mock_tree_sitter_available(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.TREE_SITTER_AVAILABLE", True)


@pytest.fixture
def mock_tree_sitter_unavailable(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.TREE_SITTER_AVAILABLE", False)


@pytest.fixture
def mock_tiktoken_available(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.TIKTOKEN_AVAILABLE", True)


@pytest.fixture
def mock_tiktoken_unavailable(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.TIKTOKEN_AVAILABLE", False)


@pytest.fixture
def mock_directory_tree_available(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.DIRECTORY_TREE_AVAILABLE", True)


@pytest.fixture
def mock_directory_tree_unavailable(monkeypatch):
    monkeypatch.setattr("codebase_skeleton.DIRECTORY_TREE_AVAILABLE", False)
