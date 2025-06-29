#!/usr/bin/env python3
"""Script to run linters with auto-fix capabilities.

Run with: python lint.py [--autofix]
"""

import argparse
import importlib.util
import subprocess
import sys


def is_venv():
    """Check if running in a virtual environment."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []

    # Check for required modules
    required_modules = ["flake8", "isort", "autopep8", "pyflakes"]

    # In Python 3.12+, also check for pycodestyle as a fallback
    if sys.version_info >= (3, 12):
        required_modules.append("pycodestyle")

    for module in required_modules:
        if importlib.util.find_spec(module) is None:
            missing_deps.append(module)

    # Special check for autopep8 compatibility with Python 3.12+
    if sys.version_info >= (3, 12) and importlib.util.find_spec("autopep8") is not None:
        try:
            import autopep8

            # Try to access a function that would use lib2to3
            # Will throw an error if lib2to3 is missing and not handled properly
            autopep8_version = autopep8.__version__
            print(f"Using autopep8 version: {autopep8_version}")
        except ImportError as e:
            if "lib2to3" in str(e):
                print("WARNING: You're using Python 3.12+ where lib2to3 is no longer included.")
                print("Your installed version of autopep8 may not work correctly.")
                print("Consider using a version of autopep8 compatible with Python 3.12+")
                print("or run this script with Python 3.11 or earlier.")

    if missing_deps:
        print("ERROR: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")

        if not is_venv():
            print("\nYou are using the system Python environment.")
            print("It's recommended to use a virtual environment:")
            print("\n1. Create a virtual environment:")
            print("   python3 -m venv .venv")
            print("\n2. Activate the virtual environment:")
            print("   source .venv/bin/activate  # On Linux/macOS")
            print("   .venv\\Scripts\\activate     # On Windows")
            print("\n3. Install dependencies:")
            print("   pip install -r requirements-dev.txt")
        else:
            print("\nPlease install these dependencies with:")
            print("  pip install -r requirements-dev.txt")

        return False

    return True


def run_command(cmd, cwd=None):
    """Run a shell command and return the exit code."""
    try:
        process = subprocess.run(cmd, shell=True, cwd=cwd)
        return process.returncode
    except Exception as e:
        print(f"Error executing command '{cmd}': {e}")
        return 1


def fix_unused_imports(root_dir):
    """Fix unused imports using pyflakes and autoflake."""
    try:
        if importlib.util.find_spec("autoflake") is not None:
            print("Running autoflake to remove unused imports...")
            cmd = "autoflake --remove-all-unused-imports --recursive --in-place penpot_mcp/ tests/"
            return run_command(cmd, cwd=root_dir)
        else:
            print("autoflake not found. To automatically remove unused imports, install:")
            print("  pip install autoflake")
            return 0
    except Exception as e:
        print(f"Error with autoflake: {e}")
        return 0


def fix_whitespace_and_docstring_issues(root_dir):
    """Attempt to fix whitespace and simple docstring issues."""
    # Find Python files that need fixing
    try:
        filelist_cmd = "find penpot_mcp tests setup.py -name '*.py' -type f"
        process = subprocess.run(
            filelist_cmd, shell=True, cwd=root_dir,
            capture_output=True, text=True
        )

        if process.returncode != 0:
            print("Error finding Python files")
            return 1

        files = process.stdout.strip().split('\n')
        fixed_count = 0

        for file_path in files:
            if not file_path:
                continue

            full_path = Path(root_dir) / file_path

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Fix trailing whitespace
                fixed_content = '\n'.join(line.rstrip() for line in content.split('\n'))

                # Ensure final newline
                if not fixed_content.endswith('\n'):
                    fixed_content += '\n'

                # Add basic docstrings to empty modules, classes, functions
                if '__init__.py' in file_path and '"""' not in fixed_content:
                    package_name = file_path.split('/')[-2]
                    fixed_content = f'"""Package {package_name}."""\n' + fixed_content

                # Write back if changes were made
                if fixed_content != content:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    fixed_count += 1

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        if fixed_count > 0:
            print(f"Fixed whitespace and newlines in {fixed_count} files")

        return 0
    except Exception as e:
        print(f"Error in whitespace fixing: {e}")
        return 0


def main():
    """Main entry point for the linter script."""
    parser = argparse.ArgumentParser(description="Run linters with optional auto-fix")
    parser.add_argument(
        "--autofix", "-a", action="store_true", help="Automatically fix linting issues"
    )
    args = parser.parse_args()

    # Verify dependencies before proceeding
    if not check_dependencies():
        return 1

    root_dir = Path(__file__).parent.absolute()

    print("Running linters...")

    # Run isort
    isort_cmd = "isort --profile black ."
    if args.autofix:
        print("Running isort with auto-fix...")
        exit_code = run_command(isort_cmd, cwd=root_dir)
    else:
        print("Checking imports with isort...")
        exit_code = run_command(f"{isort_cmd} --check", cwd=root_dir)

    if exit_code != 0 and not args.autofix:
        print("isort found issues. Run with --autofix to fix automatically.")

    # Run additional fixers when in autofix mode
    if args.autofix:
        # Fix unused imports
        fix_unused_imports(root_dir)

        # Fix whitespace and newline issues
        fix_whitespace_and_docstring_issues(root_dir)

        # Run autopep8
        print("Running autopep8 with auto-fix...")

        if sys.version_info >= (3, 12):
            print("Detected Python 3.12+. Using compatible code formatting approach...")
            # Use a more compatible approach for Python 3.12+
            # First try autopep8 (newer versions may have fixed lib2to3 dependency)
            autopep8_cmd = "autopep8 --recursive --aggressive --aggressive --in-place --select E,W penpot_mcp/ tests/ setup.py"
            try:
                exit_code = run_command(autopep8_cmd, cwd=root_dir)
                if exit_code != 0:
                    print("Warning: autopep8 encountered issues. Some files may not have been fixed.")
            except Exception as e:
                if "lib2to3" in str(e):
                    print("Error with autopep8 due to missing lib2to3 module in Python 3.12+")
                    print("Using pycodestyle for checking only (no auto-fix is possible)")
                    exit_code = run_command("pycodestyle penpot_mcp/ tests/", cwd=root_dir)
                else:
                    raise
        else:
            # Normal execution for Python < 3.12
            autopep8_cmd = "autopep8 --recursive --aggressive --aggressive --in-place --select E,W penpot_mcp/ tests/ setup.py"
            exit_code = run_command(autopep8_cmd, cwd=root_dir)
            if exit_code != 0:
                print("Warning: autopep8 encountered issues. Some files may not have been fixed.")

    # Run flake8 (check only, no auto-fix)
    print("Running flake8...")
    flake8_cmd = "flake8 --exclude=.venv,venv,__pycache__,.git,build,dist,*.egg-info,node_modules"
    flake8_result = run_command(flake8_cmd, cwd=root_dir)

    if flake8_result != 0:
        print("flake8 found issues that need to be fixed manually.")
        print("Common issues and how to fix them:")
        print("- F401 (unused import): Remove the import or use it")
        print("- D1XX (missing docstring): Add a docstring to the module/class/function")
        print("- E501 (line too long): Break the line or use line continuation")
        print("- F841 (unused variable): Remove or use the variable")

    if args.autofix:
        print("Auto-fix completed! Run flake8 again to see if there are any remaining issues.")
    elif exit_code != 0 or flake8_result != 0:
        print("Linting issues found. Run with --autofix to fix automatically where possible.")
        return 1
    else:
        print("All linting checks passed!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
