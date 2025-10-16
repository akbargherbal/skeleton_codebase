#!/usr/bin/env python3
"""
Debug test to trace the exclusion logic step by step.
Run with: pytest tests/unit/debug_exclusion_test.py -vv -s
"""
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from codebase_skeleton import TreeBuilder, Config


def test_debug_exclusion_logic():
    """Debug test to trace exactly what happens with src exclusion."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "README.md").write_text("# Mock")
        (temp_dir / "src" / "main.py").write_text("print('hello')")

        print("\n" + "=" * 80)
        print("SETUP:")
        print("=" * 80)
        print(f"temp_dir: {temp_dir}")
        print(f"temp_dir.name: {temp_dir.name}")

        # Create config with exclusion
        config = Config(exclude={"src"})
        print(f"\nconfig.exclude: {config.exclude}")
        print(f"type(config.exclude): {type(config.exclude)}")
        for item in config.exclude:
            print(f"  - {repr(item)} (type: {type(item)})")

        # Mock directory_tree as unavailable
        import codebase_skeleton

        original = codebase_skeleton.DIRECTORY_TREE_AVAILABLE
        codebase_skeleton.DIRECTORY_TREE_AVAILABLE = False

        # Patch the should_ignore function to add debug output
        original_fallback_tree = TreeBuilder._fallback_tree

        def debug_fallback_tree(root: Path, config: Config) -> str:
            """Patched version with debug output."""
            lines = [f"{root.name}/"]

            def should_ignore(path: Path) -> bool:
                """Check if path should be ignored in tree."""
                print(f"\n--- should_ignore() called ---")
                print(f"  path: {path}")
                print(f"  path.name: {repr(path.name)} (type: {type(path.name)})")
                print(f"  config.exclude: {config.exclude}")

                # Special case: Never ignore .gitignore or .dockerignore
                if path.name in {".gitignore", ".dockerignore"}:
                    print(
                        f"  -> Special case (.gitignore/.dockerignore): returning False"
                    )
                    return False

                # Check custom exclusions first
                print(f"  Checking custom exclusions...")
                for pattern in config.exclude:
                    print(f"    pattern: {repr(pattern)} (type: {type(pattern)})")

                    # For patterns starting with '.', do exact name match
                    if pattern.startswith("."):
                        print(f"      -> Dot pattern check")
                        if path.name == pattern:
                            print(f"      -> MATCH! returning True")
                            return True

                    # For wildcard patterns like "*.pyc"
                    elif "*" in pattern:
                        print(f"      -> Wildcard pattern check")
                        if path.match(pattern):
                            print(f"      -> MATCH! returning True")
                            return True

                    # For other patterns
                    else:
                        print(f"      -> Regular pattern check")
                        # Check if the pattern matches this path's name
                        print(
                            f"        path.name == pattern? {path.name} == {pattern} = {path.name == pattern}"
                        )
                        if path.name == pattern:
                            print(f"        -> NAME MATCH! returning True")
                            return True

                        # Check if pattern appears in any parent directory name
                        try:
                            rel_path = path.relative_to(root)
                            print(f"        rel_path: {rel_path}")
                            print(f"        rel_path.parts: {rel_path.parts}")
                            print(
                                f"        pattern in rel_path.parts? {pattern in rel_path.parts}"
                            )
                            if pattern in rel_path.parts:
                                print(f"        -> PARTS MATCH! returning True")
                                return True
                        except ValueError as e:
                            print(f"        ValueError: {e}")
                            if pattern in path.parts:
                                print(
                                    f"        -> ABSOLUTE PARTS MATCH! returning True"
                                )
                                return True

                print(f"  -> NO MATCH, returning False")
                return False

            def add_dir(path: Path, prefix: str = "", depth: int = 0):
                if depth >= 5:
                    return

                try:
                    items = sorted(
                        path.iterdir(), key=lambda x: (not x.is_dir(), x.name)
                    )
                except PermissionError:
                    return

                print(f"\n=== add_dir() processing: {path} ===")
                print(f"Items before filtering: {[item.name for item in items]}")

                # Filter items
                filtered_items = []
                for item in items:
                    ignore = should_ignore(item)
                    print(f"  {item.name}: ignore={ignore}")
                    if not ignore:
                        filtered_items.append(item)

                items = filtered_items
                print(f"Items after filtering: {[item.name for item in items]}")

                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current = "└── " if is_last else "├── "
                    extension = "    " if is_last else "│   "

                    if item.is_dir():
                        lines.append(f"{prefix}{current}{item.name}/")
                        add_dir(item, prefix + extension, depth + 1)
                    else:
                        lines.append(f"{prefix}{current}{item.name}")

            add_dir(root)
            return "\n".join(lines)

        # Use the debug version
        TreeBuilder._fallback_tree = staticmethod(debug_fallback_tree)

        # Build tree
        print("\n" + "=" * 80)
        print("BUILDING TREE:")
        print("=" * 80)
        tree_str = TreeBuilder.build(temp_dir, config)

        # Restore
        TreeBuilder._fallback_tree = staticmethod(original_fallback_tree)
        codebase_skeleton.DIRECTORY_TREE_AVAILABLE = original

        print("\n" + "=" * 80)
        print("FINAL TREE OUTPUT:")
        print("=" * 80)
        print(tree_str)
        print("=" * 80)

        print("\n" + "=" * 80)
        print("ASSERTIONS:")
        print("=" * 80)
        print(f"'src/' in tree_str: {'src/' in tree_str}")
        print(f"'main.py' in tree_str: {'main.py' in tree_str}")

        lines = tree_str.strip().split("\n")
        has_main_py = any(
            line.strip().endswith("main.py") and "tests/" not in line for line in lines
        )
        print(f"Has main.py outside tests: {has_main_py}")

    finally:
        shutil.rmtree(temp_dir)


def test_simple_exclusion_check():
    """Even simpler test - just check the logic directly."""
    from pathlib import Path
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())

    try:
        (temp_dir / "src").mkdir()
        src_path = temp_dir / "src"

        config = Config(exclude={"src"})

        print("\n" + "=" * 80)
        print("SIMPLE EXCLUSION CHECK:")
        print("=" * 80)
        print(f"src_path: {src_path}")
        print(f"src_path.name: {repr(src_path.name)}")
        print(f"config.exclude: {config.exclude}")

        # Manual check
        pattern = "src"
        print(f"\npattern: {repr(pattern)}")
        print(f"src_path.name == pattern: {src_path.name == pattern}")
        print(f"Result: {src_path.name == pattern}")

        # Check if it's in the set
        print(f"\npattern in config.exclude: {pattern in config.exclude}")
        for item in config.exclude:
            print(f"  item: {repr(item)}, item == pattern: {item == pattern}")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_debug_exclusion_logic()
    test_simple_exclusion_check()
