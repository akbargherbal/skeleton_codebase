#!/usr/bin/env python3
"""
Verify that the monkeypatch fixture is working correctly.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import codebase_skeleton
from codebase_skeleton import TreeBuilder, Config


def test_check_directory_tree_available_value(mock_directory_tree_unavailable):
    """Check what DIRECTORY_TREE_AVAILABLE is set to."""
    print(f"\nDIRECTORY_TREE_AVAILABLE = {codebase_skeleton.DIRECTORY_TREE_AVAILABLE}")
    print(f"Type: {type(codebase_skeleton.DIRECTORY_TREE_AVAILABLE)}")
    
    assert codebase_skeleton.DIRECTORY_TREE_AVAILABLE == False, \
        "Fixture should set DIRECTORY_TREE_AVAILABLE to False"


def test_fallback_tree_respects_exclusions_verbose(
    mock_codebase, mock_directory_tree_unavailable
):
    """Exact copy of the failing test with verbose output."""
    import codebase_skeleton
    
    print(f"\n{'='*80}")
    print("TEST START")
    print(f"{'='*80}")
    print(f"DIRECTORY_TREE_AVAILABLE = {codebase_skeleton.DIRECTORY_TREE_AVAILABLE}")
    print(f"mock_codebase = {mock_codebase}")
    
    custom_config = Config(exclude={"src"})
    print(f"custom_config.exclude = {custom_config.exclude}")
    
    tree_str = TreeBuilder.build(mock_codebase, custom_config)
    
    print(f"\n{'='*80}")
    print("TREE OUTPUT:")
    print(f"{'='*80}")
    print(tree_str)
    print(f"{'='*80}")
    
    print(f"\nChecking assertions:")
    print(f"  'src/' in tree_str: {'src/' in tree_str}")
    
    lines = tree_str.strip().split("\n")
    has_main_outside_tests = any(
        line.strip().endswith("main.py") and "tests/" not in line for line in lines
    )
    print(f"  has main.py outside tests: {has_main_outside_tests}")
    
    # The actual test assertions
    assert "src/" not in tree_str, f"FAILED: 'src/' found in tree"
    assert not has_main_outside_tests, f"FAILED: main.py found outside tests"
    
    print("\n✅ TEST PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-vv", "-s"])
