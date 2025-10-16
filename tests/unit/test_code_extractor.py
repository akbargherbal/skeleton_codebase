#!/usr/bin/env python3
"""
Test module: test_code_extractor
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import CodeExtractor

SAMPLE_PYTHON_CODE = """
import os
from sys import argv

class MyClass:
    \"\"\"A sample class.\"\"\"
    def __init__(self, value):
        self.value = value

    def my_method(self, multiplier: int) -> int:
        \"\"\"A sample method.\"\"\"
        return self.value * multiplier

def top_level_func(name: str):
    \"\"\"A top-level function.\"\"\"
    print(f"Hello, {name}")
"""

SAMPLE_JS_CODE = """
import { other } from './other.js';

export const myVar = 123;

export async function fetchData(url) {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

class User {
    constructor(name) {
        this.name = name;
    }
}
"""

SAMPLE_TS_CODE = """
import type { Request, Response } from 'express';

interface UserProfile {
    id: number;
    name: string;
}

export function getUser(req: Request): UserProfile {
    // Implementation details
    return { id: 1, name: "test" };
}
"""


@pytest.fixture
def code_extractor(mock_tree_sitter_available):
    return CodeExtractor()


class TestCodeExtractor:
    """Test CodeExtractor for skeleton generation."""

    def test_extractor_initialization_with_tree_sitter(
        self, mock_tree_sitter_available
    ):
        """Test CodeExtractor initializes with Tree-sitter."""
        extractor = CodeExtractor()
        assert "python" in extractor.parsers
        assert "javascript" in extractor.parsers
        assert "python" in extractor.queries

    def test_extractor_initialization_without_tree_sitter(
        self, mock_tree_sitter_unavailable
    ):
        """Test CodeExtractor initializes without Tree-sitter."""
        extractor = CodeExtractor()
        assert not extractor.parsers
        assert not extractor.queries

    def test_extract_skeleton_python_file(self, code_extractor):
        """Test skeleton extraction from Python file."""
        skeleton = code_extractor.extract_skeleton(Path("test.py"), SAMPLE_PYTHON_CODE)
        assert "import os" in skeleton
        assert "class MyClass:" in skeleton
        assert "def my_method(self, multiplier: int) -> int:" in skeleton
        assert "# [Implementation hidden]" in skeleton
        assert "self.value = value" not in skeleton

    def test_extract_skeleton_javascript_file(self, code_extractor):
        """Test skeleton extraction from JavaScript file."""
        skeleton = code_extractor.extract_skeleton(Path("test.js"), SAMPLE_JS_CODE)
        assert "import { other } from './other.js';" in skeleton
        assert "export async function fetchData(url)" in skeleton
        assert "class User" in skeleton
        assert "const response" not in skeleton

    def test_extract_skeleton_typescript_file(self, code_extractor):
        """Test skeleton extraction from TypeScript file."""
        skeleton = code_extractor.extract_skeleton(Path("test.ts"), SAMPLE_TS_CODE)
        assert "import type { Request, Response } from 'express';" in skeleton
        assert "export function getUser(req: Request): UserProfile" in skeleton

    def test_extract_skeleton_unsupported_extension(self, code_extractor):
        """Test extraction falls back for unsupported file types."""
        code = "SOME_CODE = 1"
        skeleton = code_extractor.extract_skeleton(Path("test.foo"), code)
        assert "SOME_CODE = 1" in skeleton  # Fallback includes first few lines

    def test_extract_skeleton_no_parser(self, mock_tree_sitter_unavailable):
        """Test extraction uses fallback when parser unavailable."""
        extractor = CodeExtractor()
        skeleton = extractor.extract_skeleton(Path("test.py"), SAMPLE_PYTHON_CODE)
        assert "import os" in skeleton
        assert "class MyClass:" in skeleton
        # NEW BEHAVIOR: Fallback now EXCLUDES implementation details
        assert "# [Implementation hidden]" in skeleton
        assert "self.value = value" not in skeleton
        assert "return self.value" not in skeleton

    def test_extract_skeleton_no_parser_preserves_docstrings(
        self, mock_tree_sitter_unavailable
    ):
        """Test fallback preserves docstrings but hides implementation."""
        extractor = CodeExtractor()
        skeleton = extractor.extract_skeleton(Path("test.py"), SAMPLE_PYTHON_CODE)
        assert '"""A sample class."""' in skeleton
        assert '"""A sample method."""' in skeleton
        assert '"""A top-level function."""' in skeleton


class TestCodeExtractorTreeSitter:
    """Test Tree-sitter specific extraction logic."""

    def test_extract_with_treesitter_python(self, code_extractor):
        """Test Tree-sitter extraction for Python code."""
        skeleton = code_extractor._extract_with_treesitter(SAMPLE_PYTHON_CODE, "python")
        assert "def top_level_func(name: str):" in skeleton
        assert '"""A top-level function."""' in skeleton
        assert "# [Implementation hidden]" in skeleton
        assert 'print(f"Hello, {name}")' not in skeleton

    def test_extract_with_treesitter_preserves_imports(self, code_extractor):
        """Test that import statements are preserved."""
        skeleton = code_extractor._extract_with_treesitter(SAMPLE_PYTHON_CODE, "python")
        assert "import os" in skeleton
        assert "from sys import argv" in skeleton

    def test_extract_with_treesitter_preserves_exports(self, code_extractor):
        """Test that export statements are preserved."""
        skeleton = code_extractor._extract_with_treesitter(SAMPLE_JS_CODE, "javascript")
        assert "export const myVar = 123;" in skeleton
        assert "export async function fetchData(url)" in skeleton

    def test_extract_with_treesitter_maintains_order(self, code_extractor):
        """Test that source order is maintained in output."""
        skeleton = code_extractor._extract_with_treesitter(SAMPLE_PYTHON_CODE, "python")
        import_pos = skeleton.find("import")
        class_pos = skeleton.find("class")
        func_pos = skeleton.find("def top_level_func")
        assert -1 < import_pos < class_pos < func_pos

    @patch("codebase_skeleton.Parser.parse", side_effect=Exception("mock parse error"))
    def test_extract_with_treesitter_handles_parse_error(
        self, mock_parse, code_extractor
    ):
        """Test extraction handles Tree-sitter parse errors."""
        # It should fall back to the less precise method
        skeleton = code_extractor._extract_with_treesitter("invalid code", "python")
        assert "invalid code" in skeleton

    def test_extract_function_with_docstring(self, code_extractor):
        """Test function extraction includes docstring."""
        code = 'def func():\n    """My docstring."""\n    pass'
        skeleton = code_extractor._extract_with_treesitter(code, "python")
        assert '"""My docstring."""' in skeleton

    def test_extract_function_without_docstring(self, code_extractor):
        """Test function extraction without docstring."""
        code = "def func():\n    pass"
        skeleton = code_extractor._extract_with_treesitter(code, "python")
        assert '"""' not in skeleton
        assert "# [Implementation hidden]" in skeleton

    def test_extract_class_with_docstring_and_methods(self, code_extractor):
        """Test class extraction includes class docstring and methods."""
        skeleton = code_extractor._extract_with_treesitter(SAMPLE_PYTHON_CODE, "python")
        assert '"""A sample class."""' in skeleton
        assert "def my_method(self, multiplier: int) -> int:" in skeleton
        assert "return self.value" not in skeleton


class TestCodeExtractorFallback:
    """Test fallback extraction without Tree-sitter."""

    @pytest.fixture
    def fallback_extractor(self, mock_tree_sitter_unavailable):
        return CodeExtractor()

    def test_fallback_extract_definitions(self, fallback_extractor):
        """Test fallback extracts def and class statements."""
        skeleton = fallback_extractor._fallback_extract(SAMPLE_PYTHON_CODE)
        assert "import os" in skeleton
        assert "class MyClass:" in skeleton
        assert "def __init__(self, value):" in skeleton
        assert "def my_method(self, multiplier: int) -> int:" in skeleton
        assert "def top_level_func(name: str):" in skeleton

    def test_fallback_extract_docstrings_triple_double(self, fallback_extractor):
        """Test fallback extracts triple double-quote docstrings."""
        skeleton = fallback_extractor._fallback_extract(SAMPLE_PYTHON_CODE)
        assert '"""A sample class."""' in skeleton
        assert '"""A sample method."""' in skeleton

    def test_fallback_extract_hides_implementation(self, fallback_extractor):
        """Test fallback hides implementation details."""
        skeleton = fallback_extractor._fallback_extract(SAMPLE_PYTHON_CODE)
        assert "self.value = value" not in skeleton
        assert "return self.value * multiplier" not in skeleton
        assert 'print(f"Hello, {name}")' not in skeleton
        assert "# [Implementation hidden]" in skeleton

    def test_fallback_extract_empty_file(self, fallback_extractor):
        """Test fallback handles empty files."""
        skeleton = fallback_extractor._fallback_extract("")
        # Empty file results in empty skeleton or minimal placeholder
        assert skeleton in ("", "# [Rest of file hidden]")

    def test_fallback_extract_unparsable_file(self, fallback_extractor):
        """Test fallback's last resort on a file with no recognizable structures."""
        content = "# This is a file with no functions or classes.\nVAR_A = 1\nVAR_B = 2\nVAR_C = 3\nVAR_D = 4\nVAR_E = 5\nVAR_F = 6"
        skeleton = fallback_extractor._fallback_extract(content)
        assert "# This is a file with no functions or classes." in skeleton
        # The logic takes the first 5 lines. Let's test the boundary.
        assert "VAR_D = 4" in skeleton  # 5th line should be present
        assert "VAR_E = 5" not in skeleton  # 6th line should be absent
        assert "# [Rest of file hidden]" in skeleton
