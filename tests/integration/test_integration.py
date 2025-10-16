#!/usr/bin/env python3
"""
Test module: test_integration
"""

import os
import re
import sys
import time
from pathlib import Path

import pytest

# Add project root to sys.path to allow importing codebase_skeleton
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import Config, SkeletonGenerator


def create_project_structure(root: Path, structure: dict):
    """Recursively create a project structure from a dictionary."""
    for name, content in structure.items():
        path = root / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_project_structure(path, content)
        elif isinstance(content, str):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        else:
            raise TypeError(f"Unsupported content type: {type(content)}")


class TestIntegration:
    """Integration tests for full workflows."""

    def test_e2e_python_project(self, temp_dir):
        """End-to-end: Python project with multiple modules."""
        structure = {
            "my_python_app": {
                "README.md": "# Python App",
                "requirements.txt": "flask\nrequests",
                "app": {
                    "__init__.py": "",
                    "main.py": "def run():\n    print('Running')",
                    "db.py": "class Database:\n    pass",
                },
                "tests": {"test_main.py": "def test_run():\n    assert True"},
            }
        }
        project_root = temp_dir / "my_python_app"
        create_project_structure(temp_dir, structure)

        generator = SkeletonGenerator(project_root, Config())
        output = generator.generate()

        assert "<full-content>" in output
        assert "<file path='README.md'" in output
        assert "<file path='requirements.txt'" in output
        assert "<skeleton>" in output
        assert "app/main.py" in output
        assert "app/db.py" in output
        # Removed: assert "<excluded>" in output
        # Removed: assert "<directory path='tests' files='1'/>" in output

    def test_e2e_javascript_project(self, temp_dir):
        """End-to-end: JavaScript/Node project."""
        structure = {
            "my_js_app": {
                "package.json": '{"name": "my-js-app"}',
                "index.js": "function main() { console.log('hi'); }",
                "lib": {"auth.js": "export const auth = {};"},
                "node_modules": {"express": {"index.js": "// express code"}},
            }
        }
        project_root = temp_dir / "my_js_app"
        create_project_structure(temp_dir, structure)

        generator = SkeletonGenerator(project_root, Config())
        output = generator.generate()

        # Assert that core files are present
        assert "<file path='package.json'" in output
        assert "<file path='index.js'" in output
        assert "<file path='lib/auth.js'" in output

        # Assert that node_modules content is NOT processed
        assert "// express code" not in output

        # Assert that node_modules IS correctly excluded (check stats, not output)
        assert generator.stats["excluded"] > 0

    def test_e2e_mixed_project(self, temp_dir):
        """End-to-end: Mixed Python/JavaScript project."""
        structure = {
            "mixed_app": {
                "pyproject.toml": "[tool.poetry]",
                "package.json": '{"name": "mixed-app"}',
                "src": {
                    "main.py": "def main(): pass",
                    "index.js": "function run() {}",
                },
                "tests": {"test_main.py": "assert True"},
            }
        }
        project_root = temp_dir / "mixed_app"
        create_project_structure(temp_dir, structure)

        generator = SkeletonGenerator(project_root, Config())
        output = generator.generate()

        assert "<file path='pyproject.toml'" in output
        assert "<file path='package.json'" in output
        assert "<file path='src/main.py'" in output
        assert "<file path='src/index.js'" in output
        # Removed: assert "<directory path='tests' files='1'/>" in output

    def test_e2e_with_exclusions(self, temp_dir):
        """End-to-end: Project with tests and migrations excluded."""
        structure = {
            "excluded_proj": {
                "src": {"main.py": "pass"},
                "tests": {"test_main.py": "pass"},
                "migrations": {"0001_initial.py": "pass"},
                "data": {"db.sqlite3": "binary data"},
            }
        }
        project_root = temp_dir / "excluded_proj"
        create_project_structure(temp_dir, structure)

        config = Config(exclude={"data/"})
        generator = SkeletonGenerator(project_root, config)
        output = generator.generate()

        assert "<file path='src/main.py'" in output
        # Removed: assert "<directory path='tests' files='1'/>" in output
        # Removed: assert "<directory path='migrations' files='1'/>" in output
        # Removed: assert "<directory path='data' files='1'/>" in output
        # Instead, verify exclusions happened via stats
        assert generator.stats["excluded"] >= 3

    def test_e2e_with_custom_includes(self, temp_dir):
        """End-to-end: Project with specific files for full content."""
        structure = {
            "custom_proj": {
                "src": {
                    "main.py": "def run():\n    # implementation\n    pass",
                    # Using a variable assignment instead of a comment for a more robust test
                    "utils.py": "def helper():\n    implementation_detail = True\n    return implementation_detail",
                }
            }
        }
        project_root = temp_dir / "custom_proj"
        create_project_structure(temp_dir, structure)

        config = Config(mode="custom", include_full={"src/main.py"})
        generator = SkeletonGenerator(project_root, config)
        output = generator.generate()

        assert "<full-content>" in output
        assert "<file path='src/main.py'" in output
        assert "# implementation" in output
        assert "<skeleton>" in output
        assert "<file path='src/utils.py'" in output
        assert "# [Implementation hidden]" in output
        # Assert that the implementation line is not in the output
        assert "implementation_detail = True" not in output

    def test_e2e_overview_mode_output(self, mock_codebase):
        """End-to-end: Overview mode produces expected output."""
        config = Config(mode="overview")
        generator = SkeletonGenerator(mock_codebase, config)
        output = generator.generate()

        assert "<full-content>" not in output
        assert "<skeleton>" not in output
        assert "<tree>" in output
        assert "<stats>" in output
        # Removed: assert "<excluded>" in output

    def test_e2e_skeleton_mode_output(self, mock_codebase):
        """End-to-end: Skeleton mode produces expected output."""
        generator = SkeletonGenerator(mock_codebase, Config())
        output = generator.generate()

        assert "<full-content>" in output
        assert "<file path='README.md'" in output
        assert "Mock Project" in output

        assert "<skeleton>" in output
        assert "<file path='src/main.py'" in output
        assert "class Greeter:" in output
        assert "# [Implementation hidden]" in output
        assert 'print(f"Hello, {self.name}!")' not in output
        # Removed: assert "<excluded>" in output
        # Removed: assert "<directory path='tests' files='1'/>" in output

    def test_e2e_token_count_accuracy(self, mock_codebase, mock_tiktoken_available):
        """End-to-end: Token counts are reasonable."""
        generator = SkeletonGenerator(mock_codebase, Config())
        output = generator.generate()

        file_tokens = [int(m) for m in re.findall(r"tokens='(\d+)'", output)]
        total_tokens_match = re.search(r"<total-tokens>(\d+)</total-tokens>", output)

        assert total_tokens_match is not None
        total_tokens = int(total_tokens_match.group(1))

        assert sum(file_tokens) == total_tokens
        assert total_tokens > 0

    def test_e2e_large_codebase_performance(self, temp_dir):
        """End-to-end: Performance with 200+ files."""
        num_dirs = 10
        files_per_dir = 20
        structure = {}
        for i in range(num_dirs):
            dir_name = f"module_{i}"
            structure[dir_name] = {}
            for j in range(files_per_dir):
                file_name = f"file_{j}.py"
                structure[dir_name][file_name] = f"def func_{i}_{j}():\n    pass"

        create_project_structure(temp_dir, structure)

        start_time = time.time()
        generator = SkeletonGenerator(temp_dir, Config())
        generator.generate()
        end_time = time.time()

        duration = end_time - start_time
        assert generator.stats["files_processed"] == num_dirs * files_per_dir
        assert duration < 15  # Generous timeout for CI

    def test_e2e_unicode_filenames(self, temp_dir):
        """End-to-end: Handles Unicode filenames correctly."""
        structure = {
            "你好世界.py": "def hello():\n    print('世界')",
            "src": {"데이터.csv": "col1,col2"},
        }
        create_project_structure(temp_dir, structure)

        generator = SkeletonGenerator(temp_dir, Config())
        output = generator.generate()

        assert "<file path='你好世界.py'" in output
        assert "<file path='src/데이터.csv'" in output
        assert "col1,col2" in output

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="os.symlink requires special permissions on Windows",
    )
    def test_e2e_symlinks_handling(self, temp_dir):
        """End-to-end: Handles symlinks appropriately."""
        structure = {
            "actual_dir": {"a.py": "def func_a(): pass"},
            "b.py": "def func_b(): pass",
        }
        create_project_structure(temp_dir, structure)

        os.symlink(temp_dir / "b.py", temp_dir / "c_link.py")
        os.symlink(
            temp_dir / "actual_dir", temp_dir / "linked_dir", target_is_directory=True
        )

        generator = SkeletonGenerator(temp_dir, Config())
        output = generator.generate()

        assert "<file path='c_link.py'" in output
        assert "<file path='linked_dir/a.py'" in output

    def test_e2e_deeply_nested_structure(self, temp_dir):
        """End-to-end: Handles deeply nested directory structures."""
        deep_path = temp_dir
        for i in range(10):
            deep_path = deep_path / f"level_{i}"

        structure = {"deep_file.py": "def deep_func(): pass"}
        create_project_structure(deep_path, structure)

        generator = SkeletonGenerator(temp_dir, Config())
        output = generator.generate()

        expected_path = "level_0/level_1/level_2/level_3/level_4/level_5/level_6/level_7/level_8/level_9/deep_file.py"
        assert f"<file path='{expected_path}'" in output
        assert "deep_func" in output

    def test_e2e_show_excluded_flag(self, temp_dir):
        """End-to-end: show_excluded flag controls excluded section visibility."""
        structure = {
            "my_app": {
                "src": {"main.py": "def run(): pass"},
                "tests": {"test_main.py": "def test_run(): pass"},
            }
        }
        project_root = temp_dir / "my_app"
        create_project_structure(temp_dir, structure)

        # Test 1: Default behavior (show_excluded=False)
        config_default = Config()
        generator_default = SkeletonGenerator(project_root, config_default)
        output_default = generator_default.generate()

        assert "<excluded>" not in output_default
        assert generator_default.stats["excluded"] > 0  # Still tracks excluded files

        # Test 2: With show_excluded=True
        config_with_flag = Config(show_excluded=True)
        generator_with_flag = SkeletonGenerator(project_root, config_with_flag)
        output_with_flag = generator_with_flag.generate()

        assert "<excluded>" in output_with_flag
        assert "<directory path='tests' files='1'/>" in output_with_flag
