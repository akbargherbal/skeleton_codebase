"""
Test to demonstrate Bug #1: Config files in excluded directories
are incorrectly included with full content.
"""

import pytest
from pathlib import Path
from codebase_skeleton import Config, SkeletonGenerator


class TestBug01ConfigInExcludedDirs:
    """Tests demonstrating Bug #1 - config files bypass exclusion."""

    def test_config_file_in_node_modules_should_be_excluded(self, tmp_path):
        """
        Bug #1: tsconfig.json inside node_modules should be EXCLUDED,
        not included with full content.
        """
        # Create structure
        root = tmp_path / "project"
        root.mkdir()

        # Root level config (should be included)
        root_tsconfig = root / "tsconfig.json"
        root_tsconfig.write_text('{"compilerOptions": {"strict": true}}')

        # node_modules config (should be excluded)
        node_modules = root / "node_modules" / "typescript"
        node_modules.mkdir(parents=True)
        nm_tsconfig = node_modules / "tsconfig.json"
        nm_tsconfig.write_text('{"compilerOptions": {"lib": ["es2015"]}}')

        # Generate skeleton
        config = Config(mode="skeleton")
        generator = SkeletonGenerator(root, config)
        output = generator.generate()

        # ASSERTIONS
        # Root config should be in full-content
        assert "<full-content>" in output
        assert "tsconfig.json" in output
        assert '"strict": true' in output  # Root config content

        # node_modules config should NOT appear anywhere
        assert (
            '"lib": ["es2015"]' not in output
        )  # node_modules content should NOT appear

        # Verify stats
        assert generator.stats["full_content"] == 1  # Only root tsconfig
        assert generator.stats["excluded"] >= 1  # At least the node_modules file

        # The node_modules/typescript/tsconfig.json path should not appear in full-content section
        assert (
            "node_modules/typescript/tsconfig.json" not in output.split("<skeleton>")[0]
        )

    def test_config_file_in_venv_should_be_excluded(self, tmp_path):
        """
        Bug #1: pyproject.toml inside .venv should be EXCLUDED.
        """
        # Create structure
        root = tmp_path / "project"
        root.mkdir()

        # Root level config (should be included)
        root_pyproject = root / "pyproject.toml"
        root_pyproject.write_text('[tool.poetry]\nname = "myproject"')

        # .venv config (should be excluded)
        venv_path = (
            root / ".venv" / "lib" / "python3.11" / "site-packages" / "setuptools"
        )
        venv_path.mkdir(parents=True)
        venv_pyproject = venv_path / "pyproject.toml"
        venv_pyproject.write_text("[tool.setuptools]\nzip-safe = false")

        # Generate skeleton
        config = Config(mode="skeleton")
        generator = SkeletonGenerator(root, config)
        output = generator.generate()

        # ASSERTIONS
        # Root config should be included
        assert "myproject" in output  # Root config content

        # .venv config should NOT appear
        assert "setuptools" not in output  # .venv content should NOT appear
        assert "zip-safe" not in output

        # Verify stats
        assert generator.stats["full_content"] == 1  # Only root pyproject
        assert generator.stats["excluded"] >= 1

    def test_config_file_in_build_dir_should_be_excluded(self, tmp_path):
        """
        Bug #1: Config files in build/, dist/, vendor/ should be EXCLUDED.
        """
        # Create structure
        root = tmp_path / "project"
        root.mkdir()

        # Root level config
        root_package = root / "package.json"
        root_package.write_text('{"name": "myapp", "version": "1.0.0"}')

        # Build dir config (should be excluded)
        build_dir = root / "build" / "static"
        build_dir.mkdir(parents=True)
        build_package = build_dir / "package.json"
        build_package.write_text('{"name": "build-artifact", "private": true}')

        # Dist dir config (should be excluded)
        dist_dir = root / "dist" / "vendor"
        dist_dir.mkdir(parents=True)
        dist_package = dist_dir / "package.json"
        dist_package.write_text('{"name": "vendor-lib", "private": true}')

        # Generate skeleton
        config = Config(mode="skeleton")
        generator = SkeletonGenerator(root, config)
        output = generator.generate()

        # ASSERTIONS
        # Root config should be included
        assert '"name": "myapp"' in output

        # Build and dist configs should NOT appear
        assert "build-artifact" not in output
        assert "vendor-lib" not in output

        # Verify stats
        assert generator.stats["full_content"] == 1  # Only root package.json
        assert generator.stats["excluded"] >= 2  # build and dist files

    def test_legitimate_subdir_config_should_be_included(self, tmp_path):
        """
        Verify that config files in legitimate subdirectories
        (not excluded dirs) are still included.
        """
        # Create structure
        root = tmp_path / "project"
        root.mkdir()

        # Root config
        root_tsconfig = root / "tsconfig.json"
        root_tsconfig.write_text('{"extends": "./tsconfig.base.json"}')

        # Legitimate subdir config (should be included)
        backend_dir = root / "src" / "backend"
        backend_dir.mkdir(parents=True)
        backend_tsconfig = backend_dir / "tsconfig.json"
        backend_tsconfig.write_text('{"compilerOptions": {"module": "commonjs"}}')

        # Generate skeleton
        config = Config(mode="skeleton")
        generator = SkeletonGenerator(root, config)
        output = generator.generate()

        # ASSERTIONS
        # Both configs should be included
        assert '"extends": "./tsconfig.base.json"' in output
        assert '"module": "commonjs"' in output

        # Verify stats
        assert generator.stats["full_content"] == 2  # Both tsconfig files

    def test_token_count_reduction_after_fix(self, tmp_path):
        """
        Verify that excluding config files from node_modules
        significantly reduces token count.
        """
        # Create structure with many node_modules configs
        root = tmp_path / "project"
        root.mkdir()

        # Root config (small)
        root_pkg = root / "package.json"
        root_pkg.write_text('{"name": "app"}')

        # Multiple node_modules configs (large)
        for pkg in ["typescript", "@types/node", "react", "lodash", "axios"]:
            pkg_dir = root / "node_modules" / pkg
            pkg_dir.mkdir(parents=True)
            pkg_json = pkg_dir / "package.json"
            # Large config content
            pkg_json.write_text(
                '{"name": "' + pkg + '", "description": "' + ("x" * 200) + '"}'
            )

        # Generate skeleton
        config = Config(mode="skeleton")
        generator = SkeletonGenerator(root, config)
        output = generator.generate()

        # ASSERTIONS
        # Token count should be low (only root config)
        # If bug exists, token count would be high (5 * 200+ chars)
        total_tokens = generator.stats["total_tokens"]

        # With bug: ~1000+ tokens (5 large files)
        # Without bug: <100 tokens (just root config)
        assert (
            total_tokens < 200
        ), f"Token count too high: {total_tokens} (bug not fixed)"

        # Only root package.json should be in full content
        assert generator.stats["full_content"] == 1
        assert generator.stats["excluded"] >= 5  # All node_modules files
