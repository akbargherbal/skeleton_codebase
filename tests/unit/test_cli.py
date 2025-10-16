#!/usr/bin/env python3
"""
Test module: test_cli
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import main, Config


class TestCLI:
    """Test command-line interface."""

    @patch("codebase_skeleton.SkeletonGenerator")
    def test_main_with_valid_path(self, mock_generator_class, mock_codebase):
        """Test main() with valid codebase path."""
        mock_instance = mock_generator_class.return_value
        mock_instance.generate.return_value = "Generated Skeleton"

        with patch("sys.argv", ["codebase_skeleton.py", str(mock_codebase)]):
            main()

        mock_generator_class.assert_called_once()
        args, _ = mock_generator_class.call_args
        assert args[0] == mock_codebase
        assert isinstance(args[1], Config)
        assert args[1].mode == "skeleton"
        mock_instance.generate.assert_called_once()

    def test_main_with_invalid_path(self, capsys):
        """Test main() with non-existent path."""
        with patch("sys.argv", ["codebase_skeleton.py", "/no/such/path"]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Error: Path does not exist" in captured.err

    def test_main_path_is_file_not_directory(self, temp_dir, capsys):
        """Test main() exits when path is a file."""
        file_path = temp_dir / "file.txt"
        file_path.touch()
        with patch("sys.argv", ["codebase_skeleton.py", str(file_path)]):
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1

        captured = capsys.readouterr()
        assert "Error: Path is not a directory" in captured.err

    @patch("codebase_skeleton.SkeletonGenerator")
    def test_main_overview_mode(self, mock_generator_class, mock_codebase):
        """Test main() with --mode=overview."""
        with patch(
            "sys.argv", ["codebase_skeleton.py", str(mock_codebase), "--mode=overview"]
        ):
            main()

        args, _ = mock_generator_class.call_args
        assert args[1].mode == "overview"

    @patch("codebase_skeleton.SkeletonGenerator")
    def test_main_include_full_flag(self, mock_generator_class, mock_codebase):
        """Test main() with --include-full argument."""
        with patch(
            "sys.argv",
            [
                "codebase_skeleton.py",
                str(mock_codebase),
                "--include-full=src/main.py,README.md",
            ],
        ):
            main()

        args, _ = mock_generator_class.call_args
        assert args[1].include_full == {"src/main.py", "README.md"}

    @patch("codebase_skeleton.SkeletonGenerator")
    def test_main_exclude_flag(self, mock_generator_class, mock_codebase):
        """Test main() with --exclude argument."""
        with patch(
            "sys.argv",
            ["codebase_skeleton.py", str(mock_codebase), "--exclude=*.js,build/"],
        ):
            main()

        args, _ = mock_generator_class.call_args
        assert args[1].exclude == {"*.js", "build/"}

    @patch("codebase_skeleton.SkeletonGenerator")
    def test_main_skeleton_only_flag(self, mock_generator_class, mock_codebase):
        """Test main() with --skeleton-only argument."""
        with patch(
            "sys.argv",
            ["codebase_skeleton.py", str(mock_codebase), "--skeleton-only=src/"],
        ):
            main()

        args, _ = mock_generator_class.call_args
        assert args[1].skeleton_only == {"src/"}

    def test_main_output_to_file(self, mock_codebase, temp_dir):
        """Test main() with --output flag writes to file."""
        output_file = temp_dir / "output.txt"
        with patch(
            "sys.argv",
            ["codebase_skeleton.py", str(mock_codebase), f"--output={output_file}"],
        ):
            main()

        assert output_file.exists()
        content = output_file.read_text()
        assert "<codebase project=" in content

    def test_main_output_to_stdout(self, mock_codebase, capsys):
        """Test main() without --output prints to stdout."""
        with patch("sys.argv", ["codebase_skeleton.py", str(mock_codebase)]):
            main()

        captured = capsys.readouterr()
        assert "<codebase project=" in captured.out

    def test_main_no_arguments(self, capsys):
        """Test main() with no arguments shows error."""
        with patch("sys.argv", ["codebase_skeleton.py"]):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "usage: codebase_skeleton.py" in captured.err
