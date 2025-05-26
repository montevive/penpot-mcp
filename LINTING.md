# Linting Guide

This document provides guidelines on how to work with the linting tools configured in this project.

## Overview

The project uses the following linting tools:

- **flake8**: Code style and quality checker
- **isort**: Import sorting
- **autopep8**: PEP 8 code formatting with auto-fix capability
- **pyupgrade**: Upgrades Python syntax for newer versions
- **pre-commit**: Framework for managing pre-commit hooks

## Quick Start

1. Use the setup script to install all dependencies and set up pre-commit hooks:

```bash
./fix-lint-deps.sh
```

Or install dependencies manually:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

2. Run the linting script:

```bash
# Check for issues
./lint.py

# Fix issues automatically where possible
./lint.py --autofix
```

## Dependencies

The linting tools require specific dependencies:

- **flake8** and **flake8-docstrings**: For code style and documentation checking
- **isort**: For import sorting
- **autopep8**: For automatic PEP 8 compliance
- **pyupgrade**: For Python syntax upgrading
- **setuptools**: Required for lib2to3 which is used by autopep8

If you encounter a `ModuleNotFoundError: No module named 'lib2to3'` error, make sure you have setuptools installed:

```bash
pip install setuptools>=65.5.0
```

Or simply run the fix script:

```bash
./fix-lint-deps.sh
```

## Configuration

The linting tools are configured in the following files:

- **setup.cfg**: Contains settings for flake8, autopep8, etc.
- **.pre-commit-config.yaml**: Configuration for pre-commit hooks
- **.editorconfig**: Editor settings for consistent code formatting

## Linting Rules

### Code Style Rules

We follow PEP 8 with some exceptions:

- **Line Length**: Max line length is 100 characters
- **Ignored Rules**:
  - E203: Whitespace before ':' (conflicts with Black)
  - W503: Line break before binary operator (conflicts with Black)

### Documentation Rules

All public modules, functions, classes, and methods should have docstrings. We use the Google style for docstrings.

Example:

```python
def function(param1, param2):
    """Summary of function purpose.

    More detailed explanation if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ExceptionType: When and why this exception is raised.
    """
    # function implementation
```

### Import Sorting

Imports should be sorted using isort with the black profile. Imports are grouped in the following order:

1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

With each group sorted alphabetically.

## Auto-Fixing Issues

Many issues can be fixed automatically:

- **Import Sorting**: `isort` can sort imports automatically
- **PEP 8 Formatting**: `autopep8` can fix many style issues
- **Python Syntax**: `pyupgrade` can update syntax to newer Python versions

Run the auto-fix command:

```bash
./lint.py --autofix
```

## Troubleshooting

If you encounter issues with the linting tools:

1. **Missing dependencies**: Run `./fix-lint-deps.sh` to install all required dependencies
2. **Autopep8 errors**: Make sure setuptools is installed for lib2to3 support
3. **Pre-commit hook failures**: Run `pre-commit run --all-files` to see which files are causing issues

## Pre-commit Hooks

Pre-commit hooks run automatically when you commit changes. They ensure that linting issues are caught before code is committed.

If hooks fail during a commit:

1. The commit will be aborted
2. Review the error messages
3. Fix the issues manually or using auto-fix
4. Stage the fixed files
5. Retry your commit

## Common Issues and Solutions

### Disabling Linting for Specific Lines

Sometimes it's necessary to disable linting for specific lines:

```python
# For flake8
some_code = "example"  # noqa: E501

# For multiple rules
some_code = "example"  # noqa: E501, F401
```

### Handling Third-Party Code

For third-party code that doesn't follow our style, consider isolating it in a separate file or directory and excluding it from linting.

## IDE Integration

### VSCode

Install the Python, Flake8, and EditorConfig extensions. Add to settings.json:

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "python.formatting.provider": "autopep8",
    "python.sortImports.args": ["--profile", "black"]
}
```

### PyCharm

Enable Flake8 in:
Settings → Editor → Inspections → Python → Flake8

Configure isort:
Settings → Editor → Code Style → Python → Imports

## Customizing Linting Rules

To modify linting rules:

1. Edit `setup.cfg` for flake8 and autopep8 settings
2. Edit `.pre-commit-config.yaml` for pre-commit hook settings
3. Run `pre-commit autoupdate` to update hook versions

## Continuous Integration

Linting checks are part of the CI pipeline. Pull requests that fail linting will not be merged until issues are fixed.
